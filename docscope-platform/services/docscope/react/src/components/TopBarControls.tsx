/**
 * Top Bar Controls Component for DocScope React Frontend
 * 
 * PURELY PRESENTATIONAL component - no business logic.
 * Provides elegant controls for clustering, universe filter, and fetch limit.
 * 
 * Design Principles:
 * - UI and logic strictly separated
 * - All state managed by logic layer (read via props)
 * - All business logic handled by parent via callbacks
 * - Component is testable in isolation (just rendering)
 */

import { useState, useEffect } from 'react';
import type { ApplicationState } from '../logic/core/types';

interface TopBarControlsProps {
  /** Current application state (read-only) */
  state: ApplicationState;
  /** Callback when count button clicked */
  onCountClick: () => void;
  /** Callback when clustering toggle changes */
  onClusteringToggle: () => void;
  /** Callback when compute clusters button clicked - receives cluster count */
  onComputeClusters: (clusterCount: number) => void;
  /** Callback when cluster count input changes (while typing) */
  onClusterCountChange: (value: string) => void;
  /** Callback when limit input changes */
  onLimitChange: (value: string) => void;
  /** Callback to open universe filter modal */
  onUniverseFilterOpen: () => void;
  /** Callback to open semantic filter modal */
  onSemanticFilterOpen: () => void;
  /** Callback to open symbolization modal */
  onSymbolizationOpen: () => void;
  /** Callback when sort button clicked */
  onSortClick: () => void;
  /** Whether symbolization is active */
  symbolizationActive?: boolean;
  /** Whether sort is active */
  sortActive?: boolean;
}

/**
 * Top Bar Controls Component
 * PURELY PRESENTATIONAL - just renders UI based on state
 */
