/**
 * View Management Functions for DocScope React Frontend
 * 
 * Pure functions for managing view state without side effects.
 * All functions are truly pure - same input always produces same output.
 * Following view_management_fp.py as reference.
 */

import type { ViewState } from '../core/types';

/**
 * Extract view state from Plotly relayoutData - TRULY PURE function
 * Same input always produces same output, no side effects
 */
export function extractViewFromRelayoutPure(
  relayoutData: any,
  currentTime: number
): ViewState | null {
  if (!relayoutData) {
    return null;
  }

  // Handle autosize events
  if ('autosize' in relayoutData) {
    return null;
  }

  // Extract x-axis range
  let xRange: [number, number] | null = null;
  if ('xaxis.range[0]' in relayoutData && 'xaxis.range[1]' in relayoutData) {
    const x1 = relayoutData['xaxis.range[0]'];
    const x2 = relayoutData['xaxis.range[1]'];
    xRange = [x1, x2];
  } else if ('xaxis.range' in relayoutData && Array.isArray(relayoutData['xaxis.range'])) {
    xRange = relayoutData['xaxis.range'] as [number, number];
  }

  // Extract y-axis range
  let yRange: [number, number] | null = null;
  if ('yaxis.range[0]' in relayoutData && 'yaxis.range[1]' in relayoutData) {
    const y1 = relayoutData['yaxis.range[0]'];
    const y2 = relayoutData['yaxis.range[1]'];
    yRange = [y1, y2];
  } else if ('yaxis.range' in relayoutData && Array.isArray(relayoutData['yaxis.range'])) {
    yRange = relayoutData['yaxis.range'] as [number, number];
  }

  // Only return view state if we have valid ranges
  if (!xRange || !yRange) {
    return null;
  }

  // Set zoom/pan flags
  const isZoomed = Boolean(xRange && yRange);
  const isPanned = isZoomed;

  // Convert to bbox format
  const bbox = rangesToBboxString(xRange, yRange);

  // Return None if not zoomed (no valid view)
  if (!isZoomed) {
    return null;
  }

  // Return plain object - no classes, no side effects
  // Note: limit is not extracted from relayout data, it stays as-is from current state
  return {
    bbox,
    xRange,
    yRange,
    isZoomed,
    isPanned,
    limit: 5000, // Default limit when extracting from relayout
    lastUpdate: currentTime
  };
}

/**
 * Extract view from relayout data - wrapper with injected time dependency
 */
export function extractViewFromRelayout(
  relayoutData: any,
  timestampProvider: () => number = () => Date.now()
): ViewState | null {
  return extractViewFromRelayoutPure(relayoutData, timestampProvider());
}

/**
 * Extract view state from existing figure - TRULY PURE function
 */
export function extractViewFromFigurePure(
  figure: any,
  currentTime: number
): ViewState | null {
  if (!figure || !figure.layout) {
    return null;
  }

  const layout = figure.layout;

  // Extract x-axis range
  let xRange: [number, number] | null = null;
  if (layout.xaxis && layout.xaxis.range) {
    xRange = layout.xaxis.range as [number, number];
  }

  // Extract y-axis range
  let yRange: [number, number] | null = null;
  if (layout.yaxis && layout.yaxis.range) {
    yRange = layout.yaxis.range as [number, number];
  }

  // Only return view state if we have valid ranges
  if (!xRange || !yRange) {
    return null;
  }

  // Set zoom/pan flags
  const isZoomed = Boolean(xRange && yRange);
  const isPanned = isZoomed;

  // Convert to bbox format
  const bbox = rangesToBboxString(xRange, yRange);

  // Return None if not zoomed (no valid view)
  if (!isZoomed) {
    return null;
  }

  // Return plain object
  // Note: limit is not extracted from figure, stays as-is from current state
  return {
    bbox,
    xRange,
    yRange,
    isZoomed,
    isPanned,
    limit: 5000, // Default limit when extracting from figure
    lastUpdate: currentTime
  };
}

/**
 * Extract view from figure - wrapper with injected time dependency
 */
export function extractViewFromFigure(
  figure: any,
  timestampProvider: () => number = () => Date.now()
): ViewState | null {
  return extractViewFromFigurePure(figure, timestampProvider());
}

/**
 * Validate view state - TRULY PURE function
 */
export function validateViewState(viewState: ViewState): boolean {
  if (!viewState) {
    return false;
  }

  const xRange = viewState.xRange;
  const yRange = viewState.yRange;

  if (!xRange || !yRange) {
    return false;
  }

  if (!Array.isArray(xRange) || !Array.isArray(yRange)) {
    return false;
  }

  if (xRange.length !== 2 || yRange.length !== 2) {
    return false;
  }

  if (xRange[0] >= xRange[1]) {
    return false;
  }

  if (yRange[0] >= yRange[1]) {
    return false;
  }

  return true;
}

