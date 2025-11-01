"""
Main DocScope application.
"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import os
from dotenv import load_dotenv

# Load environment variables from .env.local if it exists
# Use absolute path to ensure it works regardless of current working directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
print(f"🔍 DEBUG - Loading environment from: {env_path}")
print(f"🔍 DEBUG - File exists: {os.path.exists(env_path)}")
load_dotenv(env_path)
print(f"🔍 DEBUG - After load_dotenv - USE_NEW_CALLBACKS: {os.getenv('USE_NEW_CALLBACKS', 'NOT_LOADED')}")

from .components.ui_components import (
    create_header, create_controls, create_status_indicator,
    create_main_graph, create_metadata_panel, create_data_store,
    create_clustering_store, create_loading_spinner
)

# Import the new orchestrated callback system
from .components.callbacks_orchestrated import register_orchestrated_callbacks

from .components.data_service import get_unique_sources
from .config.settings import TARGET_RECORDS_PER_VIEW


def create_app():
    """Create and configure the Dash application."""
    
    # Initialize the app
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )
    
    # Add critical CSS to eliminate white flash
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                /* Critical CSS to eliminate white flash */
                html, body, #react-entry-point {
                    background-color: #000 !important;
                    color: #fff !important;
                    margin: 0;
                    padding: 0;
                }
                .dash-app-content {
                    background-color: #000 !important;
                    color: #fff !important;
                }
                
                /* Target Plotly graph containers specifically */
                .js-plotly-plot,
                .plotly,
                .plotly-graph-div,
                /* Removed problematic background-color rules that were hiding scatter plot points */
                
                /* Target the specific graph container */
                #graph-3,
                #graph-3 .js-plotly-plot,
                #graph-3 .plotly,
                #graph-3 .plotly-graph-div,
                #graph-3 .plot-container,
                #graph-3 .svg-container {
                    background-color: #2b2b2b !important;
                    color: #fff !important;
                }
                
                /* Target any canvas elements */
                canvas {
                    background-color: #2b2b2b !important;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    # Get initial countries (will be updated when data loads)
    initial_countries = ['United States', 'China', 'Rest of the World']
    
    # Create the layout
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
            dcc.Location(id='url', refresh=False),
            dcc.Store(id='cluster-busy', data=False),
            dcc.Store(id='cluster-overlay', data=None),
            dcc.Store(id='clear-selection-store', data=0),
                    dcc.Store(id='data-store'),  # Single source of truth for data
        dcc.Store(id='data-metadata', data={'total_count': 0}),  # Store for data metadata like total count
        dcc.Store(id='target-records-debounce', data=None),  # For debouncing target records input
            dcc.Interval(id='target-records-interval', interval=500, disabled=True),  # 500ms debounce interval
            dcc.Interval(id='zoom-loading-interval', interval=100, disabled=True),  # 100ms interval for background zoom loading
            dcc.Store(id='available-sources', data=[]),
            dcc.Store(id='selected-sources', data=[]),
            dcc.Store(id='source-filter-trigger', data=0),  # Trigger for data refresh when sources change
            dcc.Store(id='filter-trigger', data={'triggered': False, 'timestamp': 0}),  # Trigger for visualization when filters change
            dcc.Store(id='zoom-trigger', data=0),  # Trigger for data refresh when zoom changes
            dcc.Store(id='zoom-data-updated', data=0),  # Trigger scatter plot update when zoom data is loaded
            dcc.Store(id='app-ready', data=True),
            dcc.Store(id='scatter-initial-load', data=True),
            dcc.Store(id='view-ranges-store', data=None),  # Store for axis ranges
            dcc.Store(id='force-autorange', data=True),  # Force autorange on startup
            dcc.Store(id='last-search-text', data=None),  # Persist last confirmed semantic search text
            dcc.Store(id='current-view-state', data={
                'bbox': None,
                'year_range': [2000, 2025],
                'search_text': None,
                'similarity_threshold': 0.5,
                'target_records': 5000
            }),  # Central store for current view state
            # Enrichment stores
            dcc.Store(id='enrichment-tables', data={}),  # Available enrichment tables for selected source
            dcc.Store(id='enrichment-fields', data={}),  # Available fields for selected table
            dcc.Store(id='enrichment-state', data={
                'source': None,
                'table': None,
                'field': None,
                'active': False
            }),  # Current enrichment configuration
            dcc.Store(id='clear-enrichment-trigger', data=0),  # Trigger for clearing enrichment dropdowns
            dcc.Store(id='universe-constraints', data=None),  # Store for universe constraint SQL filters
            dcc.Store(id='constraint-state-store', data={}),  # Store for current constraint state
            # REMOVED: paper-details-store - no longer needed since we use cached data
            # Remove the separate dcc.Loading wrapper at the top
            # dcc.Loading(
            #     id='status-indicator-loading',
            #     type='default',
            #     children=[ ... ]
            # ),
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
                                # Status indicator and Fetch control grouped together
                                html.Div([
                                    # Status indicator in the upper left, with loading spinner
                                    dcc.Loading(
                                        id='status-indicator-loading',
                                        type='default',
                                        children=[
                                            html.Button(
                                                id='status-indicator',
                                                children='',
                                                style={
                                                    'display': 'inline-block',
                                                    'width': '120px',
                                                    'margin': '10px',
                                                    'margin-right': '10px',
                                                    'padding': '8px 12px',
                                                    'background-color': '#4CAF50',
                                                    'color': 'white',
                                                    'border': 'none',
                                                    'border-radius': '5px',
                                                    'font-weight': 'bold',
                                                    'cursor': 'default',
                                                }
                                            )
                                        ]
                                    ),
                                    # Fetch control (renamed from Max Dots)
                                    html.Div([
                                        html.Label(
                                            "Fetch:",
                                            style={'color': '#ffffff', 'font-size': '0.9em', 'margin-bottom': '2px'}
                                        ),
                                        dcc.Input(
                                            id='target-records-per-view',
                                            type='number',
                                            min=100,
                                            max=50000,
                                            step=1,
                                            value=TARGET_RECORDS_PER_VIEW,  # Use configurable default
                                            style={'width': '80px'}
                                        ),
                                        html.Div(
                                            id='target-records-loading',
                                            style={'display': 'none', 'margin-left': '5px'},
                                            children="⏳"
                                        )
                                    ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center', 'margin': '10px'})
                                ], style={'display': 'flex', 'align-items': 'center'}),
                                
                                # Clustering controls grouped together
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
                                    # Clusters control (renamed from Number of Clusters)
                                    html.Div([
                                        html.Label(
                                            "Clusters:",
                                            style={'color': '#ffffff', 'font-size': '0.9em', 'margin-bottom': '2px'}
                                        ),
                                        dcc.Input(
                                            id='num-clusters',
                                            type='number',
                                            min=1,
                                            max=999,
                                            step=1,
                                            value=30,
                                            style={'width': '80px'}
                                        )
                                    ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center', 'margin': '10px'}),
                                    # Show clusters checkbox
                                    html.Div([
                                        dcc.Checklist(
                                            id='show-clusters',
                                            options=[{'label': 'Show Clusters', 'value': 'show'}],
                                            value=['show'],
                                            style={'color': '#fff', 'margin': '10px'}
                                        )
                                    ], style={'display': 'flex', 'align-items': 'center'})
                                ], style={'display': 'flex', 'align-items': 'center'}),
                            ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px', 'justify-content': 'space-between'}),
                            # Graph
                            create_main_graph(),
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
                                        children=[]
                                    ),
                                    # Source Filter Section with Set Universe and Enrichment buttons
                                    html.Div([
                                        html.Label("Source Filter:", style={'fontWeight': 'bold', 'color': '#000000', 'marginBottom': '5px', 'fontSize': '0.9em'}),
                                        html.Div([
                                            html.Div(
                                                id='source-filter',
                                                children=[],
                                                style={'flex': '1', 'marginRight': '10px'}
                                            ),
                                            html.Div([
                                                html.Button(
                                                    'Set Universe',
                                                    id='set-universe-button',
                                                    n_clicks=0,
                                                    style={
                                                        'padding': '4px 8px',
                                                        'background-color': '#4CAF50',
                                                        'color': 'white',
                                                        'border': 'none',
                                                        'border-radius': '3px',
                                                        'cursor': 'pointer',
                                                        'transition': 'background-color 0.2s',
                                                        'fontSize': '0.8em',
                                                        'height': 'fit-content',
                                                        'whiteSpace': 'nowrap'
                                                    }
                                                ),
                                                html.Button(
                                                    'Enrichment',
                                                    id='open-enrichment-modal',
                                                    n_clicks=0,
                                                    style={
                                                        'padding': '4px 8px',
                                                        'background-color': '#2196F3',
                                                        'color': 'white',
                                                        'border': 'none',
                                                        'border-radius': '3px',
                                                        'cursor': 'pointer',
                                                        'transition': 'background-color 0.2s',
                                                        'fontSize': '0.8em',
                                                        'height': 'fit-content',
                                                        'whiteSpace': 'nowrap'
                                                    }
                                                )
                                            ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'flex-end', 'gap': '5px'})
                                        ], style={'display': 'flex', 'align-items': 'flex-start', 'width': '100%'})
                                    ], style={'marginBottom': '20px', 'width': '100%'}),
                                    # Enrichment Modal
                                    dbc.Modal([
                                        dbc.ModalHeader("Enrichment Configuration"),
                                        dbc.ModalBody([
                                            # Enrichment source dropdown
                                            html.Div([
                                                html.Label("Source:", style={'fontSize': '0.9em', 'color': '#333333', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                                                dcc.Dropdown(
                                                    id='enrichment-source-dropdown',
                                                    placeholder='Select source...',
                                                    style={'width': '100%', 'color': '#000000', 'marginBottom': '15px'},
                                                    clearable=True
                                                )
                                            ]),
                                            # Enrichment table dropdown
                                            html.Div([
                                                html.Label("Table:", style={'fontSize': '0.9em', 'color': '#333333', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                                                dcc.Dropdown(
                                                    id='enrichment-table-dropdown',
                                                    placeholder='Select table...',
                                                    style={'width': '100%', 'color': '#000000', 'marginBottom': '15px'},
                                                    clearable=True,
                                                    disabled=True
                                                )
                                            ]),
                                            # Enrichment field dropdown
                                            html.Div([
                                                html.Label("Field:", style={'fontSize': '0.9em', 'color': '#333333', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                                                dcc.Dropdown(
                                                    id='enrichment-field-dropdown',
                                                    placeholder='Select field...',
                                                    style={'width': '100%', 'color': '#000000', 'marginBottom': '20px'},
                                                    clearable=True,
                                                    disabled=True
                                                )
                                            ]),
                                            # Apply and Clear buttons
                                            html.Div([
                                                html.Button(
                                                    'Apply',
                                                    id='apply-enrichment-button',
                                                    n_clicks=0,
                                                    style={
                                                        'padding': '8px 20px',
                                                        'background-color': '#2196F3',
                                                        'color': 'white',
                                                        'border': 'none',
                                                        'border-radius': '5px',
                                                        'cursor': 'pointer',
                                                        'transition': 'background-color 0.2s',
                                                        'margin-right': '10px'
                                                    },
                                                    disabled=True
                                                ),
                                                html.Button(
                                                    'Clear',
                                                    id='clear-enrichment-button',
                                                    n_clicks=0,
                                                    style={
                                                        'padding': '8px 20px',
                                                        'background-color': '#f44336',
                                                        'color': 'white',
                                                        'border': 'none',
                                                        'border-radius': '5px',
                                                        'cursor': 'pointer',
                                                        'transition': 'background-color 0.2s'
                                                    },
                                                    disabled=True
                                                )
                                            ], style={'display': 'flex', 'justify-content': 'flex-start'})
                                        ]),
                                        dbc.ModalFooter([
                                            html.Button(
                                                'Close',
                                                id='close-enrichment-modal',
                                                n_clicks=0,
                                                style={
                                                    'padding': '8px 20px',
                                                    'background-color': '#6c757d',
                                                    'color': 'white',
                                                    'border': 'none',
                                                    'border-radius': '5px',
                                                    'cursor': 'pointer',
                                                    'transition': 'background-color 0.2s'
                                                }
                                            )
                                        ])
                                    ], id='enrichment-modal', is_open=False, size='md'),
                                    # Year Range Slider Section (added below country filter)
                                    html.Div([
                                        html.Label("Publication Year Range:", style={'fontWeight': 'bold', 'color': '#000000', 'marginBottom': '5px'}),
                                        html.Div(id='year-range-label', style={'color': '#333', 'marginBottom': '5px'}),
                                        dcc.RangeSlider(
                                            id='year-range-slider',
                                            min=1950,
                                            max=2025,
                                            step=1,
                                            value=[2000, 2025],
                                            marks={year: str(year) for year in range(1950, 2026, 10)},
                                            tooltip={
                                                'placement': 'top',
                                                'always_visible': True,
                                                'style': {'width': '60px', 'fontSize': '14px', 'textAlign': 'center'}
                                            }
                                        )
                                    ], style={'marginBottom': '20px', 'width': '100%'}),
                                    # Semantic Search Section
                                    html.Div([
                                        html.H6("Semantic Search", style={'marginBottom': '10px', 'color': '#333'}),
                                        # Similarity Threshold Slider (added above search text input)
                                        html.Div([
                                            html.Label("Similarity Threshold:", style={'color': '#333', 'marginRight': '10px', 'fontWeight': 'bold'}),
                                            dcc.Slider(
                                                id='similarity-threshold',
                                                min=0.0,
                                                max=1.0,
                                                step=0.1,
                                                value=0.5,
                                                marks={0.0: '0.0', 0.5: '0.5', 1.0: '1.0'},
                                                tooltip={'placement': 'bottom', 'always_visible': True}
                                            )
                                        ], style={'marginBottom': '15px'}),
                                        html.Div([
                                            html.Label("Search Text:", style={'display': 'block', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                                            dcc.Textarea(
                                                id='search-text',
                                                placeholder='Enter search terms (e.g., "machine learning", "computer vision") or paste long text...',
                                                style={
                                                    'width': '100%',
                                                    'minHeight': '80px',
                                                    'resize': 'vertical',
                                                    'border': '1px solid #ccc',
                                                    'borderRadius': '4px',
                                                    'padding': '8px',
                                                    'fontSize': '14px',
                                                    'fontFamily': 'monospace'
                                                },
                                                value=''
                                            )
                                        ], style={'marginBottom': '10px'}),
                                        html.Div([
                                            html.Button(
                                                'Search',
                                                id='search-button',
                                                n_clicks=0,
                                                style={
                                                    'backgroundColor': '#007bff',
                                                    'color': 'white',
                                                    'border': 'none',
                                                    'padding': '8px 16px',
                                                    'borderRadius': '4px',
                                                    'marginRight': '5px',
                                                    'cursor': 'pointer'
                                                }
                                            ),
                                            html.Button(
                                                'Clear',
                                                id='clear-search-button',
                                                style={
                                                    'backgroundColor': '#6c757d',
                                                    'color': 'white',
                                                    'border': 'none',
                                                    'padding': '8px 16px',
                                                    'borderRadius': '4px',
                                                    'cursor': 'pointer'
                                                }
                                            )
                                        ], style={'textAlign': 'center'})
                                    ], style={
                                        'borderTop': '1px solid #ddd',
                                        'paddingTop': '15px',
                                        'marginTop': '15px'
                                    })
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            # Universe Constraint Modal (using html.Div instead of dcc.Modal)
            html.Div(
                id='universe-constraint-modal',
                children=[
                    html.Div([
                        html.H3("Set Universe Constraint", style={'color': '#333', 'marginBottom': '20px'}),
                        html.P(
                            "Enter a SQL WHERE clause to constrain the universe of papers. This constraint will be applied to all queries.",
                            style={'color': '#666', 'marginBottom': '15px'}
                        ),
                        # Natural Language Input Section
                        html.Div([
                            html.Label("Natural Language Request:", style={'color': '#333', 'fontWeight': 'bold', 'marginBottom': '5px'}),
                            html.P(
                                "Describe what papers you want to see in plain English:",
                                style={'color': '#666', 'fontSize': '12px', 'marginBottom': '8px'}
                            ),
                            dcc.Textarea(
                                id='natural-language-input',
                                placeholder='e.g., "Show me OpenAlex papers from US and China" or "RAND documents with type = RR"',
                                style={
                                    'width': '100%',
                                    'minHeight': '60px',
                                    'resize': 'vertical',
                                    'border': '1px solid #ccc',
                                    'borderRadius': '4px',
                                    'padding': '8px',
                                    'fontSize': '14px',
                                    'fontFamily': 'monospace',
                                    'marginBottom': '10px'
                                }
                            ),
                                                                                                        html.Div([
                                        html.Button(
                                            'Generate SQL',
                                            id='generate-sql-button',
                                            n_clicks=0,
                                            style={
                                                'backgroundColor': '#007bff',
                                                'color': 'white',
                                                'border': 'none',
                                                'padding': '8px 16px',
                                                'borderRadius': '4px',
                                                'marginBottom': '10px',
                                                'cursor': 'pointer',
                                                'marginRight': '10px'
                                            }
                                        ),
                                        html.Button(
                                            '📋 View Schema',
                                            id='view-schema-button',
                                            n_clicks=0,
                                            style={
                                                'backgroundColor': '#6f42c1',
                                                'color': 'white',
                                                'border': 'none',
                                                'padding': '8px 16px',
                                                'borderRadius': '4px',
                                                'marginBottom': '10px',
                                                'cursor': 'pointer'
                                            }
                                        )
                                    ], style={'display': 'flex', 'gap': '10px'}),
                                        # Status display for generation
                                        html.Div(id='generation-status', style={'marginBottom': '15px'}),
                        ], style={'marginBottom': '20px'}),
                        
                        # Example query above the input
                        html.Div([
                            html.Label("Example:", style={'color': '#333', 'fontWeight': 'bold', 'marginBottom': '5px'}),
                            html.Code(
                                "doctrove_source = 'randpub' AND randpub_publication_type = 'RR'",
                                style={
                                    'display': 'block',
                                    'background': '#f8f9fa',
                                    'padding': '10px',
                                    'borderRadius': '4px',
                                    'fontFamily': 'monospace',
                                    'fontSize': '12px',
                                    'color': '#333',
                                    'marginBottom': '15px'
                                }
                            )
                        ]),
                        
                        # Schema display area
                        html.Div(id='schema-display', style={'marginBottom': '20px'}),
                        dcc.Textarea(
                            id='universe-constraint-input',
                            placeholder='Enter SQL WHERE clause (e.g., doctrove_source = \'openalex\' AND (openalex_country_uschina = \'United States\' OR openalex_country_uschina = \'China\'))',
                            style={
                                'width': '100%',
                                'minHeight': '80px',
                                'resize': 'vertical',
                                'border': '1px solid #ccc',
                                'borderRadius': '4px',
                                'padding': '8px',
                                'fontSize': '14px',
                                'fontFamily': 'monospace',
                                'marginBottom': '20px'
                            }
                        ),
                        # Test results display
                        html.Div(id='test-results', style={'marginBottom': '20px'}),
                        # Note about testing
                        html.Div([
                            html.P("💡 Tip: Use 'Test Query' to verify your SQL works before applying it", 
                                   style={'color': '#666', 'fontSize': '12px', 'fontStyle': 'italic', 'textAlign': 'center'})
                        ], style={'marginBottom': '15px'}),
                        html.Div([
                            html.Button(
                                'Test Query',
                                id='test-query-button',
                                n_clicks=0,
                                style={
                                    'backgroundColor': '#17a2b8',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '10px 20px',
                                    'borderRadius': '4px',
                                    'marginRight': '10px',
                                    'cursor': 'pointer'
                                }
                            ),
                            html.Button(
                                'Apply Constraint',
                                id='apply-universe-constraint-button',
                                n_clicks=0,
                                style={
                                    'backgroundColor': '#28a745',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '10px 20px',
                                    'borderRadius': '4px',
                                    'marginRight': '10px',
                                    'cursor': 'pointer'
                                }
                            ),
                            html.Button(
                                'Cancel',
                                id='cancel-universe-constraint-button',
                                n_clicks=0,
                                style={
                                    'backgroundColor': '#6c757d',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '10px 20px',
                                    'borderRadius': '4px',
                                    'cursor': 'pointer'
                                }
                            )
                        ], style={'textAlign': 'center'})
                    ], style={
                        'backgroundColor': 'white',
                        'padding': '30px',
                        'borderRadius': '8px',
                        'maxWidth': '750px',
                        'margin': 'auto'
                    })
                ],
                style={
                    'position': 'fixed',
                    'top': '0',
                    'left': '0',
                    'width': '100%',
                    'height': '100%',
                    'backgroundColor': 'rgba(0,0,0,0.5)',
                    'display': 'none',
                    'zIndex': 1000,
                    'justifyContent': 'center',
                    'alignItems': 'center'
                }
            ),
        ],
    )
    
    # Register callbacks
    # Use the new orchestrated callback system
    print("🚀 Using NEW orchestrated callback system")
    register_orchestrated_callbacks(app)
    
    # Register simple LLM callback
    register_llm_callbacks(app)
    
    return app


def register_llm_callbacks(app):
    """Register callbacks for LLM SQL generation and testing."""
    
    @app.callback(
        [Output('universe-constraint-input', 'value', allow_duplicate=True),
         Output('generation-status', 'children')],
        [Input('generate-sql-button', 'n_clicks')],
        [State('natural-language-input', 'value')],
        prevent_initial_call=True
    )
    def generate_sql_from_natural_language(n_clicks, natural_language):
        if not n_clicks or not natural_language:
            return dash.no_update, dash.no_update
        
        try:
            # Simple OpenAI API call using the same key as embedding service
            import requests
            import json
            
            # Use the same Azure OpenAI key as the embedding service
            api_key = "a349cd5ebfcb45f59b2004e6e8b7d700"
            url = "https://apigw.rand.org/openai/RAND/inference/deployments/gpt-4o-2024-11-20-us/chat/completions?api-version=2024-02-01"
            
            headers = {
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": api_key
            }
            
            # Load the comprehensive documentation for the LLM
            try:
                with open('docscope/docs/UNIVERSE_FILTER_GUIDE.md', 'r') as f:
                    guide_content = f.read()
                with open('docscope/docs/DATABASE_SCHEMA.md', 'r') as f:
                    schema_content = f.read()
            except FileNotFoundError:
                # Fallback to inline prompt if files not found
                guide_content = "Use standard SQL WHERE clause construction with available fields."
                schema_content = "Available fields: doctrove_source, doctrove_title, doctrove_abstract, doctrove_primary_date, openalex_country_uschina, openalex_country_country, country2"
            
            # Dynamic prompt that uses the loaded markdown documents
            prompt = f"""You are a SQL expert. Generate ONLY a SQL WHERE clause for this request: "{natural_language}"

