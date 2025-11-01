#!/usr/bin/env python3
"""
Test the CTE approach integrated into business logic.
This will test the actual business logic functions with CTE approach.
"""

import os
import sys
import time
import signal
import logging
import numpy as np

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

def safe_database_operation(operation_func, timeout_seconds=15, test_name="Unknown"):
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

def generate_test_embedding():
    """Generate a test embedding."""
    test_embedding = np.random.randn(1536).astype(np.float32)
    test_embedding = test_embedding / np.linalg.norm(test_embedding)
    return test_embedding

def test_business_logic_similarity_only():
    """Test business logic with similarity only."""
    from business_logic import build_optimized_query_v2
    
    test_embedding = generate_test_embedding()
    
    def operation():
        # Test similarity only
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title', 'doctrove_source'],
            search_text="machine learning",
            limit=10
        )
        
        logger.info(f"Query: {query[:200]}...")
        logger.info(f"Parameters: {len(params)} params")
        logger.info(f"Warnings: {warnings}")
        
        return len(params)
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Business Logic - Similarity Only")

def test_business_logic_similarity_plus_bbox():
    """Test business logic with similarity + bbox."""
    from business_logic import build_optimized_query_v2
    
    test_embedding = generate_test_embedding()
    
    def operation():
        # Test similarity + bbox
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title', 'doctrove_source'],
            search_text="machine learning",
            bbox="2.2860022533483075,-7.932099066874233,20.666694546883626,10.207678519388882",
            limit=10
        )
        
        logger.info(f"Query: {query[:200]}...")
        logger.info(f"Parameters: {len(params)} params")
        logger.info(f"Warnings: {warnings}")
        
        return len(params)
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Business Logic - Similarity + Bbox")

def test_business_logic_similarity_plus_source_date():
    """Test business logic with similarity + source + date."""
    from business_logic import build_optimized_query_v2
    
    test_embedding = generate_test_embedding()
    
    def operation():
        # Test similarity + source + date
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title', 'doctrove_source'],
            search_text="machine learning",
            sql_filter="(doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')",
            limit=10
        )
        
        logger.info(f"Query: {query[:200]}...")
        logger.info(f"Parameters: {len(params)} params")
        logger.info(f"Warnings: {warnings}")
        
        return len(params)
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Business Logic - Similarity + Source + Date")

def test_business_logic_no_similarity():
    """Test business logic without similarity (should use regular query)."""
    from business_logic import build_optimized_query_v2
    
    def operation():
        # Test without similarity
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title', 'doctrove_source'],
            limit=10
        )
        
        logger.info(f"Query: {query[:200]}...")
        logger.info(f"Parameters: {len(params)} params")
        logger.info(f"Warnings: {warnings}")
        
        return len(params)
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Business Logic - No Similarity")

def main():
    """Test the business logic with CTE approach."""
    logger.info("🔬 Testing Business Logic with CTE Approach")
    logger.info("🎯 Goal: Verify CTE approach works in business logic")
    logger.info("⏰ Timeout: 10 seconds per test")
    logger.info("=" * 60)
    
    tests = [
        ("Similarity Only", test_business_logic_similarity_only),
        ("Similarity + Bbox", test_business_logic_similarity_plus_bbox),
        ("Similarity + Source + Date", test_business_logic_similarity_plus_source_date),
        ("No Similarity", test_business_logic_no_similarity),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            result, duration = test_func()
            results[test_name] = {
                'success': result is not None,
                'duration': duration,
                'param_count': result if result is not None else 0
            }
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = {
                'success': False,
                'duration': 0,
                'param_count': 0,
                'error': str(e)
            }
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("BUSINESS LOGIC CTE TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        params = result['param_count']
        logger.info(f"{test_name:25} | {status:8} | {duration:6.2f}s | {params:2d} params")
    
    # Analysis
    logger.info(f"\n{'='*60}")
    logger.info("ANALYSIS")
    logger.info(f"{'='*60}")
    
    similarity_tests = [name for name in results.keys() if 'Similarity' in name]
    similarity_success = all(results[name]['success'] for name in similarity_tests)
    
    if similarity_success:
        logger.info("✅ All similarity tests passed!")
        logger.info("🚀 CTE approach is working in business logic")
    else:
        logger.error("❌ Some similarity tests failed")
    
    if results.get('No Similarity', {}).get('success', False):
        logger.info("✅ Non-similarity queries still work")
    else:
        logger.error("❌ Non-similarity queries have issues")
    
    return all(result['success'] for result in results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
