"""
Visualization Pure Functions for DocScope

This module implements visualization operations using pure functions,
following our functional programming principles.
"""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .component_contracts_fp import ViewState, FilterState, EnrichmentState

logger = logging.getLogger(__name__)

# ============================================================================
# PURE FUNCTIONS FOR VISUALIZATION
# ============================================================================

def create_figure(data: pd.DataFrame, filter_state: FilterState, 
                 enrichment_state: EnrichmentState) -> go.Figure:
    """Create a scatter plot figure with proper styling - pure function."""
    if data.empty:
        logger.warning("No data provided for figure creation")
        return _create_empty_figure()
    
    try:
        # Create new figure (immutable operation)
        fig = go.Figure()
        
        # Add scatter plot trace
        scatter_trace = _create_scatter_trace(data, filter_state, enrichment_state)
        fig.add_trace(scatter_trace)
        
        # Apply layout
        fig.update_layout(**_get_figure_layout(filter_state, enrichment_state))
        
        # Apply styling
        fig = _apply_figure_styling(fig, filter_state, enrichment_state)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating figure: {e}")
        return _create_empty_figure()

def apply_view_preservation(figure: go.Figure, view_state: Dict[str, Any]) -> go.Figure:
    """Apply view state to figure to preserve zoom/pan - pure function."""
    if not view_state or not _validate_view_state_for_figure(view_state):
        return figure
    
    try:
        # Create new figure (immutable operation)
        new_figure = go.Figure(data=figure.data, layout=figure.layout)
        
        # Disable autorange and set explicit ranges
        new_figure.layout.xaxis.autorange = False
        new_figure.layout.yaxis.autorange = False
        
        if view_state.get('x_range'):
            new_figure.layout.xaxis.range = view_state.get('x_range')
        if view_state.get('y_range'):
            new_figure.layout.yaxis.range = view_state.get('y_range')
        
        # Add view preservation metadata
        new_figure.layout.meta = {
            'view_preserved': True,
            'view_timestamp': view_state.get('last_update'),
            'view_bbox': view_state.get('bbox')
        }
        
        return new_figure
        
    except Exception as e:
        logger.error(f"Error applying view preservation: {e}")
        return figure

def validate_figure(figure: go.Figure) -> bool:
    """Validate that figure is properly formatted - pure function."""
    if not figure:
        return False
    
    try:
        # Check if figure has data
        if not figure.data:
            logger.warning("Figure has no data")
            return False
        
        # Check if figure has layout
        if not figure.layout:
            logger.warning("Figure has no layout")
            return False
        
        # Check if first trace is scatter plot
        first_trace = figure.data[0]
        if not hasattr(first_trace, 'type') or first_trace.type != 'scatter':
            logger.warning("First trace is not a scatter plot")
            return False
        
        # Check if axes are properly configured
        if not hasattr(figure.layout, 'xaxis') or not hasattr(figure.layout, 'yaxis'):
            logger.warning("Figure missing axis configuration")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating figure: {e}")
        return False

# ============================================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================================

def _create_scatter_trace(data: pd.DataFrame, filter_state: FilterState, 
                         enrichment_state: EnrichmentState) -> go.Scatter:
    """Create scatter plot trace from data - private helper."""
    # Determine x and y columns
    x_col = _get_x_column(data)
    y_col = _get_y_column(data)
    
    # Create scatter trace
    trace = go.Scatter(
        x=data[x_col],
        y=data[y_col],
        mode='markers',
        marker=dict(
            size=_get_marker_size(data, enrichment_state),
            color=_get_marker_color(data, filter_state, enrichment_state),
            opacity=0.7,
            line=dict(width=1, color='white')
        ),
        text=_get_hover_text(data, filter_state),
        hovertemplate=_get_hover_template(filter_state, enrichment_state),
        name='Papers'
    )
    
    return trace

def _get_x_column(data: pd.DataFrame) -> str:
    """Get x-axis column name - private helper."""
    # Prefer 2D embedding columns
    if 'doctrove_embedding_2d_x' in data.columns:
        return 'doctrove_embedding_2d_x'
    elif 'umap_x' in data.columns:
        return 'umap_x'
    elif 'tsne_x' in data.columns:
        return 'tsne_x'
    else:
        # Fall back to first numeric column
        numeric_cols = data.select_dtypes(include=['number']).columns
        return numeric_cols[0] if len(numeric_cols) > 0 else data.columns[0]

def _get_y_column(data: pd.DataFrame) -> str:
    """Get y-axis column name - private helper."""
    # Prefer 2D embedding columns
    if 'doctrove_embedding_2d_y' in data.columns:
        return 'doctrove_embedding_2d_y'
    elif 'umap_y' in data.columns:
        return 'umap_y'
    elif 'tsne_y' in data.columns:
        return 'tsne_y'
    else:
        # Fall back to second numeric column
        numeric_cols = data.select_dtypes(include=['number']).columns
        return numeric_cols[1] if len(numeric_cols) > 1 else data.columns[1]

