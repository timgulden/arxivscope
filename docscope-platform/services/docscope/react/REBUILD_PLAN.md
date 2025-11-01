# DocScope React Frontend Rebuild Plan

> **Purpose**: Comprehensive plan for rebuilding the DocScope React frontend using strict functional programming principles and the Interceptor pattern.

> **Status**: Planned - Ready for implementation

> **Approach**: Logic layer first (with tests), then UI layer (referencing UI screenshots)

---

## **🚀 Getting Started (For New Chats)**

**If you're starting a new conversation to work on this React frontend rebuild:**

1. **Read the Big Picture**: Start with `CONTEXT_SUMMARY.md` (in project root) to understand:
   - Current system architecture
   - Environment setup (local laptop, ports 5001/3000/5432)
   - React frontend status (currently empty, needs rebuild)
   - Legacy Dash frontend (reference only)

2. **Read This Document**: This rebuild plan (`REBUILD_PLAN.md`) provides:
   - Complete phased approach (Logic layer → Testing → UI layer)
   - Functional programming principles to follow
   - Interceptor pattern usage
   - Detailed implementation steps

3. **Read State Management Strategy**: Review `STATE_MANAGEMENT_STRATEGY.md` (same directory) to understand:
   - Single source of truth approach
   - Where state lives (logic layer)
   - How to read/write state (hooks and reducers)
   - Integration with interceptor pattern

4. **Key Reference Documents**:
   - **Design Principles**: `embedding-enrichment/DESIGN_PRINCIPLES.md`
   - **Interceptor Pattern**: `docs/ARCHITECTURE/interceptor101.md`
   - **Functional Programming**: `docs/ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md`
   - **Dash Code Reference**: `docscope/components/` (for understanding current functionality)
     - `view_management_fp.py` - View state management (pure functions)
     - `data_fetching_fp.py` - Data fetching (pure functions)
     - `interceptor_orchestrator.py` - Interceptor pattern implementation
     - `component_contracts_fp.py` - Component contracts

**Quick Context Check**:
- ✅ React frontend code was lost (submodule not bundled)
- ✅ Need to rebuild from scratch using Dash code as reference
- ✅ Approach: Logic layer first with tests, then UI
- ✅ Must follow functional programming principles (pure functions)
- ✅ Must use Interceptor pattern for cross-cutting concerns
- ✅ State management: Single source of truth in logic layer

**Current Status**:
- Logic layer: Not yet implemented
- UI layer: Not yet implemented  
- React project: Initialized (Vite + React + TypeScript)
- Planning: Complete (this document)

---

## **Overview**

This document provides a detailed plan for rebuilding the lost React frontend code, following the successful approach used previously: identify basic functions from documentation and Dash code, implement them elegantly with tests, then build the UI.

### **Core Principles**

1. **Functional Programming First** - All business logic as pure functions with no side effects
2. **Interceptor Pattern** - Use interceptors for cross-cutting concerns (logging, validation, error handling)
3. **Logic Before UI** - Implement and test logic layer completely before building UI
4. **Contract-Based Architecture** - Clear interfaces between UI and logic layers
5. **Comprehensive Testing** - Unit tests for pure functions, integration tests for workflows

---

## **Phase 1: Logic Layer Foundation**

### **1.1 Setup TypeScript Logic Layer Structure**

**Location**: `docscope-platform/services/docscope/react/src/logic/`

**Structure**:
```
logic/
├── core/
│   ├── types.ts              # Core type definitions
│   ├── contracts.ts           # Service interface contracts
│   └── interceptor.ts         # Interceptor framework (TypeScript)
├── view/
│   ├── view-management.ts    # View state extraction and management
│   └── view-validation.ts    # View state validation
├── data/
│   ├── data-fetching.ts      # API data fetching operations
│   ├── data-transformation.ts # Data transformation and validation
│   └── data-caching.ts       # Caching logic
├── filters/
│   ├── filter-state.ts       # Filter state management
│   ├── filter-query.ts       # SQL filter generation
│   └── filter-validation.ts  # Filter validation
├── visualization/
│   ├── figure-creation.ts    # Plotly figure creation
│   ├── figure-update.ts      # Figure update logic
│   └── figure-validation.ts  # Figure validation
├── clustering/
│   ├── kmeans.ts             # K-means clustering algorithm
│   ├── voronoi.ts            # Voronoi region generation
│   └── llm-integration.ts    # LLM cluster summary generation
└── orchestration/
    ├── interceptor-stack.ts   # Interceptor stack execution
    ├── workflow-orchestration.ts # Complete workflow orchestration
    └── state-management.ts    # Application state management
```

