#!/usr/bin/env python3
"""
Functional 2D Embedding Enrichment

A pure functional programming implementation of 2D embedding generation
that integrates with the existing async_enrichment.py system.

This module provides:
- Pure functions for 2D embedding processing
- Immutable data structures using NamedTuples
- Functional composition with map/filter/reduce
- Integration with the BaseEnrichment framework
"""

import logging
import numpy as np
import pickle
import os
import sys
import time
from typing import List, Dict, Any, Optional, Callable, NamedTuple, Tuple
from functools import partial, reduce
import psycopg2
from psycopg2.extras import RealDictCursor
import umap.umap_ as umap
from sklearn.preprocessing import StandardScaler

# Add paths for imports
sys.path.append('../doctrove-api')
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

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

# Immutable data structures using NamedTuples
PaperEmbedding = NamedTuple('PaperEmbedding', [
    ('paper_id', str),
    ('embedding_1d', np.ndarray),
    ('embedding_2d', Optional[np.ndarray])
])

ProcessingResult = NamedTuple('ProcessingResult', [
    ('successful_count', int),
    ('failed_count', int),
    ('total_processed', int),
    ('processing_time', float)
])

UMAPModel = NamedTuple('UMAPModel', [
    ('model', umap.UMAP),
    ('scaler', StandardScaler),
    ('model_path', str)
])

EnrichmentResult = NamedTuple('EnrichmentResult', [
    ('paper_id', str),
    ('doctrove_embedding_2d', Tuple[float, float])
])

# Pure functions for database operations
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

    # Extract 1D embeddings using functional approach
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

def convert_papers_to_embeddings(papers: List[Dict[str, Any]]) -> List[PaperEmbedding]:
    """
    Convert paper dictionaries to PaperEmbedding objects (pure function).

    Args:
        papers: List of paper dictionaries from database

    Returns:
        List of PaperEmbedding objects
    """
    def create_paper_embedding(paper_data):
        """Create PaperEmbedding from database row (pure function)."""
        try:
            embedding_1d = parse_embedding_data(paper_data['doctrove_embedding'])
            return PaperEmbedding(
                paper_id=paper_data['doctrove_paper_id'],
                embedding_1d=embedding_1d,
                embedding_2d=None
            )
        except Exception as e:
            logger.warning(f"Failed to parse embedding for paper {paper_data['doctrove_paper_id']}: {e}")
            return None

    # Map and filter out None results
    return list(filter(None, map(create_paper_embedding, papers)))

def convert_embeddings_to_enrichment_results(papers_with_2d: List[PaperEmbedding]) -> List[EnrichmentResult]:
    """
    Convert PaperEmbedding objects to EnrichmentResult objects (pure function).

    Args:
        papers_with_2d: List of PaperEmbedding objects with 2D embeddings

    Returns:
        List of EnrichmentResult objects
    """
    def create_enrichment_result(paper):
        """Create EnrichmentResult from PaperEmbedding (pure function)."""
        x, y = paper.embedding_2d[0], paper.embedding_2d[1]
        return EnrichmentResult(
            paper_id=paper.paper_id,
            doctrove_embedding_2d=(x, y)
        )

    return list(map(create_enrichment_result, papers_with_2d))

def save_2d_embeddings_batch(enrichment_results: List[EnrichmentResult], connection_factory: Callable) -> ProcessingResult:
    """
    Save 2D embeddings to database (pure function with controlled side effects).

    Args:
        enrichment_results: List of EnrichmentResult objects
        connection_factory: Function to create database connections

    Returns:
        ProcessingResult object
    """
    if not enrichment_results:
        return ProcessingResult(successful_count=0, failed_count=0, total_processed=0, processing_time=0.0)

    start_time = time.time()

    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Prepare data for batch update using functional approach
                def create_update_data(result):
                    """Create update data tuple (pure function)."""
                    x, y = result.doctrove_embedding_2d
                    point_str = f"({x},{y})"
                    return (point_str, result.paper_id)

                update_data = list(map(create_update_data, enrichment_results))

                # Update papers with 2D embeddings
                cur.executemany("""
                    UPDATE doctrove_papers
                    SET doctrove_embedding_2d = %s::point
                    WHERE doctrove_paper_id = %s
                """, update_data)

                # Commit the transaction
                conn.commit()

                successful_count = len(enrichment_results)
                processing_time = time.time() - start_time
                logger.info(f"Successfully saved {successful_count} 2D embeddings to database in {processing_time:.2f}s")

    except Exception as e:
        logger.error(f"Failed to save 2D embeddings batch: {e}")
        processing_time = time.time() - start_time
        return ProcessingResult(successful_count=0, failed_count=len(enrichment_results), total_processed=len(enrichment_results), processing_time=processing_time)

    return ProcessingResult(
        successful_count=successful_count,
        failed_count=0,
        total_processed=len(enrichment_results),
        processing_time=processing_time
    )

