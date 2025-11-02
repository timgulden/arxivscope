/**
 * Application State Store for DocScope React Frontend
 * 
 * Single source of truth for all application state.
 * Following STATE_MANAGEMENT_STRATEGY.md: all state in one place.
 * 
 * Pure functions for state management - NO SIDE EFFECTS.
 */

import type {
  ApplicationState,
  StateAction,
  ViewState,
  EnrichmentState,
} from './types';


/**
 * Create initial application state - TRULY PURE function
 */
export function createInitialState(): ApplicationState {
  return {
    view: {
      bbox: null,
      xRange: null,
      yRange: null,
      isZoomed: false,
      isPanned: false,
      limit: 5000,
      lastUpdate: Date.now(),
    },
    filter: {
      universeConstraints: null,
      selectedSources: [],
      yearRange: null,
      searchText: null,
      similarityThreshold: 0.5,
      lastUpdate: Date.now(),
    },
    data: {
      papers: [],
      loading: false,
      error: null,
      lastFetched: null,
      maxExtent: null,
    },
    enrichment: {
      useClustering: false,
      useLlmSummaries: false,
      similarityThreshold: 0.8,
      clusterCount: 10,
      lastUpdate: Date.now(),
      active: false,
      source: null,
      table: null,
      field: null,
    },
    ui: {
      loading: false,
      error: null,
      modalOpen: false,
      selectedPaperId: null,
    },
  };
}

/**
 * State reducer - TRULY PURE function
 * Transforms state immutably based on actions
 */
export function stateReducer(state: ApplicationState, action: StateAction): ApplicationState {
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
          papers: action.payload,
          loading: false,
          error: null,
          lastFetched: Date.now(),
          maxExtent: state.data.maxExtent,
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

    case 'MAX_EXTENT_LOADED':
      return {
        ...state,
        data: {
          ...state.data,
          maxExtent: action.payload,
        },
      };

    case 'ENRICHMENT_UPDATE':
      return {
        ...state,
        enrichment: action.payload,
      };

    case 'UI_LOADING':
      return {
        ...state,
        ui: {
          ...state.ui,
          loading: action.payload,
        },
      };

    case 'UI_ERROR':
      return {
        ...state,
        ui: {
          ...state.ui,
          error: action.payload,
        },
      };

    case 'UI_SELECT_PAPER':
      return {
        ...state,
        ui: {
          ...state.ui,
          selectedPaperId: action.payload,
        },
      };

    default:
      return state;
  }
}

// ============================================================================
// PURE HELPER FUNCTIONS FOR STATE UPDATES
// ============================================================================
// These functions create new state objects immutably.
// They are pure functions that can be unit tested.

/**
 * Toggle clustering in enrichment state - PURE function
 */
export function toggleClustering(currentEnrichment: EnrichmentState): EnrichmentState {
  return {
    ...currentEnrichment,
    useClustering: !currentEnrichment.useClustering,
    lastUpdate: Date.now(),
  };
}

/**
 * Update cluster count in enrichment state - PURE function with validation
 */
export function updateClusterCount(
  currentEnrichment: EnrichmentState,
  clusterCount: number
): EnrichmentState | null {
  // Validate cluster count (max 99)
  if (isNaN(clusterCount) || clusterCount < 2 || clusterCount > 99) {
    return null; // Invalid - return null to signal validation failure
  }

  return {
    ...currentEnrichment,
    clusterCount,
    useClustering: true, // Enable clustering when count is set
    lastUpdate: Date.now(),
  };
}

/**
 * Update view limit - PURE function with validation
 */
export function updateViewLimit(
  currentView: ViewState,
  limit: number
): ViewState | null {
  // Validate limit (max 99999)
  if (isNaN(limit) || limit < 100 || limit > 99999) {
    return null; // Invalid - return null to signal validation failure
  }

  return {
    ...currentView,
    limit,
    lastUpdate: Date.now(),
  };
}

/**
 * Parse and validate cluster count from string input - PURE function
 */
export function parseClusterCount(input: string): number | null {
  if (input === '') {
    return null; // Allow empty input while typing
  }

  const num = parseInt(input, 10);
  if (isNaN(num) || num < 2 || num > 99) {
    return null;
  }

  return num;
}

/**
 * Parse and validate limit from string input - PURE function
 */
export function parseLimit(input: string): number | null {
  const num = parseInt(input, 10);
  if (isNaN(num) || num < 100 || num > 99999) {
    return null;
  }

  return num;
}

