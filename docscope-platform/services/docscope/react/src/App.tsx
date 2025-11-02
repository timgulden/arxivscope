import { useEffect, useState } from 'react';
import { useAppState } from './hooks/useAppState';
import { useDataFetch } from './hooks/useDataFetch';
import { MainCanvas } from './components/MainCanvas';
import { MetadataSidebar } from './components/MetadataSidebar';
import { DateSlider } from './components/DateSlider';
import { SemanticFilterModal } from './components/SemanticFilterModal';
import { TopBarControls } from './components/TopBarControls';
import { UniverseFilterModal } from './components/UniverseFilterModal';
import { 
  createFetchRequest, 
  testQuery,
  toggleClustering, 
  updateClusterCount, 
  updateViewLimit,
  parseClusterCount,
  parseLimit
} from './logic';
import './App.css';

function App() {
  const [state, dispatch] = useAppState();
  const { fetchPapers, fetchMaxExtent } = useDataFetch(dispatch);
  const [semanticFilterOpen, setSemanticFilterOpen] = useState(false);
  const [universeFilterOpen, setUniverseFilterOpen] = useState(false);
  // TODO: Add symbolization and sort state to proper state management
  const [symbolizationActive, setSymbolizationActive] = useState(false);
  const [sortActive, setSortActive] = useState(false);

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

  // ============================================================================
  // Top Bar Controls Handlers - Using Pure Functions from Logic Layer
  // ============================================================================

  // Handle clustering toggle - uses pure function from logic layer
  const handleClusteringToggle = () => {
    const newEnrichment = toggleClustering(state.enrichment);
    dispatch({ type: 'ENRICHMENT_UPDATE', payload: newEnrichment });
  };

  // Handle compute clusters button - uses pure functions from logic layer
  const handleComputeClusters = async (clusterCount: number) => {
    const newEnrichment = updateClusterCount(state.enrichment, clusterCount);
    
    if (newEnrichment) {
      dispatch({ type: 'ENRICHMENT_UPDATE', payload: newEnrichment });
      
      // Trigger data refetch with updated enrichment
      const fetchRequest = createFetchRequest(state.view, state.filter, newEnrichment);
      await fetchPapers(fetchRequest);
    }
  };

  // Handle cluster count input change - uses pure parsing function
  const handleClusterCountChange = (value: string) => {
    // Just validate - actual update happens on blur or compute button click
    // This is just for immediate feedback while typing
    const parsed = parseClusterCount(value);
    // Could track valid/invalid state for UI feedback if needed
  };

  // Handle limit/fetch input change - uses pure functions from logic layer
  const handleLimitChange = async (value: string) => {
    const limit = parseLimit(value);
    
    if (limit !== null) {
      const newView = updateViewLimit(state.view, limit);
      
      if (newView) {
        dispatch({ type: 'VIEW_UPDATE', payload: newView });
        
        // Trigger data refetch with new limit
        const fetchRequest = createFetchRequest(newView, state.filter, state.enrichment);
        await fetchPapers(fetchRequest);
      }
    }
  };

  // Handle universe filter test - uses pure function from logic layer
  const handleTestUniverseQuery = async (sql: string): Promise<{ success: boolean; message: string }> => {
    // Create API provider function
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/api';
    const apiProvider = async (params: { sqlFilter: string }) => {
      const response = await fetch(
        `${apiBaseUrl}/papers?sql_filter=${encodeURIComponent(params.sqlFilter)}&limit=1&test_query=true`,
        { method: 'GET' }
      );
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      return await response.json();
    };

    // Use pure function from logic layer
    return testQuery(sql, apiProvider);
  };

  // Handle universe filter application - uses pure functions from logic layer
  const handleUniverseFilterApply = async (universeConstraints: string | null) => {
    // Update filter state
    dispatch({
      type: 'FILTER_UPDATE',
      payload: {
        ...state.filter,
        universeConstraints,
        lastUpdate: Date.now(),
      },
    });

    // Trigger data fetch with updated filter
    const updatedFilter = {
      ...state.filter,
      universeConstraints,
      lastUpdate: Date.now(),
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
        justifyContent: 'space-between',
        fontSize: '14px',
        position: 'relative'
      }}>
        {/* Left Section: DocScope title */}
        <h1 style={{ margin: 0, fontSize: '18px' }}>DocScope</h1>
        
        {/* Top Bar Controls: Left, Center (Universe/Semantic/Symbolization cluster), Right */}
        <TopBarControls
          state={state}
          onCountClick={() => {/* TODO: Implement count display toggle */}}
          onClusteringToggle={handleClusteringToggle}
          onComputeClusters={handleComputeClusters}
          onClusterCountChange={handleClusterCountChange}
          onLimitChange={handleLimitChange}
          onUniverseFilterOpen={() => setUniverseFilterOpen(true)}
          onSemanticFilterOpen={() => setSemanticFilterOpen(true)}
          onSymbolizationOpen={() => {
            setSymbolizationActive(!symbolizationActive);
            // TODO: Implement symbolization modal
          }}
          onSortClick={() => {
            setSortActive(!sortActive);
            // TODO: Implement sort functionality
          }}
          symbolizationActive={symbolizationActive}
          sortActive={sortActive}
        />
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

      {/* Universe Filter Modal */}
      {universeFilterOpen && (
        <UniverseFilterModal
          state={state}
          onClose={() => setUniverseFilterOpen(false)}
          onTestQuery={handleTestUniverseQuery}
          onApply={handleUniverseFilterApply}
        />
      )}
    </div>
  );
}

export default App;
