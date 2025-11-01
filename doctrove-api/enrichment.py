"""
Pure functions for 2D embedding generation using UMAP.
"""

import json
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Tuple, Optional
# Lazy import to avoid UMAP initialization during module import
# from config import UMAP_CONFIG, EMBEDDING_VERSION

def parse_embedding_string(embedding_str: str) -> np.ndarray:
    """
    Pure function: parses embedding string from database into numpy array.
    
    Args:
        embedding_str: JSON string representation of embedding
        
    Returns:
        Numpy array of embedding values
    """
    if embedding_str is None:
        return None
    
    try:
        # Handle both JSON string and list formats
        if isinstance(embedding_str, str):
            # Try to parse as JSON first
            try:
                embedding_list = json.loads(embedding_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to parse as a simple string format
                # Handle formats like "(0.1,0.2)" or "[0.1,0.2]"
                embedding_str = embedding_str.strip()
                if embedding_str.startswith('(') and embedding_str.endswith(')'):
                    # Remove parentheses and split by comma
                    embedding_str = embedding_str[1:-1]
                    embedding_list = [float(x.strip()) for x in embedding_str.split(',')]
                elif embedding_str.startswith('[') and embedding_str.endswith(']'):
                    # Remove brackets and split by comma
                    embedding_str = embedding_str[1:-1]
                    embedding_list = [float(x.strip()) for x in embedding_str.split(',')]
                else:
                    # Try to split by comma directly
                    embedding_list = [float(x.strip()) for x in embedding_str.split(',')]
        else:
            embedding_list = embedding_str
        
        return np.array(embedding_list, dtype=np.float32)
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as e:
        # Only log warnings for unexpected errors, not for common format issues
        if not isinstance(embedding_str, str) or len(embedding_str) > 100:
            # This is likely a real error, not just a format issue
            print(f"Warning: Could not parse embedding (unexpected format): {type(embedding_str)}")
        return None

def extract_embeddings_from_papers(papers: List[Dict[str, Any]], embedding_type: str = 'title') -> Tuple[List[str], np.ndarray]:
    """
    Pure function: extracts embeddings from papers and returns paper IDs and embedding matrix.
    
    Args:
        papers: List of paper dictionaries
        embedding_type: 'title', 'abstract', or 'unified'
        
    Returns:
        Tuple of (paper_ids, embedding_matrix)
    """
    paper_ids = []
    embeddings = []
    
    for paper in papers:
        if embedding_type == 'unified':
            embedding_key = 'doctrove_embedding'
        else:
            embedding_key = f'doctrove_{embedding_type}_embedding'
        
        embedding_str = paper.get(embedding_key)
        
        if embedding_str:
            embedding_array = parse_embedding_string(embedding_str)
            if embedding_array is not None:
                paper_ids.append(paper['doctrove_paper_id'])
                embeddings.append(embedding_array)
    
    if not embeddings:
        return [], np.array([])
    
    return paper_ids, np.array(embeddings)

def create_umap_model(config: Optional[Dict[str, Any]] = None):
    """
    Pure function: creates a UMAP model with specified configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured UMAP model
    """
    # Lazy import to avoid initialization issues
    import umap.umap_ as umap
    from config import UMAP_CONFIG
    
    if config is None:
        config = UMAP_CONFIG.copy()
    
    return umap.UMAP(**config)

def fit_umap_model(embeddings: np.ndarray, config: Optional[Dict[str, Any]] = None):
    """
    Pure function: fits a UMAP model to embeddings.
    
    Args:
        embeddings: Numpy array of embeddings
        config: Optional UMAP configuration
        
    Returns:
        Fitted UMAP model
    """
    if len(embeddings) == 0:
        raise ValueError("No embeddings provided")
    
    umap_model = create_umap_model(config)
    umap_model.fit(embeddings)
    return umap_model

def simple_2d_projection(embeddings: np.ndarray) -> np.ndarray:
    """
    Pure function: simple 2D projection for very small datasets.
    Uses first two principal components or simple coordinate assignment.
    
    Args:
        embeddings: Numpy array of embeddings
        
    Returns:
        Numpy array of 2D coordinates
    """
    if len(embeddings) == 0:
        return np.array([])
    
    if len(embeddings) == 1:
        # Single point at origin
        return np.array([[0.0, 0.0]])
    elif len(embeddings) == 2:
        # Two points on opposite sides
        return np.array([[-1.0, 0.0], [1.0, 0.0]])
    elif len(embeddings) == 3:
        # Triangle formation
        return np.array([[-0.5, -0.5], [0.5, -0.5], [0.0, 0.5]])
    elif len(embeddings) == 4:
        # Square formation
        return np.array([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]])
    else:
        # For larger datasets, use PCA
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2)
        return pca.fit_transform(embeddings)

