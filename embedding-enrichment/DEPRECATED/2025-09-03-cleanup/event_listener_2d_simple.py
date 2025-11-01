#!/usr/bin/env python3
"""
Simple 2D Embedding Event Listener
Based on the working pattern of event_listener_functional.py
"""

import os
import sys
import time
import logging
import threading
import signal
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass, field
from functools import partial
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

# Import database connection from doctrove-api
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enrichment_2d.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ProcessingResult:
    """Immutable processing result."""
    successful: int
    failed: int
    timestamp: float

def create_connection_factory() -> Callable:
    """Create a connection factory function (pure function)."""
    def connection_factory():
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    return connection_factory

def get_papers_needing_2d_embeddings_count(connection_factory: Callable) -> int:
    """
    Get count of papers needing 2D embeddings (pure function).
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Number of papers needing 2D embeddings
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NULL
                AND doctrove_embedding IS NOT NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
            """)
            return cur.fetchone()[0]

def process_2d_embedding_batch(connection_factory: Callable, batch_size: int = 100) -> ProcessingResult:
    """
    Process exactly one batch of 2D embeddings using functional enrichment.
    
    Args:
        connection_factory: Database connection factory
        batch_size: Number of papers to process
        
    Returns:
        ProcessingResult with success/failure counts
    """
    try:
        logger.info(f"Processing batch of {batch_size} papers for 2D embeddings...")
        
        # Import our functional enrichment
        from functional_embedding_2d_enrichment import create_functional_2d_enrichment
        
        # Get papers that need 2D embeddings
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
                """, (batch_size,))
                
                papers = []
                for row in cur.fetchall():
                    paper = {
                        'doctrove_paper_id': row[0],
                        'doctrove_title': row[1],
                        'doctrove_abstract': row[2],
                        'doctrove_embedding': row[3]
                    }
                    papers.append(paper)
        
        if not papers:
            logger.info("No papers need 2D embeddings")
            return ProcessingResult(successful=0, failed=0, timestamp=time.time())
        
        # Process papers using functional enrichment
        enrichment = create_functional_2d_enrichment()
        result_count = enrichment.run_enrichment(papers)
        
        successful = result_count
        failed = len(papers) - result_count
        
        return ProcessingResult(
            successful=successful,
            failed=failed,
            timestamp=time.time()
        )
        
    except Exception as e:
        logger.error(f"Error processing 2D embedding batch: {e}")
        return ProcessingResult(successful=0, failed=batch_size, timestamp=time.time())

def main_loop():
    """Main processing loop for 2D embeddings."""
    connection_factory = create_connection_factory()
    total_processed = 0
    batch_size = 100
    
    logger.info("Starting 2D embedding processing loop...")
    
    while True:
        try:
            # Get count of papers needing 2D embeddings
            papers_needing_2d = get_papers_needing_2d_embeddings_count(connection_factory)
            
            if papers_needing_2d == 0:
                logger.info("No papers need 2D embeddings. Sleeping for 30 seconds...")
                time.sleep(30)
                continue
            
            logger.info(f"Found {papers_needing_2d} papers needing 2D embeddings")
            
            # Process one batch
            result = process_2d_embedding_batch(connection_factory, batch_size)
            
            total_processed += result.successful
            
            logger.info(f"Batch completed: {result.successful} successful, {result.failed} failed")
            logger.info(f"Total 2D embeddings processed: {total_processed}")
            
            # Brief pause between batches
            time.sleep(2)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal. Stopping 2D embedding processing...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(30)
            continue
    
    logger.info(f"2D embedding processing stopped. Total processed: {total_processed}")

if __name__ == "__main__":
    main_loop()

