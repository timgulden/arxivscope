#!/usr/bin/env python3
"""
Functional 2D Embedding Processor

This module processes 1D embeddings to 2D using UMAP in a functional programming style.
All functions are pure, immutable, and side-effect free.
"""

import logging
import numpy as np
import pickle
import os
import sys
import time
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass, field
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

@dataclass(frozen=True)
class PaperEmbedding:
    """Immutable representation of a paper's embedding data."""
    paper_id: str
    embedding_1d: np.ndarray
    embedding_2d: Optional[np.ndarray] = None

@dataclass(frozen=True)
class ProcessingBatch:
    """Immutable representation of a processing batch."""
    papers: List[PaperEmbedding]
    batch_index: int
    total_batches: int

@dataclass(frozen=True)
class ProcessingResult:
    """Immutable result of processing operations."""
    successful_count: int
    failed_count: int
    total_processed: int
    batch_index: int

@dataclass(frozen=True)
class UMAPModel:
    """Immutable representation of a UMAP model."""
    model: umap.UMAP
    scaler: StandardScaler
    model_path: str

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

def load_papers_needing_2d_embeddings(connection_factory: Callable, batch_size: int = 10000, offset: int = 0) -> List[PaperEmbedding]:
    """
    Load papers that need 2D embeddings (pure function).
    
    Args:
        connection_factory: Function to create database connections
        batch_size: Number of papers to load
        offset: Offset for pagination
    
    Returns:
        List of PaperEmbedding objects
    """
    papers = []
    
    with connection_factory() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_embedding
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NOT NULL 
                AND doctrove_embedding_2d IS NULL
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            results = cur.fetchall()
    
    for paper in results:
        try:
            embedding_1d = parse_embedding_data(paper['doctrove_embedding'])
            papers.append(PaperEmbedding(
                paper_id=paper['doctrove_paper_id'],
                embedding_1d=embedding_1d
            ))
        except Exception as e:
            logger.warning(f"Failed to parse embedding for paper {paper['doctrove_paper_id']}: {e}")
            continue
    
    return papers

def count_papers_needing_2d_embeddings(connection_factory: Callable) -> int:
    """
    Count papers that need 2D embeddings (pure function).
    
    Args:
        connection_factory: Function to create database connections
    
    Returns:
        Count of papers needing 2D embeddings
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NOT NULL 
                AND doctrove_embedding_2d IS NULL
            """)
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
    
    # Create new PaperEmbedding objects with 2D embeddings
    return [
        PaperEmbedding(
            paper_id=paper.paper_id,
            embedding_1d=paper.embedding_1d,
            embedding_2d=emb_2d
        )
        for paper, emb_2d in zip(papers, embeddings_2d)
    ]

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
                # Prepare data for batch update
                update_data = []
                for paper in papers_with_2d:
                    # Convert numpy array to PostgreSQL point format
                    x, y = paper.embedding_2d[0], paper.embedding_2d[1]
                    point_str = f"({x},{y})"
                    update_data.append((point_str, paper.paper_id))
                
                # Use executemany for efficient batch update
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

def process_2d_embeddings_batch_with_model(
    connection_factory: Callable,
    umap_model: UMAPModel,
    batch_size: int = 10000,
    offset: int = 0
) -> ProcessingResult:
    """
    Process a single batch of 2D embeddings with pre-loaded model (pure function).
    
    Args:
        connection_factory: Function to create database connections
        umap_model: Pre-loaded UMAP model
        batch_size: Number of papers to process
        offset: Offset for pagination
    
    Returns:
        ProcessingResult object
    """
    start_time = time.time()
    
    # Load papers needing 2D embeddings
    logger.info(f"Loading {batch_size} papers from database...")
    load_start = time.time()
    papers = load_papers_needing_2d_embeddings(connection_factory, batch_size, offset)
    load_time = time.time() - load_start
    logger.info(f"Loaded {len(papers)} papers in {load_time:.2f}s")
    
    if not papers:
        logger.info("No papers need 2D embeddings")
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

