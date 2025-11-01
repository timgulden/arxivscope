/**
 * Visualization Pure Functions for DocScope React Frontend
 * 
 * Implements visualization operations using pure functions.
 * Following functional programming principles: NO SIDE EFFECTS.
 */

import type { ViewState, FilterState, EnrichmentState, Paper } from '../core/types';

/**
 * Wrap title at word boundaries - PURE function
 * Wraps at approximately maxLength characters, breaking at spaces
 */
function wrapTitle(title: string, maxLength: number = 50): string {
  if (title.length <= maxLength) {
    return title;
  }
  
  // Find the last space before maxLength
  const truncated = title.substring(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');
  
  if (lastSpace > 0) {
    return title.substring(0, lastSpace) + '<br>' + title.substring(lastSpace + 1);
  }
  
  // No space found, just truncate
  return title;
}

/**
 * Plotly figure data structure - minimal representation
 * Following Dash visualization: we build the data structure, Plotly renders it
 */
export interface PlotlyTrace {
  x: number[];
  y: number[];
  mode: 'markers';
  marker: {
    size: number;
    opacity: number;
    color: string | string[];
    line?: {
      width: number;
      color: string;
    };
  };
  text?: string[];
  customdata?: any[]; // Store paper IDs for click/hover events
  hovertemplate: string;
  name: string;
  type: 'scatter';
  showlegend: boolean;
}

export interface PlotlyLayout {
  plot_bgcolor: string;
  paper_bgcolor: string;
  xaxis: {
    showgrid: boolean;
    zeroline: boolean;
    visible: boolean;
    showline: boolean;
    showticklabels: boolean;
    autorange: boolean;
    range?: [number, number];
  };
  yaxis: {
    showgrid: boolean;
    zeroline: boolean;
    visible: boolean;
    showline: boolean;
    showticklabels: boolean;
    autorange: boolean;
    range?: [number, number];
  };
  margin: { l: number; r: number; t: number; b: number };
  showlegend: boolean;
  legend?: {
    x: number;
    y: number;
    bgcolor: string;
  };
  dragmode: 'pan';
  hovermode: 'closest';
}

export interface PlotlyFigure {
  data: PlotlyTrace[];
  layout: PlotlyLayout;
}

/**
 * Create empty figure - TRULY PURE function
 */
export function createEmptyFigure(): PlotlyFigure {
  return {
    data: [],
    layout: createDefaultLayout(),
  };
}

/**
 * Create default layout - TRULY PURE function
 * Following Dash dark theme from screenshots
 */
function createDefaultLayout(): PlotlyLayout {
  return {
    plot_bgcolor: '#2b2b2b',
    paper_bgcolor: '#2b2b2b',
    xaxis: {
      showgrid: false,
      zeroline: false,
      visible: false,
      showline: false,
      showticklabels: false,
      autorange: true,
    },
    yaxis: {
      showgrid: false,
      zeroline: false,
      visible: false,
      showline: false,
      showticklabels: false,
      autorange: true,
    },
    margin: { l: 0, r: 0, t: 0, b: 0 },
    showlegend: false,
    dragmode: 'pan',
    hovermode: 'closest',
  };
}

/**
 * Create figure from papers - TRULY PURE function
 * Main entry point for visualization
 */
export function createFigure(
  papers: Paper[],
  viewState: ViewState,
  filterState: FilterState,
  enrichmentState: EnrichmentState
): PlotlyFigure {
  if (!papers || papers.length === 0) {
    return createEmptyFigure();
  }

  // Create trace
  const trace = createScatterTrace(papers, filterState, enrichmentState);

  // Create layout
  const layout = createLayoutWithView(viewState);

  return {
    data: [trace],
    layout,
  };
}

/**
 * Create scatter trace - TRULY PURE function
 * Following Dash: white 20% opacity markers
 */
function createScatterTrace(
  papers: Paper[],
  filterState: FilterState,
  enrichmentState: EnrichmentState
): PlotlyTrace {
  // Extract coordinates
  const x = papers.map(p => p.doctrove_embedding_2d.x);
  const y = papers.map(p => p.doctrove_embedding_2d.y);
  const texts = papers.map(p => wrapTitle(p.doctrove_title));
  const customdata = papers.map(p => p.doctrove_paper_id); // Store paper IDs for click events

  // Determine color based on enrichment or source
  const color = getMarkerColor(papers, filterState, enrichmentState);

  return {
    x,
    y,
    mode: 'markers',
    marker: {
      size: 8,
      opacity: 0.5, // Increased opacity - less transparent
      color,
      line: {
        width: 0, // No outline as per Dash code
        color: 'white',
      },
    },
    text: texts,
    customdata,
    hovertemplate: '%{text}<extra></extra>',
    name: 'Papers',
    type: 'scatter',
    showlegend: false,
  };
}

/**
 * Get marker color - TRULY PURE function
 * Returns single color or array of colors based on enrichment
 */
function getMarkerColor(
  papers: Paper[],
  _filterState: FilterState, // TODO: Use for source-based coloring
  enrichmentState: EnrichmentState
): string | string[] {
  // If enrichment is active, check for enrichment field in papers
  if (enrichmentState.active) {
    // Check if papers have enrichment values
    const enrichmentField = enrichmentState.field;
    if (enrichmentField && papers.some(p => p[enrichmentField] !== undefined)) {
      // Return array of colors based on enrichment values
      return papers.map(p => getEnrichmentColor(p[enrichmentField]));
    }
  }

  // Default: all white (matches Dash default)
  return 'white';
}

/**
 * Get enrichment color - TRULY PURE function
 * Maps enrichment values to colors (from database/config)
 * TODO: This should come from config/API, but hardcoded for now
 */
function getEnrichmentColor(value: any): string {
  // This is a placeholder - colors should come from enrichment config
  // For now, using basic color mapping
  if (typeof value === 'string') {
    const colorMap: Record<string, string> = {
      'United States': '#007bff', // Blue
      'China': '#ff0000', // Red
      'Other': '#28a745', // Green
      'Unknown': '#6c757d', // Gray
    };
    return colorMap[value] || 'white';
  }
  return 'white';
}

/**
 * Create layout with view preservation - TRULY PURE function
 */
function createLayoutWithView(viewState: ViewState): PlotlyLayout {
  const layout = createDefaultLayout();

  // If view is zoomed, preserve ranges
  if (viewState.isZoomed && viewState.xRange && viewState.yRange) {
    layout.xaxis.autorange = false;
    layout.xaxis.range = viewState.xRange;
    layout.yaxis.autorange = false;
    layout.yaxis.range = viewState.yRange;
  }

  return layout;
}

/**
 * Apply view preservation to existing figure - TRULY PURE function
 * Following Dash view_management_fp.py preserveViewInFigure
 */
export function preserveViewInFigure(
  figure: PlotlyFigure,
  viewState: ViewState
): PlotlyFigure {
  if (!viewState.isZoomed || !viewState.xRange || !viewState.yRange) {
    return figure;
  }

  // Create new figure with preserved view (immutable)
  return {
    data: figure.data,
    layout: {
      ...figure.layout,
      xaxis: {
        ...figure.layout.xaxis,
        autorange: false,
        range: viewState.xRange,
      },
      yaxis: {
        ...figure.layout.yaxis,
        autorange: false,
        range: viewState.yRange,
      },
    },
  };
}

/**
 * Validate figure - TRULY PURE function
 */
export function validateFigure(figure: PlotlyFigure): boolean {
  if (!figure || !figure.data || !figure.layout) {
    return false;
  }

  // Check that data is array
  if (!Array.isArray(figure.data)) {
    return false;
  }

  // Check that layout has required properties
  if (!figure.layout.xaxis || !figure.layout.yaxis) {
    return false;
  }

  return true;
}

