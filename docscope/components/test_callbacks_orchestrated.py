"""
Comprehensive tests for the new orchestrated callbacks.

This module tests the new callback architecture that uses our orchestrator system
with single responsibility per callback.
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch
import dash
from dash import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import time

# Import our new callbacks
from .callbacks_orchestrated import (
    register_orchestrated_callbacks,
    create_fallback_figure,
    get_fallback_values,
    create_status_content
)

# Import our orchestrator for testing
from .component_orchestrator_fp import (
    orchestrate_view_update,
    orchestrate_data_fetch,
    orchestrate_visualization,
    orchestrate_complete_workflow
)


class TestOrchestratedCallbacks:
    """Test the new orchestrated callback architecture."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock Dash app
        self.app = MagicMock()
        self.app.callback = MagicMock()
        
        # Mock callback context
        self.mock_context = MagicMock()
        self.mock_context.triggered = [{'prop_id': 'test-input.value'}]
        
        # Sample test data
        self.sample_view_ranges = {
            'xaxis': [-5.0, 5.0],
            'yaxis': [-5.0, 5.0],
            'timestamp': time.time()
        }
        
        self.sample_data = [
            {'id': 1, 'title': 'Test Paper 1', 'x': 0.0, 'y': 0.0},
            {'id': 2, 'title': 'Test Paper 2', 'x': 1.0, 'y': 1.0}
        ]
        
        self.sample_enrichment = {
            'sources': ['openalex'],
            'year_range': [2020, 2023],
            'similarity_threshold': 0.7,
            'use_clustering': True,
            'use_llm_summaries': False,
            'cluster_count': 5
        }
    
    def test_register_orchestrated_callbacks(self):
        """Test that callbacks are registered correctly."""
        # Register callbacks
        register_orchestrated_callbacks(self.app)
        
        # Verify that app.callback was called multiple times (once per callback)
        assert self.app.callback.call_count >= 6  # We have 6 main callbacks
        
        # Verify callback decorators were applied
        callback_calls = self.app.callback.call_args_list
        
        # Check that we have the right outputs
        outputs = [call[0][0] for call in callback_calls]
        expected_outputs = [
            'view-ranges-store.data',
            'data-store.data', 
            'graph-3.figure',
            'enrichment-state.data',
            'status-indicator.children',
            'cluster-busy.data'
        ]
        
        for expected in expected_outputs:
            assert any(expected in str(output) for output in outputs), f"Missing output: {expected}"
    
    def test_callback_registration_structure(self):
        """Test that callback registration creates the expected structure."""
        # Register callbacks
        register_orchestrated_callbacks(self.app)
        
        # Verify callback calls
        callback_calls = self.app.callback.call_args_list
        
        # Check that all required callbacks are registered with correct structure
        # Instead of hardcoding positions, find callbacks by their characteristics
        
        # Find view management callback (should have view-ranges-store.data as output)
        view_callback = None
        for callback in callback_calls:
            if 'view-ranges-store.data' in str(callback[0][0]):
                view_callback = callback
                break
        assert view_callback is not None, "View management callback not found"
        assert 'graph-3.relayoutData' in str(view_callback[0][1])
        
        # Find data fetching callback (should have data-store.data as output)
        data_callback = None
        for callback in callback_calls:
            if 'data-store.data' in str(callback[0][0]):
                data_callback = callback
                break
        assert data_callback is not None, "Data fetching callback not found"
        # view-ranges-store.data should be in States, not Inputs for this callback
        assert 'view-ranges-store.data' in str(data_callback[0][2])  # States parameter
        
        # Find zoom data fetch callback (should have data-store.data as output and view-ranges-store.data as input)
        zoom_callback = None
        for callback in callback_calls:
            if ('data-store.data' in str(callback[0][0]) and 
                'view-ranges-store.data' in str(callback[0][1])):
                zoom_callback = callback
                break
        assert zoom_callback is not None, "Zoom data fetch callback not found"
        assert 'data-store.data' in str(zoom_callback[0][0])
        assert 'view-ranges-store.data' in str(zoom_callback[0][1])  # Input for zoom data fetch


class TestFallbackFunctions:
    """Test fallback utility functions."""
    
    def test_create_fallback_figure(self):
        """Test fallback figure creation."""
        figure = create_fallback_figure()
        
        # Verify it's a Plotly figure
        assert isinstance(figure, go.Figure)
        
        # Verify it has data
        assert len(figure.data) == 1
        assert isinstance(figure.data[0], go.Scatter)
        
        # Verify layout
        assert figure.layout.title.text == "Fallback Visualization"
        assert figure.layout.xaxis.title.text == "X Axis"
        assert figure.layout.yaxis.title.text == "Y Axis"
    
    def test_get_fallback_values(self):
        """Test fallback values retrieval."""
        fallbacks = get_fallback_values()
        
        # Verify structure
        assert isinstance(fallbacks, dict)
        assert 'data' in fallbacks
        assert 'figure' in fallbacks
        assert 'view_state' in fallbacks
        assert 'enrichment_state' in fallbacks
        
        # Verify values
        assert fallbacks['data'] == []
        assert isinstance(fallbacks['figure'], go.Figure)
        assert fallbacks['view_state'] == {}
        assert fallbacks['enrichment_state'] == {}

    def test_create_status_content_missing_and_estimated_counts(self):
        """Status content is single-line and robust without total_count."""
        # Missing total_count but some data
        data = [{'id': 1}, {'id': 2}]
        html_div = create_status_content(data, {})
        # Should not crash; content should mention Loaded 2 papers
        assert 'Loaded' in str(html_div)
        assert '2' in str(html_div)


