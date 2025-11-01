"""
Pure, composable figure creation functions for DocScope.

This module provides functional programming approach to creating figures
with proper view preservation, eliminating code duplication across callbacks.
"""

from typing import Dict, Optional, Any, List
import pandas as pd
import plotly.graph_objects as go
import logging

logger = logging.getLogger(__name__)


def create_figure_with_preservation(
    df: pd.DataFrame,
    view_state: Dict[str, Any],
    enrichment_state: Optional[Dict[str, Any]] = None,
    view_ranges: Optional[Dict[str, Any]] = None
) -> go.Figure:
    """
    Create a figure with proper view preservation.
    
    Args:
        df: DataFrame containing paper data
        view_state: Dictionary containing view information
        enrichment_state: Optional dictionary containing enrichment configuration
        
    Returns:
        go.Figure: Plotly figure with proper view preservation
        
    Example:
        >>> df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
        >>> view_state = {'bbox': [0, 0, 10, 10]}
        >>> fig = create_figure_with_preservation(df, view_state)
    """
    if df.empty:
        logger.warning("Empty DataFrame provided, creating empty figure")
        return create_empty_figure()
    
    # Create the base figure
    fig = create_base_scatter_plot(df, enrichment_state)
    
    # PROPER VIEW PRESERVATION: Extract and apply current view ranges
    if view_state and view_state.get('bbox'):
        # Extract bbox coordinates
        bbox = view_state['bbox']
        if isinstance(bbox, str):
            try:
                coords = [float(x.strip()) for x in bbox.split(',')]
                if len(coords) == 4:
                    x1, y1, x2, y2 = coords
                    x_range = [x1, x2]
                    y_range = [y1, y2]
                else:
                    logger.warning(f"Invalid bbox format: {bbox}")
                    x_range = None
                    y_range = None
            except ValueError:
                logger.warning(f"Could not parse bbox: {bbox}")
                x_range = None
                y_range = None
        elif isinstance(bbox, list) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            x_range = [x1, x2]
            y_range = [y1, y2]
        else:
            logger.warning(f"Unexpected bbox format: {bbox}")
            x_range = None
            y_range = None
        
        if x_range and y_range and len(x_range) == 2 and len(y_range) == 2:
            fig.layout.xaxis.range = x_range
            fig.layout.yaxis.range = y_range
            fig.layout.xaxis.autorange = False
            fig.layout.yaxis.autorange = False
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Applied view ranges: x={x_range}, y={y_range}")
        else:
            logger.warning(f"Invalid view ranges: x={x_range}, y={y_range}")
            # CRITICAL: Do NOT enable autorange here - this could interfere with zoom/pan
            # The initial load callback should handle autorange, not this function
            # Just leave autorange as False to preserve any existing view state
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Invalid view ranges - preserving current autorange state")
    else:
        # No view ranges available - this is likely an initial load
        # CRITICAL: Do NOT enable autorange here - this could interfere with zoom/pan
        # The initial load callback should handle autorange, not this function
        # Just leave autorange as False to preserve any existing view state
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("No view ranges - preserving current autorange state")
    
    # CRITICAL: Always apply our DocScope styling, regardless of view state
    # This ensures initial load gets proper colors and styling
    fig = apply_common_layout(fig)
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Created figure with {len(df)} points and view preservation")
    return fig


def create_base_scatter_plot(
    df: pd.DataFrame,
    enrichment_state: Optional[Dict[str, Any]] = None
) -> go.Figure:
    """
    Create a base scatter plot from DataFrame.
    
    Args:
        df: DataFrame containing paper data
        enrichment_state: Optional dictionary containing enrichment configuration
        
    Returns:
        go.Figure: Basic scatter plot without view preservation
    """
    if df.empty:
        return create_empty_figure()
    
    # Check if we have the required columns
    required_columns = ['x', 'y']
    if not all(col in df.columns for col in required_columns):
        logger.error(f"Missing required columns: {required_columns}")
        return create_empty_figure()
    
    # Create figure
    fig = go.Figure()
    
    if enrichment_state and is_enrichment_active(enrichment_state):
        # Create enrichment-based visualization
        fig = create_enrichment_scatter_plot(df, enrichment_state)
    else:
        # Create basic scatter plot
        fig = create_basic_scatter_plot(df)
    
    # Don't apply common layout here - it will be applied in create_figure_with_preservation
    # This prevents duplicate styling application
    
    return fig