def _get_marker_size(data: pd.DataFrame, enrichment_state: EnrichmentState) -> List[float]:
    """Get marker sizes based on data and enrichment state - private helper."""
    if not enrichment_state or not hasattr(enrichment_state, 'use_clustering'):
        return [8] * len(data)  # Default size
    
    # Use clustering-based sizing if available
    if 'cluster_size' in data.columns:
        # Normalize cluster sizes to marker sizes
        sizes = data['cluster_size'].values
        min_size, max_size = 5, 15
        normalized_sizes = (sizes - sizes.min()) / (sizes.max() - sizes.min())
        return min_size + normalized_sizes * (max_size - min_size)
    
    return [8] * len(data)

def _get_marker_color(data: pd.DataFrame, filter_state: FilterState, 
                     enrichment_state: EnrichmentState) -> List[str]:
    """Get marker colors based on data and states - private helper."""
    if not data.empty and 'cluster_id' in data.columns:
        # Use cluster colors
        return _get_cluster_colors(data['cluster_id'].unique())
    elif filter_state and filter_state.selected_sources:
        # Use source-based colors
        return _get_source_colors(data, filter_state.selected_sources)
    else:
        # Use default color
        return ['#1f77b4'] * len(data)

def _get_cluster_colors(cluster_ids: List[int]) -> List[str]:
    """Get colors for clusters - private helper."""
    # Color palette for clusters
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    result = []
    for cluster_id in cluster_ids:
        color_index = cluster_id % len(colors)
        result.append(colors[color_index])
    
    return result

def _get_source_colors(data: pd.DataFrame, selected_sources: List[str]) -> List[str]:
    """Get colors based on data sources - private helper."""
    if 'doctrove_source' not in data.columns:
        return ['#1f77b4'] * len(data)
    
    # Color palette for sources
    source_colors = {
        'openalex': '#1f77b4',
        'randpub': '#ff7f0e',
        'arxiv': '#2ca02c',
        'pubmed': '#d62728'
    }
    
    colors = []
    for source in data['doctrove_source']:
        colors.append(source_colors.get(source.lower(), '#7f7f7f'))
    
    return colors

def _get_hover_text(data: pd.DataFrame, filter_state: FilterState) -> List[str]:
    """Get hover text for markers - private helper."""
    if data.empty:
        return []
    
    hover_texts = []
    for _, row in data.iterrows():
        # Create informative hover text
        title = row.get('doctrove_title', 'No title')
        source = row.get('doctrove_source', 'Unknown source')
        date = row.get('doctrove_primary_date', 'No date')
        
        hover_text = f"<b>{title}</b><br>"
        hover_text += f"Source: {source}<br>"
        hover_text += f"Date: {date}"
        
        hover_texts.append(hover_text)
    
    return hover_texts

def _get_hover_template(filter_state: FilterState, enrichment_state: EnrichmentState) -> str:
    """Get hover template for markers - private helper."""
    template = "<b>%{text}</b><br>"
    
    if enrichment_state and hasattr(enrichment_state, 'use_clustering'):
        template += "Cluster: %{marker.color}<br>"
    
    template += "<extra></extra>"
    return template

def _get_figure_layout(filter_state: FilterState, enrichment_state: EnrichmentState) -> Dict[str, Any]:
    """Get figure layout configuration - private helper."""
    layout = {
        'title': {
            'text': _get_figure_title(filter_state, enrichment_state),
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        'xaxis': {
            'title': 'X Axis',
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': '#e1e5e9'
        },
        'yaxis': {
            'title': 'Y Axis',
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': '#e1e5e9'
        },
        'hovermode': 'closest',
        'showlegend': True,
        'legend': {
            'x': 1.02,
            'y': 1,
            'xanchor': 'left',
            'yanchor': 'top'
        }
    }
    
    return layout

def _get_figure_title(filter_state: FilterState, enrichment_state: EnrichmentState) -> str:
    """Get figure title based on states - private helper."""
    title_parts = []
    
    if filter_state and filter_state.selected_sources:
        sources = ', '.join(filter_state.selected_sources)
        title_parts.append(f"Sources: {sources}")
    
    if filter_state and filter_state.year_range:
        years = f"{filter_state.year_range[0]}-{filter_state.year_range[1]}"
        title_parts.append(f"Years: {years}")
    
    if enrichment_state and hasattr(enrichment_state, 'use_clustering'):
        title_parts.append("Clustering Enabled")
    
    if title_parts:
        return " | ".join(title_parts)
    else:
        return "Document Visualization"

def _apply_figure_styling(figure: go.Figure, filter_state: FilterState, 
                         enrichment_state: EnrichmentState) -> go.Figure:
    """Apply styling to figure - private helper."""
    try:
        # Create new figure (immutable operation)
        styled_figure = go.Figure(data=figure.data, layout=figure.layout)
        
        # Apply theme
        styled_figure.update_layout(
            template='plotly_white',
            font=dict(family='Arial, sans-serif', size=12),
            dragmode='pan'  # Force pan mode to prevent box mode from taking over
        )
        
        # Apply responsive sizing
        styled_figure.update_layout(
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=50),
            dragmode='pan'  # Force pan mode to prevent box mode from taking over
        )
        
        return styled_figure
        
    except Exception as e:
        logger.error(f"Error applying figure styling: {e}")
        return figure

