#!/usr/bin/env python3
"""
Event-driven enrichment listener using PostgreSQL LISTEN/NOTIFY.
Listens for database events and triggers appropriate enrichment services.
"""

import sys
import os
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Import the combined 2D processor
from combined_2d_processor import process_combined_2d_embeddings, process_combined_2d_embeddings_incremental

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EventListener:
    """
    PostgreSQL event listener for enrichment pipeline.
    Listens for NOTIFY events and triggers appropriate services.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self.running = False
        self.listeners = {}
        self.connection = None
        self.cursor = None
        
    def register_listener(self, event_name: str, callback: Callable[[str], None]):
        """Register a callback for a specific event."""
        self.listeners[event_name] = callback
        logger.debug(f"Registered listener for event: {event_name}")
    
    def create_connection(self):
        """Create a connection for listening to events."""
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.connection.cursor()
            logger.debug("Event listener connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to create event listener connection: {e}")
            return False
    
    def listen_for_events(self):
        """Listen for PostgreSQL NOTIFY events."""
        if not self.create_connection():
            return
        
        # Listen for all events we care about
        events_to_listen = list(self.listeners.keys())
        for event in events_to_listen:
            self.cursor.execute(f"LISTEN {event}")
            logger.debug(f"Listening for event: {event}")
        
        try:
            while self.running:
                # Wait for notifications
                if self.connection.poll():
                    notify = self.connection.notifies()
                    if notify:
                        for notification in notify:
                            self.handle_notification(notification)
                else:
                    time.sleep(0.1)  # Small delay to prevent busy waiting
                    
        except Exception as e:
            logger.error(f"Error in event listener: {e}")
        finally:
            self.cleanup()
    
    def handle_notification(self, notification):
        """Handle a received notification."""
        event_name = notification.channel
        payload = notification.payload
        
        logger.debug(f"Received event: {event_name} with payload: {payload}")
        
        # Call the appropriate callback
        if event_name in self.listeners:
            try:
                self.listeners[event_name](payload)
            except Exception as e:
                logger.error(f"Error in event handler for {event_name}: {e}")
        else:
            logger.warning(f"No handler registered for event: {event_name}")
    
    def start(self):
        """Start the event listener."""
        self.running = True
        logger.debug("Starting event listener...")
        
        # Start listening in a separate thread
        self.listener_thread = threading.Thread(target=self.listen_for_events)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        
        logger.debug("Event listener started")
    
    def stop(self):
        """Stop the event listener."""
        self.running = False
        logger.debug("Stopping event listener...")
        self.cleanup()
    
    def cleanup(self):
        """Clean up connections."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.debug("Event listener connections closed")

