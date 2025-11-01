"""
View Management Functions for DocScope - Pure Functional Version

This module provides pure functions for managing view state without classes.
All functions are stateless and work with plain dictionaries.
"""

import time
from typing import Dict, List, Optional, Callable, Any

# ============================================================================
# VIEW STATE EXTRACTION - Pure Functions Only
# ============================================================================

def extract_view_from_relayout_pure(relayout_data: Dict, current_time: float) -> Optional[Dict[str, Any]]:
    """Extract view state from Dash relayoutData - TRULY PURE function."""
    if not relayout_data:
        return None
        
    # Handle autosize events
    if 'autosize' in relayout_data:
        return None
        
    # Extract x-axis range
    x_range = None
    if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
        x1, x2 = relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']
        x_range = [x1, x2]
    elif 'xaxis.range' in relayout_data and isinstance(relayout_data['xaxis.range'], list):
        x_range = relayout_data['xaxis.range']
    
    # Extract y-axis range
    y_range = None
    if 'yaxis.range[0]' in relayout_data and 'yaxis.range[1]' in relayout_data:
        y1, y2 = relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']
        y_range = [y1, y2]
    elif 'yaxis.range' in relayout_data and isinstance(relayout_data['yaxis.range'], list):
        y_range = relayout_data['yaxis.range']
    
    # Only return view state if we have valid ranges
    if not x_range or not y_range:
        return None
    
    # Set zoom/pan flags
    is_zoomed = bool(x_range and y_range)
    is_panned = is_zoomed
    
    # Convert to bbox format
    bbox = _ranges_to_bbox_string(x_range, y_range)
    
    # Return None if not zoomed (no valid view)
    if not is_zoomed:
        return None
    
    # Return plain dictionary - no classes!
    return {
        'bbox': bbox,
        'x_range': x_range,
        'y_range': y_range,
        'is_zoomed': is_zoomed,
        'is_panned': is_panned,
        'last_update': current_time
    }

def extract_view_from_relayout(relayout_data: Dict, timestamp_provider: Callable[[], float] = None) -> Optional[Dict[str, Any]]:
    """Extract view state from Dash relayoutData - wrapper with injected time dependency."""
    if timestamp_provider is None:
        timestamp_provider = time.time
    
    return extract_view_from_relayout_pure(relayout_data, timestamp_provider())

def extract_view_from_figure_pure(figure: Dict, current_time: float) -> Optional[Dict[str, Any]]:
    """Extract view state from existing figure - TRULY PURE function."""
    if not figure or 'layout' not in figure:
        return None
        
    layout = figure['layout']
    
    # Extract x-axis range
    x_range = None
    if 'xaxis' in layout and 'range' in layout['xaxis']:
        x_range = layout['xaxis']['range']
    
    # Extract y-axis range
    y_range = None
    if 'yaxis' in layout and 'range' in layout['yaxis']:
        y_range = layout['yaxis']['range']
    
    # Only return view state if we have valid ranges
    if not x_range or not y_range:
        return None
    
    # Set zoom/pan flags
    is_zoomed = bool(x_range and y_range)
    is_panned = is_zoomed
    
    # Convert to bbox format
    bbox = _ranges_to_bbox_string(x_range, y_range)
    
    # Return None if not zoomed (no valid view)
    if not is_zoomed:
        return None
    
    # Return plain dictionary - no classes!
    return {
        'bbox': bbox,
        'x_range': x_range,
        'y_range': y_range,
        'is_zoomed': is_zoomed,
        'is_panned': is_panned,
        'last_update': current_time
    }

def extract_view_from_figure(figure: Dict, timestamp_provider: Callable[[], float] = None) -> Optional[Dict[str, Any]]:
    """Extract view state from existing figure - wrapper with injected time dependency."""
    if timestamp_provider is None:
        timestamp_provider = time.time
    
    return extract_view_from_figure_pure(figure, timestamp_provider())

# ============================================================================
# VIEW STATE VALIDATION - Pure Functions Only
# ============================================================================

def validate_view_state(view_state: Dict[str, Any]) -> bool:
    """Validate view state dictionary - TRULY PURE function."""
    if not view_state:
        return False
    
    x_range = view_state.get('x_range')
    y_range = view_state.get('y_range')
    
    if not x_range or not y_range:
        return False
    
    if not isinstance(x_range, list) or not isinstance(y_range, list):
        return False
    
    if len(x_range) != 2 or len(y_range) != 2:
        return False
    
    if x_range[0] >= x_range[1]:
        return False
    
    if y_range[0] >= y_range[1]:
        return False
    
    return True

# ============================================================================
# VIEW STATE CREATION - Pure Functions Only
# ============================================================================

def create_default_view_state_pure(current_time: float) -> Dict[str, Any]:
    """Create a default view state - TRULY PURE function."""
    return {
        'bbox': None,
        'x_range': None,
        'y_range': None,
        'is_zoomed': False,
        'is_panned': False,
        'last_update': current_time
    }

def create_default_view_state(timestamp_provider: Callable[[], float] = None) -> Dict[str, Any]:
    """Create a default view state - wrapper with injected time dependency."""
    if timestamp_provider is None:
        timestamp_provider = time.time
    
    return create_default_view_state_pure(timestamp_provider())

