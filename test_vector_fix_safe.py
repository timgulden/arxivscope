#!/usr/bin/env python3
"""
Safe test script for vector format fixes.
Uses timeout protection and proper error handling to prevent terminal hanging.
"""

import os
import sys
import time
import signal
import logging
import numpy as np
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))

# Import the business logic
from business_logic import get_embedding_for_text, build_optimized_query_v2, build_count_query_v2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def timeout_handler(signum, frame):
    """Handle timeout signal."""
    raise TimeoutError("Operation timed out")

def safe_database_operation(operation_func, timeout_seconds=30):
    """Execute database operation with timeout protection."""
    # Set up timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = operation_func()
        signal.alarm(0)  # Cancel timeout
        return result
    except TimeoutError:
        logger.error(f"❌ Operation timed out after {timeout_seconds} seconds")
        return None
    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        return None
    finally:
        signal.signal(signal.SIGALRM, old_handler)  # Restore original handler

def test_embedding_generation():
    """Test embedding generation without database interaction."""
    logger.info("🧪 Testing embedding generation...")
    
    try:
        # Test embedding generation
        search_text = "machine learning algorithms"
        embedding = get_embedding_for_text(search_text, "abstract")
        
        if embedding is None:
            logger.error("❌ Failed to generate embedding")
            return False
            
        # Check embedding properties
        if hasattr(embedding, 'shape'):
            logger.info(f"✅ Embedding shape: {embedding.shape}")
            if embedding.shape[0] != 1536:
                logger.error(f"❌ Wrong embedding dimension: {embedding.shape[0]} (expected 1536)")
                return False
        else:
            logger.error("❌ Embedding is not a numpy array")
            return False
            
        # Test .tolist() conversion
        embedding_list = embedding.tolist()
        if len(embedding_list) != 1536:
            logger.error(f"❌ Wrong list length: {len(embedding_list)} (expected 1536)")
            return False
            
        logger.info(f"✅ Embedding conversion successful: {len(embedding_list)} dimensions")
        logger.info(f"✅ First 5 values: {embedding_list[:5]}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        return False

def test_query_building():
    """Test query building without database execution."""
    logger.info("🧪 Testing query building...")
    
    try:
        # Test parameters - use the correct function signature
        fields = ["doctrove_title", "doctrove_authors"]
        search_text = "machine learning"
        limit = 10
        
        # Test query building with correct parameters
        query_result = build_optimized_query_v2(
            fields=fields,
            search_text=search_text,
            limit=limit
        )
        
        if query_result is None:
            logger.error("❌ Query building failed")
            return False
            
        logger.info(f"✅ Query built successfully")
        logger.info(f"✅ Query: {query_result.query[:200]}...")
        logger.info(f"✅ Parameters count: {len(query_result.params)}")
        
        # Check if vector parameter is properly formatted
        if query_result.params:
            # Check if we have embedding parameters
            embedding_params = [p for p in query_result.params if isinstance(p, list) and len(p) == 1536]
            if embedding_params:
                logger.info("✅ Vector parameter properly formatted (1536 dimensions)")
            else:
                logger.info("ℹ️  No vector parameters in this query (expected for non-semantic queries)")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Query building failed: {e}")
        return False

def test_database_connection():
    """Test database connection with timeout protection."""
    logger.info("🧪 Testing database connection...")
    
    def db_operation():
        # Import database config
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        
        # Test connection
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            
        conn.close()
        return result[0] == 1
    
    result = safe_database_operation(db_operation, timeout_seconds=10)
    if result:
        logger.info("✅ Database connection successful")
        return True
    else:
        logger.error("❌ Database connection failed or timed out")
        return False

def test_simple_query():
    """Test a simple query with timeout protection - avoiding COUNT queries."""
    logger.info("🧪 Testing simple database query...")
    
    def db_operation():
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Simple query with LIMIT - avoids COUNT on 17M records
            cur.execute("SELECT doctrove_paper_id, doctrove_title FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL LIMIT 5")
            results = cur.fetchall()
            
        conn.close()
        return len(results)
    
    result = safe_database_operation(db_operation, timeout_seconds=15)
    if result is not None:
        logger.info(f"✅ Simple query successful: {result} papers returned")
        return True
    else:
        logger.error("❌ Simple query failed or timed out")
        return False

def test_vector_similarity_query():
    """Test vector similarity query following the pattern from test_fixed_query_simple.py."""
    logger.info("🧪 Testing vector similarity query...")
    
    def db_operation():
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        import numpy as np
        
        # Generate a proper 1536-dimensional test embedding (same as your test script)
        test_embedding = np.random.randn(1536).astype(np.float32)
        test_embedding = test_embedding / np.linalg.norm(test_embedding)
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        with conn.cursor() as cur:
            # Simple vector similarity query (same pattern as your test script)
            simple_query = """
            SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
                   (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
            FROM doctrove_papers dp
            WHERE dp.doctrove_embedding IS NOT NULL
            ORDER BY dp.doctrove_embedding <=> %s::vector
            LIMIT 10
            """
            
            parameters = [test_embedding.tolist(), test_embedding.tolist()]
            cur.execute(simple_query, parameters)
            results = cur.fetchall()
            
        conn.close()
        return len(results)
    
    result = safe_database_operation(db_operation, timeout_seconds=30)
    if result is not None:
        logger.info(f"✅ Vector similarity query successful: {result} papers returned")
        return True
    else:
        logger.error("❌ Vector similarity query failed or timed out")
        return False

def main():
    """Run all tests with proper error handling."""
    logger.info("🚀 Starting safe vector fix tests...")
    
    tests = [
        ("Embedding Generation", test_embedding_generation),
        ("Query Building", test_query_building),
        ("Database Connection", test_database_connection),
        ("Simple Query", test_simple_query),
        ("Vector Similarity Query", test_vector_similarity_query)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Vector fixes appear to be working.")
    else:
        logger.error("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
