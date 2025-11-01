"""
Interceptor-Based Orchestrator for DocScope

This module implements component orchestration using the interceptor pattern
and pure functions, following our functional programming principles.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
import plotly.graph_objects as go
from .component_contracts_fp import ViewState, FilterState, EnrichmentState

logger = logging.getLogger(__name__)

# ============================================================================
# INTERCEPTOR DEFINITIONS
# ============================================================================

class Interceptor:
    """Interceptor data structure following our established pattern."""
    
    def __init__(self, enter: Optional[Callable] = None, 
                 leave: Optional[Callable] = None, 
                 error: Optional[Callable] = None):
        self.enter = enter
        self.leave = leave
        self.error = error

# ============================================================================
# INTERCEPTOR STACK EXECUTION
# ============================================================================

def execute_interceptor_stack(interceptors: List[Interceptor], context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a stack of interceptors following our established pattern."""
    try:
        # Execute enter functions (left to right)
        for interceptor in interceptors:
            if interceptor.enter:
                context = interceptor.enter(context)
        
        # Execute leave functions (right to left)
        for interceptor in reversed(interceptors):
            if interceptor.leave:
                context = interceptor.leave(context)
        
        return context
        
    except Exception as e:
        # Handle errors using interceptor error functions
        logger.error(f"Error in interceptor stack: {e}")
        context['error'] = str(e)
        
        # Find the interceptor that caused the error and call its error function
        for interceptor in interceptors:
            if interceptor.error:
                try:
                    context = interceptor.error(context)
                    # Clear error if handled
                    if 'error' in context:
                        del context['error']
                    break
                except Exception as cleanup_error:
                    logger.error(f"Error in interceptor error handler: {cleanup_error}")
        
        return context

# ============================================================================
# VIEW MANAGEMENT INTERCEPTORS
# ============================================================================

def view_extraction_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Extract view state from relayout data."""
    try:
        relayout_data = ctx.get('relayout_data')
        if relayout_data:
            # Import the pure function
            from .view_management_fp import extract_view_from_relayout
            view_state = extract_view_from_relayout(relayout_data)
            ctx['view_state'] = view_state
            ctx['view_extracted'] = True
        return ctx
    except Exception as e:
        logger.error(f"Error in view extraction interceptor: {e}")
        ctx['error'] = f"View extraction failed: {e}"
        raise

def view_validation_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate view state."""
    try:
        view_state = ctx.get('view_state')
        if view_state:
            # Import the pure function
            from .view_management_fp import validate_view_state
            is_valid = validate_view_state(view_state)
            ctx['view_valid'] = is_valid
            if not is_valid:
                logger.warning("Invalid view state detected")
        return ctx
    except Exception as e:
        logger.error(f"Error in view validation interceptor: {e}")
        ctx['error'] = f"View validation failed: {e}"
        raise

def view_preservation_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve view in figure."""
    try:
        figure = ctx.get('figure')
        view_state = ctx.get('view_state')
        if figure and view_state and ctx.get('view_valid', False):
            # Import the pure function
            from .view_management_fp import preserve_view_in_figure
            preserved_figure = preserve_view_in_figure(figure, view_state)
            ctx['figure'] = preserved_figure
            ctx['view_preserved'] = True
        return ctx
    except Exception as e:
        logger.error(f"Error in view preservation interceptor: {e}")
        ctx['error'] = f"View preservation failed: {e}"
        raise

def view_cleanup_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up view-related temporary data."""
    try:
        # Remove temporary view data
        for key in ['view_extracted', 'view_valid', 'view_preserved']:
            if key in ctx:
                del ctx[key]
        return ctx
    except Exception as e:
        logger.error(f"Error in view cleanup interceptor: {e}")
        return ctx

