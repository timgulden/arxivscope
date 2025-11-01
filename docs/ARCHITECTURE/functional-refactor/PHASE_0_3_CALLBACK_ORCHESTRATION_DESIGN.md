# Phase 0.3: Callback Orchestration Design

## 🎯 **Objective**

Design the orchestration patterns that coordinate data flow between our focused callbacks while maintaining separation of concerns. This phase addresses how the individual services communicate and how we avoid the callback complexity issues from the original architecture.

## 🏗️ **Current Architecture Status**

### **✅ Phase 0.2 Complete**
- **ViewManagementService** - Handles view state extraction and preservation
- **DataFetchingService** - Manages API requests and data fetching
- **VisualizationService** - Creates and updates visualizations
- **Data Structures** - Immutable state objects with clear contracts

### **🔧 Phase 0.3 Focus**
- **Callback Communication Patterns** - How callbacks talk to each other
- **Data Flow Orchestration** - Coordinating state changes across components
- **Dependency Management** - Avoiding callback chains and race conditions
- **State Synchronization** - Keeping all components in sync

## 🔄 **Data Flow Architecture**

### **1. User Interaction Flow**
```
User Action → Input Callback → State Update → Output Callback → UI Update
     ↓              ↓              ↓              ↓              ↓
  Zoom/Pan → update_view_ranges → view-ranges-store → fetch_data_for_view → data-store → update_visualization → graph-3
```

### **2. Filter Change Flow**
```
Filter Change → fetch_data_for_view → data-store → update_visualization → graph-3
     ↓              ↓              ↓              ↓              ↓
Source Filter → FilterState → API Request → New Data → Preserved View
```

### **3. Enrichment Flow**
```
Enrichment → apply_enrichment → enrichment-state + data-store → update_visualization → graph-3
     ↓              ↓              ↓              ↓              ↓
Apply Button → EnrichmentState → API Request → Enriched Data → Enhanced View
```

## 🎭 **Callback Orchestration Patterns**

### **Pattern 1: State-Driven Orchestration**
```python
# Instead of callback chains, use state as the orchestrator
@app.callback(
    Output('data-store', 'data'),
    [Input('view-ranges-store', 'data'),      # View changes
     Input('selected-sources', 'data'),       # Filter changes
     Input('year-range-slider', 'value'),     # Filter changes
     Input('sidebar-search-button', 'n_clicks')], # Search changes
    [State('sidebar-search-text', 'value'),
     State('enrichment-state', 'data'),
     State('graph-3', 'figure')],
    prevent_initial_call=True
)
def fetch_data_for_view(view_ranges, selected_sources, year_range, search_clicks, 
                        search_text, enrichment_state, current_figure):
    """Orchestrates data fetching based on ANY state change."""
    # Single responsibility: coordinate data fetching
    # No view management logic
    # No visualization logic
```

### **Pattern 2: Event-Driven State Updates**
```python
# Each callback updates only its own state
@app.callback(
    Output('view-ranges-store', 'data'),
    [Input('graph-3', 'relayoutData')],
    [State('view-ranges-store', 'data')],
    prevent_initial_call=True
)
def update_view_ranges(relayout_data, current_ranges):
    """Updates view state when user zooms/pans."""
    # Single responsibility: view state management
    # Triggers data fetch callback automatically via Input dependency
```

### **Pattern 3: Reactive Visualization**
```python
# Visualization reacts to data changes
@app.callback(
    Output('graph-3', 'figure'),
    [Input('data-store', 'data')],
    [State('selected-sources', 'data'),
     State('enrichment-state', 'data'),
     State('view-ranges-store', 'data')],
    prevent_initial_call=True
)
def update_visualization(data_records, selected_sources, enrichment_state, view_ranges):
    """Creates visualization when data changes."""
    # Single responsibility: visualization creation
    # Automatically preserves view via State dependency
```

## 🔗 **Dependency Management Strategy**

### **1. Input Dependencies (Triggers)**
```python
# Clear trigger hierarchy
Input('view-ranges-store', 'data')      # Primary trigger for data fetching
Input('selected-sources', 'data')       # Secondary trigger for data fetching
Input('year-range-slider', 'value')     # Secondary trigger for data fetching
Input('sidebar-search-button', 'n_clicks') # Secondary trigger for data fetching
```

### **2. State Dependencies (Context)**
```python
# Context information for decision making
State('sidebar-search-text', 'value')   # Search context
State('enrichment-state', 'data')       # Enrichment context
State('graph-3', 'figure')             # Current view context
```

### **3. Output Dependencies (Results)**
```python
# Clear result flow
Output('data-store', 'data')            # Data for visualization
Output('graph-3', 'figure')             # Visualization for user
Output('status-indicator', 'children')  # Status for user feedback
```

## 🚫 **Anti-Patterns to Avoid**

