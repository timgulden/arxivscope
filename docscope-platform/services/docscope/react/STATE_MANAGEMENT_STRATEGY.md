# State Management Strategy for DocScope React Frontend

> **Purpose**: Define the single source of truth for all application state, ensuring no duplication and clear access patterns.

> **Goal**: One place stores each piece of state; everything that needs that state reads from that place.

---

## **The Problem**

We need to decide where application state lives:
- View bounding box (current zoom/pan)
- Filter state (sources, year range, search text)
- Data state (loaded papers)
- Enrichment state (clustering, LLM summaries)
- UI state (loading indicators, error messages)

**Key Requirements**:
1. ✅ Single source of truth for each piece of state
2. ✅ No duplication across multiple places
3. ✅ Clear access patterns (how to read/write state)
4. ✅ Aligns with functional programming principles
5. ✅ Testable and maintainable

---

## **Analysis of Options**

### **Option 1: State in Logic Layer Only**

**Architecture**:
```
┌─────────────────────────────────────┐
│         Logic Layer                 │
│  ┌─────────────────────────────┐   │
│  │  Application State Store    │   │
│  │  • ViewState                 │   │
│  │  • FilterState               │   │
│  │  • DataState                 │   │
│  │  • EnrichmentState           │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  Pure Reducer Functions     │   │
│  │  • updateViewState()         │   │
│  │  • updateFilterState()       │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
           ▲              │
           │              │
           │ read         │ dispatch
           │              ▼
┌─────────────────────────────────────┐
│         UI Layer (React)            │
│  • Read state via hooks             │
│  • Dispatch actions via hooks       │
│  • No local state (except transient)│
└─────────────────────────────────────┘
```

**Pros**:
- ✅ Single source of truth in logic layer
- ✅ Pure reducer functions (testable)
- ✅ No business logic in UI layer
- ✅ State is just data (immutable)
- ✅ Follows functional programming principles

**Cons**:
- ⚠️ UI layer must go through logic layer for all state
- ⚠️ Potential overkill if only managing simple UI state

---

### **Option 2: State in UI Layer Only (React useState/useReducer)**

**Architecture**:
```
┌─────────────────────────────────────┐
│         UI Layer (React)            │
│  ┌─────────────────────────────┐   │
│  │  React State/Context         │   │
│  │  • useState/useReducer       │   │
│  │  • Context API               │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
           ▲              │
           │              │
           │ read         │ update
           │              │
┌─────────────────────────────────────┐
│         Logic Layer                 │
│  • Pure transformation functions    │
│  • Called by UI, but don't own state│
└─────────────────────────────────────┘
```

**Pros**:
- ✅ Uses React's built-in patterns
- ✅ Simple for UI-specific state