def transform_embeddings_to_2d(embeddings: np.ndarray, umap_model) -> np.ndarray:
    """
    Pure function: transforms embeddings to 2D using fitted UMAP model.
    
    Args:
        embeddings: Numpy array of embeddings
        umap_model: Fitted UMAP model
        
    Returns:
        Numpy array of 2D coordinates
    """
    if len(embeddings) == 0:
        return np.array([])
    
    return umap_model.transform(embeddings)

def save_umap_model(umap_model, model_path: str = '../embedding-enrichment/umap_model.pkl') -> None:
    """
    Pure function: saves a fitted UMAP model to disk.
    
    Args:
        umap_model: Fitted UMAP model to save
        model_path: Path where to save the model
    """
    with open(model_path, 'wb') as f:
        pickle.dump(umap_model, f)

def load_umap_model(model_path: str = '../embedding-enrichment/umap_model.pkl'):
    """
    Pure function: loads a fitted UMAP model from disk.
    
    Args:
        model_path: Path to the saved model
        
    Returns:
        Loaded UMAP model or None if file doesn't exist
    """
    if not os.path.exists(model_path):
        return None
    
    try:
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Warning: Could not load UMAP model: {e}")
        return None

def create_2d_embedding_metadata(umap_model, config: Dict[str, Any], 
                               embedding_type: str, version: str = None, 
                               is_incremental: bool = False) -> Dict[str, Any]:
    """
    Pure function: creates metadata for 2D embeddings.
    
    Args:
        umap_model: Fitted UMAP model
        config: UMAP configuration used
        embedding_type: Type of embedding ('title' or 'abstract')
        version: Optional version string
        is_incremental: Whether this was processed incrementally
        
    Returns:
        Metadata dictionary
    """
    # Lazy import to avoid initialization issues
    from config import EMBEDDING_VERSION
    
    if version is None:
        version = EMBEDDING_VERSION
    
    metadata = {
        'version': version,
        'algorithm': 'umap',
        'embedding_type': embedding_type,
        'parameters': config.copy(),
        'n_components': umap_model.n_components,
        'n_neighbors': umap_model.n_neighbors,
        'min_dist': umap_model.min_dist,
        'metric': umap_model.metric,
        'random_state': umap_model.random_state,
        'is_incremental': is_incremental
    }
    
    return metadata

