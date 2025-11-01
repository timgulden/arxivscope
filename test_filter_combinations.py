#!/usr/bin/env python3
"""
Systematic filter combination testing to isolate the hanging issue.
Tests each filter individually and in combinations to find the problematic combination.
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

# Import the business logic
from business_logic import build_optimized_query_v2, get_embedding_for_text

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

def execute_query_directly(query: str, params: List[Any], test_name: str):
    """Execute a query directly against the database."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name=test_name)

def test_basic_query():
    """Test 1: Basic query with no filters."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    LIMIT 10
    """
    return execute_query_directly(query, [], "Basic Query (No Filters)")

def test_embedding_filter():
    """Test 2: Query with embedding filter only."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding IS NOT NULL
    LIMIT 10
    """
    return execute_query_directly(query, [], "Embedding Filter Only")

def test_2d_embedding_filter():
    """Test 3: Query with 2D embedding filter only."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding_2d IS NOT NULL
    LIMIT 10
    """
    return execute_query_directly(query, [], "2D Embedding Filter Only")

def test_source_filter():
    """Test 4: Query with source filter only."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    WHERE doctrove_source IN ('openalex','randpub','extpub','aipickle')
    LIMIT 10
    """
    return execute_query_directly(query, [], "Source Filter Only")

def test_date_filter():
    """Test 5: Query with date filter only."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    WHERE (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
    LIMIT 10
    """
    return execute_query_directly(query, [], "Date Filter Only")

def test_bbox_filter():
    """Test 6: Query with bounding box filter only."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    WHERE dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
    LIMIT 10
    """
    return execute_query_directly(query, [], "Bounding Box Filter Only")

def test_vector_similarity():
    """Test 7: Query with vector similarity only."""
    def operation():
        # Generate test embedding
        test_embedding = np.random.randn(1536).astype(np.float32)
        test_embedding = test_embedding / np.linalg.norm(test_embedding)
        
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
               (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 10
        """
        
        params = [test_embedding.tolist(), test_embedding.tolist()]
        
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="Vector Similarity Only")

def test_source_date_combination():
    """Test 8: Source + Date filters."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    WHERE doctrove_source IN ('openalex','randpub','extpub','aipickle') 
    AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
    LIMIT 10
    """
    return execute_query_directly(query, [], "Source + Date Filters")

def test_source_date_2d_combination():
    """Test 9: Source + Date + 2D embedding filters."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    WHERE doctrove_source IN ('openalex','randpub','extpub','aipickle') 
    AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
    AND (doctrove_embedding_2d IS NOT NULL)
    LIMIT 10
    """
    return execute_query_directly(query, [], "Source + Date + 2D Embedding")

def test_source_date_2d_bbox_combination():
    """Test 10: Source + Date + 2D embedding + Bounding box filters."""
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
    FROM doctrove_papers dp
    WHERE doctrove_source IN ('openalex','randpub','extpub','aipickle') 
    AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')
    AND (doctrove_embedding_2d IS NOT NULL)
    AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -0.932099066874233), point(20.666694546883626, 10.207678519388882))
    LIMIT 10
    """
    return execute_query_directly(query, [], "Source + Date + 2D + Bounding Box")

def test_full_complex_query():
    """Test 11: The full complex query that was hanging."""
    def operation():
        # Generate test embedding
        test_embedding = np.random.randn(1536).astype(np.float32)
        test_embedding = test_embedding / np.linalg.norm(test_embedding)
        
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source, dp.doctrove_primary_date, dp.doctrove_embedding_2d, 
               (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
        FROM doctrove_papers dp
        WHERE (doctrove_source IN ('openalex','randpub','extpub','aipickle') AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31'))
        AND (doctrove_embedding_2d IS NOT NULL)
        AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
        AND dp.doctrove_embedding IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 100
        """
        
        params = [test_embedding.tolist(), test_embedding.tolist()]
        
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=30, test_name="FULL COMPLEX QUERY")

def main():
    """Run systematic filter combination tests."""
    logger.info("🔬 Starting systematic filter combination testing...")
    logger.info("=" * 80)
    
    tests = [
        ("Basic Query", test_basic_query),
        ("Embedding Filter", test_embedding_filter),
        ("2D Embedding Filter", test_2d_embedding_filter),
        ("Source Filter", test_source_filter),
        ("Date Filter", test_date_filter),
        ("Bounding Box Filter", test_bbox_filter),
        ("Vector Similarity", test_vector_similarity),
        ("Source + Date", test_source_date_combination),
        ("Source + Date + 2D", test_source_date_2d_combination),
        ("Source + Date + 2D + BBox", test_source_date_2d_bbox_combination),
        ("FULL COMPLEX QUERY", test_full_complex_query),
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
    logger.info("SYSTEMATIC TEST SUMMARY")
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
    else:
        logger.info("✅ All individual filter tests passed!")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)






