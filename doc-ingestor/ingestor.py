"""
Data loading functions for doc-ingestor.
These functions handle I/O operations and are impure.
"""

import pandas as pd
import os
from typing import List, Dict, Any, Tuple
from transformers import transform_dataframe_to_papers
from json_ingestor import load_dataframe_from_json

def detect_file_format(file_path: str) -> str:
    """
    Detect file format based on file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        'pickle', 'json', or 'unknown'
    """
    _, ext = os.path.splitext(file_path.lower())
    if ext in ['.pkl', '.pickle']:
        return 'pickle'
    elif ext == '.json':
        return 'json'
    else:
        return 'unknown'

def load_dataframe_from_file(file_path: str) -> pd.DataFrame:
    """
    Load a pandas DataFrame from various file formats.
    
    Args:
        file_path: Path to the file
        
    Returns:
        pandas DataFrame
    """
    file_format = detect_file_format(file_path)
    
    if file_format == 'pickle':
        return pd.read_pickle(file_path)
    elif file_format == 'json':
        return load_dataframe_from_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}. Supported formats: .pkl, .pickle, .json")

def dataframe_to_dict_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Pure function: converts a pandas DataFrame to a list of dictionaries.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        List of dictionaries representing DataFrame rows
    """
    return df.to_dict('records')

def load_file_to_papers(file_path: str, limit: int = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Impure function: loads papers from various file formats using pure transformations.
    
    Args:
        file_path: Path to the file (supports .pkl, .pickle, .json)
        limit: Optional limit on number of papers to process
        
    Returns:
        Tuple of (common_papers, source_metadata_list)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.debug(f"📂 Loading data from file: {file_path}")
    
    # Load data (impure)
    df = load_dataframe_from_file(file_path)
    logger.debug(f"📊 Raw data loaded: {len(df)} rows, {len(df.columns)} columns")
    
    # Apply limit if specified
    if limit is not None:
        df = df.head(limit)
        logger.debug(f"📏 Applied limit: {len(df)} rows")
    
    # Convert to list of dicts (pure)
    logger.debug("🔄 Converting DataFrame to list of dictionaries...")
    df_rows = dataframe_to_dict_list(df)
    logger.debug(f"✅ DataFrame conversion completed: {len(df_rows)} rows")
    
    # Transform to papers (pure)
    logger.debug("🔄 Starting paper transformation...")
    common_papers, source_metadata_list = transform_dataframe_to_papers(df_rows)
    
    return common_papers, source_metadata_list

# Backward compatibility
def load_dataframe_from_pickle(pickle_path: str) -> pd.DataFrame:
    """
    Deprecated: Use load_dataframe_from_file instead.
    """
    return load_dataframe_from_file(pickle_path)

def load_pickle_to_papers(pickle_path: str, limit: int = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Deprecated: Use load_file_to_papers instead.
    """
    return load_file_to_papers(pickle_path, limit) 