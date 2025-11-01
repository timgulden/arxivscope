import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import umap
import dash_bootstrap_components as dbc
import numpy as np
from scipy.spatial import Voronoi
from sklearn.cluster import DBSCAN, KMeans
import plotly.graph_objects as go
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, Point, MultiPoint, box
from shapely.ops import unary_union
import math
from shapely.ops import voronoi_diagram
import requests
import re
import certifi
from dash.dependencies import ALL
from dash.exceptions import PreventUpdate
import dash
import json
from typing import List, Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:5001/api"

def voronoi_finite_polygons_2d(vor, bbox):
    # bbox: (min_x, max_x, min_y, max_y)
    new_regions = []
    new_vertices = vor.vertices.tolist()
    center = vor.points.mean(axis=0)
    radius = max(bbox[1] - bbox[0], bbox[3] - bbox[2]) * 2

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]
        if all(v >= 0 for v in vertices):
            # Finite region
            polygon = [vor.vertices[v] for v in vertices]
        else:
            # Infinite region
            ridges = all_ridges[p1]
            polygon = [v for v in vertices if v >= 0]
            for p2, v1, v2 in ridges:
                if v2 < 0:
                    v1, v2 = v2, v1
                if v1 >= 0 and v2 >= 0:
                    continue
                # Compute the missing endpoint
                t = vor.points[p2] - vor.points[p1]  # tangent
                t /= np.linalg.norm(t)
                n = np.array([-t[1], t[0]])  # normal
                midpoint = vor.points[[p1, p2]].mean(axis=0)
                direction = np.sign(np.dot(midpoint - center, n)) * n
                far_point = vor.vertices[v2] + direction * radius
                polygon.append(len(new_vertices))
                new_vertices.append(far_point.tolist())
            polygon = [new_vertices[v] for v in polygon]
        # Clip polygon to bounding box
        poly = Polygon(polygon).buffer(0)  # Clean up geometry
        if not poly.is_valid or poly.is_empty:
            continue  # Skip truly degenerate polygons
        min_x, max_x, min_y, max_y = bbox
        bbox_poly = box(min_x, min_y, max_x, max_y)
        poly = poly.intersection(bbox_poly)
        if not poly.is_empty and poly.is_valid:
            new_regions.append(poly)
    return new_regions

