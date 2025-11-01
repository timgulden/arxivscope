"""
Graph component for creating scatter plots and clustering visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
from docscope.config.settings import GRAPH_LAYOUT, SOURCE_COLOR_MAP, DEFAULT_COLOR
import pandas as pd # Added for pd.notna
import logging
from .data_service import filter_data_by_sources

logger = logging.getLogger(__name__)


def create_empty_figure() -> go.Figure:
    """Create a consistently styled empty figure that matches the dark theme."""
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor='#2b2b2b',
        paper_bgcolor='#2b2b2b',
        xaxis=dict(showgrid=False, zeroline=False, visible=False, showline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, showline=False, showticklabels=False),
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False
    )
    return fig


def create_scatter_plot(df, selected_sources: List[str] = None, 
                       enrichment_source: Optional[str] = None, 
                       enrichment_table: Optional[str] = None,
                       enrichment_field: Optional[str] = None) -> go.Figure:
    """
    Create scatter plot from DataFrame.
    
    Args:
        df: DataFrame with paper data
        selected_sources: List of selected sources to filter by
        enrichment_source: Optional source for enrichment data
        enrichment_table: Optional enrichment table name
        enrichment_field: Optional enrichment field to use for coloring
        
    Returns:
        Plotly figure with scatter plot
    """
    
    # Input validation
    if df is None:
        logger.warning("DataFrame is None, creating empty figure")
        return create_empty_figure()
    
    if not isinstance(df, pd.DataFrame):
        logger.error(f"Invalid DataFrame type: {type(df)}")
        return create_empty_figure()
    
    # Debug logging for enrichment parameters
    logger.debug(f"=== GRAPH COMPONENT DEBUG ===")
    logger.debug(f"Enrichment parameters: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}")
    logger.debug(f"DataFrame columns: {list(df.columns)}")
    if enrichment_field:
        logger.debug(f"Enrichment field '{enrichment_field}' in columns: {enrichment_field in df.columns}")
        if enrichment_field in df.columns:
            unique_values = df[enrichment_field].dropna().unique()
            logger.debug(f"Enrichment field unique values: {unique_values}")
    
    if selected_sources is not None and not isinstance(selected_sources, list):
        logger.warning(f"Invalid selected_sources type: {type(selected_sources)}, ignoring")
        selected_sources = None
    
    if df.empty:
        # Create a subtle fallback figure that matches the dark theme
        test_fig = go.Figure()
        test_fig.add_trace(go.Scatter(
            x=[-10, 0, 10],
            y=[-10, 0, 10],
            mode='markers',
            marker=dict(
                size=15,
                color=['#666666', '#888888', '#aaaaaa'],  # Dark grey shades instead of bright colors
                symbol=['circle', 'square', 'diamond'],
                opacity=0.6  # Make them more subtle
            ),
            name='No Data Available',
            hoverinfo='skip'  # Disable hover to make them less interactive
        ))
        test_fig.update_layout(
            plot_bgcolor='#2b2b2b',
            paper_bgcolor='#2b2b2b',
            xaxis=dict(showgrid=False, zeroline=False, visible=False, showline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False, showline=False, showticklabels=False),
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False  # Hide legend for cleaner look
        )
        return test_fig
    
    # Filter by selected sources if provided
    filtered_df = filter_data_by_sources(df, selected_sources) if selected_sources else df
    
    if filtered_df.empty:
        return create_empty_figure()
    

    
    # Get visualization configuration
    from ..config.settings import VISUALIZATION_CONFIG
    config = VISUALIZATION_CONFIG
    embedding_type = config.get('embedding_type', 'title')
    show_connections = config.get('show_connections', False)
    point_size = config.get('point_size', 8)
    point_opacity = config.get('point_opacity', 0.8)
    connection_opacity = config.get('connection_opacity', 0.3)
    
    # Prepare custom data for hover - include all paper information for instant popup display
    # Reset index to ensure proper mapping after filtering
    filtered_df = filtered_df.reset_index(drop=True)
    
    # Optimized customdata creation for performance (ultra-lightweight)
    customdata = []
    for _, row in filtered_df.iterrows():
        paper_info = [
            row.get('doctrove_paper_id', ''),  # Paper ID
            row.get('Title', 'No title available'),  # Title
            '',  # Summary (empty - fetched on-demand)
            row.get('Primary Date', 'No date available'),  # Date
            row.get('Source', 'Unknown source'),  # Source
            '',  # Authors (empty - fetched on-demand)
            '',  # DOI (empty - fetched on-demand)
            row.get('similarity_score', None),  # Similarity score
            ''   # Links (empty - fetched on-demand)
        ]
        customdata.append(paper_info)
    
    fig = go.Figure()
    
    if embedding_type == 'both' and show_connections and 'title_x' in filtered_df.columns and 'abstract_x' in filtered_df.columns:
        # Show both title and abstract points connected by lines
        
        # Add connection lines first (so they appear behind points) - separate traces for thick and thin lines
        thick_lines_x = []
        thick_lines_y = []
        thin_lines_x = []
        thin_lines_y = []
        connection_count = 0
        distances = []
        
        # First pass: calculate all distances
        for _, row in filtered_df.iterrows():
            if pd.notna(row['title_x']) and pd.notna(row['abstract_x']):
                distance = ((row['title_x'] - row['abstract_x'])**2 + (row['title_y'] - row['abstract_y'])**2)**0.5
                distances.append(distance)
        
        # Calculate average distance
        avg_distance = sum(distances) / len(distances) if distances else 1.0
        
        # Second pass: separate lines by thickness
        for _, row in filtered_df.iterrows():
            if pd.notna(row['title_x']) and pd.notna(row['abstract_x']):
                
                distance = ((row['title_x'] - row['abstract_x'])**2 + (row['title_y'] - row['abstract_y'])**2)**0.5
                
                # Separate lines by thickness
                if distance < avg_distance:
                    # Thicker lines for shorter distances (more similar title/abstract)
                    thick_lines_x.extend([row['title_x'], row['abstract_x'], None])
                    thick_lines_y.extend([row['title_y'], row['abstract_y'], None])
                else:
                    # Thin lines for longer distances (more different title/abstract)
                    thin_lines_x.extend([row['title_x'], row['abstract_x'], None])
                    thin_lines_y.extend([row['title_y'], row['abstract_y'], None])
                connection_count += 1
        
        # Add connection lines with emphasis on shorter lines (more similar title/abstract)
        short_lines_x = []
        short_lines_y = []
        long_lines_x = []
        long_lines_y = []
        
        for _, row in filtered_df.iterrows():
            if pd.notna(row['title_x']) and pd.notna(row['abstract_x']):
                distance = ((row['title_x'] - row['abstract_x'])**2 + (row['title_y'] - row['abstract_y'])**2)**0.5
                
                if distance < avg_distance:
                    # Shorter lines - more visible (similar title/abstract)
                    short_lines_x.extend([row['title_x'], row['abstract_x'], None])
                    short_lines_y.extend([row['title_y'], row['abstract_y'], None])
                else:
                    # Longer lines - more subtle (different title/abstract)
                    long_lines_x.extend([row['title_x'], row['abstract_x'], None])
                    long_lines_y.extend([row['title_y'], row['abstract_y'], None])
        
        # Add shorter lines first (more visible)
        if short_lines_x:
            fig.add_trace(go.Scattergl(
                x=short_lines_x,
                y=short_lines_y,
                mode='lines',
                line=dict(color='rgba(255, 255, 255, 0.4)', width=3),
                showlegend=False,
                hoverinfo='skip',
                visible=True,
                name='Similar Connections'
            ))
        
        # Add longer lines second (more subtle)
        if long_lines_x:
            fig.add_trace(go.Scattergl(
                x=long_lines_x,
                y=long_lines_y,
                mode='lines',
                line=dict(color='rgba(255, 255, 255, 0.1)', width=1),
                showlegend=False,
                hoverinfo='skip',
                visible=True,
                name='Different Connections'
            ))
        

        
        # Add title points (diamonds with reduced opacity)
        title_mask = filtered_df['title_x'].notna()
        if title_mask.any():
            title_df = filtered_df[title_mask]
            title_colors = [colors[i] for i in range(len(filtered_df)) if title_mask.iloc[i]]
            
            fig.add_trace(go.Scatter(
                x=title_df['title_x'],
                y=title_df['title_y'],
                mode='markers',
                marker=dict(
                    size=point_size, 
                    opacity=point_opacity * 0.5,  # Reduced opacity for diamonds
                    color=title_colors,
                    symbol='diamond',
                    line=dict(width=0)  # Remove white outline
                ),
                name='Title Embeddings',
                customdata=[customdata[i] for i in range(len(filtered_df)) if title_mask.iloc[i]],
                hoverinfo='none',
                showlegend=True
            ))
        
        # Add abstract points (circles)
        abstract_mask = filtered_df['abstract_x'].notna()
        if abstract_mask.any():
            abstract_df = filtered_df[abstract_mask]
            abstract_colors = [colors[i] for i in range(len(filtered_df)) if abstract_mask.iloc[i]]
            
            fig.add_trace(go.Scatter(
                x=abstract_df['abstract_x'],
                y=abstract_df['abstract_y'],
                mode='markers',
                marker=dict(
                    size=point_size, 
                    opacity=point_opacity, 
                    color=abstract_colors,
                    symbol='circle',
                    line=dict(width=0)  # Remove white outline
                ),
                name='Abstract Embeddings',
                customdata=[customdata[i] for i in range(len(filtered_df)) if abstract_mask.iloc[i]],
                hoverinfo='none',
                showlegend=True
            ))
    else:
        # Standard single embedding type visualization
        # Check if coordinates exist
        if 'x' not in filtered_df.columns or 'y' not in filtered_df.columns:
            logger.warning("Missing x or y coordinates in DataFrame")
            # Create empty figure
            fig = go.Figure()
            fig.update_layout(
                plot_bgcolor='#2b2b2b',
                paper_bgcolor='#2b2b2b',
                xaxis=dict(showgrid=False, zeroline=False, visible=True, showline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, visible=True, showline=False, showticklabels=False),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            return fig
        

        # Debug: Show actual columns (commented out for production)
        # print(f"=== GRAPH COMPONENT: DataFrame columns: {list(filtered_df.columns)} ===")
        # print(f"=== GRAPH COMPONENT: Has 'x' column: {'x' in filtered_df.columns} ===")
        # print(f"=== GRAPH COMPONENT: Has 'y' column: {'y' in filtered_df.columns} ===")
        # print(f"=== GRAPH COMPONENT: Has 'doctrove_embedding_2d' column: {'doctrove_embedding_2d' in filtered_df.columns} ===")
        logger.debug(f"GRAPH COMPONENT: Creating scatter plot with {len(filtered_df)} points")
        
        # Check for NaN or None values (only log if debug enabled)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"NaN values in x: {filtered_df['x'].isna().sum()}, NaN values in y: {filtered_df['y'].isna().sum()}")
            logger.debug(f"None values in x: {(filtered_df['x'] == None).sum()}, None values in y: {(filtered_df['y'] == None).sum()}")
            
            # Debug: Check what's in the RAND papers
            if 'Source' in filtered_df.columns:
                rand_papers = filtered_df[filtered_df['Source'] == 'randpub']
                if not rand_papers.empty:
                    logger.debug(f"RAND papers columns: {rand_papers.columns.tolist()}")
                    logger.debug(f"RAND papers with x: {rand_papers['x'].notna().sum()}")
                    logger.debug(f"RAND papers with y: {rand_papers['y'].notna().sum()}")
                    logger.debug(f"RAND papers with doctrove_embedding_2d: {rand_papers['doctrove_embedding_2d'].notna().sum()}")
            
            # Filter out NaN values
            logger.debug(f"Before NaN filtering - x notna: {filtered_df['x'].notna().sum()}, y notna: {filtered_df['y'].notna().sum()}")
            valid_mask = filtered_df['x'].notna() & filtered_df['y'].notna()
            filtered_df = filtered_df[valid_mask]
            logger.debug(f"After filtering NaN, {len(filtered_df)} points remain")
        else:
            # Still do the filtering, just don't log it
            valid_mask = filtered_df['x'].notna() & filtered_df['y'].notna()
            filtered_df = filtered_df[valid_mask]
        
        # Optimized color mapping for performance
        colors = []
        
        # Check if we should use enrichment-based coloring
        
        if enrichment_field and enrichment_field in filtered_df.columns:
            # Use enrichment field for coloring
            logger.debug(f"Using enrichment field '{enrichment_field}' for coloring")
            
            # Get unique values from enrichment field
            unique_values = filtered_df[enrichment_field].dropna().unique()
            logger.debug(f"Enrichment field has {len(unique_values)} unique values: {unique_values}")
            
            # Create color map for enrichment values - GENERALIZABLE APPROACH
            import plotly.colors as pc
            enrichment_colors = {}
            
            # Define a smart color scheme that works for any enrichment field
            # Use semantic colors for common patterns, fallback to distinct colors
            semantic_colors = {
                # Country-related values
                'United States': '#1976D2',      # Blue
                'US': '#1976D2',                # Blue (alternative)
                'China': '#D32F2F',             # Red
                'Rest of the World': '#2E7D32', # Green
                'Other': '#2E7D32',             # Green (alternative)
                'Unknown': '#6D3E91',           # Purple for unknown
                'FAILED_BATCH': '#FF9800',      # Orange for failed
                
                # Institution-related values (if any)
                'University': '#9C27B0',        # Purple
                'Institute': '#795548',         # Brown
                'Corporation': '#607D8B',       # Blue-grey
                
                # Common boolean/status values
                'True': '#4CAF50',              # Green
                'False': '#F44336',             # Red
                'Yes': '#4CAF50',               # Green
                'No': '#F44336',                # Red
            }
            
            # Create colors for all unique values
            for i, value in enumerate(unique_values):
                if pd.isna(value) or value is None:
                    enrichment_colors[value] = DEFAULT_COLOR
                elif value in semantic_colors:
                    # Use semantic colors for known values
                    enrichment_colors[value] = semantic_colors[value]
                else:
                    # Use distinct colors for other values - ensure good contrast
                    # Use a larger color palette to avoid similar colors
                    color_palettes = [pc.qualitative.Set3, pc.qualitative.Pastel1, pc.qualitative.Dark2]
                    palette_idx = (i // len(pc.qualitative.Set3)) % len(color_palettes)
                    color_idx = i % len(pc.qualitative.Set3)
                    enrichment_colors[value] = color_palettes[palette_idx][color_idx]
            
            # Assign colors based on enrichment field values
            for value in filtered_df[enrichment_field]:
                if pd.isna(value) or value is None:
                    colors.append(DEFAULT_COLOR)
                else:
                    colors.append(enrichment_colors.get(value, DEFAULT_COLOR))
            
            # Debug: Log the colors array (only if debug enabled)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🔍 COLOR DEBUG - Colors array created: {colors}")
                logger.debug(f"🔍 COLOR DEBUG - Unique values: {unique_values}")
                logger.debug(f"🔍 COLOR DEBUG - Enrichment colors mapping: {enrichment_colors}")
                    
        else:
            # Use original source/country coloring logic
            logger.debug("Using source/country-based coloring")
            
            # Map API source names to expected source names for color mapping
            source_mapping = {
                'randpub': 'randpub',
                'extpub': 'extpub',
                'aipickle': 'aipickle',
                'openalex': 'openalex'
            }
            
            # Pre-compute color mappings for better performance
            source_colors = {}
            for source in filtered_df['Source'].unique():
                if pd.isna(source) or source is None:
                    source_colors[source] = DEFAULT_COLOR
                elif source == 'aipickle':
                    source_colors[source] = SOURCE_COLOR_MAP.get('aipickle', DEFAULT_COLOR)
                else:
                    mapped_source = source_mapping.get(source, source)
                    source_colors[source] = SOURCE_COLOR_MAP.get(mapped_source, DEFAULT_COLOR)
            
            # Vectorized color assignment - GENERALIZABLE country detection
            # Automatically detect any country-related columns for intelligent coloring
            country_column = None
            country_columns = [col for col in filtered_df.columns if any(keyword in col.lower() for keyword in ['country', 'origin', 'location', 'region'])]
            
            if country_columns:
                # Use the first country column found
                country_column = country_columns[0]
                logger.debug(f"Auto-detected country column: {country_column}")
            elif 'country2' in filtered_df.columns:
                country_column = 'country2'
                logger.debug(f"Using fallback country column: {country_column}")
            elif 'Country of Publication' in filtered_df.columns:
                country_column = 'Country of Publication'
                logger.debug(f"Using legacy country column: {country_column}")
            
            for idx, source in enumerate(filtered_df['Source']):
                # All sources now use unified source-based coloring
                colors.append(source_colors.get(source, DEFAULT_COLOR))
        
        # Convert to lists to ensure proper format for Plotly
        x_coords = filtered_df['x'].tolist()
        y_coords = filtered_df['y'].tolist()
        
        # Only log scatter plot details if debug is enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Creating scatter plot with {len(x_coords)} points")
            logger.debug(f"X coords type: {type(x_coords)}, first few: {x_coords[:3]}")
            logger.debug(f"Y coords type: {type(y_coords)}, first few: {y_coords[:3]}")
            logger.debug(f"Creating scatter trace with {len(x_coords)} points")
            logger.debug(f"Colors array length for scatter: {len(colors[:len(x_coords)])}")
            logger.debug(f"First 5 colors for scatter: {colors[:5]}")
        
        # Optimized hover text creation for performance
        hover_texts = []
        for _, row in filtered_df.iterrows():
            title = row.get('Title', 'No title available')
            # Clean up title for hover display
            if title and title != 'No title available':
                # Truncate long titles and clean up whitespace
                clean_title = ' '.join(title.replace('\n', ' ').split())
                if len(clean_title) > 100:
                    clean_title = clean_title[:97] + '...'
                hover_texts.append(clean_title)
            else:
                hover_texts.append('No title available')
        
        # Create separate scatter traces for each enrichment value to get proper legend
        if enrichment_field and enrichment_field in filtered_df.columns:
            unique_values = filtered_df[enrichment_field].dropna().unique()
            logger.debug(f"Creating separate traces for {len(unique_values)} enrichment values: {unique_values}")
            
            for value in unique_values:
                if pd.isna(value) or value is None:
                    continue
                
                # Filter data for this specific value
                value_mask = filtered_df[enrichment_field] == value
                value_df = filtered_df[value_mask]
                
                if len(value_df) == 0:
                    continue
                
                # Get color for this value - use the enrichment colors we built
                if value in enrichment_colors:
                    color = enrichment_colors[value]
                    logger.debug(f"🔍 COLOR DEBUG - Using enrichment color for '{value}': {color}")
                else:
                    # Fallback color
                    import plotly.colors as pc
                    color_idx = list(unique_values).index(value) % len(pc.qualitative.Set3)
                    color = pc.qualitative.Set3[color_idx]
                    logger.warning(f"🔍 COLOR DEBUG - No enrichment color found for '{value}', using fallback: {color}")
                
                # Create hover texts for this value
                value_hover_texts = []
                for _, row in value_df.iterrows():
                    title = row.get('Title', 'No title available')
                    if title and title != 'No title available':
                        clean_title = ' '.join(title.replace('\n', ' ').split())
                        if len(clean_title) > 100:
                            clean_title = clean_title[:97] + '...'
                        value_hover_texts.append(clean_title)
                    else:
                        value_hover_texts.append('No title available')
                
                # Create scatter trace for this value
                scatter_trace = go.Scatter(
                    x=value_df['x'].tolist(),
                    y=value_df['y'].tolist(),
                    mode='markers',
                    marker=dict(
                        size=point_size,
                        opacity=point_opacity,
                        color=color,
                        line=dict(width=0)
                    ),
                    customdata=[[
                        row.get('doctrove_paper_id', ''),  # Paper ID
                        row.get('Title', 'No title available'),  # Title
                        '',  # Summary (empty - fetched on-demand)
                        row.get('Primary Date', 'No date available'),  # Date
                        row.get('Source', 'Unknown source'),  # Source
                        '',  # Authors (empty - fetched on-demand)
                        '',  # DOI (empty - fetched on-demand)
                        row.get('similarity_score', None),  # Similarity score
                        ''   # Links (empty - fetched on-demand)
                    ] for _, row in value_df.iterrows()],
                    text=value_hover_texts,
                    hoverinfo='text',
                    showlegend=True,
                    visible=True,
                    name=str(value)
                )
                
                fig.add_trace(scatter_trace)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Added trace for '{value}' with {len(value_df)} points, color: {color}")
                    # Debug the customdata structure to verify it's correct
                    if hasattr(scatter_trace, 'customdata') and scatter_trace.customdata:
                        logger.debug(f"🔍 ENRICHMENT DEBUG: Trace customdata length: {len(scatter_trace.customdata)}")
                        if scatter_trace.customdata and len(scatter_trace.customdata) > 0:
                            first_item = scatter_trace.customdata[0]
                            logger.debug(f"🔍 ENRICHMENT DEBUG: First customdata item length: {len(first_item) if isinstance(first_item, list) else 'not a list'}")
                            logger.debug(f"🔍 ENRICHMENT DEBUG: First customdata item type: {type(first_item)}")
                            if isinstance(first_item, list) and len(first_item) >= 8:
                                logger.debug(f"🔍 ENRICHMENT DEBUG: Customdata structure looks correct for click functionality")
                            else:
                                logger.warning(f"🔍 ENRICHMENT DEBUG: Customdata structure may be incorrect for click functionality")
        else:
            # Create a single scatter trace for non-enrichment visualization
            scatter_trace = go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers',
                marker=dict(
                    size=point_size,
                    opacity=point_opacity,
                    color=colors,
                    line=dict(width=0)
                ),
                customdata=customdata,
                text=hover_texts,
                hoverinfo='text',
                showlegend=False,
                visible=True,
                name='Papers'
            )
            
            fig.add_trace(scatter_trace)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Single scatter trace created with {len(x_coords)} points")
        
        logger.debug(f"=== SCATTER PLOT CREATED ===")
        logger.debug(f"  Total traces: {len(fig.data)}")
        logger.debug(f"  Total points: {len(x_coords)}")
        logger.debug(f"  Customdata: {len(customdata) if customdata else 0}")
        logger.debug(f"  Clickmode: event+select")
        logger.debug(f"  Hoverinfo: all")
    
    # Calculate view bounds based on the data
    # REMOVE: Do not set x_range and y_range based on data, so Dash can preserve zoom/pan
    # if len(x_coords) > 0 and len(y_coords) > 0:
    #     x_min, x_max = min(x_coords), max(x_coords)
    #     y_min, y_max = min(y_coords), max(y_coords)
    #     x_padding = (x_max - x_min) * 0.1
    #     y_padding = (y_max - y_min) * 0.1
    #     x_range = [x_min - x_padding, x_max + x_padding]
    #     y_range = [y_min - y_padding, y_max + y_padding]
    #     print(f"DEBUG: Setting view bounds - x: {x_range}, y: {y_range}")
    # else:
    #     x_range = [-10, 10]
    #     y_range = [-10, 10]
    #     print(f"DEBUG: Using default view bounds - x: {x_range}, y: {y_range}")

    # Optimized layout for performance
    fig.update_layout(
        dragmode='pan',
        hovermode='closest',
        clickmode='event',  # Enable click events
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            visible=True, 
            showline=False, 
            showticklabels=False
            # autorange will be set by callback logic
        ),
        yaxis=dict(
            showgrid=False, 
            zeroline=False, 
            visible=True, 
            showline=False, 
            showticklabels=False
            # autorange will be set by callback logic
        ),
        legend_title_text=' ',
        plot_bgcolor='#2b2b2b',
        paper_bgcolor='#2b2b2b',
        font=dict(family="Arial", size=12, color='#ffffff'),
        margin=dict(l=0, r=0, t=40, b=0),
        title_font=dict(size=20, color='#ffffff'),
        showlegend=(embedding_type == 'both' and show_connections) or (enrichment_field and enrichment_field in filtered_df.columns)
    )
    
    
    logger.debug(f"GRAPH COMPONENT: Final figure has {len(fig.data)} traces")
    
    return fig


def add_clustering_overlay(fig: go.Figure, clustering_data: Dict[str, Any]) -> go.Figure:
    """
    Add clustering overlay to existing figure. Accepts overlays with 'polygons' and 'annotations' keys.
    """
    import plotly.graph_objects as go
    
    # Input validation
    if fig is None:
        logger.error("Figure is None, cannot add clustering overlay")
        return go.Figure()
    
    if not isinstance(fig, go.Figure):
        logger.error(f"Invalid figure type: {type(fig)}")
        return go.Figure()
    
    if clustering_data is None:
        logger.debug("No clustering_data provided to add_clustering_overlay.")
        return fig
    
    if not isinstance(clustering_data, dict):
        logger.error(f"Invalid clustering_data type: {type(clustering_data)}")
        return fig
    # Add polygons (Voronoi regions)
    polygons = clustering_data.get('polygons', [])
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Adding {len(polygons)} polygons to overlay.")
    for idx, poly in enumerate(polygons):
        x = poly.get('x', [])
        y = poly.get('y', [])
        # Explicitly close the polygon if not already closed
        if x and y and (x[0] != x[-1] or y[0] != y[-1]):
            x = x + [x[0]]
            y = y + [y[0]]
        if idx == 0 and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"First polygon x[0]={x[0]}, y[0]={y[0]}, x[-1]={x[-1]}, y[-1]={y[-1]}")
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines',
            line=dict(color='rgba(255,255,255,0.3)', width=1),  # 30% transparent white for subtler Voronoi lines
            showlegend=False,
            hoverinfo='skip',
            name='Cluster Region',
            opacity=1.0
        ))
        if idx == 0 and logger.isEnabledFor(logging.DEBUG):
            logger.debug("Polygon trace fill: None, fillcolor: None")
    # Add annotations (cluster labels, summaries, etc.)
    annotations = clustering_data.get('annotations', [])
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Adding {len(annotations)} annotations to overlay.")
    if 'layout' not in fig:
        fig.layout = {}
    if not hasattr(fig.layout, 'annotations') or fig.layout.annotations is None:
        fig.layout.annotations = []
    for ann in annotations:
        # Force annotation style: white, not bold, font size 18
        ann['font'] = {'color': 'white', 'size': 18, 'family': 'Arial'}
        ann['showarrow'] = False
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Annotation style: {ann['font']}")
        fig.add_annotation(**ann)
    # Re-add the main scatter trace (dots) as the last trace to ensure it's on top
    # Find the original scatter trace (mode='markers')
    marker_traces = [t for t in fig.data if hasattr(t, 'mode') and t.mode == 'markers']
    if marker_traces:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Re-adding {len(marker_traces)} marker traces to top.")
        # Remove and re-add
        for t in marker_traces:
            fig.data = tuple(trace for trace in fig.data if trace != t)
            fig.add_trace(t)
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("No marker traces found to re-add.")
    # Ensure background and grid are not changed by overlays
    # IMPORTANT: Preserve dragmode='pan' to prevent reverting to box mode
    fig.update_layout(
        plot_bgcolor='#2b2b2b',
        paper_bgcolor='#2b2b2b',
        xaxis=dict(showgrid=False, zeroline=False, visible=True, showline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=True, showline=False, showticklabels=False),
        margin=dict(l=0, r=0, t=40, b=0),
        dragmode='pan'  # Force pan mode to prevent box mode from taking over
    )
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"add_clustering_overlay: now {len(fig.data)} traces in figure. Layout: {fig.layout}")
    return fig


def create_country_distribution_chart(df) -> go.Figure:
    """
    Create country distribution chart.
    
    Args:
        df: DataFrame with paper data
        
    Returns:
        Plotly figure with country distribution
    """
    if df.empty or 'Source' not in df.columns:
        return go.Figure()
    
    # Count papers by source instead of country
    source_counts = df['Source'].value_counts()
    
    # Create colors for sources
    colors = []
    for source in source_counts.index:
        if source in SOURCE_COLOR_MAP:
            colors.append(SOURCE_COLOR_MAP[source])
        else:
            colors.append(DEFAULT_COLOR)
    
    # Create bar chart
    fig = go.Figure(data=go.Bar(
        x=source_counts.index,
        y=source_counts.values,
        marker_color=colors,
        text=source_counts.values,
        textposition='auto'
    ))
    
    fig.update_layout(
        title='Papers by Source',
        xaxis_title='Source',
        yaxis_title='Number of Papers',
        showlegend=False
    )
    
    return fig 