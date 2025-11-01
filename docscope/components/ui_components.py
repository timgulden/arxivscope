"""
UI components for the DocScope application.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import List


def create_header() -> html.Div:
    """Create the application header."""
    return html.Div([
        html.H1("DocScope: ArXiv Paper Explorer", 
                style={'textAlign': 'center', 'color': 'white', 'marginBottom': '20px'}),
        html.P("Interactive visualization of ArXiv papers using UMAP embeddings",
               style={'textAlign': 'center', 'color': 'lightgray', 'marginBottom': '30px'})
    ], style={'backgroundColor': '#2c3e50', 'padding': '20px', 'borderRadius': '10px'})


def create_controls(available_countries: List[str]) -> html.Div:
    """Create the control panel."""
    return html.Div([
        # Semantic Search Section
        html.Div([
            html.H5("Semantic Search", style={'color': '#ffffff', 'marginBottom': '10px'}),
            html.Div([
                dcc.Input(
                    id='search-text',
                    type='text',
                    placeholder='Enter search terms (e.g., "machine learning", "computer vision")',
                    style={'width': '300px', 'marginRight': '10px'}
                ),
                html.Button(
                    'Search',
                    id='search-button',
                    n_clicks=0,
                    style={'backgroundColor': '#007bff', 'color': 'white', 'border': 'none', 'padding': '8px 16px', 'borderRadius': '4px'}
                ),
                html.Button(
                    'Clear',
                    id='clear-search-button',
                    n_clicks=0,
                    style={'backgroundColor': '#6c757d', 'color': 'white', 'border': 'none', 'padding': '8px 16px', 'borderRadius': '4px', 'marginLeft': '5px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
            html.Div([
                html.Label("Similarity Threshold:", style={'color': '#ffffff', 'marginRight': '10px'}),
                dcc.Slider(
                    id='similarity-threshold',
                    min=0.0,
                    max=1.0,
                    step=0.1,
                    value=0.5,
                    marks={0.0: '0.0', 0.5: '0.5', 1.0: '1.0'},
                    tooltip={'placement': 'bottom', 'always_visible': True}
                )
            ], style={'marginBottom': '15px'})
        ], style={'backgroundColor': '#34495e', 'padding': '15px', 'borderRadius': '5px', 'marginBottom': '20px'}),
        
        # Clustering Controls
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
        
        html.Div([
            dcc.Checklist(
                id='show-clusters',
                options=[{'label': 'Show Clusters', 'value': 'show'}],
                value=['show'],
                style={'color': '#fff', 'margin': '10px'}
            )
        ], style={'display': 'flex', 'align-items': 'center'}),
        
        # Country Filter
        html.Div([
            html.Label("Countries:", style={'fontWeight': 'bold', 'color': '#000000'}),
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': country, 'value': country} for country in available_countries],
                value=available_countries,
                multi=True,
                placeholder="Select countries..."
            )
        ], style={'marginBottom': '20px'}),

        # Year Range Slider
        html.Div([
            html.Label("Publication Year Range:", style={'fontWeight': 'bold', 'color': '#000000', 'marginBottom': '5px'}),
            html.Div(id='year-range-label', style={'color': '#333', 'marginBottom': '5px'}),
            dcc.RangeSlider(
                id='year-range-slider',
                min=1950,
                max=2025,
                step=1,
                value=[2000, 2025],
                marks={year: str(year) for year in range(1950, 2026, 5)},
                tooltip={'placement': 'bottom', 'always_visible': False}
            )
        ], style={'marginBottom': '20px'}),
        

    ])


def create_status_indicator() -> html.Div:
    """Create the status indicator."""
    return html.Div(
        id='status-indicator',
        children='',
        style={
            'margin': '10px',
            'padding': '10px 20px',
            'background-color': '#007bff',  # Use blue like search button for better contrast
            'color': 'white',
            'border-radius': '5px',
            'font-weight': 'bold',
            'border': 'none',
            'transition': 'background-color 0.2s',
            'opacity': 1
        }
    )


def create_main_graph() -> html.Div:
    """Create the main scatter plot graph."""
    return dcc.Graph(
        id="graph-3",
        style={'height': 'calc(100% - 60px)'},
        config={
            'displayModeBar': True, 
            'scrollZoom': True,
            'staticPlot': False,
            'responsive': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],  # Keep pan2d and zoom2d for better interaction
            'editable': False,
            'showEditInChartStudio': False,
            'showSendToCloud': False,
            'showTips': False,
            'showAxisDragHandles': False,
            'showAxisRangeEntryBoxes': False
        },
        figure={
            'data': [],
            'layout': {
                'plot_bgcolor': '#2b2b2b',
                'paper_bgcolor': '#2b2b2b',
                'font': {'color': '#ffffff'},
                'xaxis': {
                    'showgrid': False,
                    'showline': False,
                    'showticklabels': False,
                    'zeroline': False,
                    'visible': True
                },
                'yaxis': {
                    'showgrid': False,
                    'showline': False,
                    'showticklabels': False,
                    'zeroline': False,
                    'visible': True
                },
                'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
                'showlegend': False,
                'autosize': True,
                'hovermode': 'closest',
                'dragmode': 'pan',
                'clickmode': 'event+select'  # Enable both click and select events
            }
        }
    )


def create_metadata_panel() -> html.Div:
    """Create the metadata display panel."""
    return html.Div([
        dbc.Card([
            dbc.CardHeader("Paper Details", style={'backgroundColor': '#34495e', 'color': 'white'}),
            dbc.CardBody([
                html.Div(id="click-data-display", children="Click on a point to view details")
            ])
        ])
    ], style={'marginBottom': '20px'})


def create_data_store() -> dcc.Store:
    """Create the data store component."""
    return dcc.Store(id='data-store', storage_type='memory')


def create_clustering_store() -> dcc.Store:
    """Create the clustering store component."""
    return dcc.Store(id='clustering-store', storage_type='memory')





def create_paper_details_store() -> dcc.Store:
    """Create the paper details store component for lazy loading."""
    # REMOVED: paper-details-store - no longer needed since we use cached data
    return None


def create_loading_spinner() -> html.Div:
    """Create the loading spinner."""
    return html.Div([
        dbc.Spinner(
            html.Div(id="loading-output"),
            color="primary"
        )
    ]) 