def fetch_papers_from_api(limit: int = 10000, bbox: Optional[str] = None, 
                         sql_filter: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch papers from the API and convert to DataFrame.
    
    Args:
        limit: Maximum number of papers to fetch
        bbox: Optional bounding box filter (x1,y1,x2,y2)
        sql_filter: Optional SQL filter
        
    Returns:
        DataFrame with papers data
    """
    try:
        # Build query parameters
        params = {
            'limit': limit,
            'fields': 'doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source,doctrove_primary_date,doctrove_embedding_2d,aipickle_country'
        }
        
        if bbox:
            params['bbox'] = bbox
            
        if sql_filter:
            params['sql_filter'] = sql_filter
        
        # Make API request
        response = requests.get(f"{API_BASE_URL}/papers", params=params)
        response.raise_for_status()
        
        data = response.json()
        papers = data['papers']
        
        if not papers:
            print("No papers returned from API")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(papers)
        
        # Extract 2D coordinates from point format string "(x,y)"
        if 'title_embedding_2d' in df.columns:
            def parse_point(point_str):
                if pd.isna(point_str) or not point_str:
                    return None, None
                try:
                    # Remove parentheses and split by comma
                    point_str = point_str.strip('()')
                    x, y = map(float, point_str.split(','))
                    return x, y
                except (ValueError, AttributeError):
                    return None, None
            
            # Parse coordinates
            coords = df['title_embedding_2d'].apply(parse_point)
            df['x'] = [coord[0] if coord[0] is not None else None for coord in coords]
            df['y'] = [coord[1] if coord[1] is not None else None for coord in coords]
        
        # Clean up column names to match original app
        df = df.rename(columns={
            'doctrove_title': 'Title',
            'doctrove_abstract': 'Summary',
            'doctrove_primary_date': 'Submitted Date',
            'aipickle_country': 'Country of Publication'
        })
        
        # Handle missing country data - fill with default value
        if 'Country of Publication' not in df.columns:
            df['Country of Publication'] = 'Unknown'
        else:
            # Fill null/empty values with 'Unknown'
            df['Country of Publication'] = df['Country of Publication'].fillna('Unknown')
            df.loc[df['Country of Publication'] == '', 'Country of Publication'] = 'Unknown'
        
        # Add index for compatibility
        df.reset_index(drop=False, inplace=True)
        
        print(f"Fetched {len(df)} papers from API")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching papers from API: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing API response: {e}")
        return pd.DataFrame()

def get_available_sources() -> List[str]:
    """Get available sources/countries from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        response.raise_for_status()
        data = response.json()
        sources = [source['doctrove_source'] for source in data['sources']]
        return sorted(sources)
    except Exception as e:
        print(f"Error fetching sources: {e}")
        return []

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Configuration
TARGET_RECORDS_PER_VIEW = 500  # Target records for initial load and per zoom level

# API call debouncing
import time
last_zoom_state = None
last_api_call_time = 0
DEBOUNCE_DELAY_SECONDS = 0.05  # Reduced to 50ms for more responsive zooms

# Global data store - this will be the single source of truth
current_data = pd.DataFrame()
current_zoom_state = None

# Color mapping for countries/sources
country_color_map = {
    'United States': '#1E90FF',  # Dodger Blue
    'China': '#FF4444',  # Red
    'Rest of the World': '#4CAF50',  # Green
}

# Default color for other countries
default_color = 'green'

def get_country_color(country: str) -> str:
    """Get color for a country/source."""
    return country_color_map.get(country, default_color)

def fetch_papers_for_view(bbox: Optional[str] = None, limit: int = TARGET_RECORDS_PER_VIEW) -> pd.DataFrame:
    """
    Fetch papers from API for the current view.
    
    Args:
        bbox: Optional bounding box filter (x1,y1,x2,y2)
        limit: Maximum number of papers to fetch
        
    Returns:
        DataFrame with papers data
    """
    # Always fetch fresh data from API
    fetched_df = fetch_papers_from_api(limit=limit, bbox=bbox)
    return fetched_df

def load_initial_data() -> pd.DataFrame:
    """Load initial data at startup."""
    print("Loading initial data from API...")
    df = fetch_papers_for_view(limit=TARGET_RECORDS_PER_VIEW)
    return df

# Create initial figure
fig = go.Figure()

fig.update_layout(
    title={
        'text': 'Clusters of Papers Published in the Field of AI and LLMs',
        'y': 0.9,
        'x': 0.7,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {
            'size': 24,
            'color': '#333333',
            'family': 'Arial, sans-serif',
            'weight': 'bold',
        },
    },
    plot_bgcolor='#f0f0f0',
    paper_bgcolor='#d9d9d9',
    margin=dict(l=30, r=30, t=90, b=30),
    showlegend=False,
)

app.layout = html.Div(
    style={
        'position': 'relative',
        'width': '100%',
        'height': '100vh',
        'display': 'flex',
        'flex-direction': 'column',
        'backgroundColor': '#1e1e1e',
    },
    children=[
        dcc.Store(id='cluster-busy', data=False),
        dcc.Store(id='cluster-overlay', data=None),
        dcc.Store(id='clear-selection-store', data=0),
        dcc.Store(id='data-store', data=[]),  # Single source of truth for data
        html.Div(
            style={
                'display': 'flex',
                'flex-direction': 'row',
                'height': '100%',
            },
            children=[
                # Scatter Plot Area (flex: 3)
                html.Div(
                    style={
                        'flex': '3',
                        'display': 'flex',
                        'flex-direction': 'column',
                        'backgroundColor': '#2b2b2b',
                        'padding': '20px',
                        'height': '100%',
                        'overflow': 'hidden',
                    },
                    children=[
                        # Top controls in a horizontal layout
                        html.Div([
                            # Status indicator
                            html.Div(
                                id='status-indicator',
                                children='Loading data...',
                                style={
                                    'margin': '10px',
                                    'padding': '10px 20px',
                                    'background-color': '#FFA500',
                                    'color': 'white',
                                    'border-radius': '5px',
                                    'font-weight': 'bold',
                                }
                            ),
                            # Compute clusters button
                            html.Button(
                                'Compute clusters',
                                id='compute-clusters-button',
                                n_clicks=0,
                                style={
                                    'margin': '10px',
                                    'padding': '10px 20px',
                                    'background-color': '#4CAF50',
                                    'color': 'white',
                                    'border': 'none',
                                    'border-radius': '5px',
                                    'cursor': 'pointer',
                                    'transition': 'background-color 0.2s',
                                }
                            ),
                            # Number of clusters input
                            html.Div([
                                html.Label(
                                    "Number of Clusters:",
                                    style={'color': '#ffffff', 'margin-right': '10px'}
                                ),
                                dcc.Input(
                                    id='num-clusters',
                                    type='number',
                                    min=1,
                                    max=999,
                                    step=1,
                                    value=30,
                                    style={'width': '80px', 'margin-right': '20px'}
                                )
                            ], style={'display': 'flex', 'align-items': 'center', 'margin': '10px'}),
                            # Show region labels checkbox
                            html.Div([
                                dcc.Checklist(
                                    id='show-region-labels',
                                    options=[{'label': 'Show Region Labels', 'value': 'show'}],
                                    value=['show'],
                                    style={'color': '#fff', 'margin': '10px'}
                                )
                            ], style={'display': 'flex', 'align-items': 'center'}),
                        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px', 'justify-content': 'space-between'}),
                        # Graph
                        dcc.Graph(
                            id="graph-3",
                            style={'height': 'calc(100% - 60px)'},
                            config={'displayModeBar': True, 'scrollZoom': True}
                        ),
                    ],
                ),
                # Sidebar (flex: 1)
                html.Div(
                    style={
                        'flex': '1',
                        'padding': '20px',
                        'backgroundColor': '#ffffff',
                        'height': '100%',
                        'overflowY': 'auto',
                        'box-shadow': '0 0 10px rgba(0,0,0,0.1)',
                        'color': '#000000',
                        'display': 'flex',
                        'flex-direction': 'column',
                    },
                    children=[
                        html.Div(
                            id='content-display-area',
                            style={'flex': '1 1 auto', 'overflowY': 'auto'},
                            children='Click on a point to see details.'
                        ),
                        # Filters section at the bottom
                        html.Div(
                            id='filters-section',
                            style={
                                'flex': '0 0 auto',
                                'margin-top': '20px',
                                'padding': '10px',
                                'border': '1px solid #ccc',
                                'border-radius': '5px',
                                'background-color': '#f9f9f9',
                            },
                            children=[
                                html.Div(
                                    id='category-filter-container',
                                    style={'margin-bottom': '15px'},
                                    children=[
                                        html.P('Loading filters...', 
                                               style={'color': '#666', 'text-align': 'center'}),
                                        # Placeholder category-filter component to prevent Dash callback warnings
                                        dbc.Checklist(
                                            id='category-filter',
                                            options=[],
                                            value=[],
                                            style={'display': 'none'}  # Hidden until data loads
                                        )
                                    ],
                                ),
                            ],
                        ),

                    ],
                ),
            ],
        ),
    ],
)

# Unified callback for data-store.data: only use relayoutData as Input
@app.callback(
    Output('data-store', 'data'),
    [Input('graph-3', 'relayoutData')],
    prevent_initial_call=False
)
def unified_data_store_callback(relayoutData):
    global last_api_call_time, last_zoom_state
    # Initial load: relayoutData is None
    if relayoutData is None:
        try:
            last_api_call_time = time.time()
            df = load_initial_data()
            if df.empty:
                return []
            print(f"Initial data loaded: {len(df)} papers")
            last_zoom_state = None
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading initial data: {e}")
            return []
    # Handle autosize events (reset to full view)
    if relayoutData and 'autosize' in relayoutData:
        print("Zoom callback: Autosize detected, resetting to full view")
        fetched_df = fetch_papers_for_view(limit=TARGET_RECORDS_PER_VIEW)
        if not fetched_df.empty:
            last_zoom_state = None
            return fetched_df.to_dict('records')
        return dash.no_update
    # Extract zoom ranges
    x_range = [relayoutData.get('xaxis.range[0]'), relayoutData.get('xaxis.range[1]')]
    y_range = [relayoutData.get('yaxis.range[0]'), relayoutData.get('yaxis.range[1]')]
    print(f"Zoom callback: Extracted ranges - x: {x_range}, y: {y_range}")
    if any(r is None for r in x_range + y_range):
        print(f"Zoom callback: Invalid ranges, skipping - x: {x_range}, y: {y_range}")
        return dash.no_update
    bbox = f"{x_range[0]},{y_range[0]},{x_range[1]},{y_range[1]}"
    new_zoom_state = (x_range[0], y_range[0], x_range[1], y_range[1])
    print(f"Zoom callback: Zoom state changed from {last_zoom_state} to {new_zoom_state}")
    current_time = time.time()
    if last_api_call_time > 0 and (current_time - last_api_call_time) < DEBOUNCE_DELAY_SECONDS:
        remaining = DEBOUNCE_DELAY_SECONDS - (current_time - last_api_call_time)
        print(f"Debouncing API call - {remaining:.1f}s remaining")
        return dash.no_update
    if last_zoom_state and abs(new_zoom_state[0] - last_zoom_state[0]) < 0.01 and \
       abs(new_zoom_state[1] - last_zoom_state[1]) < 0.01 and \
       abs(new_zoom_state[2] - last_zoom_state[2]) < 0.01 and \
       abs(new_zoom_state[3] - last_zoom_state[3]) < 0.01:
        print("Zoom callback: Insignificant zoom change, skipping")
        return dash.no_update
    print(f"Zoom callback: Fetching data for bbox {bbox}")
    last_api_call_time = current_time
    fetched_df = fetch_papers_for_view(bbox=bbox, limit=TARGET_RECORDS_PER_VIEW)
    if fetched_df.empty:
        print(f"Zoom callback: No data found for bbox {bbox}")
        return dash.no_update
    last_zoom_state = new_zoom_state
    countries = sorted(fetched_df['Country of Publication'].unique())
    print(f"Zoom callback: Fetched {len(fetched_df)} papers, returning to store")
    print(f"Zoom callback: New data contains countries: {countries}")
    return fetched_df.to_dict('records')

# Callback to update status indicator when data is loaded
@app.callback(
    [Output('status-indicator', 'children'),
     Output('status-indicator', 'style')],
    [Input('data-store', 'data')],
    prevent_initial_call=False
)
def update_status_on_data_load(data_store):
    if not data_store:
        return 'Loading data...', {
            'margin': '10px',
            'padding': '10px 20px',
            'background-color': '#ff9800',  # Orange for loading
            'color': 'white',
            'border-radius': '5px',
            'font-weight': 'bold'
        }
    
    # Convert store data to DataFrame
    df = pd.DataFrame(data_store)
    return f'Loaded {len(df)} papers | Showing {len(df)}', {
        'margin': '10px',
        'padding': '10px 20px',
        'background-color': '#4CAF50',  # Green for success
        'color': 'white',
        'border-radius': '5px',
        'font-weight': 'bold'
    }

# Callback to update filters when data is loaded
@app.callback(
    Output('category-filter-container', 'children'),
    [Input('data-store', 'data')],
    prevent_initial_call=True
)
def update_filters(data_store):
    if not data_store:
        return html.P('Loading filters...', 
                     style={'color': '#666', 'text-align': 'center'})
    
    # Convert store data to DataFrame to get countries
    df = pd.DataFrame(data_store)
    countries = sorted(df['Country of Publication'].unique())
    
    # Create filter options with colors
    filter_options = []
    for cat in countries:
        color = get_country_color(cat)
        filter_options.append({
            'label': html.Span([
                html.Span(style={
                    'display': 'inline-block',
                    'width': '12px',
                    'height': '12px',
                    'background-color': color,
                    'margin-right': '10px'
                }),
                cat
            ]),
            'value': cat
        })
    
    return [
        html.H4('Filter by Country:', style={'margin-bottom': '10px', 'color': '#333'}),
        dbc.Checklist(
            id='category-filter',
            options=filter_options,
            value=countries,
            style={'width': '100%'},
            input_style={
                'margin-right': '5px',
                'cursor': 'pointer',
            },
            label_checked_style={
                'font-weight': 'bold',
                'color': '#000000',
            },
            label_style={
                'display': 'flex',
                'align-items': 'center',
                'justify-content': 'left',
                'padding': '10px',
                'margin': '5px 0',
                'border': '2px solid #ccc',
                'border-radius': '5px',
                'width': '95%',
                'height': '30px',
                'text-align': 'left',
                'background-color': '#f9f9f9',
                'cursor': 'pointer',
                'transition': 'all 0.2s ease-in-out',
                'color': '#000000',
            },
        )
    ]

# Callback to update status when filters change
@app.callback(
    [Output('status-indicator', 'children', allow_duplicate=True),
     Output('status-indicator', 'style', allow_duplicate=True)],
    [Input('category-filter', 'value')],
    [State('data-store', 'data')],
    prevent_initial_call=True
)
def update_status_on_filter_change(selected_countries, data_store):
    if not data_store:
        raise PreventUpdate
    
    # Convert store data to DataFrame
    df = pd.DataFrame(data_store)
    
    if not selected_countries:
        filtered_count = 0
    else:
        filtered_df = df[df['Country of Publication'].isin(selected_countries)]
        filtered_count = len(filtered_df)
    
    return f'Loaded {len(df)} papers | Showing {filtered_count}', {
        'margin': '10px',
        'padding': '10px 20px',
        'background-color': '#4CAF50',  # Keep green for success
        'color': 'white',
        'border-radius': '5px',
        'font-weight': 'bold'
    }

# Busy state management
@app.callback(
    Output('cluster-busy', 'data'),
    [Input('compute-clusters-button', 'n_clicks')],
    [State('category-filter', 'value'),
     State('num-clusters', 'value'),
     State('graph-3', 'figure'),
     State('graph-3', 'relayoutData')],
    prevent_initial_call=True
)
def set_busy(n_clicks, selected_countries, num_clusters, current_figure, relayoutData):
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    return True

@app.callback(
    [Output('compute-clusters-button', 'children'),
     Output('compute-clusters-button', 'style')],
    [Input('cluster-busy', 'data')],
    prevent_initial_call=False
)
def update_button(busy):
    if busy:
        return (
            'Computing...',
            {
                'margin': '10px',
                'padding': '10px 20px',
                'background-color': '#2e7d32',
                'color': 'white',
                'border': 'none',
                'border-radius': '5px',
                'cursor': 'not-allowed',
                'transition': 'background-color 0.2s',
                'opacity': 0.7
            }
        )
    else:
        return (
            'Compute clusters',
            {
                'margin': '10px',
                'padding': '10px 20px',
                'background-color': '#4CAF50',
                'color': 'white',
                'border': 'none',
                'border-radius': '5px',
                'cursor': 'pointer',
                'transition': 'background-color 0.2s',
                'opacity': 1
            }
        )

# Callback to overlay clusters/polygons/labels
@app.callback(
    Output('cluster-overlay', 'data'),
    Output('cluster-busy', 'data', allow_duplicate=True),
    [Input('compute-clusters-button', 'n_clicks')],
    [State('data-store', 'data'),
     State('num-clusters', 'value'),
     State('graph-3', 'relayoutData'),
     State('category-filter', 'value')],
    prevent_initial_call='initial_duplicate'
)
def overlay_clusters(n_clicks, data_store, num_clusters, relayoutData, selected_countries):
    import copy
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    
    print(f"Cluster callback: Triggered with {n_clicks} clicks")
    
    # Get current data from the store instead of global df
    if not data_store:
        print("Cluster callback: No data loaded")
        return {'polygons': [], 'annotations': []}, False
    
    # Convert store data to DataFrame
    df = pd.DataFrame(data_store)
    
    print(f"Cluster callback: Working with {len(df)} papers")
    
    if df.empty:
        print("Cluster callback: Empty DataFrame")
        return {'polygons': [], 'annotations': []}, False
    
    if not selected_countries:
        filtered_df = df.iloc[0:0]
    else:
        filtered_df = df[df['Country of Publication'].isin(selected_countries)]
    
    x_range = y_range = [None, None]
    if relayoutData:
        x_range = relayoutData.get('xaxis.range', relayoutData.get('xaxis.range[0]', [None, None]))
        y_range = relayoutData.get('yaxis.range', relayoutData.get('yaxis.range[0]', [None, None]))
        if isinstance(x_range, list) and len(x_range) == 2:
            pass
        elif 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
            x_range = [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]
        if 'yaxis.range[0]' in relayoutData and 'yaxis.range[1]' in relayoutData:
            y_range = [relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']]
    
    if x_range[0] is not None and x_range[1] is not None and y_range[0] is not None and y_range[1] is not None:
        mask = (
            (filtered_df['x'] >= x_range[0]) & 
            (filtered_df['x'] <= x_range[1]) & 
            (filtered_df['y'] >= y_range[0]) & 
            (filtered_df['y'] <= y_range[1])
        )
        visible_df = filtered_df[mask]
    else:
        visible_df = filtered_df
    
    overlay = {'polygons': [], 'annotations': []}
    
    if len(visible_df) >= num_clusters:
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        visible_embeds = visible_df[['x', 'y']].values
        visible_df['cluster'] = kmeans.fit_predict(visible_embeds)
        cluster_centers = kmeans.cluster_centers_
        nearest_titles = get_nearest_titles(visible_df, cluster_centers, n=10)
        llm_prompt = build_llm_prompt(nearest_titles)
        try:
            llm_response = get_azure_llm_summaries(llm_prompt)
            region_summaries = parse_llm_response(llm_response, len(cluster_centers))
        except Exception as e:
            print(f"LLM API call failed: {e}")
            region_summaries = ["Summary unavailable."] * len(cluster_centers)
        
        points = [Point(x, y) for x, y in cluster_centers]
        hull = MultiPoint(visible_df[['x', 'y']].values).convex_hull
        min_x, min_y = visible_df[['x', 'y']].min()
        max_x, max_y = visible_df[['x', 'y']].max()
        bounding_rect = box(min_x, min_y, max_x, max_y)
        regions = voronoi_diagram(MultiPoint(points), envelope=bounding_rect, edges=False)
        voronoi_regions = []
        
        for i, poly in enumerate(regions.geoms):
            clipped_poly = poly.intersection(hull)
            if clipped_poly.is_empty or not clipped_poly.is_valid:
                continue
            x, y = clipped_poly.exterior.xy
            clipped_points = np.column_stack((x, y))
            voronoi_regions.append({
                'region_id': i,
                'polygon': clipped_points.tolist(),
                'center': cluster_centers[i].tolist() if i < len(cluster_centers) else None
            })
        
        for i, region in enumerate(voronoi_regions):
            poly_points = region['polygon']
            overlay['polygons'].append({
                'x': [float(pt[0]) for pt in poly_points],
                'y': [float(pt[1]) for pt in poly_points]
            })
        
        def smart_wrap(text, width=27):
            words = text.split(' ')
            lines = []
            current_line = ''
            for word in words:
                if len(current_line) + len(word) + 1 > width:
                    lines.append(current_line)
                    current_line = word
                else:
                    if current_line:
                        current_line += ' ' + word
                    else:
                        current_line = word
            if current_line:
                lines.append(current_line)
            return '<br>'.join(lines)
        
        for i, region in enumerate(voronoi_regions):
            summary = region_summaries[i] if i < len(region_summaries) else "Summary unavailable."
            summary_clean = clean_summary(summary)
            centroid = region['center']
            label_text = smart_wrap(summary_clean)
            overlay['annotations'].append({
                'x': float(centroid[0]),
                'y': float(centroid[1]),
                'text': label_text
            })
    
    return overlay, False

# Callback to update the dots and overlay clusters/polygons/labels
@app.callback(
    Output("graph-3", "figure"),
    [Input('data-store', 'data'),
     Input("category-filter", "value"),
     Input('cluster-overlay', 'data'),
     Input('graph-3', 'clickData'),
     Input('clear-selection-store', 'data'),
     Input("show-region-labels", "value")],
    [State("graph-3", "figure")]
)
def update_dots(data_store, selected_countries, cluster_overlay, clickData, clear_trigger, show_region_labels, current_figure):
    
    # Check if data is available
    if not data_store:
        print("Plot callback: No data in store")
        # Return empty figure while loading
        return go.Figure(layout={
            'plot_bgcolor': '#2b2b2b',
            'paper_bgcolor': '#2b2b2b',
            'xaxis': dict(showgrid=False, zeroline=False, visible=False),
            'yaxis': dict(showgrid=False, zeroline=False, visible=False),
            'annotations': [{
                'text': 'Loading data...',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20, 'color': '#ffffff'},
                'x': 0.5,
                'y': 0.5
            }]
        })
    
    # Convert store data to DataFrame
    df = pd.DataFrame(data_store)
    
    if df.empty:
        print("Plot callback: Empty DataFrame")
        # Return empty figure if no data
        return go.Figure(layout={
            'plot_bgcolor': '#2b2b2b',
            'paper_bgcolor': '#2b2b2b',
            'xaxis': dict(showgrid=False, zeroline=False, visible=False),
            'yaxis': dict(showgrid=False, zeroline=False, visible=False),
            'annotations': [{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20, 'color': '#ffffff'},
                'x': 0.5,
                'y': 0.5
            }]
        })
    
    print(f"Plot callback: Received {len(df)} papers from store")
    
    # Robust filtering logic - show all papers if filter is empty or all countries selected
    available_countries = sorted(df['Country of Publication'].unique())
    if not selected_countries or set(selected_countries) == set(available_countries):
        # Show all papers if no filter or all countries selected
        filtered_df = df
        print(f"Plot callback: Displaying all {len(filtered_df)} papers")
    else:
        # Filter by selected countries
        filtered_df = df[df['Country of Publication'].isin(selected_countries)]
        print(f"Plot callback: Filtered to {len(filtered_df)} papers")
    
    # Limit to maximum 500 points for performance
    if len(filtered_df) > TARGET_RECORDS_PER_VIEW:
        filtered_df = filtered_df.head(TARGET_RECORDS_PER_VIEW)
        print(f"Plot callback: Limited to {len(filtered_df)} papers")
    
    # Ensure we have valid coordinates
    if 'x' not in filtered_df.columns or 'y' not in filtered_df.columns:
        print("Plot callback: Missing x or y coordinates")
        return go.Figure(layout={
            'plot_bgcolor': '#2b2b2b',
            'paper_bgcolor': '#2b2b2b',
            'xaxis': dict(showgrid=False, zeroline=False, visible=False),
            'yaxis': dict(showgrid=False, zeroline=False, visible=False),
            'annotations': [{
                'text': 'Invalid data format',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20, 'color': '#ffffff'},
                'x': 0.5,
                'y': 0.5
            }]
        })
    
    # Remove any rows with invalid coordinates
    filtered_df = filtered_df.dropna(subset=['x', 'y'])
    
    if filtered_df.empty:
        print("Plot callback: No valid coordinates after filtering")
        return go.Figure(layout={
            'plot_bgcolor': '#2b2b2b',
            'paper_bgcolor': '#2b2b2b',
            'xaxis': dict(showgrid=False, zeroline=False, visible=False),
            'yaxis': dict(showgrid=False, zeroline=False, visible=False),
            'annotations': [{
                'text': 'No valid data points',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20, 'color': '#ffffff'},
                'x': 0.5,
                'y': 0.5
            }]
        })
    
    fig = go.Figure()
    customdata = [[i] for i in filtered_df['index'].values]
    
    # Determine marker opacity
    opacities = [0.8] * len(filtered_df)
    ctx = dash.callback_context
    
    # If clear selection was triggered, reset opacities
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('clear-selection-store'):
        clickData = None
    
    if clickData and 'points' in clickData and clickData['points']:
        selected_index = clickData['points'][0]['pointIndex']
        opacities = [0.5] * len(filtered_df)
        if 0 <= selected_index < len(opacities):
            opacities[selected_index] = 1.0
    
    # Map colors for countries
    colors = [get_country_color(country) for country in filtered_df['Country of Publication']]
    
    fig.add_trace(go.Scatter(
        x=filtered_df['x'],
        y=filtered_df['y'],
        mode='markers',
        marker=dict(size=8, opacity=opacities, color=colors),
        customdata=customdata,
        hoverinfo='none',
        showlegend=False,
        visible=True,
        name='dot-trace'
    ))
    
    # Overlay clusters/polygons/labels if present
    if cluster_overlay and 'polygons' in cluster_overlay:
        for poly in cluster_overlay['polygons']:
            fig.add_trace(go.Scatter(
                x=poly['x'],
                y=poly['y'],
                mode='lines',
                line=dict(color='rgba(255, 255, 0, 0.7)', width=2),
                fill=None,
                showlegend=False,
                hoverinfo='skip',
                visible=True
            ))
    
    if cluster_overlay and 'annotations' in cluster_overlay:
        annotations = []
        show_labels = 'show' in show_region_labels if show_region_labels else False
        for ann in cluster_overlay['annotations']:
            annotations.append(dict(
                x=ann['x'],
                y=ann['y'],
                text=ann['text'],
                showarrow=False,
                font=dict(size=13, color='#cccccc', family='Arial'),
                bgcolor='rgba(0,0,0,0.4)',
                bordercolor='rgba(255,255,0,0.7)',
                borderwidth=1,
                opacity=1 if show_labels else 0
            ))
        fig.update_layout(annotations=annotations)
    
    # Use axis ranges from current_figure if present
    if current_figure and 'layout' in current_figure:
        xaxis = current_figure['layout'].get('xaxis', {})
        yaxis = current_figure['layout'].get('yaxis', {})
        x_range = xaxis.get('range', None)
        y_range = yaxis.get('range', None)
        if x_range and y_range and len(x_range) == 2 and len(y_range) == 2:
            fig.update_layout(xaxis_range=x_range, yaxis_range=y_range)
    
    fig.update_layout(
        dragmode='pan',
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        legend_title_text=' ',
        plot_bgcolor='#2b2b2b',
        paper_bgcolor='#2b2b2b',
        font=dict(family="Arial", size=12, color='#ffffff'),
        margin=dict(l=0, r=0, t=40, b=0),
        title_font=dict(size=20, color='#ffffff'),
        showlegend=False,
    )
    
    print(f"Plot callback: Updated plot with {len(filtered_df)} points")
    
    return fig

