#!/usr/bin/env python3
"""
Simple test to find the working bbox + similarity combination.
Focus on the two-stage approach that should work.
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

def safe_database_operation(operation_func, timeout_seconds=8, test_name="Unknown"):
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

def test_bbox_first_approach():
    """Test: Bbox first, then similarity (GPT5's recommended approach)."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Step 1: Get bbox results first (spatial prefiltering)
                bbox_query = """
                SELECT doctrove_paper_id, doctrove_embedding
                FROM doctrove_papers
                WHERE doctrove_embedding IS NOT NULL
                AND doctrove_embedding_2d IS NOT NULL
                AND doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                LIMIT 1000
                """
                
                cur.execute(bbox_query)
                bbox_results = cur.fetchall()
                
                if not bbox_results:
                    return 0
                
                # Step 2: Calculate similarity for bbox results
                paper_ids = [row['doctrove_paper_id'] for row in bbox_results]
                placeholders = ','.join(['%s'] * len(paper_ids))
                
                similarity_query = f"""
                SELECT doctrove_paper_id, doctrove_title, doctrove_source,
                       (1 - (doctrove_embedding <=> %s::vector)) as similarity_score
                FROM doctrove_papers
                WHERE doctrove_paper_id IN ({placeholders})
                ORDER BY doctrove_embedding <=> %s::vector
                LIMIT 10
                """
                
                params = [test_embedding.tolist()] + paper_ids + [test_embedding.tolist()]
                cur.execute(similarity_query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=8, test_name="Bbox First Approach")

def test_smaller_bbox():
    """Test: Smaller bbox to reduce dataset size."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Smaller bbox (center of the original)
                query = """
                WITH bbox_results AS (
                  SELECT doctrove_paper_id, doctrove_title, doctrove_source, doctrove_embedding
                  FROM doctrove_papers
                  WHERE doctrove_embedding IS NOT NULL
                  AND doctrove_embedding_2d IS NOT NULL
                  AND doctrove_embedding_2d <@ box(point(8, -2), point(15, 5))
                  LIMIT 500
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
    
    return safe_database_operation(operation, timeout_seconds=8, test_name="Smaller Bbox")

def test_bbox_with_source_filter():
    """Test: Bbox + source filter first, then similarity."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Bbox + source filter first, then similarity
                query = """
                WITH filtered_results AS (
                  SELECT doctrove_paper_id, doctrove_title, doctrove_source, doctrove_embedding
                  FROM doctrove_papers
                  WHERE doctrove_embedding IS NOT NULL
                  AND doctrove_embedding_2d IS NOT NULL
                  AND doctrove_source IN ('openalex','randpub')
                  AND doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                  LIMIT 1000
                )
                SELECT doctrove_paper_id, doctrove_title, doctrove_source,
                       (1 - (doctrove_embedding <=> %s::vector)) as similarity_score
                FROM filtered_results
                ORDER BY doctrove_embedding <=> %s::vector
                LIMIT 10
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=8, test_name="Bbox + Source Filter")

def main():
    """Test different bbox + similarity approaches."""
    logger.info("🔬 Testing Bbox + Similarity Approaches")
    logger.info("🎯 Goal: Find a working combination")
    logger.info("⏰ Timeout: 8 seconds per test")
    logger.info("=" * 50)
    
    tests = [
        ("Bbox First Approach", test_bbox_first_approach),
        ("Smaller Bbox", test_smaller_bbox),
        ("Bbox + Source Filter", test_bbox_with_source_filter),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*15} {test_name} {'='*15}")
        
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
    logger.info(f"\n{'='*50}")
    logger.info("BBOX + SIMILARITY TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        count = result['result_count']
        logger.info(f"{test_name:20} | {status:8} | {duration:5.2f}s | {count:2d} results")
    
    # Analysis
    logger.info(f"\n{'='*50}")
    logger.info("ANALYSIS")
    logger.info(f"{'='*50}")
    
    working_tests = [name for name, result in results.items() if result['success']]
    if working_tests:
        logger.info(f"✅ Working approaches: {', '.join(working_tests)}")
        logger.info("🎯 We found a working combination!")
    else:
        logger.error("❌ All approaches failed - need to investigate further")
    
    return len(working_tests) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



