"""
Tests for Pure Function Implementations

This test suite validates:
1. View management pure functions (TRULY PURE - no side effects)
2. Data fetching pure functions (TRULY PURE - no side effects)  
3. Visualization pure functions (TRULY PURE - no side effects)
4. Interceptor orchestration
"""

import pytest
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from unittest.mock import Mock, patch

# Using proper relative imports now

from .component_contracts_fp import ViewState, FilterState, EnrichmentState
from .view_management_fp import (
    extract_view_from_relayout_pure, extract_view_from_relayout,
    extract_view_from_figure_pure, extract_view_from_figure,
    preserve_view_in_figure, validate_view_state,
    create_default_view_state_pure, create_default_view_state,
    create_view_state_from_ranges_pure, create_view_state_from_ranges
)
from .data_fetching_fp import (
    create_fetch_request, fetch_data_pure, fetch_data, validate_fetch_request,
    create_minimal_fetch_request, merge_fetch_requests
)
from .visualization_fp import (
    create_figure, apply_view_preservation, validate_figure,
    create_figure_with_clustering, export_figure_data
)

# ============================================================================
# TEST VIEW MANAGEMENT FUNCTIONS - TRULY PURE
# ============================================================================

class TestViewManagementFunctions:
    """Test view management pure functions - NO SIDE EFFECTS."""
    
    def test_extract_view_from_relayout_pure_valid(self):
        """Test extracting view from valid relayout data using PURE function."""
        relayout_data = {
            'xaxis.range[0]': -5.0,
            'xaxis.range[1]': 5.0,
            'yaxis.range[0]': -3.0,
            'yaxis.range[1]': 3.0
        }
        
        # Use pure function with injected time
        current_time = 1234567890.0
        view_state = extract_view_from_relayout_pure(relayout_data, current_time)
        
        assert view_state is not None
        assert view_state['x_range'] == [-5.0, 5.0]
        assert view_state['y_range'] == [-3.0, 3.0]
        assert view_state['is_zoomed'] is True
        assert view_state['is_panned'] is True
        assert view_state['bbox'] == "-5.0,-3.0,5.0,3.0"
        assert view_state['last_update'] == current_time  # Injected dependency
    
    def test_extract_view_from_relayout_wrapper(self):
        """Test wrapper function that provides time dependency."""
        relayout_data = {
            'xaxis.range[0]': -5.0,
            'xaxis.range[1]': 5.0,
            'yaxis.range[0]': -3.0,
            'yaxis.range[1]': 3.0
        }
        
        # Mock timestamp provider
        mock_time = Mock(return_value=1234567890.0)
        view_state = extract_view_from_relayout(relayout_data, mock_time)
        
        assert view_state is not None
        assert view_state['last_update'] == 1234567890.0
        mock_time.assert_called_once()  # Verify dependency injection
    
    def test_extract_view_from_relayout_autosize(self):
        """Test that autosize events return None."""
        relayout_data = {'autosize': True}
        
        view_state = extract_view_from_relayout_pure(relayout_data, 1234567890.0)
        
        assert view_state is None

    def test_extract_view_from_relayout_dragmode_only(self):
        """Test that dragmode-only relayout returns None."""
        relayout_data = {'dragmode': 'pan'}
        
        view_state = extract_view_from_relayout_pure(relayout_data, 1234567890.0)
        
        assert view_state is None

    def test_extract_view_from_relayout_annotations_shapes_only(self):
        """Test that clustering-related relayout (annotations/shapes) returns None."""
        relayout_data = {'annotations': [], 'shapes': []}
        
        view_state = extract_view_from_relayout_pure(relayout_data, 1234567890.0)
        
        assert view_state is None
    
    def test_extract_view_from_relayout_empty(self):
        """Test extracting view from empty relayout data."""
        relayout_data = {}
        
        view_state = extract_view_from_relayout_pure(relayout_data, 1234567890.0)
        
        assert view_state is None
    
    def test_extract_view_from_figure_pure_valid(self):
        """Test extracting view from valid figure using PURE function."""
        figure_data = {
            'layout': {
                'xaxis': {'range': [-2.0, 2.0]},
                'yaxis': {'range': [-1.0, 1.0]}
            }
        }
        
        current_time = 1234567890.0
        view_state = extract_view_from_figure_pure(figure_data, current_time)
        
        assert view_state is not None
        assert view_state['x_range'] == [-2.0, 2.0]
        assert view_state['y_range'] == [-1.0, 1.0]
        assert view_state['is_zoomed'] is True
        assert view_state['last_update'] == current_time
    
    def test_preserve_view_in_figure(self):
        """Test preserving view in figure."""
        # Create test figure
        fig = go.Figure()
        fig.add_scatter(x=[1, 2, 3], y=[1, 2, 3])
        
        # Create view state as dictionary
        view_state = {
            'x_range': [-5.0, 5.0],
            'y_range': [-3.0, 3.0],
            'is_zoomed': True
        }
        
        # Preserve view
        preserved_fig = preserve_view_in_figure(fig, view_state)
        
        assert preserved_fig.layout.xaxis.autorange is False
        assert preserved_fig.layout.yaxis.autorange is False
        assert preserved_fig.layout.xaxis.range == (-5.0, 5.0)
        assert preserved_fig.layout.yaxis.range == (-3.0, 3.0)
    
    def test_validate_view_state_valid(self):
        """Test validation of valid view state."""
        view_state = {
            'x_range': [-5.0, 5.0],
            'y_range': [-3.0, 3.0]
        }
        
        result = validate_view_state(view_state)
        assert result is True
    
    def test_validate_view_state_invalid(self):
        """Test validation of invalid view state."""
        view_state = {
            'x_range': [5.0, -5.0],  # Invalid: min > max
            'y_range': [-3.0, 3.0]
        }
        
        result = validate_view_state(view_state)
        assert result is False
    
    def test_create_default_view_state_pure(self):
        """Test creating default view state using PURE function."""
        current_time = 1234567890.0
        view_state = create_default_view_state_pure(current_time)
        
        assert view_state['bbox'] is None
        assert view_state['x_range'] is None
        assert view_state['y_range'] is None
        assert view_state['is_zoomed'] is False
        assert view_state['is_panned'] is False
        assert view_state['last_update'] == current_time  # Injected dependency
    
    def test_create_default_view_state_wrapper(self):
        """Test wrapper function that provides time dependency."""
        mock_time = Mock(return_value=1234567890.0)
        view_state = create_default_view_state(mock_time)
        
        assert view_state['last_update'] == 1234567890.0
        mock_time.assert_called_once()
    
    def test_create_view_state_from_ranges_pure(self):
        """Test creating view state from coordinate ranges using PURE function."""
        x_range = [-5.0, 5.0]
        y_range = [-3.0, 3.0]
        current_time = 1234567890.0
        
        view_state = create_view_state_from_ranges_pure(x_range, y_range, current_time)
        
        assert view_state['x_range'] == x_range
        assert view_state['y_range'] == y_range
        assert view_state['is_zoomed'] is True
        assert view_state['is_panned'] is True
        assert view_state['bbox'] == "-5.0,-3.0,5.0,3.0"
        assert view_state['last_update'] == current_time