# Separate callback for interactive updates (clicks, filters, etc.)


# Display click data
@app.callback(
    Output('content-display-area', 'children'),
    Input('graph-3', 'clickData'),
    Input('clear-selection-store', 'data'),
    State('data-store', 'data')
)
def display_click_data(clickData, clear_trigger, data_store):
    ctx = dash.callback_context
    # If clear selection was triggered, clear the sidebar
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('clear-selection-store'):
        return 'Click on a point to see details.'
    
    if clickData is None or not data_store:
        return 'Click on a point to see details.'
    
    try:
        # Convert data_store back to DataFrame
        df = pd.DataFrame(data_store)
        if df.empty:
            return 'Click on a point to see details.'
        
        point = clickData["points"][0]
        if "customdata" in point and point["customdata"] is not None:
            point_index = point["customdata"][0]
            
            # Find the paper with this index
            paper_data = df[df['index'] == point_index]
            if paper_data.empty:
                return 'Click on a point to see details.'
            
            # Get the paper details
            paper = paper_data.iloc[0]
            title = paper.get('Title', 'No title available')
            summary = paper.get('Summary', 'No summary available')
            date = paper.get('Submitted Date', 'No date available')
            category = paper.get('Country of Publication', 'Unknown source')
            
            children = html.Div(
                style={
                    'padding': '10px',
                    'background-color': 'rgba(0, 31, 63, 0.85)',
                    'color': '#ffffff',
                    'border-radius': '5px',
                    'position': 'relative'
                },
                children=[
                    html.H4(title, style={'font-weight': 'bold', 'color': '#ffffff', 'font-size': '20px'}),
                    html.P(f"Date Submitted: {date}", style={'color': '#ffffff', 'margin-top': '5px'}),
                    html.P(f"Source: {category}", style={'color': '#ffffff', 'margin-top': '5px'}),
                    html.P(summary, style={'margin-top': '10px', 'color': '#ffffff'}),
                    html.A('Dismiss', id='dismiss-link', n_clicks=0, style={
                        'color': '#00BFFF', 'text-decoration': 'underline', 'cursor': 'pointer', 'font-size': '13px',
                        'background': 'none', 'border': 'none', 'padding': 0,
                        'position': 'absolute', 'right': '20px', 'bottom': '10px', 'zIndex': 10,
                        'display': 'inline-block',
                    }),
                ]
            )
            return children
        else:
            return 'Click on a point to see details.'
    except Exception as e:
        return f'Error: {e}'

