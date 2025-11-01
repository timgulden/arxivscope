#!/usr/bin/env python3
"""
Queue-based 2D Embedding Worker

This worker processes papers from the existing papers_needing_2d_embeddings queue.
Uses functional programming principles while leveraging the existing database infrastructure.
"""

import logging
import numpy as np
import pickle
import os
import sys
import time
import random
from typing import List, Tuple, Optional, Callable, NamedTuple
from functools import partial
import psycopg2
from psycopg2.extras import RealDictCursor
import umap.umap_ as umap
from sklearn.preprocessing import StandardScaler
import argparse

# Add paths for imports
sys.path.append('../doctrove-api')
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UMAP configuration
UMAP_CONFIG = {
    'n_components': 2,
    'n_neighbors': 15,
    'min_dist': 0.1,
    'metric': 'cosine',
    'random_state': None,
    'low_memory': True,
    'verbose': False
}

# Simple named tuples for immutable data structures
PaperEmbedding = NamedTuple('PaperEmbedding', [
    ('paper_id', str),
    ('embedding_1d', np.ndarray),
    ('embedding_2d', Optional[np.ndarray])
])

ProcessingResult = NamedTuple('ProcessingResult', [
    ('successful_count', int),
    ('failed_count', int),
    ('total_processed', int),
    ('batch_index', int)
])

UMAPModel = NamedTuple('UMAPModel', [
    ('model', umap.UMAP),
    ('scaler', StandardScaler),
    ('model_path', str)
])

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

def parse_embedding_data(embedding_data) -> np.ndarray:
    """Parse embedding data into numpy array (pure function)."""
    if isinstance(embedding_data, str):
        embedding_data = embedding_data.strip('[]').split(',')
        return np.array([float(x.strip()) for x in embedding_data], dtype=np.float32)
    else:
        return np.array(embedding_data, dtype=np.float32)

def claim_papers_from_queue(
    connection_factory: Callable, 
    batch_size: int = 100
) -> List[PaperEmbedding]:
    """
    Claim papers from the papers_needing_2d_embeddings queue using FOR UPDATE SKIP LOCKED.
    
    Args:
        connection_factory: Function to create database connections
        batch_size: Number of papers to claim
    
    Returns:
        List of claimed PaperEmbedding objects
    """
    with connection_factory() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Claim papers from queue with atomic operation
            cur.execute("""
                WITH to_process AS (
                    SELECT q.paper_id, dp.doctrove_embedding
                    FROM papers_needing_2d_embeddings q
                    JOIN doctrove_papers dp ON q.paper_id = dp.doctrove_paper_id
                    WHERE dp.doctrove_embedding IS NOT NULL
                    ORDER BY q.priority DESC, q.added_at ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                )
                DELETE FROM papers_needing_2d_embeddings q
                WHERE q.paper_id IN (SELECT paper_id FROM to_process)
                RETURNING q.paper_id, (SELECT doctrove_embedding FROM to_process WHERE paper_id = q.paper_id) as doctrove_embedding
            """, (batch_size,))
            
            results = cur.fetchall()
            conn.commit()
    
    # Use functional approach: map and filter
    def create_paper_embedding(paper_data):
        """Create PaperEmbedding from database row (pure function)."""
        try:
            embedding_1d = parse_embedding_data(paper_data['doctrove_embedding'])
            return PaperEmbedding(
                paper_id=paper_data['paper_id'],
                embedding_1d=embedding_1d,
                embedding_2d=None
            )
        except Exception as e:
            logger.warning(f"Failed to parse embedding for paper {paper_data['paper_id']}: {e}")
            return None
    
    # Map and filter out None results
    papers = list(filter(None, map(create_paper_embedding, results)))
    
    return papers

