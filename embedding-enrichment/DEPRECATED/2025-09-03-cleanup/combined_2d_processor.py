"""
Combined 2D Embedding Processor

This module processes both title and abstract embeddings together in a single UMAP model
to ensure they're mapped to the same 2D space for comparability.
"""

import logging
import numpy as np
import pickle
import os
import sys
from typing import List, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import umap.umap_ as umap
from sklearn.preprocessing import StandardScaler

# Add paths for imports
sys.path.append('../doctrove-api')
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UMAP configuration - avoid BitGenerator issues with newer NumPy
UMAP_CONFIG = {
    'n_components': 2,
    'n_neighbors': 15,
    'min_dist': 0.1,
    'metric': 'cosine',
    'random_state': None,  # Use None instead of integer to avoid BitGenerator issues
    'low_memory': True,  # Use low memory mode to avoid issues
    'verbose': False  # Reduce verbosity
}

def get_database_connection():
    """Get database connection using the same parameters as the event listener."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def load_embeddings_for_2d_processing() -> Tuple[List[np.ndarray], List[str], List[str]]:
    """
    Load all unified embeddings that need 2D projections.
    
    Returns:
        Tuple of (embeddings, paper_ids, embedding_types)
    """
    embeddings = []
    paper_ids = []
    embedding_types = []
    
    with get_database_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get papers with unified embeddings but no 2D
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_embedding
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NOT NULL 
                AND doctrove_embedding_2d IS NULL
            """)
            papers = cur.fetchall()
    
    logger.debug(f"Found {len(papers)} papers needing 2D embeddings")
    
    # Process unified embeddings
    for paper in papers:
        try:
            embedding_data = paper['doctrove_embedding']
            if isinstance(embedding_data, str):
                embedding_data = embedding_data.strip('[]').split(',')
                embedding = np.array([float(x.strip()) for x in embedding_data], dtype=np.float32)
            else:
                embedding = np.array(embedding_data, dtype=np.float32)
            embeddings.append(embedding)
            paper_ids.append(paper['doctrove_paper_id'])
            embedding_types.append('unified')
        except Exception as e:
            # Don't log individual failures to prevent massive log files
            pass
    
    logger.debug(f"Processed {len(papers)} unified embeddings.")
    logger.debug(f"Successfully loaded {len(embeddings)} embeddings for 2D processing")
    logger.debug(f"  - Unified embeddings: {len([t for t in embedding_types if t == 'unified'])}")
    return embeddings, paper_ids, embedding_types

def train_or_load_umap_model(embeddings: List[np.ndarray], model_path: str = 'umap_model.pkl') -> umap.UMAP:
    """
    Train a new UMAP model or load existing one.
    
    Args:
        embeddings: List of embedding arrays
        model_path: Path to save/load the UMAP model
    
    Returns:
        Trained UMAP model
    """
    if os.path.exists(model_path):
        logger.debug(f"Loading existing UMAP model from {model_path}")
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    
    logger.debug("Training new UMAP model...")
    
    # Convert embeddings to numpy array
    embeddings_array = np.array(embeddings)
    
    # Standardize embeddings
    scaler = StandardScaler()
    embeddings_scaled = scaler.fit_transform(embeddings_array)
    
    # Train UMAP model
    model = umap.UMAP(**UMAP_CONFIG)
    model.fit(embeddings_scaled)
    
    # Save the model
    logger.debug(f"Saving UMAP model to {model_path}")
    with open(model_path, 'wb') as f:
        pickle.dump((model, scaler), f)
    
    return model

def generate_2d_embeddings(embeddings: List[np.ndarray], model: umap.UMAP, scaler: StandardScaler) -> List[np.ndarray]:
    """
    Generate 2D embeddings using the trained UMAP model.
    
    Args:
        embeddings: List of embedding arrays
        model: Trained UMAP model
        scaler: Fitted StandardScaler
    
    Returns:
        List of 2D embedding arrays
    """
    embeddings_array = np.array(embeddings)
    embeddings_scaled = scaler.transform(embeddings_array)
    embeddings_2d = model.transform(embeddings_scaled)
    
    return [emb.tolist() for emb in embeddings_2d]