def view_error_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle view management errors."""
    try:
        error_msg = ctx.get('error', 'Unknown view error')
        logger.error(f"View management error: {error_msg}")
        
        # Provide fallback view state
        ctx['view_state'] = None
        ctx['view_valid'] = False
        
        # Clear error
        if 'error' in ctx:
            del ctx['error']
        
        return ctx
    except Exception as e:
        logger.error(f"Error in view error interceptor: {e}")
        return ctx

# ============================================================================
# DATA FETCHING INTERCEPTORS
# ============================================================================

def data_request_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Create data fetch request."""
    try:
        view_state = ctx.get('view_state')
        filter_state = ctx.get('filter_state')
        enrichment_state = ctx.get('enrichment_state')
        
        if all([view_state, filter_state, enrichment_state]):
            # Import the pure function
            from .data_fetching_fp import create_fetch_request
            fetch_request = create_fetch_request(view_state, filter_state, enrichment_state)
            ctx['fetch_request'] = fetch_request
            ctx['request_created'] = True
        return ctx
    except Exception as e:
        logger.error(f"Error in data request interceptor: {e}")
        ctx['error'] = f"Data request creation failed: {e}"
        raise

def data_validation_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate fetch request."""
    try:
        fetch_request = ctx.get('fetch_request')
        if fetch_request:
            # Import the pure function
            from .data_fetching_fp import validate_fetch_request
            is_valid = validate_fetch_request(fetch_request)
            ctx['request_valid'] = is_valid
            if not is_valid:
                logger.warning("Invalid fetch request detected")
        return ctx
    except Exception as e:
        logger.error(f"Error in data validation interceptor: {e}")
        ctx['error'] = f"Data validation failed: {e}"
        raise

def data_fetch_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch data from API."""
    try:
        fetch_request = ctx.get('fetch_request')
        if fetch_request and ctx.get('request_valid', False):
            # Import the pure function
            from .data_fetching_fp import fetch_data
            data = fetch_data(fetch_request)
            ctx['data'] = data
            ctx['data_fetched'] = True
        return ctx
    except Exception as e:
        logger.error(f"Error in data fetch interceptor: {e}")
        ctx['error'] = f"Data fetch failed: {e}"
        raise

def data_cleanup_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up data-related temporary data."""
    try:
        # Remove temporary data
        for key in ['request_created', 'request_valid', 'data_fetched']:
            if key in ctx:
                del ctx[key]
        return ctx
    except Exception as e:
        logger.error(f"Error in data cleanup interceptor: {e}")
        return ctx

def data_error_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle data fetching errors."""
    try:
        error_msg = ctx.get('error', 'Unknown data error')
        logger.error(f"Data fetching error: {error_msg}")
        
        # Provide fallback data
        ctx['data'] = pd.DataFrame()
        ctx['request_valid'] = False
        
        # Clear error
        if 'error' in ctx:
            del ctx['error']
        
        return ctx
    except Exception as e:
        logger.error(f"Error in data error interceptor: {e}")
        return ctx

# ============================================================================
# VISUALIZATION INTERCEPTORS
# ============================================================================

def figure_creation_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Create visualization figure."""
    try:
        data = ctx.get('data')
        filter_state = ctx.get('filter_state')
        enrichment_state = ctx.get('enrichment_state')
        
        if data is not None and filter_state and enrichment_state:
            # Import the pure function
            from .visualization_fp import create_figure
            figure = create_figure(data, filter_state, enrichment_state)
            ctx['figure'] = figure
            ctx['figure_created'] = True
        return ctx
    except Exception as e:
        logger.error(f"Error in figure creation interceptor: {e}")
        ctx['error'] = f"Figure creation failed: {e}"
        raise

def figure_validation_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate created figure."""
    try:
        figure = ctx.get('figure')
        if figure:
            # Import the pure function
            from .visualization_fp import validate_figure
            is_valid = validate_figure(figure)
            ctx['figure_valid'] = is_valid
            if not is_valid:
                logger.warning("Invalid figure detected")
        return ctx
    except Exception as e:
        logger.error(f"Error in figure validation interceptor: {e}")
        ctx['error'] = f"Figure validation failed: {e}"
        raise

def figure_cleanup_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up figure-related temporary data."""
    try:
        # Remove temporary figure data
        for key in ['figure_created', 'figure_valid']:
            if key in ctx:
                del ctx[key]
        return ctx
    except Exception as e:
        logger.error(f"Error in figure cleanup interceptor: {e}")
        return ctx

def figure_error_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle visualization errors."""
    try:
        error_msg = ctx.get('error', 'Unknown visualization error')
        logger.error(f"Visualization error: {error_msg}")
        
        # Provide fallback figure
        ctx['figure'] = go.Figure()
        ctx['figure_valid'] = False
        
        # Clear error
        if 'error' in ctx:
            del ctx['error']
        
        return ctx
    except Exception as e:
        logger.error(f"Error in figure error interceptor: {e}")
        return ctx

