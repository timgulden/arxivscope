/**
 * Visualization Pure Functions for DocScope React Frontend
 * 
 * Implements visualization operations using pure functions.
 * Following functional programming principles: NO SIDE EFFECTS.
 */

import type { ViewState, FilterState, EnrichmentState, Paper } from '../core/types';
import type { ClusterData } from '../core/types';

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
  mode: 'markers' | 'lines';
  marker?: {
    size: number;
    opacity: number;
    color: string | string[];
    line?: {
      width: number;
      color: string;
    };
  };
  line?: {
    width: number;
    color: string;
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
  annotations?: Array<{
    x: number;
    y: number;
    text: string;
    showarrow: boolean;
    font?: {
      color: string;
      size: number;
      family: string;
    };
    bgcolor?: string;
    bordercolor?: string;
    borderwidth?: number;
  }>;
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

  // Add cluster overlays if clusters are visible
  const data: PlotlyTrace[] = [trace];
  if (enrichmentState.clustersVisible && enrichmentState.clusterData) {
    // Add Voronoi polygon traces (orange boundaries)
    for (const polygon of enrichmentState.clusterData.polygons) {
      // Close polygon if not already closed
      const x = polygon.x.length > 0 && polygon.x[0] === polygon.x[polygon.x.length - 1] 
        ? polygon.x 
        : [...polygon.x, polygon.x[0]];
      const y = polygon.y.length > 0 && polygon.y[0] === polygon.y[polygon.y.length - 1] 
        ? polygon.y 
        : [...polygon.y, polygon.y[0]];
      
      data.push({
        x,
        y,
        mode: 'lines',
        marker: {
          size: 8,
          opacity: 1,
          color: '#FF8C00', // Orange color (not used in lines mode but required)
        },
        // For lines mode, use line property (not marker.line)
        line: {
          width: 1,
          color: '#FF8C00', // Orange color
        },
        hovertemplate: '',
        name: 'Cluster Region',
        type: 'scatter',
        showlegend: false,
      });
    }
    
    // Add annotations (orange text)
    if (!layout.annotations) {
      layout.annotations = [];
    }
    for (const annotation of enrichmentState.clusterData.annotations) {
      layout.annotations.push({
        x: annotation.x,
        y: annotation.y,
        text: annotation.text,
        showarrow: false,
        font: {
          color: '#FF8C00', // Orange color
          size: 18,
          family: 'Arial',
        },
        bgcolor: 'rgba(0, 0, 0, 0.4)',
        bordercolor: 'rgba(0, 0, 0, 0)',
        borderwidth: 0,
      });
    }
  }

  return {
    data,
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
 * Returns single color or array of colors based on enrichment or symbolization
 */
function getMarkerColor(
  papers: Paper[],
  _filterState: FilterState, // TODO: Use for source-based coloring
  enrichmentState: EnrichmentState
): string | string[] {
  // Check for symbolization first (takes precedence)
  if (enrichmentState.symbolizationId !== null && 
      enrichmentState.symbolizationColorMap && 
      enrichmentState.symbolizationField) {
    const field = enrichmentState.symbolizationField;
    const colorMap = enrichmentState.symbolizationColorMap;
    
    // Parse field name to get column name (API returns column name, not qualified name)
    // Example: "enrichment_country.country_uschina" -> "country_uschina"
    const fieldParts = field.split('.');
    const columnName = fieldParts.length > 1 ? fieldParts[fieldParts.length - 1] : field;
    
    // Debug: Log field names and available keys
    console.log('🔍 Symbolization debug:', {
      symbolizationId: enrichmentState.symbolizationId,
      symbolizationField: field,
      parsedColumnName: columnName,
      colorMapKeys: Object.keys(colorMap),
      samplePaperKeys: papers.length > 0 ? Object.keys(papers[0]) : [],
      samplePaperValue: papers.length > 0 ? (papers[0] as any)[columnName] : null,
      samplePaper: papers.length > 0 ? papers[0] : null,
    });
    
    // Check multiple possible field name variations
    // API returns the column name (e.g., "country_uschina"), not the qualified name
    const possibleFieldNames = [
      columnName,  // Most likely: just the column name
      field,       // Full qualified name (if API returns it)
      // Also try with underscores if it has dots
      field.replace('.', '_'),
    ];
    
    // Find the field name that exists in papers
    // Check if field exists (even if null - it means the field was returned)
    let foundField: string | null = null;
    for (const fieldName of possibleFieldNames) {
      if (papers.some(p => p[fieldName] !== undefined)) {
        foundField = fieldName;
        break;
      }
    }
    
    if (foundField) {
      console.log('✅ Found field:', foundField);
      
      // Extract value_overrides from color map structure
      // Color map structure: { apply_to: string, source_defaults: {...}, value_overrides: {...} }
      const valueOverrides = (colorMap as any).value_overrides || {};
      const sourceDefaults = (colorMap as any).source_defaults || {};
      
      console.log('🔍 Color map structure:', {
        hasValueOverrides: !!valueOverrides,
        valueOverrideKeys: Object.keys(valueOverrides),
        hasSourceDefaults: !!sourceDefaults,
        sourceDefaultKeys: Object.keys(sourceDefaults),
      });
      
      // Return array of colors based on symbolization color map
      const colors = papers.map(p => {
        const value = p[foundField!];
        if (value !== undefined && value !== null) {
          const valueStr = String(value);
          
          // First, check value_overrides (explicit value-to-color mappings)
          if (valueOverrides[valueStr] || valueOverrides[valueStr.toLowerCase()]) {
            const color = valueOverrides[valueStr] || valueOverrides[valueStr.toLowerCase()];
            console.log(`  ✅ Mapped value "${valueStr}" -> color "${color}" (from value_overrides)`);
            return color;
          }
          
          // Fallback: Check source_defaults if available
          const source = (p as any).doctrove_source;
          if (source && sourceDefaults[source]) {
            const color = sourceDefaults[source];
            console.log(`  ✅ Mapped source "${source}" -> color "${color}" (from source_defaults)`);
            return color;
          }
          
          // No match found
          console.log(`  ⚠️ No color mapping for value "${valueStr}" (source: ${source})`);
          return 'white';
        }
        // Field exists but value is null - use default color
        return 'white';
      });
      
      const uniqueColors = colors.filter((c, i) => colors.indexOf(c) === i);
      console.log('🎨 Generated colors:', uniqueColors.slice(0, 10));
      console.log(`   Total papers: ${papers.length}, Unique colors: ${uniqueColors.length}, White: ${colors.filter(c => c === 'white').length}`);
      return colors;
    } else {
      console.warn('⚠️ Symbolization field not found in papers. Tried:', possibleFieldNames);
      console.warn('   Available paper keys:', papers.length > 0 ? Object.keys(papers[0]) : []);
    }
  }
  
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

