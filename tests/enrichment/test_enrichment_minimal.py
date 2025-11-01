#!/usr/bin/env python3
"""
Minimal test to isolate the tuple index error in the functional enrichment script.
"""

import sys
import os
import logging

# Add paths for imports
sys.path.append('../doctrove-api')
sys.path.append('.')

from db import create_connection_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_query():
    """Test just the database query part to isolate the issue."""
    logger.info("🧪 Testing database query in isolation...")
    
    try:
        connection_factory = create_connection_factory()
        
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Test 1: Get paper IDs (this was working)
                logger.info("Test 1: Getting paper IDs...")
                id_query = """
                    SELECT om.doctrove_paper_id
                    FROM openalex_metadata om
                    JOIN doctrove_papers dp ON om.doctrove_paper_id = dp.doctrove_paper_id
                    WHERE dp.doctrove_source = 'openalex'
                      AND NOT EXISTS (
                        SELECT 1 FROM openalex_details_enrichment e 
                        WHERE e.doctrove_paper_id = om.doctrove_paper_id
                      )
                    LIMIT 3
                """
                cur.execute(id_query)
                paper_ids = [row[0] for row in cur.fetchall()]
                logger.info(f"✅ Test 1 passed: Found {len(paper_ids)} paper IDs")
                logger.info(f"Paper IDs: {paper_ids}")
                
                if not paper_ids:
                    logger.info("No papers found, stopping test")
                    return
                
                # Test 2: Fetch individual paper data (this was failing)
                logger.info("Test 2: Fetching individual paper data...")
                all_results = []
                
                # Test 2a: Try a simple query first
                logger.info("Test 2a: Simple query test...")
                try:
                    cur.execute("SELECT 1 as test")
                    result = cur.fetchone()
                    logger.info(f"✅ Simple query test passed: {result}")
                except Exception as e:
                    logger.error(f"❌ Simple query test failed: {e}")
                    raise
                
                # Test 2b: Try a basic metadata query
                logger.info("Test 2b: Basic metadata query test...")
                try:
                    cur.execute("SELECT COUNT(*) FROM openalex_metadata")
                    result = cur.fetchone()
                    logger.info(f"✅ Basic metadata query test passed: {result}")
                except Exception as e:
                    logger.error(f"❌ Basic metadata query test failed: {e}")
                    raise
                
                # Test 2c: Try the problematic query with a hardcoded ID
                logger.info("Test 2c: Hardcoded ID query test...")
                try:
                    cur.execute("""
                        SELECT om.doctrove_paper_id, om.openalex_raw_data
                        FROM openalex_metadata om
                        WHERE om.doctrove_paper_id = '6db9c04e-8caf-4d9e-a8af-4111fc36f01e'
                          AND om.openalex_raw_data IS NOT NULL
                          AND om.openalex_raw_data != '{}'
                          AND om.openalex_raw_data LIKE '%authorships%'
                    """)
                    result = cur.fetchone()
                    if result:
                        logger.info(f"✅ Hardcoded query test passed: {result[0]}")
                    else:
                        logger.info("⚠️  Hardcoded query returned no data")
                except Exception as e:
                    logger.error(f"❌ Hardcoded query test failed: {e}")
                    raise
                
                # Test 2d: Now try with parameterized query
                logger.info("Test 2d: Parameterized query test...")
                for i, paper_id in enumerate(paper_ids):
                    logger.info(f"Processing paper {i+1}/{len(paper_ids)}: {paper_id}")
                    logger.info(f"Paper ID type: {type(paper_id)}, value: {repr(paper_id)}")
                    
                    try:
                        # Check if paper_id is what we expect
                        if paper_id is None:
                            logger.error(f"Paper ID is None for paper {i+1}")
                            continue
                        
                        # Ensure paper_id is a string
                        paper_id_str = str(paper_id) if paper_id is not None else None
                        logger.info(f"Paper ID string: {repr(paper_id_str)}")
                        
                        # Test different parameter formats
                        logger.info("Testing parameter format 1: tuple with single element")
                        cur.execute("""
                            SELECT om.doctrove_paper_id, om.openalex_raw_data
                            FROM openalex_metadata om
                            WHERE om.doctrove_paper_id = %s
                              AND om.openalex_raw_data IS NOT NULL
                              AND om.openalex_raw_data != '{}'
                              AND om.openalex_raw_data LIKE '%authorships%'
                        """, (paper_id_str,))
                        
                        result = cur.fetchone()
                        if result:
                            all_results.append(result)
                            logger.info(f"✅ Paper {i+1} data fetched successfully with tuple format")
                        else:
                            logger.info(f"⚠️  Paper {i+1} returned no data")
                            
                    except Exception as e:
                        logger.error(f"❌ Error fetching paper {i+1}: {e}")
                        logger.error(f"Paper ID: {paper_id}")
                        logger.error(f"Paper ID type: {type(paper_id)}")
                        logger.error(f"Paper ID repr: {repr(paper_id)}")
                        
                        # Try alternative parameter format
                        logger.info("Trying alternative parameter format: list")
                        try:
                            cur.execute("""
                                SELECT om.doctrove_paper_id, om.openalex_raw_data
                                FROM openalex_metadata om
                                WHERE om.doctrove_paper_id = %s
                                  AND om.openalex_raw_data IS NOT NULL
                                  AND om.openalex_raw_data != '{}'
                                  AND om.openalex_raw_data LIKE '%authorships%'
                            """, [paper_id_str])
                            
                            result = cur.fetchone()
                            if result:
                                all_results.append(result)
                                logger.info(f"✅ Paper {i+1} data fetched successfully with list format")
                            else:
                                logger.info(f"⚠️  Paper {i+1} returned no data with list format")
                                
                        except Exception as e2:
                            logger.error(f"❌ Alternative format also failed: {e2}")
                            raise e  # Re-raise the original error
                
                logger.info(f"✅ Test 2 passed: Fetched data for {len(all_results)} papers")
                
                # Test 3: Check data structure
                if all_results:
                    logger.info("Test 3: Checking data structure...")
                    for i, result in enumerate(all_results):
                        logger.info(f"Result {i+1}: type={type(result)}, length={len(result) if hasattr(result, '__len__') else 'no length'}")
                        logger.info(f"Result {i+1} content: {result}")
                    
                    logger.info("✅ Test 3 passed: Data structure verified")
                
        logger.info("🎉 All database tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting minimal enrichment test")
    
    if test_database_query():
        logger.info("✅ All tests passed - the issue is likely in the functional processing logic")
    else:
        logger.error("❌ Tests failed - found the root cause")
        sys.exit(1)
