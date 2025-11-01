#!/usr/bin/env python3
"""
Test the two-stage query solution from GPT5.
Implements spatial prefiltering + vector similarity ranking to fix the hanging issue.
"""

import os
import sys
import time
import signal
import logging
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List, Tuple

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

def test_old_problematic_query():
    """Test 1: The old problematic query that hangs."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # The old problematic query
                query = """
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
                       (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
                FROM doctrove_papers dp
                WHERE dp.doctrove_embedding IS NOT NULL
                AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
                AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
                AND dp.doctrove_embedding_2d IS NOT NULL
                AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                ORDER BY dp.doctrove_embedding <=> %s::vector
                LIMIT 10
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="Old Problematic Query")

def test_two_stage_query():
    """Test 2: GPT5's two-stage query solution."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # GPT5's two-stage query solution
                query = """
                WITH pre AS (
                  SELECT dp.doctrove_paper_id AS id, dp.doctrove_embedding
                  FROM doctrove_papers dp
                  WHERE dp.doctrove_embedding IS NOT NULL
                    AND dp.doctrove_source IN ('openalex','randpub','extpub','aipickle')
                    AND dp.doctrove_primary_date BETWEEN DATE '2000-01-01' AND DATE '2025-12-31'
                    AND dp.doctrove_embedding_2d IS NOT NULL
                    AND dp.doctrove_embedding_2d <@ box(
                          point(2.2860022533483075,-7.932099066874233),
                          point(20.666694546883626,10.207678519388882)
                        )
                  ORDER BY dp.doctrove_embedding_2d <-> point(11.4763484, 1.1377897)  -- bbox center
                  LIMIT 50000
                )
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
                       dp.doctrove_primary_date, dp.doctrove_embedding_2d,
                       1 - (dp.doctrove_embedding <=> %s) AS similarity_score
                FROM pre p
                JOIN doctrove_papers dp ON dp.doctrove_paper_id = p.id
                ORDER BY dp.doctrove_embedding <=> %s
                LIMIT 10
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="Two-Stage Query Solution")

def test_bbox_size_check():
    """Test 3: Check how many records are in the bounding box."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check bounding box size
                query = """
                SELECT COUNT(*) as bbox_count
                FROM doctrove_papers dp
                WHERE dp.doctrove_embedding IS NOT NULL
                AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
                AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
                AND dp.doctrove_embedding_2d IS NOT NULL
                AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
                """
                
                cur.execute(query)
                result = cur.fetchone()
                return result['bbox_count']
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Bounding Box Size Check")

def test_simple_similarity():
    """Test 4: Simple similarity query (baseline)."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Simple similarity query
                query = """
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
                       (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
                FROM doctrove_papers dp
                WHERE dp.doctrove_embedding IS NOT NULL
                ORDER BY dp.doctrove_embedding <=> %s::vector
                LIMIT 10
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Simple Similarity Query")

def main():
    """Test the two-stage query solution."""
    logger.info("🔬 Testing GPT5's Two-Stage Query Solution")
    logger.info("🎯 Goal: Fix the similarity + bounding box hanging issue")
    logger.info("=" * 80)
    
    tests = [
        ("Bounding Box Size Check", test_bbox_size_check),
        ("Simple Similarity Query", test_simple_similarity),
        ("Two-Stage Query Solution", test_two_stage_query),
        ("Old Problematic Query", test_old_problematic_query),
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
    logger.info(f"\n{'='*80}")
    logger.info("TWO-STAGE QUERY TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        count = result['result_count']
        logger.info(f"{test_name:30} | {status:8} | {duration:6.2f}s | {count:3d} results")
    
    # Analysis
    logger.info(f"\n{'='*80}")
    logger.info("ANALYSIS")
    logger.info(f"{'='*80}")
    
    if 'Bounding Box Size Check' in results and results['Bounding Box Size Check']['success']:
        bbox_count = results['Bounding Box Size Check']['result_count']
        logger.info(f"📊 Bounding box contains {bbox_count:,} records")
        
        if bbox_count > 100000:
            logger.warning("⚠️  Large bounding box - two-stage query is essential!")
        elif bbox_count > 10000:
            logger.info("ℹ️  Medium bounding box - two-stage query recommended")
        else:
            logger.info("✅ Small bounding box - either approach should work")
    
    if 'Two-Stage Query Solution' in results and results['Two-Stage Query Solution']['success']:
        logger.info("🎉 Two-stage query solution works!")
    
    if 'Old Problematic Query' in results and results['Old Problematic Query']['success']:
        logger.warning("⚠️  Old query also works - may need larger test data")
    elif 'Old Problematic Query' in results and not results['Old Problematic Query']['success']:
        logger.info("✅ Old query fails as expected - two-stage solution needed")
    
    return all(result['success'] for result in results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