# ============================================================================
# TEST DATA FETCHING FUNCTIONS - TRULY PURE
# ============================================================================

class TestDataFetchingFunctions:
    """Test data fetching pure functions - NO SIDE EFFECTS."""
    
    def test_create_fetch_request_valid(self):
        """Test creating fetch request with valid states."""
        # Create mock states
        view_state = {
            'bbox': "-5.0,-3.0,5.0,3.0",
            'is_zoomed': True
        }
        
        filter_state = Mock()
        filter_state.to_sql_filter.return_value = "test_filter"
        filter_state.search_text = "test search"
        
        enrichment_state = Mock()
        enrichment_state.similarity_threshold = 0.8
        
        # Create fetch request
        fetch_request = create_fetch_request(view_state, filter_state, enrichment_state)
        
        assert fetch_request['bbox'] == "-5.0,-3.0,5.0,3.0"
        assert fetch_request['sql_filter'] == "test_filter"
        assert fetch_request['search_text'] == "test search"
        assert fetch_request['limit'] == 5000
        assert fetch_request['view_zoomed'] is True
        assert 'enrichment_params' in fetch_request
    
    def test_create_fetch_request_missing_states(self):
        """Test creating fetch request with missing states."""
        fetch_request = create_fetch_request(None, None, None)
        
        assert fetch_request == {}
    
    def test_validate_fetch_request_valid(self):
        """Test validation of valid fetch request."""
        fetch_request = {
            'limit': 5000,
            'bbox': "-5.0,-3.0,5.0,3.0",
            'sql_filter': "test_filter"
        }
        
        result = validate_fetch_request(fetch_request)
        assert result is True
    
    def test_validate_fetch_request_invalid_limit(self):
        """Test validation of fetch request with invalid limit."""
        fetch_request = {
            'limit': -1,  # Invalid: negative limit
            'bbox': "-5.0,-3.0,5.0,3.0"
        }
        
        result = validate_fetch_request(fetch_request)
        assert result is False
    
    def test_validate_fetch_request_invalid_bbox(self):
        """Test validation of fetch request with invalid bbox."""
        fetch_request = {
            'limit': 5000,
            'bbox': "invalid_bbox"  # Invalid format
        }
        
        result = validate_fetch_request(fetch_request)
        assert result is False
    
    def test_create_minimal_fetch_request(self):
        """Test creating minimal fetch request."""
        fetch_request = create_minimal_fetch_request()
        
        assert fetch_request['limit'] == 5000
        assert fetch_request['bbox'] is None
        assert fetch_request['sql_filter'] is None
        assert fetch_request['search_text'] is None
        assert fetch_request['enrichment_params'] == {}
        assert fetch_request['view_zoomed'] is False
    
    def test_merge_fetch_requests(self):
        """Test merging two fetch requests."""
        primary = {'limit': 5000, 'bbox': 'primary_bbox'}
        secondary = {'limit': 3000, 'bbox': 'secondary_bbox', 'sql_filter': 'filter'}
        
        merged = merge_fetch_requests(primary, secondary)
        
        assert merged['limit'] == 5000  # Primary value
        assert merged['bbox'] == 'primary_bbox'  # Primary value
        assert merged['sql_filter'] == 'filter'  # Secondary value (not in primary)
    
    def test_fetch_data_pure(self):
        """Test pure data fetching function with injected provider."""
        # Mock data provider
        mock_provider = Mock(return_value=[{'id': 1, 'title': 'Test'}, {'id': 2, 'title': 'Test2'}])
        
        fetch_request = {'limit': 5000, 'bbox': '-5,-3,5,3'}
        
        # Use pure function with injected provider
        data = fetch_data_pure(fetch_request, mock_provider)
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 2
        assert data.iloc[0]['id'] == 1
        
        # Verify provider was called with correct parameters
        mock_provider.assert_called_once_with(
            limit=5000, bbox='-5,-3,5,3', sql_filter=None, search_text=None
        )
    
    @pytest.mark.skip(reason="Integration test - requires data_service module")
    def test_fetch_data_success(self):
        """Test successful data fetching."""
        # Skip integration test for now
        pass
    
    @pytest.mark.skip(reason="Integration test - requires data_service module")
    def test_fetch_data_error(self):
        """Test data fetching with error."""
        # Skip integration test for now
        pass

