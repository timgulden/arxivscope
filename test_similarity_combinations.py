#!/usr/bin/env python3
"""
Focused test for similarity query + filter combinations.
Tests similarity query with individual filters, then pairs, to isolate the hanging issue.
Uses very short timeouts to prevent hangs.
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

def safe_database_operation(operation_func, timeout_seconds=5, test_name="Unknown"):
    """Execute database operation with very short timeout protection."""
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

def execute_similarity_query(query: str, params: List[Any], test_name: str):
    """Execute a similarity query with timeout protection."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=5, test_name=test_name)

def test_similarity_only():
    """Test 1: Similarity query only (baseline)."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity Only")

def test_similarity_plus_embedding_filter():
    """Test 2: Similarity + embedding filter (should be same as similarity only)."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + Embedding Filter")

def test_similarity_plus_source_filter():
    """Test 3: Similarity + source filter."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + Source Filter")

def test_similarity_plus_date_filter():
    """Test 4: Similarity + date filter."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + Date Filter")

def test_similarity_plus_2d_filter():
    """Test 5: Similarity + 2D embedding filter."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND dp.doctrove_embedding_2d IS NOT NULL
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + 2D Embedding Filter")

def test_similarity_plus_bbox_filter():
    """Test 6: Similarity + bounding box filter."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + Bounding Box Filter")

def test_similarity_plus_source_date():
    """Test 7: Similarity + source + date filters."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
    AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + Source + Date")

def test_similarity_plus_source_2d():
    """Test 8: Similarity + source + 2D embedding filters."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
    AND dp.doctrove_embedding_2d IS NOT NULL
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + Source + 2D")

def test_similarity_plus_date_2d():
    """Test 9: Similarity + date + 2D embedding filters."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
    AND dp.doctrove_embedding_2d IS NOT NULL
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + Date + 2D")

def test_similarity_plus_2d_bbox():
    """Test 10: Similarity + 2D embedding + bounding box filters."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND dp.doctrove_embedding_2d IS NOT NULL
    AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + 2D + Bounding Box")

def test_similarity_plus_source_date_2d():
    """Test 11: Similarity + source + date + 2D embedding filters."""
    test_embedding = generate_test_embedding()
    
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
    AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
    AND dp.doctrove_embedding_2d IS NOT NULL
    ORDER BY dp.doctrove_embedding <=> %s::vector
    LIMIT 10
    """
    
    params = [test_embedding.tolist(), test_embedding.tolist()]
    return execute_similarity_query(query, params, "Similarity + Source + Date + 2D")

def test_similarity_plus_all_filters():
    """Test 12: Similarity + ALL filters (the problematic combination)."""
    test_embedding = generate_test_embedding()
    
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
    return execute_similarity_query(query, params, "Similarity + ALL FILTERS")

def main():
    """Run systematic similarity + filter combination tests."""
    logger.info("🔬 Starting systematic similarity + filter combination testing...")
    logger.info("🎯 Focus: Isolate which filter combination breaks similarity queries")
    logger.info("⏰ Timeout: 5 seconds per test to prevent hangs")
    logger.info("=" * 80)
    
    tests = [
        ("Similarity Only", test_similarity_only),
        ("Similarity + Embedding", test_similarity_plus_embedding_filter),
        ("Similarity + Source", test_similarity_plus_source_filter),
        ("Similarity + Date", test_similarity_plus_date_filter),
        ("Similarity + 2D", test_similarity_plus_2d_filter),
        ("Similarity + BBox", test_similarity_plus_bbox_filter),
        ("Similarity + Source + Date", test_similarity_plus_source_date),
        ("Similarity + Source + 2D", test_similarity_plus_source_2d),
        ("Similarity + Date + 2D", test_similarity_plus_date_2d),
        ("Similarity + 2D + BBox", test_similarity_plus_2d_bbox),
        ("Similarity + Source + Date + 2D", test_similarity_plus_source_date_2d),
        ("Similarity + ALL FILTERS", test_similarity_plus_all_filters),
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
    logger.info("SIMILARITY + FILTER COMBINATION TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        count = result['result_count']
        logger.info(f"{test_name:30} | {status:8} | {duration:6.2f}s | {count:3d} results")
    
    # Find the problematic combination
    logger.info(f"\n{'='*80}")
    logger.info("ANALYSIS")
    logger.info(f"{'='*80}")
    
    failed_tests = [name for name, result in results.items() if not result['success']]
    if failed_tests:
        logger.error(f"❌ Failed tests: {', '.join(failed_tests)}")
        logger.error("🔍 These are the problematic filter combinations!")
        
        # Find the first failure to identify the breaking point
        for i, (test_name, result) in enumerate(results.items()):
            if not result['success']:
                logger.error(f"🚨 BREAKING POINT: {test_name} is the first test to fail!")
                break
    else:
        logger.info("✅ All similarity + filter combination tests passed!")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)





