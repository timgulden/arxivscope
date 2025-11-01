"""
Data Fetching Pure Functions for DocScope

This module implements data fetching operations using pure functions,
following our functional programming principles - NO SIDE EFFECTS.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
import pandas as pd
from .component_contracts_fp import ViewState, FilterState, EnrichmentState

logger = logging.getLogger(__name__)

# ============================================================================
# PURE FUNCTIONS FOR DATA FETCHING - NO SIDE EFFECTS
# ============================================================================

def create_fetch_request(view_state: ViewState, filter_state: FilterState, 
                        enrichment_state: EnrichmentState) -> Dict[str, Any]:
    """Create a data fetch request with all necessary parameters - TRULY PURE function."""
    if not all([view_state, filter_state, enrichment_state]):
        return {}
    
    # Create new request dict (immutable operation)
    fetch_request = {
        'bbox': view_state.get('bbox') if view_state else None,
        'sql_filter': filter_state.to_sql_filter() if filter_state else None,
        'search_text': filter_state.search_text if filter_state else None,
        'limit': 5000,  # Default limit
        'enrichment_params': _extract_enrichment_params(enrichment_state)
    }
    
    # Add view-specific parameters
    if view_state and view_state.get('is_zoomed'):
        fetch_request['view_zoomed'] = True
        fetch_request['x_range'] = view_state.get('x_range')
        fetch_request['y_range'] = view_state.get('y_range')
    
    return fetch_request

def fetch_data_pure(fetch_request: Dict[str, Any], data_provider: Callable) -> pd.DataFrame:
    """Fetch data using provided data provider - TRULY PURE function with injected dependency."""
    try:
        # Extract parameters from request
        bbox = fetch_request.get('bbox')
        sql_filter = fetch_request.get('sql_filter')
        search_text = fetch_request.get('search_text')
        limit = fetch_request.get('limit', 5000)
        enrichment_params = fetch_request.get('enrichment_params', {})
        
        # Fetch data using injected provider
        data = data_provider(
            limit=limit,
            bbox=bbox,
            sql_filter=sql_filter,
            search_text=search_text,
            **enrichment_params
        )
        
        # Return data as DataFrame
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            return data
        else:
            return pd.DataFrame()
            
    except Exception:
        return pd.DataFrame()

def fetch_data(fetch_request: Dict[str, Any]) -> pd.DataFrame:
    """Fetch data from API using the request parameters - wrapper with injected API dependency."""
    try:
        # Import the API function
        from .data_service import fetch_papers_from_api
        
        # Use the pure function with injected API dependency
        return fetch_data_pure(fetch_request, fetch_papers_from_api)
        
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def validate_fetch_request(fetch_request: Dict[str, Any]) -> bool:
    """Validate that fetch request is complete and valid - TRULY PURE function."""
    if not fetch_request:
        return False
    
    # Check required fields
    required_fields = ['limit']
    for field in required_fields:
        if field not in fetch_request:
            return False
    
    # Validate limit
    limit = fetch_request.get('limit')
    if not isinstance(limit, int) or limit <= 0:
        return False
    
    # Validate bbox if present
    bbox = fetch_request.get('bbox')
    if bbox and not _validate_bbox(bbox):
        return False
    
    # Validate SQL filter if present
    sql_filter = fetch_request.get('sql_filter')
    if sql_filter and not _validate_sql_filter(sql_filter):
        return False
    
    return True

# ============================================================================
# PRIVATE HELPER FUNCTIONS - ALL PURE
# ============================================================================

def _extract_enrichment_params(enrichment_state: EnrichmentState) -> Dict[str, Any]:
    """Extract enrichment parameters from enrichment state - TRULY PURE helper."""
    if not enrichment_state:
        return {}
    
    params = {}
    
    # Add similarity threshold
    if hasattr(enrichment_state, 'similarity_threshold'):
        params['similarity_threshold'] = enrichment_state.similarity_threshold
    
    # Add clustering parameters
    if hasattr(enrichment_state, 'use_clustering'):
        params['use_clustering'] = enrichment_state.use_clustering
    
    # Add LLM parameters
    if hasattr(enrichment_state, 'use_llm_summaries'):
        params['use_llm_summaries'] = enrichment_state.use_llm_summaries
    
    return params

def _validate_bbox(bbox: str) -> bool:
    """Validate bbox string format - TRULY PURE helper."""
    if not isinstance(bbox, str):
        return False
    
    try:
        # Expected format: "x1,y1,x2,y2"
        parts = bbox.split(',')
        if len(parts) != 4:
            return False
        
        coords = [float(part) for part in parts]
        x1, y1, x2, y2 = coords
        
        # Check that coordinates form a valid rectangle
        if x1 >= x2 or y1 >= y2:
            return False
        
        return True
        
    except (ValueError, TypeError):
        return False

def _validate_sql_filter(sql_filter: str) -> bool:
    """Validate SQL filter string - TRULY PURE helper."""
    if not isinstance(sql_filter, str):
        return False
    
    # Basic SQL injection prevention
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER']
    filter_upper = sql_filter.upper()
    
    for keyword in dangerous_keywords:
        if keyword in filter_upper:
            return False
    
    return True

# ============================================================================
# DATA FETCHING UTILITY FUNCTIONS - ALL PURE
# ============================================================================

def create_minimal_fetch_request() -> Dict[str, Any]:
    """Create a minimal fetch request with defaults - TRULY PURE function."""
    return {
        'limit': 5000,
        'bbox': None,
        'sql_filter': None,
        'search_text': None,
        'enrichment_params': {},
        'view_zoomed': False
    }

def merge_fetch_requests(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two fetch requests, preferring primary - TRULY PURE function."""
    if not primary:
        return secondary
    if not secondary:
        return primary
    
    # Create new merged request (immutable operation)
    merged = primary.copy()
    
    # Merge fields, preferring primary values
    for key, value in secondary.items():
        if key not in merged or merged[key] is None:
            merged[key] = value
    
    return merged