**Key Requirements**:
- All functions must be pure (no side effects)
- All types must be defined explicitly
- All contracts must be defined before implementation
- No UI dependencies in logic layer

**Timeline**: Week 1, Days 1-2

### **1.2 Implement Core Types and Contracts**

**File**: `logic/core/types.ts`

**Types to Define**:
```typescript
// View State (from view_management_fp.py)
export interface ViewState {
  bbox: string | null;
  xRange: [number, number] | null;
  yRange: [number, number] | null;
  isZoomed: boolean;
  isPanned: boolean;
  lastUpdate: number;
}

// Filter State (from component_contracts_fp.py)
export interface FilterState {
  selectedSources: string[];
  yearRange: [number, number];
  searchText: string | null;
  similarityThreshold: number;
  lastUpdate: number;
}

// Enrichment State
export interface EnrichmentState {
  useClustering: boolean;
  useLlmSummaries: boolean;
  similarityThreshold: number;
  clusterCount: number;
  lastUpdate: number;
}

// Paper Data
export interface Paper {
  doctrovePaperId: string;
  doctroveTitle: string;
  doctroveSource: string;
  doctroveEmbedding2d: [number, number];
  doctrovePrimaryDate: string;
  // ... other fields from API
}

// Fetch Request
export interface FetchRequest {
  bbox: string | null;
  sqlFilter: string | null;
  searchText: string | null;
  limit: number;
  enrichmentParams: Record<string, any>;
  viewZoomed: boolean;
  xRange?: [number, number];
  yRange?: [number, number];
}

// Context (for interceptors)
export interface InterceptorContext {
  [key: string]: any;
  phase?: string;
  error?: string;
}
```

**File**: `logic/core/contracts.ts`

**Contracts to Define** (based on `component_contracts_fp.py`):
```typescript
// View Management Contract
export interface ViewManagementContract {
  extractViewFromRelayout: (relayoutData: any) => ViewState | null;
  extractViewFromFigure: (figure: any) => ViewState | null;
  preserveViewInFigure: (figure: any, viewState: ViewState) => any;
  validateViewState: (viewState: ViewState) => boolean;
}

// Data Fetching Contract
export interface DataFetchingContract {
  createFetchRequest: (
    viewState: ViewState,
    filterState: FilterState,
    enrichmentState: EnrichmentState
  ) => FetchRequest;
  fetchData: (fetchRequest: FetchRequest) => Promise<Paper[]>;
  validateFetchRequest: (fetchRequest: FetchRequest) => boolean;
}

// Visualization Contract
export interface VisualizationContract {
  createFigure: (
    papers: Paper[],
    filterState: FilterState,
    enrichmentState: EnrichmentState
  ) => any; // Plotly.Figure
  applyViewPreservation: (figure: any, viewState: ViewState) => any;
  validateFigure: (figure: any) => boolean;
}
```

**Timeline**: Week 1, Day 1

### **1.3 Implement Interceptor Framework**

**File**: `logic/core/interceptor.ts`

**Implementation** (based on `interceptor101.md` and `interceptor_orchestrator.py`):

