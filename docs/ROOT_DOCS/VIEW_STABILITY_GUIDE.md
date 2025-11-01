# View Stability Guide for DocScope

## Overview

This document describes the solution to view stability issues in the DocScope visualization system, specifically how to prevent unwanted autoranging and view jumping when applying filters or changing data sources.

## The Problem

When users apply filters (especially source filters) or change data sources, the visualization would:
- Jump to show the full dataset (autoranging)
- Jump to off-center coordinates
- Reset zoom levels unexpectedly
- Cause inconsistent behavior between different types of filters

## Root Cause Analysis

### Why View Jumping Occurred

1. **Stale State Variables**: Using `current_figure` from `State('graph-3', 'figure')` provided stale/cached data that didn't reflect the user's current view
2. **Inconsistent View Management**: Different callback triggers used different approaches to preserve view state
3. **Autorange Conflicts**: Setting `autorange = False` without proper coordinate preservation led to unexpected behavior
4. **Bbox Extraction Errors**: Parsing bbox strings and applying them incorrectly caused coordinate mismatches

### The Key Insight

**`view_ranges` is the authoritative source for current view state**, not `current_figure`. The `view_ranges` store is specifically designed to preserve view state between callbacks and contains live, accurate coordinates.

## The Solution

### For Source Changes (`triggered == 'selected-sources'`)

```python
if triggered == 'selected-sources':
    # For source changes, use view_ranges to preserve the current view state
    logger.info("Source change - using view_ranges to preserve current view")
    fig.layout.xaxis.autorange = False
    fig.layout.yaxis.autorange = False
    
    # Use view_ranges (the authoritative source) instead of current_figure
    if view_ranges and 'xaxis' in view_ranges and 'yaxis' in view_ranges:
        try:
            x_range = view_ranges['xaxis']
            y_range = view_ranges['yaxis']
            if len(x_range) == 2 and len(y_range) == 2:
                x1, y1, x2, y2 = x_range[0], y_range[0], x_range[1], y_range[1]
                fig.layout.xaxis.range = [x1, x2]
                fig.layout.yaxis.range = [y1, y2]
                logger.info(f"Applied bbox from view_ranges: x=[{x1}, {x2}], y=[{y1}, {y2}]")
        except Exception as e:
            logger.warning(f"Error applying bbox from view_ranges: {e}")
    else:
        logger.warning("No view_ranges available for source change")
```

### For Other Operations (Zoom/Pan, Search, Year Filters)

```python
else:
    # For other operations, disable autorange and set explicit ranges
    logger.info("Non-source change - disabling autorange")
    fig.layout.xaxis.autorange = False
    fig.layout.yaxis.autorange = False
    
    # Set explicit ranges if we have a bbox (preserved view state)
    if view_state.get('bbox'):
        try:
            bbox_parts = view_state['bbox'].split(',')
            if len(bbox_parts) == 4:
                x1, y1, x2, y2 = map(float, bbox_parts)
                fig.layout.xaxis.range = [x1, x2]
                fig.layout.yaxis.range = [y1, y2]
                logger.info(f"Set explicit ranges from bbox: x=[{x1}, {x2}], y=[{y1}, {y2}]")
        except Exception as e:
            logger.warning(f"Error setting explicit ranges from bbox: {e}")
    else:
        # No bbox - set default ranges to prevent autorange
        logger.info("No bbox - setting default ranges to prevent autorange")
        fig.layout.xaxis.range = [-10, 10]  # Default range
        fig.layout.yaxis.range = [-10, 10]  # Default range
```

## Why This Solution Works

### 1. Authoritative Data Source
- **`view_ranges`**: Live, current view state specifically designed for preservation
- **`current_figure`**: Stale state variable that doesn't reflect current view

### 2. Consistent View Management
- **Source changes**: Use `view_ranges` for immediate view preservation
- **Other operations**: Use `view_state['bbox']` for explicit range setting
- **All operations**: Set `autorange = False` to prevent automatic rescaling

### 3. Proper Coordinate Handling
- **Direct access**: Extract x/y ranges directly from `view_ranges`
- **No string parsing**: Avoid bbox string parsing errors
- **Immediate application**: Apply coordinates directly to figure layout

## Implementation Details