def create_basic_scatter_plot(df: pd.DataFrame) -> go.Figure:
    """
    Create a basic scatter plot without enrichment.
    
    Args:
        df: DataFrame containing paper data
        
    Returns:
        go.Figure: Basic scatter plot
    """
    fig = go.Figure()
    
    # Import DocScope settings for proper point styling
    try:
        from ..config.settings import VISUALIZATION_CONFIG, SOURCE_COLOR_MAP
        point_size = VISUALIZATION_CONFIG.get('point_size', 8)
        point_opacity = VISUALIZATION_CONFIG.get('point_opacity', 0.7)
    except ImportError:
        point_size = 8
        point_opacity = 0.7
        # Fallback color maps for testing
        SOURCE_COLOR_MAP = {
            'openalex': '#FF8C00',      # Orange for OpenAlex
            'randpub': '#6D3E91',       # Purple for RAND Publications
            'extpub': '#B19CD9',        # Light purple for External RAND
            'aipickle': '#2E7D32',      # Darker green for ArXiv AI Subset
        }
    
    # Check if we have source information for proper coloring
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"DataFrame columns: {list(df.columns)}")
    
    # The data_service renames 'doctrove_source' to 'Source', so check both
    source_column = None
    if 'doctrove_source' in df.columns:
        source_column = 'doctrove_source'
    elif 'Source' in df.columns:
        source_column = 'Source'
    
    if source_column:
        # Use source-based coloring like the original
        unique_sources = df[source_column].unique()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Found sources in '{source_column}': {unique_sources}")
        
        colors = []
        aipickle_count = 0
        
        for idx, source in enumerate(df[source_column]):
            if source == 'aipickle':
                aipickle_count += 1
                # All sources now use unified source-based coloring
                color = SOURCE_COLOR_MAP.get('aipickle', '#4CAF50')
                colors.append(color)
            elif source in SOURCE_COLOR_MAP:
                colors.append(SOURCE_COLOR_MAP[source])
            else:
                colors.append('#1976D2')  # Default blue for unknown sources
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Unknown source '{source}' - using default blue")
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Total aipickle papers found: {aipickle_count}")
            logger.debug(f"Final color count: {len(colors)}")
    else:
        # Fallback to default color
        logger.warning("No source column found (neither 'doctrove_source' nor 'Source') - using default blue")
        colors = '#1976D2'
    
    # Add single scatter trace
    fig.add_trace(
        go.Scatter(
            x=df['x'],
            y=df['y'],
            mode='markers',
            marker=dict(
                size=point_size,
                color=colors,  # Use source-based colors
                opacity=point_opacity,
                line=dict(width=0)  # Remove white outline like original
            ),
            text=df.get('title', ''),  # Use title if available
            hovertemplate='<b>%{text}</b><br>' +
                         'x: %{x}<br>' +
                         'y: %{y}<br>' +
                         '<extra></extra>',
            name='Papers',
            hoverinfo='none'  # Match original behavior
        )
    )
    
    return fig


def create_enrichment_scatter_plot(
    df: pd.DataFrame,
    enrichment_state: Dict[str, Any]
) -> go.Figure:
    """
    Create a scatter plot with enrichment-based coloring.
    
    Args:
        df: DataFrame containing paper data
        enrichment_state: Dictionary containing enrichment configuration
        
    Returns:
        go.Figure: Enrichment-based scatter plot
    """
    fig = go.Figure()
    
    # Get enrichment field from state
    enrichment_field = enrichment_state.get('field')
    
    if not enrichment_field or enrichment_field not in df.columns:
        logger.warning(f"Enrichment field '{enrichment_field}' not found in DataFrame")
        return create_basic_scatter_plot(df)
    
    # Get unique enrichment values
    unique_values = df[enrichment_field].dropna().unique()
    
    if len(unique_values) == 0:
        logger.warning(f"No valid enrichment values found in field '{enrichment_field}'")
        return create_basic_scatter_plot(df)
    
    # Create separate trace for each enrichment value
    for value in unique_values:
        # Filter data for this value
        mask = df[enrichment_field] == value
        subset = df[mask]
        
        if len(subset) == 0:
            continue
        
        # Get color for this value
        color = get_enrichment_color(value)
        
        # Add trace
        fig.add_trace(
            go.Scatter(
                x=subset['x'],
                y=subset['y'],
                mode='markers',
                marker=dict(
                    size=6,
                    color=color,
                    opacity=0.7
                ),
                text=subset.get('title', ''),
                hovertemplate='<b>%{text}</b><br>' +
                             f'{enrichment_field}: {value}<br>' +
                             'x: %{x}<br>' +
                             'y: %{y}<br>' +
                             '<extra></extra>',
                name=str(value)
            )
        )
    
    return fig


def get_enrichment_color(value: Any) -> str:
    """
    Get color for enrichment value.
    
    Args:
        value: Enrichment value
        
    Returns:
        str: Hex color code
    """
    # High-contrast color mapping for common values
    color_map = {
        'United States': '#1976D2',  # Blue
        'China': '#D32F2F',          # Red
        'Rest of the World': '#2E7D32'  # Darker green
    }
    
    # Return mapped color if available, otherwise use default
    return color_map.get(str(value), '#FF9800')  # Default orange