```typescript
/**
 * Interceptor data structure following our established pattern.
 * An interceptor has 0-3 functions: enter, leave, error
 * All functions have the same signature: (context) => context
 */
export interface Interceptor {
  enter?: (context: InterceptorContext) => InterceptorContext;
  leave?: (context: InterceptorContext) => InterceptorContext;
  error?: (context: InterceptorContext) => InterceptorContext;
}

/**
 * Execute a stack of interceptors following the established pattern:
 * 1. Call enter functions (left to right)
 * 2. Call leave functions (right to left)
 * 3. On error, call error function of the failing interceptor
 */
export function executeInterceptorStack(
  interceptors: Interceptor[],
  initialContext: InterceptorContext
): InterceptorContext {
  let context = initialContext;
  const executedInterceptors: Interceptor[] = [];

  try {
    // Execute enter functions (left to right)
    for (const interceptor of interceptors) {
      executedInterceptors.push(interceptor);
      if (interceptor.enter) {
        context = interceptor.enter(context);
      }
    }

    // Execute leave functions (right to left)
    for (const interceptor of executedInterceptors.reverse()) {
      if (interceptor.leave) {
        context = interceptor.leave(context);
      }
    }

    return context;
  } catch (error) {
    // Find the interceptor that caused the error
    const errorIndex = executedInterceptors.length - 1;
    const errorInterceptor = executedInterceptors[errorIndex];

    // Add error to context
    context.error = error instanceof Error ? error.message : String(error);

    // Call error function if it exists
    if (errorInterceptor?.error) {
      context = errorInterceptor.error(context);
      // Clear error if handled
      if (context.error && !context.error) {
        delete context.error;
      }
    }

    // Execute leave functions for interceptors that were entered
    for (let i = errorIndex - 1; i >= 0; i--) {
      const interceptor = executedInterceptors[i];
      if (interceptor.leave) {
        context = interceptor.leave(context);
      }
    }

    return context;
  }
}
```

**Key Requirements**:
- Strict adherence to `interceptor101.md` pattern
- Each interceptor does ONE thing only
- No error handling in interceptors (handled by stack executor)
- All functions have signature: `(context) => context`

**Timeline**: Week 1, Day 2

### **1.4 Implement View Management (Pure Functions)**

**File**: `logic/view/view-management.ts`

**Functions to Implement** (based on `view_management_fp.py`):

```typescript
/**
 * Extract view state from Plotly relayoutData - PURE function
 */
export function extractViewFromRelayoutPure(
  relayoutData: any,
  currentTime: number
): ViewState | null {
  // Implementation based on view_management_fp.py:extract_view_from_relayout_pure
  // Must be truly pure - no side effects, no dependencies on external state
}

/**
 * Extract view state from existing figure - PURE function
 */
export function extractViewFromFigurePure(
  figure: any,
  currentTime: number
): ViewState | null {
  // Implementation based on view_management_fp.py:extract_view_from_figure_pure
}

/**
 * Validate view state - PURE function
 */
export function validateViewState(viewState: ViewState): boolean {
  // Implementation based on view_management_fp.py:validate_view_state
}

/**
 * Create default view state - PURE function
 */
export function createDefaultViewStatePure(currentTime: number): ViewState {
  // Implementation based on view_management_fp.py:create_default_view_state_pure
}

/**
 * Create view state from coordinate ranges - PURE function
 */
export function createViewStateFromRangesPure(
  xRange: [number, number],
  yRange: [number, number],
  currentTime: number
): ViewState {
  // Implementation based on view_management_fp.py:create_view_state_from_ranges_pure
}

/**
 * Preserve view in figure - PURE function
 */
export function preserveViewInFigure(
  figure: any,
  viewState: ViewState
): any {
  // Implementation based on view_management_fp.py:preserve_view_in_figure
}

/**
 * Check if view is stable between two states - PURE function
 */
export function isViewStable(
  currentView: ViewState,
  previousView: ViewState,
  stabilityThreshold: number = 0.001
): boolean {
  // Implementation based on view_management_fp.py:is_view_stable
}

/**
 * Merge two view states - PURE function
 */
export function mergeViewStates(
  primary: ViewState,
  secondary: ViewState
): ViewState {
  // Implementation based on view_management_fp.py:merge_view_states
}
```

**Wrapper Functions** (for dependency injection):
```typescript
/**
 * Extract view from relayout data - wrapper with injected time dependency
 */
export function extractViewFromRelayout(
  relayoutData: any,
  timestampProvider: () => number = () => Date.now()
): ViewState | null {
  return extractViewFromRelayoutPure(relayoutData, timestampProvider());
}
```

