"""
Orchestrated callback system for DocScope using functional programming principles.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import plotly.graph_objects as go
import dash
from dash import Input, Output, State, callback_context, html, dcc
from dash.exceptions import PreventUpdate
import pandas as pd
import time
import os

# Import our orchestrator system
from .component_orchestrator_fp import (
    orchestrate_view_update,
    orchestrate_visualization,
    orchestrate_complete_workflow,
    orchestrate_clustering
)
from .component_contracts_fp import (
    FilterState, EnrichmentState
)

logger = logging.getLogger(__name__)

# Simple file logging for debug info
def log_debug_to_file(message: str):
    """Log debug message to file."""
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Write message to log file
        with open('logs/enrichment_debug.log', 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
            
    except Exception as e:
        print(f"Error writing to log file: {e}")

# Log that logging is set up
log_debug_to_file("🔧 Simple file logging setup complete for enrichment debugging")

def register_orchestrated_callbacks(app):
    """Register new callbacks using our orchestrator system."""
    
    log_debug_to_file("🚀 REGISTERING ORCHESTRATED CALLBACKS")
    log_debug_to_file("🚀 This function is being called!")
    
    # Core callbacks with single responsibilities
    
    @app.callback(
        Output('view-ranges-store', 'data', allow_duplicate=True),
        Input('graph-3', 'relayoutData'),
        State('view-ranges-store', 'data'),
        prevent_initial_call=True
    )
    def handle_view_change(relayout_data: Optional[Dict], current_view_ranges: Optional[Dict]) -> Dict:
        """
        Handle view changes (zoom/pan) - delegates to orchestrator.
        
        This callback ONLY handles view state extraction and storage.
        It does NOT fetch data or create figures.
        """
        try:
            import time
            callback_id = "handle_view_change"
            timestamp = time.time()
            debug_msg = f"🔍 VIEW CHANGE DEBUG: {callback_id} ENTERED at {timestamp:.3f}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            debug_msg = f"🔍 VIEW CHANGE DEBUG: {callback_id} - callback_context.triggered: {callback_context.triggered}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            # WRISTWATCH TIMER: Mark zoom operation start
            if relayout_data and ('xaxis.range' in str(relayout_data) or 'yaxis.range' in str(relayout_data)):
                debug_msg = f"⏱️  WRISTWATCH: ZOOM OPERATION STARTED at {timestamp:.3f}"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
            logger.info(f"View change callback triggered by: {callback_context.triggered}")
            print(f"🔍 VIEW CHANGE: Callback triggered by: {callback_context.triggered}")
            
            # Diagnostic logging to understand what's happening
            if relayout_data:
                logger.info(f"RELAYOUT DATA CONTENTS: {relayout_data}")
                logger.info(f"RELAYOUT DATA KEYS: {list(relayout_data.keys())}")
                print(f"🔍 VIEW CHANGE: Relayout data keys: {list(relayout_data.keys())}")
                
                # CRITICAL: Ignore certain relayout events that shouldn't trigger data fetches
                # These events are typically caused by UI operations, not user zoom/pan
                if 'autosize' in relayout_data:
                    logger.info("Ignoring autosize relayout event - no data fetch needed")
                    print(f"🚫 VIEW CHANGE: Ignoring autosize relayout event")
                    debug_msg = f"🔍 VIEW CHANGE DEBUG: {callback_id} - Preventing update for autosize"
                    print(debug_msg)
                    with open("/tmp/zoom_debug.log", "a") as f:
                        f.write(f"{debug_msg}\n")
                    raise dash.exceptions.PreventUpdate
                
                # Check if this is just a minor UI update (like adding clusters) rather than a view change
                if len(relayout_data) == 1 and 'dragmode' in relayout_data:
                    logger.info("Ignoring dragmode-only relayout event - no data fetch needed")
                    print(f"🚫 VIEW CHANGE: Ignoring dragmode-only relayout event")
                    debug_msg = f"🔍 VIEW CHANGE DEBUG: {callback_id} - Preventing update for dragmode"
                    print(debug_msg)
                    with open("/tmp/zoom_debug.log", "a") as f:
                        f.write(f"{debug_msg}\n")
                    raise dash.exceptions.PreventUpdate
                
                # NEW: Check if this is a clustering-related relayout event
                if 'annotations' in relayout_data or 'shapes' in relayout_data:
                    logger.info("Ignoring clustering-related relayout event - no data fetch needed")
                    print(f"🚫 VIEW CHANGE: Ignoring clustering-related relayout event")
                    debug_msg = f"🔍 VIEW CHANGE DEBUG: {callback_id} - Preventing update for clustering"
                    print(debug_msg)
                    with open("/tmp/zoom_debug.log", "a") as f:
                        f.write(f"{debug_msg}\n")
                    raise dash.exceptions.PreventUpdate
            
            # Use our orchestrator for view management
            result = orchestrate_view_update(
                relayout_data=relayout_data,
                current_view_ranges=current_view_ranges
            )
            
            if result['success']:
                logger.info("View update successful")
                debug_msg = f"🔍 VIEW CHANGE DEBUG: {callback_id} - Returning view_state: {result['view_state']}"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                return result['view_state']
            else:
                logger.warning(f"View update failed: {result.get('error', 'Unknown error')}")
                # Return current view ranges as fallback
                debug_msg = f"🔍 VIEW CHANGE DEBUG: {callback_id} - Returning fallback: {current_view_ranges or {}}"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                return current_view_ranges or {}
                
        except Exception as e:
            logger.error(f"View change callback error: {e}")
            # Return current view ranges as fallback
            return current_view_ranges or {}
    
    # Persist the last confirmed semantic query when Search is clicked
    @app.callback(
        Output('last-search-text', 'data', allow_duplicate=True),
        Input('search-button', 'n_clicks'),
        State('search-text', 'value'),
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def persist_last_search_text(n_clicks: Optional[int], search_text: Optional[str]) -> Optional[str]:
        try:
            print(f"🔍 SEARCH BUTTON DEBUG: CALLBACK TRIGGERED - n_clicks={n_clicks}, search_text='{search_text}'")
            if not n_clicks:
                print(f"🔍 SEARCH BUTTON DEBUG: No clicks, preventing update")
                raise dash.exceptions.PreventUpdate
            text = (search_text or '').strip()
            print(f"🔍 SEARCH BUTTON DEBUG: Returning text='{text}'")
            return text if text else None
        except Exception as e:
            print(f"🔍 SEARCH BUTTON DEBUG: Exception: {e}")
            raise dash.exceptions.PreventUpdate


    @app.callback(
        [Output('data-store', 'data', allow_duplicate=True),
         Output('data-metadata', 'data', allow_duplicate=True)],
        [Input('search-button', 'n_clicks'),
         Input('universe-constraints', 'data'),
         Input('selected-sources', 'data'),
         Input('year-range-slider', 'value')],
        [State('enrichment-state', 'data'),
         State('graph-3', 'figure'),
         State('search-text', 'value'),
         State('view-ranges-store', 'data'),
         State('force-autorange', 'data'),
         State('similarity-threshold', 'value')],  # Get current similarity threshold value
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def handle_data_fetch(
        search_clicks: Optional[int],  # Input parameter
        universe_constraints: Optional[str],  # Input parameter
        sources: Optional[List[str]],  # Input parameter
        year_range: Optional[List[int]],  # Input parameter
        enrichment_state: Optional[Dict],
        current_figure: Optional[Dict],
        search_text: Optional[str],
        view_ranges: Optional[Dict],   # State parameter for bbox filtering
        force_autorange: Optional[bool],   # State parameter for autorange flag
        similarity_threshold: Optional[float]  # State parameter (current value)
    ) -> Tuple[List[Dict], Dict]:
        """
        Handle data fetching - delegates to orchestrator.
        
        This callback ONLY handles data retrieval.
        It does NOT manage view state or create figures.
        """
        try:
            # UNIQUE CALLBACK ID: handle_data_fetch
            import time
            callback_id = "handle_data_fetch"
            timestamp = time.time()
            print(f"🚀 CALLBACK {callback_id} ENTERED at {timestamp}")
            print(f"🚀 CALLBACK {callback_id} - callback_context.triggered: {callback_context.triggered}")
            
            # Determine which input triggered the callback
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0] if callback_context.triggered else None

            # Whitelist triggers to prevent unintended invocations during zoom
            allowed_triggers = {
                'search-button', 'universe-constraints', 'selected-sources', 'year-range-slider'
            }
            # Also block graph-related triggers that can cause double fetches
            blocked_triggers = {
                'graph-3', 'view-ranges-store', 'data-store', 'data-metadata', 
                'enrichment-state', 'cluster-overlay', 'show-clusters'
            }
            if triggered_id and (triggered_id not in allowed_triggers or triggered_id in blocked_triggers):
                logger.info(f"handle_data_fetch: Ignoring trigger from {triggered_id} (not allowed or blocked)")
                raise dash.exceptions.PreventUpdate
            
            # Add debounce to prevent rapid successive calls
            import time as _time
            last_fetch_ts = getattr(handle_data_fetch, '_last_fetch_ts', 0.0)
            now_ts = _time.time()
            if (now_ts - last_fetch_ts) < 0.5:
                print(f"🔍 DATA FETCH DEBUG: {callback_id} - Debouncing call (last: {now_ts - last_fetch_ts:.3f}s ago)")
                logger.info(f"handle_data_fetch: Debouncing call (last: {now_ts - last_fetch_ts:.3f}s ago)")
                raise dash.exceptions.PreventUpdate
            handle_data_fetch._last_fetch_ts = now_ts
            print(f"🔍 DATA FETCH DEBUG: {callback_id} - Proceeding with data fetch")
            
            print(f"🚀 CALLBACK {callback_id} - Triggered by: {triggered_id}")
            print(f"🔍 DATA FETCH DEBUG: search_clicks={search_clicks}, triggered_id={triggered_id}")
            print(f"🔍 SEARCH CLICKS DEBUG: search_clicks={search_clicks} (type: {type(search_clicks)})")
            print(f"🔍 SEARCH TEXT DEBUG: Raw search_text='{search_text}' (type: {type(search_text)}, length: {len(search_text) if search_text else 0})")
            print(f"🔍 CALLBACK CONTEXT DEBUG: {callback_context.triggered if callback_context else 'No context'}")
            logger.info(f"Data fetch callback triggered by search button (clicks: {search_clicks})")
            logger.info(f"View ranges: {view_ranges}")
            logger.info(f"Sources: {sources}")
            logger.info(f"Year range: {year_range}")
            logger.info(f"Similarity threshold: {similarity_threshold}")
            logger.info(f"Search text: '{search_text}' (length: {len(search_text) if search_text else 0})")
            
            # CRITICAL: Skip if this is initial load (let handle_initial_load handle it)
            if triggered_id == 'url':
                print(f"🚀 CALLBACK {callback_id} - Skipping (URL change)")
                logger.info(f"Data fetch callback triggered by url change - skipping (initial load will handle)")
                raise dash.exceptions.PreventUpdate
            
            # TARGETED DISABLE: Only disable during true initial load (search_clicks is None)
            # Allow zoom/pan when search_clicks is 0 (user hasn't searched but can zoom)
            if search_clicks is None:
                print(f"🚀 CALLBACK {callback_id} - Skipping true initial load (search_clicks is None)")
                logger.info(f"Data fetch callback disabled during true initial load")
                raise dash.exceptions.PreventUpdate
            
            # REMOVED: The bbox filtering logic that was preventing zoom from working
            
            print(f"🚀 CALLBACK {callback_id} - About to proceed with data fetching...")
            logger.info(f"Data fetch callback triggered by search button (clicks: {search_clicks})")
            logger.info(f"View ranges: {view_ranges}")
            logger.info(f"Sources: {sources}")
            logger.info(f"Year range: {year_range}")
            logger.info(f"Similarity threshold: {similarity_threshold}")
            logger.info(f"Search text: {search_text}")
            
            # CRITICAL: Check for year range changes FIRST, before force_autorange check
            if triggered_id == 'year-range-slider':
                # Year range change - use the same bbox-constrained approach as zoom changes
                logger.info("🚀 YEAR RANGE CHANGE: Using bbox-constrained data fetching like zoom changes")
                
                # CRITICAL: Clear force_autorange flag for year range changes so bbox extraction works
                if force_autorange:
                    logger.info("🚀 YEAR RANGE CHANGE: Clearing force_autorange flag to enable bbox extraction")
                    force_autorange = False
                
                # Extract current bbox from the graph to use for data fetching
                if current_figure and 'layout' in current_figure and 'xaxis' in current_figure['layout'] and 'yaxis' in current_figure['layout']:
                    x_range = current_figure['layout']['xaxis'].get('range')
                    y_range = current_figure['layout']['yaxis'].get('range')
                    
                    if x_range and y_range and len(x_range) == 2 and len(y_range) == 2:
                        # Use current bbox for data fetching (same as zoom changes)
                        view_ranges = {
                            'x_range': x_range,
                            'y_range': y_range,
                            'bbox': f"{x_range[0]},{y_range[0]},{x_range[1]},{y_range[1]}",
                            'is_zoomed': True,
                            'last_update': time.time(),
                            'year_range_change': True  # Flag to indicate this is year range change
                        }
                        logger.info(f"Using current bbox for year range change: bbox={view_ranges['bbox']}")
                    else:
                        logger.info("No valid zoom ranges for bbox constraint in year range change")
                        view_ranges = None
                else:
                    logger.info("No current figure available for bbox constraint in year range change")
                    view_ranges = None
            
            # CRITICAL: Handle semantic search triggers - preserve current bbox
            elif triggered_id == 'search-button':
                logger.info(f"🚀 SEMANTIC SEARCH: Preserving current bbox for {triggered_id}")
                
                # CRITICAL: Clear force_autorange flag for semantic search so bbox extraction works
                if force_autorange:
                    logger.info("🚀 SEMANTIC SEARCH: Clearing force_autorange flag to enable bbox extraction")
                    force_autorange = False
                
                # Extract current bbox from the graph to preserve user's view
                if current_figure and 'layout' in current_figure and 'xaxis' in current_figure['layout'] and 'yaxis' in current_figure['layout']:
                    x_range = current_figure['layout']['xaxis'].get('range')
                    y_range = current_figure['layout']['yaxis'].get('range')
                    
                    if x_range and y_range and len(x_range) == 2 and len(y_range) == 2:
                        # Use current bbox for semantic search (preserve user's view)
                        view_ranges = {
                            'x_range': x_range,
                            'y_range': y_range,
                            'bbox': f"{x_range[0]},{y_range[0]},{x_range[1]},{y_range[1]}",
                            'is_zoomed': True,
                            'last_update': time.time(),
                            'semantic_search': True  # Flag to indicate this is semantic search
                        }
                        logger.info(f"Using current bbox for semantic search: bbox={view_ranges['bbox']}")
                        print(f"🔍 SEMANTIC: Using current bbox for semantic search: bbox={view_ranges['bbox']}")
                    else:
                        logger.info("No valid zoom ranges in current figure for semantic search")
                        view_ranges = None
                else:
                    logger.info("No current figure available for bbox constraint in semantic search")
                    view_ranges = None
            
            # CRITICAL: Skip zoom state extraction if autorange is being forced (but only if not a year range change)
            elif force_autorange:
                logger.info("🚀 FORCE AUTORANGE: Skipping zoom state extraction to preserve autorange")
                print(f"🚀 FORCE AUTORANGE: Skipping zoom state extraction to preserve autorange")
                view_ranges = None  # Force no bbox filtering
            elif current_figure and 'layout' in current_figure and 'xaxis' in current_figure['layout'] and 'yaxis' in current_figure['layout']:
                x_range = current_figure['layout']['xaxis'].get('range')
                y_range = current_figure['layout']['yaxis'].get('range')
                
                if x_range and y_range and len(x_range) == 2 and len(y_range) == 2:
                    # Always use current zoom state from graph, overriding stale store data
                    view_ranges = {
                        'x_range': x_range,
                        'y_range': y_range,
                        'bbox': f"{x_range[0]},{y_range[0]},{x_range[1]},{y_range[1]}",
                        'is_zoomed': True,
                        'last_update': time.time()
                    }
                    logger.info(f"Using current zoom state from graph: x_range={x_range}, y_range={y_range}")
                    print(f"🌍 ZOOM: Using current zoom state from graph: x_range={x_range}, y_range={y_range}")
                else:
                    logger.info("No valid zoom ranges in current figure")
                    print(f"🌍 ZOOM: No valid zoom ranges in current figure")
            else:
                logger.info("No current figure available for zoom state")
                print(f"🌍 ZOOM: No current figure available for zoom state")
            
            # Use our unified data fetcher for consistent, deduplicated data fetching
            from .unified_data_fetcher import fetch_papers_unified, create_fetch_constraints
            
            # Create constraints object
            print(f"🔍 CONSTRAINTS DEBUG: About to create constraints with search_text='{search_text}'")
            constraints = create_fetch_constraints(
                sources=sources,
                year_range=year_range,
                universe_constraints=universe_constraints,
                bbox=view_ranges.get('bbox') if view_ranges else None,
                enrichment_state=enrichment_state,
                similarity_threshold=similarity_threshold,
                search_text=search_text,
                limit=5000
            )
            print(f"🔍 CONSTRAINTS DEBUG: Created constraints with search_text='{constraints.search_text}'")
            
            # Make single API call with all constraints
            print(f"🔍 DEBUG: About to call fetch_papers_unified...")
            result = fetch_papers_unified(constraints)
            print(f"🔍 DEBUG: fetch_papers_unified returned: {type(result)}")
            
            if result.success:
                data = result.data
                total_count = result.total_count
                metadata = result.metadata
                print(f"🔍 DEBUG: Success! Got {len(data)} papers, total_count: {total_count}")
                logger.info(f"Data fetch successful: {len(data)} records out of {total_count} total")
                
                # Debug logging for count query mismatches
                if len(data) > 0 and total_count > len(data) and total_count > 5000:
                    logger.warning(f"Count query mismatch detected: {len(data)} papers returned but total_count is {total_count}")
                    print(f"⚠️ COUNT MISMATCH: Got {len(data)} papers but total_count is {total_count}")
                    # This suggests the count query didn't apply the universe constraint properly
                    # However, we should NOT correct the total_count because it represents the actual
                    # total papers in the database. The mismatch just means the backend count
                    # query has an issue, but the total count is still valid.
                    logger.info(f"Keeping original total_count: {total_count} (not correcting to {len(data)})")
                
                logger.info(f"🔍 DATA FETCH: Returning {len(data)} papers with metadata: {metadata}")
                print(f"🔍 DEBUG: About to return data and metadata...")
                
                # Ensure Dash detects a change: copy data and add a fresh timestamp to metadata
                try:
                    data = [dict(item) for item in (data or [])]
                except Exception:
                    pass
                try:
                    import time as _t
                    if isinstance(metadata, dict):
                        metadata = dict(metadata)
                        metadata['updated_at'] = _t.time()
                        # Do not force autorange here; only initial load should set this
                except Exception:
                    pass
                
                return data, metadata
            else:
                print(f"🔍 DEBUG: Data fetch failed: {result.error}")
                logger.warning(f"Data fetch failed: {result.error}")
                # Return empty data and metadata as fallback
                return [], {'total_count': 0}
                
        except Exception as e:
            print(f"🔍 DEBUG: Exception in data fetch: {e}")
            logger.error(f"Data fetch callback error: {e}")
            # Do not overwrite existing data on errors (avoid clearing initial load)
            raise dash.exceptions.PreventUpdate

    @app.callback(
        [Output('data-store', 'data', allow_duplicate=True),
         Output('data-metadata', 'data', allow_duplicate=True)],
        [Input('view-ranges-store', 'data')],  # Listen to zoom/pan events
        [State('selected-sources', 'data'),
         State('year-range-slider', 'value'),
         State('similarity-threshold', 'value'),
         State('universe-constraints', 'data'),
         State('enrichment-state', 'data'),
         State('search-button', 'n_clicks'),
         State('search-text', 'value'),
         State('last-search-text', 'data'),
         State('target-records-per-view', 'value')],  # Respect Fetch: box setting
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def handle_zoom_data_fetch(
        view_ranges: Optional[Dict],
        sources: Optional[List[str]],
        year_range: Optional[List[int]],
        similarity_threshold: Optional[float],
        universe_constraints: Optional[str],
        enrichment_state: Optional[Dict],
        search_clicks: Optional[int],
        search_text: Optional[str],
        last_search_text: Optional[str],
        target_records: Optional[int]
    ) -> Tuple[List[Dict], Dict]:
        """
        Handle data fetching for zoom/pan events.
        
        This callback ONLY handles bbox-based data fetching when user zooms/pans.
        It's separate from handle_data_fetch to avoid conflicts during initial load.
        """
        try:
            # Strategic logging for zoom sequence tracking
            import time
            callback_id = "handle_zoom_data_fetch"
            timestamp = time.time()
            debug_msg = f"🔍 ZOOM DEBUG: {callback_id} ENTERED at {timestamp:.3f}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            debug_msg = f"🔍 ZOOM DEBUG: {callback_id} - callback_context.triggered: {callback_context.triggered}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            debug_msg = f"🔍 ZOOM DEBUG: {callback_id} - view_ranges: {view_ranges}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            # Skip if no view ranges (initial load clearing)
            if not view_ranges or view_ranges == {}:
                print(f"🔍 ZOOM DEBUG: {callback_id} - No view ranges, skipping")
                raise dash.exceptions.PreventUpdate
            
            # Skip if no bbox data (not a zoom/pan event)
            if not view_ranges.get('bbox'):
                print(f"🔍 ZOOM DEBUG: {callback_id} - No bbox data, skipping")
                raise dash.exceptions.PreventUpdate

            # Gate on meaningful bbox changes to avoid duplicate fetches
            # Use last_update timestamp or bbox string comparison if available
            last_bbox = getattr(handle_zoom_data_fetch, '_last_bbox', None)
            current_bbox = view_ranges.get('bbox')
            print(f"🔍 ZOOM DEBUG: {callback_id} - bbox comparison: current={current_bbox}, last={last_bbox}")
            if isinstance(current_bbox, str) and isinstance(last_bbox, str):
                if current_bbox == last_bbox:
                    print(f"🔍 ZOOM DEBUG: {callback_id} - Same bbox, skipping")
                    raise dash.exceptions.PreventUpdate
            # CORRECT debouncing for pan/zoom: Cancel existing operation and start new one
            # This ensures the user gets the LAST zoom they performed, not the first one
            import time as _time
            now_ts = _time.time()
            
            # Check if another callback is already running
            if getattr(handle_zoom_data_fetch, '_running', False):
                print(f"🔍 ZOOM DEBUG: {callback_id} - Canceling previous zoom operation for new one")
                # Don't skip - we want to cancel the old and start the new
                # The _running flag will be cleared when this callback completes
            
            # Update timestamp to track the latest zoom request
            handle_zoom_data_fetch._last_ts = now_ts
            
            # Mark this callback as running
            handle_zoom_data_fetch._running = True

            # Record the bbox for next invocation
            handle_zoom_data_fetch._last_bbox = current_bbox
            
            # Skip if this is initial load (search_clicks is None)
            if search_clicks is None:
                print(f"🔍 ZOOM DEBUG: {callback_id} - Initial load (search_clicks is None), skipping")
                raise dash.exceptions.PreventUpdate
            
            # Determine effective semantic query: prefer current input, else last confirmed
            effective_search_text = search_text if (search_text and str(search_text).strip()) else last_search_text
            debug_msg = f"🔍 ZOOM DEBUG: {callback_id} - About to fetch data with bbox: {current_bbox}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")

            # Use our unified data fetcher for consistent, deduplicated data fetching
            from .unified_data_fetcher import fetch_papers_unified, create_fetch_constraints
            
            # Create constraints object with bbox
            # Use the Fetch: box setting from the interface
            fetch_limit = target_records or 5000  # Default to 5000 if not set
            constraints = create_fetch_constraints(
                sources=sources,
                year_range=year_range,
                universe_constraints=universe_constraints,
                bbox=view_ranges.get('bbox'),
                enrichment_state=enrichment_state,
                similarity_threshold=similarity_threshold,
                search_text=effective_search_text,
                limit=fetch_limit  # Respect Fetch: box setting
            )
            
            # Make single API call with all constraints
            debug_msg = f"🔍 ZOOM DEBUG: {callback_id} - Calling fetch_papers_unified..."
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            result = fetch_papers_unified(constraints)
            debug_msg = f"🔍 ZOOM DEBUG: {callback_id} - fetch_papers_unified completed"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            if result.success:
                data = result.data
                total_count = result.total_count
                metadata = result.metadata
                print(f"🔍 ZOOM DEBUG: {callback_id} - Returning {len(data)} papers")
                debug_msg = f"🔍 ZOOM DEBUG: {callback_id} - About to return data and metadata"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                
                # Add timing marker for callback completion
                import time
                completion_ts = time.time()
                debug_msg = f"🔍 ZOOM DEBUG: {callback_id} - CALLBACK COMPLETED at {completion_ts:.3f}"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                
                # WRISTWATCH TIMER: Mark data fetch complete
                debug_msg = f"⏱️  WRISTWATCH: DATA FETCH COMPLETED at {completion_ts:.3f}"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                
                # Add debugging for data size and processing
                data_size = len(str(data)) if data else 0
                debug_msg = f"🔍 DATA SIZE DEBUG: Returning {len(data)} papers, serialized size: {data_size:,} chars"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                
                # Add callback counter to track concurrent callbacks
                callback_count = getattr(handle_zoom_data_fetch, '_callback_count', 0) + 1
                handle_zoom_data_fetch._callback_count = callback_count
                debug_msg = f"🔍 CALLBACK COUNT: Zoom data fetch callback #{callback_count}"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                
                # Clear running flag on success
                handle_zoom_data_fetch._running = False
                debug_msg = f"🔍 ZOOM DEBUG: {callback_id} - _running flag cleared, returning data"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                return data, metadata
            else:
                # Handle failure case
                logger.error(f"Zoom data fetch failed: {result.error}")
                print(f"🔍 ZOOM DEBUG: {callback_id} - Fetch failed: {result.error}")
                # Clear running flag on failure
                handle_zoom_data_fetch._running = False
                raise dash.exceptions.PreventUpdate
                
        except dash.exceptions.PreventUpdate:
            # Re-raise PreventUpdate to properly skip the callback
            raise
        except Exception as e:
            # Clear running flag on exception
            handle_zoom_data_fetch._running = False
            logger.error(f"Zoom data fetch callback error: {e}")
            # Do not overwrite existing data-store on errors during zoom
            raise dash.exceptions.PreventUpdate

# REMOVED: handle_filter_data_fetch - universe constraints now handled by main handle_data_fetch callback




    @app.callback(
        Output('available-sources', 'data'),
        [Input('url', 'pathname')],
        prevent_initial_call=False
    )
    def load_available_sources(pathname: str) -> List[str]:
        """Load available sources for the source filter."""
        try:
            logger.info("Loading available sources")
            # Return the same source list that the old system uses
            sources = [
                'openalex',
                'randpub',
                'extpub',
                'aipickle',
                '__AIPICKLE_COUNTRIES__:United States,China,Rest of the World'
            ]
            logger.info(f"Available sources loaded: {sources}")
            return sources
        except Exception as e:
            logger.error(f"Error loading available sources: {e}")
            return []

    @app.callback(
        Output('content-display-area', 'children'),
        [Input('graph-3', 'clickData')],
        prevent_initial_call=False
    )
    def display_paper_metadata(click_data: Optional[Dict[str, Any]]) -> html.Div:
        """
        Display paper metadata when a point is clicked.
        
        This callback uses our functional paper metadata service
        to maintain separation of concerns and pure function principles.
        """
        try:
            # Import our functional paper metadata service
            from .paper_metadata_service import (
                parse_click_data, 
                create_paper_metadata_display, 
                create_default_display, 
                create_error_display
            )
            
            # Parse click data into structured metadata
            metadata = parse_click_data(click_data)
            
            if metadata is None:
                # No valid click data - show default message
                return create_default_display()
            
            # Create metadata display using pure function
            return create_paper_metadata_display(metadata)
            
        except Exception as e:
            logger.error(f"Paper metadata display error: {e}")
            return create_error_display(f"Error displaying paper details: {e}")

    @app.callback(
        Output('graph-3', 'figure'),
        [Input('data-store', 'data')],  # Single trigger: data changes
        [State('view-ranges-store', 'data'),   # Move to State to avoid redraw races
         State('data-metadata', 'data'),       # Move to State to avoid spurious triggers
         State('enrichment-state', 'data'),
         State('cluster-overlay', 'data'),
         State('show-clusters', 'value')],
        prevent_initial_call=True
    )
    def handle_visualization(
        data: Optional[List[Dict]],
        view_ranges: Optional[Dict],
        metadata: Optional[Dict],
        enrichment_state: Optional[Dict],
        cluster_overlay: Optional[Dict],
        show_clusters: Optional[List[str]]
    ) -> go.Figure:
        """
        Handle visualization updates - delegates to orchestrator.
        
        This callback ONLY handles figure creation and view preservation.
        It does NOT fetch data or manage view state.
        """
        try:
            # Strategic logging for zoom sequence tracking
            import time
            callback_id = "handle_visualization"
            timestamp = time.time()
            debug_msg = f"🔍 VISUALIZATION DEBUG: {callback_id} ENTERED at {timestamp:.3f}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            # Add timing marker for when Dash triggers this callback
            debug_msg = f"🔍 VISUALIZATION DEBUG: {callback_id} - DASH TRIGGERED THIS CALLBACK at {timestamp:.3f}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            # Calculate delay since last data fetch completion
            # Look for the last "DATA FETCH COMPLETED" timestamp in the log
            try:
                with open("/tmp/zoom_debug.log", "r") as f:
                    log_content = f.read()
                    last_fetch_line = [line for line in log_content.split('\n') if 'DATA FETCH COMPLETED' in line][-1]
                    if last_fetch_line:
                        last_fetch_ts = float(last_fetch_line.split('at ')[1])
                        delay = timestamp - last_fetch_ts
                        debug_msg = f"🔍 DELAY ANALYSIS: {delay:.3f}s delay between data fetch and visualization trigger"
                        print(debug_msg)
                        with open("/tmp/zoom_debug.log", "a") as f:
                            f.write(f"{debug_msg}\n")
            except:
                pass  # Ignore errors in delay calculation
            
            # Add detailed timing for visualization steps
            debug_msg = f"🔍 VISUALIZATION DEBUG: {callback_id} - About to call orchestrate_visualization"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            # Debug logging to see exactly what's triggering this callback
            ctx = callback_context
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'Unknown'
            debug_msg = f"🔍 VISUALIZATION DEBUG: {callback_id} - Triggered by: {triggered_id}, Data length: {len(data) if data else 0}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            # Add timing analysis - check if this is the data we just fetched
            if data and len(data) > 0:
                debug_msg = f"🔍 VISUALIZATION DEBUG: {callback_id} - Received data with {len(data)} papers"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
            logger.info(f"🔍 VISUALIZATION DEBUG: Callback triggered by: {triggered_id}")
            logger.info(f"🔍 VISUALIZATION DEBUG - Data length: {len(data) if data else 0}")
            logger.info(f"🔍 VISUALIZATION DEBUG - View ranges: {view_ranges}")
            
            # CRITICAL: Skip visualization when there's no data to display
            # This prevents creating empty graphs
            if not data or len(data) == 0:
                logger.info("🔍 VISUALIZATION DEBUG: Skipping visualization with no data")
                print(f"🔍 VISUALIZATION DEBUG: Skipping visualization with no data")
                raise dash.exceptions.PreventUpdate
            
            # Use our orchestrator for visualization
            # Check if this is a force autorange request from initial load
            force_autorange = metadata.get('force_autorange', False) if metadata else False
            
            # CRITICAL DEBUG: Log the force_autorange flag
            logger.info(f"🔍 VISUALIZATION DEBUG - metadata: {metadata}")
            logger.info(f"🔍 VISUALIZATION DEBUG - force_autorange flag: {force_autorange}")
            print(f"🔍 VISUALIZATION DEBUG - metadata: {metadata}")
            print(f"🔍 VISUALIZATION DEBUG - force_autorange flag: {force_autorange}")
            
            result = orchestrate_visualization(
                data=data,
                view_ranges=view_ranges,
                enrichment_state=enrichment_state,
                force_autorange=force_autorange
            )
            
            # Add timing after orchestrate_visualization
            import time
            after_orchestrator_ts = time.time()
            debug_msg = f"🔍 VISUALIZATION DEBUG: {callback_id} - orchestrate_visualization completed at {after_orchestrator_ts:.3f}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            logger.info(f"🔍 VISUALIZATION DEBUG - Orchestrator result: {result}")
            logger.info(f"🔍 VISUALIZATION DEBUG - Success: {result.get('success')}")
            logger.info(f"🔍 VISUALIZATION DEBUG - Error: {result.get('error')}")
            
            if result['success']:
                logger.info("Visualization update successful")
                figure = result['figure']
                logger.info(f"🔍 VISUALIZATION DEBUG - Figure type: {type(figure)}")
                logger.info(f"🔍 VISUALIZATION DEBUG - Figure has data: {len(figure.data) if hasattr(figure, 'data') else 'No data attribute'}")
                logger.info(f"🔍 VISUALIZATION DEBUG - Figure title: {figure.layout.title.text if hasattr(figure.layout, 'title') and figure.layout.title else 'No title'}")
                
                # If clusters should be shown and cluster data exists, add them to the new figure
                if show_clusters and cluster_overlay and cluster_overlay.get('polygons'):
                    try:
                        from .graph_component import add_clustering_overlay
                        logger.info("Preserving clusters in visualization update")
                        figure = add_clustering_overlay(figure, cluster_overlay)
                    except ImportError as e:
                        logger.warning(f"Could not import clustering overlay: {e}")
                    except Exception as e:
                        logger.warning(f"Could not add clustering overlay: {e}")
                
                logger.info(f"🔍 VISUALIZATION DEBUG - Returning successful figure with {len(figure.data)} traces")
                # Add final timing
                import time
                final_ts = time.time()
                debug_msg = f"🔍 VISUALIZATION DEBUG: {callback_id} - Returning figure at {final_ts:.3f}"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                
                # WRISTWATCH TIMER: Mark zoom operation complete
                debug_msg = f"⏱️  WRISTWATCH: ZOOM OPERATION COMPLETED at {final_ts:.3f}"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                
                return figure
            else:
                logger.warning(f"Visualization update failed: {result.get('error', 'Unknown error')}")
                logger.error(f"🔍 VISUALIZATION DEBUG - Orchestrator returned success=False, error: {result.get('error')}")
                # Return empty figure that preserves view ranges instead of fallback figure
                from .graph_component import create_empty_figure
                empty_figure = create_empty_figure()
                
                # Preserve view ranges if available to maintain user's current view
                if view_ranges and 'x_range' in view_ranges and 'y_range' in view_ranges:
                    logger.info(f"🔍 VISUALIZATION DEBUG - Preserving view ranges in error figure")
                    empty_figure.update_layout(
                        xaxis=dict(range=view_ranges['x_range']),
                        yaxis=dict(range=view_ranges['y_range']),
                        dragmode='pan'
                    )
                
                return empty_figure
                
        except Exception as e:
            logger.error(f"Visualization callback error: {e}")
            # Return empty figure that preserves view ranges instead of fallback figure
            from .graph_component import create_empty_figure
            empty_figure = create_empty_figure()
            
            # Preserve view ranges if available to maintain user's current view
            if view_ranges and 'x_range' in view_ranges and 'y_range' in view_ranges:
                logger.info(f"🔍 VISUALIZATION DEBUG - Preserving view ranges in error figure")
                empty_figure.update_layout(
                    xaxis=dict(range=view_ranges['x_range']),
                    yaxis=dict(range=view_ranges['y_range']),
                    dragmode='pan'
                )
            
            return empty_figure
    
    @app.callback(
        Output('enrichment-state', 'data'),
        [Input('selected-sources', 'data'),
         Input('year-range-slider', 'value'),
         Input('similarity-threshold', 'value')],
        [State('enrichment-state', 'data')],
        prevent_initial_call=True
    )
    def handle_enrichment_state_update(
        sources: Optional[List[str]],
        year_range: Optional[List[int]],
        similarity_threshold: Optional[float],
        current_enrichment: Optional[Dict]
    ) -> Dict:
        """
        Handle enrichment state updates - manages enrichment configuration.
        
        This callback ONLY handles enrichment state management.
        It does NOT fetch data or create visualizations.
        """
        try:
            logger.info(f"Enrichment state callback triggered by: {callback_context.triggered}")
            
            # Preserve existing enrichment configuration if active
            if current_enrichment and current_enrichment.get('active'):
                logger.info("Preserving active enrichment configuration")
                return current_enrichment
            
            # Only create new enrichment state if no active enrichment exists
            new_enrichment = {
                'sources': sources or [],
                'year_range': year_range or [2000, 2025],
                'similarity_threshold': similarity_threshold or 0.5,
                'use_clustering': True,  # Default to clustering enabled
                'use_llm_summaries': False,  # Default to LLM summaries disabled
                'cluster_count': 10,  # Default cluster count
                'last_updated': time.time()
            }
            
            logger.info("Enrichment state updated successfully")
            return new_enrichment
            
        except Exception as e:
            logger.error(f"Enrichment state callback error: {e}")
            # Return current enrichment state as fallback
            return current_enrichment or {}
    

    

    
    @app.callback(
        Output('status-indicator', 'children'),
        [Input('data-store', 'data')],
        [State('data-metadata', 'data')],
        prevent_initial_call=True
    )
    def handle_status_update(data: Optional[List[Dict]], metadata: Optional[Dict]) -> html.Div:
        """
        Handle status updates - shows data status to user with total count.
        
        This callback ONLY handles status display.
        It does NOT fetch data or manage state.
        """
        try:
            # Debug logging to see when this callback is triggered
            ctx = callback_context
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'Unknown'
            logger.info(f"🔍 STATUS CALLBACK: Triggered by {triggered_id}")
            logger.info(f"🔍 STATUS CALLBACK: Data length: {len(data) if data else 0}")
            logger.info(f"🔍 STATUS CALLBACK: Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
            logger.info(f"🔍 STATUS CALLBACK: Total count: {metadata.get('total_count', 'Missing') if metadata else 'None'}")
            
            # Use pure function to generate status content
            status_content = create_status_content(data, metadata)
            return status_content
            
        except Exception as e:
            logger.error(f"Status update callback error: {e}")
            return html.Div("Status unknown", style={'color': '#ffd43b'})
    
    @app.callback(
        Output('cluster-busy', 'data'),
        [Input('compute-clusters-button', 'n_clicks')],
        [State('selected-sources', 'data'),
         State('num-clusters', 'value')],
        prevent_initial_call=True
    )
    def set_cluster_busy_state(
        n_clicks: Optional[int],
        selected_sources: Optional[List[str]],
        num_clusters: Optional[int]
    ) -> bool:
        """
        Set busy state when clustering button is clicked.
        
        This callback ONLY handles clustering busy state.
        It does NOT handle general loading states.
        """
        try:
            if n_clicks is None or n_clicks == 0:
                raise dash.exceptions.PreventUpdate
            
            logger.info(f"Clustering button clicked - setting busy state")
            return True
            
        except Exception as e:
            logger.error(f"Cluster busy state callback error: {e}")
            return False
    
    @app.callback(
        [Output('data-store', 'data', allow_duplicate=True),
         Output('data-metadata', 'data', allow_duplicate=True),
         Output('view-ranges-store', 'data', allow_duplicate=True),
         Output('force-autorange', 'data', allow_duplicate=True)],
        [Input('app-ready', 'data')],  # CRITICAL FIX: Use app-ready instead of url.pathname to prevent loops
        [State('year-range-slider', 'value'),
         State('selected-sources', 'data'),
         State('similarity-threshold', 'value')],
        prevent_initial_call='initial_duplicate',  # CRITICAL FIX: Allow initial call with duplicate callbacks
        allow_duplicate=True
    )
    def handle_initial_load(
        app_ready: bool,  # CRITICAL FIX: Match the actual input parameter
        year_range: Optional[List[int]],
        sources: Optional[List[str]],
        similarity_threshold: Optional[float]
    ) -> Tuple[List[Dict], Dict, Dict, bool]:
        # CRITICAL: This callback should run on app startup
        # Remove the complex URL checking logic that was preventing it from running
        """
        Handle initial app load - loads initial data and sets up the app.
        
        This callback ONLY runs on app startup and bypasses deduplication
        to ensure the app loads properly.
        """
        try:
            # UNIQUE CALLBACK ID: handle_initial_load
            import time
            callback_id = "handle_initial_load"
            timestamp = time.time()
            print(f"🚀 CALLBACK {callback_id} ENTERED at {timestamp}")
            print(f"🚀 CALLBACK {callback_id} - app_ready: {app_ready}")
            print(f"🚀 CALLBACK {callback_id} - callback_context.triggered: {callback_context.triggered}")
            
            logger.info("Initial load callback triggered")
            print(f"🚀 INITIAL LOAD: Starting app initialization...")
            logger.info(f"🔍 INITIAL LOAD DEBUG: app_ready: {app_ready}")
            logger.info(f"🔍 INITIAL LOAD DEBUG: callback_context.triggered: {callback_context.triggered}")
            
            # Initial load needs to fetch some papers to start with
            logger.info("Initial load - fetching initial papers")
            
            # Set default values for initial load
            default_year_range = year_range or [2000, 2025]
            default_sources = sources or ['openalex', 'randpub', 'extpub', 'aipickle']
            default_similarity_threshold = similarity_threshold or 0.5
            
            # Use our unified data fetcher for initial load
            from .unified_data_fetcher import fetch_papers_unified, create_fetch_constraints
            
            # CRITICAL: Create special constraints for initial load that FORCE autorange
            # This prevents any stored bbox from interfering with the startup view
            constraints = create_fetch_constraints(
                sources=default_sources,
                year_range=default_year_range,
                bbox=None,  # CRITICAL: No bbox for initial load
                similarity_threshold=default_similarity_threshold,
                limit=5000,
                force_autorange=True  # Special flag for orchestrator
            )
            
            # Use unified fetcher for initial load
            result = fetch_papers_unified(constraints)
            
            if result.success:
                data = result.data
                total_count = result.total_count
                logger.info(f"Initial load successful: {len(data)} records out of {total_count} total")
                print(f"🚀 INITIAL LOAD: Successfully loaded {len(data)} records")
                
                # CRITICAL: Clear any stale view ranges to prevent bbox filtering during initial load
                metadata = {
                    'total_count': total_count, 
                    'initial_load': True, 
                    'ready': True,
                    'bbox_cleared': True,  # Signal that bbox was cleared
                    'force_full_dataset': True  # Signal that full dataset should be fetched
                }
                
                logger.info("Initial load: returning data with bbox cleared")
                
                # Ensure Dash detects a change: copy data and add updated_at
                try:
                    data = [dict(item) for item in (data or [])]
                    import time as _t
                    metadata = dict(metadata)
                    metadata['updated_at'] = _t.time()
                except Exception:
                    pass

                # CRITICAL: Return data, metadata, cleared view ranges, and force_autorange flag
                # This ensures no stale bbox data interferes with initial load
                # The empty dict {} forces autorange and prevents any stored bbox from being used
                # force_autorange=True ensures the orchestrator keeps autorange for initial load only
                return data, metadata, {}, True  # Return as separate values for Dash compatibility
            else:
                logger.warning(f"Initial load failed: {result.error}")
                print(f"❌ INITIAL LOAD: Failed to load data")
                
                metadata = {'total_count': 0, 'initial_load': True, 'error': str(result.error)}
                return [], metadata, {}, True  # Return as separate values for Dash compatibility
                
        except Exception as e:
            logger.error(f"Initial load callback error: {e}")
            print(f"❌ INITIAL LOAD: Error during initialization: {e}")
            return [], {'total_count': 0, 'initial_load': True, 'error': str(e)}, {}, True  # Return as separate values


    
    @app.callback(
        Output('source-filter', 'children'),
        [Input('available-sources', 'data')],
        [State('selected-sources', 'data')],
        prevent_initial_call=False
    )
    def update_source_filter(available_sources: List[str], selected_sources: List[str]) -> html.Div:
        """
        Update source filter options and values - matches old system functionality.
        
        This callback creates the source filter sidebar with color chips.
        """
        try:
            logger.info("Source filter callback triggered")
            
            if not available_sources:
                return html.P('No sources available', style={'color': '#666', 'text-align': 'center'})
            
            # Import settings for color mapping
            from ..config.settings import SOURCE_COLOR_MAP, DEFAULT_COLOR
            
            # Map display labels and handle API source name differences
            label_map = {
                'openalex': 'OpenAlex',
                'randpub': 'RAND Publications',
                'extpub': 'External RAND',
                'aipickle': 'ArXiv AI Subset'
            }
            
            # Map API source names to expected source names for color mapping
            source_mapping = {
                'randpub': 'randpub',
                'extpub': 'extpub',
                'aipickle': 'aipickle',
                'openalex': 'openalex'
            }
            
            # Filter out special country info from available sources
            clean_sources = [s for s in available_sources if not s.startswith('__AIPICKLE_COUNTRIES__:')]
            
            # Define display order using API source names
            display_order = ['openalex', 'randpub', 'extpub', 'aipickle']
            ordered_sources = [s for s in display_order if s in clean_sources] + [s for s in clean_sources if s not in display_order]
            
            # Handle initial value setting - only set if not already set
            if not selected_sources or len(selected_sources) == 0:
                value = [source for source in clean_sources]
            elif set(selected_sources) != set(clean_sources):
                # Only update if the sources have actually changed
                value = [source for source in clean_sources]
            else:
                # No change - keep existing and don't update the store
                # Return the existing selected_sources to prevent unnecessary updates
                return html.P('Filters loaded', style={'color': '#666', 'text-align': 'center'})
            
            # Build options with color chips and labels - unified approach for all sources
            options = []
            for s in ordered_sources:
                # All sources get the same treatment with color chips
                mapped_source = source_mapping.get(s, s)
                color = SOURCE_COLOR_MAP.get(mapped_source, DEFAULT_COLOR)
                label = label_map.get(s, s)
                full_label = html.Span([
                    html.Span(style={
                        'display': 'inline-block',
                        'width': '16px',
                        'height': '16px',
                        'backgroundColor': color,
                        'marginRight': '12px',
                        'borderRadius': '3px',
                        'verticalAlign': 'middle',
                        'opacity': 1.0
                    }),
                    label
                ], style={'display': 'flex', 'alignItems': 'center'})
                
                options.append({
                    'label': full_label,
                    'value': s
                })
            
            # Create the main checklist
            checklist = html.Div([
                dcc.Checklist(
                    id='source-filter-checklist',
                    options=options,
                    value=value,
                    inputStyle={'marginRight': '12px', 'width': '18px', 'height': '18px'},
                    labelStyle={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px', 'marginLeft': '2px', 'fontSize': '15px'}
                )
            ])
            
            # Note: Country sub-lines for aipickle have been removed since we no longer use country-based coloring
            # The aipickle source is now displayed as a simple text label without color chips or country breakdowns
            
            logger.info(f"Source filter updated with {len(options)} options")
            return checklist
            
        except Exception as e:
            logger.error(f"Source filter callback error: {e}")
            return html.P(f'Error loading filters: {e}', style={'color': '#ff6b6b', 'text-align': 'center'})

    @app.callback(
        [Output('selected-sources', 'data'),
         Output('source-filter-checklist', 'value')],
        [Input('source-filter-checklist', 'value'),
         Input('selected-sources', 'data')],
        prevent_initial_call=True
    )
    def manage_source_selection(
        checklist_values: Optional[List[str]],
        current_selected_sources: Optional[List[str]]
    ) -> Tuple[List[str], List[str]]:
        """
        Manage source selection - bidirectional sync between checklist and data store.
        Also handles enrichment-driven source changes.
        """
        try:
            # Check which input triggered the callback
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0] if callback_context.triggered else None
            
            log_debug_to_file(f"🔍 SOURCE FILTER DEBUG - Callback triggered by: {triggered_id}")
            log_debug_to_file(f"🔍 SOURCE FILTER DEBUG - checklist_values: {checklist_values}")
            log_debug_to_file(f"🔍 SOURCE FILTER DEBUG - current_selected_sources: {current_selected_sources}")
            
            if triggered_id == 'source-filter-checklist':
                # User changed the checklist - update the data store
                selected_sources = checklist_values or []
                logger.info(f"Source filter changed by user: {selected_sources}")
                log_debug_to_file(f"🔍 SOURCE FILTER DEBUG - User change, returning: {selected_sources}")
                return selected_sources, selected_sources
            elif triggered_id == 'selected-sources':
                # Data store changed (e.g., by enrichment) - update the checklist
                selected_sources = current_selected_sources or []
                logger.info(f"Source filter updated from data store: {selected_sources}")
                log_debug_to_file(f"🔍 SOURCE FILTER DEBUG - Data store change, returning: {selected_sources}")
                return selected_sources, selected_sources
            else:
                # Initial call or unknown trigger - use checklist values
                selected_sources = checklist_values or []
                logger.info(f"Source filter initial/unknown trigger: {selected_sources}")
                log_debug_to_file(f"🔍 SOURCE FILTER DEBUG - Initial/unknown trigger, returning: {selected_sources}")
                return selected_sources, selected_sources
            
        except Exception as e:
            logger.error(f"Error managing source selection: {e}")
            # Return empty lists as fallback
            return [], []

    @app.callback(
        Output('loading-state', 'data'),
        [Input('data-store', 'data')],
        [State('enrichment-state', 'data')],
        prevent_initial_call=True
    )
    def update_loading_state(data: Optional[List[Dict]], enrichment_state: Optional[Dict]) -> bool:
        """Update loading state based on data and enrichment."""
        try:
            if not data:
                return False
            
            # Check if enrichment is enabled and data needs processing
            if enrichment_state and enrichment_state.get('use_clustering', False):
                # Simulate loading state for clustering operations
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Loading state callback error: {e}")
            return False

    @app.callback(
        Output('year-range-label', 'children'),
        [Input('year-range-slider', 'value')],
        prevent_initial_call=False
    )
    def update_year_range_label(year_range: List[int]) -> str:
        """Update the year range label to show current selection."""
        try:
            if not year_range or len(year_range) != 2:
                return "2000 - 2025"
            
            start_year, end_year = year_range
            return f"{start_year} - {end_year}"
            
        except Exception as e:
            logger.error(f"Year range label callback error: {e}")
            return "2000 - 2025"

    # REMOVED: handle_year_range_change callback - duplicate functionality with handle_data_fetch
    # This was causing duplicate API calls when year range changed
    
    # ============================================================================
    # CLUSTERING CALLBACKS - Pure Functional Architecture
    # ============================================================================
    

    
    @app.callback(
        [Output('compute-clusters-button', 'children'),
         Output('compute-clusters-button', 'style')],
        [Input('cluster-busy', 'data')],
        prevent_initial_call=False
    )
    def handle_cluster_button_update(busy: bool) -> Tuple[str, Dict[str, Any]]:
        """
        Handle cluster button updates - manages button text and styling.
        
        This callback ONLY handles button UI state.
        It does NOT perform actual clustering.
        """
        try:
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
                
        except Exception as e:
            logger.error(f"Cluster button update callback error: {e}")
            # Return default button state on error
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
    
    # ============================================================================
    # SEARCH CLEAR CALLBACK - Pure Functional Architecture
    # ============================================================================
    
    @app.callback(
        [Output('search-text', 'value', allow_duplicate=True),
         Output('search-button', 'n_clicks', allow_duplicate=True)],
        [Input('clear-search-button', 'n_clicks')],
        [State('search-button', 'n_clicks')],
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def handle_search_clear(
        clear_clicks: Optional[int],
        current_search_clicks: Optional[int]
    ) -> Tuple[str, int]:
        """
        Handle search clearing - resets search text and triggers data refresh.
        
        This callback ONLY handles search clearing.
        It does NOT perform data fetching or visualization.
        """
        try:
            if clear_clicks is None or clear_clicks == 0:
                raise PreventUpdate
            
            logger.info("Search clear button clicked - clearing search text and triggering refresh")
            
            # Clear the search text and increment search button clicks to trigger data fetch
            new_search_clicks = (current_search_clicks or 0) + 1
            return "", new_search_clicks
            
        except Exception as e:
            logger.error(f"Search clear callback error: {e}")
            # Return current state on error
            return "", current_search_clicks or 0
    
    # ============================================================================
    # CLUSTERING CALLBACKS - Pure Functional Architecture
    # ============================================================================
    
    @app.callback(
        [Output('cluster-overlay', 'data'),
         Output('cluster-busy', 'data', allow_duplicate=True),
         Output('show-clusters', 'value')],
        [Input('compute-clusters-button', 'n_clicks')],
        [State('data-store', 'data'),
         State('num-clusters', 'value'),
         State('selected-sources', 'data'),
         State('graph-3', 'relayoutData')],
        prevent_initial_call=True
    )
    def handle_clustering_operation(
        n_clicks: Optional[int],
        data_store: Optional[List[Dict]],
        num_clusters: Optional[int],
        selected_sources: Optional[List[str]],
        relayout_data: Optional[Dict]
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Handle clustering operations - delegates to orchestrator.
        
        This callback ONLY handles clustering coordination.
        It delegates actual clustering to the orchestrator.
        """
        try:
            logger.info(f"CLUSTERING CALLBACK TRIGGERED - n_clicks: {n_clicks}, data_store length: {len(data_store) if data_store else 0}")
            
            # Input validation
            if n_clicks is None or n_clicks == 0:
                logger.info("CLUSTERING CALLBACK: n_clicks is None or 0, returning no_update")
                return dash.no_update, dash.no_update, dash.no_update
            
            # Validate number of clusters
            if num_clusters is not None:
                try:
                    num_clusters_int = int(num_clusters)
                    if num_clusters_int < 1 or num_clusters_int > 1000:
                        logger.warning(f"Invalid num_clusters: {num_clusters}, using default 30")
                        num_clusters_int = 30
                except (ValueError, TypeError):
                    logger.warning(f"Invalid num_clusters type: {type(num_clusters)}, using default 30")
                    num_clusters_int = 30
            else:
                num_clusters_int = 30
            
            # Check data availability
            if not data_store or len(data_store) == 0:
                logger.warning("No data available for clustering - please load some data first")
                return {'polygons': [], 'annotations': []}, False, ['show']
            
            logger.info(f"Starting clustering operation with {num_clusters_int} clusters")
            
            # Use our orchestrator for clustering
            logger.info(f"CLUSTERING CALLBACK: Calling orchestrate_clustering with {len(data_store)} data points")
            result = orchestrate_clustering(
                data=data_store,
                num_clusters=num_clusters_int,
                selected_sources=selected_sources,
                relayout_data=relayout_data
            )
            
            logger.info(f"CLUSTERING CALLBACK: Orchestrator result: {result}")
            
            if result['success']:
                logger.info("Clustering operation successful")
                return result['cluster_data'], False, ['show']  # Auto-check show clusters
            else:
                logger.warning(f"Clustering operation failed: {result.get('error', 'Unknown error')}")
                return {'polygons': [], 'annotations': []}, False, ['show']
                
        except Exception as e:
            logger.error(f"Clustering operation callback error: {e}")
            import traceback
            logger.error(f"CLUSTERING CALLBACK: Full traceback: {traceback.format_exc()}")
            return {'polygons': [], 'annotations': []}, False, ['show']
    
    @app.callback(
        Output('graph-3', 'figure', allow_duplicate=True),
        [Input('cluster-overlay', 'data'),
         Input('show-clusters', 'value')],
        [State('graph-3', 'figure')],
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def update_graph_with_clusters(
        cluster_overlay: Optional[Dict[str, Any]],
        show_clusters: Optional[List[str]],
        current_figure: go.Figure
    ) -> go.Figure:
        """
        Update graph with clustering overlay - displays clusters and labels.
        
        This callback handles the visual display of clustering results.
        It does NOT perform clustering operations.
        """
        try:
            # Add debug logging for clustering callback
            import time
            callback_id = "update_graph_with_clusters"
            timestamp = time.time()
            debug_msg = f"🔍 CLUSTERING DEBUG: {callback_id} ENTERED at {timestamp:.3f}"
            print(debug_msg)
            with open("/tmp/zoom_debug.log", "a") as f:
                f.write(f"{debug_msg}\n")
            
            # CRITICAL: Skip during initial load to prevent conflicts with main visualization
            if not cluster_overlay or not cluster_overlay.get('polygons'):
                debug_msg = f"🔍 CLUSTERING DEBUG: {callback_id} - Skipping (no cluster data)"
                print(debug_msg)
                with open("/tmp/zoom_debug.log", "a") as f:
                    f.write(f"{debug_msg}\n")
                logger.info("🔍 CLUSTERING CALLBACK: Skipping during initial load (no cluster data)")
                return dash.no_update
                
            logger.info(f"🔍 CLUSTERING CALLBACK: update_graph_with_clusters triggered")
            logger.info(f"🔍 CLUSTERING CALLBACK: show_clusters: {show_clusters}")
            logger.info(f"🔍 CLUSTERING CALLBACK: cluster_overlay exists: {cluster_overlay is not None}")
            logger.info(f"🔍 CLUSTERING CALLBACK: current_figure type: {type(current_figure)}")
            if hasattr(current_figure, 'data'):
                logger.info(f"🔍 CLUSTERING CALLBACK: current_figure has {len(current_figure.data)} traces")
                if len(current_figure.data) > 0:
                    logger.info(f"🔍 CLUSTERING CALLBACK: First trace type: {type(current_figure.data[0])}")
                    logger.info(f"🔍 CLUSTERING CALLBACK: First trace name: {current_figure.data[0].name if hasattr(current_figure.data[0], 'name') else 'No name'}")
            # If clusters are not supposed to be shown, remove cluster traces efficiently
            if not show_clusters:
                logger.info("Clusters hidden - removing cluster traces")
                
                # Convert dictionary to Plotly figure if needed
                if isinstance(current_figure, dict):
                    fig = go.Figure(current_figure)
                else:
                    fig = current_figure
                
                # Efficiently remove only cluster-related traces without rebuilding the whole figure
                traces_to_keep = []
                for trace in fig.data:
                    # Keep all traces EXCEPT cluster-related ones
                    if hasattr(trace, 'name') and trace.name == 'Cluster Region':
                        continue  # Skip cluster traces
                    else:
                        traces_to_keep.append(trace)  # Keep everything else
                
                # Only update the data, keep the existing layout and structure
                fig.data = traces_to_keep
                
                # Clear any cluster annotations
                if hasattr(fig.layout, 'annotations'):
                    fig.layout.annotations = []
                
                logger.info(f"🔍 CLUSTERING CALLBACK: Returning figure with {len(fig.data)} traces after hiding clusters")
                return fig
            
            # If clusters should be shown but no cluster data exists, do nothing
            if not cluster_overlay or not cluster_overlay.get('polygons'):
                logger.info("No cluster overlay data available")
                return dash.no_update
            
            logger.info(f"Adding clustering overlay to graph: {len(cluster_overlay.get('polygons', []))} polygons, {len(cluster_overlay.get('annotations', []))} annotations")
            
            # Import the clustering overlay function
            try:
                from .graph_component import add_clustering_overlay
                
                # Convert dictionary to Plotly figure if needed
                if isinstance(current_figure, dict):
                    fig = go.Figure(current_figure)
                else:
                    fig = current_figure
                
                # CRITICAL: Clear any existing clusters before adding new ones
                # This prevents superimposing multiple sets of clusters
                traces_to_keep = []
                for trace in fig.data:
                    # Keep all traces EXCEPT cluster-related ones
                    if hasattr(trace, 'name') and trace.name == 'Cluster Region':
                        continue  # Skip cluster traces
                    else:
                        traces_to_keep.append(trace)  # Keep everything else
                
                # Update figure with only non-cluster traces
                fig.data = traces_to_keep
                
                # Clear any existing cluster annotations
                if hasattr(fig.layout, 'annotations'):
                    fig.layout.annotations = []
                
                # Now add the new clusters to the clean figure
                updated_figure = add_clustering_overlay(fig, cluster_overlay)
                
                # Ensure the figure maintains our pan mode and styling
                updated_figure.update_layout(
                    dragmode='pan',  # CRITICAL: Preserve pan mode
                    plot_bgcolor='#2b2b2b',
                    paper_bgcolor='#2b2b2b',
                    xaxis=dict(showgrid=False, zeroline=False, visible=True, showline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, visible=True, showline=False, showticklabels=False),
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                
                logger.info("Clustering overlay added successfully")
                logger.info(f"🔍 CLUSTERING CALLBACK: Returning figure with {len(updated_figure.data)} traces after adding clusters")
                return updated_figure
                
            except ImportError as e:
                logger.error(f"Clustering overlay import error: {e}")
                return dash.no_update
            except Exception as e:
                logger.error(f"Clustering overlay error: {e}")
                return dash.no_update
                
        except Exception as e:
            logger.error(f"Graph update with clusters error: {e}")
            logger.error(f"🔍 CLUSTERING CALLBACK: Error occurred, returning dash.no_update")
            return dash.no_update
    
    # ============================================================================
    # ENRICHMENT FILTER CALLBACKS - Pure Functional Architecture
    # ============================================================================
    
    log_debug_to_file("🚀 REGISTERING ENRICHMENT SOURCE CALLBACK")
    
    @app.callback(
        [Output('enrichment-source-dropdown', 'options'),
         Output('enrichment-source-dropdown', 'value')],
        [Input('app-ready', 'data')],
        prevent_initial_call=False
    )
    def populate_enrichment_sources(app_ready: bool) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """Populate enrichment source dropdown with available sources."""
        try:
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - populate_enrichment_sources called with app_ready: {app_ready}")
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - Callback function is executing!")
            
            # Filter to sources that likely have enrichment data
            enrichment_sources = ['openalex', 'aipickle']
            
            options = [{'label': source.title(), 'value': source} for source in enrichment_sources]
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - Enrichment sources populated: {enrichment_sources}")
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - Options created: {options}")
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - About to return: {options}")
            
            return options, None
            
        except Exception as e:
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - Error populating enrichment sources: {e}")
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - Exception details: {type(e).__name__}: {str(e)}")
            return [], None
    
    @app.callback(
        [Output('enrichment-table-dropdown', 'options'),
         Output('enrichment-table-dropdown', 'value'),
         Output('enrichment-table-dropdown', 'disabled'),
         Output('enrichment-field-dropdown', 'value', allow_duplicate=True)],
        [Input('enrichment-source-dropdown', 'value')],
        prevent_initial_call=True
    )
    def populate_enrichment_tables(selected_source: Optional[str]) -> Tuple[List[Dict[str, str]], Optional[str], bool, Optional[str]]:
        """Populate enrichment table dropdown based on selected source."""
        try:
            if not selected_source:
                return [], None, True, None
            
            logger.info(f"Populating enrichment tables for source: {selected_source}")
            
            # Define available tables for each source - GENERALIZABLE APPROACH
            # Instead of hard-coding table names, dynamically detect them from the API
            try:
                from .data_service import get_enrichment_tables
                available_tables = get_enrichment_tables(selected_source)
                
                if available_tables:
                    # Filter to only show tables that are useful for enrichment visualization
                    all_tables = list(available_tables.keys())
                    
                    # Define which tables are actually useful for each source
                    useful_tables = []
                    if selected_source == 'openalex':
                        # Only show main enrichment and metadata tables for OpenAlex
                        useful_tables = [
                            'openalex_enrichment_country',  # Main country enrichment
                            'openalex_metadata'             # Basic metadata
                        ]
                    elif selected_source == 'aipickle':
                        # Only show main enrichment tables for AIPickle
                        useful_tables = [
                            'aipickle_metadata'  # Main metadata with country fields
                        ]
                    elif selected_source == 'randpub':
                        # Only show main metadata table for RAND
                        useful_tables = [
                            'randpub_metadata'  # Main metadata
                        ]
                    else:
                        # For unknown sources, show all tables
                        useful_tables = all_tables
                    
                    # Filter to only include useful tables that actually exist
                    tables = [table for table in useful_tables if table in all_tables]
                    
                    if not tables:
                        # Fallback to all tables if filtering removed everything
                        tables = all_tables
                        logger.warning(f"Filtering removed all tables for {selected_source}, using all available: {tables}")
                    else:
                        logger.info(f"Filtered to useful tables for {selected_source}: {tables}")
                else:
                    # Fallback to known table patterns if API fails
                    logger.warning(f"API returned no tables for {selected_source}, using fallback patterns")
                    if selected_source == 'openalex':
                        tables = ['openalex_enrichment_country']
                    elif selected_source == 'aipickle':
                        tables = ['aipickle_metadata']
                    else:
                        tables = []
            except Exception as e:
                logger.error(f"Error fetching enrichment tables from API: {e}")
                # Fallback to known table patterns
                if selected_source == 'openalex':
                    tables = ['openalex_enrichment_country']
                elif selected_source == 'aipickle':
                    tables = ['aipickle_metadata']
                else:
                    tables = []
            
            # Create options with clean, readable display names
            options = []
            for table in tables:
                # Simplify table names to just show their key purpose
                if table == 'openalex_enrichment_country':
                    clean_name = 'Country'
                elif table == 'openalex_metadata':
                    clean_name = 'Metadata'
                elif table == 'aipickle_metadata':
                    clean_name = 'Metadata'
                elif table == 'randpub_metadata':
                    clean_name = 'Metadata'
                else:
                    # Fallback for any other tables - extract the key purpose
                    clean_name = table
                    
                    # Remove source prefix if present
                    if table.startswith(f'{selected_source}_'):
                        clean_name = table[len(f'{selected_source}_'):]
                    
                    # Remove common prefixes and get the key word
                    clean_name = clean_name.replace('_enrichment_', '_')
                    clean_name = clean_name.replace('_metadata', '')
                    clean_name = clean_name.replace('_field_mapping', '')
                    
                    # Split by underscore and take the last meaningful word
                    parts = clean_name.split('_')
                    if parts:
                        clean_name = parts[-1].title()
                    
                    # Clean up common patterns
                    clean_name = clean_name.replace('Country', 'Country')
                    clean_name = clean_name.replace('Institution', 'Institution')
                    clean_name = clean_name.replace('Publication', 'Publication')
                
                options.append({'label': clean_name, 'value': table})
            
            logger.info(f"Enrichment tables populated: {tables}")
            return options, None, False, None
            
        except Exception as e:
            logger.error(f"Error populating enrichment tables: {e}")
            return [], None, True, None
    
    @app.callback(
        [Output('enrichment-field-dropdown', 'options'),
         Output('enrichment-field-dropdown', 'value'),
         Output('enrichment-field-dropdown', 'disabled')],
        [Input('enrichment-table-dropdown', 'value')],
        [State('enrichment-source-dropdown', 'value')],
        prevent_initial_call=True
    )
    def populate_enrichment_fields(selected_table: Optional[str], selected_source: Optional[str]) -> Tuple[List[Dict[str, str]], Optional[str], bool]:
        """Populate enrichment field dropdown based on selected table."""
        try:
            if not selected_table or not selected_source:
                return [], None, True
            
            logger.info(f"Populating enrichment fields for table: {selected_table}")
            
            # Get available fields from the API (same as old code)
            try:
                from .data_service import get_enrichment_tables
                tables = get_enrichment_tables(selected_source)
                
                if selected_table in tables:
                    fields = tables[selected_table]
                    # Filter to fields that are suitable for visualization (not metadata fields)
                    visualization_fields = [f for f in fields if not f['field_name'].endswith(('_processed_at', '_version', '_confidence'))]
                    field_names = [f['field_name'] for f in visualization_fields]
                else:
                    field_names = []
            except Exception as e:
                logger.error(f"Error fetching enrichment fields from API: {e}")
                field_names = []
            
            # Create options with clean display names using list comprehension
            # Use display_name for label and field_name for value (same as old code)
            options = []
            for f in visualization_fields:
                # Clean up the display name for better readability
                display_name = f['display_name']
                field_name = f['field_name']
                
                # If display_name is too long or messy, create a cleaner version
                if len(display_name) > 30 or '_' in display_name:
                    # Create a cleaner name from the field_name
                    clean_name = field_name
                    
                    # Remove source prefix if present
                    if field_name.startswith(f'{selected_source}_'):
                        clean_name = field_name[len(f'{selected_source}_'):]
                    
                    # Remove common prefixes that make names longer
                    clean_name = clean_name.replace('openalex_country_', '')
                    clean_name = clean_name.replace('aipickle_', '')
                    clean_name = clean_name.replace('randpub_', '')
                    
                    # Replace underscores with spaces and title case
                    clean_name = clean_name.replace('_', ' ').title()
                    
                    # Clean up common patterns
                    clean_name = clean_name.replace('Country', 'Country')
                    clean_name = clean_name.replace('Institution', 'Institution')
                    clean_name = clean_name.replace('Publication', 'Publication')
                    clean_name = clean_name.replace('Uschina', 'US/China')
                    clean_name = clean_name.replace('Country Origin', 'Country Origin')
                    clean_name = clean_name.replace('Country Alt', 'Country Alt')
                    
                    # Truncate very long names
                    if len(clean_name) > 25:
                        clean_name = clean_name[:22] + '...'
                    
                    display_name = clean_name
                
                options.append({'label': display_name, 'value': field_name})
            
            logger.info(f"Enrichment fields populated: {[f['field_name'] for f in visualization_fields]}")
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - API returned fields: {[f['field_name'] for f in visualization_fields]}")
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - Field display names: {[f['display_name'] for f in visualization_fields]}")
            log_debug_to_file(f"🔍 ENRICHMENT DEBUG - Created options: {options}")
            return options, None, False
            
        except Exception as e:
            logger.error(f"Error populating enrichment fields: {e}")
            return [], None, True
    
    @app.callback(
        [Output('apply-enrichment-button', 'disabled'),
         Output('clear-enrichment-button', 'disabled')],
        [Input('enrichment-source-dropdown', 'value'),
         Input('enrichment-table-dropdown', 'value'),
         Input('enrichment-field-dropdown', 'value')],
        prevent_initial_call=True
    )
    def update_enrichment_button_states(source: Optional[str], table: Optional[str], field: Optional[str]) -> Tuple[bool, bool]:
        """Enable/disable enrichment buttons based on selection completeness."""
        try:
            # Enable apply button only when all three are selected
            apply_disabled = not (source and table and field)
            
            # Enable clear button when any enrichment is active
            clear_disabled = not (source or table or field)
            
            return apply_disabled, clear_disabled
            
        except Exception as e:
            logger.error(f"Error updating enrichment button states: {e}")
            return True, True
    
    @app.callback(
        [Output('enrichment-state', 'data', allow_duplicate=True),
         Output('selected-sources', 'data', allow_duplicate=True)],
        [Input('apply-enrichment-button', 'n_clicks')],
        [State('enrichment-source-dropdown', 'value'),
         State('enrichment-table-dropdown', 'value'),
         State('enrichment-field-dropdown', 'value'),
         State('source-filter-checklist', 'value')],
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def apply_enrichment(
        n_clicks: Optional[int],
        source: Optional[str],
        table: Optional[str],
        field: Optional[str],
        current_source_selection: Optional[List[str]]
    ) -> Tuple[Dict, List[str]]:
        """Apply enrichment visualization by updating enrichment state only."""
        try:
            # UNIQUE CALLBACK ID: apply_enrichment
            import time
            callback_id = "apply_enrichment"
            timestamp = time.time()
            print(f"🚀 CALLBACK {callback_id} ENTERED at {timestamp}")
            
            # CRITICAL: Only run when enrichment button is explicitly clicked
            if n_clicks is None or n_clicks == 0:
                print(f"🚀 CALLBACK {callback_id} - Skipping (no clicks)")
                raise dash.exceptions.PreventUpdate
            
            print(f"🚀 CALLBACK {callback_id} - Applying enrichment: {source}/{table}/{field}")
            logger.info(f"Applying enrichment: {source}/{table}/{field}")
            
            # Update enrichment state
            enrichment_state = {
                'source': source,
                'table': table,
                'field': field,
                'active': True
            }
            
            # CRITICAL: When enrichment is applied, filter to show ONLY the enrichment source
            # This ensures only the enriched data is visible
            if source:
                selected_sources = [source]
                logger.info(f"Enrichment applied - filtering to source: {selected_sources}")
            else:
                # Fallback to current selection if no source specified
                selected_sources = current_source_selection or []
                logger.warning(f"No enrichment source specified, using current selection: {selected_sources}")
            
            # Return enrichment state and filtered sources
            return enrichment_state, selected_sources
            
        except Exception as e:
            logger.error(f"Error applying enrichment: {e}")
            return {'source': None, 'table': None, 'field': None, 'active': False}, []
    
    @app.callback(
        [Output('enrichment-state', 'data', allow_duplicate=True),
         Output('selected-sources', 'data', allow_duplicate=True)],
        [Input('clear-enrichment-button', 'n_clicks')],
        [State('enrichment-state', 'data')],
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def clear_enrichment(
        n_clicks: Optional[int],
        current_enrichment_state: Optional[Dict]
    ) -> Tuple[Dict, List[str]]:
        """Clear enrichment and restore previous view state while preserving zoom level."""
        try:
            # UNIQUE CALLBACK ID: clear_enrichment
            import time
            callback_id = "clear_enrichment"
            timestamp = time.time()
            print(f"🚀 CALLBACK {callback_id} ENTERED at {timestamp}")
            
            # CRITICAL: Only run when clear enrichment button is explicitly clicked
            if n_clicks is None or n_clicks == 0:
                print(f"🚀 CALLBACK {callback_id} - Skipping (no clicks)")
                raise dash.exceptions.PreventUpdate
            
            print(f"🚀 CALLBACK {callback_id} - Clearing enrichment")
            logger.info("Clearing enrichment")
            
            # Reset enrichment state
            enrichment_state = {
                'source': None,
                'table': None,
                'field': None,
                'active': False
            }
            
            # SMART SOURCE RESTORATION: Show all sources when enrichment is cleared
            # This gives users a comprehensive view of all data while preserving their zoom level
            # 
            # Why this approach is better than restoring previous selection:
            # 1. Users expect to see everything when they clear a filter
            # 2. It preserves their current zoom level and view context
            # 3. It's more intuitive - clear = show all
            # 4. Users can then apply other filters or enrichment as needed
            restored_sources = ['openalex', 'randpub', 'extpub', 'aipickle']
            
            logger.info(f"Enrichment cleared - restoring all sources: {restored_sources}")
            print(f"🌍 ENRICHMENT: Cleared enrichment, showing all sources: {restored_sources}")
            
            # Return enrichment state - data fetching will be handled by main callback
            # The zoom level will be preserved because we're not resetting view ranges
            return enrichment_state, restored_sources
            
        except Exception as e:
            logger.error(f"Error clearing enrichment: {e}")
            return {'source': None, 'table': None, 'field': None, 'active': False}, []
    
    # ============================================================================
    # UNIVERSE CONSTRAINT CALLBACKS
    # ============================================================================
    
    @app.callback(
        [Output('universe-constraint-modal', 'style'),
         Output('universe-constraint-input', 'value'),
         Output('universe-constraints', 'data')],
        [Input('set-universe-button', 'n_clicks'),
         Input('apply-universe-constraint-button', 'n_clicks'),
         Input('cancel-universe-constraint-button', 'n_clicks')],
        [State('universe-constraint-modal', 'style'),
         State('universe-constraint-input', 'value'),
         State('universe-constraints', 'data')],
        prevent_initial_call=True
    )
    def handle_universe_modal(
        set_clicks: Optional[int],
        apply_clicks: Optional[int],
        cancel_clicks: Optional[int],
        modal_style: Dict[str, Any],
        input_value: Optional[str],
        current_constraints: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str], Optional[str]]:
        """
        Handle opening/closing the universe constraint modal and applying constraints.
        """
        try:
            # Determine which button was clicked
            ctx = callback_context
            if not ctx.triggered:
                return modal_style, input_value
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            # Base modal style
            base_style = {
                'position': 'fixed',
                'top': '0',
                'left': '0',
                'width': '100%',
                'height': '100%',
                'backgroundColor': 'rgba(0,0,0,0.5)',
                'zIndex': 1000,
                'justifyContent': 'center',
                'alignItems': 'center'
            }
            
            if button_id == 'set-universe-button':
                # Open modal with current constraint value
                # CRITICAL: Don't change the store when opening modal - only when applying
                open_style = base_style.copy()
                open_style['display'] = 'flex'
                return open_style, current_constraints or "", dash.no_update
            elif button_id == 'apply-universe-constraint-button':
                # Apply the constraint and close modal
                if input_value and input_value.strip():
                    logger.info(f"Setting universe constraint: {input_value}")
                    print(f"🌍 UNIVERSE: Setting constraint: {input_value}")
                    close_style = base_style.copy()
                    close_style['display'] = 'none'
                    # Return the constraint value to update the store
                    return close_style, input_value.strip(), input_value.strip()
                else:
                    # Clear constraint if input is empty
                    logger.info("Clearing universe constraint")
                    print(f"🌍 UNIVERSE: Clearing constraint")
                    close_style = base_style.copy()
                    close_style['display'] = 'none'
                    # Return empty string to clear the constraint
                    return close_style, "", None
            elif button_id == 'cancel-universe-constraint-button':
                # Close modal without changes
                close_style = base_style.copy()
                close_style['display'] = 'none'
                return close_style, input_value, current_constraints
            
            return modal_style, input_value, current_constraints
            
        except Exception as e:
            logger.error(f"Error handling universe modal: {e}")
            return False, input_value
    

    
    @app.callback(
        [Output('set-universe-button', 'children'),
         Output('set-universe-button', 'style')],
        Input('universe-constraints', 'data'),
        prevent_initial_call=True
    )
    def update_universe_button_appearance(constraints: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Update the Set Universe button appearance based on whether constraints are active.
        """
        try:
            if constraints:
                # Constraint is active - show green "Universe" button
                return "Universe", {
                    'padding': '4px 8px',
                    'background-color': '#4CAF50',  # Green
                    'color': 'white',
                    'border': 'none',
                    'border-radius': '3px',
                    'cursor': 'pointer',
                    'transition': 'background-color 0.2s',
                    'fontSize': '0.8em',
                    'height': 'fit-content',
                    'whiteSpace': 'nowrap'
                }
            else:
                # No constraint - show blue "Set Universe" button
                return "Set Universe", {
                    'padding': '4px 8px',
                    'background-color': '#2196F3',  # Blue
                    'color': 'white',
                    'border': 'none',
                    'border-radius': '3px',
                    'cursor': 'pointer',
                    'transition': 'background-color 0.2s',
                    'fontSize': '0.8em',
                    'height': 'fit-content',
                    'whiteSpace': 'nowrap'
                }
        except Exception as e:
            logger.error(f"Error updating universe button: {e}")
            # Return default blue button on error
            return "Set Universe", {
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
    
    # ============================================================================
    # ENRICHMENT MODAL CALLBACKS
    # ============================================================================
    
    @app.callback(
        Output('enrichment-modal', 'is_open'),
        [Input('open-enrichment-modal', 'n_clicks'),
         Input('close-enrichment-modal', 'n_clicks')],
        [State('enrichment-modal', 'is_open')],
        prevent_initial_call=True
    )
    def toggle_enrichment_modal(open_clicks: Optional[int], close_clicks: Optional[int], is_open: bool) -> bool:
        """
        Toggle the enrichment modal open/closed state.
        """
        try:
            ctx = callback_context
            if not ctx.triggered:
                return is_open
            
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if triggered_id == 'open-enrichment-modal':
                return True
            elif triggered_id == 'close-enrichment-modal':
                return False
            
            return is_open
            
        except Exception as e:
            logger.error(f"Enrichment modal toggle error: {e}")
            return is_open

    # ============================================================================
    # DEBUG/STATISTICS CALLBACKS
    # ============================================================================
    
    @app.callback(
        Output('status-indicator', 'children', allow_duplicate=True),
        Input('url', 'pathname'),
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def show_dedup_stats(pathname: str) -> html.Div:
        """
        Show deduplication statistics for debugging.
        
        This callback shows when queries are being deduplicated.
        """
        try:
            from .query_deduplicator import get_dedup_stats
            stats = get_dedup_stats()
            
            # Keep this callback inert to avoid overwriting the main status indicator
            from dash import no_update
            return no_update
                
        except ImportError:
            return html.Div("Dedup stats not available", style={'color': '#ffd43b'})
        except Exception as e:
            logger.error(f"Dedup stats error: {e}")
            return html.Div("Stats error", style={'color': '#ffd43b'})
    
    @app.callback(
        Output('universe-constraints', 'data', allow_duplicate=True),
        Input('set-universe-button', 'n_clicks'),
        [State('universe-constraints', 'data')],
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def clear_universe_constraint_on_click(n_clicks: Optional[int], current_constraints: Optional[str]) -> Optional[str]:
        """
        Clear the universe constraint when the button is clicked (if constraint is active).
        """
        try:
            if n_clicks and n_clicks > 0 and current_constraints:
                logger.info("Universe button clicked - clearing constraint")
                print(f"🌍 UNIVERSE: Button clicked, clearing constraint")
                return None
            raise dash.exceptions.PreventUpdate
        except Exception as e:
            logger.error(f"Error clearing universe constraint: {e}")
            raise dash.exceptions.PreventUpdate
    
    # REMOVED: This callback was causing conflicts with handle_initial_load
    # Both were triggered by app-ready and updating the same stores
    # The handle_initial_load callback now handles both initial data and autorange setup

    # ============================================================================
    # SAFETY CALLBACK - Ensures bbox is never used for initial loads
    # ============================================================================
    
    # REMOVED: This callback was causing infinite loops and memory issues
    # The force_autorange_on_startup callback is sufficient for startup autorange



    # Return the app with all callbacks registered
    return app

def create_status_content(data: Optional[List[Dict]], metadata: Optional[Dict]) -> html.Div:
    """
    Create status content - SURGICAL CHANGE: two-line status with minimal width.
    
    We intentionally avoid any dependence on total_count or estimated counts
    to prevent expensive COUNT queries on large datasets. This preserves
    functionality while removing the costly second status line.
    """
    try:
        record_count = len(data) if data else 0
        # If no data has been loaded yet, show a neutral prompt
        if record_count == 0:
            status_content = [
                html.Div("No queries yet", style={'color': 'white', 'font-size': '0.9em'})
            ]
            return html.Div(status_content, style={'text-align': 'center', 'line-height': '1.2'})
        
        # Render on two lines with minimal width
        status_content = [
            html.Div("Showing", style={'color': 'white', 'font-size': '0.9em'}),
            html.Div(f"{record_count:,} papers", style={'color': 'white', 'font-size': '0.9em', 'font-weight': 'bold'})
        ]
        return html.Div(status_content, style={'text-align': 'center', 'line-height': '1.2'})
    except Exception as e:
        logger.error(f"Error creating status content: {e}")
        return html.Div("Status error", style={'color': '#ffd43b'})

def create_fallback_figure() -> go.Figure:
    """Create a fallback figure when visualization fails."""
    return go.Figure(
        data=[
            go.Scatter(
                x=[0, 1, 2, 3, 4],
                y=[0, 1, 4, 9, 16],
                mode='markers',
                name='Fallback Data'
            )
        ],
        layout=go.Layout(
            title="Fallback Visualization",
            xaxis_title="X Axis",
            yaxis_title="Y Axis"
        )
    )

def get_fallback_values() -> Dict[str, Any]:
    """Get fallback values for failed operations."""
    return {
        'data': [],
        'figure': create_fallback_figure(),
        'view_state': {},
        'enrichment_state': {}
    }