def process_papers_for_2d_embeddings_incremental(papers: List[Dict[str, Any]], 
                                                embedding_type: str = 'title',
                                                config: Optional[Dict[str, Any]] = None,
                                                model_path: str = '../embedding-enrichment/umap_model.pkl',
                                                is_first_batch: bool = False) -> List[Dict[str, Any]]:
    """
    Pure function: processes papers to generate 2D embeddings using incremental UMAP.
    
    Args:
        papers: List of paper dictionaries
        embedding_type: 'title' or 'abstract'
        config: Optional UMAP configuration
        model_path: Path to save/load UMAP model
        is_first_batch: Whether this is the first batch (fit new model vs load existing)
        
    Returns:
        List of dictionaries with paper_id, 2d_coords, and metadata
    """
    if not papers:
        return []
    
    # Extract embeddings
    paper_ids, embeddings = extract_embeddings_from_papers(papers, embedding_type)
    
    if len(embeddings) == 0:
        print(f"No valid {embedding_type} embeddings found")
        return []
    
    print(f"Processing {len(embeddings)} {embedding_type} embeddings")
    
    # For very small datasets, use simple 2D projection
    if len(embeddings) < 5:
        print("Using simple 2D projection for small dataset")
        coords_2d = simple_2d_projection(embeddings)
        is_incremental = False
        
        # Create simple metadata
        metadata = {
            'version': 'simple_v1',
            'algorithm': 'simple_projection',
            'embedding_type': embedding_type,
            'parameters': {'method': 'simple_2d_projection'},
            'n_components': 2,
            'is_incremental': False
        }
    else:
        # Use UMAP for larger datasets
        if is_first_batch:
            # First batch: fit new UMAP model
            print("Fitting new UMAP model for first batch")
            umap_model = fit_umap_model(embeddings, config)
            save_umap_model(umap_model, model_path)
            is_incremental = False
        else:
            # Subsequent batches: load existing model
            print("Loading existing UMAP model for incremental processing")
            umap_model = load_umap_model(model_path)
            if umap_model is None:
                raise ValueError("No saved UMAP model found. Run first batch with is_first_batch=True")
            is_incremental = True
        
        # Transform to 2D
        coords_2d = transform_embeddings_to_2d(embeddings, umap_model)
        
        # Create metadata
        # Lazy import to avoid initialization issues
        from config import UMAP_CONFIG
        metadata = create_2d_embedding_metadata(umap_model, config or UMAP_CONFIG, embedding_type, is_incremental=is_incremental)
    
    # Create results
    results = []
    for i, paper_id in enumerate(paper_ids):
        coords = coords_2d[i]
        results.append({
            'paper_id': paper_id,
            'coords_2d': (float(coords[0]), float(coords[1])),
            'metadata': metadata
        })
    
    return results

def process_papers_for_2d_embeddings(papers: List[Dict[str, Any]], 
                                   embedding_type: str = 'title',
                                   config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Pure function: processes papers to generate 2D embeddings (legacy function for single-batch processing).
    
    Args:
        papers: List of paper dictionaries
        embedding_type: 'title' or 'abstract'
        config: Optional UMAP configuration
        
    Returns:
        List of dictionaries with paper_id, 2d_coords, and metadata
    """
    if not papers:
        return []
    
    # Extract embeddings
    paper_ids, embeddings = extract_embeddings_from_papers(papers, embedding_type)
    
    if len(embeddings) == 0:
        print(f"No valid {embedding_type} embeddings found")
        return []
    
    print(f"Processing {len(embeddings)} {embedding_type} embeddings")
    
    # Fit UMAP model
    umap_model = fit_umap_model(embeddings, config)
    
    # Transform to 2D
    coords_2d = transform_embeddings_to_2d(embeddings, umap_model)
    
    # Create metadata
    # Lazy import to avoid initialization issues
    from config import UMAP_CONFIG
    metadata = create_2d_embedding_metadata(umap_model, config or UMAP_CONFIG, embedding_type)
    
    # Create results
    results = []
    for i, paper_id in enumerate(paper_ids):
        coords = coords_2d[i]
        results.append({
            'paper_id': paper_id,
            'coords_2d': (float(coords[0]), float(coords[1])),
            'metadata': metadata
        })
    
    return results

def validate_2d_coordinates(coords: Tuple[float, float]) -> bool:
    """
    Pure function: validates 2D coordinates.
    
    Args:
        coords: Tuple of (x, y) coordinates
        
    Returns:
        True if coordinates are valid
    """
    if not isinstance(coords, tuple) or len(coords) != 2:
        return False
    
    x, y = coords
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return False
    
    # Check for NaN or infinite values
    if np.isnan(x) or np.isnan(y) or np.isinf(x) or np.isinf(y):
        return False
    
    return True

def count_valid_embeddings(papers: List[Dict[str, Any]], embedding_type: str = 'title') -> int:
    """
    Pure function: counts papers with valid embeddings.
    
    Args:
        papers: List of paper dictionaries
        embedding_type: 'title', 'abstract', or 'unified'
        
    Returns:
        Number of papers with valid embeddings
    """
    count = 0
    for paper in papers:
        if embedding_type == 'unified':
            embedding_key = 'doctrove_embedding'
        else:
            embedding_key = f'doctrove_{embedding_type}_embedding'
        
        embedding_str = paper.get(embedding_key)
        
        if embedding_str:
            embedding_array = parse_embedding_string(embedding_str)
            if embedding_array is not None:
                count += 1
    
    return count 