**Key Requirements**:
- All functions must be truly pure (no side effects)
- No dependencies on external state
- All functions must be testable in isolation
- Use timestamp provider injection for time-dependent functions

**Timeline**: Week 1, Days 3-4

### **1.5 Implement Data Fetching (Pure Functions)**

**File**: `logic/data/data-fetching.ts`

**Functions to Implement** (based on `data_fetching_fp.py`):

```typescript
/**
 * Create fetch request with all necessary parameters - PURE function
 */
export function createFetchRequest(
  viewState: ViewState,
  filterState: FilterState,
  enrichmentState: EnrichmentState
): FetchRequest {
  // Implementation based on data_fetching_fp.py:create_fetch_request
}

/**
 * Fetch data using provided data provider - PURE function with injected dependency
 */
export function fetchDataPure(
  fetchRequest: FetchRequest,
  dataProvider: (params: any) => Promise<Paper[]>
): Promise<Paper[]> {
  // Implementation based on data_fetching_fp.py:fetch_data_pure
}

/**
 * Validate fetch request - PURE function
 */
export function validateFetchRequest(fetchRequest: FetchRequest): boolean {
  // Implementation based on data_fetching_fp.py:validate_fetch_request
}

/**
 * Create minimal fetch request - PURE function
 */
export function createMinimalFetchRequest(): FetchRequest {
  // Implementation based on data_fetching_fp.py:create_minimal_fetch_request
}

/**
 * Optimize fetch request for performance - PURE function
 */
export function optimizeFetchRequest(fetchRequest: FetchRequest): FetchRequest {
  // Implementation based on data_fetching_fp.py:optimize_fetch_request
}
```

**Wrapper Functions** (for API integration):
```typescript
/**
 * Fetch data from API - wrapper with injected API dependency
 */
export async function fetchData(
  fetchRequest: FetchRequest,
  apiBaseUrl: string = 'http://localhost:5001/api'
): Promise<Paper[]> {
  // Create data provider function
  const dataProvider = async (params: any): Promise<Paper[]> => {
    const response = await fetch(`${apiBaseUrl}/papers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    const data = await response.json();
    return data.papers || [];
  };

  return fetchDataPure(fetchRequest, dataProvider);
}
```

**Key Requirements**:
- All functions must be pure
- API calls must be injected via dependency injection
- All validation must be pure functions
- Error handling must be pure (return Result types or throw)

**Timeline**: Week 1, Days 4-5

### **1.6 Implement Filter State Management**

**File**: `logic/filters/filter-state.ts`

**Functions to Implement** (based on `component_contracts_fp.py:FilterState`):

```typescript
/**
 * Create filter state - PURE function
 */
export function createFilterState(
  selectedSources: string[] = [],
  yearRange: [number, number] = [2000, new Date().getFullYear()],
  searchText: string | null = null,
  similarityThreshold: number = 0.8
): FilterState {
  return {
    selectedSources,
    yearRange,
    searchText,
    similarityThreshold,
    lastUpdate: Date.now(),
  };
}

/**
 * Update filter state - PURE function (immutable update)
 */
export function updateFilterState(
  current: FilterState,
  updates: Partial<FilterState>
): FilterState {
  return {
    ...current,
    ...updates,
    lastUpdate: Date.now(),
  };
}

/**
 * Convert filter state to SQL filter - PURE function
 */
export function filterStateToSqlFilter(filterState: FilterState): string {
  // Implementation based on component_contracts_fp.py:FilterState.to_sql_filter
}

/**
 * Validate filter state - PURE function
 */
export function validateFilterState(filterState: FilterState): boolean {
  // Implementation based on component_contracts_fp.py:FilterState.is_valid
}
```

**Timeline**: Week 1, Day 5

### **1.7 Implement Visualization Logic**

**File**: `logic/visualization/figure-creation.ts`

**Functions to Implement** (based on `graph_component.py` and Dash code):

```typescript
/**
 * Create scatter plot figure - PURE function
 */