def save_2d_embeddings(paper_ids: List[str], embedding_types: List[str], embeddings_2d: List[np.ndarray]) -> int:
    """
    Save 2D embeddings to the database.
    
    Args:
        paper_ids: List of paper IDs
        embedding_types: List of embedding types (all 'unified' now)
        embeddings_2d: List of 2D embedding arrays
    
    Returns:
        Number of embeddings successfully saved
    """
    if not paper_ids or not embeddings_2d:
        return 0
    
    saved_count = 0
    
    with get_database_connection() as conn:
        with conn.cursor() as cur:
            for i, (paper_id, embedding_type, embedding_2d) in enumerate(zip(paper_ids, embedding_types, embeddings_2d)):
                try:
                    # Convert numpy array to PostgreSQL point format
                    x, y = embedding_2d[0], embedding_2d[1]
                    point_str = f"({x},{y})"
                    
                    # Save unified 2D embedding
                    cur.execute("""
                        UPDATE doctrove_papers 
                        SET doctrove_embedding_2d = %s::point 
                        WHERE doctrove_paper_id = %s
                    """, (point_str, paper_id))
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to save 2D embedding for paper {paper_id}: {e}")
                    # Rollback the transaction on error
                    conn.rollback()
                    raise
        
        conn.commit()
    
    logger.debug(f"Successfully saved {saved_count} 2D embeddings")
    return saved_count

def process_combined_2d_embeddings(model_path: str = 'umap_model.pkl') -> bool:
    """
    Main function to process both title and abstract embeddings together.
    
    Args:
        model_path: Path to save/load the UMAP model
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.debug("Starting combined 2D embedding processing...")
        
        # Load embeddings that need 2D projections
        embeddings, paper_ids, embedding_types = load_embeddings_for_2d_processing()
        
        if not embeddings:
            logger.debug("No embeddings need 2D processing")
            return True
        
        logger.debug(f"Processing {len(embeddings)} embeddings in combined 2D space...")
        
        # Train or load UMAP model
        if os.path.exists(model_path):
            logger.debug(f"Loading existing UMAP model from {model_path}")
            with open(model_path, 'rb') as f:
                loaded_data = pickle.load(f)
                
            # Handle both old format (just model) and new format (model, scaler)
            if isinstance(loaded_data, tuple) and len(loaded_data) == 2:
                model, scaler = loaded_data
                logger.debug("Loaded UMAP model with scaler")
            else:
                # Old format - just the model, need to create a new scaler
                model = loaded_data
                logger.debug("Loaded UMAP model (old format), creating new scaler")
                # Create a new scaler and fit it to the current embeddings
                embeddings_array = np.array(embeddings)
                scaler = StandardScaler()
                scaler.fit(embeddings_array)
        else:
            logger.debug("Training new UMAP model on combined embeddings...")
            model = train_or_load_umap_model(embeddings, model_path)
            with open(model_path, 'rb') as f:
                model, scaler = pickle.load(f)
        
        # Generate 2D embeddings
        logger.debug("Generating 2D embeddings...")
        embeddings_2d = generate_2d_embeddings(embeddings, model, scaler)
        
        # Save to database
        logger.debug("Saving 2D embeddings to database...")
        saved_count = save_2d_embeddings(paper_ids, embedding_types, embeddings_2d)
        
        logger.debug(f"Combined 2D processing completed: {saved_count} embeddings processed")
        return True
        
    except Exception as e:
        logger.error(f"Error in combined 2D processing: {e}")
        return False

def process_combined_2d_embeddings_incremental(batch_size: int = 100000, model_path: str = 'umap_model.pkl') -> bool:
    """
    Incremental function to process only papers that need 2D projections.
    
    Args:
        batch_size: Number of papers to process in each batch
        model_path: Path to save/load the UMAP model
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.debug(f"Starting incremental combined 2D embedding processing (batch_size={batch_size})...")
        
        # Check if we have a UMAP model
        if not os.path.exists(model_path):
            logger.warning(f"No UMAP model found at {model_path}. Running full processing instead.")
            return process_combined_2d_embeddings(model_path)
        
        # Load existing UMAP model
        logger.debug(f"Loading existing UMAP model from {model_path}")
        with open(model_path, 'rb') as f:
            loaded_data = pickle.load(f)
            
        # Handle both old format (just model) and new format (model, scaler)
        if isinstance(loaded_data, tuple) and len(loaded_data) == 2:
            model, scaler = loaded_data
            logger.debug("Loaded UMAP model with scaler")
        else:
            # Old format - just the model, need to create a new scaler
            model = loaded_data
            logger.debug("Loaded UMAP model (old format), creating new scaler")
            # We'll create a scaler when we load the first batch
        
        # Process papers in batches
        total_processed = 0
        batch_number = 0
        
        while True:
            # Get next batch of papers needing 2D projections
            batch_embeddings, batch_paper_ids, batch_embedding_types = load_embeddings_for_2d_processing_batch(
                batch_size=batch_size, 
                offset=batch_number * batch_size
            )
            
            if not batch_embeddings:
                logger.debug("No more papers need 2D processing")
                break
            
            batch_number += 1
            logger.debug(f"Processing batch {batch_number}: {len(batch_embeddings)} papers")
            
            # Create scaler if needed (for old format models)
            if 'scaler' not in locals():
                embeddings_array = np.array(batch_embeddings)
                scaler = StandardScaler()
                scaler.fit(embeddings_array)
                logger.debug("Created new scaler for incremental processing")
            
            # Generate 2D embeddings using existing model
            embeddings_2d = generate_2d_embeddings(batch_embeddings, model, scaler)
            
            # Save to database
            saved_count = save_2d_embeddings(batch_paper_ids, batch_embedding_types, embeddings_2d)
            total_processed += saved_count
            
            logger.debug(f"Batch {batch_number} completed: {saved_count} embeddings saved")
            
            # If we got fewer papers than batch_size, we're done
            if len(batch_embeddings) < batch_size:
                break
        
        logger.debug(f"Incremental combined 2D processing completed: {total_processed} total embeddings processed")
        return True
        
    except Exception as e:
        logger.error(f"Error in incremental combined 2D processing: {e}")
        return False


