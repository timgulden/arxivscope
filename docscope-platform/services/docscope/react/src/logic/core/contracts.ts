/**
 * Component Interface Contracts for DocScope React Frontend
 * 
 * This module defines the contracts that all services must implement,
 * using pure functions and interceptor patterns.
 * Following component_contracts_fp.py as reference.
 */

import type Plotly from 'plotly.js';
import type { ViewState, FilterState, EnrichmentState, FetchRequest, Paper } from './types';

/**
 * View Management Contract
 * Defines functions for managing view state (zoom/pan)
 */
export interface ViewManagementContract {
  extractViewFromRelayout: (relayoutData: any) => ViewState | null;
  extractViewFromFigure: (figure: any) => ViewState | null;
  preserveViewInFigure: (figure: any, viewState: ViewState) => any;
  validateViewState: (viewState: ViewState) => boolean;
}

/**
 * Data Fetching Contract
 * Defines functions for fetching data from API
 */
export interface DataFetchingContract {
  createFetchRequest: (
    viewState: ViewState,
    filterState: FilterState,
    enrichmentState: EnrichmentState
  ) => FetchRequest;
  fetchData: (fetchRequest: FetchRequest) => Promise<Paper[]>;
  validateFetchRequest: (fetchRequest: FetchRequest) => boolean;
}

/**
 * Visualization Contract
 * Defines functions for creating and managing visualizations
 */
export interface VisualizationContract {
  createFigure: (
    papers: Paper[],
    filterState: FilterState,
    enrichmentState: EnrichmentState
  ) => Plotly.Data[] | Plotly.Layout | Plotly.Config;
  applyViewPreservation: (figure: any, viewState: ViewState) => any;
  validateFigure: (figure: any) => boolean;
}

