import { useEffect, useState } from 'react';
import { useAppState } from './hooks/useAppState';
import { useDataFetch } from './hooks/useDataFetch';
import { MainCanvas } from './components/MainCanvas';
import { MetadataSidebar } from './components/MetadataSidebar';
import { DateSlider } from './components/DateSlider';
import { SemanticFilterModal } from './components/SemanticFilterModal';
import { createFetchRequest } from './logic';
import './App.css';

function App() {
  const [state, dispatch] = useAppState();
  const { fetchPapers, fetchMaxExtent } = useDataFetch(dispatch);
  const [semanticFilterOpen, setSemanticFilterOpen] = useState(false);

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      // First, fetch max extent for home button functionality
      await fetchMaxExtent();
      
      // Then create fetch request and fetch papers
      const fetchRequest = createFetchRequest(state.view, state.filter, state.enrichment);
      await fetchPapers(fetchRequest);
    };

    // Only load if no papers are loaded yet
    if (state.data.papers.length === 0 && !state.data.loading) {
      loadInitialData();
    }
  }, []); // Empty deps - only run on mount

  // Handle date change with debouncing
  const handleDateChange = async (yearRange: [number, number]) => {
    // Create fetch request with updated date filter
    const fetchRequest = createFetchRequest(state.view, 
      { ...state.filter, yearRange, lastUpdate: Date.now() }, 
      state.enrichment);
    
    // Fetch papers
    await fetchPapers(fetchRequest);
  };

  // Handle semantic filter application
  const handleSemanticFilterApply = async (searchText: string | null, similarityThreshold: number) => {
    // Create fetch request with updated filter values
    const updatedFilter = {
      ...state.filter,
      searchText,
      similarityThreshold,
      lastUpdate: Date.now()
    };
    const fetchRequest = createFetchRequest(state.view, updatedFilter, state.enrichment);
    await fetchPapers(fetchRequest);
  };

  return (
    <div style={{ 
      width: '100vw', 
      height: '100vh',
      margin: 0,
      padding: 0,
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#1e1e1e',
      color: '#ffffff'
    }}>
      {/* Top bar */}
      <header style={{
        backgroundColor: '#2c3e50',
        padding: '10px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: '20px',
        fontSize: '14px',
        position: 'relative'
      }}>
        <h1 style={{ margin: 0, fontSize: '18px' }}>DocScope</h1>
        
        {/* Semantic Filter Button - Centered */}
        <button
          onClick={() => setSemanticFilterOpen(true)}
          style={{
            position: 'absolute',
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '6px 12px',
            backgroundColor: state.filter.searchText ? '#3498db' : '#27ae60',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
          onMouseOver={(e) => {
            if (state.filter.searchText) {
              e.currentTarget.style.backgroundColor = '#2980b9';
            } else {
              e.currentTarget.style.backgroundColor = '#229954';
            }
          }}
          onMouseOut={(e) => {
            if (state.filter.searchText) {
              e.currentTarget.style.backgroundColor = '#3498db';
            } else {
              e.currentTarget.style.backgroundColor = '#27ae60';
            }
          }}
        >
          Semantic Filter
        </button>
      </header>
      
      {/* Main content area - canvas and sidebar */}
      <div style={{ 
        flex: 1, 
        display: 'flex',
        flexDirection: 'row',
        overflow: 'hidden'
      }}>
        {/* Main canvas with date slider */}
        <div style={{ 
          flex: 1, 
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <div style={{ 
            flex: 1, 
            position: 'relative',
            overflow: 'hidden'
          }}>
            <MainCanvas state={state} dispatch={dispatch} onDataFetch={fetchPapers} />
          </div>
          {/* Date slider at bottom of canvas only */}
          <DateSlider state={state} dispatch={dispatch} onDateChange={handleDateChange} />
        </div>
        
        {/* Metadata sidebar - always rendered */}
        <MetadataSidebar state={state} dispatch={dispatch} />
      </div>
      
      {/* Semantic Filter Modal */}
      {semanticFilterOpen && (
        <SemanticFilterModal
          state={state}
          dispatch={dispatch}
          onClose={() => setSemanticFilterOpen(false)}
          onApply={handleSemanticFilterApply}
        />
      )}
    </div>
  );
}

export default App;