def fetch_request_to_dict(fetch_request: Dict[str, Any]) -> Dict[str, Any]:
    """Convert fetch request to serializable dictionary - TRULY PURE function."""
    if not fetch_request:
        return {}
    
    # Create copy and ensure all values are serializable
    result = {}
    for key, value in fetch_request.items():
        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
            result[key] = value
        else:
            # Convert non-serializable objects to string representation
            result[key] = str(value)
    
    return result

def dict_to_fetch_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary to fetch request - TRULY PURE function."""
    if not data:
        return create_minimal_fetch_request()
    
    # Create new fetch request with data
    fetch_request = create_minimal_fetch_request()
    
    # Update with provided data
    for key, value in data.items():
        if key in fetch_request:
            fetch_request[key] = value
    
    return fetch_request

def is_fetch_request_stable(current: Dict[str, Any], previous: Dict[str, Any], 
                           stability_threshold: float = 0.001) -> bool:
    """Check if fetch request is stable between two requests - TRULY PURE function."""
    if not current or not previous:
        return False
    
    # Check if bbox changed significantly
    current_bbox = current.get('bbox')
    previous_bbox = previous.get('bbox')
    
    if current_bbox != previous_bbox:
        if current_bbox and previous_bbox:
            # Parse bbox coordinates and check stability
            try:
                current_coords = [float(x) for x in current_bbox.split(',')]
                previous_coords = [float(x) for x in previous_bbox.split(',')]
                
                if len(current_coords) == 4 and len(previous_coords) == 4:
                    # Calculate change in bbox area
                    current_area = (current_coords[2] - current_coords[0]) * (current_coords[3] - current_coords[1])
                    previous_area = (previous_coords[2] - previous_coords[0]) * (previous_coords[3] - previous_coords[1])
                    
                    if abs(current_area - previous_area) > stability_threshold:
                        return False
            except (ValueError, IndexError):
                return False
    
    # Check if other critical parameters changed
    critical_fields = ['sql_filter', 'search_text', 'limit']
    for field in critical_fields:
        if current.get(field) != previous.get(field):
            return False
    
    return True

def optimize_fetch_request(fetch_request: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize fetch request for performance - TRULY PURE function."""
    if not fetch_request:
        return fetch_request
    
    # Create optimized copy
    optimized = fetch_request.copy()
    
    # Optimize limit based on view state
    if optimized.get('view_zoomed', False):
        # When zoomed, we can fetch fewer points for better performance
        current_limit = optimized.get('limit', 5000)
        optimized['limit'] = min(current_limit, 3000)
    
    # Optimize bbox precision
    bbox = optimized.get('bbox')
    if bbox and _is_bbox_precise(bbox):
        # Round bbox coordinates to reduce unnecessary API calls
        optimized['bbox'] = _round_bbox(bbox)
    
    return optimized

def _is_bbox_precise(bbox: str) -> bool:
    """Check if bbox coordinates are too precise - TRULY PURE helper."""
    try:
        coords = [float(x) for x in bbox.split(',')]
        if len(coords) != 4:
            return False
        
        # Check if coordinates have too many decimal places
        for coord in coords:
            if abs(coord - round(coord, 3)) < 0.001:
                return True
        
        return False
        
    except (ValueError, IndexError):
        return False

def _round_bbox(bbox: str) -> str:
    """Round bbox coordinates to reasonable precision - TRULY PURE helper."""
    try:
        coords = [float(x) for x in bbox.split(',')]
        if len(coords) != 4:
            return bbox
        
        # Round to 3 decimal places
        rounded_coords = [round(coord, 3) for coord in coords]
        return ','.join(map(str, rounded_coords))
        
    except (ValueError, IndexError):
        return bbox