def process_2d_embeddings_incremental(
    connection_factory: Callable,
    batch_size: int = 10000,
    model_path: str = 'umap_model.pkl'
) -> bool:
    """
    Process all papers needing 2D embeddings incrementally (pure function).
    
    Args:
        connection_factory: Function to create database connections
        batch_size: Number of papers to process per batch
        model_path: Path to UMAP model
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting incremental 2D embedding processing (batch_size={batch_size})...")
        
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
        
        while True:
            # Process batch with pre-loaded model
            result = process_2d_embeddings_batch_with_model(
                connection_factory=connection_factory,
                umap_model=umap_model,
                batch_size=batch_size,
                offset=batch_index * batch_size
            )
            
            if result.total_processed == 0:
                logger.info("No more papers need 2D processing")
                break
            
            total_processed += result.successful_count
            batch_index += 1
            
            logger.info(f"Batch {batch_index}: {result.successful_count} successful, {result.failed_count} failed")
            
            # If we got fewer papers than batch_size, we're done
            if result.total_processed < batch_size:
                break
        
        logger.info(f"Incremental 2D processing completed: {total_processed} total embeddings processed")
        return True
        
    except Exception as e:
        logger.error(f"Error in incremental 2D processing: {e}")
        return False

def process_2d_embeddings_continuous(
    connection_factory: Callable,
    batch_size: int = 10000,
    model_path: str = 'umap_model.pkl',
    sleep_seconds: int = 10
) -> bool:
    """
    Process 2D embeddings continuously, handling new embeddings as they arrive.
    
    Args:
        connection_factory: Function to create database connections
        batch_size: Number of papers to process per batch
        model_path: Path to UMAP model
        sleep_seconds: Seconds to sleep when no papers need processing
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting continuous 2D embedding processing (batch_size={batch_size}, sleep={sleep_seconds}s)...")
        
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
                # Process batch with pre-loaded model
                result = process_2d_embeddings_batch_with_model(
                    connection_factory=connection_factory,
                    umap_model=umap_model,
                    batch_size=batch_size,
                    offset=0  # Always start from 0 for continuous processing
                )
                
                if result.total_processed == 0:
                    consecutive_empty_batches += 1
                    if consecutive_empty_batches >= max_empty_batches:
                        logger.info(f"No papers need 2D processing (empty batch #{consecutive_empty_batches}). Sleeping for {sleep_seconds} seconds...")
                        consecutive_empty_batches = 0  # Reset counter after logging
                    time.sleep(sleep_seconds)
                    continue
                
                # Reset empty batch counter when we process papers
                consecutive_empty_batches = 0
                total_processed += result.successful_count
                batch_index += 1
                
                logger.info(f"Batch {batch_index}: {result.successful_count} successful, {result.failed_count} failed (Total: {total_processed})")
                
                # If we got fewer papers than batch_size, we might be caught up
                if result.total_processed < batch_size:
                    logger.info(f"Small batch ({result.total_processed} papers) - might be caught up. Sleeping for {sleep_seconds} seconds...")
                    time.sleep(sleep_seconds)
                
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

def prompt_user_for_model_creation() -> bool:
    """Prompts the user to confirm model creation."""
    while True:
        response = input("Do you want to create a new UMAP model? (y/n): ").lower()
        if response == 'y':
            return True
        elif response == 'n':
            return False
        else:
            print("Please enter 'y' or 'n'.")

