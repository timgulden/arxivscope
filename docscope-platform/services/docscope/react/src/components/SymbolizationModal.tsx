/**
 * Symbolization Modal Component for DocScope React Frontend
 * 
 * PURELY PRESENTATIONAL component - no business logic.
 * Provides a modal interface for selecting a symbolization to apply to papers.
 * 
 * Design Principles:
 * - UI and logic strictly separated
 * - All state managed by logic layer (read via props)
 * - All business logic handled by parent via callbacks
 */

import { useState, useEffect } from 'react';
import type { ApplicationState } from '../logic/core/types';
import type { Symbolization } from '../logic/api/symbolization-api';

interface SymbolizationModalProps {
  /** Current application state (read-only) */
  state: ApplicationState;
  /** Available symbolizations to choose from */
  symbolizations: Symbolization[];
  /** Whether symbolizations are loading */
  loading?: boolean;
  /** Callback to close modal */
  onClose: () => void;
  /** Callback to apply symbolization */
  onApply: (symbolizationId: number | null) => Promise<void>;
}

/**
 * Symbolization Modal Component
 * PURELY PRESENTATIONAL - just renders UI based on state
 */
export function SymbolizationModal({ 
  state, 
  symbolizations,
  loading = false,
  onClose, 
  onApply 
}: SymbolizationModalProps) {
  const [selectedId, setSelectedId] = useState<number | null>(
    state.enrichment.symbolizationId
  );

  // Sync local selection when domain state changes
  useEffect(() => {
    setSelectedId(state.enrichment.symbolizationId);
  }, [state.enrichment.symbolizationId]);

  const handleApply = async () => {
    await onApply(selectedId);
    onClose(); // Close modal after applying
  };

  const handleClear = async () => {
    await onApply(null);
    onClose(); // Close modal after clearing
  };

  const modalOverlayStyle: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  };

  const modalContentStyle: React.CSSProperties = {
    backgroundColor: 'white',
    padding: '30px',
    borderRadius: '8px',
    maxWidth: '600px',
    width: '90%',
    maxHeight: '80vh',
    overflowY: 'auto',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  };

  const titleStyle: React.CSSProperties = {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '20px',
    color: '#333',
  };

  const descriptionStyle: React.CSSProperties = {
    fontSize: '14px',
    color: '#666',
    marginBottom: '20px',
  };

  const listStyle: React.CSSProperties = {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    marginBottom: '20px',
  };

  const itemStyle: React.CSSProperties = {
    padding: '12px',
    marginBottom: '8px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'pointer',
    backgroundColor: '#fff',
    transition: 'background-color 0.2s',
  };

  const selectedItemStyle: React.CSSProperties = {
    ...itemStyle,
    backgroundColor: '#e3f2fd',
    borderColor: '#2196F3',
  };

  const itemNameStyle: React.CSSProperties = {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#333',
    marginBottom: '4px',
  };

  const itemDescriptionStyle: React.CSSProperties = {
    fontSize: '12px',
    color: '#666',
    marginBottom: '8px',
  };

  const colorMapStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginTop: '8px',
  };

  const colorChipStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 8px',
    borderRadius: '4px',
    backgroundColor: '#f5f5f5',
    fontSize: '11px',
  };

  const colorSwatchStyle = (color: string): React.CSSProperties => ({
    width: '16px',
    height: '16px',
    borderRadius: '2px',
    backgroundColor: color,
    border: '1px solid #ccc',
  });

  const buttonContainerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '10px',
    marginTop: '20px',
  };

  const buttonStyle: React.CSSProperties = {
    padding: '10px 20px',
    borderRadius: '4px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold',
    transition: 'background-color 0.2s',
  };

  const applyButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: '#28a745',
    color: 'white',
  };

  const clearButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: '#6c757d',
    color: 'white',
  };

  const cancelButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: '#dc3545',
    color: 'white',
  };

  return (
    <div style={modalOverlayStyle} onClick={onClose}>
      <div style={modalContentStyle} onClick={(e) => e.stopPropagation()}>
        <h2 style={titleStyle}>Select Symbolization</h2>
        <p style={descriptionStyle}>
          Choose a symbolization to color papers based on field values.
        </p>

        {loading ? (
          <div>Loading symbolizations...</div>
        ) : symbolizations.length === 0 ? (
          <div>No symbolizations available.</div>
        ) : (
          <ul style={listStyle}>
            {symbolizations.map((sym) => (
              <li
                key={sym.id}
                style={selectedId === sym.id ? selectedItemStyle : itemStyle}
                onClick={() => setSelectedId(sym.id)}
              >
                <div style={itemNameStyle}>{sym.name}</div>
              </li>
            ))}
          </ul>
        )}

        <div style={buttonContainerStyle}>
          <button
            style={clearButtonStyle}
            onClick={handleClear}
            onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#5a6268')}
            onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#6c757d')}
          >
            Clear
          </button>
          <button
            style={applyButtonStyle}
            onClick={handleApply}
            disabled={selectedId === null}
            onMouseOver={(e) => {
              if (!e.currentTarget.disabled) {
                e.currentTarget.style.backgroundColor = '#218838';
              }
            }}
            onMouseOut={(e) => {
              if (!e.currentTarget.disabled) {
                e.currentTarget.style.backgroundColor = '#28a745';
              }
            }}
          >
            Apply
          </button>
          <button
            style={cancelButtonStyle}
            onClick={onClose}
            onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#c82333')}
            onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#dc3545')}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