# ============================================================================
# ORCHESTRATION FUNCTIONS
# ============================================================================

def orchestrate_view_update(services: Dict[str, Any], relayout_data: Dict) -> Optional[ViewState]:
    """Orchestrate view state update using interceptors."""
    try:
        # Create context
        context = {
            'relayout_data': relayout_data,
            'phase': 'view_update'
        }
        
        # Define view management interceptor stack
        view_interceptors = [
            Interceptor(enter=view_extraction_interceptor, leave=view_cleanup_interceptor, error=view_error_interceptor),
            Interceptor(enter=view_validation_interceptor, error=view_error_interceptor),
            Interceptor(enter=view_preservation_interceptor, error=view_error_interceptor)
        ]
        
        # Execute interceptor stack
        result_context = execute_interceptor_stack(view_interceptors, context)
        
        # Return view state if successful
        if result_context.get('view_valid', False):
            return result_context.get('view_state')
        return None
        
    except Exception as e:
        logger.error(f"Error orchestrating view update: {e}")
        return None

def orchestrate_data_fetch(services: Dict[str, Any], context: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Orchestrate data fetching operation using interceptors."""
    try:
        # Add phase information
        context['phase'] = 'data_fetch'
        
        # Define data fetching interceptor stack
        data_interceptors = [
            Interceptor(enter=data_request_interceptor, leave=data_cleanup_interceptor, error=data_error_interceptor),
            Interceptor(enter=data_validation_interceptor, error=data_error_interceptor),
            Interceptor(enter=data_fetch_interceptor, error=data_error_interceptor)
        ]
        
        # Execute interceptor stack
        result_context = execute_interceptor_stack(data_interceptors, context)
        
        # Return data if successful
        if result_context.get('data_fetched', False):
            return result_context.get('data')
        return None
        
    except Exception as e:
        logger.error(f"Error orchestrating data fetch: {e}")
        return None

def orchestrate_visualization(services: Dict[str, Any], data: pd.DataFrame, 
                             context: Dict[str, Any]) -> go.Figure:
    """Orchestrate visualization creation using interceptors."""
    try:
        # Add data and phase information
        context['data'] = data
        context['phase'] = 'visualization'
        
        # Define visualization interceptor stack
        viz_interceptors = [
            Interceptor(enter=figure_creation_interceptor, leave=figure_cleanup_interceptor, error=figure_error_interceptor),
            Interceptor(enter=figure_validation_interceptor, error=figure_error_interceptor)
        ]
        
        # Execute interceptor stack
        result_context = execute_interceptor_stack(viz_interceptors, context)
        
        # Return figure if successful
        if result_context.get('figure_valid', False):
            return result_context.get('figure')
        
        # Return fallback figure
        return go.Figure()
        
    except Exception as e:
        logger.error(f"Error orchestrating visualization: {e}")
        return go.Figure()

def orchestrate_complete_workflow(services: Dict[str, Any], workflow_context: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrate complete workflow from view update to visualization."""
    try:
        # Phase 1: View Management
        if 'relayout_data' in workflow_context:
            view_state = orchestrate_view_update(services, workflow_context['relayout_data'])
            if view_state:
                workflow_context['view_state'] = view_state
        
        # Phase 2: Data Fetching
        if workflow_context.get('view_state') and workflow_context.get('filter_state'):
            data = orchestrate_data_fetch(services, workflow_context)
            if data is not None:
                workflow_context['data'] = data
        
        # Phase 3: Visualization
        if workflow_context.get('data') is not None:
            figure = orchestrate_visualization(services, workflow_context['data'], workflow_context)
            workflow_context['figure'] = figure
        
        return workflow_context
        
    except Exception as e:
        logger.error(f"Error orchestrating complete workflow: {e}")
        workflow_context['error'] = str(e)
        return workflow_context