**Cons**:
- ❌ State mixed with presentation logic
- ❌ Harder to test business logic in isolation
- ❌ Violates functional programming separation of concerns
- ❌ Logic layer becomes stateless (can't own state)

---

### **Option 3: Hybrid Approach (Domain State vs UI State)**

**Architecture**:
```
┌─────────────────────────────────────┐
│         Logic Layer                 │
│  ┌─────────────────────────────┐   │
│  │  Domain State Store          │   │
│  │  • ViewState                 │   │
│  │  • FilterState               │   │
│  │  • DataState                 │   │
│  │  • EnrichmentState           │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
           ▲              │
           │              │
┌─────────────────────────────────────┐
│         UI Layer                     │
│  ┌─────────────────────────────┐   │
│  │  UI State (React)           │   │
│  │  • Loading indicators       │   │
│  │  • Modal open/closed         │   │
│  │  • Form input focus         │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Pros**:
- ✅ Clear separation: domain vs presentation
- ✅ Domain logic testable in logic layer
- ✅ UI state stays in UI layer

**Cons**:
- ⚠️ Risk of duplication if boundaries unclear
- ⚠️ Hard to determine "domain" vs "UI" for some state
- ⚠️ Still need coordination between layers

---

## **Recommended Approach: Single State Store in Logic Layer**

**Recommendation**: **Option 1** with clear patterns for state management

**Rationale**:
1. **Aligns with Functional Programming**: State is just immutable data; updates are pure functions
2. **Single Source of Truth**: All state in one place in logic layer
3. **Testable**: Pure reducer functions are easy to test
4. **No Duplication**: Clear that state lives in one place
5. **Follows Your Previous Pattern**: Your Dash code already centralizes state in stores

---

## **Implementation Architecture**

### **State Store Structure**

**Location**: `logic/core/state-store.ts`

```typescript
/**
 * Application State - Single Source of Truth
 * All application state lives here. Everything else reads from here.
 */
export interface ApplicationState {
  // View State - Current zoom/pan view
  view: ViewState;
  
  // Filter State - Current filters (sources, year, search)
  filter: FilterState;
  
  // Data State - Loaded papers and metadata
  data: {
    papers: Paper[];
    loading: boolean;
    error: string | null;
    lastFetched: number | null;
  };
  
  // Enrichment State - Clustering, LLM summaries
  enrichment: EnrichmentState;
  
  // UI State - Loading, errors, modals (minimal, transient only)
  ui: {
    loading: boolean;
    error: string | null;
    modalOpen: boolean;
    selectedPaperId: string | null;
  };
}

/**
 * Initial Application State
 */
export function createInitialState(): ApplicationState {
  return {
    view: createDefaultViewState(),
    filter: createDefaultFilterState(),
    data: {
      papers: [],
      loading: false,
      error: null,
      lastFetched: null,
    },
    enrichment: createDefaultEnrichmentState(),
    ui: {
      loading: false,
      error: null,
      modalOpen: false,
      selectedPaperId: null,
    },
  };
}
```

### **State Updates (Pure Reducers)**

**Location**: `logic/core/state-store.ts`

```typescript
/**
 * State Update Actions - Define what can happen
 */
export type StateAction =
  | { type: 'VIEW_UPDATE'; payload: ViewState }
  | { type: 'FILTER_UPDATE'; payload: FilterState }
  | { type: 'DATA_LOAD_START' }
  | { type: 'DATA_LOAD_SUCCESS'; payload: Paper[] }
  | { type: 'DATA_LOAD_ERROR'; payload: string }
  | { type: 'ENRICHMENT_UPDATE'; payload: EnrichmentState }
  | { type: 'UI_LOADING'; payload: boolean }
  | { type: 'UI_ERROR'; payload: string | null }
  | { type: 'UI_SELECT_PAPER'; payload: string | null };

/**
 * State Reducer - Pure function that updates state
 * Given current state + action, returns new state
 */
export function stateReducer(
  state: ApplicationState,
  action: StateAction
): ApplicationState {
  switch (action.type) {
    case 'VIEW_UPDATE':
      return {
        ...state,
        view: action.payload,
      };
    
    case 'FILTER_UPDATE':
      return {
        ...state,
        filter: action.payload,
      };
    
    case 'DATA_LOAD_START':
      return {
        ...state,
        data: {
          ...state.data,
          loading: true,
          error: null,
        },
      };
    
    case 'DATA_LOAD_SUCCESS':
      return {
        ...state,
        data: {
          ...state.data,
          papers: action.payload,
          loading: false,
          error: null,
          lastFetched: Date.now(),
        },
      };
    
    case 'DATA_LOAD_ERROR':
      return {
        ...state,
        data: {
          ...state.data,
          loading: false,
          error: action.payload,
        },
      };
    
    // ... more actions
    
    default:
      return state; // No change for unknown actions
  }
}

/**
 * Helper function to update view state
 * Pure function - takes state + view update, returns new state
 */
export function updateViewState(
  state: ApplicationState,
  viewUpdate: Partial<ViewState> | ViewState
): ApplicationState {
  const newView: ViewState = typeof viewUpdate === 'object' && !('bbox' in viewUpdate && 'xRange' in viewUpdate)
    ? { ...state.view, ...viewUpdate }
    : viewUpdate as ViewState;
  
  return stateReducer(state, {
    type: 'VIEW_UPDATE',
    payload: newView,
  });
}

/**
 * Helper function to update filter state
 */
export function updateFilterState(
  state: ApplicationState,
  filterUpdate: Partial<FilterState> | FilterState
): ApplicationState {
  const newFilter: FilterState = typeof filterUpdate === 'object' && !('selectedSources' in filterUpdate)
    ? { ...state.filter, ...filterUpdate }
    : filterUpdate as FilterState;
  
  return stateReducer(state, {
    type: 'FILTER_UPDATE',
    payload: newFilter,
  });
}

// Similar helper functions for other state updates...
```

### **State Store Provider (React Context)**

**Location**: `src/providers/StateProvider.tsx`

```typescript
import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import {
  ApplicationState,
  createInitialState,
  stateReducer,
  StateAction,
} from '../logic/core/state-store';

/**
 * State Context - Provides state and dispatch to all components
 */
interface StateContextValue {
  state: ApplicationState;
  dispatch: (action: StateAction) => void;
  
  // Convenience methods for common updates
  updateView: (viewUpdate: Partial<ViewState> | ViewState) => void;
  updateFilter: (filterUpdate: Partial<FilterState> | FilterState) => void;
  loadData: (papers: Paper[]) => void;
  setError: (error: string | null) => void;
}

const StateContext = createContext<StateContextValue | null>(null);

/**
 * State Provider Component
 * Wraps application and provides state to all children
 */
export function StateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(stateReducer, undefined, createInitialState);

  // Convenience methods
  const updateView = (viewUpdate: Partial<ViewState> | ViewState) => {
    dispatch({ type: 'VIEW_UPDATE', payload: viewUpdate as ViewState });
  };

  const updateFilter = (filterUpdate: Partial<FilterState> | FilterState) => {
    dispatch({ type: 'FILTER_UPDATE', payload: filterUpdate as FilterState });
  };

  const loadData = (papers: Paper[]) => {
    dispatch({ type: 'DATA_LOAD_SUCCESS', payload: papers });
  };

  const setError = (error: string | null) => {
    dispatch({ type: 'UI_ERROR', payload: error });
  };

  const value: StateContextValue = {
    state,
    dispatch,
    updateView,
    updateFilter,
    loadData,
    setError,
  };

  return (
    <StateContext.Provider value={value}>
      {children}
    </StateContext.Provider>
  );
}

