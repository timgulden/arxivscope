"""
Asynchronous enrichment system for DocTrove.
Automatically processes new papers for 2D embeddings and other enrichments.
"""

import logging
import threading
import time
import queue
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

from db import create_connection_factory
from enrichment_framework import BaseEnrichment

logger = logging.getLogger(__name__)

class AsyncEnrichmentWorker:
    """
    Background worker for processing enrichment tasks asynchronously.
    """
    
    def __init__(self, connection_factory: Callable, batch_size: int = 500, 
                 poll_interval: int = 30):
        """
        Initialize the enrichment worker.
        
        Args:
            connection_factory: Database connection factory
            batch_size: Number of papers to process in each batch
            poll_interval: Seconds between polling for new papers
        """
        self.connection_factory = connection_factory
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.running = False
        self.worker_thread = None
        self.task_queue = queue.Queue()
        
        # Register enrichment types
        self.enrichments = self._register_enrichments()
    
    def _register_enrichments(self) -> Dict[str, BaseEnrichment]:
        """Register all available enrichment types."""
        enrichments = {}
        
        # Import enrichment classes
        try:
            from enrichment_framework import CredibilityEnrichment
            enrichments['credibility'] = CredibilityEnrichment()
        except ImportError:
            logger.warning("CredibilityEnrichment not available")
        
        # Add 2D embedding enrichment (fundamental type)
        try:
            # Import from the embedding-enrichment directory
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'embedding-enrichment'))
            from enrichment_framework import Embedding2DEnrichment
            enrichments['embedding_2d'] = Embedding2DEnrichment()
        except ImportError as e:
            logger.warning(f"Embedding2DEnrichment not available: {e}")
        
        logger.debug(f"Registered {len(enrichments)} enrichment types: {list(enrichments.keys())}")
        return enrichments
    
    def start(self):
        """Start the background enrichment worker."""
        if self.running:
            logger.warning("Enrichment worker is already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.debug("Async enrichment worker started")
    
    def stop(self):
        """Stop the background enrichment worker."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.debug("Async enrichment worker stopped")
    
    def _worker_loop(self):
        """Main worker loop that polls for new papers and processes them."""
        while self.running:
            try:
                # Check for new papers that need enrichment
                new_papers = self._get_papers_needing_enrichment()
                
                if new_papers:
                    logger.debug(f"Found {len(new_papers)} papers needing enrichment")
                    self._process_enrichment_batch(new_papers)
                else:
                    logger.debug("No papers needing enrichment")
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in enrichment worker loop: {e}")
                time.sleep(self.poll_interval)
    
    def _get_papers_needing_enrichment(self) -> List[Dict[str, Any]]:
        """Get papers that need enrichment processing."""
        with self.connection_factory() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get papers that need 2D embeddings
                cur.execute("""
                    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_abstract,
                           dp.doctrove_embedding
                    FROM doctrove_papers dp
                    WHERE dp.doctrove_embedding_2d IS NULL
                    AND dp.doctrove_embedding IS NOT NULL
                    ORDER BY dp.doctrove_paper_id
                    LIMIT %s
                """, (self.batch_size,))
                
                papers = cur.fetchall()
                return [dict(paper) for paper in papers]
    
    def _process_enrichment_batch(self, papers: List[Dict[str, Any]]):
        """Process a batch of papers through all enrichment types."""
        logger.debug(f"Processing {len(papers)} papers through enrichments")
        
        for enrichment_name, enrichment in self.enrichments.items():
            try:
                logger.debug(f"Running {enrichment_name} enrichment on {len(papers)} papers")
                
                # Check if papers have required fields for this enrichment
                required_fields = enrichment.get_required_fields()
                valid_papers = self._filter_papers_by_required_fields(papers, required_fields)
                
                if valid_papers:
                    # Run enrichment
                    result_count = enrichment.run_enrichment(valid_papers)
                    logger.debug(f"Completed {enrichment_name} enrichment: {result_count} papers processed")
                else:
                    logger.debug(f"No papers have required fields for {enrichment_name} enrichment")
                    
            except Exception as e:
                logger.error(f"Error running {enrichment_name} enrichment: {e}")
    
    def _filter_papers_by_required_fields(self, papers: List[Dict[str, Any]], 
                                        required_fields: List[str]) -> List[Dict[str, Any]]:
        """Filter papers to only include those with required fields."""
        valid_papers = []
        
        for paper in papers:
            has_all_fields = all(field in paper and paper[field] is not None 
                               for field in required_fields)
            if has_all_fields:
                valid_papers.append(paper)
        
        return valid_papers
    
    def trigger_immediate_enrichment(self, paper_ids: List[str]):
        """
        Trigger immediate enrichment for specific papers.
        
        Args:
            paper_ids: List of paper IDs to enrich immediately
        """
        if not paper_ids:
            return
        
        # Add to task queue for immediate processing
        self.task_queue.put({
            'type': 'immediate',
            'paper_ids': paper_ids,
            'timestamp': datetime.now()
        })
        logger.debug(f"Queued immediate enrichment for {len(paper_ids)} papers")


def setup_async_enrichment_triggers(connection_factory: Callable):
    """
    Set up database triggers to automatically queue enrichment tasks.
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Create enrichment queue table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS enrichment_queue (
                    id SERIAL PRIMARY KEY,
                    paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
                    enrichment_type TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT NOW(),
                    processed_at TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT
                );
            """)
            
            # Create trigger function
            cur.execute("""
                CREATE OR REPLACE FUNCTION queue_enrichment_task()
                RETURNS TRIGGER AS $$
                BEGIN
                    -- Queue 2D embedding enrichment for new papers
                    IF NEW.doctrove_embedding IS NOT NULL AND NEW.doctrove_embedding_2d IS NULL THEN
                        INSERT INTO enrichment_queue (paper_id, enrichment_type, priority)
                        VALUES (NEW.doctrove_paper_id, 'embedding_2d', 1);
                    END IF;
                    
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Create trigger
            cur.execute("""
                DROP TRIGGER IF EXISTS trigger_queue_enrichment ON doctrove_papers;
                CREATE TRIGGER trigger_queue_enrichment
                    AFTER INSERT OR UPDATE ON doctrove_papers
                    FOR EACH ROW
                    EXECUTE FUNCTION queue_enrichment_task();
            """)
            
            conn.commit()
            logger.debug("Async enrichment triggers set up successfully")


def start_async_enrichment_service():
    """
    Start the asynchronous enrichment service.
    This should be called after the main application starts.
    """
    connection_factory = create_connection_factory()
    
    # Set up database triggers
    setup_async_enrichment_triggers(connection_factory)
    
    # Create and start enrichment worker
    worker = AsyncEnrichmentWorker(connection_factory)
    worker.start()
    
    return worker


# Example usage
if __name__ == "__main__":
    # Start the enrichment service
    worker = start_async_enrichment_service()
    
    try:
        # Keep the service running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping enrichment service...")
        worker.stop()
        print("Enrichment service stopped") 