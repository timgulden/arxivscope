"""
Utility functions for error handling and user feedback.
"""

import dash
from dash import html


def create_error_message(error_type: str, details: str = None) -> html.Div:
    """Create a user-friendly error message component."""
    error_messages = {
        'data_loading': 'Unable to load data. Please try refreshing the page.',
        'clustering': 'Clustering failed. Please try again with fewer clusters.',
        'api_error': 'Service temporarily unavailable. Please try again later.',
        'network_error': 'Network connection issue. Please check your internet connection.',
        'invalid_input': 'Invalid input provided. Please check your settings.',
        'general': 'An unexpected error occurred. Please try again.'
    }
    
    message = error_messages.get(error_type, error_messages['general'])
    if details:
        message += f" Details: {details}"
    
    return html.Div([
        html.H6("⚠️ Error", style={'color': '#ff6b6b', 'marginBottom': '10px'}),
        html.P(message, style={'color': '#666', 'fontSize': '14px'})
    ], style={
        'padding': '15px',
        'border': '1px solid #ff6b6b',
        'borderRadius': '5px',
        'backgroundColor': '#fff5f5',
        'marginBottom': '15px'
    }) 