def _validate_view_state_for_figure(view_state: Dict[str, Any]) -> bool:
    """Validate view state for figure application - private helper."""
    if not view_state:
        return False
    
    # Check if view state has valid ranges
    if not view_state.get('x_range') or not view_state.get('y_range'):
        return False
    
    # Check if ranges are lists with 2 elements
    if len(view_state.get('x_range', [])) != 2 or len(view_state.get('y_range', [])) != 2:
        return False
    
    # Check if ranges are valid (min < max)
    x_range = view_state.get('x_range', [])
    y_range = view_state.get('y_range', [])
    if x_range[0] >= x_range[1]:
        return False
    if y_range[0] >= y_range[1]:
        return False
    
    return True

def _create_empty_figure() -> go.Figure:
    """Create an empty figure for error cases - private helper."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data available",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        title="No Data"
    )
    return fig

# ============================================================================
# VISUALIZATION UTILITY FUNCTIONS
# ============================================================================

def create_figure_with_clustering(data: pd.DataFrame, filter_state: FilterState, 
                                enrichment_state: EnrichmentState) -> go.Figure:
    """Create figure with clustering visualization - pure function."""
    if data.empty:
        return _create_empty_figure()
    
    try:
        # Create base figure
        fig = create_figure(data, filter_state, enrichment_state)
        
        # Add clustering visualization if enabled
        if enrichment_state and hasattr(enrichment_state, 'use_clustering') and enrichment_state.use_clustering:
            fig = _add_clustering_visualization(fig, data, enrichment_state)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating clustering figure: {e}")
        return _create_empty_figure()

def _add_clustering_visualization(figure: go.Figure, data: pd.DataFrame, 
                                enrichment_state: EnrichmentState) -> go.Figure:
    """Add clustering visualization to figure - private helper."""
    if 'cluster_id' not in data.columns:
        return figure
    
    try:
        # Create new figure with clustering
        cluster_fig = go.Figure(data=figure.data, layout=figure.layout)
        
        # Add cluster boundaries if available
        if hasattr(enrichment_state, 'cluster_boundaries'):
            cluster_fig = _add_cluster_boundaries(cluster_fig, enrichment_state.cluster_boundaries)
        
        return cluster_fig
        
    except Exception as e:
        logger.error(f"Error adding clustering visualization: {e}")
        return figure

def _add_cluster_boundaries(figure: go.Figure, cluster_boundaries: List[Dict]) -> go.Figure:
    """Add cluster boundary shapes to figure - private helper."""
    try:
        for boundary in cluster_boundaries:
            if 'coordinates' in boundary:
                coords = boundary['coordinates']
                if len(coords) >= 3:  # Need at least 3 points for a polygon
                    figure.add_shape(
                        type="polygon",
                        x0=min(p[0] for p in coords),
                        y0=min(p[1] for p in coords),
                        x1=max(p[0] for p in coords),
                        y1=max(p[1] for p in coords),
                        fillcolor="rgba(0,0,0,0)",
                        line=dict(color="gray", width=1, dash="dash")
                    )
        
        return figure
        
    except Exception as e:
        logger.error(f"Error adding cluster boundaries: {e}")
        return figure

def export_figure_data(figure: go.Figure) -> Dict[str, Any]:
    """Export figure data for serialization - pure function."""
    if not figure:
        return {}
    
    try:
        # Extract data from figure
        data = []
        for trace in figure.data:
            trace_data = {
                'type': trace.type,
                'x': trace.x.tolist() if hasattr(trace.x, 'tolist') else trace.x,
                'y': trace.y.tolist() if hasattr(trace.y, 'tolist') else trace.y,
                'mode': trace.mode,
                'name': trace.name
            }
            data.append(trace_data)
        
        # Extract layout information
        layout = {
            'title': figure.layout.title.text if figure.layout.title else None,
            'xaxis': {
                'title': figure.layout.xaxis.title.text if figure.layout.xaxis.title else None,
                'range': figure.layout.xaxis.range if hasattr(figure.layout.xaxis, 'range') else None
            },
            'yaxis': {
                'title': figure.layout.yaxis.title.text if figure.layout.yaxis.title else None,
                'range': figure.layout.yaxis.range if hasattr(figure.layout.yaxis, 'range') else None
            }
        }
        
        return {
            'data': data,
            'layout': layout,
            'export_timestamp': pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting figure data: {e}")
        return {}
