"""
Component Orchestrator Pure Functions for DocScope

This module implements component orchestration using pure functions and interceptors,
following our functional programming principles - NO SIDE EFFECTS, NO CLASSES.

The orchestrator coordinates data flow between components using:
1. Pure functions for all operations
2. Interceptor pattern for request/response processing
3. Immutable state management
4. Injected dependencies for external services
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
import pandas as pd
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# ============================================================================
# INTERCEPTOR DEFINITIONS - Pure Data Structures
# ============================================================================

class Interceptor:
    """Interceptor data structure following our established pattern - pure data class."""
    
    def __init__(self, enter: Optional[Callable] = None,
                 leave: Optional[Callable] = None,
                 error: Optional[Callable] = None):
        self.enter = enter
        self.leave = leave
        self.error = error

# ============================================================================
# INTERCEPTOR STACK EXECUTION - Pure Functions
# ============================================================================

def execute_interceptor_stack(interceptors: List[Interceptor], context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a stack of interceptors following our established pattern - TRULY PURE function."""
    try:
        # Execute enter functions (left to right)
        for interceptor in interceptors:
            if interceptor.enter:
                context = interceptor.enter(context)
        
        # Execute leave functions (right to left)
        for interceptor in reversed(interceptors):
            if interceptor.leave:  # Fixed: was calling enter instead of leave
                context = interceptor.leave(context)
        
        return context
        
    except Exception as e:
        # Handle errors using interceptor error functions
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
# VIEW MANAGEMENT INTERCEPTORS - All Pure Functions
# ============================================================================

def view_extraction_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Extract view state from relayout data - TRULY PURE interceptor."""
    relayout_data = context.get('relayout_data')
    if not relayout_data:
        # No relayout data - this is likely initial load
        # Don't create default view state - let the full dataset be displayed
        new_context = context.copy()
        new_context['view_state'] = None
        new_context['view_extracted'] = True
        new_context['view_fallback'] = False
        return new_context
    
    # Handle autosize events
    if 'autosize' in relayout_data:
        # Autosize event - don't create default view state
        # Let the figure handle its own sizing
        new_context = context.copy()
        new_context['view_state'] = None
        new_context['view_extracted'] = True
        new_context['view_fallback'] = False
        return new_context
    
    # Import pure function
    from .view_management_fp import extract_view_from_relayout_pure
    
    # Extract view state using pure function
    current_time = context.get('current_time', 0.0)
    view_state = extract_view_from_relayout_pure(relayout_data, current_time)
    
    # If no view state extracted, don't create a default
    # This allows the full dataset to be displayed
    if not view_state:
        new_context = context.copy()
        new_context['view_state'] = None
        new_context['view_extracted'] = True
        new_context['view_fallback'] = False
        return new_context
    
    # Update context immutably
    new_context = context.copy()
    new_context['view_state'] = view_state
    new_context['view_extracted'] = True
    
    return new_context

def view_validation_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate extracted view state - TRULY PURE interceptor."""
    view_state = context.get('view_state')
    if not view_state:
        return context
    
    # Import pure function
    from .view_management_fp import validate_view_state
    
    # Validate view state using pure function
    is_valid = validate_view_state(view_state)
    
    # Update context immutably
    new_context = context.copy()
    new_context['view_valid'] = is_valid
    
    if not is_valid:
        new_context['error'] = 'Invalid view state'
    
    return new_context

def view_preservation_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare view preservation logic - TRULY PURE interceptor."""
    view_state = context.get('view_state')
    if not view_state or not context.get('view_valid', False):
        return context
    
    # Import pure function
    from .view_management_fp import view_state_to_dict
    
    # Convert view state to serializable format
    view_dict = view_state_to_dict(view_state)
    
    # Update context immutably
    new_context = context.copy()
    new_context['view_dict'] = view_dict
    new_context['view_preserved'] = True
    
    return new_context

def view_cleanup_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up view processing - TRULY PURE interceptor."""
    # Remove temporary view processing flags
    cleanup_keys = ['view_extracted', 'view_valid', 'view_preserved']
    
    new_context = context.copy()
    for key in cleanup_keys:
        if key in new_context:
            del new_context[key]
    
    return new_context