## 💡 HELPFUL GUIDELINES - AUTHOR SEARCHES:

**For searching authors, consider using:**
- Field: `doctrove_authors` (works for all sources)
- Syntax: `array_to_string(doctrove_authors, '|') LIKE '%AuthorName%'`
- Example: `doctrove_source = 'randpub' AND array_to_string(doctrove_authors, '|') LIKE '%Gulden%'`

**Alternative approaches that also work:**
- `randpub_authors LIKE '%AuthorName%'` (RAND-specific)
- `openalex_authors LIKE '%AuthorName%'` (OpenAlex-specific)

**Note:** `doctrove_authors` is preferred because it works universally across all sources.

## INSTRUCTIONS:
Please read and follow the query construction guide and database schema provided below.

## QUERY CONSTRUCTION GUIDE:
{guide_content}

## DATABASE SCHEMA:
{schema_content}

## TASK:
Based on the guide and schema above, generate a SQL WHERE clause that:
1. Uses ONLY the fields documented in the schema
2. Follows the naming conventions and relationships described
3. Applies the appropriate source constraints
4. Returns ONLY the WHERE clause (no SELECT, FROM, JOIN)

## OUTPUT:
Return ONLY the SQL WHERE clause. Nothing else.

**Note**: After generating SQL, use the "Test Query" button to verify it works before applying."""

            data = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            print(f"🔍 LLM DEBUG: Making API call to Azure OpenAI...")
            # Disable SSL verification for development (not recommended for production)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.post(url, headers=headers, json=data, timeout=30, verify=False)
            print(f"🔍 LLM DEBUG: Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"🔍 LLM DEBUG: Error response: {response.text}")
                return dash.no_update, f"❌ API Error: {response.status_code} - {response.text}"
            
            result = response.json()
            print(f"🔍 LLM DEBUG: Response: {result}")
            
            if 'choices' not in result or not result['choices']:
                return dash.no_update, f"❌ Invalid response format: {result}"
            
            generated_sql = result['choices'][0]['message']['content'].strip()
            print(f"🔍 LLM DEBUG: Generated SQL: {generated_sql}")
            
            # Clean up the response - remove markdown code blocks, quotes, and extra text
            # Remove markdown code blocks
            if generated_sql.startswith('```'):
                generated_sql = generated_sql[3:]
            if generated_sql.endswith('```'):
                generated_sql = generated_sql[:-3]
            
            # Remove SQL language specifiers
            if generated_sql.startswith('sql'):
                generated_sql = generated_sql[3:]
            
            # Remove quotes if present
            if generated_sql.startswith('"') and generated_sql.endswith('"'):
                generated_sql = generated_sql[1:-1]
            if generated_sql.startswith("'") and generated_sql.endswith("'"):
                generated_sql = generated_sql[1:-1]
            
            # Clean up any remaining whitespace and newlines
            generated_sql = generated_sql.strip()
            
            # Additional cleaning: remove any remaining markdown artifacts
            generated_sql = generated_sql.replace('`', '')  # Remove any remaining backticks
            
            print(f"🔍 LLM DEBUG: Cleaned SQL: {generated_sql}")
            print(f"🔍 LLM DEBUG: SQL length: {len(generated_sql)}")
            print(f"🔍 LLM DEBUG: SQL contains SELECT: {'SELECT' in generated_sql.upper()}")
            print(f"🔍 LLM DEBUG: SQL contains FROM: {'FROM' in generated_sql.upper()}")
            print(f"🔍 LLM DEBUG: SQL contains JOIN: {'JOIN' in generated_sql.upper()}")
            
            # Validate that we have actual SQL content
            if not generated_sql or len(generated_sql.strip()) < 10:
                return dash.no_update, f"❌ Generated SQL is too short or empty. Please try again."
            
            # Check for common invalid patterns
            if 'SELECT' in generated_sql.upper() or 'FROM' in generated_sql.upper() or 'JOIN' in generated_sql.upper():
                return dash.no_update, f"❌ Generated SQL contains invalid clauses (SELECT, FROM, JOIN). Only WHERE clause allowed."
            
            # Validate the generated SQL to catch obvious errors
            if 'topic' in generated_sql.lower():
                return dash.no_update, f"❌ Generated SQL contains invalid field 'topic'. Please try a different request."
            
            if 'doctrove_source = \'doctrove\'' in generated_sql:
                return dash.no_update, f"❌ Generated SQL has invalid source 'doctrove'. Valid sources are: openalex, randpub, extpub, aipickle"
            
            # Note: Both doctrove_authors and randpub_authors work for RAND publications
            # doctrove_authors is preferred for universal compatibility
            
            # Check for balanced parentheses
            open_parens = generated_sql.count('(')
            close_parens = generated_sql.count(')')
            if open_parens != close_parens:
                return dash.no_update, f"❌ Generated SQL has unbalanced parentheses. Please try again."
            
            # Check for basic SQL syntax
            if not any(op in generated_sql.upper() for op in ['=', 'LIKE', 'IN', '>', '<', '>=', '<=']):
                return dash.no_update, f"❌ Generated SQL appears to be invalid. Please try a different request."
            
            print(f"🔍 LLM DEBUG: SQL validation passed")
            return generated_sql, f"✅ Please check the automatically generated SQL query below"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            print(f"🔍 LLM DEBUG: Network error: {e}")
            return dash.no_update, f"❌ Network error: Please check your connection and try again"
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            print(f"🔍 LLM DEBUG: JSON error: {e}")
            return dash.no_update, f"❌ Invalid response from AI service: Please try again"
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"🔍 LLM DEBUG: Unexpected error: {e}")
            return dash.no_update, f"❌ Unexpected error: {str(e)}"

    @app.callback(
        Output('schema-display', 'children'),
        [Input('view-schema-button', 'n_clicks')],
        prevent_initial_call=True
    )
    def display_database_schema(n_clicks):
        """Display the database schema when the View Schema button is clicked."""
        if not n_clicks:
            return dash.no_update
        
        try:
            # Load the database schema document
            with open('docscope/docs/DATABASE_SCHEMA.md', 'r') as f:
                schema_content = f.read()
            
            # Convert markdown to HTML-like display
            # Simple conversion for readability
            html_content = []
            lines = schema_content.split('\n')
            
            for line in lines:
                if line.startswith('# '):
                    # Main heading
                    html_content.append(html.H3(line[2:], style={'color': '#1976d2', 'marginTop': '20px', 'marginBottom': '10px'}))
                elif line.startswith('## '):
                    # Sub heading
                    html_content.append(html.H4(line[3:], style={'color': '#333', 'marginTop': '15px', 'marginBottom': '8px'}))
                elif line.startswith('### '):
                    # Sub-sub heading
                    html_content.append(html.H5(line[4:], style={'color': '#555', 'marginTop': '12px', 'marginBottom': '6px'}))
                elif line.startswith('- '):
                    # List item
                    html_content.append(html.Li(line[2:], style={'marginBottom': '4px', 'color': '#333'}))
                elif line.startswith('```'):
                    # Skip code block markers
                    continue
                elif line.strip() and not line.startswith('|'):
                    # Regular paragraph
                    html_content.append(html.P(line, style={'marginBottom': '8px', 'lineHeight': '1.4', 'color': '#333'}))
                elif line.startswith('|'):
                    # Table row - simple table display
                    if '---' not in line:  # Skip separator lines
                        cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last cells
                        if cells:
                            html_content.append(html.Tr([html.Td(cell, style={'padding': '4px 8px', 'border': '1px solid #ddd', 'color': '#333'}) for cell in cells]))
            
            # Wrap in a scrollable container
            return html.Div([
                html.H4("📋 Database Schema", style={'color': '#1976d2', 'marginBottom': '15px', 'textAlign': 'center'}),
                html.Div([
                    html.Div(html_content, style={'textAlign': 'left'}),
                    html.Div([
                        html.Button(
                            '✕ Close Schema',
                            id='close-schema-button',
                            n_clicks=0,
                            style={
                                'backgroundColor': '#6c757d',
                                'color': 'white',
                                'border': 'none',
                                'padding': '8px 16px',
                                'borderRadius': '4px',
                                'cursor': 'pointer',
                                'marginTop': '15px'
                            }
                        )
                    ], style={'textAlign': 'center'})
                ], style={
                    'maxHeight': '400px',
                    'overflowY': 'auto',
                    'backgroundColor': '#f8f9fa',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'border': '1px solid #dee2e6'
                })
            ])
            
        except FileNotFoundError:
            return html.Div([
                html.Div("❌ Schema file not found", style={'color': '#d32f2f', 'fontWeight': 'bold', 'marginBottom': '10px', 'backgroundColor': '#ffebee', 'padding': '8px', 'borderRadius': '4px'}),
                html.Div("💡 Database schema documentation is not available", style={'fontSize': '14px', 'color': '#d32f2f', 'backgroundColor': '#ffebee', 'padding': '8px', 'borderRadius': '4px'})
            ])
        except Exception as e:
            return html.Div([
                html.Div("❌ Error loading schema", style={'color': '#d32f2f', 'fontWeight': 'bold', 'marginBottom': '10px', 'backgroundColor': '#ffebee', 'padding': '8px', 'borderRadius': '4px'}),
                html.Div(f"💡 Error: {str(e)}", style={'fontSize': '14px', 'color': '#d32f2f', 'backgroundColor': '#ffebee', 'padding': '8px', 'borderRadius': '4px'})
                         ])

    @app.callback(
        Output('schema-display', 'children', allow_duplicate=True),
        [Input('close-schema-button', 'n_clicks')],
        prevent_initial_call=True
    )
    def close_schema_display(n_clicks):
        """Close the schema display when the close button is clicked."""
        if not n_clicks:
            return dash.no_update
        return ""  # Clear the schema display

    @app.callback(
        Output('test-results', 'children'),
        [Input('test-query-button', 'n_clicks')],
        [State('universe-constraint-input', 'value')],
        prevent_initial_call=True
    )
    def test_sql_query(n_clicks, sql_query):
        """Test the SQL query in the input field to see if it returns results."""
        if not n_clicks:
            return dash.no_update
        
        if not sql_query or not sql_query.strip():
            return html.Div([
                html.Div("⚠️ No SQL to test", style={'color': '#f57c00', 'fontWeight': 'bold', 'marginBottom': '10px', 'backgroundColor': '#fff3e0', 'padding': '8px', 'borderRadius': '4px'}),
                html.Div("💡 Generate SQL first or type your own SQL query", style={'fontSize': '14px', 'color': '#f57c00', 'backgroundColor': '#fff3e0', 'padding': '8px', 'borderRadius': '4px'})
            ])
        
        try:
            # Import data service to test the query
            from .components.data_service import fetch_papers_from_api
            
            print(f"🔍 TEST DEBUG: Testing SQL query: {sql_query}")
            
            # Attempt to auto-detect enrichment join requirements from the SQL
            enrichment_source = None
            enrichment_table = None
            enrichment_field = None
            try:
                import re
                
                # Define main table fields that should NOT trigger enrichment joins
                main_table_fields = {
                    'doctrove_paper_id', 'doctrove_title', 'doctrove_abstract', 
                    'doctrove_source', 'doctrove_primary_date', 'doctrove_authors',
                    'doctrove_embedding_2d', 'doctrove_links'
                }
                
                # Find ALL two-part patterns in the SQL query (but be more specific)
                # Look for patterns that are likely enrichment fields, not just any underscore
                two_part_matches = re.findall(r"(\w+)_(\w+)", sql_query)
                print(f"🔍 TEST DEBUG: Found two-part patterns: {two_part_matches}")
                
                # Find ALL three-part patterns in the SQL query
                three_part_matches = re.findall(r"(\w+)_(\w+)_(\w+)", sql_query)
                print(f"🔍 TEST DEBUG: Found three-part patterns: {three_part_matches}")
                
                # Filter two-part patterns to only include likely enrichment fields
                # Skip patterns that are clearly not enrichment (like 'randpub')
                filtered_two_part = []
                for src, fld in two_part_matches:
                    field_name = f'{src}_{fld}'
                    # Skip if this looks like a main table field or source value
                    if field_name in main_table_fields or fld in ['source', 'publication', 'papers']:
                        print(f"🔍 TEST DEBUG: Skipping likely non-enrichment pattern: {field_name}")
                        continue
                    filtered_two_part.append((src, fld))
                
                print(f"🔍 TEST DEBUG: Filtered two-part patterns: {filtered_two_part}")
                
                # Process three-part patterns first (more specific)
                for src, tbl, fld in three_part_matches:
                    field_name = f'{src}_{tbl}_{fld}'
                    if field_name not in main_table_fields:
                        enrichment_source = src
                        # Handle special cases for table naming
                        if src == 'randpub':
                            enrichment_table = 'randpub_metadata'  # Special case for RAND
                        else:
                            enrichment_table = f'{src}_{tbl}'
                        enrichment_field = field_name
                        print(f"🔍 TEST DEBUG: Detected three-part pattern: {field_name} → table: {enrichment_table}")
                        break
                
                # If no three-part pattern found, process filtered two-part patterns
                if not enrichment_source:
                    for src, fld in filtered_two_part:
                        field_name = f'{src}_{fld}'
                        
                        # Skip if this is a main table field
                        if field_name in main_table_fields:
                            print(f"🔍 TEST DEBUG: Skipping main table field: {field_name}")
                            continue
                        else:
                            enrichment_source = src
                            # Handle special cases for table naming
                            if src == 'randpub':
                                enrichment_table = 'randpub_metadata'  # Special case for RAND
                            else:
                                enrichment_table = f'{src}_metadata'  # Assume standard naming convention
                            enrichment_field = field_name
                            print(f"🔍 TEST DEBUG: Detected two-part pattern: {field_name} → table: {enrichment_table}")
                            break
                    
            except Exception as _e:
                # Best-effort auto-detection; ignore failures
                print(f"🔍 TEST DEBUG: Auto-detection failed: {_e}")
                pass
            print(f"🔍 TEST DEBUG: Auto-detected enrichment for test: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}")
            
            # Add detailed debug logging for query composition
            print(f"🔍 TEST DEBUG: About to call fetch_papers_from_api with:")
            print(f"🔍 TEST DEBUG:   - sql_filter: '{sql_query}'")
            print(f"🔍 TEST DEBUG:   - enrichment_source: '{enrichment_source}'")
            print(f"🔍 TEST DEBUG:   - enrichment_table: '{enrichment_table}'")
            print(f"🔍 TEST DEBUG:   - enrichment_field: '{enrichment_field}'")
            print(f"🔍 TEST DEBUG:   - limit: None")
            print(f"🔍 TEST DEBUG:   - similarity_threshold: 0.5")
            
            # Test the query without limit to get accurate count
            test_result = fetch_papers_from_api(
                limit=None,  # No limit to get accurate count
                sql_filter=sql_query,
                similarity_threshold=0.5,
                enrichment_source=enrichment_source,
                enrichment_table=enrichment_table,
                enrichment_field=enrichment_field
            )
            
            print(f"🔍 TEST DEBUG: Test result type: {type(test_result)}, content: {test_result}")
            
            # test_result is a tuple (DataFrame, total_count)
            df, total_count = test_result
            
            if df is not None and not df.empty:
                # Query works and returns results
                paper_count = len(df)
                # Convert DataFrame to list of dictionaries for easier access
                papers_list = df.to_dict('records')
                
                return html.Div([
                    html.Div(f"✅ Query test successful!", style={'color': '#2e7d32', 'fontWeight': 'bold', 'marginBottom': '10px', 'backgroundColor': '#e8f5e8', 'padding': '8px', 'borderRadius': '4px'}),
                    html.Div(f"📊 Query returns {paper_count} papers", style={'color': '#2e7d32', 'marginBottom': '8px', 'backgroundColor': '#e8f5e8', 'padding': '8px', 'borderRadius': '4px'})
                ])
            else:
                # Query works but returns no results
                return html.Div([
                    html.Div("⚠️ Query syntax is valid but returns no papers", style={'color': '#f57c00', 'fontWeight': 'bold', 'marginBottom': '10px', 'backgroundColor': '#fff3e0', 'padding': '8px', 'borderRadius': '4px'}),
                    html.Div(f"💡 Query returned 0 papers (total available: {total_count})", style={'fontSize': '14px', 'color': '#f57c00', 'backgroundColor': '#fff3e0', 'padding': '8px', 'borderRadius': '4px'})
                ])
                
        except Exception as e:
            # Query failed
            error_msg = str(e)
            print(f"🔍 TEST DEBUG: Query test failed: {error_msg}")
            
            # Provide more helpful error messages
            if "int' object has no attribute 'get'" in error_msg:
                help_text = "💡 This error suggests the query returned unexpected data format. Try simplifying your query or check field names."
            elif "column" in error_msg.lower() and "does not exist" in error_msg.lower():
                help_text = "💡 The field name in your query doesn't exist. Check the available fields in the examples above."
            elif "syntax error" in error_msg.lower():
                help_text = "💡 There's a SQL syntax error. Check parentheses, quotes, and operators."
            elif "permission denied" in error_msg.lower():
                help_text = "💡 Database permission issue. This might be a system problem."
            else:
                help_text = "💡 Check your SQL syntax or try a different query."
            
            return html.Div([
                html.Div("❌ Query test failed", style={'color': '#d32f2f', 'fontWeight': 'bold', 'marginBottom': '10px', 'backgroundColor': '#ffebee', 'padding': '8px', 'borderRadius': '4px'}),
                html.Div(f"Error: {error_msg}", style={'color': '#d32f2f', 'fontSize': '14px', 'marginBottom': '8px', 'backgroundColor': '#ffebee', 'padding': '8px', 'borderRadius': '4px'}),
                html.Div(help_text, style={'fontSize': '14px', 'color': '#1976d2', 'backgroundColor': '#e3f2fd', 'padding': '8px', 'borderRadius': '4px'})
            ])


def run_app(debug=True, host='0.0.0.0', port=None):
    """Run the DocScope application."""
    import os
    if port is None:
        # Require explicit port configuration - no dangerous fallbacks
        port_env = os.getenv('DOCSCOPE_PORT')
        if port_env is None:
            raise ValueError(
                "CRITICAL: DOCSCOPE_PORT environment variable is not set!\n"
                "This application requires explicit port configuration.\n"
                "Please set DOCSCOPE_PORT in your .env.local file.\n"
                "Example: DOCSCOPE_PORT=8051"
            )
        try:
            port = int(port_env)
        except ValueError:
            raise ValueError(
                f"CRITICAL: Invalid DOCSCOPE_PORT value: '{port_env}'\n"
                "DOCSCOPE_PORT must be a valid integer.\n"
                "Example: DOCSCOPE_PORT=8051"
            )
    
    app = create_app()
    app.run(debug=debug, host=host, port=port)


if __name__ == '__main__':
    run_app() 