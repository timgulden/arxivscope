# DocScope Callback Architecture & Data Fetching Design

## Overview

This document explains the callback architecture and data fetching system in DocScope. After extensive refactoring to resolve performance issues and callback conflicts, the system now uses a unified approach with clear separation of concerns.

## 🏗️ Architecture Overview

### **Core Principles**
1. **Single Responsibility**: Each callback has one clear purpose
2. **Unified Data Fetching**: One function handles all data retrieval
3. **Clear Data Flow**: Data flows from fetch → store → visualization
4. **No Callback Conflicts**: Proper use of `allow_duplicate` and `prevent_initial_call`

### **Key Components**
- **`handle_data_fetch`**: Main data fetching callback (filters, search, universe constraints)
- **`handle_zoom_data_fetch`**: Zoom/pan data fetching (bbox filtering)
- **`handle_visualization`**: Graph creation and updates
- **`handle_initial_load`**: Initial data loading and view setup

## 📊 Data Flow Architecture

```
User Action → Callback → Data Fetch → Store Update → Visualization
     ↓           ↓         ↓           ↓            ↓
Filter Change → handle_data_fetch → unified_data_fetcher → data-store → handle_visualization
Zoom/Pan    → handle_zoom_data_fetch → unified_data_fetcher → data-store → handle_visualization
Initial Load → handle_initial_load → unified_data_fetcher → data-store → handle_visualization
```

## 🔄 Callback Details

### **1. Main Data Fetching (`handle_data_fetch`)**

**Purpose**: Handle all filter-based data fetching (sources, year range, universe constraints, search)

**Inputs**:
- `search-button` clicks
- `universe-constraints` changes
- `selected-sources` changes  
- `year-range-slider` changes

**States**:
- `similarity-threshold`
- `enrichment-state`
- `graph-3` figure (for current zoom state)
- `search-text`
- `view-ranges-store`

**Outputs**:
- `data-store` (paper data)
- `data-metadata` (counts, timestamps)

**Key Features**:
- **Unified filtering**: Combines all constraints into single API call
- **Zoom preservation**: Extracts current zoom state from graph
- **Conflict prevention**: Skips during initial load to prevent conflicts

### **2. Zoom/Pan Data Fetching (`handle_zoom_data_fetch`)**

**Purpose**: Handle bbox-based data fetching when user zooms/pans

**Inputs**:
- `view-ranges-store` changes (bbox updates)

**States**:
- All filter states (sources, year range, universe constraints)
- `search-button` clicks (to determine if user has searched)

**Outputs**:
- `data-store` (bbox-filtered paper data)
- `data-metadata` (counts, timestamps)

**Key Features**:
- **Bbox filtering**: Only fetches papers within current view
- **Filter preservation**: Maintains all current filters
- **Initial load protection**: Skips during initial load

### **3. Visualization (`handle_visualization`)**

**Purpose**: Create and update graphs when data changes

**Inputs**:
- `data-store` changes
- `view-ranges-store` changes

**States**:
- `enrichment-state`
- `cluster-overlay`
- `show-clusters`

**Outputs**:
- `graph-3` figure

**Key Features**:
- **Automatic updates**: Triggers when data or view ranges change
- **View preservation**: Maintains current zoom/pan state
- **Cluster support**: Preserves clustering overlays

### **4. Initial Load (`handle_initial_load`)**

**Purpose**: Load initial data and set up default view

**Inputs**:
- `url` pathname changes

**States**:
- `year-range-slider` value
- `similarity-threshold` value

**Outputs**:
- `data-store` (initial paper data)
- `data-metadata` (initial counts)
- `view-ranges-store` (cleared for fresh start)

**Key Features**:
- **No filters**: Loads all papers initially
- **View clearing**: Clears any stale view ranges
- **Autorange**: Sets initial view to show all data

## 🎯 Data Fetching System

### **Unified Data Fetcher (`unified_data_fetcher.py`)**

**Purpose**: Single function to fetch papers with all constraints applied

**Key Features**:
- **Constraint combination**: Merges sources, year range, universe constraints, bbox
- **Single API call**: Ensures data consistency and performance
- **Error handling**: Graceful fallbacks for failed requests

**Constraint Processing**:
```python
# Build SQL filter from all constraints
sql_filter = build_unified_sql_filter(constraints)

# Make single API call
result = fetch_papers_from_api(
    limit=constraints.limit,
    bbox=constraints.bbox,
    sql_filter=sql_filter,
    similarity_threshold=constraints.similarity_threshold,
    search_text=constraints.search_text
)
```

### **Constraint Building**

**Source Filtering**:
```python
if constraints.sources and len(constraints.sources) > 0:
    source_list = [s.lower() for s in constraints.sources]
    quoted_sources = [f"'{s}'" for s in source_list]
    filter_parts.append(f"doctrove_source IN ({','.join(quoted_sources)})")
```

**Year Range Filtering**:
```python
if constraints.year_range and len(constraints.year_range) == 2:
    start_year, end_year = constraints.year_range
    filter_parts.append(f"(doctrove_primary_date >= '{start_year}-01-01' AND doctrove_primary_date <= '{end_year}-12-31')")
```