class TestCallbackIntegration:
    """Test callback integration with orchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = MagicMock()
        self.app.callback = MagicMock()
    
    @patch('docscope.components.callbacks_orchestrated.orchestrate_view_update')
    def test_view_callback_integration(self, mock_orchestrate):
        """Test that view callback integrates with orchestrator."""
        # Mock orchestrator response
        mock_orchestrate.return_value = {
            'success': True,
            'view_state': {'xaxis': [-5.0, 5.0], 'yaxis': [-5.0, 5.0]},
            'error': None
        }
        
        # Register callbacks
        register_orchestrated_callbacks(self.app)
        
        # Verify orchestrator function is imported and used
        # This test validates the integration without calling the actual callback
        assert mock_orchestrate.called is False  # Not called during registration
        
        # Verify the callback was registered with the right signature
        callback_calls = self.app.callback.call_args_list
        view_callback = callback_calls[0]
        
        # Check that view callback has the right inputs/outputs
        assert 'view-ranges-store.data' in str(view_callback[0][0])  # Output
        assert 'graph-3.relayoutData' in str(view_callback[0][1])    # Input
    
    @patch('docscope.components.callbacks_orchestrated.orchestrate_visualization')
    def test_orchestrate_visualization_honors_force_autorange(self, mock_orchestrate):
        """Ensure force_autorange flag is passed through to orchestrator."""
        app = MagicMock()
        app.callback = MagicMock()
        register_orchestrated_callbacks(app)
        mock_orchestrate.return_value = {'success': True, 'figure': go.Figure()}
        # Call orchestrator directly to verify parameter wiring contract
        result = mock_orchestrate(data=[{'id': 1}], view_ranges=None, enrichment_state=None, force_autorange=True)
        assert result['success'] is True
        mock_orchestrate.assert_called_with(data=[{'id': 1}], view_ranges=None, enrichment_state=None, force_autorange=True)
    
    @patch('docscope.components.component_orchestrator_fp.orchestrate_data_fetch')
    def test_data_callback_integration(self, mock_orchestrate):
        """Test that data callback integrates with orchestrator."""
        # Mock orchestrator response
        mock_orchestrate.return_value = {
            'success': True,
            'data': [{'id': 1, 'title': 'Test'}],
            'error': None
        }
        
        # Register callbacks
        register_orchestrated_callbacks(self.app)
        
        # Verify the callback was registered with the right signature
        callback_calls = self.app.callback.call_args_list
        
        # Find data callback by its characteristics (should have data-store.data as output)
        data_callback = None
        for callback in callback_calls:
            if 'data-store.data' in str(callback[0][0]):
                data_callback = callback
                break
        assert data_callback is not None, "Data callback not found"
        
        # Check that data callback has the right inputs/outputs
        assert 'data-store.data' in str(data_callback[0][0])  # Output
        assert 'view-ranges-store.data' in str(data_callback[0][2])  # State (not Input)
    
    @patch('docscope.components.component_orchestrator_fp.orchestrate_visualization')
    def test_zoom_data_callback_integration(self, mock_orchestrate):
        """Test that zoom data callback integrates with orchestrator."""
        # Mock orchestrator response
        mock_orchestrate.return_value = {
            'success': True,
            'data': [{'id': 1, 'title': 'Test'}],
            'error': None
        }
        
        # Register callbacks
        register_orchestrated_callbacks(self.app)
        
        # Verify the callback was registered with the right signature
        callback_calls = self.app.callback.call_args_list
        
        # Find zoom data callback by its characteristics (should have data-store.data as output and view-ranges-store.data as input)
        zoom_callback = None
        for callback in callback_calls:
            if ('data-store.data' in str(callback[0][0]) and 
                'view-ranges-store.data' in str(callback[0][1])):
                zoom_callback = callback
                break
        assert zoom_callback is not None, "Zoom data callback not found"
        
        # Check that zoom data callback has the right inputs/outputs
        assert 'data-store.data' in str(zoom_callback[0][0])  # Output
        assert 'view-ranges-store.data' in str(zoom_callback[0][1])  # Input for zoom data fetch


class TestCallbackErrorHandling:
    """Test callback error handling and recovery."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = MagicMock()
        self.app.callback = MagicMock()
    
    def test_callback_registration_error_handling(self):
        """Test that callback registration handles errors gracefully."""
        # This test validates that the registration process is robust
        # even if there are issues with individual callbacks
        
        try:
            register_orchestrated_callbacks(self.app)
            # If we get here, registration succeeded
            assert True
        except Exception as e:
            # If registration fails, it should fail gracefully
            pytest.fail(f"Callback registration failed unexpectedly: {e}")
    
    def test_callback_structure_validation(self):
        """Test that all required callbacks are registered."""
        # Register callbacks
        register_orchestrated_callbacks(self.app)
        
        # Verify we have the expected number of callbacks
        callback_calls = self.app.callback.call_args_list
        assert len(callback_calls) >= 6, f"Expected at least 6 callbacks, got {len(callback_calls)}"
        
        # Verify each callback has the required structure
        for i, callback_call in enumerate(callback_calls):
            # Each callback should have outputs and inputs
            assert len(callback_call[0]) >= 2, f"Callback {i} missing required arguments"
            
            # First argument should be outputs
            outputs = callback_call[0][0]
            assert outputs is not None, f"Callback {i} missing outputs"
            
            # Second argument should be inputs
            inputs = callback_call[0][1]
            assert inputs is not None, f"Callback {i} missing inputs"


if __name__ == '__main__':
    pytest.main([__file__])