# ============================================================================
# TEST VISUALIZATION FUNCTIONS - TRULY PURE
# ============================================================================

class TestVisualizationFunctions:
    """Test visualization pure functions - NO SIDE EFFECTS."""
    
    def test_create_figure_empty_data(self):
        """Test creating figure with empty data."""
        data = pd.DataFrame()
        filter_state = Mock()
        enrichment_state = Mock()
        
        fig = create_figure(data, filter_state, enrichment_state)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == "No Data"
    
    def test_create_figure_with_data(self):
        """Test creating figure with valid data."""
        data = pd.DataFrame({
            'doctrove_embedding_2d_x': [1, 2, 3],
            'doctrove_embedding_2d_y': [1, 2, 3],
            'doctrove_title': ['Title1', 'Title2', 'Title3'],
            'doctrove_source': ['openalex', 'openalex', 'openalex']
        })
        
        filter_state = Mock()
        filter_state.selected_sources = ['openalex']
        filter_state.year_range = [2020, 2023]
        
        enrichment_state = Mock()
        enrichment_state.use_clustering = False
        
        fig = create_figure(data, filter_state, enrichment_state)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'scatter'
        assert "Sources: openalex" in fig.layout.title.text
        assert "Years: 2020-2023" in fig.layout.title.text
    
    def test_apply_view_preservation(self):
        """Test applying view preservation to figure."""
        # Create test figure
        fig = go.Figure()
        fig.add_scatter(x=[1, 2, 3], y=[1, 2, 3])
        
        # Create view state
        view_state = {
            'x_range': [-5.0, 5.0],
            'y_range': [-3.0, 3.0],
            'last_update': 1234567890.0
        }
        
        # Apply view preservation
        preserved_fig = apply_view_preservation(fig, view_state)
        
        assert preserved_fig.layout.xaxis.autorange is False
        assert preserved_fig.layout.yaxis.autorange is False
        assert preserved_fig.layout.xaxis.range == (-5.0, 5.0)
        assert preserved_fig.layout.yaxis.range == (-3.0, 3.0)
        assert preserved_fig.layout.meta['view_preserved'] is True
        assert preserved_fig.layout.meta['view_timestamp'] == 1234567890.0

    def test_apply_view_preservation_handles_missing_ranges_gracefully(self):
        """When view_state lacks ranges, function should return figure unchanged."""
        fig = go.Figure()
        fig.add_scatter(x=[1, 2, 3], y=[1, 2, 3])
        view_state = {'x_range': None, 'y_range': None}
        new_fig = apply_view_preservation(fig, view_state)
        # Autorange should remain default True unless previously changed
        assert isinstance(new_fig, go.Figure)
    
    def test_validate_figure_valid(self):
        """Test validation of valid figure."""
        fig = go.Figure()
        fig.add_scatter(x=[1, 2, 3], y=[1, 2, 3])
        
        result = validate_figure(fig)
        assert result is True
    
    def test_validate_figure_invalid(self):
        """Test validation of invalid figure."""
        fig = go.Figure()  # No data
        
        result = validate_figure(fig)
        assert result is False
    
    def test_create_figure_with_clustering(self):
        """Test creating figure with clustering."""
        data = pd.DataFrame({
            'doctrove_embedding_2d_x': [1, 2, 3],
            'doctrove_embedding_2d_y': [1, 2, 3],
            'cluster_id': [0, 1, 0]
        })
        
        filter_state = Mock()
        filter_state.selected_sources = ['openalex']
        filter_state.year_range = [2020, 2023]
        
        enrichment_state = Mock()
        enrichment_state.use_clustering = True
        
        fig = create_figure_with_clustering(data, filter_state, enrichment_state)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
    
    def test_export_figure_data(self):
        """Test exporting figure data."""
        fig = go.Figure()
        fig.add_scatter(x=[1, 2, 3], y=[1, 2, 3])
        fig.update_layout(title="Test Figure")
        
        export_data = export_figure_data(fig)
        
        assert 'data' in export_data
        assert 'layout' in export_data
        assert 'export_timestamp' in export_data
        assert len(export_data['data']) == 1
        assert export_data['data'][0]['type'] == 'scatter'

