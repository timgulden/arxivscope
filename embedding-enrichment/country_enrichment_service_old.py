#!/usr/bin/env python3
"""
OpenAlex Country Enrichment Service
Automatically processes papers that don't have country data, marking them as UNK if no data available.
Triggered by OpenAlex papers with NO country enrichment record (including UNK).
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from db import create_connection_factory

logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 1000  # Process 1K records at a time
MAX_RETRIES = 3

def get_papers_needing_country_enrichment(connection_factory, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get papers that need country enrichment.
    Returns papers where NO country enrichment record exists (not even UNK).
    
    Key insight: UNK = "We tried and found no country data" (valid result)
                 NULL = "We haven't tried yet" (needs processing)
    """
    query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_abstract
        FROM doctrove_papers dp
        JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
        LEFT JOIN openalex_enrichment_country ec ON dp.doctrove_paper_id = ec.doctrove_paper_id
        WHERE dp.doctrove_source = 'openalex'
        AND ec.doctrove_paper_id IS NULL  -- NO enrichment record exists (not even UNK)
        AND dp.doctrove_title IS NOT NULL
        AND dp.doctrove_title != ''
        ORDER BY dp.doctrove_paper_id
    """
    if limit:
        query += f" LIMIT {limit}"
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            papers = []
            for row in cur.fetchall():
                paper = {
                    'doctrove_paper_id': row[0],
                    'doctrove_title': row[1],
                    'doctrove_abstract': row[2]
                }
                papers.append(paper)
            return papers

def count_papers_needing_country_enrichment(connection_factory) -> int:
    """Count papers that need country enrichment."""
    query = """
        SELECT COUNT(*)
        FROM doctrove_papers dp
        JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
        LEFT JOIN openalex_enrichment_country ec ON dp.doctrove_paper_id = ec.doctrove_paper_id
        WHERE dp.doctrove_source = 'openalex'
        AND ec.doctrove_paper_id IS NULL  -- NO enrichment record exists
        AND dp.doctrove_title IS NOT NULL
        AND dp.doctrove_title != ''
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()[0]

def process_country_enrichment_for_papers(papers: List[Dict[str, Any]], connection_factory) -> List[Dict[str, Any]]:
    """
    Process country enrichment for a batch of papers.
    Returns papers with country data or UNK markers.
    """
    if not papers:
        return []
    
    # Import the enrichment logic
    from openalex_country_enrichment_optimized import create_optimized_enrichment
    
    try:
        # Create enrichment processor
        enrichment_processor = create_optimized_enrichment(connection_factory)
        
        # Process papers
        enrichment_results = enrichment_processor()
        
        # Filter results for our papers
        paper_ids = {p['doctrove_paper_id'] for p in papers}
        filtered_results = [r for r in enrichment_results if r.paper_id in paper_ids]
        
        return filtered_results
        
    except Exception as e:
        logger.error(f"Error processing country enrichment: {e}")
        return []

