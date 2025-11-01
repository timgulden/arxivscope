"""
Configuration settings for DocScope frontend.
"""

# API Configuration
import os
from dotenv import load_dotenv

# Load .env.local if it exists (for local development)
env_local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local')
if os.path.exists(env_local_path):
    load_dotenv(env_local_path)

# Get API URL from environment, with no hard-coded fallback
API_BASE_URL = os.getenv('DOCTROVE_API_URL')
if not API_BASE_URL:
    raise ValueError(
        "DOCTROVE_API_URL environment variable not set. "
        "Please set it in .env.local or as an environment variable. "
        "Example: DOCTROVE_API_URL=http://localhost:5003/api"
    )

# Application Configuration
TARGET_RECORDS_PER_VIEW = int(os.getenv('TARGET_RECORDS_PER_VIEW', 5000))  # Configurable default, 5000 for proper visual interface
DEBOUNCE_DELAY_SECONDS = 0.05  # Reduced to 50ms for more responsive zooms
MAX_CACHE_SIZE = 10  # Maximum number of cached data sets

# Graph Configuration
GRAPH_CONFIG = {
    'displayModeBar': True, 
    'scrollZoom': True
}

# Color mapping for sources and countries
SOURCE_COLOR_MAP = {
    'openalex': '#FF8C00',      # Orange for OpenAlex
    'randpub': '#6D3E91',       # Purple for RAND Publications
    'extpub': '#B19CD9',        # Light purple for External RAND
    'aipickle': '#2E7D32',      # Darker green for ArXiv AI Subset
}

# Note: COUNTRY_COLOR_MAP removed - no longer using country-based coloring for aipickle
# All sources now use unified coloring approach

# Color mapping for OpenAlex uschina field
USCHINA_COLOR_MAP = {
    'US': '#1976D2',      # Blue for US
    'China': '#D32F2F',   # Red for China
    'Other': '#4CAF50',   # Green for other countries
}

# Default color for other countries (including RAND papers without country code)
DEFAULT_COLOR = '#6D3E91'  # RAND logo purple

# Graph layout configuration
GRAPH_LAYOUT = {
    'xaxis': {
        'title': {'text': 'UMAP X', 'font': {'color': '#ffffff'}},
        'showgrid': False,
        'gridcolor': '#404040',
        'zeroline': False,
        'showline': False,
        'linecolor': '#404040',
        'tickfont': {'color': '#ffffff'},
        'showticklabels': False,
    },
    'yaxis': {
        'title': {'text': 'UMAP Y', 'font': {'color': '#ffffff'}},
        'showgrid': False,
        'gridcolor': '#404040',
        'zeroline': False,
        'showline': False,
        'linecolor': '#404040',
        'tickfont': {'color': '#ffffff'},
        'showticklabels': False,
    },
    'plot_bgcolor': '#2b2b2b',
    'paper_bgcolor': '#2b2b2b',
    'margin': dict(l=0, r=0, t=40, b=0),
    'showlegend': False,
}

# API field mappings - Updated for v2 API with unified embeddings
# Removed hardcoded AIPickle fields - use enrichment fields explicitly when needed
API_FIELDS = 'doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source,doctrove_primary_date,doctrove_authors,doctrove_embedding_2d,doctrove_links'

# Visualization Configuration
VISUALIZATION_CONFIG = {
    'embedding_type': 'doctrove',  # Unified embedding field
    'point_size': 8,  # Size of scatter plot points - back to normal size
    'point_opacity': 0.7,  # Opacity of scatter plot points - 70% opaque for balanced transparency
}

# Column name mappings for DataFrame
COLUMN_MAPPINGS = {
    'doctrove_title': 'Title',
    'doctrove_abstract': 'Summary',
    'doctrove_primary_date': 'Primary Date',
    'doctrove_authors': 'Authors',
    'doctrove_source': 'Source',
    'country2': 'Country of Publication',
    'doi': 'DOI',
    'doctrove_links': 'Links'
} 