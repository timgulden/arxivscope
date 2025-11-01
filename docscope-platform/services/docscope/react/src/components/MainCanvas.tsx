/**
 * Main Canvas Component for DocScope React Frontend
 * 
 * Displays the scatter plot visualization using react-plotly.js
 * Following Dash graph configuration and dark theme.
 */

import { useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import { createFigure, createEmptyFigure } from '../logic';
import { extractViewFromRelayout, createViewStateFromMaxExtent } from '../logic/view/view-management';
import { createFetchRequest } from '../logic/data/data-fetching';
import type { ApplicationState, StateAction } from '../logic/core/types';

interface MainCanvasProps {
  state: ApplicationState;
  dispatch: (action: StateAction) => void;
  onDataFetch?: (fetchRequest: any) => void;
}

/**
 * Main Canvas Component
 * Displays papers as scatter plot with dark theme
 */
export function MainCanvas({ state, dispatch, onDataFetch }: MainCanvasProps) {
  // Create figure from current state
  const figure = state.data.papers.length > 0 
    ? createFigure(state.data.papers, state.view, state.filter, state.enrichment)
    : createEmptyFigure();

  // Debounce ref for pan/zoom fetches
  const fetchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Handle relayout events (zoom/pan)
  const handleRelayout = (eventData: any) => {
    if (!eventData || !onDataFetch) return;
    
    // Check if this is a home button/autorange event
    // Home button triggers relayout with no range data - we need to apply max extent instead
    const hasAutorangeTrigger = 'xaxis.autorange' in eventData || 'yaxis.autorange' in eventData;
    const hasNoRanges = !('xaxis.range' in eventData) && !('xaxis.range[0]' in eventData);
    
    let newViewState;
    if (hasAutorangeTrigger || hasNoRanges) {
      // Home button or autorange: apply max extent if available
      if (!state.data.maxExtent) {
        console.warn('Home button clicked but max extent not loaded yet');
        return;
      }
      
      newViewState = createViewStateFromMaxExtent(state.data.maxExtent, state.view.limit);
    } else {
      // Regular pan/zoom: extract view from relayout data
      newViewState = extractViewFromRelayout(eventData);
      if (!newViewState) return; // No valid ranges
    }
    
    // Dispatch view update immediately
    dispatch({ type: 'VIEW_UPDATE', payload: newViewState });
    
    // Clear existing timeout
    if (fetchTimeoutRef.current) {
      clearTimeout(fetchTimeoutRef.current);
    }
    
    // Debounce the fetch by 500ms
    fetchTimeoutRef.current = setTimeout(() => {
      // Create fetch request with new bbox
      const fetchRequest = createFetchRequest(newViewState, state.filter, state.enrichment);
      
      // Trigger data fetch
      onDataFetch(fetchRequest);
    }, 500);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (fetchTimeoutRef.current) {
        clearTimeout(fetchTimeoutRef.current);
      }
    };
  }, []);

  // Handle click events on points
  const handleClick = (eventData: any) => {
    if (eventData && eventData.points && eventData.points.length > 0) {
      const point = eventData.points[0];
      const paperId = point.customdata;
      if (paperId) {
        dispatch({ type: 'UI_SELECT_PAPER', payload: paperId });
      }
    }
  };

  // Calculate current view extent for status display
  const getViewText = (): string => {
    if (state.view.bbox) {
      // Parse bbox string and format with 2 decimals
      const parts = state.view.bbox.split(',');
      if (parts.length === 4) {
        const nums = parts.map(p => parseFloat(p.trim()));
        if (nums.every(n => !isNaN(n))) {
          return `View: ${nums.map(n => n.toFixed(2)).join(', ')}`;
        }
      }
      return `View: ${state.view.bbox}`;
    } else if (state.view.xRange && state.view.yRange) {
      const [xMin, xMax] = state.view.xRange;
      const [yMin, yMax] = state.view.yRange;
      return `View: ${xMin.toFixed(2)}, ${yMin.toFixed(2)}, ${xMax.toFixed(2)}, ${yMax.toFixed(2)}`;
    } else if (state.data.papers.length > 0) {
      // Calculate extent from loaded papers
      const xCoords = state.data.papers.map(p => p.doctrove_embedding_2d.x);
      const yCoords = state.data.papers.map(p => p.doctrove_embedding_2d.y);
      const xMin = Math.min(...xCoords);
      const xMax = Math.max(...xCoords);
      const yMin = Math.min(...yCoords);
      const yMax = Math.max(...yCoords);
      return `View: ${xMin.toFixed(2)}, ${yMin.toFixed(2)}, ${xMax.toFixed(2)}, ${yMax.toFixed(2)}`;
    }
    return 'View: No data';
  };

  // Determine status text and color
  const getStatusText = (): { text: string; color: string } => {
    if (state.data.loading) {
      return { text: 'Fetching...', color: '#FFA500' }; // Orange for loading
    }
    return { text: 'Ready', color: '#4CAF50' }; // Green for ready
  };

  const status = getStatusText();

  return (
    <div style={{ 
      width: '100%', 
      height: '100%',
      backgroundColor: '#2b2b2b',
      position: 'relative'
    }}>
      <Plot
        data={figure.data}
        layout={figure.layout}
        config={{
          displayModeBar: true,
          scrollZoom: true,
          staticPlot: false,
          responsive: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          editable: false,
          showEditInChartStudio: false,
          showSendToCloud: false,
          showTips: false,
          showAxisDragHandles: false,
          showAxisRangeEntryBoxes: false,
        }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
        onRelayout={handleRelayout}
        onClick={handleClick}
      />
      
      {/* Status overlay in upper left corner - matches screenshot styling */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        padding: '10px 15px',
        backgroundColor: 'rgba(0, 0, 0, 0.2)', // 80% transparent black (20% opaque)
        color: 'white',
        borderRadius: '5px',
        fontSize: '0.85em',
        lineHeight: '1.4',
        pointerEvents: 'none',
        zIndex: 1000,
        minWidth: '140px',
        textAlign: 'left',
      }}>
        <div style={{ marginBottom: '4px' }}>
          Showing {state.data.papers.length.toLocaleString()} papers
        </div>
        <div style={{ marginBottom: '4px' }}>
          {getViewText()}
        </div>
        <div style={{ marginBottom: '4px' }}>
          <span style={{ opacity: 0.8 }}>Status:</span> <span style={{ color: status.color }}>{status.text}</span>
        </div>
      </div>
    </div>
  );
}