def apply_common_layout(fig: go.Figure) -> go.Figure:
    """
    Apply common layout settings to figure using DocScope styling.
    
    Args:
        fig: Plotly figure
        
    Returns:
        go.Figure: Figure with DocScope styling applied
    """
    # Import DocScope settings for proper styling
    try:
        from ..config.settings import GRAPH_LAYOUT, VISUALIZATION_CONFIG
    except ImportError:
        # Fallback for testing - use basic styling
        GRAPH_LAYOUT = {
            'plot_bgcolor': '#2b2b2b',
            'paper_bgcolor': '#2b2b2b',
            'margin': dict(l=0, r=0, t=40, b=0),
            'showlegend': False,
            'xaxis': {
                'title': None,  # Hide axis title completely
                'showgrid': False,
                'zeroline': False,
                'showline': False,
                'showticklabels': False,
            },
            'yaxis': {
                'title': None,  # Hide axis title completely
                'showgrid': False,
                'zeroline': False,
                'showline': False,
                'showticklabels': False,
            }
        }
        VISUALIZATION_CONFIG = {}
    
    # Apply DocScope's custom layout (dark theme, custom styling)
    fig.update_layout(**GRAPH_LAYOUT)
    
    # Don't set fixed height - let the UI component handle sizing
    # This allows the graph to use the full canvas height
    fig.update_layout(autosize=True)
    
    # Set default drag mode to pan for better user experience
    # This prevents aspect ratio problems from zoom-to-box mode
    # Force pan mode to prevent any other components from overriding it
    fig.update_layout(dragmode='pan')
    
    # Also set it directly on the layout to be extra sure
    if hasattr(fig, 'layout'):
        fig.layout.dragmode = 'pan'
    
    return fig


def apply_view_preservation(
    fig: go.Figure,
    view_state: Dict[str, Any],
    view_ranges: Optional[Dict[str, Any]] = None
) -> go.Figure:
    """
    Apply view preservation to figure following the VIEW_STABILITY_GUIDE.
    
    Args:
        fig: Plotly figure
        view_state: Dictionary containing view information
        view_ranges: Optional view_ranges store data (authoritative source)
        
    Returns:
        go.Figure: Figure with view preservation applied
    """
    # Check if we have view_ranges (the authoritative source for current view)
    if view_ranges and 'xaxis' in view_ranges and 'yaxis' in view_ranges:
        try:
            x_range = view_ranges['xaxis']
            y_range = view_ranges['yaxis']
            if len(x_range) == 2 and len(y_range) == 2:
                x1, y1, x2, y2 = x_range[0], y_range[0], x_range[1], y_range[1]
                fig.layout.xaxis.range = [x1, x2]
                fig.layout.yaxis.range = [y1, y2]
                # Disable autorange only when we have valid ranges to preserve
                fig.layout.xaxis.autorange = False
                fig.layout.yaxis.autorange = False
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Applied view preservation from view_ranges: x=[{x1}, {x2}], y=[{y1}, {y2}]")
                return fig
        except Exception as e:
            logger.warning(f"Error applying bbox from view_ranges: {e}")
    
    # Fallback: Extract bbox from view state
    bbox = view_state.get('bbox') if view_state else None
    
    if bbox:
        # Parse bbox string format: "x1,y1,x2,y2"
        try:
            if isinstance(bbox, str):
                bbox_parts = bbox.split(',')
                if len(bbox_parts) == 4:
                    x1, y1, x2, y2 = map(float, bbox_parts)
                    
                    # Set explicit ranges
                    fig.layout.xaxis.range = [x1, x2]
                    fig.layout.yaxis.range = [y1, y2]
                    
                    # Disable autorange only when we have valid ranges to preserve
                    fig.layout.xaxis.autorange = False
                    fig.layout.yaxis.autorange = False
                    
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Applied view preservation from bbox string: x=[{x1}, {x2}], y=[{y1}, {y2}]")
                else:
                    logger.warning(f"Invalid bbox string format: {bbox} (expected 4 parts, got {len(bbox_parts)})")
            elif isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                
                # Set explicit ranges
                fig.layout.xaxis.range = [x1, x2]
                fig.layout.yaxis.range = [y1, y2]
                
                # Disable autorange only when we have valid ranges to preserve
                fig.layout.xaxis.autorange = False
                fig.layout.yaxis.autorange = False
                
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Applied view preservation from bbox list: x=[{x1}, {x2}], y=[{y1}, {y2}]")
            else:
                logger.warning(f"Invalid bbox format: {bbox} (type: {type(bbox)})")
        except Exception as e:
            logger.warning(f"Error parsing bbox: {e}")
    else:
        # No view information available - do NOT enable autorange
        # CRITICAL: This could interfere with zoom/pan operations
        # The initial load callback should handle autorange, not this function
        # Just preserve the current autorange state
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("No view information available - preserving current autorange state")
    
    return fig


