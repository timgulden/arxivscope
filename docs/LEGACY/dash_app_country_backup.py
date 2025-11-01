import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import umap
import dash_bootstrap_components as dbc  # Import the Bootstrap components
import numpy as np
from scipy.spatial import Voronoi
from sklearn.cluster import DBSCAN, KMeans
import plotly.graph_objects as go
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, Point, MultiPolygon, LineString, box
from shapely.ops import unary_union
import math
from shapely.geometry import MultiPoint
from shapely.ops import voronoi_diagram
import requests
import re
import certifi
from dash.dependencies import ALL
from dash.exceptions import PreventUpdate
import dash

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

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Load and preprocess the DataFrame
df = pd.read_pickle("final_df_country.pkl")[
    ['Title', 'Summary', 'Submitted Date', 'category', 'Link', 'Country2', 'title_Embedding']
]



df.rename(columns={'Country2': 'Country of Publication'}, inplace=True)
df['Country of Publication'] = df['Country of Publication'].str.replace("'", "", regex=False)


reducer = umap.UMAP(random_state=42)
embeddings = df['title_Embedding'].tolist()
umap_embeds = reducer.fit_transform(embeddings)
df['x'] = umap_embeds[:, 0]
df['y'] = umap_embeds[:, 1]
df.reset_index(drop=False, inplace=True)  

# Use K-means clustering for cluster centers
print("Performing K-means clustering...")
n_clusters = 30
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
df['cluster'] = kmeans.fit_predict(umap_embeds)
cluster_centers = kmeans.cluster_centers_
print(f"K-means found {len(cluster_centers)} cluster centers")

# Compute convex hull of all data points
hull = MultiPoint(df[['x', 'y']].values).convex_hull

# Compute bounding rectangle
min_x, min_y = df[['x', 'y']].min()
max_x, max_y = df[['x', 'y']].max()
bounding_rect = box(min_x, min_y, max_x, max_y)

# Prepare points as Shapely Points
points = [Point(x, y) for x, y in cluster_centers]

# Generate Voronoi diagram using bounding rectangle
print("Generating Voronoi diagram using shapely.ops.voronoi_diagram with bounding rectangle...")
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
        'polygon': clipped_points,
        'center': cluster_centers[i] if i < len(cluster_centers) else None
    })
print(f"Created {len(voronoi_regions)} Voronoi regions using shapely.ops.voronoi_diagram with convex hull clipping")

color_sequence = px.colors.qualitative.Plotly  


countries = sorted(df['Country of Publication'].unique())

# Define custom color mapping
country_color_map = {}
for country in countries:
    if country == 'United States':
        country_color_map[country] = '#1E90FF'  # Dodger Blue
    elif country == 'China':
        country_color_map[country] = 'red'
    else:
        country_color_map[country] = 'green'


fig = px.scatter(
    df,
    x='x',
    y='y',
    color='Country of Publication',
    labels={'x': '', 'y': '', 'Country of Publication': 'Country of Publication'},
    title='-----',
    hover_data=['Title', 'Summary', 'Submitted Date', 'Link'],
    color_discrete_map=country_color_map,
    custom_data=['index']
)

fig.update_traces(
    marker=dict(
        size=10,  
        opacity=0.5,  
        line=dict(
            width=1,
            color='#333333'  
        ),
        symbol="circle-open" 
    ),
    selector=dict(mode='markers')
)

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
        dcc.Store(id='cluster-busy', data=False),  # Store for busy state
        dcc.Store(id='cluster-overlay', data=None),  # Store for cluster overlays
        dcc.Store(id='clear-selection-store', data=0),
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
                            style={'flex': '1 1 auto', 'overflowY': 'auto'}
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
                                        dbc.Checklist(
                                            id='category-filter',
                                            options=[
                                                {
                                                    'label': html.Span([
                                                        html.Span(style={
                                                            'display': 'inline-block',
                                                            'width': '12px',
                                                            'height': '12px',
                                                            'background-color': country_color_map[cat],
                                                            'margin-right': '10px'
                                                        }),
                                                        cat
                                                    ]),
                                                    'value': cat
                                                } for cat in countries
                                            ],
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
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.A('Dismiss', id='dismiss-link', n_clicks=0, style={'display': 'none'}),
                    ],
                ),
            ],
        ),
    ],
)

# --- Busy state management ---
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
     Output('compute-clusters-button', 'style'),
     Output('compute-clusters-button', 'disabled')],
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
                'background-color': '#2e7d32',  # darker green
                'color': 'white',
                'border': 'none',
                'border-radius': '5px',
                'cursor': 'not-allowed',
                'transition': 'background-color 0.2s',
                'opacity': 0.7
            },
            True
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
            },
            False
        )

# --- End busy state management ---

