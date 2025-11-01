/**
 * Semantic Filter Modal Component for DocScope React Frontend
 * 
 * Provides a modal interface for entering semantic search text and adjusting
 * similarity threshold. Supports very long text input (abstracts).
 */

import { useState, useEffect } from 'react';
import type { ApplicationState, StateAction } from '../logic/core/types';

interface SemanticFilterModalProps {
  state: ApplicationState;
  dispatch: (action: StateAction) => void;
  onClose: () => void;
  onApply: (searchText: string | null, similarityThreshold: number) => void;
}

/**
 * Semantic Filter Modal Component
 */
export function SemanticFilterModal({ state, dispatch, onClose, onApply }: SemanticFilterModalProps) {
  const [searchText, setSearchText] = useState(state.filter.searchText || '');
  const [similarityThreshold, setSimilarityThreshold] = useState(state.filter.similarityThreshold || 0.5);

  // Update local state when filter state changes externally
  useEffect(() => {
    setSearchText(state.filter.searchText || '');
    setSimilarityThreshold(state.filter.similarityThreshold || 0.5);
  }, [state.filter.searchText, state.filter.similarityThreshold]);

  const handleApply = () => {
    // Update filter state
    dispatch({
      type: 'FILTER_UPDATE',
      payload: {
        ...state.filter,
        searchText: searchText || null,
        similarityThreshold,
        lastUpdate: Date.now()
      }
    });
    
    // Trigger data fetch with current values
    onApply(searchText || null, similarityThreshold);
    
    // Close modal
    onClose();
  };

  const handleClear = () => {
    // Just clear the textbox, don't close modal or update filter
    setSearchText('');
    setSimilarityThreshold(0.5);
  };

  return (
    <>
      {/* Backdrop */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 1000,
        }}
        onClick={onClose}
      />
      
      {/* Modal */}
      <div
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: '#34495e',
          borderRadius: '8px',
          padding: '20px',
          minWidth: '600px',
          maxWidth: '800px',
          maxHeight: '80vh',
          zIndex: 1001,
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}>
          <h2 style={{ margin: 0, fontSize: '20px', color: '#ffffff' }}>Semantic Filter</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#ffffff',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0',
              width: '30px',
              height: '30px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            ×
          </button>
        </div>

        {/* Similarity Threshold */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            marginBottom: '10px',
            color: '#ffffff',
            fontSize: '14px',
          }}>
            Similarity Threshold: {similarityThreshold.toFixed(2)}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={similarityThreshold}
            onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
            style={{
              width: '100%',
              height: '6px',
              borderRadius: '3px',
              background: '#7f8c8d',
              outline: 'none',
            }}
          />
        </div>

        {/* Text Input */}
        <div style={{ marginBottom: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <label style={{
            display: 'block',
            marginBottom: '10px',
            color: '#ffffff',
            fontSize: '14px',
          }}>
            Search Text:
          </label>
          <textarea
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Enter text to search for semantically similar papers..."
            style={{
              flex: 1,
              minHeight: '200px',
              padding: '12px',
              backgroundColor: '#ecf0f1',
              border: '1px solid #95a5a6',
              borderRadius: '4px',
              fontSize: '14px',
              fontFamily: 'inherit',
              resize: 'vertical',
              color: '#2c3e50',
            }}
          />
        </div>

        {/* Buttons */}
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '10px',
        }}>
          <button
            onClick={handleClear}
            style={{
              padding: '10px 20px',
              backgroundColor: '#95a5a6',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'bold',
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#7f8c8d'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#95a5a6'}
          >
            Clear
          </button>
          <button
            onClick={handleApply}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'bold',
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2980b9'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3498db'}
          >
            Apply
          </button>
        </div>
      </div>
    </>
  );
}

