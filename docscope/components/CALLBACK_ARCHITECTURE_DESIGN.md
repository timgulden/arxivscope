# Focused Callback Architecture Design

## 🎯 **Overview**

This document describes the new focused callback architecture that replaces the monolithic `callbacks_simple.py` with a clean, separated concerns design. The new architecture addresses the view stability issues and functional programming violations identified in Phase 0.1.

## 🚨 **Problems Solved**

### **1. Monolithic Callbacks (125+ lines)**
- **Before**: Single `unified_data_fetch_and_redraw` function handling 5+ responsibilities
- **After**: Separate, focused callbacks with single responsibilities

### **2. Mixed Concerns**
- **Before**: View management, data fetching, visualization, and state management all mixed together
- **After**: Clear separation with dedicated services for each concern

### **3. Complex View Preservation Logic**
- **Before**: View preservation logic scattered throughout data fetching callbacks
- **After**: Centralized `ViewManagementService` with clear, testable methods

### **4. Imperative Logic**
- **Before**: Complex if/elif/else chains and imperative state management
- **After**: Functional composition with pure functions and immutable data structures

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                    FOCUSED CALLBACK ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   VIEW MGMT     │  │   DATA FETCH    │  │ VISUALIZATION   │ │
│  │   CALLBACKS     │  │   CALLBACKS     │  │   CALLBACKS     │ │
│  │                 │  │                 │  │                 │ │
│  │ • update_view   │  │ • fetch_data    │  │ • update_viz    │ │
│  │ • track_zoom    │  │ • apply_filter  │  │ • create_fig    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                    │                    │           │
│           ▼                    ▼                    ▼           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ViewManagement   │  │DataFetching     │  │Visualization    │ │
│  │Service          │  │Service          │  │Service          │ │
│  │                 │  │                 │  │                 │ │
│  │ • extract_view  │  │ • create_request│  │ • create_figure │ │
│  │ • preserve_view │  │ • fetch_data    │  │ • apply_styling │ │
│  │ • validate_view │  │ • handle_errors │  │ • handle_errors │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                    │                    │           │
│           ▼                    ▼                    ▼           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   ViewState     │  │  FilterState    │  │EnrichmentState  │ │
│  │   (dataclass)   │  │  (dataclass)    │  │  (dataclass)    │ │
│  │                 │  │                 │  │                 │ │
│  │ • bbox          │  │ • sources       │  │ • active        │ │
│  │ • x_range       │  │ • year_range    │  │ • source        │ │
│  │ • y_range       │  │ • search_text   │  │ • table         │ │
│  │ • is_zoomed     │  │ • threshold     │  │ • field         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 **Core Components**

### **1. Data Structures (Dataclasses)**

#### **ViewState**
```python
@dataclass
class ViewState:
    bbox: Optional[str] = None          # "x1,y1,x2,y2" format
    x_range: Optional[List[float]] = None  # [min, max]
    y_range: Optional[List[float]] = None  # [min, max]
    is_zoomed: bool = False
    is_panned: bool = False
    
    def to_bbox_string(self) -> Optional[str]:
        """Convert ranges to bbox string format."""
```

**Purpose**: Encapsulates all view-related state in an immutable, testable structure.

#### **FilterState**
```python
@dataclass
class FilterState:
    selected_sources: List[str]
    year_range: List[int]
    search_text: Optional[str]
    similarity_threshold: float
    
    def to_sql_filter(self) -> str:
        """Convert filter state to SQL filter string."""
```

**Purpose**: Manages all filtering logic with pure functions for SQL generation.

#### **EnrichmentState**
```python
@dataclass
class EnrichmentState:
    active: bool = False
    source: Optional[str] = None
    table: Optional[str] = None
    field: Optional[str] = None
    
    def to_api_params(self) -> Dict[str, Any]:
        """Convert to API parameters."""
```

**Purpose**: Handles enrichment configuration with clean parameter conversion.

### **2. Service Classes**

#### **ViewManagementService**
```python
class ViewManagementService:
    @staticmethod
    def extract_view_from_relayout(relayout_data: Dict) -> Optional[ViewState]:
        """Extract view state from Dash relayoutData."""
    
    @staticmethod
    def extract_view_from_figure(figure: Dict) -> Optional[ViewState]:
        """Extract view state from existing figure."""
    
    @staticmethod
    def preserve_view_in_figure(figure: go.Figure, view_state: ViewState) -> go.Figure:
        """Apply view state to figure to preserve zoom/pan."""
    
    @staticmethod
    def validate_view_state(view_state: ViewState) -> bool:
        """Validate that view state has valid coordinates."""
```