### **1. Callback Chains**
```python
# ❌ DON'T: Chain callbacks together
@app.callback(Output('step-2', 'data'), Input('step-1', 'data'))
def step_2(data): pass

@app.callback(Output('step-3', 'data'), Input('step-2', 'data'))
def step_3(data): pass

# ✅ DO: Use state as the orchestrator
@app.callback(Output('step-2', 'data'), Input('step-1', 'data'))
def step_2(data): pass

@app.callback(Output('step-3', 'data'), Input('step-1', 'data'))
def step_3(data): pass
```

### **2. Mixed Responsibilities**
```python
# ❌ DON'T: Mix concerns in single callback
def bad_callback(data, view, filters):
    # View management
    # Data fetching
    # Visualization
    # State management
    pass

# ✅ DO: Separate concerns
def view_callback(data): # View management only
    pass

def data_callback(view): # Data fetching only
    pass

def viz_callback(data): # Visualization only
    pass
```

### **3. Complex State Logic**
```python
# ❌ DON'T: Complex conditional logic in callbacks
def bad_callback(trigger, state1, state2, state3):
    if trigger == 'a' and state1 and not state2:
        if state3:
            # Complex nested logic
            pass
    elif trigger == 'b' and state2:
        # More complex logic
        pass

# ✅ DO: Use service methods for complex logic
def good_callback(trigger, state1, state2, state3):
    decision = DecisionService.make_decision(trigger, state1, state2, state3)
    return DecisionService.execute_decision(decision)
```

## 🎯 **Orchestration Design Principles**

### **1. Single Source of Truth**
- **View State**: `view-ranges-store` is the authoritative source
- **Data State**: `data-store` is the authoritative source
- **Filter State**: Individual filter components maintain their own state
- **Enrichment State**: `enrichment-state` is the authoritative source

### **2. Unidirectional Data Flow**
```
User Input → State Update → Data Fetch → Visualization Update
     ↓              ↓              ↓              ↓
  Zoom/Pan → view-ranges-store → data-store → graph-3
```

### **3. Reactive Updates**
- **No manual callback triggering**
- **State changes automatically trigger dependent callbacks**
- **Clear Input/State/Output relationships**

### **4. Error Isolation**
- **Each callback handles its own errors**
- **Service methods provide graceful fallbacks**
- **Errors don't cascade between callbacks**

## 🔧 **Implementation Strategy**

### **Phase 0.3.1: Orchestration Patterns**
1. **Design callback communication patterns**
2. **Implement state-driven orchestration**
3. **Test callback interactions**

### **Phase 0.3.2: Error Handling**
1. **Implement error isolation**
2. **Add graceful fallbacks**
3. **Test error scenarios**

### **Phase 0.3.3: Performance Optimization**
1. **Optimize callback execution order**
2. **Implement smart state updates**
3. **Test performance improvements**

## 📊 **Expected Benefits**

### **1. Simplified Callback Logic**
- **Before**: 125+ line monolithic callback
- **After**: 10-20 line focused callbacks

### **2. Clearer Data Flow**
- **Before**: Complex callback chains
- **After**: State-driven orchestration

### **3. Better Error Handling**
- **Before**: Errors cascade through callbacks
- **After**: Errors isolated to individual callbacks

### **4. Improved Maintainability**
- **Before**: Hard to modify individual concerns
- **After**: Easy to modify individual services

## 🧪 **Testing Strategy**

### **1. Unit Tests**
- **Service orchestration logic**
- **State transformation pipelines**
- **Error handling scenarios**

### **2. Integration Tests**
- **Callback interaction patterns**
- **State synchronization**
- **Data flow validation**

### **3. Performance Tests**
- **Callback execution time**
- **Memory usage patterns**
- **State update frequency**

## 🚀 **Next Steps**

### **Immediate Actions**
1. **Implement orchestration patterns** in focused callbacks
2. **Add error handling** to service methods
3. **Test callback interactions** with mock data

### **Success Criteria**
- ✅ **All callbacks have single responsibilities**
- ✅ **State-driven orchestration works correctly**
- ✅ **Error handling is graceful and isolated**
- ✅ **Performance meets requirements**

### **Ready for Phase 0.4**
- **Component interaction patterns**
- **Interface contracts**
- **Dependency injection design**

## 📝 **Summary**

Phase 0.3 focuses on the orchestration layer that coordinates our focused callbacks. By implementing state-driven orchestration, we eliminate callback chains and complex dependencies while maintaining clear separation of concerns.

The key insight is that **state should be the orchestrator, not callbacks**. Each callback focuses on its single responsibility, and state changes automatically trigger the appropriate updates through Dash's reactive system.

This approach provides:
- **Cleaner architecture** with clear boundaries
- **Better performance** through optimized state updates
- **Easier debugging** through isolated error handling
- **Improved maintainability** through focused responsibilities

**Status**: Ready for implementation
**Next Phase**: Phase 0.4 - Component Interaction Patterns