export function createScatterFigure(
  papers: Paper[],
  filterState: FilterState,
  enrichmentState: EnrichmentState
): any {
  // Implementation based on graph_component.py
  // Must be pure - no side effects
  // Use plotly.js for figure creation
}

/**
 * Apply view preservation to figure - PURE function
 */
export function applyViewPreservation(
  figure: any,
  viewState: ViewState
): any {
  // Implementation based on view_management_fp.py:preserve_view_in_figure
}

/**
 * Validate figure - PURE function
 */
export function validateFigure(figure: any): boolean {
  // Check that figure has required structure
}
```

**Timeline**: Week 2, Days 1-2

### **1.8 Implement Clustering Logic**

**File**: `logic/clustering/kmeans.ts`

**Functions to Implement** (based on `clustering_service.py`):

```typescript
/**
 * Perform K-means clustering - PURE function
 */
export function kmeansClustering(
  papers: Paper[],
  clusterCount: number
): ClusterResult {
  // Pure implementation of K-means algorithm
  // No side effects, predictable outputs
}

/**
 * Generate Voronoi regions - PURE function
 */
export function generateVoronoiRegions(
  clusterCenters: [number, number][],
  bounds: { x: [number, number], y: [number, number] }
): VoronoiRegion[] {
  // Pure implementation using D3 Voronoi or similar
}

export interface ClusterResult {
  clusters: Cluster[];
  centers: [number, number][];
}

export interface Cluster {
  id: number;
  papers: Paper[];
  center: [number, number];
  summary?: string; // LLM-generated summary
}

export interface VoronoiRegion {
  id: number;
  points: [number, number][];
  clusterId: number;
}
```

**File**: `logic/clustering/llm-integration.ts`

**Functions to Implement** (based on clustering LLM integration):

```typescript
/**
 * Generate cluster summaries via LLM - PURE function with injected API
 */
export async function generateClusterSummaries(
  clusters: Cluster[],
  llmProvider: (papers: Paper[]) => Promise<string>
): Promise<Cluster[]> {
  // Pure function with injected LLM API dependency
  // No side effects except API call (which is injected)
}
```

**Timeline**: Week 2, Days 3-4

### **1.9 Implement Orchestration with Interceptors**

**File**: `logic/orchestration/interceptor-stack.ts`

**Interceptor Definitions** (based on `interceptor_orchestrator.py`):

```typescript
/**
 * View extraction interceptor - ONE responsibility only
 */
export const viewExtractionInterceptor: Interceptor = {
  enter: (context: InterceptorContext): InterceptorContext => {
    const relayoutData = context.relayoutData;
    if (relayoutData) {
      const viewState = extractViewFromRelayout(relayoutData);
      context.viewState = viewState;
      context.viewExtracted = true;
    }
    return context;
  },
};

/**
 * View validation interceptor - ONE responsibility only
 */
export const viewValidationInterceptor: Interceptor = {
  enter: (context: InterceptorContext): InterceptorContext => {
    const viewState = context.viewState;
    if (viewState) {
      const isValid = validateViewState(viewState);
      context.viewValid = isValid;
      if (!isValid) {
        console.warn('Invalid view state detected');
      }
    }
    return context;
  },
};

/**
 * Data request interceptor - ONE responsibility only
 */
export const dataRequestInterceptor: Interceptor = {
  enter: (context: InterceptorContext): InterceptorContext => {
    const { viewState, filterState, enrichmentState } = context;
    if (viewState && filterState && enrichmentState) {
      const fetchRequest = createFetchRequest(viewState, filterState, enrichmentState);
      context.fetchRequest = fetchRequest;
      context.requestCreated = true;
    }
    return context;
  },
};

/**
 * Data validation interceptor - ONE responsibility only
 */
export const dataValidationInterceptor: Interceptor = {
  enter: (context: InterceptorContext): InterceptorContext => {
    const fetchRequest = context.fetchRequest;
    if (fetchRequest) {
      const isValid = validateFetchRequest(fetchRequest);
      context.requestValid = isValid;
      if (!isValid) {
        console.warn('Invalid fetch request detected');
      }
    }
    return context;
  },
};

/**
 * Data fetch interceptor - ONE responsibility only
 */