def load_embeddings_for_2d_processing_batch(batch_size: int = 100000, offset: int = 0) -> Tuple[List[np.ndarray], List[str], List[str]]:
    """
    Load a batch of embeddings that need 2D projections.
    
    Args:
        batch_size: Number of papers to load
        offset: Offset for pagination
    
    Returns:
        Tuple of (embeddings, paper_ids, embedding_types)
    """
    embeddings = []
    paper_ids = []
    embedding_types = []
    
    try:
        with get_database_connection() as conn:
            with conn.cursor() as cur:
                # Get papers needing 2D projections
                cur.execute("""
                    SELECT doctrove_paper_id, doctrove_embedding
                    FROM doctrove_papers 
                    WHERE doctrove_embedding IS NOT NULL 
                    AND doctrove_embedding_2d IS NULL
                    ORDER BY doctrove_paper_id
                    LIMIT %s OFFSET %s
                """, (batch_size, offset))
                
                papers = cur.fetchall()
        
        # Process unified embeddings
        for paper_id, embedding_data in papers:
            try:
                if isinstance(embedding_data, str):
                    embedding_data = embedding_data.strip('[]').split(',')
                    embedding = np.array([float(x.strip()) for x in embedding_data], dtype=np.float32)
                else:
                    embedding = np.array(embedding_data, dtype=np.float32)
                embeddings.append(embedding)
                paper_ids.append(paper_id)
                embedding_types.append('unified')
            except Exception as e:
                logger.warning(f"Failed to process unified embedding for paper {paper_id}: {e}")
        
        logger.debug(f"Loaded {len(embeddings)} unified embeddings for 2D processing (batch_size={batch_size}, offset={offset})")
        return embeddings, paper_ids, embedding_types
        
    except Exception as e:
        logger.error(f"Error loading embeddings for 2D processing: {e}")
        return [], [], []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Combined 2D embedding processor')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='incremental',
                       help='Processing mode (default: incremental)')
    parser.add_argument('--batch-size', type=int, default=100000,
                       help='Batch size for incremental processing (default: 100000)')
    parser.add_argument('--model-path', default='umap_model.pkl',
                       help='Path to UMAP model (default: umap_model.pkl)')
    
    args = parser.parse_args()
    
    if args.mode == 'incremental':
        success = process_combined_2d_embeddings_incremental(
            batch_size=args.batch_size, 
            model_path=args.model_path
        )
        if success:
            print("Incremental combined 2D processing completed successfully")
        else:
            print("Incremental combined 2D processing failed")
            exit(1)
    else:
        success = process_combined_2d_embeddings(args.model_path)
        if success:
            print("Full combined 2D processing completed successfully")
        else:
            print("Full combined 2D processing failed")
            exit(1) 