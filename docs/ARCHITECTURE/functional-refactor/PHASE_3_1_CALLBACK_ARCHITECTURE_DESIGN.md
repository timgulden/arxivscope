# Phase 3.1: New Dash Callback Architecture Design

## 🎯 **OBJECTIVE**
Design and implement new Dash callbacks that use our orchestrator system, replacing the monolithic `callbacks_simple.py` with a clean, functional architecture.

---

## 📊 **CURRENT STATE ANALYSIS**

### **Existing Callback Structure (callbacks_simple.py)**
- **Total Callbacks**: 19 callbacks (1257 lines)
- **Main Callback**: `unified_data_fetch_and_redraw` (100+ lines)
- **Mixed Responsibilities**: Data fetching + view management + figure creation
- **Complex Logic**: Imperative conditional logic scattered throughout
- **View Stability Issues**: Multiple competing view preservation strategies

### **Key Callbacks to Replace:**
1. **`unified_data_fetch_and_redraw`** - Main data + visualization callback
2. **`update_graph_on_source_change`** - Source filter handling
3. **`update_graph_on_year_change`** - Year filter handling
4. **`update_graph_on_search`** - Search functionality
5. **`update_view_ranges_store`** - View state management
6. **`update_enrichment_state`** - Enrichment state management

---

## 🏗️ **NEW CALLBACK ARCHITECTURE DESIGN**

### **Core Principle: Single Responsibility Per Callback**
Each callback will have ONE job and use our orchestrator for coordination:

```python
# OLD WAY (Mixed responsibilities)
@app.callback(
    [Output('data-store', 'data'),
     Output('graph-3', 'figure'),
     Output('status-indicator', 'children')],
    [Input('graph-3', 'relayoutData'),
     Input('selected-sources', 'data'),
     Input('year-range-slider', 'value')],
    [State('sidebar-search-text', 'value'),
     State('view-ranges-store', 'data')]
)
def unified_data_fetch_and_redraw(...):  # Does everything
    # View extraction + data fetching + figure creation + view preservation
    pass

# NEW WAY (Single responsibility)
@app.callback(
    Output('view-ranges-store', 'data'),
    Input('graph-3', 'relayoutData'),
    State('view-ranges-store', 'data')
)
def handle_view_change(relayout_data, current_view_ranges):
    """ONLY handles view changes - delegates to orchestrator"""
    return orchestrator.orchestrate_view_update(relayout_data, current_view_ranges)

@app.callback(
    Output('data-store', 'data'),
    [Input('view-ranges-store', 'data'),
     Input('selected-sources', 'data'),
     Input('year-range-slider', 'value')],
    [State('sidebar-search-text', 'value'),
     State('similarity-threshold', 'value')]
)
def handle_data_fetch(view_ranges, sources, year_range, search_text, threshold):
    """ONLY handles data fetching - delegates to orchestrator"""
    return orchestrator.orchestrate_data_fetch(view_ranges, sources, year_range, search_text, threshold)

@app.callback(
    Output('graph-3', 'figure'),
    [Input('data-store', 'data'),
     Input('view-ranges-store', 'data')],
    [State('enrichment-state', 'data')]
)
def handle_visualization(data, view_ranges, enrichment_state):
    """ONLY handles visualization - delegates to orchestrator"""
    return orchestrator.orchestrate_visualization(data, view_ranges, enrichment_state)
```

---

## 🔄 **CALLBACK ORCHESTRATION FLOW**

### **1. View Change Flow**
```
User Zoom/Pan → handle_view_change → orchestrator.orchestrate_view_update → Update view_ranges_store
```

### **2. Filter Change Flow**
```
Filter Change → handle_data_fetch → orchestrator.orchestrate_data_fetch → Update data_store
```

### **3. Visualization Update Flow**
```
Data/View Change → handle_visualization → orchestrator.orchestrate_visualization → Update graph-3
```

### **4. Complete Workflow Flow**
```
Any Change → Appropriate Handler → Orchestrator → State Update → Visualization Update
```

---

## 📝 **NEW CALLBACK IMPLEMENTATION PLAN**

### **Step 1: Create New Callback File**
- **File**: `docscope/components/callbacks_orchestrated.py`
- **Purpose**: New callbacks using our orchestrator
- **Structure**: One callback per responsibility

### **Step 2: Implement Core Callbacks**
1. **View Management Callback**
   - Input: `graph-3.relayoutData`
   - Output: `view-ranges-store.data`
   - Logic: Extract view, validate, store

2. **Data Fetching Callback**
   - Inputs: `view-ranges-store.data`, `selected-sources.data`, `year-range-slider.value`
   - Output: `data-store.data`
   - Logic: Build filters, fetch data, store