export const dataFetchInterceptor: Interceptor = {
  enter: async (context: InterceptorContext): Promise<InterceptorContext> => {
    const fetchRequest = context.fetchRequest;
    if (fetchRequest && context.requestValid) {
      const data = await fetchData(fetchRequest);
      context.data = data;
      context.dataFetched = true;
    }
    return context;
  },
};

// Add cleanup and error interceptors following the same pattern
```

**File**: `logic/orchestration/workflow-orchestration.ts`

**Orchestration Functions**:

```typescript
/**
 * Orchestrate view update using interceptors
 */
export async function orchestrateViewUpdate(
  relayoutData: any
): Promise<ViewState | null> {
  const context: InterceptorContext = {
    relayoutData,
    phase: 'view_update',
  };

  const interceptors: Interceptor[] = [
    viewExtractionInterceptor,
    viewValidationInterceptor,
    viewPreservationInterceptor,
  ];

  const resultContext = executeInterceptorStack(interceptors, context);

  if (resultContext.viewValid) {
    return resultContext.viewState;
  }
  return null;
}

/**
 * Orchestrate data fetch using interceptors
 */
export async function orchestrateDataFetch(
  viewState: ViewState,
  filterState: FilterState,
  enrichmentState: EnrichmentState
): Promise<Paper[] | null> {
  const context: InterceptorContext = {
    viewState,
    filterState,
    enrichmentState,
    phase: 'data_fetch',
  };

  const interceptors: Interceptor[] = [
    dataRequestInterceptor,
    dataValidationInterceptor,
    dataFetchInterceptor,
  ];

  const resultContext = await executeInterceptorStack(interceptors, context);

  if (resultContext.dataFetched) {
    return resultContext.data;
  }
  return null;
}

/**
 * Orchestrate complete workflow
 */
export async function orchestrateCompleteWorkflow(
  workflowContext: InterceptorContext
): Promise<InterceptorContext> {
  // Phase 1: View Management
  if (workflowContext.relayoutData) {
    const viewState = await orchestrateViewUpdate(workflowContext.relayoutData);
    if (viewState) {
      workflowContext.viewState = viewState;
    }
  }

  // Phase 2: Data Fetching
  if (workflowContext.viewState && workflowContext.filterState) {
    const data = await orchestrateDataFetch(
      workflowContext.viewState,
      workflowContext.filterState,
      workflowContext.enrichmentState
    );
    if (data) {
      workflowContext.data = data;
    }
  }

  // Phase 3: Visualization
  if (workflowContext.data) {
    const figure = createScatterFigure(
      workflowContext.data,
      workflowContext.filterState,
      workflowContext.enrichmentState
    );
    workflowContext.figure = figure;
  }

  return workflowContext;
}
```

**Key Requirements**:
- Each interceptor does ONE thing only
- More interceptors preferred to larger interceptors
- No error handling in interceptors (handled by stack executor)
- All interceptors follow signature: `(context) => context`

**Timeline**: Week 2, Days 4-5

---

## **Phase 2: Comprehensive Testing**

### **2.1 Unit Tests for Pure Functions**

**Structure**: `logic/**/__tests__/`

**Test Requirements**:
- Every pure function must have unit tests
- Tests must verify pure function properties:
  - Same input always produces same output
  - No side effects
  - No dependencies on external state
- Test coverage target: >90%

**Example Test** (for view management):
```typescript
// logic/view/__tests__/view-management.test.ts
import {
  extractViewFromRelayoutPure,
  validateViewState,
  createDefaultViewStatePure,
} from '../view-management';