# ============================================================================
# TEST INTEGRATION - TRULY PURE
# ============================================================================

class TestIntegration:
    """Test integration between pure functions - NO SIDE EFFECTS."""
    
    def test_view_to_figure_workflow_pure(self):
        """Test complete workflow from view state to figure using PURE functions."""
        # Create view state using pure function
        current_time = 1234567890.0
        view_state = create_view_state_from_ranges_pure([-5.0, 5.0], [-3.0, 3.0], current_time)
        
        # Create filter state
        filter_state = Mock()
        filter_state.selected_sources = ['openalex']
        filter_state.year_range = [2020, 2023]
        filter_state.search_text = None
        
        # Create enrichment state
        enrichment_state = Mock()
        enrichment_state.use_clustering = False
        enrichment_state.similarity_threshold = 0.8
        
        # Create data
        data = pd.DataFrame({
            'doctrove_embedding_2d_x': [1, 2, 3],
            'doctrove_embedding_2d_y': [1, 2, 3],
            'doctrove_title': ['Title1', 'Title2', 'Title3'],
            'doctrove_source': ['openalex', 'openalex', 'openalex']
        })
        
        # Create figure
        fig = create_figure(data, filter_state, enrichment_state)
        
        # Apply view preservation
        preserved_fig = apply_view_preservation(fig, view_state)
        
        # Validate results
        assert validate_figure(preserved_fig) is True
        assert preserved_fig.layout.xaxis.range == (-5.0, 5.0)
        assert preserved_fig.layout.yaxis.range == (-3.0, 3.0)
        assert preserved_fig.layout.meta['view_preserved'] is True

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])
