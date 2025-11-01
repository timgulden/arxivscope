"""
Test utilities for DocScope components.
Provides common test functions, mock data generators, and test fixtures.
"""

import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from typing import List, Dict, Any, Optional


def create_mock_paper_data(count: int = 3) -> List[Dict[str, Any]]:
    """Create mock paper data for testing."""
    papers = []
    for i in range(count):
        paper = {
            'doctrove_paper_id': str(i + 1),
            'doctrove_title': f'Test Paper {i + 1}',
            'doctrove_abstract': f'This is test abstract {i + 1}',
            'doctrove_primary_date': f'2024-01-{i + 1:02d}',
            'doctrove_authors': [f'Author {i + 1}'],
            'doctrove_embedding_2d': f'({0.1 + i * 0.1}, {0.2 + i * 0.1})',

            'country2': ['United States', 'China', 'United Kingdom'][i % 3],
            'doi': f'10.1000/test.{i + 1}',
            'links': '[{"href": "https://arxiv.org/abs/test", "rel": "alternate", "type": "text/html"}]',
            'doctrove_source': ['arxiv', 'nature', 'science'][i % 3]
        }
        papers.append(paper)
    return papers


def create_mock_api_response(papers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a mock API response."""
    return {
        'papers': papers,
        'total': len(papers),
        'limit': len(papers)
    }


def create_mock_stats_response() -> Dict[str, Any]:
    """Create a mock stats API response."""
    return {
        'sources': [
            {'doctrove_source': 'arxiv'},
            {'doctrove_source': 'nature'},
            {'doctrove_source': 'science'},
            {'doctrove_source': 'RAND'}
        ],
        'total_papers': 1000
    }


def create_mock_llm_response(cluster_count: int) -> Dict[str, Any]:
    """Create a mock LLM API response for clustering."""
    summaries = []
    for i in range(cluster_count):
        summaries.append(f"{i + 1}. Cluster {i + 1} summary")
    
    return {
        'choices': [{
            'message': {
                'content': '\n'.join(summaries)
            }
        }]
    }


def create_test_dataframe(include_coordinates: bool = True, include_rand: bool = False) -> pd.DataFrame:
    """Create a test DataFrame with realistic data."""
    papers = create_mock_paper_data(5)
    
    if include_rand:
        # Add a RAND paper with no country
        rand_paper = {
            'doctrove_paper_id': '6',
            'doctrove_title': 'RAND Test Paper',
            'doctrove_abstract': 'This is a RAND test abstract',
            'doctrove_primary_date': '2024-01-06',
            'doctrove_authors': ['RAND Author'],
            'doctrove_embedding_2d': '(0.6, 0.7)',

            'country2': None,  # RAND papers have no country
            'doi': '10.1000/test.6',
            'links': '[{"href": "https://rand.org/test", "rel": "alternate", "type": "text/html"}]',
            'doctrove_source': 'RAND'
        }
        papers.append(rand_paper)
    
    df = pd.DataFrame(papers)
    
    if include_coordinates:
        # Parse coordinates and add x, y columns
        df['x'] = [0.1 + i * 0.1 for i in range(len(df))]
        df['y'] = [0.2 + i * 0.1 for i in range(len(df))]
    
    # Rename columns to match application expectations
    df = df.rename(columns={
        'doctrove_title': 'Title',
        'doctrove_abstract': 'Summary',
        'doctrove_primary_date': 'Submitted Date',
        'doctrove_authors': 'Authors',
        'country2': 'Country of Publication',
        'doi': 'DOI',
        'links': 'Links'
    })
    
    return df


def create_mock_requests_response(data: Dict[str, Any], status_code: int = 200) -> MagicMock:
    """Create a mock requests response."""
    mock_response = MagicMock()
    mock_response.json.return_value = data
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = status_code
    return mock_response


def create_mock_click_data(point_index: int = 0) -> Dict[str, Any]:
    """Create mock click data for testing callbacks."""
    return {
        'points': [{
            'customdata': [point_index],
            'x': 0.1,
            'y': 0.2,
            'pointIndex': point_index
        }]
    }


def create_mock_relayout_data(x_range: tuple = (0, 1), y_range: tuple = (0, 1)) -> Dict[str, Any]:
    """Create mock relayout data for testing zoom callbacks."""
    return {
        'xaxis.range[0]': x_range[0],
        'xaxis.range[1]': x_range[1],
        'yaxis.range[0]': y_range[0],
        'yaxis.range[1]': y_range[1]
    }


def create_mock_clustering_result(cluster_count: int = 3) -> Dict[str, Any]:
    """Create mock clustering result for testing."""
    polygons = []
    annotations = []
    
    for i in range(cluster_count):
        # Create a simple polygon (triangle)
        polygons.append({
            'x': [0 + i, 1 + i, 0.5 + i],
            'y': [0 + i, 0 + i, 1 + i]
        })
        
        # Create annotation
        annotations.append({
            'x': 0.5 + i,
            'y': 0.5 + i,
            'text': f'Cluster {i + 1}'
        })
    
    return {
        'polygons': polygons,
        'annotations': annotations
    }


def create_mock_error_response(error_type: str) -> MagicMock:
    """Create a mock error response for testing error handling."""
    mock_response = MagicMock()
    
    if error_type == 'connection':
        mock_response.raise_for_status.side_effect = Exception("Connection error")
    elif error_type == 'timeout':
        mock_response.raise_for_status.side_effect = Exception("Timeout error")
    elif error_type == 'http':
        mock_response.raise_for_status.side_effect = Exception("HTTP 500 error")
    elif error_type == 'json':
        mock_response.json.side_effect = Exception("JSON parsing error")
    else:
        mock_response.raise_for_status.side_effect = Exception("Unknown error")
    
    return mock_response


def assert_dataframe_structure(df: pd.DataFrame, expected_columns: List[str]):
    """Assert that DataFrame has expected structure."""
    for col in expected_columns:
        assert col in df.columns, f"Expected column '{col}' not found in DataFrame"


def assert_error_handling(func, *args, exception_type=Exception, **kwargs):
    """Assert that a function handles errors gracefully."""
    try:
        result = func(*args, **kwargs)
        # If no exception is raised, the function should handle the error gracefully
        return result
    except exception_type:
        # If the expected exception is raised, that's also acceptable
        return None
    except Exception as e:
        # If an unexpected exception is raised, fail the test
        raise AssertionError(f"Unexpected exception: {e}")


def create_test_app():
    """Create a test Dash app for testing callbacks."""
    import dash
    from dash import html
    
    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.Div(id='test-output'),
        html.Button(id='test-button', n_clicks=0)
    ])
    
    return app


def setup_test_logging():
    """Set up test logging configuration."""
    import logging
    
    # Configure logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('dash').setLevel(logging.WARNING) 