describe('View Management Pure Functions', () => {
  describe('extractViewFromRelayoutPure', () => {
    it('should extract view state from valid relayout data', () => {
      const relayoutData = {
        'xaxis.range[0]': 0,
        'xaxis.range[1]': 10,
        'yaxis.range[0]': 0,
        'yaxis.range[1]': 10,
      };
      const time = Date.now();
      const result = extractViewFromRelayoutPure(relayoutData, time);
      
      expect(result).toBeTruthy();
      expect(result?.bbox).toBe('0,0,10,10');
      expect(result?.isZoomed).toBe(true);
    });

    it('should return null for invalid relayout data', () => {
      const relayoutData = { autosize: true };
      const time = Date.now();
      const result = extractViewFromRelayoutPure(relayoutData, time);
      
      expect(result).toBeNull();
    });

    it('should be pure - same input always produces same output', () => {
      const relayoutData = {
        'xaxis.range[0]': 0,
        'xaxis.range[1]': 10,
        'yaxis.range[0]': 0,
        'yaxis.range[1]': 10,
      };
      const time = 1000;
      
      const result1 = extractViewFromRelayoutPure(relayoutData, time);
      const result2 = extractViewFromRelayoutPure(relayoutData, time);
      
      expect(result1).toEqual(result2);
    });
  });

  // More tests...
});
```

**Timeline**: Week 3, Days 1-3 (in parallel with Phase 1)

### **2.2 Interceptor Tests**

**Test Requirements**:
- Test interceptor stack execution
- Test enter/leave/error function calling order
- Test error handling and recovery
- Test context transformation

**Example Test**:
```typescript
// logic/core/__tests__/interceptor.test.ts
import { executeInterceptorStack, Interceptor } from '../interceptor';

describe('Interceptor Stack Execution', () => {
  it('should execute enter functions left to right', () => {
    const callOrder: string[] = [];
    const interceptors: Interceptor[] = [
      {
        enter: (ctx) => {
          callOrder.push('I1.enter');
          return ctx;
        },
      },
      {
        enter: (ctx) => {
          callOrder.push('I2.enter');
          return ctx;
        },
      },
    ];

    executeInterceptorStack(interceptors, {});
    
    expect(callOrder).toEqual(['I1.enter', 'I2.enter']);
  });

  it('should execute leave functions right to left', () => {
    const callOrder: string[] = [];
    const interceptors: Interceptor[] = [
      {
        enter: () => ({}),
        leave: (ctx) => {
          callOrder.push('I1.leave');
          return ctx;
        },
      },
      {
        enter: () => ({}),
        leave: (ctx) => {
          callOrder.push('I2.leave');
          return ctx;
        },
      },
    ];

    executeInterceptorStack(interceptors, {});
    
    expect(callOrder).toEqual(['I2.leave', 'I1.leave']);
  });

  it('should call error function on exception', () => {
    const errorHandler = jest.fn((ctx) => {
      delete ctx.error;
      return ctx;
    });
    
    const interceptors: Interceptor[] = [
      {
        enter: () => {
          throw new Error('Test error');
        },
        error: errorHandler,
      },
    ];

    const result = executeInterceptorStack(interceptors, {});
    
    expect(errorHandler).toHaveBeenCalled();
    expect(result.error).toBeUndefined();
  });
});
```

**Timeline**: Week 3, Day 3

### **2.3 Integration Tests**

**Test Requirements**:
- Test complete workflows
- Test interceptor stack integration
- Test API integration (with mocked API)
- Test data flow through complete system

**Timeline**: Week 3, Days 4-5

---

## **Phase 3: UI Layer Implementation**

### **3.1 Review UI Screenshots**

**Tasks**:
- Analyze UI screenshots to identify:
  - Component structure
  - Layout and styling
  - User interactions
  - Visual elements
- Create UI component specification document
- Map UI components to logic layer functions

**Timeline**: Week 4, Day 1

### **3.2 Setup React Component Structure**

**Location**: `src/components/`

**Structure**:
```
components/
├── layout/
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── MainContent.tsx
├── visualization/
│   ├── ScatterPlot.tsx
│   ├── ClusteringOverlay.tsx
│   └── VoronoiRegions.tsx
├── controls/
│   ├── SourceFilter.tsx
│   ├── YearRangeFilter.tsx
│   ├── SearchInput.tsx
│   └── ClusterControls.tsx
├── data/
│   ├── PaperList.tsx
│   ├── PaperDetail.tsx
│   └── StatusIndicator.tsx
└── hooks/
    ├── useViewState.ts
    ├── useFilterState.ts
    ├── useDataFetching.ts
    └── useOrchestration.ts