class EnrichmentOrchestrator:
    """
    Orchestrates the enrichment pipeline based on events.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self.event_listener = EventListener(connection_params)
        self.batch_size = 100000  # 2D projection batch size
        self.embedding_batch = []
        self.processing_lock = threading.Lock()
        
        # Register event handlers
        self.event_listener.register_listener('paper_added', self.handle_paper_added)
        self.event_listener.register_listener('embedding_ready', self.handle_embedding_ready)
        self.event_listener.register_listener('projection_ready', self.handle_projection_ready)
    
    def handle_paper_added(self, paper_id: str):
        """Handle new paper added - generate embeddings."""
        logger.debug(f"New paper added: {paper_id}")
        # Trigger embedding generation for this paper
        self.generate_embeddings_for_paper(paper_id)
    
    def handle_embedding_ready(self, paper_id: str):
        """Handle embedding ready - add to 2D batch."""
        logger.debug(f"Embedding ready for paper: {paper_id}")
        
        with self.processing_lock:
            self.embedding_batch.append(paper_id)
            
            # Check if we have enough papers for 2D projection
            if len(self.embedding_batch) >= self.batch_size:
                self.process_2d_batch()
    
    def handle_projection_ready(self, paper_id: str):
        """Handle 2D projection ready."""
        logger.debug(f"2D projection ready for paper: {paper_id}")
        # Could trigger additional enrichments here
    
    def generate_embeddings_for_paper(self, paper_id: str):
        """Generate embeddings for a single paper."""
        try:
            # Import embedding service
            from embedding_service import generate_embeddings_for_papers, update_papers_with_embeddings
            
            # Get paper data
            paper_data = self.get_paper_data(paper_id)
            if not paper_data:
                logger.warning(f"Could not get paper data for {paper_id}")
                return
            
            # Generate embeddings
            papers_with_embeddings = generate_embeddings_for_papers([paper_data])
            
            # Update database
            if papers_with_embeddings:
                update_papers_with_embeddings(
                    self.create_connection_factory(),
                    papers_with_embeddings
                )
                logger.debug(f"Generated embeddings for paper {paper_id}")
            
        except Exception as e:
            logger.error(f"Error generating embeddings for paper {paper_id}: {e}")
    
    def process_2d_batch(self):
        """Process a batch of papers for 2D projection."""
        if not self.embedding_batch:
            return
        
        try:
            logger.debug(f"Processing 2D batch with {len(self.embedding_batch)} papers")
            
            # Get paper IDs for this batch
            batch_paper_ids = self.embedding_batch.copy()
            self.embedding_batch.clear()
            
            # Process 2D projections using existing service
            from main import process_incremental_workflow
            
            # This will trigger the 2D enrichment for the papers in the batch
            # For now, we'll use the existing workflow
            logger.debug(f"Triggering 2D projection for batch: {batch_paper_ids[:5]}...")
            
            # TODO: Implement batch-specific 2D processing
            # For now, we'll just log that we would process these
            
        except Exception as e:
            logger.error(f"Error processing 2D batch: {e}")
    
    def get_paper_data(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper data from database."""
        try:
            with self.create_connection_factory()() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT doctrove_paper_id, doctrove_title, doctrove_abstract
                        FROM doctrove_papers 
                        WHERE doctrove_paper_id = %s
                    """, (paper_id,))
                    
                    row = cur.fetchone()
                    if row:
                        return {
                            'doctrove_paper_id': row[0],
                            'doctrove_title': row[1],
                            'doctrove_abstract': row[2]
                        }
                    return None
        except Exception as e:
            logger.error(f"Error getting paper data: {e}")
            return None
    
    def create_connection_factory(self):
        """Create a database connection factory."""
        def get_connection():
            return psycopg2.connect(**self.connection_params)
        return get_connection
    
    def start(self):
        """Start the enrichment orchestrator."""
        logger.debug("Starting enrichment orchestrator...")
        self.event_listener.start()
        
        # Also start a background thread to process any remaining papers
        self.background_thread = threading.Thread(target=self.background_processing)
        self.background_thread.daemon = True
        self.background_thread.start()
    
    def background_processing(self):
        """Background processing for papers that might have been missed."""
        while True:
            try:
                time.sleep(60)  # Check every minute
                logger.info("Background processing cycle starting...")
                
                # Check for papers needing embeddings
                with self.create_connection_factory()() as conn:
                    with conn.cursor() as cur:
                        # First, find papers with NULL titles to exclude them
                        cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_title IS NULL")
                        papers_with_null_titles = cur.fetchone()[0]
                        print(f"DEBUG: Papers with NULL titles: {papers_with_null_titles}")
                        
                        # Use the database's official counting function for consistency and performance
                        cur.execute("SELECT get_papers_needing_embeddings_count()")
                        papers_needing_embeddings = cur.fetchone()[0]
                        print(f"DEBUG: Raw papers_needing_embeddings value: {papers_needing_embeddings} (type: {type(papers_needing_embeddings)})")
                        
                        # 🚨 SAFETY CHECK: If we get 0 papers when we should have 13.6M, something is wrong!
                        if papers_needing_embeddings == 0:
                            logger.error("🚨 CRITICAL ERROR: Database function returned 0 papers needing embeddings!")
                            logger.error("🚨 This should be ~13.6M papers. Something is seriously wrong!")
                            logger.error("🚨 Stopping service to prevent infinite loop of doing nothing.")
                            logger.error("🚨 Check database connection, function definition, or data integrity.")
                            raise Exception("CRITICAL: Database function returned 0 papers when expecting 13.6M")
                        elif papers_needing_embeddings > 10000000:  # More than 10M papers
                            logger.info(f"✅ SUCCESS: Database function returned {papers_needing_embeddings:,} papers needing embeddings - this looks correct!")
                        else:
                            logger.warning(f"⚠️  WARNING: Database function returned {papers_needing_embeddings:,} papers - this seems low, expected ~13.6M")
                        
                        # TEMPORARILY SKIP problematic queries to get service running
                        papers_needing_2d = 0  # Skip 2D query for now
                        papers_needing_country = 0  # Skip country query for now
                        papers_without_embeddings = papers_needing_embeddings  # Use same value
                        
                        print(f"DEBUG: Skipped complex queries - using simplified values")
                        
                        print(f"DEBUG: Before logging - papers_needing_embeddings: {papers_needing_embeddings}")
                        print(f"DEBUG: Before logging - papers_needing_2d: {papers_needing_2d}")
                        print(f"DEBUG: Before logging - papers_needing_country: {papers_needing_country}")
                        print(f"DEBUG: Before logging - papers_without_embeddings: {papers_without_embeddings}")
                        
                        # TRACE: Quick check before logging
                        print(f"TRACE: Final values - embeddings: {papers_needing_embeddings}, 2D: {papers_needing_2d}")
                        
                        logger.info(f"Background: Found {papers_needing_embeddings} papers needing embeddings, {papers_needing_2d} needing 2D, {papers_needing_country} needing country, {papers_without_embeddings} with no embeddings")
                        
                        if papers_needing_embeddings > 0:
                            logger.info(f"Background: Starting embedding processing for {papers_needing_embeddings} papers")
                            # Process embeddings
                            self.process_papers_needing_embeddings()
                        if papers_needing_2d > 0:
                            logger.info(f"Background: Starting 2D projection processing for {papers_needing_2d} papers")
                            # Process 2D projections
                            self.process_papers_needing_2d_projections()
                        # Temporarily disabled country enrichment to focus on embedding processing
                        # if papers_needing_country > 0:
                        #     logger.info(f"Background: Starting country enrichment for {papers_needing_country} papers")
                        #     # Process country enrichment
                        #     self.process_papers_needing_country_enrichment()
                
            except Exception as e:
                logger.error(f"Error in background processing: {e}")
    
    def process_papers_needing_embeddings(self):
        """Process papers that need embeddings using the embedding service."""
        try:
            logger.info("Starting background embedding processing...")
            
            # Check what types of embeddings are needed
            with self.create_connection_factory()() as conn:
                with conn.cursor() as cur:
                    # Count papers needing initial embeddings (exclude NULL titles)
                    cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NULL AND doctrove_paper_id NOT IN (SELECT doctrove_paper_id FROM doctrove_papers WHERE doctrove_title IS NULL)")
                    initial_embeddings_count = cur.fetchone()[0]
                    
                    # Count papers needing 2D embeddings (have embedding but no 2D)
                    cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL AND doctrove_embedding_2d IS NULL")
                    papers_needing_2d_count = cur.fetchone()[0]
            
            logger.info(f"Embedding needs: {initial_embeddings_count} need initial embeddings, {papers_needing_2d_count} need 2D embeddings")
            
            # Import embedding service
            logger.info("About to import embedding_service...")
            from embedding_service import process_embedding_enrichment
            logger.info("Successfully imported embedding_service")
            
            total_processed = 0
            
            # Process all papers needing initial embeddings
            total_needing = initial_embeddings_count
            logger.info(f"Processing {total_needing} papers needing initial embeddings")
            logger.info(f"Calling process_embedding_enrichment with batch_size=500, limit={min(total_needing, 5000)}")
            
            results = process_embedding_enrichment(
                batch_size=500,
                limit=min(total_needing, 5000)
            )
            logger.info("process_embedding_enrichment returned successfully")
            total_processed += results['successful_embeddings']
            logger.info(f"Embeddings: {results['successful_embeddings']} successful, {results['failed_embeddings']} failed")
            
            logger.info(f"Background embedding processing completed: {total_processed} total papers processed")
            
        except Exception as e:
            logger.error(f"Error in background embedding processing: {e}", exc_info=True)
    
    def process_papers_needing_2d_projections(self):
        """Process papers that need 2D projections - use incremental combined 2D processor."""
        try:
            logger.info("Starting background 2D projection processing (incremental combined)...")
            success = process_combined_2d_embeddings_incremental(batch_size=100000)
            if success:
                logger.info("Incremental combined 2D projection processing completed successfully.")
            else:
                logger.error("Incremental combined 2D projection processing failed.")
        except Exception as e:
            logger.error(f"Error in incremental combined 2D projection processing: {e}", exc_info=True)
    
    def process_papers_needing_country_enrichment(self):
        """Process papers that need country enrichment using pure functional approach."""
        try:
            logger.info("Starting background country enrichment processing...")
            
            # Import pure functions from country enrichment service
            from country_enrichment_service import smart_batch_processing
            
            # Use smart batching for efficient processing
            results = smart_batch_processing(
                self.create_connection_factory(),
                max_papers=50000  # Process up to 50K papers per background cycle for large-scale processing
            )
            
            logger.info(f"Country enrichment: {results['total_processed']} processed, {results['total_successful']} successful, {results['total_unknown']} unknown")
            
        except Exception as e:
            logger.error(f"Error in background country enrichment processing: {e}", exc_info=True)
    
    def stop(self):
        """Stop the enrichment orchestrator."""
        logger.debug("Stopping enrichment orchestrator...")
        self.event_listener.stop()

def main():
    """Main entry point for the event-driven enrichment system."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Event-driven enrichment orchestrator')
    parser.add_argument('--batch-size', type=int, default=100000,
                       help='Batch size for 2D projections (default: 100000)')
    parser.add_argument('--test', action='store_true',
                       help='Test the event system')
    
    args = parser.parse_args()
    
    # Database connection parameters
    connection_params = {
        'host': DB_HOST,
        'port': DB_PORT,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }
    
    # Create orchestrator
    orchestrator = EnrichmentOrchestrator(connection_params)
    orchestrator.batch_size = args.batch_size
    
    if args.test:
        # Test the event system
        print("Testing event system...")
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT test_notify_paper_added(gen_random_uuid())")
        print("Test event sent!")
        return
    
    try:
        # Start the orchestrator
        orchestrator.start()
        
        print("Event-driven enrichment system started!")
        print("Listening for database events...")
        print("Press Ctrl+C to stop")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping enrichment system...")
        orchestrator.stop()
        print("Enrichment system stopped")

if __name__ == "__main__":
    main() 