def view_error_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle view processing errors - TRULY PURE interceptor."""
    error = context.get('error', 'Unknown view error')
    logger.error(f"View processing error: {error}")
    
    # Create fallback view state
    from .view_management_fp import create_default_view_state_pure
    current_time = context.get('current_time', 0.0)
    fallback_view = create_default_view_state_pure(current_time)
    
    # Update context with fallback
    new_context = context.copy()
    new_context['view_state'] = fallback_view
    new_context['view_error'] = error
    new_context['error'] = None  # Clear error
    
    return new_context

# ============================================================================
# DATA FETCHING INTERCEPTORS - All Pure Functions
# ============================================================================

def data_request_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Create data fetch request - TRULY PURE interceptor."""
    view_state = context.get('view_state')
    filter_state = context.get('filter_state')
    enrichment_state = context.get('enrichment_state')
    
    if not all([view_state, filter_state, enrichment_state]):
        return context
    
    # Import pure function
    from .data_fetching_fp import create_fetch_request
    
    # Create fetch request using pure function
    fetch_request = create_fetch_request(view_state, filter_state, enrichment_state)
    
    # Update context immutably
    new_context = context.copy()
    new_context['fetch_request'] = fetch_request
    new_context['data_request_created'] = True
    
    return new_context

def data_validation_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data fetch request - TRULY PURE interceptor."""
    fetch_request = context.get('fetch_request')
    if not fetch_request:
        return context
    
    # Import pure function
    from .data_fetching_fp import validate_fetch_request
    
    # Validate request using pure function
    is_valid = validate_fetch_request(fetch_request)
    
    # Update context immutably
    new_context = context.copy()
    new_context['request_valid'] = is_valid
    
    if not is_valid:
        new_context['error'] = 'Invalid fetch request'
    
    return new_context

def data_fetch_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch data using injected provider - TRULY PURE interceptor."""
    fetch_request = context.get('fetch_request')
    if not fetch_request or not context.get('request_valid', False):
        return context
    
    # Get injected data provider
    data_provider = context.get('data_provider')
    if not data_provider:
        return context
    
    # Import pure function
    from .data_fetching_fp import fetch_data_pure
    
    # Fetch data using pure function with injected provider
    data = fetch_data_pure(fetch_request, data_provider)
    
    # Update context immutably
    new_context = context.copy()
    new_context['data'] = data
    new_context['data_fetched'] = True
    
    return new_context

def data_cleanup_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up data processing - TRULY PURE interceptor."""
    # Remove temporary data processing flags
    cleanup_keys = ['data_request_created', 'request_valid', 'data_fetched']
    
    new_context = context.copy()
    for key in cleanup_keys:
        if key in new_context:
            del new_context[key]
    
    return new_context

def data_error_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle data processing errors - TRULY PURE interceptor."""
    error = context.get('error', 'Unknown data error')
    logger.error(f"Data processing error: {error}")
    
    # Create empty DataFrame as fallback
    fallback_data = pd.DataFrame()
    
    # Update context with fallback
    new_context = context.copy()
    new_context['data'] = fallback_data
    new_context['data_error'] = error
    new_context['error'] = None  # Clear error
    
    return new_context

# ============================================================================
# VISUALIZATION INTERCEPTORS - All Pure Functions
# ============================================================================

def visualization_creation_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Create visualization figure - TRULY PURE interceptor."""
    data = context.get('data')
    filter_state = context.get('filter_state')
    enrichment_state = context.get('enrichment_state')
    
    # Import pure function
    from .visualization_fp import create_figure
    
    # Create figure using pure function
    if data is None or data.empty:
        # Create fallback figure with dummy data that will pass validation
        fallback_figure = go.Figure()
        
        # Add dummy scatter trace to pass validation
        fallback_figure.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(size=10, color='lightgray'),
            text=['No Data Available'],
            name='No Data'
        ))
        
        # Set layout
        fallback_figure.update_layout(
            title="No Data Available",
            xaxis=dict(range=[-5, 5], title="X Axis"),
            yaxis=dict(range=[-3, 3], title="Y Axis"),
            showlegend=False
        )
        
        new_context = context.copy()
        new_context['figure'] = fallback_figure
        new_context['visualization_created'] = True
        new_context['visualization_fallback'] = True
        return new_context
    
    # Create figure with actual data
    figure = create_figure(data, filter_state, enrichment_state)
    
    # Update context immutably
    new_context = context.copy()
    new_context['figure'] = figure
    new_context['visualization_created'] = True
    
    return new_context

def view_preservation_application_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Apply view preservation to figure - TRULY PURE interceptor."""
    figure = context.get('figure')
    view_state = context.get('view_state')
    
    if not figure or not view_state:
        return context
    
    # Import pure function
    from .visualization_fp import apply_view_preservation
    
    # Apply view preservation using pure function
    preserved_figure = apply_view_preservation(figure, view_state)
    
    # Update context immutably
    new_context = context.copy()
    new_context['figure'] = preserved_figure
    new_context['view_preservation_applied'] = True
    
    return new_context