# 1. Callback to overlay clusters/polygons/labels and store in cluster-overlay
@app.callback(
    Output('cluster-overlay', 'data'),
    Output('cluster-busy', 'data', allow_duplicate=True),
    [Input('compute-clusters-button', 'n_clicks')],
    [State('graph-3', 'figure'),
     State('num-clusters', 'value'),
     State('graph-3', 'relayoutData'),
     State('category-filter', 'value')],
    prevent_initial_call='initial_duplicate'
)
def overlay_clusters(n_clicks, current_figure, num_clusters, relayoutData, selected_countries):
    import copy
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
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

# 2. Callback to update the dots and overlay clusters/polygons/labels
@app.callback(
    Output("graph-3", "figure"),
    [Input("category-filter", "value"),
     Input('cluster-overlay', 'data'),
     Input('graph-3', 'clickData'),
     Input('clear-selection-store', 'data')],
    [State("graph-3", "figure")]
)
def update_dots(selected_countries, cluster_overlay, clickData, clear_trigger, current_figure):
    if not selected_countries:
        filtered_df = df.iloc[0:0]
    else:
        filtered_df = df[df['Country of Publication'].isin(selected_countries)]
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
    fig.add_trace(go.Scatter(
        x=filtered_df['x'],
        y=filtered_df['y'],
        mode='markers',
        marker=dict(size=8, opacity=opacities, color=filtered_df['Country of Publication'].map(country_color_map)),
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
                opacity=1
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
        autosize=True,
        clickmode='event+select',
    )
    return fig

# In the toggle callback, update annotation opacity
@app.callback(
    Output("graph-3", "figure", allow_duplicate=True),
    [Input("show-region-labels", "value")],
    [State("graph-3", "figure")],
    prevent_initial_call=True
)
def toggle_region_labels(show_region_labels, fig):
    show = 'show' in show_region_labels if show_region_labels else False
    if 'annotations' in fig['layout']:
        for ann in fig['layout']['annotations']:
            ann['opacity'] = 1 if show else 0
    return fig

fig.update_xaxes(
    showgrid=False,
    zeroline=False,
    visible=False,
    constrain="domain"
)

fig.update_yaxes(
    showgrid=False,
    zeroline=False,
    visible=False,
    constrain="domain"
)



@app.callback(
    Output('content-display-area', 'children'),
    Input('graph-3', 'clickData'),
    Input('clear-selection-store', 'data')
)
def display_click_data(clickData, clear_trigger):
    ctx = dash.callback_context
    # If clear selection was triggered, clear the sidebar
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('clear-selection-store'):
        return 'Click on a point to see details.'
    if clickData is None:
        return 'Click on a point to see details.'
    try:
        point = clickData["points"][0]
        if "customdata" in point and point["customdata"] is not None:
            point_index = point["customdata"][0]
            title = df.loc[df['index'] == point_index, 'Title'].values[0]
            summary = df.loc[df['index'] == point_index, 'Summary'].values[0]
            link = df.loc[df['index'] == point_index, 'Link'].values[0]
            date = df.loc[df['index'] == point_index, 'Submitted Date'].values[0]
            category = df.loc[df['index'] == point_index, 'Country of Publication'].values[0]
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
                    html.P(summary, style={'margin-top': '10px', 'color': '#ffffff'}),
                    html.Div([
                        html.A('Read more', href=link, target='_blank', style={
                            'color': '#00BFFF', 'text-decoration': 'underline', 'cursor': 'pointer', 'font-size': '13px', 'background': 'none', 'border': 'none', 'padding': 0,
                            'margin-right': 'auto'
                        }),
                    ], style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'space-between', 'align-items': 'center', 'margin-top': '10px'}),
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
        "For each group of paper titles below, provide a very brief (not a full sentence, just desriptive words) description of the main subject or theme that unites them and best differentiates them from the other groups.  Do not use markdown, just plain text.  \n\n"
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

# Callback to increment clear-selection-store when Dismiss is clicked
@app.callback(
    Output('clear-selection-store', 'data'),
    Input('dismiss-link', 'n_clicks'),
    State('clear-selection-store', 'data'),
    prevent_initial_call=True
)
def trigger_clear_selection_dismiss(n_clicks, current):
    if n_clicks:
        return (current or 0) + 1
    return dash.no_update

@app.callback(
    Output('dismiss-link', 'style'),
    Input('graph-3', 'clickData'),
)
def update_dismiss_link_style(clickData):
    if clickData and 'points' in clickData and clickData['points']:
        # Popup is visible: blue, lower right
        return {
            'color': '#00BFFF', 'text-decoration': 'underline', 'cursor': 'pointer', 'font-size': '13px',
            'background': 'none', 'border': 'none', 'padding': 0,
            'position': 'absolute', 'right': '20px', 'bottom': '10px', 'zIndex': 10,
            'display': 'inline-block',
        }
    else:
        # Popup is not visible: completely hidden
        return {
            'display': 'none'
        }

if __name__ == "__main__":
    app.run(debug=True)
    #app.run_server(host="0.0.0.0", port=8050, debug=False)