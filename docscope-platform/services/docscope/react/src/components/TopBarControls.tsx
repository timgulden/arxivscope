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
  onComputeClusters: (clusterCount: number) => Promise<void>;
  /** Callback when hide clusters button clicked */
  onHideClusters: () => void;
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
  onHideClusters,
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
  // Local UI state for fetch limit input to reflect changes immediately while typing
  const [fetchInput, setFetchInput] = useState<string>(
    state.view.limit.toString()
  );

  // Sync local input state when domain state changes
  useEffect(() => {
    setClusterCountInput(state.enrichment.clusterCount.toString());
  }, [state.enrichment.clusterCount]);

  // Sync local fetch input when domain state changes externally
  useEffect(() => {
    setFetchInput(state.view.limit.toString());
  }, [state.view.limit]);

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
        {/* Compute Clusters Button - Three states: Compute Clusters (green), Computing... (gray), Hide Clusters (blue) */}
        <div style={controlGroupStyle}>
          <button
            onClick={() => {
              console.log('Compute Clusters button clicked');
              console.log('clustersVisible:', state.enrichment.clustersVisible);
              console.log('clusterCountInput:', clusterCountInput);
              
              if (state.enrichment.clustersVisible) {
                // Hide clusters if visible
                console.log('Hiding clusters');
                onHideClusters();
              } else {
                // Compute clusters if not visible
                const num = parseInt(clusterCountInput, 10);
                console.log('Parsed cluster count:', num);
                if (!isNaN(num) && num >= 2 && num <= 99) {
                  console.log('Calling onComputeClusters with', num);
                  onComputeClusters(num);
                } else {
                  console.warn('Invalid cluster count:', num, 'from input:', clusterCountInput);
                  alert(`Invalid cluster count: ${clusterCountInput}. Please enter a number between 2 and 99.`);
                }
              }
            }}
            disabled={state.enrichment.clusterComputing}
            style={{
              padding: '6px 12px',
              backgroundColor: state.enrichment.clusterComputing 
                ? '#7f8c8d'  // Gray when computing
                : state.enrichment.clustersVisible 
                  ? '#3498db'  // Blue when visible (Hide Clusters)
                  : '#27ae60',  // Green when not visible (Compute Clusters)
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              cursor: state.enrichment.clusterComputing ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              transition: 'background-color 0.2s',
              opacity: state.enrichment.clusterComputing ? 0.6 : 1,
            }}
            onMouseOver={(e) => {
              if (!state.enrichment.clusterComputing) {
                e.currentTarget.style.backgroundColor = state.enrichment.clustersVisible 
                  ? '#2980b9'  // Darker blue on hover
                  : '#229954';  // Darker green on hover
              }
            }}
            onMouseOut={(e) => {
              if (!state.enrichment.clusterComputing) {
                e.currentTarget.style.backgroundColor = state.enrichment.clustersVisible 
                  ? '#3498db' 
                  : '#27ae60';
              }
            }}
          >
            {state.enrichment.clusterComputing 
              ? 'Computing...' 
              : state.enrichment.clustersVisible 
                ? 'Hide Clusters' 
                : 'Compute Clusters'}
          </button>
        </div>

        {/* Clusters Input */}
        <div style={controlGroupStyle}>
          <label style={labelStyle}>Clusters:</label>
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
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
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            value={fetchInput}
            onChange={(e) => {
              const value = e.target.value;
              setFetchInput(value);
              onLimitChange(value);
            }}
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

