#!/usr/bin/env python3
"""
Minimal test to isolate the hanging issue in the functional version.
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

def test_simple_query():
    """Test a simple query to see if the issue is database-related."""
    logger.info("🧪 Testing simple database query...")
    
    try:
        connection_factory = create_connection_factory()
        
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Simple query first
                cur.execute("SELECT COUNT(*) FROM openalex_details_enrichment")
                count = cur.fetchone()[0]
                logger.info(f"✅ Simple query works: {count} records in enrichment table")
                
                # Test the problematic part - getting paper IDs
                cur.execute("""
                    SELECT om.doctrove_paper_id
                    FROM openalex_metadata om
                    JOIN doctrove_papers dp ON om.doctrove_paper_id = dp.doctrove_paper_id
                    WHERE dp.doctrove_source = 'openalex'
                      AND om.doctrove_paper_id::text NOT IN (
                        SELECT doctrove_paper_id::text FROM openalex_details_enrichment
                      )
                    LIMIT 5
                """)
                paper_ids = cur.fetchall()
                logger.info(f"✅ Paper ID query works: Found {len(paper_ids)} papers")
                
                if paper_ids:
                    # Test the ANY clause that might be problematic
                    test_ids = [row[0] for row in paper_ids[:3]]
                    cur.execute("""
                        SELECT om.doctrove_paper_id, LENGTH(om.openalex_raw_data::text)
                        FROM openalex_metadata om
                        WHERE om.doctrove_paper_id = ANY(%s)
                    """, (test_ids,))
                    results = cur.fetchall()
                    logger.info(f"✅ ANY clause works: Found {len(results)} results")
                
        logger.info("🎉 All database queries work fine")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def test_json_parsing():
    """Test JSON parsing that might be causing issues."""
    logger.info("🧪 Testing JSON parsing...")
    
    try:
        connection_factory = create_connection_factory()
        
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Get one paper's raw data
                cur.execute("""
                    SELECT om.openalex_raw_data
                    FROM openalex_metadata om
                    WHERE om.openalex_raw_data IS NOT NULL
                      AND om.openalex_raw_data != '{}'
                    LIMIT 1
                """)
                result = cur.fetchone()
                
                if result:
                    import json
                    raw_data_str = result[0]
                    raw_data = json.loads(raw_data_str)
                    logger.info(f"✅ JSON parsing works: {len(raw_data.keys())} keys found")
                    
                    # Test authorship processing
                    authorships = raw_data.get('authorships', [])
                    logger.info(f"✅ Authorship extraction works: {len(authorships)} authorships")
                    
        logger.info("🎉 JSON parsing works fine")
        return True
        
    except Exception as e:
        logger.error(f"❌ JSON parsing test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting minimal functional test")
    
    # Test database queries
    if not test_simple_query():
        sys.exit(1)
    
    # Test JSON parsing
    if not test_json_parsing():
        sys.exit(1)
    
    logger.info("✅ All tests passed - the issue is likely in the functional processing logic")

