#!/usr/bin/env python3
"""
Fast Event-driven Enrichment System
Optimized for speed - no expensive counting queries
"""

import os
import sys
import time
import logging
import threading
import signal
from typing import Dict, Callable, Optional

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

# Import database connection
from db import create_connection_factory

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

class FastEventListener:
    """Fast event listener that skips expensive counting queries."""
    
    def __init__(self):
        self.running = False
        self.listeners: Dict[str, Callable] = {}
        self.listener_thread: Optional[threading.Thread] = None
        self.create_connection_factory = create_connection_factory()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def register_listener(self, event_name: str, callback: Callable):
        """Register a callback for an event."""
        self.listeners[event_name] = callback
        logger.info(f"Registered listener for event: {event_name}")
    
    def start(self):
        """Start the event listener."""
        self.running = True
        logger.info("Fast event listener started")
        
        # Start background processing in a separate thread
        self.background_thread = threading.Thread(target=self._background_processing)
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
        """Stop the event listener."""
        self.running = False
        logger.info("Fast event listener stopped")
    
    def _background_processing(self):
        """Background processing loop - optimized for speed."""
        logger.info("Fast background processing started")
        
        while self.running:
            try:
                logger.info("🚀 Fast processing cycle starting...")
                
                # Process embeddings directly without counting
                self._process_embeddings_fast()
                
                # Wait before next cycle
                logger.info("⏳ Waiting 30 seconds before next cycle...")
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in fast background processing: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _process_embeddings_fast(self):
        """Process embeddings without expensive counting queries."""
        try:
            logger.info("Starting fast embedding processing...")
            
            # Import embedding service
            logger.info("About to import embedding_service...")
            from embedding_service import process_embedding_enrichment
            logger.info("Successfully imported embedding_service")
            
            # Process embeddings with reasonable batch size
            batch_size = 500
            limit = 5000
            
            logger.info(f"Calling process_embedding_enrichment with batch_size={batch_size}, limit={limit}")
            result = process_embedding_enrichment(batch_size=batch_size, limit=limit)
            logger.info("process_embedding_enrichment returned successfully")
            
            # Log results
            if result and 'successful' in result:
                successful = result['successful']
                failed = result.get('failed', 0)
                logger.info(f"Embeddings: {successful} successful, {failed} failed")
            else:
                logger.info("Embeddings: Processing completed")
            
            logger.info("Fast embedding processing completed")
            
        except Exception as e:
            logger.error(f"Error in fast embedding processing: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function."""
    print("Fast Event-driven enrichment system started!")
    print("Listening for database events...")
    print("Press Ctrl+C to stop")
    
    # Create and start the event listener
    listener = FastEventListener()
    
    try:
        listener.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    finally:
        listener.stop()

if __name__ == "__main__":
    main()