**Responsibilities**:
- ✅ **View Extraction**: Parse Dash relayoutData and figure layouts
- ✅ **View Preservation**: Apply view state to figures
- ✅ **View Validation**: Ensure coordinate validity
- ✅ **Coordinate Conversion**: Transform between different formats

#### **DataFetchingService**
```python
class DataFetchingService:
    @staticmethod
    def create_fetch_request(
        view_state: ViewState,
        filter_state: FilterState,
        enrichment_state: EnrichmentState,
        target_records: int = 5000
    ) -> Dict[str, Any]:
        """Create a data fetch request with all necessary parameters."""
    
    @staticmethod
    def fetch_data(fetch_request: Dict[str, Any]) -> pd.DataFrame:
        """Fetch data from API using the request parameters."""
```

**Responsibilities**:
- ✅ **Request Building**: Compose API requests from state objects
- ✅ **Data Fetching**: Handle API calls and error handling
- ✅ **Parameter Management**: Coordinate all fetch parameters

#### **VisualizationService**
```python
class VisualizationService:
    @staticmethod
    def create_figure(
        data: pd.DataFrame,
        filter_state: FilterState,
        enrichment_state: EnrichmentState
    ) -> go.Figure:
        """Create a scatter plot figure with proper styling."""
```

**Responsibilities**:
- ✅ **Figure Creation**: Build Plotly figures from data
- ✅ **Styling Application**: Apply consistent visual styling
- ✅ **Error Handling**: Graceful fallbacks for visualization errors

### **3. Focused Callbacks**

#### **View Management Callbacks**
```python
@app.callback(
    Output('view-ranges-store', 'data'),
    [Input('graph-3', 'relayoutData')],
    [State('view-ranges-store', 'data')],
    prevent_initial_call=True
)
def update_view_ranges(relayout_data, current_ranges):
    """Update view ranges when user zooms/pans - VIEW MANAGEMENT ONLY."""
```

**Single Responsibility**: Track and store view state changes.

#### **Data Fetching Callbacks**
```python
@app.callback(
    Output('data-store', 'data'),
    [Input('view-ranges-store', 'data'),
     Input('selected-sources', 'data'),
     Input('year-range-slider', 'value'),
     Input('sidebar-search-button', 'n_clicks'),
     Input('similarity-threshold', 'value')],
    [State('sidebar-search-text', 'value'),
     State('enrichment-state', 'data'),
     State('graph-3', 'figure')],
    prevent_initial_call=True
)
def fetch_data_for_view(...):
    """Fetch data when view or filters change - DATA FETCHING ONLY."""
```

**Single Responsibility**: Coordinate data fetching based on state changes.

#### **Visualization Callbacks**
```python
@app.callback(
    Output('graph-3', 'figure'),
    [Input('data-store', 'data')],
    [State('selected-sources', 'data'),
     State('enrichment-state', 'data'),
     State('view-ranges-store', 'data')],
    prevent_initial_call=True
)
def update_visualization(data_records, selected_sources, enrichment_state, view_ranges):
    """Update visualization when data changes - VISUALIZATION ONLY."""
```

**Single Responsibility**: Create and update visualizations with view preservation.

## 🔄 **Data Flow**

### **1. User Interaction Flow**
```
User Zoom/Pan → update_view_ranges() → ViewManagementService.extract_view_from_relayout()
     ↓
view-ranges-store updated → fetch_data_for_view() → DataFetchingService.create_fetch_request()
     ↓
API call → data-store updated → update_visualization() → VisualizationService.create_figure()
     ↓
ViewManagementService.preserve_view_in_figure() → graph-3 updated
```

### **2. Filter Change Flow**
```
Filter Change → fetch_data_for_view() → FilterState.to_sql_filter()
     ↓
API call with new filters → data-store updated → update_visualization()
     ↓
ViewManagementService.preserve_view_in_figure() → view preserved
```