**Universe Constraints**:
```python
if constraints.universe_constraints and constraints.universe_constraints.strip():
    filter_parts.append(f"({constraints.universe_constraints})")
```

**Bbox Filtering**:
```python
if constraints.bbox:
    # Bbox is passed to backend for coordinate-based filtering
    # Backend applies: x BETWEEN bbox_x1 AND bbox_x2 AND y BETWEEN bbox_y1 AND bbox_y2
```

## 🚫 Conflict Prevention

### **Initial Load Protection**

**Problem**: Multiple callbacks trying to load data during startup
**Solution**: Strict `PreventUpdate` conditions

```python
# Skip if this is initial load
if search_clicks is None:
    raise dash.exceptions.PreventUpdate

# Skip if triggered by URL change (initial load)
if triggered_id == 'url':
    raise dash.exceptions.PreventUpdate
```

### **Callback Deduplication**

**Problem**: Multiple callbacks outputting to same stores
**Solution**: Proper use of `allow_duplicate` and `prevent_initial_call`

```python
@app.callback(
    [Output('data-store', 'data', allow_duplicate=True),
     Output('data-metadata', 'data', allow_duplicate=True)],
    # ... inputs and states ...
    prevent_initial_call=True,
    allow_duplicate=True
)
```

### **View State Management**

**Problem**: Stale bbox data causing incorrect data fetching
**Solution**: Always extract current zoom state from graph

```python
# Always preserve current zoom state from graph when available
if current_figure and 'layout' in current_figure:
    x_range = current_figure['layout']['xaxis'].get('range')
    y_range = current_figure['layout']['yaxis'].get('range')
    
    if x_range and y_range and len(x_range) == 2 and len(y_range) == 2:
        # Override stale store data with current graph state
        view_ranges = {
            'x_range': x_range,
            'y_range': y_range,
            'bbox': f"{x_range[0]},{y_range[0]},{x_range[1]},{y_range[1]}"
        }
```

## 🔧 Debugging & Troubleshooting

### **Common Issues**

1. **"No queries yet" message**
   - Check if `handle_data_fetch` is being triggered
   - Verify `search_clicks` is not `None`
   - Check callback context for triggered inputs

2. **Zoom not working**
   - Verify `handle_zoom_data_fetch` is listening to `view-ranges-store`
   - Check if bbox data is being passed correctly
   - Ensure zoom callback isn't being skipped

3. **Source filters not working**
   - Verify `selected-sources` is in `handle_data_fetch` inputs
   - Check if source filter changes trigger the callback
   - Verify SQL filter construction

4. **Callback conflicts**
   - Check for duplicate outputs to same stores
   - Verify `allow_duplicate=True` is used correctly
   - Ensure `prevent_initial_call` is set appropriately

### **Debug Logging**

**Callback Entry Logging**:
```python
# UNIQUE CALLBACK ID: handle_data_fetch
import time
callback_id = "handle_data_fetch"
timestamp = time.time()
print(f"🚀 CALLBACK {callback_id} ENTERED at {timestamp}")
print(f"🚀 CALLBACK {callback_id} - callback_context.triggered: {callback_context.triggered}")
```

**Data Flow Logging**:
```python
logger.info(f"🔍 DATA FETCH: Returning {len(data)} papers with metadata: {metadata}")
logger.info(f"🔍 VISUALIZATION DEBUG: Callback triggered by: {triggered_id}")
logger.info(f"🔍 ORCHESTRATOR DEBUG: View ranges: {view_ranges}")
```

## 📈 Performance Considerations

### **Optimizations Implemented**

1. **Single API Call**: All constraints combined into one request
2. **Bbox Filtering**: Only fetch papers within current view
3. **Callback Deduplication**: Prevent unnecessary re-executions
4. **View State Preservation**: Avoid unnecessary data refetching

### **Future Optimizations**

1. **Query Caching**: Cache results for identical constraint combinations
2. **Lazy Loading**: Load data only when needed
3. **Background Updates**: Update data in background without blocking UI

## 🔮 Future Development

### **Planned Improvements**

1. **Enrichment Coloring**: Restore automatic enrichment field detection
2. **Advanced Filtering**: Add more filter types (publication type, author, etc.)
3. **Real-time Updates**: Live data updates without manual refresh
4. **Performance Monitoring**: Track callback execution times and optimize

### **Architecture Evolution**

The current architecture provides a solid foundation for:
- Adding new filter types
- Implementing real-time features
- Scaling to larger datasets
- Adding new visualization types

## 📚 Related Documentation

- **[DEVELOPER_QUICK_REFERENCE.md](DEVELOPER_QUICK_REFERENCE.md)** - Development workflow
- **[API_DOCUMENTATION.md](../doctrove-api/API_DOCUMENTATION.md)** - Backend API reference
- **[DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)** - Database structure
- **[UNIVERSE_FILTER_GUIDE.md](docs/UNIVERSE_FILTER_GUIDE.md)** - Universe constraint syntax

---

*This document reflects the callback architecture as of the latest refactoring. For implementation details, see the actual callback files in `docscope/components/callbacks_orchestrated.py`.*
