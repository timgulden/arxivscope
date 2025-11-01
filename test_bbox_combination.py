#!/usr/bin/env python3
"""
Test bbox filter alone, then similarity + bbox combination.
Goal: Find the right way to combine them efficiently.
"""

import os
import sys
import time
import signal
import logging
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def timeout_handler(signum, frame):
    """Handle timeout signal."""
    raise TimeoutError("Operation timed out")

def safe_database_operation(operation_func, timeout_seconds=10, test_name="Unknown"):
    """Execute database operation with timeout protection."""
    logger.info(f"🧪 Testing: {test_name}")
    
    # Set up timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        start_time = time.time()
        result = operation_func()
        duration = time.time() - start_time
        signal.alarm(0)  # Cancel timeout
        
        logger.info(f"✅ {test_name}: SUCCESS ({duration:.2f}s)")
        return result, duration
    except TimeoutError:
        logger.error(f"❌ {test_name}: TIMEOUT after {timeout_seconds}s")
        return None, timeout_seconds
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        logger.error(f"❌ {test_name}: ERROR after {duration:.2f}s - {e}")
        return None, duration
    finally:
        signal.signal(signal.SIGALRM, old_handler)  # Restore original handler

def get_db_connection():
    """Get database connection."""
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def generate_test_embedding():
    """Generate a test embedding."""
    test_embedding = np.random.randn(1536).astype(np.float32)
    test_embedding = test_embedding / np.linalg.norm(test_embedding)
    return test_embedding

def test_bbox_only():
    """Test 1: Bounding box filter alone."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Bbox filter alone
                query = """
                SELECT doctrove_paper_id, doctrove_title, doctrove_source
                FROM doctrove_papers
                WHERE doctrove_embedding_2d IS NOT NULL
                AND doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                LIMIT 10
                """
                
                cur.execute(query)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Bbox Filter Only")

def test_bbox_with_other_filters():
    """Test 2: Bbox + source + date filters."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Bbox + source + date filters
                query = """
                SELECT doctrove_paper_id, doctrove_title, doctrove_source
                FROM doctrove_papers
                WHERE doctrove_embedding_2d IS NOT NULL
                AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
                AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
                AND doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                LIMIT 10
                """
                
                cur.execute(query)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Bbox + Source + Date")

def test_similarity_then_bbox():
    """Test 3: Similarity first, then bbox filter (GPT5's approach)."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Similarity first, then bbox
                query = """
                WITH similarity_results AS (
                  SELECT doctrove_paper_id, doctrove_title, doctrove_source, doctrove_embedding_2d,
                         (1 - (doctrove_embedding <=> %s::vector)) as similarity_score
                  FROM doctrove_papers
                  WHERE doctrove_embedding IS NOT NULL
                  ORDER BY doctrove_embedding <=> %s::vector
                  LIMIT 1000
                )
                SELECT doctrove_paper_id, doctrove_title, doctrove_source, similarity_score
                FROM similarity_results
                WHERE doctrove_embedding_2d IS NOT NULL
                AND doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                ORDER BY similarity_score DESC
                LIMIT 10
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="Similarity THEN Bbox")

def test_bbox_then_similarity():
    """Test 4: Bbox first, then similarity (spatial prefiltering)."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Bbox first, then similarity
                query = """
                WITH bbox_results AS (
                  SELECT doctrove_paper_id, doctrove_title, doctrove_source, doctrove_embedding
                  FROM doctrove_papers
                  WHERE doctrove_embedding IS NOT NULL
                  AND doctrove_embedding_2d IS NOT NULL
                  AND doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                  LIMIT 1000
                )
                SELECT doctrove_paper_id, doctrove_title, doctrove_source,
                       (1 - (doctrove_embedding <=> %s::vector)) as similarity_score
                FROM bbox_results
                ORDER BY doctrove_embedding <=> %s::vector
                LIMIT 10
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="Bbox THEN Similarity")

def test_problematic_combination():
    """Test 5: The problematic combination that hangs."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # The problematic combination
                query = """
                SELECT doctrove_paper_id, doctrove_title, doctrove_source,
                       (1 - (doctrove_embedding <=> %s::vector)) as similarity_score
                FROM doctrove_papers
                WHERE doctrove_embedding IS NOT NULL
                AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
                AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
                AND doctrove_embedding_2d IS NOT NULL
                AND doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                ORDER BY doctrove_embedding <=> %s::vector
                LIMIT 10
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="Problematic Combination")

def main():
    """Test different ways to combine bbox and similarity."""
    logger.info("🔬 Testing Bbox + Similarity Combinations")
    logger.info("🎯 Goal: Find the right way to combine bbox and similarity")
    logger.info("⏰ Timeout: 10-15 seconds per test")
    logger.info("=" * 60)
    
    tests = [
        ("Bbox Only", test_bbox_only),
        ("Bbox + Source + Date", test_bbox_with_other_filters),
        ("Similarity THEN Bbox", test_similarity_then_bbox),
        ("Bbox THEN Similarity", test_bbox_then_similarity),
        ("Problematic Combination", test_problematic_combination),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            result, duration = test_func()
            results[test_name] = {
                'success': result is not None,
                'duration': duration,
                'result_count': result if result is not None else 0
            }
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = {
                'success': False,
                'duration': 0,
                'result_count': 0,
                'error': str(e)
            }
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("BBOX + SIMILARITY TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        count = result['result_count']
        logger.info(f"{test_name:25} | {status:8} | {duration:6.2f}s | {count:3d} results")
    
    # Analysis
    logger.info(f"\n{'='*60}")
    logger.info("ANALYSIS")
    logger.info(f"{'='*60}")
    
    if 'Bbox Only' in results and results['Bbox Only']['success']:
        logger.info("✅ Bbox filter works alone")
    else:
        logger.error("❌ Bbox filter has issues")
    
    if 'Problematic Combination' in results and results['Problematic Combination']['success']:
        logger.info("✅ The problematic combination actually works!")
        logger.info("🔍 The issue might be with specific data or query execution order")
    else:
        logger.error("❌ The problematic combination hangs as expected")
    
    # Find the best approach
    working_approaches = [name for name, result in results.items() if result['success'] and 'Similarity' in name]
    if working_approaches:
        logger.info(f"✅ Working approaches: {', '.join(working_approaches)}")
    
    return all(result['success'] for result in results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



