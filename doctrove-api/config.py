"""
Configuration for embedding-enrichment service.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Load .env.local if present (for laptop-specific overrides)
# Use absolute path since backend runs from doctrove-api/ directory
import os
env_local_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')
print(f"Loading .env.local from: {env_local_path}")
print(f"File exists: {os.path.exists(env_local_path)}")
load_dotenv(env_local_path, override=True)
print(f"After loading .env.local, DOCTROVE_API_PORT = {os.getenv('DOCTROVE_API_PORT', 'NOT_SET')}")

# Database configuration
DB_HOST = os.getenv('DOC_TROVE_HOST', 'localhost')
DB_PORT = int(os.getenv('DOC_TROVE_PORT', 5432))  # PostgreSQL default port 5432
DB_NAME = os.getenv('DOC_TROVE_DB', 'doctrove')
DB_USER = os.getenv('DOC_TROVE_USER', 'doctrove_admin')
DB_PASSWORD = os.getenv('DOC_TROVE_PASSWORD', 'doctrove_admin')

# UMAP configuration
UMAP_CONFIG = {
    'n_neighbors': 15,
    'min_dist': 0.1,
    'n_components': 2,
    'metric': 'cosine',
    'random_state': 42,
    'verbose': True
}

def get_adaptive_umap_config(dataset_size: int) -> Dict[str, Any]:
    """
    Get UMAP configuration adapted for the dataset size.
    
    Args:
        dataset_size: Number of papers in the dataset
        
    Returns:
        UMAP configuration dictionary
    """
    config = UMAP_CONFIG.copy()
    
    # For very small datasets, use PCA instead of UMAP
    if dataset_size < 5:
        # Use PCA for very small datasets
        config['algorithm'] = 'pca'
        config['n_neighbors'] = 1
        config['min_dist'] = 0.01
    elif dataset_size < 10:
        config['n_neighbors'] = max(2, dataset_size - 1)
        config['min_dist'] = 0.05  # Tighter clustering for small datasets
    elif dataset_size < 50:
        config['n_neighbors'] = min(10, dataset_size - 1)
    elif dataset_size < 100:
        config['n_neighbors'] = min(15, dataset_size - 1)
    
    return config

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
OPENAI_CHAT_MODEL = os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o')

# Feature flags for OpenAI services
USE_OPENAI_EMBEDDINGS = os.getenv('USE_OPENAI_EMBEDDINGS', 'true').lower() == 'true'
USE_OPENAI_LLM = os.getenv('USE_OPENAI_LLM', 'true').lower() == 'true'

# Legacy RAND corporate API configuration (DEPRECATED - do not use without authorization)
RAND_OPENAI_API_KEY = 'a349cd5ebfcb45f59b2004e6e8b7d700'  # DEPRECATED - kept for reference only
RAND_OPENAI_BASE_URL = 'https://apigw.rand.org/openai/RAND/inference'
RAND_EMBEDDING_DEPLOYMENT = 'text-embedding-3-small-v1-base'
RAND_CHAT_DEPLOYMENT = 'gpt-4o-2024-11-20-us'

# Service configuration
BATCH_SIZE = 1000  # Number of papers to process in each batch
EMBEDDING_VERSION = 'umap_v1'  # Version tag for the embedding algorithm

# Adaptive batch sizing based on dataset characteristics
BATCH_SIZING_CONFIG = {
    'small_dataset': {
        'max_papers': 5000,
        'first_batch_size': 2000,
        'subsequent_batch_size': 1000,
        'rationale': 'Small datasets: 2000 papers for better local structure and diversity'
    },
    'medium_dataset': {
        'max_papers': 50000,
        'first_batch_size': 2000,
        'subsequent_batch_size': 1000,
        'rationale': 'Medium datasets: 2000 papers for good field coverage'
    },
    'large_dataset': {
        'max_papers': 500000,
        'first_batch_size': 10000,
        'subsequent_batch_size': 2000,
        'rationale': 'Large datasets: 10000 papers for comprehensive coverage'
    },
    'very_large_dataset': {
        'max_papers': 2000000,
        'first_batch_size': 50000,
        'subsequent_batch_size': 10000,
        'rationale': 'Very large datasets: 50000 papers for comprehensive coverage'
    },
    'massive_dataset': {
        'max_papers': float('inf'),
        'first_batch_size': 100000,
        'subsequent_batch_size': 20000,
        'rationale': 'Massive datasets: 100000 papers for maximum quality and efficiency'
    }
}

def get_adaptive_batch_sizes(total_papers: int) -> tuple[int, int]:
    """
    Determine optimal batch sizes based on dataset size.
    
    Args:
        total_papers: Total number of papers in the dataset
        
    Returns:
        Tuple of (first_batch_size, subsequent_batch_size)
    """
    if total_papers <= BATCH_SIZING_CONFIG['small_dataset']['max_papers']:
        config = BATCH_SIZING_CONFIG['small_dataset']
    elif total_papers <= BATCH_SIZING_CONFIG['medium_dataset']['max_papers']:
        config = BATCH_SIZING_CONFIG['medium_dataset']
    elif total_papers <= BATCH_SIZING_CONFIG['large_dataset']['max_papers']:
        config = BATCH_SIZING_CONFIG['large_dataset']
    elif total_papers <= BATCH_SIZING_CONFIG['very_large_dataset']['max_papers']:
        config = BATCH_SIZING_CONFIG['very_large_dataset']
    else:
        config = BATCH_SIZING_CONFIG['massive_dataset']
    
    return config['first_batch_size'], config['subsequent_batch_size']

def get_batch_sizing_rationale(total_papers: int) -> str:
    """
    Get the rationale for the chosen batch sizing.
    
    Args:
        total_papers: Total number of papers in the dataset
        
    Returns:
        Explanation of why these batch sizes were chosen
    """
    if total_papers <= BATCH_SIZING_CONFIG['small_dataset']['max_papers']:
        return BATCH_SIZING_CONFIG['small_dataset']['rationale']
    elif total_papers <= BATCH_SIZING_CONFIG['medium_dataset']['max_papers']:
        return BATCH_SIZING_CONFIG['medium_dataset']['rationale']
    elif total_papers <= BATCH_SIZING_CONFIG['large_dataset']['max_papers']:
        return BATCH_SIZING_CONFIG['large_dataset']['rationale']
    elif total_papers <= BATCH_SIZING_CONFIG['very_large_dataset']['max_papers']:
        return BATCH_SIZING_CONFIG['very_large_dataset']['rationale']
    else:
        return BATCH_SIZING_CONFIG['massive_dataset']['rationale']

# Legacy configuration for backward compatibility
DEFAULT_FIRST_BATCH_SIZE = 500
DEFAULT_BATCH_SIZE = 1000 