/**
 * Hook to access state
 * Components use this to read state
 */
export function useStateStore() {
  const context = useContext(StateContext);
  if (!context) {
    throw new Error('useStateStore must be used within StateProvider');
  }
  return context;
}

/**
 * Hooks for reading specific parts of state
 */
export function useViewState(): ViewState {
  const { state } = useStateStore();
  return state.view;
}

export function useFilterState(): FilterState {
  const { state } = useStateStore();
  return state.filter;
}

export function useDataState() {
  const { state } = useStateStore();
  return state.data;
}

export function useEnrichmentState(): EnrichmentState {
  const { state } = useStateStore();
  return state.enrichment;
}
```

### **Usage in Components**

**Example: Reading State**

```typescript
// ScatterPlot.tsx
import { useViewState, useDataState } from '../providers/StateProvider';

export function ScatterPlot() {
  // Read state from single source of truth
  const viewState = useViewState();
  const { papers, loading } = useDataState();
  
  // Component logic uses state
  // No local state for view or data
}
```

**Example: Updating State**

```typescript
// FilterControls.tsx
import { useStateStore } from '../providers/StateProvider';
import { updateFilterState } from '../logic/core/state-store';

export function FilterControls() {
  const { state, updateFilter } = useStateStore();
  
  const handleSourceChange = (sources: string[]) => {
    // Update filter state - goes through single source of truth
    updateFilter({
      ...state.filter,
      selectedSources: sources,
    });
  };
}
```

**Example: Using Orchestration**

```typescript
// DataFetcher.tsx
import { useStateStore } from '../providers/StateProvider';
import { orchestrateDataFetch } from '../logic/orchestration/workflow-orchestration';