def create_view_state_from_ranges_pure(x_range: List[float], y_range: List[float], current_time: float) -> Dict[str, Any]:
    """Create view state from coordinate ranges - TRULY PURE function."""
    return {
        'bbox': _ranges_to_bbox_string(x_range, y_range),
        'x_range': x_range.copy(),  # Copy to ensure immutability
        'y_range': y_range.copy(),  # Copy to ensure immutability
        'is_zoomed': True,
        'is_panned': True,
        'last_update': current_time
    }

def create_view_state_from_ranges(x_range: List[float], y_range: List[float], timestamp_provider: Callable[[], float] = None) -> Dict[str, Any]:
    """Create view state from coordinate ranges - wrapper with injected time dependency."""
    if timestamp_provider is None:
        timestamp_provider = time.time
    
    return create_view_state_from_ranges_pure(x_range, y_range, timestamp_provider())

# ============================================================================
# VIEW STATE UTILITY FUNCTIONS - ALL PURE
# ============================================================================

def _ranges_to_bbox_string(x_range: List[float], y_range: List[float]) -> str:
    """Convert coordinate ranges to bbox string - TRULY PURE helper."""
    if len(x_range) == 2 and len(y_range) == 2:
        return f"{x_range[0]},{y_range[0]},{x_range[1]},{y_range[1]}"
    return ""

def is_view_stable(current_view: Dict[str, Any], previous_view: Dict[str, Any], 
                   stability_threshold: float = 0.001) -> bool:
    """Check if view is stable between two states - TRULY PURE function."""
    if not current_view or not previous_view:
        return False
    
    if not validate_view_state(current_view) or not validate_view_state(previous_view):
        return False
    
    # Check x-range stability
    current_x = current_view.get('x_range')
    previous_x = previous_view.get('x_range')
    if current_x and previous_x:
        x_diff = abs(current_x[0] - previous_x[0]) + abs(current_x[1] - previous_x[1])
        if x_diff > stability_threshold:
            return False
    
    # Check y-range stability
    current_y = current_view.get('y_range')
    previous_y = previous_view.get('y_range')
    if current_y and previous_y:
        y_diff = abs(current_y[0] - previous_y[0]) + abs(current_y[1] - previous_y[1])
        if y_diff > stability_threshold:
            return False
    
    return True

def merge_view_states(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two view states, preferring primary - TRULY PURE function."""
    if not primary:
        return secondary
    if not secondary:
        return primary
    
    # Create new merged view state as plain dictionary
    merged = {}
    
    # Prefer primary values, fall back to secondary
    merged['bbox'] = primary.get('bbox') or secondary.get('bbox')
    merged['x_range'] = primary.get('x_range') or secondary.get('x_range')
    merged['y_range'] = primary.get('y_range') or secondary.get('y_range')
    merged['is_zoomed'] = primary.get('is_zoomed', False) or secondary.get('is_zoomed', False)
    merged['is_panned'] = primary.get('is_panned', False) or secondary.get('is_panned', False)
    merged['last_update'] = max(primary.get('last_update', 0), secondary.get('last_update', 0))
    
    return merged

def view_state_to_dict(view_state: Dict[str, Any]) -> Dict[str, Any]:
    """Convert view state to dictionary - TRULY PURE function (now just returns the dict)."""
    if not view_state:
        return {}
    
    return view_state.copy()  # Return copy to ensure immutability

def dict_to_view_state_pure(data: Dict[str, Any], current_time: float) -> Dict[str, Any]:
    """Convert dictionary to view state - TRULY PURE function (now just returns the dict)."""
    return {
        'bbox': data.get('bbox'),
        'x_range': data.get('x_range'),
        'y_range': data.get('y_range'),
        'is_zoomed': data.get('is_zoomed', False),
        'is_panned': data.get('is_panned', False),
        'last_update': data.get('last_update', current_time)
    }

def dict_to_view_state(data: Dict[str, Any], timestamp_provider: Callable[[], float] = None) -> Dict[str, Any]:
    """Convert dictionary to view state - wrapper with injected time dependency."""
    if timestamp_provider is None:
        timestamp_provider = time.time
    
    return dict_to_view_state_pure(data, timestamp_provider())

# ============================================================================
# FIGURE INTEGRATION - Pure Functions Only
# ============================================================================

def preserve_view_in_figure(figure: Any, view_state: Dict[str, Any]) -> Any:
    """Apply view state to figure to preserve zoom/pan - TRULY PURE function."""
    if not validate_view_state(view_state):
        return figure
        
    # Create new figure (immutable operation)
    new_figure = figure.copy() if hasattr(figure, 'copy') else figure
    
    # Disable autorange and set explicit ranges
    if hasattr(new_figure, 'layout'):
        if hasattr(new_figure.layout, 'xaxis'):
            new_figure.layout.xaxis.autorange = False
        if hasattr(new_figure.layout, 'yaxis'):
            new_figure.layout.yaxis.autorange = False
        
        x_range = view_state.get('x_range')
        y_range = view_state.get('y_range')
        
        if x_range and hasattr(new_figure.layout, 'xaxis'):
            new_figure.layout.xaxis.range = x_range
        if y_range and hasattr(new_figure.layout, 'yaxis'):
            new_figure.layout.yaxis.range = y_range
        
    return new_figure