export function TopBarControls({ 
  state,
  onCountClick,
  onClusteringToggle,
  onComputeClusters,
  onClusterCountChange,
  onLimitChange,
  onUniverseFilterOpen,
  onSemanticFilterOpen,
  onSymbolizationOpen,
  onSortClick,
  symbolizationActive = false,
  sortActive = false
}: TopBarControlsProps) {
  // Local UI state for cluster count input (for immediate feedback while typing)
  // This is NOT domain state - just transient UI state
  const [clusterCountInput, setClusterCountInput] = useState<string>(
    state.enrichment.clusterCount.toString()
  );

  // Sync local input state when domain state changes
  useEffect(() => {
    setClusterCountInput(state.enrichment.clusterCount.toString());
  }, [state.enrichment.clusterCount]);

  const controlGroupStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '0 8px', // Reduced padding since no border
  };

  const labelStyle: React.CSSProperties = {
    fontSize: '12px',
    color: '#bdc3c7',
    marginRight: '4px',
    whiteSpace: 'nowrap',
  };

  const inputStyle: React.CSSProperties = {
    width: '70px',
    padding: '4px 8px',
    backgroundColor: '#34495e',
    border: '1px solid #4a5f7a',
    borderRadius: '4px',
    color: '#ffffff',
    fontSize: '13px',
    textAlign: 'center',
  };

  const clustersInputStyle: React.CSSProperties = {
    ...inputStyle,
    width: '45px', // Much narrower for clusters
  };

  const fetchInputStyle: React.CSSProperties = {
    ...inputStyle,
    width: '56px', // 20% narrower than 70px
  };

  // Base button style matching Semantic Filter (green inactive, blue active)
  const getButtonStyle = (isActive: boolean): React.CSSProperties => ({
    padding: '6px 12px', // Match Semantic Filter padding
    backgroundColor: isActive ? '#3498db' : '#27ae60',
    color: '#ffffff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px', // Match Semantic Filter font size
    transition: 'background-color 0.2s',
  });

  const getButtonHoverColor = (isActive: boolean): string => {
    return isActive ? '#2980b9' : '#229954';
  };

  const checkboxStyle: React.CSSProperties = {
    marginRight: '6px',
    cursor: 'pointer',
  };

  // Determine if count should be displayed (would come from state or props)
  const showCount = state.data.papers.length > 0 || false; // TODO: Add count display logic
  const totalCount = state.data.papers.length; // TODO: Use actual total count from API if available

  return (
    <>
      {/* Left Section: Count button, Count display */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0',
        marginLeft: '20px', // Space after DocScope title
      }}>
        {/* Count Button */}
        <div style={controlGroupStyle}>
          <button
            onClick={onCountClick}
            style={getButtonStyle(false)}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = getButtonHoverColor(false)}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = getButtonStyle(false).backgroundColor}
          >
            Count
          </button>
        </div>

        {/* Count Display */}
        {showCount && (
          <div style={{
            ...controlGroupStyle,
            padding: '0 8px',
          }}>
            <span style={{
              fontSize: '13px',
              color: '#ecf0f1',
            }}>
              Count: {totalCount.toLocaleString()}
            </span>
          </div>
        )}
      </div>

      {/* Center Cluster: Universe Filter, Semantic Filter (centered), Symbolization */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0',
        position: 'absolute',
        left: '50%',
        transform: 'translateX(-50%)',
      }}>
        {/* Universe Filter Button - just left of Semantic Filter */}
        <div style={controlGroupStyle}>
          <button
            onClick={onUniverseFilterOpen}
            style={getButtonStyle(!!state.filter.universeConstraints)}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = getButtonHoverColor(!!state.filter.universeConstraints)}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = getButtonStyle(!!state.filter.universeConstraints).backgroundColor}
          >
            Universe Filter
          </button>
        </div>

        {/* Semantic Filter Button - centered */}
        <div style={controlGroupStyle}>
          <button
            onClick={onSemanticFilterOpen}
            style={getButtonStyle(!!state.filter.searchText)}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = getButtonHoverColor(!!state.filter.searchText)}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = getButtonStyle(!!state.filter.searchText).backgroundColor}
          >
            Semantic Filter
          </button>
        </div>
        
        {/* Symbolization Button - just right of Semantic Filter */}
        <div style={controlGroupStyle}>
          <button
            onClick={onSymbolizationOpen}
            style={getButtonStyle(symbolizationActive)}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = getButtonHoverColor(symbolizationActive)}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = getButtonStyle(symbolizationActive).backgroundColor}
          >
            Symbolization
          </button>
        </div>
      </div>

      {/* Right Section: Compute Clusters, Clusters, Fetch, Sort */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0',
        marginLeft: 'auto',
      }}>
        {/* Compute Clusters Button */}
        <div style={controlGroupStyle}>
          <button
            onClick={() => {
              const num = parseInt(clusterCountInput, 10);
              if (!isNaN(num) && num >= 2 && num <= 99) {
                onComputeClusters(num);
              }
            }}
            style={getButtonStyle(state.enrichment.useClustering)}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = getButtonHoverColor(state.enrichment.useClustering)}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = getButtonStyle(state.enrichment.useClustering).backgroundColor}
          >
            Compute Clusters
          </button>
        </div>

        {/* Clusters Input */}
        <div style={controlGroupStyle}>
          <label style={labelStyle}>Clusters:</label>
          <input
            type="number"
            min="2"
            max="99"
            step="1"
            value={clusterCountInput}
            onChange={(e) => {
              const value = e.target.value;
              setClusterCountInput(value);
              onClusterCountChange(value);
            }}
            onBlur={() => {
              // Reset to domain state if invalid on blur
              const num = parseInt(clusterCountInput, 10);
              if (isNaN(num) || num < 2 || num > 99) {
                setClusterCountInput(state.enrichment.clusterCount.toString());
              }
            }}
            style={clustersInputStyle}
          />
        </div>

        {/* Fetch Input */}
        <div style={controlGroupStyle}>
          <label style={labelStyle}>Fetch:</label>
          <input
            type="number"
            min="100"
            max="99999"
            step="100"
            value={state.view.limit}
            onChange={(e) => onLimitChange(e.target.value)}
            style={fetchInputStyle}
          />
        </div>

        {/* Sort Button */}
        <div style={controlGroupStyle}>
          <button
            onClick={onSortClick}
            style={getButtonStyle(sortActive)}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = getButtonHoverColor(sortActive)}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = getButtonStyle(sortActive).backgroundColor}
          >
            Sort
          </button>
        </div>
      </div>
    </>
  );
}

