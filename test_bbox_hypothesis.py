#!/usr/bin/env python3
"""
Test Hypothesis: Bbox is the only filter that can't be combined with embeddings
If true, we can work around by disabling bbox when similarity is active
"""

import os
import sys
import time
import signal
import logging
from typing import List, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv('/opt/arxivscope/.env.local')

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DOCTROVE_DB_HOST', 'localhost'),
        port=os.getenv('DOCTROVE_DB_PORT', '5432'),
        database=os.getenv('DOCTROVE_DB_NAME', 'doctrove'),
        user=os.getenv('DOCTROVE_DB_USER', 'postgres'),
        password=os.getenv('DOCTROVE_DB_PASSWORD', 'postgres')
    )

# Test timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out")

def run_test_with_timeout(test_func, timeout_seconds=10):
    """Run a test with timeout protection"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = test_func()
        signal.alarm(0)  # Cancel the alarm
        return result
    except TimeoutError:
        logger.error(f"❌ Test timed out after {timeout_seconds} seconds")
        return False
    except Exception as e:
        signal.alarm(0)  # Cancel the alarm
        logger.error(f"❌ Test failed with error: {e}")
        return False

def get_test_embedding():
    """Get a real embedding from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get a real embedding from the database
    cursor.execute("""
        SELECT doctrove_embedding 
        FROM doctrove_papers 
        WHERE doctrove_embedding IS NOT NULL 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        # Convert string representation to list
        embedding_str = result[0]
        if isinstance(embedding_str, str):
            # Remove brackets and split by comma
            embedding_str = embedding_str.strip('[]')
            embedding = [float(x.strip()) for x in embedding_str.split(',')]
        else:
            embedding = list(embedding_str)
        return embedding
    else:
        # Fallback: generate random embedding
        return [0.1] * 1536

def test_similarity_only():
    """Test: Similarity only (should work)"""
    logger.info("🧪 Testing: Similarity Only")
    
    def _test():
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        embedding = get_test_embedding()
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
               1 - (dp.doctrove_embedding <=> %s::vector) AS similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 5;
        """
        
        cursor.execute(query, (embedding_str, embedding_str))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Similarity only: {len(results)} results")
        return True
    
    return run_test_with_timeout(_test, 10)

def test_similarity_source():
    """Test: Similarity + Source filter (should work)"""
    logger.info("🧪 Testing: Similarity + Source")
    
    def _test():
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        embedding = get_test_embedding()
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
               1 - (dp.doctrove_embedding <=> %s::vector) AS similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding IS NOT NULL
          AND dp.doctrove_source = 'aipickle'
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 5;
        """
        
        cursor.execute(query, (embedding_str, embedding_str))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Similarity + Source: {len(results)} results")
        return True
    
    return run_test_with_timeout(_test, 10)

def test_similarity_date():
    """Test: Similarity + Date filter (should work)"""
    logger.info("🧪 Testing: Similarity + Date")
    
    def _test():
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        embedding = get_test_embedding()
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
               1 - (dp.doctrove_embedding <=> %s::vector) AS similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding IS NOT NULL
          AND dp.doctrove_primary_date BETWEEN '2020-01-01' AND '2024-12-31'
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 5;
        """
        
        cursor.execute(query, (embedding_str, embedding_str))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Similarity + Date: {len(results)} results")
        return True
    
    return run_test_with_timeout(_test, 10)

def test_similarity_2d():
    """Test: Similarity + 2D embedding filter (should work)"""
    logger.info("🧪 Testing: Similarity + 2D Embedding")
    
    def _test():
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        embedding = get_test_embedding()
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
               1 - (dp.doctrove_embedding <=> %s::vector) AS similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding IS NOT NULL
          AND dp.doctrove_embedding_2d IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 5;
        """
        
        cursor.execute(query, (embedding_str, embedding_str))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Similarity + 2D: {len(results)} results")
        return True
    
    return run_test_with_timeout(_test, 10)

def test_similarity_bbox():
    """Test: Similarity + Bbox filter (should hang - this is our problem)"""
    logger.info("🧪 Testing: Similarity + Bbox (EXPECTED TO HANG)")
    
    def _test():
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        embedding = get_test_embedding()
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        # Small bbox to test
        bbox = (2.0, -8.0, 20.0, 10.0)
        
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
               1 - (dp.doctrove_embedding <=> %s::vector) AS similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding IS NOT NULL
          AND dp.doctrove_embedding_2d IS NOT NULL
          AND dp.doctrove_embedding_2d <@ box(point(%s, %s), point(%s, %s))
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 5;
        """
        
        cursor.execute(query, (embedding_str, bbox[0], bbox[1], bbox[2], bbox[3], embedding_str))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Similarity + Bbox: {len(results)} results")
        return True
    
    return run_test_with_timeout(_test, 10)

def test_bbox_only():
    """Test: Bbox only (should work)"""
    logger.info("🧪 Testing: Bbox Only")
    
    def _test():
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        bbox = (2.0, -8.0, 20.0, 10.0)
        
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding_2d IS NOT NULL
          AND dp.doctrove_embedding_2d <@ box(point(%s, %s), point(%s, %s))
        LIMIT 5;
        """
        
        cursor.execute(query, (bbox[0], bbox[1], bbox[2], bbox[3]))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Bbox only: {len(results)} results")
        return True
    
    return run_test_with_timeout(_test, 10)

def main():
    logger.info("🔬 Testing Bbox Hypothesis")
    logger.info("🎯 Goal: Verify bbox is the only filter that can't combine with similarity")
    logger.info("⏰ Timeout: 10 seconds per test")
    logger.info("=" * 60)
    
    results = {}
    
    # Test individual filters with similarity
    results['similarity_only'] = test_similarity_only()
    results['similarity_source'] = test_similarity_source()
    results['similarity_date'] = test_similarity_date()
    results['similarity_2d'] = test_similarity_2d()
    results['similarity_bbox'] = test_similarity_bbox()  # This should fail/timeout
    results['bbox_only'] = test_bbox_only()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESULTS SUMMARY")
    logger.info("=" * 60)
    
    working_combinations = []
    failing_combinations = []
    
    for test_name, success in results.items():
        if success:
            working_combinations.append(test_name)
            logger.info(f"✅ {test_name}: WORKING")
        else:
            failing_combinations.append(test_name)
            logger.info(f"❌ {test_name}: FAILING/HANGING")
    
    logger.info(f"\n🎯 HYPOTHESIS TEST:")
    if len(failing_combinations) == 1 and 'similarity_bbox' in failing_combinations:
        logger.info("✅ CONFIRMED: Bbox is the only filter that can't combine with similarity!")
        logger.info("💡 WORKAROUND: Disable bbox when similarity is active")
    else:
        logger.info("❌ HYPOTHESIS REJECTED: Multiple filters cause issues")
        logger.info(f"   Failing combinations: {failing_combinations}")
    
    logger.info(f"\n📈 Working: {len(working_combinations)}/{len(results)}")
    logger.info(f"📉 Failing: {len(failing_combinations)}/{len(results)}")

if __name__ == "__main__":
    main()
