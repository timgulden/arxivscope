#!/usr/bin/env python3
"""
Test ONLY similarity queries with LIMIT - no COUNT queries.
This tests if basic similarity search actually works.
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

def test_basic_connection():
    """Test 1: Basic database connection."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return result[0]
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=5, test_name="Basic Connection")

def test_simple_limit():
    """Test 2: Simple LIMIT query (no COUNT)."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT doctrove_paper_id FROM doctrove_papers LIMIT 5")
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=5, test_name="Simple LIMIT Query")

def test_embedding_limit():
    """Test 3: LIMIT query with embedding filter."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT doctrove_paper_id FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL LIMIT 5")
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=5, test_name="Embedding LIMIT Query")

def test_basic_similarity():
    """Test 4: Basic similarity query - the key test."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Very basic similarity query
                query = """
                SELECT doctrove_paper_id, doctrove_title
                FROM doctrove_papers
                WHERE doctrove_embedding IS NOT NULL
                ORDER BY doctrove_embedding <=> %s::vector
                LIMIT 5
                """
                
                params = [test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="Basic Similarity Query")

def test_similarity_with_score():
    """Test 5: Similarity query with score calculation."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Similarity query with score calculation
                query = """
                SELECT doctrove_paper_id, doctrove_title,
                       (1 - (doctrove_embedding <=> %s::vector)) as similarity_score
                FROM doctrove_papers
                WHERE doctrove_embedding IS NOT NULL
                ORDER BY doctrove_embedding <=> %s::vector
                LIMIT 5
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="Similarity with Score")

def main():
    """Test similarity queries with LIMIT only."""
    logger.info("🔬 Testing Similarity Queries with LIMIT Only")
    logger.info("🎯 Goal: Verify if basic similarity queries work")
    logger.info("⏰ Timeout: 5-15 seconds per test")
    logger.info("🚫 NO COUNT queries - only LIMIT")
    logger.info("=" * 60)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Simple LIMIT", test_simple_limit),
        ("Embedding LIMIT", test_embedding_limit),
        ("Basic Similarity", test_basic_similarity),
        ("Similarity with Score", test_similarity_with_score),
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
    logger.info("SIMILARITY TEST SUMMARY")
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
    
    if 'Basic Similarity' in results and results['Basic Similarity']['success']:
        logger.info("✅ Basic similarity queries DO work!")
        logger.info("🔍 The issue is likely with specific filter combinations")
    else:
        logger.error("❌ Basic similarity queries are hanging")
        logger.error("🔍 This suggests a fundamental pgvector issue")
    
    return all(result['success'] for result in results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