export function DataFetcher() {
  const { state, dispatch } = useStateStore();
  
  useEffect(() => {
    const fetchData = async () => {
      dispatch({ type: 'DATA_LOAD_START' });
      
      try {
        // Orchestration uses current state from store
        const papers = await orchestrateDataFetch(
          state.view,
          state.filter,
          state.enrichment
        );
        
        dispatch({ type: 'DATA_LOAD_SUCCESS', payload: papers });
      } catch (error) {
        dispatch({ 
          type: 'DATA_LOAD_ERROR', 
          payload: error instanceof Error ? error.message : 'Unknown error' 
        });
      }
    };
    
    fetchData();
  }, [state.view, state.filter, state.enrichment]);
}
```

---

## **Key Principles**

### **1. Single Source of Truth**

**Rule**: Each piece of state lives in exactly one place: `ApplicationState`

**Example**:
- ✅ View bounding box: `state.view.bbox`
- ❌ NOT: `localViewState.bbox` AND `state.view.bbox`
- ❌ NOT: `useState(bbox)` in component AND `state.view.bbox`

**How to Enforce**:
- All state reads go through `useStateStore()` or specific hooks
- All state updates go through reducer/dispatch
- No `useState` for domain state in components
- Only transient UI state (modal open/closed) can use `useState`

### **2. Immutable Updates**

**Rule**: State updates create new state objects, never mutate existing state

**Example**:
```typescript
// ✅ Good: Immutable update
const newState = {
  ...state,
  view: {
    ...state.view,
    bbox: newBbox,
  },
};

// ❌ Bad: Mutating state
state.view.bbox = newBbox; // NEVER DO THIS
```

**How to Enforce**:
- All updates go through reducer
- Reducer always returns new state object
- Use TypeScript readonly types where possible

### **3. Pure Reducer Functions**

**Rule**: State reducers are pure functions (no side effects)

**Example**:
```typescript
// ✅ Good: Pure reducer
function stateReducer(state: ApplicationState, action: StateAction): ApplicationState {
  switch (action.type) {
    case 'VIEW_UPDATE':
      return { ...state, view: action.payload };
    default:
      return state;
  }
}

// ❌ Bad: Impure reducer with side effects
function stateReducer(state: ApplicationState, action: StateAction): ApplicationState {
  console.log('Updating state'); // Side effect!
  localStorage.setItem('state', JSON.stringify(state)); // Side effect!
  return { ...state, view: action.payload };
}
```

**How to Enforce**:
- Reducers only transform state
- Side effects (API calls, logging) happen in orchestration layer
- Interceptors handle cross-cutting concerns (logging, validation)

### **4. Clear Access Patterns**

**Rule**: State access patterns are clear and consistent

**Reading State**:
```typescript
// ✅ Good: Use hooks
const viewState = useViewState();
const filterState = useFilterState();

// ✅ Good: Use full state if needed
const { state } = useStateStore();
const bbox = state.view.bbox;

// ❌ Bad: Direct state access (if not using context)
// const bbox = someGlobalState.view.bbox; // Not allowed
```

**Updating State**:
```typescript
// ✅ Good: Use dispatch with actions
dispatch({ type: 'VIEW_UPDATE', payload: newView });

// ✅ Good: Use convenience methods
updateView(newView);

// ❌ Bad: Direct state mutation
state.view = newView; // NEVER DO THIS
```

### **5. State Derivation**

**Rule**: Derived state is computed from base state, not stored separately

**Example**:
```typescript
// ✅ Good: Compute derived state
function useVisiblePapers() {
  const { papers } = useDataState();
  const filter = useFilterState();
  
  // Compute visible papers from base state
  return papers.filter(paper => 
    filter.selectedSources.includes(paper.doctroveSource)
  );
}

// ❌ Bad: Store derived state separately
const [visiblePapers, setVisiblePapers] = useState([]); // Duplication!
```

**How to Enforce**:
- Use computed values/selectors
- Memoize expensive computations with `useMemo`
- Never store what can be computed

---

## **Integration with Interceptor Pattern**

The state store integrates seamlessly with the interceptor pattern:

```typescript
/**
 * Interceptor that updates state
 */
const stateUpdateInterceptor: Interceptor = {
  enter: (context: InterceptorContext): InterceptorContext => {
    // Read state from context (injected by orchestration)
    const stateStore = context.stateStore;
    
    // Perform operation (e.g., fetch data)
    const data = context.data;
    
    // Update state through reducer
    const newState = stateReducer(stateStore.getState(), {
      type: 'DATA_LOAD_SUCCESS',
      payload: data,
    });
    
    // Update context with new state
    context.state = newState;
    return context;
  },
};

/**
 * Orchestration with state store
 */