def count_papers_in_queue(connection_factory: Callable) -> int:
    """
    Count papers in the 2D embedding queue (pure function).
    
    Args:
        connection_factory: Function to create database connections
    
    Returns:
        Count of papers in queue
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM papers_needing_2d_embeddings")
            return cur.fetchone()[0]

def load_umap_model(model_path: str = 'umap_model.pkl') -> Optional[UMAPModel]:
    """
    Load existing UMAP model (pure function).
    
    Args:
        model_path: Path to the model file
    
    Returns:
        UMAPModel object if successful, None otherwise
    """
    if not os.path.exists(model_path):
        return None
    
    try:
        with open(model_path, 'rb') as f:
            loaded_data = pickle.load(f)
        
        # Handle both old format (just model) and new format (model, scaler)
        if isinstance(loaded_data, tuple) and len(loaded_data) == 2:
            model, scaler = loaded_data
        else:
            # Old format - just the model, need to create a new scaler
            model = loaded_data
            scaler = None
        
        return UMAPModel(model=model, scaler=scaler, model_path=model_path)
    except Exception as e:
        logger.error(f"Failed to load UMAP model from {model_path}: {e}")
        return None

def create_scaler_from_embeddings(embeddings: List[np.ndarray]) -> StandardScaler:
    """
    Create a scaler from embeddings (pure function).
    
    Args:
        embeddings: List of embedding arrays
    
    Returns:
        Fitted StandardScaler
    """
    embeddings_array = np.array(embeddings)
    scaler = StandardScaler()
    scaler.fit(embeddings_array)
    return scaler

def transform_embeddings_to_2d(papers: List[PaperEmbedding], umap_model: UMAPModel) -> List[PaperEmbedding]:
    """
    Transform 1D embeddings to 2D using UMAP model (pure function).
    
    Args:
        papers: List of PaperEmbedding objects
        umap_model: UMAPModel object
    
    Returns:
        List of PaperEmbedding objects with 2D embeddings
    """
    if not papers:
        return []
    
    # Extract 1D embeddings
    embeddings_1d = [paper.embedding_1d for paper in papers]
    embeddings_array = np.array(embeddings_1d)
    
    # Use existing scaler or create new one
    if umap_model.scaler is None:
        scaler = create_scaler_from_embeddings(embeddings_1d)
    else:
        scaler = umap_model.scaler
    
    # Transform to 2D
    embeddings_scaled = scaler.transform(embeddings_array)
    embeddings_2d = umap_model.model.transform(embeddings_scaled)
    
    # Create new PaperEmbedding objects with 2D embeddings using functional approach
    def add_2d_embedding(paper_emb_2d_tuple):
        """Add 2D embedding to paper (pure function)."""
        paper, emb_2d = paper_emb_2d_tuple
        return PaperEmbedding(
            paper_id=paper.paper_id,
            embedding_1d=paper.embedding_1d,
            embedding_2d=emb_2d
        )
    
    return list(map(add_2d_embedding, zip(papers, embeddings_2d)))

def save_2d_embeddings_batch(papers_with_2d: List[PaperEmbedding], connection_factory: Callable) -> ProcessingResult:
    """
    Save 2D embeddings to database (pure function with controlled side effects).
    
    Args:
        papers_with_2d: List of PaperEmbedding objects with 2D embeddings
        connection_factory: Function to create database connections
    
    Returns:
        ProcessingResult object
    """
    if not papers_with_2d:
        return ProcessingResult(successful_count=0, failed_count=0, total_processed=0, batch_index=0)
    
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Prepare data for batch update using functional approach
                def create_update_data(paper):
                    """Create update data tuple (pure function)."""
                    x, y = paper.embedding_2d[0], paper.embedding_2d[1]
                    point_str = f"({x},{y})"
                    return (point_str, paper.paper_id)
                
                update_data = list(map(create_update_data, papers_with_2d))
                
                # Update papers with 2D embeddings
                cur.executemany("""
                    UPDATE doctrove_papers 
                    SET doctrove_embedding_2d = %s::point
                    WHERE doctrove_paper_id = %s
                """, update_data)
                
                # Commit the transaction
                conn.commit()
                
                successful_count = len(papers_with_2d)
                logger.info(f"Successfully saved {successful_count} 2D embeddings to database")
                
    except Exception as e:
        logger.error(f"Failed to save 2D embeddings batch: {e}")
        return ProcessingResult(successful_count=0, failed_count=len(papers_with_2d), total_processed=len(papers_with_2d), batch_index=0)
    
    return ProcessingResult(
        successful_count=successful_count,
        failed_count=0,
        total_processed=len(papers_with_2d),
        batch_index=0
    )

def process_2d_embeddings_batch_from_queue(
    connection_factory: Callable,
    umap_model: UMAPModel,
    batch_size: int = 100
) -> ProcessingResult:
    """
    Process a single batch of 2D embeddings from the queue (pure function).
    
    Args:
        connection_factory: Function to create database connections
        umap_model: Pre-loaded UMAP model
        batch_size: Number of papers to process
    
    Returns:
        ProcessingResult object
    """
    start_time = time.time()
    
    # Claim papers from queue
    logger.info(f"Claiming {batch_size} papers from queue...")
    claim_start = time.time()
    papers = claim_papers_from_queue(connection_factory, batch_size)
    claim_time = time.time() - claim_start
    logger.info(f"Claimed {len(papers)} papers in {claim_time:.2f}s")
    
    if not papers:
        logger.info("No papers available for processing")
        return ProcessingResult(successful_count=0, failed_count=0, total_processed=0, batch_index=0)
    
    # Transform to 2D
    logger.info(f"Transforming {len(papers)} embeddings to 2D...")
    transform_start = time.time()
    papers_with_2d = transform_embeddings_to_2d(papers, umap_model)
    transform_time = time.time() - transform_start
    logger.info(f"Transformed embeddings in {transform_time:.2f}s")
    
    # Save to database
    logger.info(f"Saving {len(papers_with_2d)} 2D embeddings to database...")
    save_start = time.time()
    result = save_2d_embeddings_batch(papers_with_2d, connection_factory)
    save_time = time.time() - save_start
    logger.info(f"Saved embeddings in {save_time:.2f}s")
    
    total_time = time.time() - start_time
    logger.info(f"Total batch processing time: {total_time:.2f}s ({len(papers)} papers = {len(papers)/total_time:.1f} papers/sec)")
    
    return result

def process_2d_embeddings_continuous_from_queue(
    connection_factory: Callable,
    batch_size: int = 100,
    model_path: str = 'umap_model.pkl',
    sleep_seconds: int = 10,
    worker_id: str = "worker-1"
) -> bool:
    """
    Process 2D embeddings continuously from the queue with adaptive backoff.
    
    Args:
        connection_factory: Function to create database connections
        batch_size: Number of papers to process per batch
        model_path: Path to UMAP model
        sleep_seconds: Base sleep seconds when no papers to process
        worker_id: Unique worker identifier
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting continuous 2D embedding processing from queue (batch_size={batch_size}, sleep={sleep_seconds}s, worker={worker_id})...")
        
        # Check if UMAP model exists
        if not os.path.exists(model_path):
            logger.error(f"No UMAP model found at {model_path}")
            return False
        
        # Pre-load UMAP model once (avoid reloading for each batch)
        logger.info("Pre-loading UMAP model...")
        umap_model = load_umap_model(model_path)
        if umap_model is None:
            logger.error(f"Failed to load UMAP model from {model_path}")
            return False
        logger.info("UMAP model loaded successfully")
        
        total_processed = 0
        batch_index = 0
        consecutive_empty_batches = 0
        max_empty_batches = 3  # Log after 3 consecutive empty batches
        
        while True:
            try:
                # Check queue size
                queue_size = count_papers_in_queue(connection_factory)
                logger.info(f"Queue size: {queue_size} papers")
                
                # Process batch from queue
                result = process_2d_embeddings_batch_from_queue(
                    connection_factory=connection_factory,
                    umap_model=umap_model,
                    batch_size=batch_size
                )
                
                if result.total_processed == 0:
                    consecutive_empty_batches += 1
                    if consecutive_empty_batches >= max_empty_batches:
                        logger.info(f"Queue idle - no papers available (empty batch #{consecutive_empty_batches})")
                        consecutive_empty_batches = 0  # Reset counter after logging
                    
                    # Adaptive backoff with jitter
                    jitter = random.uniform(0.9, 1.1)  # ±10% jitter
                    actual_sleep = sleep_seconds * jitter
                    logger.info(f"Sleeping for {actual_sleep:.1f}s (base: {sleep_seconds}s, jitter: {jitter:.2f})")
                    time.sleep(actual_sleep)
                    continue
                
                # Reset empty batch counter when we process papers
                consecutive_empty_batches = 0
                total_processed += result.successful_count
                batch_index += 1
                
                logger.info(f"Batch {batch_index}: {result.successful_count} successful, {result.failed_count} failed (Total: {total_processed})")
                
                # If we got fewer papers than batch_size, we might be caught up
                if result.total_processed < batch_size:
                    logger.info(f"Small batch ({result.total_processed} papers) - might be caught up. Brief pause...")
                    time.sleep(2)  # Brief pause before next claim
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal. Stopping continuous processing...")
                break
            except Exception as e:
                logger.error(f"Error in continuous processing batch: {e}")
                logger.info(f"Sleeping for {sleep_seconds} seconds before retrying...")
                time.sleep(sleep_seconds)
                continue
        
        logger.info(f"Continuous 2D processing stopped. Total embeddings processed: {total_processed}")
        return True
        
    except Exception as e:
        logger.error(f"Error in continuous 2D processing: {e}")
        return False

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Queue-based 2D Embedding Worker')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Batch size for processing (default: 100)')
    parser.add_argument('--model-path', type=str, default='umap_model.pkl',
                       help='Path to UMAP model file (default: umap_model.pkl)')
    parser.add_argument('--sleep-seconds', type=int, default=10,
                       help='Sleep seconds when no papers to process (default: 10)')
    parser.add_argument('--worker-id', type=str, default=None,
                       help='Worker ID for multi-worker support (default: auto-generated)')
    
    args = parser.parse_args()
    
    # Generate worker ID if not provided
    if args.worker_id is None:
        args.worker_id = f"worker-{os.getpid()}-{int(time.time())}"
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create connection factory
    connection_factory = create_connection_factory()
    
    # Check if model exists
    if not os.path.exists(args.model_path):
        logger.error(f"No UMAP model found at {args.model_path}")
        logger.error("Please create a UMAP model first using the functional_2d_processor.py --remap")
        sys.exit(1)
    
    # Run continuous 2D embedding processing from queue
    process_2d_embeddings_continuous_from_queue(
        connection_factory=connection_factory,
        batch_size=args.batch_size,
        model_path=args.model_path,
        sleep_seconds=args.sleep_seconds,
        worker_id=args.worker_id
    )

















