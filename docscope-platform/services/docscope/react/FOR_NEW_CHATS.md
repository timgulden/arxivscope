# For New Chats: React Frontend Rebuild

> **Quick start guide for new conversations working on the React frontend rebuild**

---

## **What You Need to Type**

**When starting a new conversation to work on the React frontend rebuild, type exactly this:**

```
Please read docscope-platform/services/docscope/react/FOR_NEW_CHATS.md to get up to speed on the React frontend rebuild task.
```

**That's it. One prompt.**

The chat will:
1. Read `FOR_NEW_CHATS.md`
2. Follow the instructions inside to read `CONTEXT_SUMMARY.md`, `REBUILD_PLAN.md`, and `STATE_MANAGEMENT_STRATEGY.md`
3. Understand the task and be ready to work

**Optional (but recommended)**: After the chat confirms it has read everything, you can ask:
```
Please confirm you understand the approach, functional programming principles, interceptor pattern, and state management strategy.
```

But this is optional - the chat should already understand these things from reading the documents.

---

## **What You Need to Know**

### **The Situation**
- ✅ React frontend code was lost during migration (submodule not bundled)
- ✅ Need to rebuild from scratch using Dash code (`docscope/components/`) as reference
- ✅ React project is initialized (Vite + React + TypeScript) but empty
- ✅ Legacy Dash frontend (`docscope/`) provides functionality reference

### **The Approach**
1. **Logic Layer First**: Implement pure functions with tests before any UI code
2. **Functional Programming**: All business logic must be pure functions (no side effects)
3. **Interceptor Pattern**: Use interceptors for cross-cutting concerns (logging, validation, error handling)
4. **State Management**: Single source of truth in logic layer (see `STATE_MANAGEMENT_STRATEGY.md`)

### **Key Documents**
- **`CONTEXT_SUMMARY.md`** - System overview, current environment, architecture
- **`REBUILD_PLAN.md`** - Complete phased rebuild plan (Logic → Testing → UI)
- **`STATE_MANAGEMENT_STRATEGY.md`** - State management architecture and patterns
- **`embedding-enrichment/DESIGN_PRINCIPLES.md`** - Core design principles
- **`docs/ARCHITECTURE/interceptor101.md`** - Interceptor pattern specification
- **`docs/ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md`** - Functional programming guide

### **Dash Code Reference** (`docscope/components/`)
- `view_management_fp.py` - View state management (pure functions)
- `data_fetching_fp.py` - Data fetching (pure functions)
- `interceptor_orchestrator.py` - Interceptor pattern implementation
- `component_contracts_fp.py` - Component contracts

---

## **Current Status**

- ✅ Planning: Complete (`REBUILD_PLAN.md`, `STATE_MANAGEMENT_STRATEGY.md`)
- ✅ Logic Layer: Complete (Phase 1) - Core types, contracts, interceptor framework, view management, data fetching, filters, visualization
- ✅ Testing: Partial (Phase 2) - Unit tests for core logic functions completed
- ✅ UI Layer: Partially Complete (Phase 3) - Basic framework, main canvas, metadata sidebar, semantic filter, date slider, home button
- ⏳ Remaining UI Features: Clustering toggle, universe filter, symbolization, count matches, sort/limit controls

**Next Step**: Implement remaining top bar controls (clustering, universe filter, symbolization, counts, sort/limit)

---

## **Key Components & Files Created**

### **UI Components** (`src/components/`)
- `MainCanvas.tsx` - Main Plotly scatter plot with pan/zoom, home button, status overlay
- `MetadataSidebar.tsx` - Paper details sidebar (always visible, 380px wide)
- `SemanticFilterModal.tsx` - Modal for semantic search with similarity threshold slider
- `DateSlider.tsx` - Continuous date range slider at bottom of canvas

### **Logic Layer** (`src/logic/`)
- `core/types.ts` - TypeScript type definitions (ViewState, FilterState, ApplicationState, etc.)
- `core/state-store.ts` - Central state store with reducer pattern
- `core/interceptor.ts` - Interceptor framework implementation
- `core/contracts.ts` - Component contracts (ViewManagement, DataFetching, Visualization)
- `view/view-management.ts` - View state extraction, validation, max extent handling
- `data/data-fetching.ts` - Fetch request creation and API integration
- `filters/filter-state.ts` - Filter state management (universe, date, semantic, bbox)
- `visualization/visualization.ts` - Plotly figure creation and styling

### **Hooks** (`src/hooks/`)
- `useAppState.ts` - React hook for accessing and updating application state
- `useDataFetch.ts` - Hook for API data fetching (`fetchPapers`, `fetchMaxExtent`)

### **Main App**
- `App.tsx` - Main application component with layout, header, and modal management

---

## **API Integration**

### **Endpoints Used**
- `GET /api/papers` - Fetch papers with filters (bbox, sql_filter, search_text, similarity_threshold, limit, fields)
- `GET /api/max-extent` - Get maximum extent (bounding box) of all 2D embeddings (no filters)
- `GET /api/papers/{id}` - Fetch individual paper details

### **API Base URL**
- Default: `http://localhost:5001/api`
- Configurable via `VITE_API_BASE_URL` environment variable

---

## **State Management Architecture**

### **State Structure**
- Single source of truth in `src/logic/core/state-store.ts`
- State split into: `view`, `filter`, `data`, `enrichment`, `ui`
- Pure reducer function handles all state updates

### **State Access**
- Use `useAppState()` hook in components: `const [state, dispatch] = useAppState()`
- Dispatch actions: `dispatch({ type: 'FILTER_UPDATE', payload: newFilter })`
- State updates are immutable and synchronous

### **State Actions**
- `VIEW_UPDATE` - Update view state (bbox, ranges, zoom/pan)
- `FILTER_UPDATE` - Update filter state (universe, date, semantic search)
- `DATA_LOAD_START/SUCCESS/ERROR` - Data loading states
- `MAX_EXTENT_LOADED` - Store max extent for home button
- `UI_SELECT_PAPER` - Paper selection for metadata sidebar

---

## **Quick Context Check**

After reading the documents, you should understand:

- ✅ **What**: Rebuilding React frontend from scratch
- ✅ **Why**: React code was lost (submodule not bundled)
- ✅ **How**: Logic layer first with tests, then UI
- ✅ **Principles**: Functional programming (pure functions) + Interceptor pattern
- ✅ **State**: Single source of truth in logic layer
- ✅ **Reference**: Dash code in `docscope/components/` provides functionality reference

---

*This document is designed to quickly get new chats up to speed. The actual detailed plans are in `REBUILD_PLAN.md` and `STATE_MANAGEMENT_STRATEGY.md`.*