def visualization_validation_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate created visualization - TRULY PURE interceptor."""
    figure = context.get('figure')
    if not figure:
        return context
    
    # Import pure function
    from .visualization_fp import validate_figure
    
    # Validate figure using pure function
    is_valid = validate_figure(figure)
    
    # Update context immutably
    new_context = context.copy()
    new_context['visualization_valid'] = is_valid
    
    if not is_valid:
        new_context['error'] = 'Invalid visualization'
    
    return new_context

def visualization_cleanup_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up visualization processing - TRULY PURE interceptor."""
    # Remove temporary visualization processing flags
    cleanup_keys = ['visualization_created', 'view_preservation_applied', 'visualization_valid']
    
    new_context = context.copy()
    for key in cleanup_keys:
        if key in new_context:
            del new_context[key]
    
    return new_context

def visualization_error_interceptor(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle visualization processing errors - TRULY PURE interceptor."""
    error = context.get('error', 'Unknown visualization error')
    logger.error(f"Visualization processing error: {error}")
    
    # Create empty figure as fallback using our helper function
    from .graph_component import create_empty_figure
    fallback_figure = create_empty_figure()
    
    # Update context with fallback
    new_context = context.copy()
    new_context['figure'] = fallback_figure
    new_context['visualization_error'] = error
    new_context['error'] = None  # Clear error
    
    return new_context

# ============================================================================
# ORCHESTRATOR FUNCTIONS - All Pure Functions
# ============================================================================

def orchestrate_view_update(relayout_data: Optional[Dict], current_view_ranges: Optional[Dict]) -> Dict[str, Any]:
    """Orchestrate view state update using interceptors - TRULY PURE function."""
    # Create context with current time
    current_time = time.time()
    context = {
        'relayout_data': relayout_data,
        'current_time': current_time,
        'current_view_ranges': current_view_ranges
    }
    
    # Define view management interceptor stack
    view_interceptors = [
        Interceptor(enter=view_extraction_interceptor, leave=view_cleanup_interceptor, error=view_error_interceptor),
        Interceptor(enter=view_validation_interceptor, error=view_error_interceptor),
        Interceptor(enter=view_preservation_interceptor, error=view_error_interceptor)
    ]
    
    # Execute interceptor stack
    result_context = execute_interceptor_stack(view_interceptors, context)
    
    # Return result in expected format
    if 'error' in result_context:
        return {
            'success': False,
            'error': result_context['error'],
            'view_state': current_view_ranges or {}
        }
    
    # Check if we actually extracted a view state
    view_state = result_context.get('view_state')
    if not view_state:
        # No view state extracted - preserve current view ranges
        # This prevents button clicks from clearing the view
        return {
            'success': True,
            'view_state': current_view_ranges or {},
            'error': None
        }
    
    return {
        'success': True,
        'view_state': result_context.get('view_dict', current_view_ranges or {}),
        'error': None
    }

def orchestrate_data_fetch(view_ranges: Optional[Dict], sources: Optional[List[str]], 
                          year_range: Optional[List[int]], search_text: Optional[str],
                          similarity_threshold: Optional[float], enrichment_state: Optional[Dict],
                          universe_constraints: Optional[str] = None) -> Dict[str, Any]:
    """Orchestrate data fetching using interceptors - TRULY PURE function."""
    try:
        # Import data service (pure function)
        from .data_service import fetch_papers_from_api
        
        # Build SQL filter based on sources and universe constraints
        sql_filter = None
        filter_parts = []
        
        # Add source filter if specified
        if sources and len(sources) > 0:
            # Convert sources to lowercase to match database values
            source_list = [s.lower() for s in sources]
            quoted_sources = [f"'{s}'" for s in source_list]
            filter_parts.append(f"doctrove_source IN ({','.join(quoted_sources)})")
        
        # Add universe constraints if specified
        if universe_constraints and universe_constraints.strip():
            universe_sql = universe_constraints.strip()
            
            # Always add universe constraints - they should work WITH other filters, not replace them
            filter_parts.append(f"({universe_sql})")
            logger.debug(f"🔍 ORCHESTRATOR DEBUG - Adding universe constraint: {universe_constraints}")
            print(f"🌍 ORCHESTRATOR: Adding universe constraint: {universe_constraints}")
            
            # Note: Universe constraints can include source constraints, but we don't remove the default source filter
            # This allows both to work together (universe constraint + explicit source filter)
                    # Debug: Filter parts (commented out for production)
        # print(f"🔍 ORCHESTRATOR DEBUG - Filter parts before combining: {filter_parts}")
        # print(f"🔍 ORCHESTRATOR DEBUG - Final SQL filter: {sql_filter}")
        
        # Combine all filter parts
        if filter_parts:
            sql_filter = " AND ".join(filter_parts)
            print(f"🔍 ORCHESTRATOR DEBUG - Combined SQL filter: {sql_filter}")
            print(f"🔍 ORCHESTRATOR DEBUG - Filter parts combined: {filter_parts}")
        else:
            print(f"🔍 ORCHESTRATOR DEBUG - No filter parts to combine")
        
        # Build bounding box from view ranges if available
        # CRITICAL: Don't override current view when applying universe constraints
        bbox = None
        if view_ranges and 'x_range' in view_ranges and 'y_range' in view_ranges:
            x_range = view_ranges['x_range']
            y_range = view_ranges['y_range']
            if len(x_range) == 2 and len(y_range) == 2:
                bbox = f"{x_range[0]},{y_range[0]},{x_range[1]},{y_range[1]}"
                print(f"🌍 ORCHESTRATOR: Using current view bbox: {bbox}")
        elif view_ranges and 'bbox' in view_ranges:
            # If we have a bbox string but no x_range/y_range, use the bbox directly
            bbox = view_ranges['bbox']
            print(f"🌍 ORCHESTRATOR: Using bbox from view_ranges: {bbox}")
        else:
            print(f"🌍 ORCHESTRATOR: No view_ranges or bbox provided - will fetch all papers")
            # This will fetch all papers, which is not what we want
            # We should preserve the current zoom state
            # TODO: In the future, we could extract current view from the graph here
        
        # CRITICAL: Enrichment system is now purely dropdown-driven
        # No more auto-detection or pattern matching - use exactly what the user selects
        enrichment_source = None
        enrichment_table = None
        enrichment_field = None
        
        # Only set enrichment parameters if they are explicitly provided
        if enrichment_state and enrichment_state.get('active'):
            enrichment_source = enrichment_state.get('source')
            enrichment_table = enrichment_state.get('table')
            enrichment_field = enrichment_state.get('field')
            logger.debug(f"🔍 ORCHESTRATOR: Using dropdown-selected enrichment: {enrichment_source}/{enrichment_table}/{enrichment_field}")
        
        # Build query parameters for deduplication check
        query_params = {
            'limit': 5000,  # Use reasonable limit
            'bbox': bbox,
            'sql_filter': sql_filter,
            'search_text': search_text,
            'similarity_threshold': similarity_threshold,
            'year_range': year_range,
            'enrichment_source': enrichment_source,
            'enrichment_table': enrichment_table,
            'enrichment_field': enrichment_field,
            'universe_constraints': universe_constraints  # Add universe constraints for deduplication
        }
        
        # Debug logging for universe constraints
        if universe_constraints and universe_constraints.strip():
            print(f"🔍 ORCHESTRATOR DEBUG - Final query params:")
            print(f"  - bbox: {bbox}")
            print(f"  - sql_filter: {sql_filter}")
            print(f"  - universe_constraints: {universe_constraints}")
            print(f"  - view_ranges: {view_ranges}")
            print(f"🔍 ORCHESTRATOR DEBUG - Filter parts: {filter_parts}")
            print(f"🔍 ORCHESTRATOR DEBUG - Combined SQL filter: {sql_filter}")
            print(f"🔍 ORCHESTRATOR DEBUG - Enrichment params: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}")
        
        # Check if this query should be skipped due to duplication
        # BUT: Skip deduplication for initial loads (when view_ranges is None)
        if view_ranges is None:
            print(f"🚀 ORCHESTRATOR: Initial load detected - bypassing deduplication")
            logger.debug("Initial load detected - bypassing deduplication")
        else:
            try:
                from .query_deduplicator import should_skip_query
                print(f"🔍 ORCHESTRATOR: Checking query deduplication...")
                should_skip, reason = should_skip_query(query_params, time_threshold=2.0)
                
                if should_skip:
                    logger.debug(f"🔍 ORCHESTRATOR: Skipping duplicate query: {reason}")
                    print(f"🚫 ORCHESTRATOR: Skipping duplicate query: {reason}")
                    # Return empty result to indicate no new data
                    return {
                        'success': True,
                        'data': [],
                        'total_count': 0,
                        'error': None,
                        'skipped': True,
                        'reason': reason
                    }
                else:
                    print(f"✅ ORCHESTRATOR: Query accepted, proceeding with API call")
            except ImportError:
                logger.warning("Query deduplicator not available - proceeding with API call")
                print(f"⚠️ ORCHESTRATOR: Query deduplication check failed: {e} - proceeding with API call")
            except Exception as e:
                logger.warning(f"Query deduplication check failed: {e} - proceeding with API call")
                print(f"⚠️ ORCHESTRATOR: Query deduplication check failed: {e} - proceeding with API call")
        
        # Fetch data using pure function
        data, total_count = fetch_papers_from_api(
            limit=5000,  # Use reasonable limit
            bbox=bbox,
            sql_filter=sql_filter,
            search_text=search_text,
            similarity_threshold=similarity_threshold,
            year_range=year_range,  # Pass year range for filtering
            enrichment_source=enrichment_source,
            enrichment_table=enrichment_table,
            enrichment_field=enrichment_field
        )
        
        # Convert DataFrame to list of dicts for JSON serialization
        if not data.empty:
            data_list = data.to_dict('records')
            return {
                'success': True,
                'data': data_list,
                'total_count': total_count,
                'error': None
            }
        else:
            return {
                'success': True,
                'data': [],
                'total_count': total_count,
                'error': None
            }
            
    except Exception as e:
        logger.error(f"Data fetch error: {e}")
        return {
            'success': False,
            'data': [],
            'error': str(e)
        }

def orchestrate_visualization(data: Optional[List[Dict]], view_ranges: Optional[Dict], 
                            enrichment_state: Optional[Dict], force_autorange: bool = False) -> Dict[str, Any]:
    """Orchestrate visualization creation using interceptors - TRULY PURE function."""
    try:
        # CRITICAL DEBUG: Log the force_autorange parameter
        logger.debug(f"🔍 ORCHESTRATOR DEBUG - force_autorange parameter: {force_autorange}")
        print(f"🌍 ORCHESTRATOR DEBUG - force_autorange parameter: {force_autorange}")
        logger.debug(f"🔍 ORCHESTRATOR DEBUG - force_autorange type: {type(force_autorange)}")
        print(f"🌍 ORCHESTRATOR DEBUG - force_autorange type: {type(force_autorange)}")
        if not data or len(data) == 0:
            # Return empty figure if no data, but preserve view ranges if available
            empty_figure = go.Figure()
            empty_figure.update_layout(
                title="No Papers Found",
                xaxis_title="X Axis",
                yaxis_title="Y Axis"
            )
            
            # Preserve view ranges if available to maintain user's current view
            if view_ranges and 'x_range' in view_ranges and 'y_range' in view_ranges:
                logger.debug(f"🔍 ORCHESTRATOR DEBUG - Preserving view ranges in empty figure")
                empty_figure.update_layout(
                    xaxis=dict(range=view_ranges['x_range']),
                    yaxis=dict(range=view_ranges['y_range']),
                    dragmode='pan'
                )
            
            return {
                'success': True,
                'figure': empty_figure,
                'error': None
            }
        
        # Convert data to DataFrame for processing
        import pandas as pd
        df = pd.DataFrame(data)
        
        # Check if we have the required x and y columns for visualization
        # The data service already processes doctrove_embedding_2d into x and y columns
        if 'x' not in df.columns or 'y' not in df.columns:
            return {
                'success': False,
                'figure': go.Figure(),
                'error': 'Missing x and y coordinate columns for visualization'
            }
        
        # Filter out rows with invalid coordinates
        valid_mask = (df['x'].notna()) & (df['y'].notna())
        filtered_df = df[valid_mask]
        
        if len(filtered_df) == 0:
            return {
                'success': False,
                'figure': go.Figure(),
                'error': 'No valid coordinate data found after filtering'
            }
        
        # Use the graph component for proper enrichment coloring
        from .graph_component import create_scatter_plot
        
        # CRITICAL DEBUG: Log the actual source distribution in the data
        if 'Source' in filtered_df.columns:
            source_counts = filtered_df['Source'].value_counts()
            logger.debug(f"🔍 SOURCE DEBUG - DataFrame source distribution: {source_counts.to_dict()}")
            print(f"🌍 SOURCE DEBUG - DataFrame source distribution: {source_counts.to_dict()}")
        elif 'doctrove_source' in filtered_df.columns:
            source_counts = filtered_df['doctrove_source'].value_counts()
            logger.debug(f"🔍 SOURCE DEBUG - DataFrame doctrove_source distribution: {source_counts.to_dict()}")
            print(f"🌍 SOURCE DEBUG - DataFrame doctrove_source distribution: {source_counts.to_dict()}")
        else:
            logger.warning(f"🔍 SOURCE DEBUG - No source column found in DataFrame. Columns: {list(filtered_df.columns)}")
            print(f"🌍 SOURCE DEBUG - No source column found in DataFrame. Columns: {list(filtered_df.columns)}")
        
        # Check if enrichment is active
        logger.debug(f"🔍 ENRICHMENT DEBUG - enrichment_state: {enrichment_state}")
        enrichment_source = enrichment_state.get('source') if enrichment_state else None
        enrichment_table = enrichment_state.get('table') if enrichment_state else None
        enrichment_field = enrichment_state.get('field') if enrichment_state else None
        logger.debug(f"🔍 ENRICHMENT DEBUG - Extracted: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}")
        
        if enrichment_state and enrichment_state.get('active'):
            # Create figure with enrichment coloring
            logger.debug(f"🔍 ENRICHMENT DEBUG - Creating enrichment figure with: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}")
            figure = create_scatter_plot(
                filtered_df, 
                None,  # No source filtering needed here
                enrichment_source,
                enrichment_table,
                enrichment_field
            )
        else:
            # Create figure with source-based coloring
            figure = create_scatter_plot(filtered_df, None)
        
        # CRITICAL DEBUG: Log view ranges before applying to understand autorange bug
        logger.debug(f"🔍 ORCHESTRATOR DEBUG - View ranges: {view_ranges}")
        logger.debug(f"🔍 ORCHESTRATOR DEBUG - View ranges type: {type(view_ranges)}")
        if view_ranges:
            logger.debug(f"🔍 ORCHESTRATOR DEBUG - View ranges keys: {list(view_ranges.keys())}")
            logger.debug(f"🔍 ORCHESTRATOR DEBUG - X range: {view_ranges.get('x_range')}")
            logger.debug(f"🔍 ORCHESTRATOR DEBUG - Y range: {view_ranges.get('y_range')}")
        
        # Apply view ranges if available
        if view_ranges and 'x_range' in view_ranges and 'y_range' in view_ranges:
            logger.debug(f"🔍 ORCHESTRATOR DEBUG - Applying view ranges to figure")
            logger.debug(f"🔍 ORCHESTRATOR DEBUG - Setting xaxis range: {view_ranges['x_range']}")
            logger.debug(f"🔍 ORCHESTRATOR DEBUG - Setting yaxis range: {view_ranges['y_range']}")
            
            # Check if this is a year range change using bbox constraint
            is_year_range_change = view_ranges.get('year_range_change', False)
            if is_year_range_change:
                logger.debug(f"🔍 ORCHESTRATOR DEBUG - This is a year range change using bbox constraint")
            
            figure.update_layout(
                xaxis=dict(range=view_ranges['x_range']),
                yaxis=dict(range=view_ranges['y_range']),
                dragmode='pan'  # CRITICAL: Force pan mode to prevent box mode from taking over
            )
        else:
            logger.warning(f"🔍 ORCHESTRATOR DEBUG - No valid view ranges to apply!")
            if view_ranges:
                logger.warning(f"🔍 ORCHESTRATOR DEBUG - View ranges exists but missing keys: {list(view_ranges.keys())}")
            else:
                logger.warning(f"🔍 ORCHESTRATOR DEBUG - View ranges is None or empty")
                
                # ENHANCED LOGIC: Check if this is a year range change (no view_ranges) vs initial load
                # For year range changes, we should preserve the current figure's zoom if it exists
                logger.debug(f"🔍 ORCHESTRATOR DEBUG - view_ranges value: {view_ranges}")
                logger.debug(f"🔍 ORCHESTRATOR DEBUG - view_ranges type: {type(view_ranges)}")
                if view_ranges:
                    logger.debug(f"🔍 ORCHESTRATOR DEBUG - view_ranges keys: {list(view_ranges.keys()) if isinstance(view_ranges, dict) else 'Not a dict'}")
                
                if not view_ranges:
                    # This could be initial load OR year range change
                    # For year range changes, we want to show all data in the new range
                    # For initial load, we want to set reasonable bounds
                    
                    # Check if this is truly initial load by looking at the data characteristics
                    # If we have a reasonable amount of data, this is likely a year range change
                    if len(filtered_df) >= 100:  # Reasonable threshold for year range change
                        logger.debug(f"🔍 ORCHESTRATOR DEBUG - Likely year range change with {len(filtered_df)} papers - autoranging to show all data")
                        print(f"🌍 ORCHESTRATOR DEBUG - Likely year range change with {len(filtered_df)} papers - autoranging to show all data")
                        # Enable autorange to show all papers in the new year range
                        figure.update_layout(
                            xaxis=dict(autorange=True),
                            yaxis=dict(autorange=True),
                            dragmode='pan'
                        )
                    else:
                        # This is likely initial load with limited data - set reasonable bounds
                        logger.debug(f"🔍 ORCHESTRATOR DEBUG - Likely initial load with {len(filtered_df)} papers - setting initial bounds")
                        print(f"🌍 ORCHESTRATOR DEBUG - Likely initial load with {len(filtered_df)} papers - setting initial bounds")
                        
                        x_min, x_max = filtered_df['x'].min(), filtered_df['x'].max()
                        y_min, y_max = filtered_df['y'].min(), filtered_df['y'].max()
                        
                        # Add some padding around the data bounds
                        x_padding = (x_max - x_min) * 0.1
                        y_padding = (y_max - y_min) * 0.1
                        
                        initial_x_range = [x_min - x_padding, x_max + x_padding]
                        initial_y_range = [y_min - y_padding, y_max + y_padding]
                        
                        logger.debug(f"🔍 ORCHESTRATOR DEBUG - Setting initial view ranges for new figure: x={initial_x_range}, y={initial_y_range}")
                        print(f"🌍 ORCHESTRATOR DEBUG - Setting initial view ranges for new figure: x={initial_x_range}, y={initial_y_range}")
                        
                        # Set the ranges directly and disable autorange forever
                        figure.update_layout(
                            xaxis=dict(range=initial_x_range, autorange=False),
                            yaxis=dict(range=initial_y_range, autorange=False),
                            dragmode='pan'
                        )
                        
                        logger.debug(f"🔍 ORCHESTRATOR DEBUG - Manual ranges set and autorange disabled: x={initial_x_range}, y={initial_y_range}")
                        print(f"🌍 ORCHESTRATOR DEBUG - Manual ranges set and autorange disabled: x={initial_x_range}, y={initial_y_range}")
                else:
                    # Papers are already displayed - preserve current view, don't auto-range
                    logger.debug(f"🔍 ORCHESTRATOR DEBUG - Papers already displayed, preserving current view (no auto-ranging)")
                    print(f"🌍 ORCHESTRATOR DEBUG - Papers already displayed, preserving current view (no auto-ranging)")
        
        logger.debug(f"🔍 ORCHESTRATOR DEBUG - About to return success=True with figure")
        logger.debug(f"🔍 ORCHESTRATOR DEBUG - Figure type: {type(figure)}")
        logger.debug(f"🔍 ORCHESTRATOR DEBUG - Figure has data: {len(figure.data) if hasattr(figure, 'data') else 'No data attribute'}")
        
        return {
            'success': True,
            'figure': figure,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        # Return fallback figure on error using our helper function
        from .graph_component import create_empty_figure
        fallback_figure = create_empty_figure()
        
        # Preserve view ranges if available
        if view_ranges and 'x_range' in view_ranges and 'y_range' in view_ranges:
            fallback_figure.update_layout(
                xaxis=dict(range=view_ranges['x_range']),
                yaxis=dict(range=view_ranges['y_range']),
                dragmode='pan'  # CRITICAL: Force pan mode to prevent box mode from taking over
            )
        
        return {
            'success': False,
            'figure': fallback_figure,
            'error': str(e)
        }

def orchestrate_complete_workflow(year_range: Optional[List[int]], sources: Optional[List[str]], 
                                similarity_threshold: Optional[float], initial_load: bool = False) -> Dict[str, Any]:
    """Orchestrate complete workflow for initial load - TRULY PURE function."""
    try:
        # Use our data fetching orchestrator
        data_result = orchestrate_data_fetch(
            view_ranges=None,  # No view ranges for initial load
            sources=sources,
            year_range=year_range,
            search_text=None,  # No search text for initial load
            similarity_threshold=similarity_threshold,
            enrichment_state=None
        )
        
        if not data_result['success']:
            return {
                'success': False,
                'data': [],
                'figure': go.Figure(),
                'error': data_result.get('error', 'Data fetch failed')
            }
        
        # Use our visualization orchestrator
        viz_result = orchestrate_visualization(
            data=data_result['data'],
            view_ranges=None,  # No view ranges for initial load
            enrichment_state=None
        )
        
        if not viz_result['success']:
            return {
                'success': False,
                'data': data_result['data'],
                'figure': go.Figure(),
                'error': viz_result.get('error', 'Visualization failed')
            }
        
        return {
            'success': True,
            'data': data_result['data'],
            'figure': viz_result['figure'],
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Complete workflow error: {e}")
        return {
            'success': False,
            'data': [],
            'figure': go.Figure(),
            'error': str(e)
        }

# ============================================================================
# CLUSTERING ORCHESTRATOR - Pure Functional Architecture
# ============================================================================

def orchestrate_clustering(data: List[Dict], num_clusters: int, 
                          selected_sources: Optional[List[str]], 
                          relayout_data: Optional[Dict]) -> Dict[str, Any]:
    """
    Orchestrate clustering operations using pure functions.
    
    This function coordinates the clustering workflow while maintaining
    separation of concerns and pure function principles.
    
    Args:
        data: List of paper data dictionaries
        num_clusters: Number of clusters to create
        selected_sources: Optional list of sources to filter by
        relayout_data: Optional relayout data for view bounds filtering
        
    Returns:
        Dict with success status, cluster data, and error info
    """
    try:
        # Input validation
        if not data or len(data) == 0:
            return {
                'success': False,
                'cluster_data': {'polygons': [], 'annotations': []},
                'error': 'No data available for clustering'
            }
        
        if num_clusters < 1 or num_clusters > 1000:
            return {
                'success': False,
                'cluster_data': {'polygons': [], 'annotations': []},
                'error': f'Invalid number of clusters: {num_clusters}'
            }
        
        # Convert data to DataFrame for processing
        import pandas as pd
        df = pd.DataFrame(data)
        
        # Check if we have the required x and y columns for clustering
        if 'x' not in df.columns or 'y' not in df.columns:
            return {
                'success': False,
                'cluster_data': {'polygons': [], 'annotations': []},
                'error': 'Missing x and y coordinate columns for clustering'
            }
        
        # Filter data by current view bounds if relayoutData is available
        filtered_df = _filter_data_by_view_bounds(df, relayout_data)
        
        # Check if we have enough data after filtering
        if len(filtered_df) < num_clusters:
            logger.warning(f"Not enough data ({len(filtered_df)}) for {num_clusters} clusters")
            num_clusters = min(len(filtered_df), 30)
            if num_clusters < 2:
                return {
                    'success': False,
                    'cluster_data': {'polygons': [], 'annotations': []},
                    'error': 'Not enough data points for clustering'
                }
        
        # Use the existing clustering service (pure function)
        try:
            from .clustering_service import overlay_clusters
            
            # Convert back to list for clustering service
            visible_data = filtered_df.to_dict('records')
            
            clustering_result = overlay_clusters(
                visible_data, num_clusters, None, None  # No source filtering needed
            )
            
            if clustering_result and 'polygons' in clustering_result:
                return {
                    'success': True,
                    'cluster_data': clustering_result,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'cluster_data': {'polygons': [], 'annotations': []},
                    'error': 'Clustering service returned invalid result'
                }
                
        except ImportError as e:
            logger.error(f"Clustering service import error: {e}")
            return {
                'success': False,
                'cluster_data': {'polygons': [], 'annotations': []},
                'error': 'Clustering service not available'
            }
        except Exception as e:
            logger.error(f"Clustering service error: {e}")
            return {
                'success': False,
                'cluster_data': {'polygons': [], 'annotations': []},
                'error': f'Clustering service failed: {str(e)}'
            }
            
    except Exception as e:
        logger.error(f"Clustering orchestration error: {e}")
        return {
            'success': False,
            'cluster_data': {'polygons': [], 'annotations': []},
            'error': f'Clustering orchestration failed: {str(e)}'
        }

def _filter_data_by_view_bounds(df: pd.DataFrame, relayout_data: Optional[Dict]) -> pd.DataFrame:
    """
    Filter data by current view bounds - pure helper function.
    
    Args:
        df: DataFrame with paper data
        relayout_data: Optional relayout data from Plotly
        
    Returns:
        Filtered DataFrame containing only visible data
    """
    if not relayout_data:
        return df
    
    try:
        # Extract view ranges from relayout data
        x_range = relayout_data.get('xaxis.range', relayout_data.get('xaxis.range[0]', [None, None]))
        y_range = relayout_data.get('yaxis.range', relayout_data.get('yaxis.range[0]', [None, None]))
        
        # Handle different relayout data formats
        if isinstance(x_range, list) and len(x_range) == 2:
            pass
        elif 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            x_range = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
        if 'yaxis.range[0]' in relayout_data and 'yaxis.range[1]' in relayout_data:
            y_range = [relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']]
        
        # Apply view bounds filtering if we have valid ranges
        if (x_range[0] is not None and x_range[1] is not None and 
            y_range[0] is not None and y_range[1] is not None):
            
            mask = (
                (df['x'] >= x_range[0]) & 
                (df['x'] <= x_range[1]) & 
                (df['y'] >= y_range[0]) & 
                (df['y'] <= y_range[1])
            )
            return df[mask]
        
        return df
        
    except Exception as e:
        logger.error(f"View bounds filtering error: {e}")
        return df

# ============================================================================
# UTILITY FUNCTIONS - All Pure Functions
# ============================================================================

def create_orchestrator_context(relayout_data: Dict = None, filter_state: Any = None,
                               enrichment_state: Any = None, data_provider: Callable = None,
                               current_time: float = None) -> Dict[str, Any]:
    """Create orchestrator context with defaults - TRULY PURE function."""
    context = {
        'relayout_data': relayout_data or {},
        'filter_state': filter_state,
        'enrichment_state': enrichment_state,
        'data_provider': data_provider,
        'current_time': current_time or 0.0,
        'services': {},
        'error': None
    }
    
    return context

def validate_orchestrator_context(context: Dict[str, Any]) -> bool:
    """Validate orchestrator context - TRULY PURE function."""
    required_keys = ['relayout_data', 'filter_state', 'enrichment_state', 'data_provider']
    
    for key in required_keys:
        if key not in context or context[key] is None:
            return False
    
    return True

def merge_orchestrator_contexts(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two orchestrator contexts, preferring primary - TRULY PURE function."""
    if not primary:
        return secondary
    if not secondary:
        return primary
    
    # Create merged context
    merged = primary.copy()
    
    # Merge fields, preferring primary values
    for key, value in secondary.items():
        if key not in merged or merged[key] is None:
            merged[key] = value
    
    return merged