### **3. Enrichment Flow**
```
Enrichment Apply → apply_enrichment() → EnrichmentState.to_api_params()
     ↓
API call with enrichment → data-store updated → update_visualization()
     ↓
VisualizationService.create_figure() with enrichment → enriched visualization
```

## ✅ **Benefits of New Architecture**

### **1. Separation of Concerns**
- **View Management**: Handles only zoom/pan state
- **Data Fetching**: Manages only API calls and filtering
- **Visualization**: Creates only figures and styling
- **State Management**: Coordinates only between components

### **2. Functional Programming**
- **Pure Functions**: Each service method has no side effects
- **Immutable Data**: Dataclasses provide clear state contracts
- **Composition**: Services can be composed and tested independently
- **No Shared State**: Each callback manages its own state

### **3. Testability**
- **Unit Tests**: Each service can be tested in isolation
- **Mock Dependencies**: Easy to mock external dependencies
- **Clear Interfaces**: Dataclasses provide clear test contracts
- **Error Scenarios**: Easy to test error handling paths

### **4. Maintainability**
- **Single Responsibility**: Each function has one clear purpose
- **Clear Dependencies**: Explicit dependencies between components
- **Easy Debugging**: Clear separation makes issues easier to isolate
- **Code Reuse**: Services can be reused across different callbacks

### **5. View Stability**
- **Centralized View Logic**: All view operations in one service
- **Consistent Preservation**: Same logic applied everywhere
- **Validation**: View state validated before use
- **Clear Boundaries**: View logic never mixed with data or visualization

## 🧪 **Testing Strategy**

### **1. Unit Tests**
- **Service Tests**: Test each service method independently
- **Data Structure Tests**: Validate dataclass behavior
- **Error Handling**: Test all error scenarios
- **Edge Cases**: Test boundary conditions

### **2. Integration Tests**
- **Data Flow Tests**: Test complete data flow between services
- **Callback Tests**: Test callback interactions
- **State Synchronization**: Test state consistency

### **3. Mock Strategy**
- **API Mocks**: Mock external API calls
- **Dash Mocks**: Mock Dash callback context
- **Figure Mocks**: Mock Plotly figure operations

## 🚀 **Migration Path**

### **Phase 1: Parallel Implementation**
- Implement new focused callbacks alongside existing ones
- Test new architecture with subset of functionality
- Validate view stability improvements

### **Phase 2: Gradual Replacement**
- Replace one callback at a time
- Monitor for regressions
- Ensure backward compatibility

### **Phase 3: Cleanup**
- Remove old monolithic callbacks
- Clean up unused imports
- Update documentation

## 📊 **Performance Impact**

### **Expected Improvements**
- **Reduced Callback Complexity**: Simpler, faster callback execution
- **Better Caching**: Dash can better optimize focused callbacks
- **Reduced Memory**: No more large callback state objects
- **Faster Debugging**: Issues easier to isolate and fix

### **Monitoring Points**
- **Callback Execution Time**: Measure before/after performance
- **Memory Usage**: Monitor for memory leaks
- **View Stability**: Track view preservation success rate
- **User Experience**: Measure zoom/pan responsiveness

## 🔮 **Future Enhancements**

### **1. Advanced View Management**
- **View History**: Track view changes for undo/redo
- **View Bookmarks**: Save and restore specific views
- **View Synchronization**: Sync views across multiple components

### **2. Enhanced Error Handling**
- **Retry Logic**: Automatic retry for failed API calls
- **Fallback Views**: Graceful degradation for errors
- **User Feedback**: Better error messages and recovery options

### **3. Performance Optimizations**
- **Request Batching**: Batch multiple API requests
- **Data Caching**: Cache frequently accessed data
- **Lazy Loading**: Load data only when needed

## 📝 **Conclusion**

The new focused callback architecture represents a fundamental improvement in the DocScope frontend design. By separating concerns, implementing functional programming principles, and creating clear service boundaries, we've addressed the core architectural issues that were causing view stability problems.

The new architecture provides:
- **Clear separation** of view management, data fetching, and visualization
- **Functional programming** principles with pure functions and immutable data
- **Comprehensive testing** strategy for all components
- **Maintainable codebase** that's easier to debug and extend
- **Improved view stability** through centralized view management

This design serves as the foundation for Phase 1 (View Management Architecture) and provides a clear path forward for the complete refactor.