def create_and_fit_umap_model(connection_factory: Callable, model_path: str) -> Optional[UMAPModel]:
    """
    Creates and fits a new UMAP model from embeddings in the database.
    
    Args:
        connection_factory: Function to create database connections
        model_path: Path to save the UMAP model
    
    Returns:
        UMAPModel object if successful, None otherwise
    """
    try:
        # Load all embeddings from the database
        logger.info("Loading all embeddings from database...")
        embeddings_1d = []
        with connection_factory() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT doctrove_embedding
                    FROM doctrove_papers 
                    WHERE doctrove_embedding IS NOT NULL 
                    AND doctrove_embedding_2d IS NULL
                """)
                results = cur.fetchall()
                for paper in results:
                    embedding_1d = parse_embedding_data(paper['doctrove_embedding'])
                    embeddings_1d.append(embedding_1d)
        logger.info(f"Loaded {len(embeddings_1d)} embeddings.")

        if not embeddings_1d:
            logger.error("No embeddings found to create UMAP model.")
            return None

        # Create and fit UMAP model
        logger.info("Creating and fitting UMAP model...")
        scaler = create_scaler_from_embeddings(embeddings_1d)
        umap_model = umap.UMAP(
            n_components=UMAP_CONFIG['n_components'],
            n_neighbors=UMAP_CONFIG['n_neighbors'],
            min_dist=UMAP_CONFIG['min_dist'],
            metric=UMAP_CONFIG['metric'],
            random_state=UMAP_CONFIG['random_state'],
            low_memory=UMAP_CONFIG['low_memory'],
            verbose=UMAP_CONFIG['verbose']
        )
        umap_model.fit(scaler.transform(np.array(embeddings_1d)))
        logger.info("UMAP model fitted successfully.")

        # Save the model
        logger.info(f"Saving UMAP model to {model_path}...")
        with open(model_path, 'wb') as f:
            pickle.dump((umap_model, scaler), f)
        logger.info(f"UMAP model saved to {model_path}")

        return UMAPModel(model=umap_model, scaler=scaler, model_path=model_path)
    except Exception as e:
        logger.error(f"Failed to create and fit UMAP model: {e}")
        return None

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Functional 2D Embedding Processor')
    parser.add_argument('--remap', action='store_true', 
                       help='Create a new UMAP model (will prompt for confirmation if model exists)')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Batch size for processing (default: 1000)')
    parser.add_argument('--model-path', type=str, default='umap_model.pkl',
                       help='Path to UMAP model file (default: umap_model.pkl)')
    parser.add_argument('--sleep-seconds', type=int, default=60,
                       help='Sleep seconds when no papers to process (default: 60)')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create connection factory
    connection_factory = create_connection_factory()
    
    # Handle UMAP model creation
    if args.remap:
        if os.path.exists(args.model_path):
            print(f"\nUMAP model already exists at {args.model_path}")
            if prompt_user_for_model_creation():
                logger.info("Creating new UMAP model...")
                umap_model = create_and_fit_umap_model(connection_factory, args.model_path)
                if umap_model is None:
                    logger.error("Failed to create UMAP model. Exiting.")
                    sys.exit(1)
            else:
                logger.info("Model creation cancelled by user. Exiting.")
                sys.exit(0)
        else:
            logger.info("No existing UMAP model found. Creating new one...")
            umap_model = create_and_fit_umap_model(connection_factory, args.model_path)
            if umap_model is None:
                logger.error("Failed to create UMAP model. Exiting.")
                sys.exit(1)
    else:
        # Check if model exists
        if not os.path.exists(args.model_path):
            logger.warning(f"No UMAP model found at {args.model_path}")
            if prompt_user_for_model_creation():
                logger.info("Creating new UMAP model...")
                umap_model = create_and_fit_umap_model(connection_factory, args.model_path)
                if umap_model is None:
                    logger.error("Failed to create UMAP model. Exiting.")
                    sys.exit(1)
            else:
                logger.info("Model creation cancelled by user. Exiting.")
                sys.exit(0)
    
    # Run continuous 2D embedding processing
    process_2d_embeddings_continuous(
        connection_factory=connection_factory,
        batch_size=args.batch_size,
        model_path=args.model_path,
        sleep_seconds=args.sleep_seconds
    )
