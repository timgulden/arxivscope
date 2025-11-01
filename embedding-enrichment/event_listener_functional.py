#!/usr/bin/env python3
"""
Database-Driven Functional Event Listener
Uses database functions and continuous processing for real-time embedding generation
Follows the same pattern as the 2D system with functional programming principles
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
        logging.FileHandler('enrichment.log'),
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

def get_papers_needing_embeddings_count_db(connection_factory: Callable) -> int:
    """
    Get count of papers needing embeddings using database function (pure function).
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Number of papers needing embeddings
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT get_papers_needing_embeddings_count()")
            return cur.fetchone()[0]

def process_embedding_batch(connection_factory: Callable) -> ProcessingResult:
    """
    Process exactly one batch of 250 embeddings (pure function with controlled side effects).
    Exactly one API call per batch.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        ProcessingResult with success/failure counts
    """
    try:
        logger.info("Processing batch of 250 papers (one API call)...")
        
        # Import embedding service
        from embedding_service import process_embedding_enrichment
        
        # Process exactly 250 embeddings with one API call
        result = process_embedding_enrichment(batch_size=250, limit=250)
        
        if result and 'successful_embeddings' in result:
            successful = result['successful_embeddings']
            failed = result.get('failed_embeddings', 0)
            return ProcessingResult(
                successful=successful,
                failed=failed,
                timestamp=time.time()
            )
        else:
            return ProcessingResult(
                successful=0,
                failed=0,
                timestamp=time.time()
            )
            
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        return ProcessingResult(
            successful=0,
            failed=250,  # Assume all 250 failed
            timestamp=time.time()
        )

def process_embeddings_continuously(connection_factory: Callable, batch_size: int = 250, total_papers: int = 0) -> int:
    """
    Process embeddings continuously until no more papers are available (pure function).
    Uses database functions and follows the same pattern as 2D system.
    
    Args:
        connection_factory: Database connection factory
        batch_size: Number of papers to process per batch
        total_papers: Total papers needing embeddings for progress calculation
        
    Returns:
        Total number of papers processed
    """
    total_processed = 0
    consecutive_empty_batches = 0
    max_empty_batches = 3  # Stop after 3 consecutive empty batches
    
    while consecutive_empty_batches < max_empty_batches:
        result = process_embedding_batch(connection_factory)
        
        if result.successful == 0 and result.failed == 0:
            consecutive_empty_batches += 1
            if consecutive_empty_batches >= max_empty_batches:
                logger.info(f"No more papers to process after {consecutive_empty_batches} empty batches")
        else:
            consecutive_empty_batches = 0  # Reset counter
            total_processed += result.successful + result.failed
            
            # Show progress in format: Processed 1500/13000000 (11.5%)
            if total_papers > 0:
                percentage = (total_processed / total_papers) * 100
                logger.info(f"Processed {total_processed:,}/{total_papers:,} ({percentage:.1f}%)")
            else:
                logger.info(f"Processed {total_processed:,} papers")
        
        # Small delay between batches
        time.sleep(1)
    
    return total_processed

class FunctionalEventListener:
    """Database-driven functional event listener with continuous processing."""
    
    def __init__(self, batch_size: int = 250):
        self.batch_size = batch_size
        self.running = False
        self.background_thread: Optional[threading.Thread] = None
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def start(self):
        """Start the database-driven functional event listener."""
        self.running = True
        logger.info("Database-driven functional event listener started")
        
        # Start background processing in a separate thread
        self.background_thread = threading.Thread(target=self._functional_background_processing)
        self.background_thread.daemon = True
        self.background_thread.start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.stop()
    
    def stop(self):
        """Stop the database-driven functional event listener."""
        self.running = False
        logger.info("Database-driven functional event listener stopped")
    
    def _functional_background_processing(self):
        """Background processing using database functions and continuous processing."""
        logger.info("Database-driven background processing started")
        
        while self.running:
            try:
                logger.info("🚀 Database-driven processing cycle starting...")
                
                # Get initial count using database function
                connection_factory = create_connection_factory()
                initial_count = get_papers_needing_embeddings_count_db(connection_factory)
                
                if initial_count == 0:
                    logger.info("No papers need embedding processing. Sleeping for 30 seconds...")
                    time.sleep(30)
                    continue
                
                logger.info(f"Found {initial_count:,} papers needing embeddings")
                
                # Process embeddings continuously (like 2D system)
                total_processed = process_embeddings_continuously(connection_factory, self.batch_size, initial_count)
                
                if total_processed > 0:
                    logger.info(f"✅ Cycle completed: {total_processed:,} papers processed")
                else:
                    logger.info("✅ No papers to process in this cycle")
                
                # Wait before next cycle
                logger.info("⏳ Waiting 30 seconds before next cycle...")
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in database-driven background processing: {e}")
                time.sleep(60)  # Wait longer on error

def main():
    """Main function."""
    print("Database-Driven Functional Event Listener started!")
    print("Using database functions and continuous processing...")
    print("250 records per batch, one API call per batch")
    print("Press Ctrl+C to stop")
    
    # Create and start the database-driven functional event listener
    listener = FunctionalEventListener(batch_size=250)
    
    try:
        listener.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    finally:
        listener.stop()

if __name__ == "__main__":
    main()



