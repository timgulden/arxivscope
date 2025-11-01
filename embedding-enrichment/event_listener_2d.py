#!/usr/bin/env python3
"""
2D Embedding Event Listener with Functional Programming

This event listener specifically handles 2D embedding generation using functional programming.
It does NOT interfere with the 1D embedding process (handled by embedding_service.py).
"""

import os
import sys
import time
import logging
import signal
import threading
from typing import Dict, Any, Optional
from functools import partial

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
sys.path.append(os.path.dirname(__file__))

# Import our functional enrichment for 2D embeddings
from functional_embedding_2d_enrichment import create_functional_2d_enrichment

# Import async enrichment system
from doc_ingestor.async_enrichment import AsyncEnrichmentWorker, create_connection_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enrichment_2d.log'),  # Separate log for 2D process
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Functional2DEnrichmentEventListener:
    """
    Event listener that uses functional programming for 2D embedding enrichment.
    This ONLY handles 2D embeddings and does NOT interfere with 1D embedding generation.
    """
    
    def __init__(self, batch_size: int = 100, poll_interval: int = 30):
        """
        Initialize the functional 2D enrichment event listener.
        
        Args:
            batch_size: Number of papers to process per batch
            poll_interval: Seconds between polling for new papers
        """
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.running = False
        self.worker_thread = None
        
        # Create connection factory
        self.connection_factory = create_connection_factory()
        
        # Create functional enrichment for 2D embeddings
        try:
            self.functional_enrichment = create_functional_2d_enrichment()
            logger.info("Functional 2D embedding enrichment initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize functional 2D enrichment: {e}")
            raise
    
    def start(self):
        """Start the 2D event listener."""
        if self.running:
            logger.warning("2D event listener is already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Functional 2D enrichment event listener started")
    
    def stop(self):
        """Stop the 2D event listener."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Functional 2D enrichment event listener stopped")
    
    def _worker_loop(self):
        """Main worker loop that polls for new papers needing 2D embeddings."""
        logger.info(f"Starting 2D worker loop (batch_size={self.batch_size}, poll_interval={self.poll_interval}s)")
        
        while self.running:
            try:
                # Check for new papers that need 2D embeddings
                papers = self._get_papers_needing_2d_embeddings()
                
                if papers:
                    logger.info(f"Found {len(papers)} papers needing 2D embeddings")
                    self._process_2d_embeddings_batch(papers)
                else:
                    logger.debug("No papers need 2D embeddings")
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in 2D worker loop: {e}")
                time.sleep(self.poll_interval)
    
    def _get_papers_needing_2d_embeddings(self) -> list:
        """
        Get papers that need 2D embedding processing.
        Only processes papers that already have 1D embeddings but are missing 2D embeddings.
        """
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # Get papers that have 1D embeddings but need 2D embeddings
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
                """, (self.batch_size,))
                
                papers = cur.fetchall()
                return [dict(paper) for paper in papers]
    
    def _process_2d_embeddings_batch(self, papers: list):
        """Process a batch of papers for 2D embeddings using functional enrichment."""
        if not papers:
            return
        
        logger.info(f"Processing {len(papers)} papers for 2D embeddings...")
        
        try:
            # Use functional enrichment to process papers for 2D embeddings
            result_count = self.functional_enrichment.run_enrichment(papers)
            
            logger.info(f"2D embedding enrichment completed: {result_count}/{len(papers)} papers processed")
            
        except Exception as e:
            logger.error(f"Error processing 2D embeddings batch: {e}")

def setup_signal_handlers(event_listener: Functional2DEnrichmentEventListener):
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down 2D enrichment gracefully...")
        event_listener.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point for the 2D event listener."""
    logger.info("Starting Functional 2D Enrichment Event Listener...")
    logger.info("This listener ONLY handles 2D embeddings and does NOT interfere with 1D embedding generation.")
    
    # Create 2D event listener
    event_listener = Functional2DEnrichmentEventListener(
        batch_size=100,  # Process 100 papers per batch
        poll_interval=30  # Check every 30 seconds
    )
    
    # Set up signal handlers
    setup_signal_handlers(event_listener)
    
    try:
        # Start the 2D event listener
        event_listener.start()
        
        # Keep the main thread alive
        while event_listener.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down 2D enrichment...")
    except Exception as e:
        logger.error(f"Unexpected error in 2D enrichment: {e}")
    finally:
        event_listener.stop()
        logger.info("2D enrichment event listener shutdown complete")

if __name__ == "__main__":
    main()