```

**Key Requirements**:
- All business logic must call logic layer functions
- UI components must be presentational (no business logic)
- Use React hooks for state management
- Integrate with logic layer through contracts

**Timeline**: Week 4, Days 1-2

### **3.3 Implement React Hooks**

**File**: `src/hooks/useOrchestration.ts`

**Implementation**:
```typescript
import { useState, useCallback } from 'react';
import { orchestrateCompleteWorkflow } from '../logic/orchestration/workflow-orchestration';
import { InterceptorContext } from '../logic/core/types';

export function useOrchestration() {
  const [context, setContext] = useState<InterceptorContext>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeWorkflow = useCallback(async (workflowContext: InterceptorContext) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await orchestrateCompleteWorkflow(workflowContext);
      setContext(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    context,
    loading,
    error,
    executeWorkflow,
  };
}
```

**Similar hooks for**:
- `useViewState` - View state management
- `useFilterState` - Filter state management
- `useDataFetching` - Data fetching operations
- `useClustering` - Clustering operations

**Timeline**: Week 4, Days 2-3

### **3.4 Implement UI Components**

**Requirements**:
- Each component must be presentational
- All business logic delegated to hooks/logic layer
- Use Plotly.js for visualization (same as Dash)
- Follow UI design from screenshots
- Responsive design
- Accessibility considerations

**Timeline**: Week 4, Days 3-5

### **3.5 Integrate UI with Logic Layer**

**Tasks**:
- Connect React components to logic layer through hooks
- Ensure all business logic flows through interceptor stacks
- Test UI integration with logic layer
- Verify contract compliance

**Timeline**: Week 5, Days 1-2

---

## **Phase 4: Performance Optimization**

### **4.1 Performance Testing**

**Tasks**:
- Test with large datasets (50,000+ papers)
- Measure render performance
- Measure data fetch performance
- Identify bottlenecks

**Timeline**: Week 5, Days 3-4

### **4.2 Optimization**

**Areas to Optimize**:
- Data fetching (caching, debouncing)
- Rendering (virtualization, lazy loading)
- Clustering (algorithm optimization)
- Memory usage

**Timeline**: Week 5, Day 5

---

## **Phase 5: Documentation and Finalization**

### **5.1 Documentation**

**Documents to Create**:
- Logic layer API documentation
- Interceptor usage guide
- Component documentation
- Integration guide

**Timeline**: Week 6, Days 1-2

### **5.2 Code Review and Refinement**

**Tasks**:
- Code review for FP principles compliance
- Code review for Interceptor pattern compliance
- Refactor as needed
- Final testing

**Timeline**: Week 6, Days 3-5

---

## **Success Criteria**

### **Logic Layer**
- ✅ All functions are pure (no side effects)
- ✅ All functions have unit tests (>90% coverage)
- ✅ All interceptors follow `interceptor101.md` pattern
- ✅ All contracts are defined and validated
- ✅ Integration tests pass

### **UI Layer**
- ✅ UI matches screenshots and requirements
- ✅ All business logic delegated to logic layer
- ✅ Components are presentational only
- ✅ UI integrates with logic layer through contracts
- ✅ Performance targets met

### **Overall**
- ✅ System follows functional programming principles
- ✅ System uses Interceptor pattern for cross-cutting concerns
- ✅ Code is maintainable and testable
- ✅ Documentation is complete
- ✅ Code review passed

---

## **References**

- **Design Principles**: `embedding-enrichment/DESIGN_PRINCIPLES.md`
- **Interceptor Pattern**: `docs/ARCHITECTURE/interceptor101.md`
- **Functional Programming Guide**: `docs/ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md`
- **Dash Code Reference**: `docscope/components/` (view_management_fp.py, data_fetching_fp.py, etc.)
- **Functional Specification**: `migration-planning/DOCSCOPE_FUNCTIONAL_SPECIFICATION.md`

---

## **Next Steps**

1. Review and approve this plan
2. Begin Phase 1: Logic Layer Foundation
3. Set up TypeScript project structure
4. Start implementing pure functions with tests

---

*Plan created: October 31, 2025*
*Status: Ready for implementation*