# Helper functions
def get_nearest_titles(df, centroids, n=10):
    nearest_titles = []
    coords = df[['x', 'y']].values
    for centroid in centroids:
        dists = np.linalg.norm(coords - centroid, axis=1)
        nearest_indices = np.argsort(dists)[:n]
        titles = df.iloc[nearest_indices]['Title'].tolist()
        nearest_titles.append(titles)
    return nearest_titles

def build_llm_prompt(nearest_titles):
    prompt = (
        "For each group of paper titles below, provide a very brief (not a full sentence, just descriptive words) description of the main subject or theme that unites them and best differentiates them from the other groups. Do not use markdown, just plain text.\n\n"
    )
    for i, titles in enumerate(nearest_titles, 1):
        prompt += f"Cluster {i}:\n"
        for title in titles:
            prompt += f"- {title}\n"
        prompt += "\n"
    prompt += "\nReturn your answer as a numbered list, one description per cluster."
    return prompt

def clean_summary(summary):
    return re.sub(r'^\*\*?Cluster \d+\*\*?:\s*', '', summary).strip()

def get_azure_llm_summaries(prompt):
    url = "https://apigw.rand.org/openai/RAND/inference/deployments/gpt-4-v0613-base/chat/completions?api-version=2024-02-01"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": "a349cd5ebfcb45f59b2004e6e8b7d700"
    }
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3
    }
    response = requests.post(url, headers=headers, json=data, verify=certifi.where())
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def parse_llm_response(response_text, n_clusters):
    # Expecting a numbered list, e.g. "1. ...\n2. ...\n3. ..."
    pattern = r"\d+\.\s*(.+?)(?=\n\d+\.|$)"
    matches = re.findall(pattern, response_text, re.DOTALL)
    # If not enough matches, fill with a default
    while len(matches) < n_clusters:
        matches.append("No summary available.")
    return matches[:n_clusters]

# Note: Removed dismiss-link callbacks to avoid circular dependency issues
# The dismiss functionality is handled directly in the display_click_data callback

if __name__ == "__main__":
    app.run(debug=True)