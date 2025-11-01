#!/usr/bin/env python3
"""
Test GPT5's recommended two-stage query approach.
This should eliminate the hanging issue by doing spatial prefiltering first.
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

def test_gpt5_two_stage_query():
    """Test GPT5's recommended two-stage query with MATERIALIZED CTE."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # GPT5's two-stage query with MATERIALIZED CTE
                query = """
                WITH pre AS MATERIALIZED (
                  SELECT dp.doctrove_paper_id, dp.doctrove_embedding
                  FROM doctrove_papers dp
                  WHERE dp.doctrove_embedding IS NOT NULL
                    AND dp.doctrove_source IN ('openalex','randpub','extpub','aipickle')
                    AND dp.doctrove_primary_date BETWEEN DATE '2000-01-01' AND DATE '2025-12-31'
                    AND dp.doctrove_embedding_2d IS NOT NULL
                    AND dp.doctrove_embedding_2d <@ box(
                          point(2.2860022533483075,-7.932099066874233),
                          point(20.666694546883626,10.207678519388882)
                        )
                  -- Optional: bias toward the bbox center so the cap keeps the most relevant
                  ORDER BY dp.doctrove_embedding_2d <-> point(11.4763484, 1.1377897)  -- (cx, cy)
                  LIMIT 50000   -- tune: 20k–100k commonly works well
                )
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
                       dp.doctrove_primary_date, dp.doctrove_embedding_2d,
                       1 - (dp.doctrove_embedding <=> %s) AS similarity_score
                FROM pre p
                JOIN doctrove_papers dp USING (doctrove_paper_id)
                ORDER BY dp.doctrove_embedding <=> %s
                LIMIT 5
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="GPT5 Two-Stage Query")

def test_gpt5_two_stage_no_center_bias():
    """Test GPT5's two-stage query without center bias."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # GPT5's two-stage query without center bias
                query = """
                WITH pre AS MATERIALIZED (
                  SELECT dp.doctrove_paper_id, dp.doctrove_embedding
                  FROM doctrove_papers dp
                  WHERE dp.doctrove_embedding IS NOT NULL
                    AND dp.doctrove_source IN ('openalex','randpub','extpub','aipickle')
                    AND dp.doctrove_primary_date BETWEEN DATE '2000-01-01' AND DATE '2025-12-31'
                    AND dp.doctrove_embedding_2d IS NOT NULL
                    AND dp.doctrove_embedding_2d <@ box(
                          point(2.2860022533483075,-7.932099066874233),
                          point(20.666694546883626,10.207678519388882)
                        )
                  LIMIT 50000   -- tune: 20k–100k commonly works well
                )
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
                       dp.doctrove_primary_date, dp.doctrove_embedding_2d,
                       1 - (dp.doctrove_embedding <=> %s) AS similarity_score
                FROM pre p
                JOIN doctrove_papers dp USING (doctrove_paper_id)
                ORDER BY dp.doctrove_embedding <=> %s
                LIMIT 5
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="GPT5 Two-Stage (No Center Bias)")

def test_smaller_cap():
    """Test with a smaller cap to see if it's faster."""
    test_embedding = generate_test_embedding()
    
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Smaller cap (10k instead of 50k)
                query = """
                WITH pre AS MATERIALIZED (
                  SELECT dp.doctrove_paper_id, dp.doctrove_embedding
                  FROM doctrove_papers dp
                  WHERE dp.doctrove_embedding IS NOT NULL
                    AND dp.doctrove_source IN ('openalex','randpub','extpub','aipickle')
                    AND dp.doctrove_primary_date BETWEEN DATE '2000-01-01' AND DATE '2025-12-31'
                    AND dp.doctrove_embedding_2d IS NOT NULL
                    AND dp.doctrove_embedding_2d <@ box(
                          point(2.2860022533483075,-7.932099066874233),
                          point(20.666694546883626,10.207678519388882)
                        )
                  LIMIT 10000   -- Smaller cap
                )
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
                       dp.doctrove_primary_date, dp.doctrove_embedding_2d,
                       1 - (dp.doctrove_embedding <=> %s) AS similarity_score
                FROM pre p
                JOIN doctrove_papers dp USING (doctrove_paper_id)
                ORDER BY dp.doctrove_embedding <=> %s
                LIMIT 5
                """
                
                params = [test_embedding.tolist(), test_embedding.tolist()]
                cur.execute(query, params)
                results = cur.fetchall()
                return len(results)
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=15, test_name="GPT5 Two-Stage (Smaller Cap)")

def test_measure_prefilter_size():
    """Measure the prefilter size to understand the dataset."""
    def operation():
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Measure prefilter size
                query = """
                SELECT count(*) as prefilter_count
                FROM doctrove_papers
                WHERE doctrove_embedding IS NOT NULL
                  AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
                  AND doctrove_primary_date BETWEEN DATE '2000-01-01' AND DATE '2025-12-31'
                  AND doctrove_embedding_2d IS NOT NULL
                  AND doctrove_embedding_2d <@ box(
                        point(2.2860022533483075,-7.932099066874233),
                        point(20.666694546883626,10.207678519388882)
                      )
                """
                
                cur.execute(query)
                result = cur.fetchone()
                return result['prefilter_count']
        finally:
            conn.close()
    
    return safe_database_operation(operation, timeout_seconds=10, test_name="Measure Prefilter Size")

def main():
    """Test GPT5's two-stage query approach."""
    logger.info("🔬 Testing GPT5's Two-Stage Query Approach")
    logger.info("🎯 Goal: Eliminate hanging with spatial prefiltering")
    logger.info("⏰ Timeout: 15 seconds per test")
    logger.info("=" * 60)
    
    tests = [
        ("Measure Prefilter Size", test_measure_prefilter_size),
        ("GPT5 Two-Stage Query", test_gpt5_two_stage_query),
        ("GPT5 Two-Stage (No Center Bias)", test_gpt5_two_stage_no_center_bias),
        ("GPT5 Two-Stage (Smaller Cap)", test_smaller_cap),
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
    logger.info("GPT5 TWO-STAGE TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        count = result['result_count']
        logger.info(f"{test_name:30} | {status:8} | {duration:6.2f}s | {count:8d} results")
    
    # Analysis
    logger.info(f"\n{'='*60}")
    logger.info("ANALYSIS")
    logger.info(f"{'='*60}")
    
    if 'Measure Prefilter Size' in results and results['Measure Prefilter Size']['success']:
        prefilter_count = results['Measure Prefilter Size']['result_count']
        logger.info(f"📊 Prefilter size: {prefilter_count:,} records")
        if prefilter_count > 100000:
            logger.info("⚠️  Large prefilter - the cap will matter a lot")
        elif prefilter_count > 50000:
            logger.info("⚠️  Medium prefilter - cap will help")
        else:
            logger.info("✅ Small prefilter - cap is just a guardrail")
    
    working_tests = [name for name, result in results.items() if result['success'] and 'Two-Stage' in name]
    if working_tests:
        logger.info(f"✅ Working two-stage approaches: {', '.join(working_tests)}")
        logger.info("🎯 GPT5's approach works! No more hanging!")
    else:
        logger.error("❌ Two-stage approaches failed - need to investigate further")
    
    return len(working_tests) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