def mark_country_enrichment_failed(connection_factory, paper_id: str, failure_reason: str):
    """Mark country enrichment as failed to avoid re-processing."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    failed_status = f"FAILED: {timestamp}, {failure_reason}"
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Insert failed record to prevent re-processing
            cur.execute("""
                INSERT INTO openalex_enrichment_country 
                (doctrove_paper_id, processed_country, processed_uschina, 
                 institution_name, author_position, confidence, llm_response)
                VALUES (%s, 'UNK', 'Unknown', NULL, NULL, 0.0, %s)
                ON CONFLICT (doctrove_paper_id) DO NOTHING
            """, (paper_id, failed_status))
        conn.commit()

def update_papers_with_country_enrichment(connection_factory, enrichment_results: List[Any]) -> int:
    """Update papers with country enrichment results."""
    if not enrichment_results:
        return 0
    
    updated_count = 0
    with connection_factory() as conn:
        with conn.cursor() as cur:
            for result in enrichment_results:
                try:
                    # Insert enrichment result
                    cur.execute("""
                        INSERT INTO openalex_enrichment_country 
                        (doctrove_paper_id, processed_country, processed_uschina,
                         institution_name, author_position, confidence, llm_response)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (doctrove_paper_id) DO UPDATE SET
                            processed_country = EXCLUDED.processed_country,
                            processed_uschina = EXCLUDED.processed_uschina,
                            institution_name = EXCLUDED.institution_name,
                            author_position = EXCLUDED.author_position,
                            confidence = EXCLUDED.confidence,
                            llm_response = EXCLUDED.llm_response
                    """, (
                        result.paper_id, result.country, result.uschina,
                        result.institution_name, result.author_position,
                        result.confidence, result.llm_response
                    ))
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error updating paper {result.paper_id}: {e}")
                    # Mark as failed
                    mark_country_enrichment_failed(connection_factory, result.paper_id, str(e))
                    conn.rollback()
                    continue
            
            conn.commit()
    
    return updated_count

def process_country_enrichment(batch_size: int = BATCH_SIZE, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Main function to process country enrichment for all papers missing country data.
    
    This service is triggered by OpenAlex papers with NO country enrichment record.
    UNK counts as a valid, completed enrichment result.
    """
    logger.info(f"Starting country enrichment for all missing country data")
    connection_factory = create_connection_factory()
    papers_needing_enrichment = get_papers_needing_country_enrichment(connection_factory, limit)
    total_papers = len(papers_needing_enrichment)
    
    if total_papers == 0:
        logger.info("No papers need country enrichment")
        return {
            'total_papers': 0,
            'processed_papers': 0,
            'successful_enrichments': 0,
            'failed_enrichments': 0
        }
    
    logger.info(f"Found {total_papers} papers needing country enrichment")
    total_processed = 0
    total_successful = 0
    total_failed = 0
    
    for i in range(0, total_papers, batch_size):
        batch = papers_needing_enrichment[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_papers + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} papers)")
        
        try:
            # Process papers using the streamlined logic
            logger.debug(f"About to call process_papers_for_country_enrichment with {len(batch)} papers")
            logger.debug(f"connection_factory type: {type(connection_factory)}")
            logger.debug(f"batch type: {type(batch)}")
            logger.debug(f"First paper: {batch[0] if batch else 'No papers'}")
            results = process_country_enrichment_for_papers(batch, connection_factory)
            
            if results:
                # Update papers with results
                updated_count = update_papers_with_country_enrichment(connection_factory, results)
                total_successful += updated_count
                total_failed += len(batch) - updated_count
            else:
                # Mark all papers in batch as UNK (no data available)
                for paper in batch:
                    mark_country_enrichment_failed(connection_factory, paper['doctrove_paper_id'], "No country data available")
                total_failed += len(batch)
            
            total_processed += len(batch)
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
            # Mark all papers in batch as failed
            for paper in batch:
                mark_country_enrichment_failed(connection_factory, paper['doctrove_paper_id'], f"Batch processing failed: {e}")
            total_failed += len(batch)
            total_processed += len(batch)
    
    logger.info(f"Country enrichment completed: {total_processed} papers processed, "
               f"{total_successful} successful, {total_failed} failed")
    
    return {
        'total_papers': total_papers,
        'processed_papers': total_processed,
        'successful_enrichments': total_successful,
        'failed_enrichments': total_failed
    }

def main():
    """Main entry point for the country enrichment service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate country enrichment for OpenAlex papers')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                       help=f'Batch size for processing (default: {BATCH_SIZE})')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of papers to process (default: no limit)')
    parser.add_argument('--status', action='store_true',
                       help='Show status of papers needing country enrichment')
    
    args = parser.parse_args()
    
    # Setup database connection
    connection_factory = create_connection_factory()
    
    if args.status:
        # Show status
        status_info = get_fast_country_enrichment_status(connection_factory)
        
        print(f"\n=== Country Enrichment Status ===")
        if status_info.get('error'):
            print(f"Error getting status: {status_info['error']}")
        else:
            print(f"Total papers with metadata: {status_info['total_with_metadata']}")
            print(f"Total papers already enriched: {status_info['total_enriched']}")
            print(f"Papers needing country enrichment: {status_info['papers_needing_enrichment']}")
            print(f"Note: UNK counts as valid enrichment result")
        return
    
    # Process country enrichment
    results = process_country_enrichment(
        batch_size=args.batch_size,
        limit=args.limit
    )
    
    print(f"\n=== Country Enrichment Results ===")
    print(f"Total papers found: {results['total_papers']}")
    print(f"Papers processed: {results['processed_papers']}")
    print(f"Successful enrichments: {results['successful_enrichments']}")
    print(f"Failed enrichments: {results['failed_enrichments']}")

if __name__ == "__main__":
    main()
