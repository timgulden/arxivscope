#!/usr/bin/env python3
"""
Script to fix OpenAlex papers that have main records but no metadata records.
This handles the case where papers were inserted before metadata insertion was working.
"""

import logging
import sys
import os
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

from ingester import OpenAlexIngester
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_papers_without_metadata(ingester):
    """
    Find OpenAlex papers that don't have corresponding metadata records.
    
    Returns:
        List of (paper_id, source_id) tuples
    """
    with ingester.connection.cursor() as cur:
        cur.execute("""
            SELECT p.doctrove_paper_id, p.doctrove_source_id
            FROM doctrove_papers p
            LEFT JOIN openalex_metadata m ON p.doctrove_paper_id = m.doctrove_paper_id
            WHERE p.doctrove_source = 'openalex'
            AND m.doctrove_paper_id IS NULL
            ORDER BY p.doctrove_paper_id
        """)
        
        results = cur.fetchall()
        logger.info(f"Found {len(results)} OpenAlex papers without metadata")
        return results

def delete_papers_without_metadata(ingester, papers_to_delete):
    """
    Delete papers that don't have metadata (since we can't recreate the metadata).
    
    Args:
        ingester: OpenAlexIngester instance
        papers_to_delete: List of (paper_id, source_id) tuples
    """
    if not papers_to_delete:
        logger.info("No papers to delete")
        return
    
    logger.info(f"Deleting {len(papers_to_delete)} papers without metadata...")
    
    with ingester.connection.cursor() as cur:
        # Delete from enrichment_queue first (due to foreign key constraint)
        paper_ids = [paper[0] for paper in papers_to_delete]
        placeholders = ','.join(['%s'] * len(paper_ids))
        
        cur.execute(f"""
            DELETE FROM enrichment_queue 
            WHERE paper_id IN ({placeholders})
        """, paper_ids)
        
        # Delete from doctrove_papers
        cur.execute(f"""
            DELETE FROM doctrove_papers 
            WHERE doctrove_paper_id IN ({placeholders})
        """, paper_ids)
        
        ingester.connection.commit()
        logger.info(f"Successfully deleted {len(papers_to_delete)} papers")

def main():
    """Main function to fix missing metadata."""
    logger.info("Starting metadata cleanup for OpenAlex papers...")
    
    try:
        # Initialize ingester
        ingester = OpenAlexIngester()
        ingester.connect()
        
        # Find papers without metadata
        papers_without_metadata = find_papers_without_metadata(ingester)
        
        if papers_without_metadata:
            logger.warning(f"Found {len(papers_without_metadata)} papers without metadata")
            
            # Show some examples
            logger.info("Examples of papers without metadata:")
            for i, (paper_id, source_id) in enumerate(papers_without_metadata[:5]):
                logger.info(f"  {i+1}. {source_id} (ID: {paper_id})")
            
            if len(papers_without_metadata) > 5:
                logger.info(f"  ... and {len(papers_without_metadata) - 5} more")
            
            # Delete papers without metadata
            delete_papers_without_metadata(ingester, papers_without_metadata)
            
            logger.info("✅ Cleanup completed successfully!")
        else:
            logger.info("✅ All OpenAlex papers have metadata - no cleanup needed!")
        
        # Final check
        final_check = find_papers_without_metadata(ingester)
        if final_check:
            logger.error(f"❌ Still found {len(final_check)} papers without metadata after cleanup")
        else:
            logger.info("✅ Verification passed - all papers now have metadata")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise
    finally:
        if 'ingester' in locals():
            ingester.disconnect()

if __name__ == "__main__":
    main() 