### Required Imports
```python
from dash import callback_context, Input, Output, State, html, dcc
import plotly.graph_objects as go
```

### Callback Structure
```python
@app.callback(
    [Output('data-store', 'data'),
     Output('graph-3', 'figure'),
     Output('status-indicator', 'children')],
    [Input('graph-3', 'relayoutData'),
     Input('selected-sources', 'data'),
     Input('year-range-slider', 'value'),
     Input('sidebar-search-button', 'n_clicks'),
     Input('similarity-threshold', 'value')],
    [State('sidebar-search-text', 'value'),
     State('view-ranges-store', 'data'),  # ← Key for view preservation
     State('enrichment-state', 'data'),
     State('graph-3', 'figure')],
    prevent_initial_call=True
)
```

### View State Building
```python
# Extract current view state from view_ranges if available
if view_ranges and 'xaxis' in view_ranges and 'yaxis' in view_ranges:
    x_range = view_ranges['xaxis']
    y_range = view_ranges['yaxis']
    if len(x_range) == 2 and len(y_range) == 2:
        x1, y1, x2, y2 = x_range[0], y_range[0], x_range[1], y_range[1]
        view_state['bbox'] = f"{x1},{y1},{x2},{y2}"
        logger.info(f"Set bbox from view_ranges: {view_state['bbox']}")
```

## Common Pitfalls to Avoid

### ❌ Don't Use `current_figure` for View Preservation
```python
# WRONG - current_figure is stale
if current_figure and hasattr(current_figure, 'layout'):
    x_range = current_figure.layout.xaxis.range  # Stale data!
```

### ❌ Don't Mix Different View Management Approaches
```python
# WRONG - Inconsistent approach
if triggered == 'selected-sources':
    fig.layout.uirevision = 'preserve'  # One approach
else:
    fig.layout.xaxis.range = [x1, x2]   # Different approach
```

### ❌ Don't Forget to Disable Autorange
```python
# WRONG - Autorange will override view preservation
fig.layout.uirevision = 'preserve'
# Missing: fig.layout.xaxis.autorange = False
```

## Testing the Solution

### Test Case 1: Source Filtering
1. Zoom in on a specific area
2. Toggle a source filter (e.g., RAND Publications)
3. **Expected**: View stays exactly where it was, showing filtered data
4. **If it fails**: Check that `view_ranges` contains current coordinates

### Test Case 2: Year Filtering
1. Zoom in on a specific area
2. Change the year range slider
3. **Expected**: View stays exactly where it was, showing filtered data
4. **If it fails**: Check that `view_state['bbox']` is being set correctly

### Test Case 3: Zoom/Pan
1. Apply a filter that changes the view
2. Zoom or pan to a new area
3. **Expected**: New area is displayed with proper coordinates
4. **If it fails**: Check that bbox extraction from `relayoutData` is working

## Debugging Tips

### Check View State Variables
```python
logger.info(f"view_ranges: {view_ranges}")
logger.info(f"view_state['bbox']: {view_state.get('bbox')}")
logger.info(f"current_figure ranges: {current_figure.layout.xaxis.range if current_figure else 'None'}")
```

### Verify Coordinate Values
```python
if view_ranges and 'xaxis' in view_ranges:
    logger.info(f"view_ranges xaxis: {view_ranges['xaxis']}")
    logger.info(f"view_ranges yaxis: {view_ranges['yaxis']}")
```

### Check Figure Layout
```python
logger.info(f"Figure xaxis.autorange: {fig.layout.xaxis.autorange}")
logger.info(f"Figure xaxis.range: {fig.layout.xaxis.range}")
logger.info(f"Figure yaxis.autorange: {fig.layout.yaxis.autorange}")
logger.info(f"Figure yaxis.range: {fig.layout.yaxis.range}")
```

## Summary

The key to view stability in DocScope is:

1. **Use `view_ranges` for source changes** - It's the authoritative source for current view state
2. **Use `view_state['bbox']` for other operations** - Consistent with the existing view preservation logic
3. **Always disable autorange** - Set `autorange = False` to prevent automatic rescaling
4. **Apply coordinates immediately** - Don't rely on `uirevision` alone
5. **Test thoroughly** - Verify that each type of filter preserves the view correctly

This solution provides consistent, predictable view behavior across all filter types while maintaining the user's zoom level and pan position.
