/**
 * Universe Filter Modal Component for DocScope React Frontend
 * 
 * PURELY PRESENTATIONAL component - no business logic.
 * Provides a modal interface for entering custom SQL WHERE clause to constrain
 * the universe of papers.
 * 
 * Design Principles:
 * - UI and logic strictly separated
 * - All state managed by logic layer (read via props)
 * - All business logic handled by parent via callbacks
 */

import { useState, useEffect } from 'react';
import type { ApplicationState } from '../logic/core/types';

interface UniverseFilterModalProps {
  /** Current application state (read-only) */
  state: ApplicationState;
  /** Callback to close modal */
  onClose: () => void;
  /** Callback to test query (pure function in logic layer) */
  onTestQuery: (sql: string) => Promise<{ success: boolean; message: string }>;
  /** Callback to apply universe constraint */
  onApply: (universeConstraints: string | null) => Promise<void>;
  /** Callback to generate SQL from natural language */
  onGenerateSql: (naturalLanguage: string) => Promise<{ sql: string; status: string }>;
  /** Callback to load schema document */
  onViewSchema: () => Promise<string>;
}

/**
 * Universe Filter Modal Component
 * PURELY PRESENTATIONAL - just renders UI based on state
 */
export function UniverseFilterModal({ 
  state, 
  onClose, 
  onTestQuery, 
  onApply,
  onGenerateSql,
  onViewSchema
}: UniverseFilterModalProps) {
  // Local UI state for input (for immediate feedback while typing)
  // This is NOT domain state - just transient UI state
  const [universeConstraints, setUniverseConstraints] = useState(
    state.filter.universeConstraints || ''
  );
  const [naturalLanguage, setNaturalLanguage] = useState('');
  const [testing, setTesting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [generationStatus, setGenerationStatus] = useState<string | null>(null);
  const [schemaDisplay, setSchemaDisplay] = useState<string | null>(null);
  const [showSchema, setShowSchema] = useState(false);

  // Sync local input state when domain state changes
  useEffect(() => {
    setUniverseConstraints(state.filter.universeConstraints || '');
    setTestResult(null);
  }, [state.filter.universeConstraints]);

  const handleTest = async () => {
    const sql = universeConstraints.trim();
    if (!sql) {
      setTestResult({ success: false, message: 'Please enter a SQL WHERE clause' });
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      // Call parent's test function (which uses pure logic layer functions)
      const result = await onTestQuery(sql);
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Error testing query',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleApply = async () => {
    const sql = universeConstraints.trim() || null;
    
    // Call parent's apply function (which handles state update and data fetch)
    await onApply(sql);
    
    // Close modal
    onClose();
  };

  const handleClear = () => {
    setUniverseConstraints('');
    setNaturalLanguage('');
    setTestResult(null);
    setGenerationStatus(null);
  };

  const handleGenerateSql = async () => {
    if (!naturalLanguage.trim()) {
      setGenerationStatus('⚠️ Please enter a natural language request');
      return;
    }

    setGenerating(true);
    setGenerationStatus(null);

    try {
      const result = await onGenerateSql(naturalLanguage.trim());
      setUniverseConstraints(result.sql);
      setGenerationStatus(result.status);
      setTestResult(null); // Clear test result when new SQL is generated
    } catch (error) {
      setGenerationStatus(
        error instanceof Error ? `❌ ${error.message}` : '❌ Error generating SQL'
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleViewSchema = async () => {
    if (showSchema) {
      setShowSchema(false);
      setSchemaDisplay(null);
      return;
    }

    try {
      const schemaContent = await onViewSchema();
      setSchemaDisplay(schemaContent);
      setShowSchema(true);
    } catch (error) {
      setSchemaDisplay(
        error instanceof Error ? `❌ Error loading schema: ${error.message}` : '❌ Error loading schema'
      );
      setShowSchema(true);
    }
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
          minWidth: '700px',
          maxWidth: '900px',
          maxHeight: '85vh',
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
          <h2 style={{ margin: 0, fontSize: '20px', color: '#ffffff' }}>Set Universe Constraint</h2>
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

        {/* Instructions */}
        <div style={{
          marginBottom: '15px',
          padding: '12px',
          backgroundColor: '#2c3e50',
          borderRadius: '4px',
          fontSize: '13px',
          color: '#ecf0f1',
          lineHeight: '1.5',
        }}>
          <strong>Enter a SQL WHERE clause</strong> to constrain the universe of papers. This constraint will be applied to all queries.
        </div>

        {/* Natural Language Input Section */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            marginBottom: '5px',
            color: '#ffffff',
            fontSize: '14px',
            fontWeight: 'bold',
          }}>
            Natural Language Request:
          </label>
          <p style={{
            color: '#ecf0f1',
            fontSize: '12px',
            marginBottom: '8px',
            marginTop: 0,
          }}>
            Describe what papers you want to see in plain English:
          </p>
          <textarea
            value={naturalLanguage}
            onChange={(e) => {
              setNaturalLanguage(e.target.value);
              setGenerationStatus(null);
            }}
            placeholder='e.g., "Show me OpenAlex papers from US and China" or "RAND documents with type = RR"'
            style={{
              width: '100%',
              minHeight: '60px',
              resize: 'vertical',
              border: '1px solid #95a5a6',
              borderRadius: '4px',
              padding: '8px',
              fontSize: '14px',
              fontFamily: 'monospace',
              marginBottom: '10px',
              backgroundColor: '#ecf0f1',
              color: '#2c3e50',
            }}
          />
          <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
            <button
              onClick={handleGenerateSql}
              disabled={generating || !naturalLanguage.trim()}
              style={{
                backgroundColor: generating ? '#7f8c8d' : '#007bff',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                marginBottom: '10px',
                cursor: generating || !naturalLanguage.trim() ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                opacity: generating || !naturalLanguage.trim() ? 0.6 : 1,
              }}
              onMouseOver={(e) => {
                if (!generating && naturalLanguage.trim()) {
                  e.currentTarget.style.backgroundColor = '#0056b3';
                }
              }}
              onMouseOut={(e) => {
                if (!generating) {
                  e.currentTarget.style.backgroundColor = '#007bff';
                }
              }}
            >
              {generating ? 'Generating...' : 'Generate SQL'}
            </button>
            <button
              onClick={handleViewSchema}
              style={{
                backgroundColor: '#6f42c1',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                marginBottom: '10px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#5a32a3'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#6f42c1'}
            >
              {showSchema ? '✕ Close Schema' : '📋 View Schema'}
            </button>
          </div>
          
          {/* Generation Status */}
          {generationStatus && (
            <div style={{
              marginBottom: '15px',
              padding: '8px 12px',
              backgroundColor: generationStatus.startsWith('❌') ? '#e74c3c' : generationStatus.startsWith('⚠️') ? '#f39c12' : '#27ae60',
              borderRadius: '4px',
              fontSize: '13px',
              color: '#ffffff',
            }}>
              {generationStatus}
            </div>
          )}

          {/* Schema Display */}
          {showSchema && schemaDisplay && (
            <div style={{
              marginBottom: '15px',
              maxHeight: '400px',
              overflowY: 'auto',
              backgroundColor: '#2c3e50',
              padding: '20px',
              borderRadius: '8px',
              border: '1px solid #95a5a6',
            }}>
              <h4 style={{
                color: '#3498db',
                marginBottom: '15px',
                textAlign: 'center',
                fontSize: '16px',
              }}>
                📋 Database Schema
              </h4>
              <pre style={{
                color: '#ecf0f1',
                fontSize: '12px',
                lineHeight: '1.4',
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
                fontFamily: 'monospace',
                margin: 0,
              }}>
                {schemaDisplay}
              </pre>
            </div>
          )}
        </div>

        {/* Example Query */}
        <div style={{ marginBottom: '15px' }}>
          <label style={{
            display: 'block',
            marginBottom: '5px',
            color: '#ffffff',
            fontSize: '14px',
            fontWeight: 'bold',
          }}>
            Example:
          </label>
          <code style={{
            display: 'block',
            background: '#2c3e50',
            padding: '10px',
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '12px',
            color: '#ecf0f1',
            marginBottom: '15px',
          }}>
            doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR'
          </code>
        </div>

        {/* SQL Input */}
        <div style={{ marginBottom: '15px', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            color: '#ffffff',
            fontSize: '14px',
            fontWeight: '500',
          }}>
            SQL WHERE Clause:
          </label>
          <textarea
            value={universeConstraints}
            onChange={(e) => {
              setUniverseConstraints(e.target.value);
              setTestResult(null); // Clear test result when typing
            }}
            placeholder="Enter SQL WHERE clause (e.g., doctrove_source = 'openalex' AND openalex_country_uschina = 'United States')"
            style={{
              flex: 1,
              minHeight: '120px',
              padding: '12px',
              backgroundColor: '#ecf0f1',
              border: '1px solid #95a5a6',
              borderRadius: '4px',
              fontSize: '14px',
              fontFamily: 'monospace',
              resize: 'vertical',
              color: '#2c3e50',
            }}
          />
        </div>

        {/* Test Result */}
        {testResult && (
          <div style={{
            marginBottom: '15px',
            padding: '10px 12px',
            backgroundColor: testResult.success ? '#27ae60' : '#e74c3c',
            borderRadius: '4px',
            fontSize: '13px',
            color: '#ffffff',
          }}>
            {testResult.message}
          </div>
        )}

        {/* Buttons */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: '10px',
        }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleTest}
              disabled={testing || !universeConstraints.trim()}
              style={{
                padding: '10px 20px',
                backgroundColor: testing ? '#7f8c8d' : '#9b59b6',
                color: '#ffffff',
                border: 'none',
                borderRadius: '4px',
                cursor: testing ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                opacity: testing ? 0.6 : 1,
              }}
              onMouseOver={(e) => {
                if (!testing && universeConstraints.trim()) {
                  e.currentTarget.style.backgroundColor = '#8e44ad';
                }
              }}
              onMouseOut={(e) => {
                if (!testing) {
                  e.currentTarget.style.backgroundColor = '#9b59b6';
                }
              }}
            >
              {testing ? 'Testing...' : 'Test Query'}
            </button>
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
          </div>
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