# apply_default_ranges function removed - no longer needed


def create_empty_figure() -> go.Figure:
    """
    Create an empty figure for when no data is available.
    
    Returns:
        go.Figure: Empty figure with appropriate message
    """
    fig = go.Figure()
    
    fig.add_annotation(
        text="No data available",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=20, color="gray")
    )
    
    # Apply DocScope styling first
    fig = apply_common_layout(fig)
    
    # CRITICAL: Do NOT enable autorange for empty figures
    # This could interfere with zoom/pan operations during normal usage
    # The initial load callback should handle autorange, not this function
    # Just preserve the current autorange state
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Empty figure created - preserving current autorange state")
    
    return fig


def is_enrichment_active(enrichment_state: Optional[Dict[str, Any]]) -> bool:
    """
    Check if enrichment is active based on enrichment state.
    
    Args:
        enrichment_state: Dictionary containing enrichment configuration
        
    Returns:
        bool: True if enrichment is active, False otherwise
    """
    if not enrichment_state:
        return False
    
    required_fields = ['source', 'table', 'field']
    return all(
        enrichment_state.get(field) and 
        isinstance(enrichment_state.get(field), str) and 
        enrichment_state.get(field).strip()
        for field in required_fields
    )


def create_figure_from_data_and_state(
    df: pd.DataFrame,
    sources: Optional[List[str]] = None,
    year_range: Optional[tuple] = None,
    search_text: Optional[str] = None,
    similarity_threshold: Optional[float] = None,
    bbox: Optional[List[float]] = None,
    enrichment_state: Optional[Dict[str, Any]] = None,
    view_ranges: Optional[Dict[str, Any]] = None
) -> go.Figure:
    """
    Create figure from data and individual state parameters.
    
    This is a convenience function for creating figures from
    callback inputs.
    
    Args:
        df: DataFrame containing paper data
        sources: List of selected source names
        year_range: Tuple of (start_year, end_year)
        search_text: Search text string
        similarity_threshold: Similarity threshold value
        bbox: Bounding box coordinates [x1, y1, x2, y2]
        enrichment_state: Optional dictionary containing enrichment configuration
        
    Returns:
        go.Figure: Plotly figure with proper view preservation
    """
    # Create view state from parameters
    view_state = {}
    
    if sources is not None:
        view_state['sources'] = sources
    
    if year_range is not None:
        view_state['year_range'] = year_range
    
    if search_text is not None:
        view_state['search_text'] = search_text
    
    if similarity_threshold is not None:
        view_state['similarity_threshold'] = similarity_threshold
    
    if bbox is not None:
        view_state['bbox'] = bbox
    
    # Create figure with preservation
    return create_figure_with_preservation(df, view_state, enrichment_state, view_ranges)


def update_figure_view(
    fig: go.Figure,
    new_bbox: List[float]
) -> go.Figure:
    """
    Update figure view with new bounding box.
    
    Args:
        fig: Plotly figure
        new_bbox: New bounding box coordinates [x1, y1, x2, y2]
        
    Returns:
        go.Figure: Figure with updated view
    """
    if not new_bbox or len(new_bbox) != 4:
        logger.warning(f"Invalid bbox format: {new_bbox}")
        return fig
    
    x1, y1, x2, y2 = new_bbox
    
    # Update ranges and disable autorange
    fig.layout.xaxis.range = [x1, x2]
    fig.layout.yaxis.range = [y1, y2]
    fig.layout.xaxis.autorange = False
    fig.layout.yaxis.autorange = False
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Updated figure view: x=[{x1}, {x2}], y=[{y1}, {y2}]")
    return fig


def get_figure_summary(fig: go.Figure) -> Dict[str, Any]:
    """
    Get summary information about a figure.
    
    Args:
        fig: Plotly figure
        
    Returns:
        Dict containing figure summary information
    """
    summary = {
        'traces': len(fig.data),
        'total_points': sum(len(trace.x) for trace in fig.data if hasattr(trace, 'x')),
        'x_range': fig.layout.xaxis.range if hasattr(fig.layout.xaxis, 'range') else None,
        'y_range': fig.layout.yaxis.range if hasattr(fig.layout.yaxis, 'range') else None,
        'autorange_x': fig.layout.xaxis.autorange if hasattr(fig.layout.xaxis, 'autorange') else None,
        'autorange_y': fig.layout.yaxis.autorange if hasattr(fig.layout.yaxis, 'autorange') else None
    }
    
    return summary
