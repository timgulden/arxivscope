#!/usr/bin/env python3
"""
Test script to process the remaining 531 papers with institution data.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory
from openalex_country_enrichment_institution_cache import InstitutionCachedOpenAlexCountryEnrichment

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_remaining_papers_with_institution_data():
    """Get papers that have institution data but no country enrichment."""
    conn_factory = create_connection_factory()
    
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT dp.doctrove_paper_id, dp.doctrove_source
                FROM doctrove_papers dp
                JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
                WHERE dp.doctrove_source = 'openalex'
                  AND dp.doctrove_paper_id NOT IN (
                    SELECT doctrove_paper_id FROM openalex_country_enrichment
                  )
                  AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements(om.openalex_raw_data::jsonb->'authorships') as authorship
                    WHERE (authorship ? 'institutions' AND jsonb_array_length(authorship->'institutions') > 0)
                       OR (authorship ? 'countries' AND jsonb_array_length(authorship->'countries') > 0)
                       OR (authorship ? 'raw_affiliation_strings' AND jsonb_array_length(authorship->'raw_affiliation_strings') > 0)
                  )
                ORDER BY dp.doctrove_paper_id
            ''')
            papers = []
            for row in cur.fetchall():
                papers.append({
                    'doctrove_paper_id': row[0],
                    'doctrove_source': row[1]
                })
            return papers

def test_remaining_papers():
    """Test processing the remaining papers with institution data."""
    logger.debug("Getting remaining papers with institution data...")
    papers = get_remaining_papers_with_institution_data()
    logger.debug(f"Found {len(papers)} papers to process")
    
    if not papers:
        logger.debug("No papers to process")
        return
    
    # Create enrichment service
    enrichment = InstitutionCachedOpenAlexCountryEnrichment()
    
    # Create table if needed
    enrichment.create_table_if_needed()
    
    # Process papers in batches
    batch_size = 50
    total_processed = 0
    
    for i in range(0, len(papers), batch_size):
        batch_papers = papers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(papers) + batch_size - 1) // batch_size
        
        logger.debug(f"Processing batch {batch_num}/{total_batches}: {len(batch_papers)} papers")
        
        try:
            # Process the batch
            results = enrichment.process_papers_with_institution_cache(batch_papers)
            
            if results:
                # Insert results
                inserted_count = enrichment.insert_results(results)
                total_processed += inserted_count
                logger.debug(f"Batch {batch_num}: Processed {len(results)} papers, inserted {inserted_count} records")
            else:
                logger.debug(f"Batch {batch_num}: No results generated")
                
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
            continue
    
    logger.debug(f"Completed processing: {total_processed} papers enriched")

if __name__ == "__main__":
    test_remaining_papers()
