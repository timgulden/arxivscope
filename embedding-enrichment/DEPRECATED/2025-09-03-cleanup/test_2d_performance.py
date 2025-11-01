#!/usr/bin/env python3
"""
Performance Test for Functional 2D Embedding Enrichment

This script tests the processing speed of our functional 2D enrichment
by processing a small batch of real papers from the database.
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
sys.path.append(os.path.dirname(__file__))

from functional_embedding_2d_enrichment import create_functional_2d_enrichment, create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_test_papers(connection_factory, limit: int = 100) -> List[Dict[str, Any]]:
    """Get a small batch of papers that need 2D embeddings for testing."""
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_abstract,
                       dp.doctrove_embedding
                FROM doctrove_papers dp
                WHERE dp.doctrove_embedding_2d IS NULL
                AND dp.doctrove_embedding IS NOT NULL
                AND dp.doctrove_title IS NOT NULL
                AND dp.doctrove_title != ''
                ORDER BY dp.doctrove_paper_id
                LIMIT %s
            """, (limit,))
            
            papers = []
            for row in cur.fetchall():
                paper = {
                    'doctrove_paper_id': row[0],
                    'doctrove_title': row[1],
                    'doctrove_abstract': row[2],
                    'doctrove_embedding': row[3]
                }
                papers.append(paper)
            return papers

def test_performance():
    """Test the performance of functional 2D enrichment."""
    logger.info("Starting 2D enrichment performance test...")
    
    try:
        # Create functional enrichment
        enrichment = create_functional_2d_enrichment()
        connection_factory = create_connection_factory()
        
        # Get test papers
        test_papers = get_test_papers(connection_factory, limit=50)
        logger.info(f"Retrieved {len(test_papers)} test papers")
        
        if not test_papers:
            logger.warning("No papers available for testing")
            return
        
        # Test processing speed
        logger.info(f"Processing {len(test_papers)} papers for 2D embeddings...")
        start_time = time.time()
        
        # Process papers using functional enrichment
        result_count = enrichment.run_enrichment(test_papers)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calculate performance metrics
        papers_per_second = len(test_papers) / processing_time if processing_time > 0 else 0
        papers_per_minute = papers_per_second * 60
        
        logger.info("=" * 50)
        logger.info("PERFORMANCE RESULTS")
        logger.info("=" * 50)
        logger.info(f"Papers processed: {result_count}/{len(test_papers)}")
        logger.info(f"Processing time: {processing_time:.2f} seconds")
        logger.info(f"Speed: {papers_per_second:.2f} papers/second")
        logger.info(f"Speed: {papers_per_minute:.0f} papers/minute")
        logger.info(f"Speed: {papers_per_minute * 60:.0f} papers/hour")
        logger.info("=" * 50)
        
        # Estimate time for remaining papers
        remaining_papers = 27500  # Approximate from our earlier query
        estimated_hours = remaining_papers / (papers_per_minute * 60) if papers_per_minute > 0 else 0
        
        logger.info(f"Estimated time to process {remaining_papers:,} remaining papers:")
        logger.info(f"  {estimated_hours:.1f} hours")
        logger.info(f"  {estimated_hours / 24:.1f} days")
        
        return {
            'papers_processed': result_count,
            'total_papers': len(test_papers),
            'processing_time': processing_time,
            'papers_per_second': papers_per_second,
            'papers_per_minute': papers_per_minute,
            'estimated_hours_for_remaining': estimated_hours
        }
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return None

if __name__ == "__main__":
    logger.info("Starting 2D enrichment performance test...")
    result = test_performance()
    
    if result:
        logger.info("Performance test completed successfully!")
        logger.info(f"Functional 2D enrichment can process {result['papers_per_minute']:.0f} papers/minute")
    else:
        logger.error("Performance test failed!")
        sys.exit(1)