export async function orchestrateDataFetchWithState(
  stateStore: StateStore,
  viewState: ViewState,
  filterState: FilterState
): Promise<Paper[]> {
  // Add state store to context
  const context: InterceptorContext = {
    stateStore,
    viewState,
    filterState,
    phase: 'data_fetch',
  };

  // Interceptors can read/write state through context
  const interceptors: Interceptor[] = [
    dataRequestInterceptor,
    dataValidationInterceptor,
    stateUpdateInterceptor, // Updates state when data fetched
  ];

  const resultContext = await executeInterceptorStack(interceptors, context);
  return resultContext.data;
}
```

---

## **Testing Strategy**

### **Testing State Store**

```typescript
// logic/core/__tests__/state-store.test.ts
import { stateReducer, createInitialState } from '../state-store';

describe('State Store', () => {
  it('should update view state immutably', () => {
    const initialState = createInitialState();
    const action = {
      type: 'VIEW_UPDATE' as const,
      payload: { bbox: '0,0,10,10', xRange: [0, 10], yRange: [0, 10], isZoomed: true, isPanned: true, lastUpdate: Date.now() },
    };
    
    const newState = stateReducer(initialState, action);
    
    expect(newState.view.bbox).toBe('0,0,10,10');
    expect(initialState.view.bbox).toBeNull(); // Original unchanged
    expect(newState).not.toBe(initialState); // New object created
  });

  it('should handle data load actions', () => {
    const initialState = createInitialState();
    const papers: Paper[] = [/* test papers */];
    
    // Start loading
    const loadingState = stateReducer(initialState, { type: 'DATA_LOAD_START' });
    expect(loadingState.data.loading).toBe(true);
    
    // Load success
    const successState = stateReducer(loadingState, {
      type: 'DATA_LOAD_SUCCESS',
      payload: papers,
    });
    expect(successState.data.loading).toBe(false);
    expect(successState.data.papers).toEqual(papers);
  });
});
```

### **Testing Components with State**

```typescript
// src/components/__tests__/ScatterPlot.test.tsx
import { render, screen } from '@testing-library/react';
import { StateProvider, createInitialState } from '../../providers/StateProvider';
import { ScatterPlot } from '../ScatterPlot';

describe('ScatterPlot', () => {
  it('should read view state from store', () => {
    const initialState = createInitialState();
    initialState.view = {
      bbox: '0,0,10,10',
      xRange: [0, 10],
      yRange: [0, 10],
      isZoomed: true,
      isPanned: true,
      lastUpdate: Date.now(),
    };
    
    render(
      <StateProvider initialState={initialState}>
        <ScatterPlot />
      </StateProvider>
    );
    
    // Component should use state from store
    expect(screen.getByText(/bbox.*0,0,10,10/i)).toBeInTheDocument();
  });
});
```

---

## **Summary**

### **Recommended Approach: Single State Store in Logic Layer**

✅ **All state in one place**: `ApplicationState` in logic layer  
✅ **Pure reducer functions**: Immutable updates, testable  
✅ **Clear access patterns**: Hooks for reading, dispatch for updating  
✅ **No duplication**: Each piece of state lives exactly once  
✅ **Functional programming**: State is data, updates are pure functions  
✅ **Integration ready**: Works with interceptor pattern  

### **What Lives Where**

**Logic Layer (`logic/core/state-store.ts`)**:
- ✅ `ApplicationState` type definition
- ✅ `createInitialState()` function
- ✅ `stateReducer()` pure function
- ✅ State update helper functions

**UI Layer (`src/providers/StateProvider.tsx`)**:
- ✅ React Context provider
- ✅ Hooks for reading state (`useViewState`, `useFilterState`, etc.)
- ✅ Convenience methods for updating state
- ❌ NO state definitions (those are in logic layer)

**Components**:
- ✅ Read state via hooks
- ✅ Update state via dispatch/convenience methods
- ✅ Can use `useState` ONLY for transient UI state (modal open, input focus)
- ❌ NO domain state in component `useState`

---

## **Next Steps**

1. ✅ Approve this strategy
2. Implement `ApplicationState` type in logic layer
3. Implement `stateReducer` function
4. Implement `StateProvider` React context
5. Update REBUILD_PLAN.md to include state management approach

---

*Strategy created: October 31, 2025*
*Status: Ready for implementation*