3. **Visualization Callback**
   - Inputs: `data-store.data`, `view-ranges-store.data`
   - Output: `graph-3.figure`
   - Logic: Create figure, apply view preservation

4. **Enrichment State Callback**
   - Inputs: `selected-sources.data`, `year-range-slider.value`
   - Output: `enrichment-state.data`
   - Logic: Update enrichment configuration

### **Step 3: Implement Supporting Callbacks**
5. **Status Update Callback**
   - Input: `data-store.data`
   - Output: `status-indicator.children`
   - Logic: Show data status

6. **Loading State Callback**
   - Inputs: Multiple data sources
   - Output: `cluster-busy.data`
   - Logic: Manage loading states

---

## 🧪 **TESTING STRATEGY**

### **Unit Tests**
- Test each callback in isolation
- Mock orchestrator responses
- Validate input/output contracts

### **Integration Tests**
- Test callback orchestration flow
- Validate state synchronization
- Test error handling

### **Dash Integration Tests**
- Test with real Dash components
- Validate view stability
- Test performance

---

## 🚀 **IMPLEMENTATION ORDER**

### **Phase 3.1.1: Core Callbacks (Priority 1)**
1. **View Management Callback** - Most critical for view stability
2. **Data Fetching Callback** - Core functionality
3. **Visualization Callback** - User experience

### **Phase 3.1.2: Supporting Callbacks (Priority 2)**
4. **Enrichment State Callback** - Feature completeness
5. **Status Update Callback** - User feedback
6. **Loading State Callback** - UX polish

### **Phase 3.1.3: Integration & Testing (Priority 3)**
7. **Integration with existing app**
8. **Performance testing**
9. **Error handling validation**

---

## 🔧 **TECHNICAL IMPLEMENTATION DETAILS**

### **Callback Registration**
```python
def register_orchestrated_callbacks(app):
    """Register new callbacks using our orchestrator."""
    
    # Import our orchestrator
    from .component_orchestrator_fp import (
        orchestrate_view_update,
        orchestrate_data_fetch,
        orchestrate_visualization
    )
    
    # Register each callback
    register_view_management_callback(app, orchestrate_view_update)
    register_data_fetching_callback(app, orchestrate_data_fetch)
    register_visualization_callback(app, orchestrate_visualization)
```

### **Error Handling**
```python
def safe_callback_execution(orchestrator_func, *args, **kwargs):
    """Wrapper for safe callback execution with error handling."""
    try:
        result = orchestrator_func(*args, **kwargs)
        return result
    except Exception as e:
        logger.error(f"Callback execution failed: {e}")
        # Return appropriate fallback values
        return get_fallback_values()
```

### **State Validation**
```python
def validate_callback_inputs(*args, **kwargs):
    """Validate callback inputs before processing."""
    # Validate view ranges
    # Validate filter parameters
    # Validate enrichment state
    # Return validation result
```

---

## 📊 **EXPECTED BENEFITS**

### **Immediate Benefits**
- **Cleaner Code**: Single responsibility per callback
- **Better Testing**: Each callback can be tested independently
- **Easier Debugging**: Clear separation of concerns
- **Improved Maintainability**: Changes isolated to specific areas

### **Long-term Benefits**
- **View Stability**: Centralized view management
- **Performance**: Optimized data flow
- **Scalability**: Easy to add new features
- **Reliability**: Robust error handling

---

## 🚨 **RISKS AND MITIGATION**

### **High Risk**
- **Breaking existing functionality** during migration
- **Performance regression** from new architecture

### **Mitigation Strategies**
- **Incremental replacement**: One callback at a time
- **Feature flags**: Easy rollback capability
- **Comprehensive testing**: Validate each step
- **Performance monitoring**: Track response times

---

## ✅ **SUCCESS CRITERIA**

### **Functional Requirements**
- [ ] All existing functionality preserved
- [ ] View stability improved
- [ ] No performance regression
- [ ] Error handling robust

### **Code Quality Requirements**
- [ ] Single responsibility per callback
- [ ] Pure functions throughout
- [ ] Comprehensive test coverage
- [ ] Clear separation of concerns

### **User Experience Requirements**
- [ ] No view jumping during operations
- [ ] Responsive UI interactions
- [ ] Clear loading states
- [ ] Helpful error messages

---

## 🔄 **NEXT STEPS**

1. **Create new callback file** (`callbacks_orchestrated.py`)
2. **Implement view management callback** (highest priority)
3. **Test with existing Dash app**
4. **Validate view stability**
5. **Continue with remaining callbacks**

---

**Status**: Design Complete - Ready for Implementation
**Priority**: HIGH - Core to Phase 3 success
**Estimated Time**: 2-3 days
**Dependencies**: Our orchestrator system (✅ Complete)
