/**
 * Core Type Definitions for DocScope React Frontend
 * 
 * All core types live here - single source of truth for type definitions.
 * Following functional programming principles: types are just data structures.
 */

/**
 * View State - Current zoom/pan view of the visualization
 * Pure data structure, no methods, no side effects
 */
export interface ViewState {
  bbox: string | null;
  xRange: [number, number] | null;
  yRange: [number, number] | null;
  isZoomed: boolean;
  isPanned: boolean;
  limit: number; // Number of records to fetch (default 5000, max 50000)
  lastUpdate: number;
}

/**
 * Filter State - Current filters (universe, sources, year, bbox, semantic)
 * Following Dash unified_data_fetcher.py: four distinct filter types with AND logic
 */
export interface FilterState {
  // Universe filter: custom SQL WHERE clause
  universeConstraints: string | null;
  
  // Source filter: selected paper sources
  selectedSources: string[];
  
  // Date filter: year range (null = no date filter)
  yearRange: [number, number] | null;
  
  // Semantic filter: search text + similarity threshold
  searchText: string | null;
  similarityThreshold: number;
  
  lastUpdate: number;
}

/**
 * Enrichment State - Clustering, LLM summaries configuration
 */
export interface EnrichmentState {
  useClustering: boolean;
  useLlmSummaries: boolean;
  similarityThreshold: number;
  clusterCount: number;
  lastUpdate: number;
  // Enrichment fields (from Dash enrichment_state)
  active: boolean;
  source: string | null;
  table: string | null;
  field: string | null;
}

/**
 * Paper Data - Individual paper with required fields
 * Following API response format: snake_case field names from backend
 */
export interface Paper {
  doctrove_paper_id: string;
  doctrove_title: string;
  doctrove_source: string;
  doctrove_embedding_2d: { x: number; y: number };
  doctrove_primary_date: string;
  // Additional optional fields as needed
  [key: string]: any;
}

/**
 * Fetch Request - Parameters for API data fetching
 * Following Dash unified_data_fetcher.py: combines all four filter types
 */
export interface FetchRequest {
  bbox: string | null;              // Spatial filter (bbox)
  sqlFilter: string | null;          // SQL filter (universe, sources, year)
  searchText: string | null;         // Semantic filter (search text)
  similarityThreshold: number;       // Semantic filter (threshold)
  limit: number;
  enrichmentParams: Record<string, any>;
  viewZoomed: boolean;
  xRange?: [number, number];
  yRange?: [number, number];
}

/**
 * Interceptor Context - Shared context passed between interceptors
 * Following interceptor101.md: context is just a dictionary
 */
export interface InterceptorContext {
  [key: string]: any;
  phase?: string;
  error?: string;
}

/**
 * Application State - Single source of truth for all application state
 * Following STATE_MANAGEMENT_STRATEGY.md: all state in one place
 */
export interface ApplicationState {
  view: ViewState;
  filter: FilterState;
  data: DataState;
  enrichment: EnrichmentState;
  ui: UiState;
}

/**
 * Data State - Loaded papers and metadata
 */
export interface DataState {
  papers: Paper[];
  loading: boolean;
  error: string | null;
  lastFetched: number | null;
  maxExtent: { xMin: number; xMax: number; yMin: number; yMax: number } | null;
}

/**
 * UI State - Loading indicators, errors, modals (minimal, transient only)
 */
export interface UiState {
  loading: boolean;
  error: string | null;
  modalOpen: boolean;
  selectedPaperId: string | null;
}

/**
 * State Update Actions - Define what can happen
 */
export type StateAction =
  | { type: 'VIEW_UPDATE'; payload: ViewState }
  | { type: 'FILTER_UPDATE'; payload: FilterState }
  | { type: 'DATA_LOAD_START' }
  | { type: 'DATA_LOAD_SUCCESS'; payload: Paper[] }
  | { type: 'DATA_LOAD_ERROR'; payload: string }
  | { type: 'MAX_EXTENT_LOADED'; payload: { xMin: number; xMax: number; yMin: number; yMax: number } }
  | { type: 'ENRICHMENT_UPDATE'; payload: EnrichmentState }
  | { type: 'UI_LOADING'; payload: boolean }
  | { type: 'UI_ERROR'; payload: string | null }
  | { type: 'UI_SELECT_PAPER'; payload: string | null };

/**
 * API Max Extent Response - Response from /api/max-extent endpoint
 */
export interface MaxExtentResponse {
  success: boolean;
  extent?: {
    x_min: number;
    x_max: number;
    y_min: number;
    y_max: number;
  };
  error?: string;
}