/**
 * Create default view state - TRULY PURE function
 */
export function createDefaultViewStatePure(currentTime: number): ViewState {
  return {
    bbox: null,
    xRange: null,
    yRange: null,
    isZoomed: false,
    isPanned: false,
    limit: 5000,
    lastUpdate: currentTime
  };
}

/**
 * Create default view state - wrapper with injected time dependency
 */
export function createDefaultViewState(
  timestampProvider: () => number = () => Date.now()
): ViewState {
  return createDefaultViewStatePure(timestampProvider());
}

/**
 * Create view state from coordinate ranges - TRULY PURE function
 */
export function createViewStateFromRangesPure(
  xRange: [number, number],
  yRange: [number, number],
  currentTime: number
): ViewState {
  return {
    bbox: rangesToBboxString(xRange, yRange),
    xRange: [xRange[0], xRange[1]], // Copy to ensure immutability
    yRange: [yRange[0], yRange[1]], // Copy to ensure immutability
    isZoomed: true,
    isPanned: true,
    limit: 5000, // Default limit
    lastUpdate: currentTime
  };
}

/**
 * Create view state from ranges - wrapper with injected time dependency
 */
export function createViewStateFromRanges(
  xRange: [number, number],
  yRange: [number, number],
  timestampProvider: () => number = () => Date.now()
): ViewState {
  return createViewStateFromRangesPure(xRange, yRange, timestampProvider());
}

/**
 * Check if view is stable between two states - TRULY PURE function
 */
export function isViewStable(
  currentView: ViewState,
  previousView: ViewState,
  stabilityThreshold: number = 0.001
): boolean {
  if (!currentView || !previousView) {
    return false;
  }

  if (!validateViewState(currentView) || !validateViewState(previousView)) {
    return false;
  }

  // Check x-range stability
  const currentX = currentView.xRange;
  const previousX = previousView.xRange;
  if (currentX && previousX) {
    const xDiff = Math.abs(currentX[0] - previousX[0]) + Math.abs(currentX[1] - previousX[1]);
    if (xDiff > stabilityThreshold) {
      return false;
    }
  }

  // Check y-range stability
  const currentY = currentView.yRange;
  const previousY = previousView.yRange;
  if (currentY && previousY) {
    const yDiff = Math.abs(currentY[0] - previousY[0]) + Math.abs(currentY[1] - previousY[1]);
    if (yDiff > stabilityThreshold) {
      return false;
    }
  }

  return true;
}

/**
 * Merge two view states, preferring primary - TRULY PURE function
 */
export function mergeViewStates(
  primary: ViewState,
  secondary: ViewState
): ViewState {
  if (!primary) {
    return secondary;
  }
  if (!secondary) {
    return primary;
  }

  // Create new merged view state as plain object
  return {
    bbox: primary.bbox || secondary.bbox,
    xRange: primary.xRange || secondary.xRange,
    yRange: primary.yRange || secondary.yRange,
    isZoomed: primary.isZoomed || secondary.isZoomed,
    isPanned: primary.isPanned || secondary.isPanned,
    limit: primary.limit || secondary.limit, // Preserve limit from primary, fall back to secondary
    lastUpdate: Math.max(primary.lastUpdate, secondary.lastUpdate)
  };
}

/**
 * Create view state from max extent - TRULY PURE function
 */
export function createViewStateFromMaxExtentPure(
  maxExtent: { xMin: number; xMax: number; yMin: number; yMax: number },
  currentTime: number,
  limit: number = 5000
): ViewState {
  return {
    bbox: rangesToBboxString([maxExtent.xMin, maxExtent.xMax], [maxExtent.yMin, maxExtent.yMax]),
    xRange: [maxExtent.xMin, maxExtent.xMax],
    yRange: [maxExtent.yMin, maxExtent.yMax],
    isZoomed: true,
    isPanned: false,
    limit,
    lastUpdate: currentTime
  };
}

/**
 * Create view state from max extent - wrapper with injected time dependency
 */
export function createViewStateFromMaxExtent(
  maxExtent: { xMin: number; xMax: number; yMin: number; yMax: number },
  limit: number = 5000,
  timestampProvider: () => number = () => Date.now()
): ViewState {
  return createViewStateFromMaxExtentPure(maxExtent, timestampProvider(), limit);
}

/**
 * Convert coordinate ranges to bbox string - TRULY PURE helper
 */
function rangesToBboxString(xRange: [number, number], yRange: [number, number]): string {
  if (xRange.length === 2 && yRange.length === 2) {
    return `${xRange[0]},${yRange[0]},${xRange[1]},${yRange[1]}`;
  }
  return '';
}

