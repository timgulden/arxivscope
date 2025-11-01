#!/usr/bin/env python3
"""
OpenAlex Details Backlog Processor - Fast Direct Processing

Works directly from openalex_metadata table, skipping the queue for backlog processing.
Uses UUID ranges for fast sequential processing with ON CONFLICT to skip already-processed papers.

This is optimized for processing large backlogs. For real-time processing of new papers,
use queue_openalex_details_worker.py which responds to database triggers.
"""

import logging
import sys
import time
from typing import List, Dict, Any, Callable

# Add paths for imports
sys.path.append('../doctrove-api')
sys.path.append('../doc-ingestor/ROOT_SCRIPTS')

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
import psycopg2
from psycopg2.extras import RealDictCursor

# Import processing functions
from openalex_details_enrichment_functional import process_batch_functional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

def get_last_processed_uuid(state_file: str = '/tmp/openalex_backlog_last_uuid.txt') -> str:
    """Get the last processed paper UUID from state file."""
    try:
        with open(state_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return '00000000-0000-0000-0000-000000000000'  # Start from beginning

def save_last_processed_uuid(last_uuid: str, state_file: str = '/tmp/openalex_backlog_last_uuid.txt'):
    """Save the last processed paper UUID to state file."""
    with open(state_file, 'w') as f:
        f.write(last_uuid)

def fetch_batch_from_metadata(
    connection_factory: Callable,
    batch_size: int = 20000,
    state_file: str = '/tmp/openalex_backlog_last_uuid.txt'
) -> List[tuple]:
    """
    Fetch batch directly from openalex_metadata using UUID ranges.
    FAST - single table scan with index on primary key.
    """
    with connection_factory() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            last_uuid = get_last_processed_uuid(state_file)
            
            # FAST & RELIABLE: UUID range with ORDER BY
            # Slightly slower fetch (~2s) but guaranteed progress
            # ON CONFLICT handles any duplicates from previous runs
            cur.execute("""
                SELECT 
                    doctrove_paper_id,
                    openalex_raw_data
                FROM openalex_metadata
                WHERE doctrove_paper_id > %s
                    AND openalex_raw_data IS NOT NULL
                    AND openalex_raw_data != '{}'
                ORDER BY doctrove_paper_id
                LIMIT %s
            """, (last_uuid, batch_size))
            
            results = cur.fetchall()
            
            if not results:
                return []
            
            # Save progress
            max_uuid = results[-1]['doctrove_paper_id']
            save_last_processed_uuid(str(max_uuid), state_file)
            
            logger.info(f"   UUID range: {last_uuid[:8]}... to {str(max_uuid)[:8]}...")
            
            # Return as tuples for process_batch_functional
            papers = [(row['doctrove_paper_id'], row['openalex_raw_data']) for row in results]
            
            return papers

def insert_paper_details(
    connection_factory: Callable,
    details_list: List[Dict[str, Any]]
) -> int:
    """Insert extracted details with ON CONFLICT to skip duplicates."""
    if not details_list:
        return 0
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Get all columns
            all_columns = set()
            for details in details_list:
                all_columns.update(details.keys())
            
            columns = sorted(list(all_columns))
            placeholders = ['%s'] * len(columns)
            
            # INSERT with ON CONFLICT DO NOTHING to skip already-processed
            query = f"""
                INSERT INTO openalex_details_enrichment ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (doctrove_paper_id) DO NOTHING
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

def process_batch(
    connection_factory: Callable,
    batch_size: int = 20000,
    state_file: str = '/tmp/openalex_backlog_last_uuid.txt'
) -> Dict[str, int]:
    """Process one batch directly from openalex_metadata."""
    start_time = time.time()
    
    # Fetch papers - should be FAST (single table, indexed)
    logger.info(f"Fetching {batch_size} papers from openalex_metadata...")
    fetch_start = time.time()
    papers = fetch_batch_from_metadata(connection_factory, batch_size, state_file)
    fetch_time = time.time() - fetch_start
    
    if not papers:
        logger.info("No more papers to process")
        return {'fetched': 0, 'processed': 0, 'failed': 0}
    
    logger.info(f"Fetched {len(papers)} papers in {fetch_time:.2f}s")
    
    # Process papers
    logger.info(f"Extracting details from {len(papers)} papers...")
    process_start = time.time()
    
    batch_result = process_batch_functional(papers)
    details_list = [r.details for r in batch_result.results if r.success and r.details]
    
    process_time = time.time() - process_start
    logger.info(f"Processed {len(details_list)} papers in {process_time:.2f}s")
    
    # Insert results
    if details_list:
        insert_start = time.time()
        inserted = insert_paper_details(connection_factory, details_list)
        insert_time = time.time() - insert_start
        logger.info(f"Inserted {inserted} new results in {insert_time:.2f}s (ON CONFLICT skipped duplicates)")
    
    failed = len(papers) - len(details_list)
    
    total_time = time.time() - start_time
    logger.info(f"Batch complete: {len(details_list)} successful, {failed} failed in {total_time:.2f}s")
    logger.info(f"   Rate: {len(papers)/total_time:.1f} papers/sec")
    
    return {
        'fetched': len(papers),
        'processed': len(details_list),
        'failed': failed
    }

def run_backlog_processor(batch_size: int = 20000, max_batches: int = None, worker_id: str = 'main'):
    """Process the backlog - runs until no more papers or max_batches reached."""
    connection_factory = create_connection_factory()
    state_file = f'/tmp/openalex_backlog_{worker_id}_last_uuid.txt'
    
    logger.info("🚀 OpenAlex Details Backlog Processor Started")
    logger.info(f"   Worker ID: {worker_id}")
    logger.info(f"   Batch size: {batch_size:,}")
    logger.info(f"   Max batches: {max_batches or 'unlimited'}")
    logger.info(f"   State file: {state_file}")
    logger.info("")
    
    batch_num = 0
    total_processed = 0
    total_failed = 0
    start_time = time.time()
    
    try:
        while True:
            batch_num += 1
            
            if max_batches and batch_num > max_batches:
                logger.info(f"Reached max batches limit ({max_batches})")
                break
            
            logger.info(f"{'='*60}")
            logger.info(f"Batch {batch_num}")
            logger.info(f"{'='*60}")
            
            result = process_batch(connection_factory, batch_size, state_file)
            
            if result['fetched'] == 0:
                logger.info("✅ No more papers to process - backlog complete!")
                break
            
            total_processed += result['processed']
            total_failed += result['failed']
            
            logger.info(f"📊 Running totals: {total_processed:,} processed, {total_failed:,} failed")
            
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            remaining = 16_800_000 - total_processed  # Approximate
            eta_hours = (remaining / rate / 3600) if rate > 0 else 0
            
            logger.info(f"⏱️  Overall rate: {rate:.1f} papers/sec, ETA: {eta_hours:.1f} hours")
            logger.info("")
            
            # Small sleep between batches
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Processor stopped by user")
    except Exception as e:
        logger.error(f"❌ Processor error: {e}")
        raise
    finally:
        elapsed = time.time() - start_time
        logger.info(f"\n📊 Final stats:")
        logger.info(f"   Batches processed: {batch_num}")
        logger.info(f"   Papers processed: {total_processed:,}")
        logger.info(f"   Papers failed: {total_failed:,}")
        logger.info(f"   Total time: {elapsed/3600:.2f} hours")
        logger.info(f"   Average rate: {total_processed/elapsed:.1f} papers/sec")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenAlex Details Backlog Processor')
    parser.add_argument('--batch-size', type=int, default=20000,
                        help='Number of papers to process per batch (default: 20000)')
    parser.add_argument('--max-batches', type=int, default=None,
                        help='Maximum number of batches to process (default: unlimited)')
    parser.add_argument('--worker-id', type=str, default='main',
                        help='Worker ID for parallel processing (default: main)')
    
    args = parser.parse_args()
    
    run_backlog_processor(batch_size=args.batch_size, max_batches=args.max_batches, worker_id=args.worker_id)

