#!/usr/bin/env python3
"""
Queue-based OpenAlex Details Enrichment Worker

This worker processes OpenAlex papers from the enrichment_queue,
extracting journal names, citations, topics, institutions, etc. from raw JSON.
Uses functional programming principles and the existing queue infrastructure.
"""

import logging
import json
import sys
import time
import random
from typing import List, Dict, Any, Optional, Callable
import psycopg2
from psycopg2.extras import RealDictCursor

# Add paths for imports
sys.path.append('../doctrove-api')
sys.path.append('../doc-ingestor/ROOT_SCRIPTS')

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Import processing functions from the existing enrichment script
try:
    from openalex_details_enrichment_functional import (
        process_single_paper,
        process_batch_functional
    )
    PROCESSING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import processing functions: {e}")
    PROCESSING_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_connection_factory() -> Callable:
    """Create a connection factory function."""
    def connection_factory():
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    return connection_factory

def get_last_processed_id(state_file: str = '/tmp/openalex_details_last_id.txt') -> int:
    """Get the last processed queue ID from state file."""
    try:
        with open(state_file, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0  # Start from beginning

def save_last_processed_id(last_id: int, state_file: str = '/tmp/openalex_details_last_id.txt'):
    """Save the last processed queue ID to state file."""
    with open(state_file, 'w') as f:
        f.write(str(last_id))

def claim_papers_from_queue(
    connection_factory: Callable, 
    batch_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Claim papers from the enrichment_queue using ultra-fast ID range SELECT.
    No locking, no updates - just read and process. ON CONFLICT handles duplicates.
    """
    with connection_factory() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get the last processed ID
            last_id = get_last_processed_id()
            
            # ULTRA-FAST: Single JOIN query to get both queue ID and raw data
            # No locks, no updates - just read and process!
            cur.execute("""
                SELECT eq.id, eq.paper_id, om.openalex_raw_data
                FROM enrichment_queue eq
                JOIN openalex_metadata om ON eq.paper_id = om.doctrove_paper_id
                WHERE eq.enrichment_type = 'openalex_details'
                    AND eq.id > %s
                    AND om.openalex_raw_data IS NOT NULL
                    AND om.openalex_raw_data != '{}'
                ORDER BY eq.id
                LIMIT %s
            """, (last_id, batch_size))
            
            results = cur.fetchall()
            
            if not results:
                return []
            
            # Save the highest ID we'll process
            max_id = max(row['id'] for row in results)
            save_last_processed_id(max_id)
            
            logger.info(f"   ID range: {last_id + 1} to {max_id}")
            
            # Return as list of tuples (paper_id, raw_data) for process_batch_functional
            papers = [(row['paper_id'], row['openalex_raw_data']) for row in results]
            
            return papers

def process_papers_batch(papers: List[tuple]) -> List[Dict[str, Any]]:
    """Process a batch of papers using the existing functional batch processor."""
    if not PROCESSING_AVAILABLE:
        logger.error("Processing functions not available - cannot process papers")
        return []
    
    try:
        # Use the existing functional batch processor
        batch_result = process_batch_functional(papers)
        
        # Extract successful results
        successful_details = [r.details for r in batch_result.results if r.success and r.details]
        
        return successful_details
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        return []

def insert_paper_details(
    connection_factory: Callable,
    details_list: List[Dict[str, Any]]
) -> int:
    """Insert extracted details into openalex_details_enrichment table."""
    if not details_list:
        return 0
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Get all possible columns from all results
            all_columns = set()
            for details in details_list:
                all_columns.update(details.keys())
            
            columns = sorted(list(all_columns))
            placeholders = ['%s'] * len(columns)
            
            # Build INSERT statement
            query = f"""
                INSERT INTO openalex_details_enrichment ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (doctrove_paper_id) DO UPDATE SET
                    processed_at = NOW()
            """
            
            # Prepare values
            values_list = []
            for details in details_list:
                values = [details.get(col) for col in columns]
                values_list.append(values)
            
            # Execute batch insert
            cur.executemany(query, values_list)
            conn.commit()
            
            return len(values_list)

def mark_papers_failed(
    connection_factory: Callable,
    paper_ids: List[str]
) -> None:
    """
    Re-queue failed papers by inserting them back into the queue.
    Since we DELETE on claim, failures need to be re-inserted.
    """
    if not paper_ids:
        return
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Re-insert failed papers back into queue
            for paper_id in paper_ids:
                cur.execute("""
                    INSERT INTO enrichment_queue (paper_id, enrichment_type, priority, status)
                    VALUES (%s, 'openalex_details', 3, 'pending')
                    ON CONFLICT DO NOTHING
                """, (paper_id,))
            conn.commit()
            logger.info(f"   Re-queued {len(paper_ids)} failed papers")

def get_queue_size(connection_factory: Callable) -> int:
    """Get count of pending papers in queue for openalex_details."""
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Fast count - just count by type since we DELETE processed papers
            cur.execute("""
                SELECT COUNT(*)
                FROM enrichment_queue
                WHERE enrichment_type = 'openalex_details'
            """)
            return cur.fetchone()[0]

def process_batch(
    connection_factory: Callable,
    batch_size: int = 100
) -> Dict[str, int]:
    """Process one batch of papers from the queue."""
    start_time = time.time()
    
    # Claim papers
    logger.info(f"Claiming {batch_size} papers from queue...")
    claim_start = time.time()
    papers = claim_papers_from_queue(connection_factory, batch_size)
    claim_time = time.time() - claim_start
    
    if not papers:
        return {'claimed': 0, 'processed': 0, 'failed': 0}
    
    logger.info(f"Claimed {len(papers)} papers in {claim_time:.2f}s")
    
    # Process papers using functional batch processor
    logger.info(f"Extracting details from {len(papers)} papers...")
    process_start = time.time()
    
    details_list = process_papers_batch(papers)
    
    process_time = time.time() - process_start
    logger.info(f"Processed {len(details_list)} papers in {process_time:.2f}s")
    
    # Calculate failed papers
    claimed_ids = [p[0] for p in papers]
    successful_ids = [d['doctrove_paper_id'] for d in details_list]
    failed_ids = [pid for pid in claimed_ids if pid not in successful_ids]
    
    # Insert successful results
    if details_list:
        insert_start = time.time()
        inserted = insert_paper_details(connection_factory, details_list)
        insert_time = time.time() - insert_start
        logger.info(f"Inserted {inserted} results in {insert_time:.2f}s")
    
    # No need to update queue - we just track progress with last_id
    # Failed papers can be retried on next run from beginning
    # (or we could log them for manual review)
    
    total_time = time.time() - start_time
    logger.info(f"Batch complete: {len(successful_ids)} successful, {len(failed_ids)} failed in {total_time:.2f}s")
    
    return {
        'claimed': len(papers),
        'processed': len(successful_ids),
        'failed': len(failed_ids)
    }

def run_worker(batch_size: int = 100, sleep_seconds: int = 10):
    """Main worker loop - polls queue and processes papers."""
    connection_factory = create_connection_factory()
    
    logger.info("🚀 OpenAlex Details Enrichment Worker Started")
    logger.info(f"   Batch size: {batch_size}")
    logger.info(f"   Sleep between checks: {sleep_seconds}s")
    logger.info("")
    
    if not PROCESSING_AVAILABLE:
        logger.error("❌ Cannot start worker - processing functions not available")
        logger.error("   Make sure openalex_details_enrichment_functional.py is in ROOT_SCRIPTS/")
        return
    
    empty_batches = 0
    total_processed = 0
    total_failed = 0
    
    try:
        while True:
            # Check queue size
            queue_size = get_queue_size(connection_factory)
            logger.info(f"Queue size: {queue_size} papers")
            
            if queue_size == 0:
                empty_batches += 1
                logger.info(f"No papers available for processing")
                if empty_batches >= 3:
                    logger.info(f"Queue idle - no papers available (empty batch #{empty_batches})")
            else:
                empty_batches = 0
                
                # Process batch
                result = process_batch(connection_factory, batch_size)
                total_processed += result['processed']
                total_failed += result['failed']
                
                logger.info(f"📊 Total: {total_processed} processed, {total_failed} failed")
                logger.info("")
            
            # Sleep with jitter to avoid thundering herd
            jitter = random.uniform(0.9, 1.1)
            sleep_time = sleep_seconds * jitter
            logger.info(f"Sleeping for {sleep_time:.1f}s (base: {sleep_seconds}s, jitter: {jitter:.2f})")
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Worker stopped by user")
        logger.info(f"📊 Final stats: {total_processed} processed, {total_failed} failed")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenAlex Details Enrichment Queue Worker')
    parser.add_argument('--batch-size', type=int, default=20000,
                        help='Number of papers to process per batch (default: 20000)')
    parser.add_argument('--sleep', type=int, default=1,
                        help='Seconds to sleep between queue checks (default: 1)')
    
    args = parser.parse_args()
    
    run_worker(batch_size=args.batch_size, sleep_seconds=args.sleep)