# Main processing function using functional composition
def process_papers_for_2d_embeddings_functional(
    papers: List[Dict[str, Any]], 
    umap_model: UMAPModel,
    connection_factory: Callable
) -> ProcessingResult:
    """
    Process papers for 2D embeddings using functional programming principles.

    Args:
        papers: List of paper dictionaries from database
        umap_model: Pre-loaded UMAP model
        connection_factory: Function to create database connections

    Returns:
        ProcessingResult object
    """
    start_time = time.time()

    # Functional composition pipeline:
    # papers -> PaperEmbedding -> PaperEmbedding with 2D -> EnrichmentResult -> save to DB
    
    # Step 1: Convert papers to PaperEmbedding objects
    logger.info(f"Converting {len(papers)} papers to embedding format...")
    paper_embeddings = convert_papers_to_embeddings(papers)
    logger.info(f"Converted {len(paper_embeddings)} papers to embedding format")

    if not paper_embeddings:
        return ProcessingResult(successful_count=0, failed_count=0, total_processed=0, processing_time=time.time() - start_time)

    # Step 2: Transform to 2D embeddings
    logger.info(f"Transforming {len(paper_embeddings)} embeddings to 2D...")
    transform_start = time.time()
    papers_with_2d = transform_embeddings_to_2d(paper_embeddings, umap_model)
    transform_time = time.time() - transform_start
    logger.info(f"Transformed embeddings in {transform_time:.2f}s")

    # Step 3: Convert to enrichment results
    enrichment_results = convert_embeddings_to_enrichment_results(papers_with_2d)

    # Step 4: Save to database
    logger.info(f"Saving {len(enrichment_results)} 2D embeddings to database...")
    save_result = save_2d_embeddings_batch(enrichment_results, connection_factory)

    total_time = time.time() - start_time
    logger.info(f"Total processing time: {total_time:.2f}s ({len(papers)} papers = {len(papers)/total_time:.1f} papers/sec)")

    return save_result

# Integration with BaseEnrichment framework
class FunctionalEmbedding2DEnrichment:
    """
    Functional 2D Embedding Enrichment that integrates with async_enrichment.py.
    
    This class provides a functional programming interface for 2D embedding generation
    while maintaining compatibility with the existing BaseEnrichment framework.
    """
    
    def __init__(self, model_path: str = 'umap_model.pkl'):
        """
        Initialize the functional 2D embedding enrichment.
        
        Args:
            model_path: Path to UMAP model file
        """
        self.model_path = model_path
        self.connection_factory = create_connection_factory()
        self.umap_model = None
        self._load_model()
    
    def _load_model(self):
        """Load UMAP model (called during initialization)."""
        self.umap_model = load_umap_model(self.model_path)
        if self.umap_model is None:
            raise ValueError(f"No UMAP model found at {self.model_path}")
        logger.info(f"Loaded UMAP model from {self.model_path}")
    
    def get_required_fields(self) -> List[str]:
        """Get list of fields required for 2D embedding enrichment."""
        return ["doctrove_paper_id", "doctrove_embedding"]
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process papers for 2D embedding enrichment (pure function interface).
        
        Args:
            papers: List of paper dictionaries with required fields
            
        Returns:
            List of enrichment result dictionaries
        """
        if not papers:
            return []
        
        # Use functional processing pipeline
        result = process_papers_for_2d_embeddings_functional(
            papers=papers,
            umap_model=self.umap_model,
            connection_factory=self.connection_factory
        )
        
        # Convert ProcessingResult to enrichment framework format
        return [{
            'paper_id': paper['doctrove_paper_id'],
            'processing_result': result
        } for paper in papers]
    
    def run_enrichment(self, papers: List[Dict[str, Any]]) -> int:
        """
        Run 2D embedding enrichment (compatible with BaseEnrichment interface).
        
        Args:
            papers: List of papers to enrich
            
        Returns:
            Number of papers successfully enriched
        """
        if not papers:
            return 0
        
        # Filter papers to only include those with required fields
        def has_required_fields(paper: Dict[str, Any]) -> bool:
            """Check if paper has all required fields (pure function)."""
            required_fields = self.get_required_fields()
            return all(field in paper and paper[field] is not None for field in required_fields)
        
        valid_papers = list(filter(has_required_fields, papers))
        
        if not valid_papers:
            logger.warning("No papers have required fields for 2D embedding enrichment")
            return 0
        
        # Process papers using functional pipeline
        result = process_papers_for_2d_embeddings_functional(
            papers=valid_papers,
            umap_model=self.umap_model,
            connection_factory=self.connection_factory
        )
        
        logger.info(f"2D embedding enrichment completed: {result.successful_count}/{len(valid_papers)} papers enriched")
        return result.successful_count

# Utility functions for integration
def create_functional_2d_enrichment(model_path: str = 'umap_model.pkl') -> FunctionalEmbedding2DEnrichment:
    """
    Create a functional 2D embedding enrichment instance.
    
    Args:
        model_path: Path to UMAP model file
        
    Returns:
        FunctionalEmbedding2DEnrichment instance
    """
    return FunctionalEmbedding2DEnrichment(model_path)

def process_batch_functional(
    papers: List[Dict[str, Any]], 
    model_path: str = 'umap_model.pkl'
) -> ProcessingResult:
    """
    Process a batch of papers for 2D embeddings using functional programming.
    
    Args:
        papers: List of paper dictionaries
        model_path: Path to UMAP model file
        
    Returns:
        ProcessingResult object
    """
    umap_model = load_umap_model(model_path)
    if umap_model is None:
        raise ValueError(f"No UMAP model found at {model_path}")
    
    connection_factory = create_connection_factory()
    
    return process_papers_for_2d_embeddings_functional(
        papers=papers,
        umap_model=umap_model,
        connection_factory=connection_factory
    )

# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the functional enrichment
    try:
        enrichment = create_functional_2d_enrichment()
        logger.info("Functional 2D embedding enrichment created successfully")
        
        # This would be used with the async_enrichment.py system
        logger.info("Ready for integration with async_enrichment.py")
        
    except Exception as e:
        logger.error(f"Failed to create functional enrichment: {e}")
        sys.exit(1)

















