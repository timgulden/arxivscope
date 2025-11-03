import { useEffect, useState, useRef } from 'react';
import { useAppState } from './hooks/useAppState';
import { useDataFetch } from './hooks/useDataFetch';
import { MainCanvas } from './components/MainCanvas';
import { MetadataSidebar } from './components/MetadataSidebar';
import { DateSlider } from './components/DateSlider';
import { SemanticFilterModal } from './components/SemanticFilterModal';
import { TopBarControls } from './components/TopBarControls';
import { UniverseFilterModal } from './components/UniverseFilterModal';
import { SymbolizationModal } from './components/SymbolizationModal';
import { 
  createFetchRequest, 
  testQuery,
  toggleClustering, 
  updateClusterCount, 
  updateViewLimit,
  parseClusterCount,
  parseLimit,
  generateSqlFromNaturalLanguage,
  createDefaultLlmApiProvider,
  computeClustersFrontend,
  createClusterAnnotations,
  getClusterSummaries,
  createDefaultSummariesApiProvider,
  setClusterComputing,
  setClustersVisible,
  hideClusters,
  setSymbolization,
  clearSymbolization,
  getSymbolizations,
  createDefaultSymbolizationApiProvider,
  type Symbolization
} from './logic';
import './App.css';

function App() {
  const [state, dispatch] = useAppState();
  const { fetchPapers, fetchMaxExtent } = useDataFetch(dispatch);
  const [semanticFilterOpen, setSemanticFilterOpen] = useState(false);
  const [universeFilterOpen, setUniverseFilterOpen] = useState(false);
  const [symbolizationOpen, setSymbolizationOpen] = useState(false);
  const [symbolizations, setSymbolizations] = useState<Symbolization[]>([]);
  const [symbolizationsLoading, setSymbolizationsLoading] = useState(false);
  // TODO: Add sort state to proper state management
  const [sortActive, setSortActive] = useState(false);
  // Debounce timers
  const limitDebounceRef = useRef<number | null>(null);
  const clusterDebounceRef = useRef<number | null>(null);

  // Fetch available symbolizations on mount
  useEffect(() => {
    const loadSymbolizations = async () => {
      setSymbolizationsLoading(true);
      try {
        const apiProvider = createDefaultSymbolizationApiProvider(
          import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
        );
        const results = await getSymbolizations(apiProvider);
        setSymbolizations(results);
      } catch (error) {
        console.error('Error loading symbolizations:', error);
      } finally {
        setSymbolizationsLoading(false);
      }
    };

    loadSymbolizations();
  }, []);

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

  // Handle compute clusters button - computes in frontend, fetches summaries from API
  const handleComputeClusters = async (clusterCount: number) => {
    console.log('handleComputeClusters called with:', clusterCount);
    console.log('Current papers count:', state.data.papers.length);
    
    try {
      // Set computing state
      let newEnrichment = setClusterComputing(state.enrichment, true);
      dispatch({ type: 'ENRICHMENT_UPDATE', payload: newEnrichment });
      console.log('Set computing state to true');
      
      // Get bbox - always use current view bounds or max extent
      // bbox format: [x_min, y_min, x_max, y_max]
      let bbox: [number, number, number, number];
      
      if (state.view.xRange && state.view.yRange) {
        // Use current view ranges
        bbox = [
          state.view.xRange[0],  // x_min
          state.view.yRange[0],  // y_min
          state.view.xRange[1],  // x_max
          state.view.yRange[1]   // y_max
        ];
        console.log('Using bbox from view ranges:', bbox);
      } else if (state.data.maxExtent) {
        // Use max extent (always available, even on startup)
        bbox = [
          state.data.maxExtent.xMin,
          state.data.maxExtent.yMin,
          state.data.maxExtent.xMax,
          state.data.maxExtent.yMax
        ];
        console.log('Using bbox from max extent:', bbox);
      } else {
        // Fallback: calculate from papers if nothing else available
        if (state.data.papers.length === 0) {
          throw new Error('No papers available for clustering');
        }
        const xs = state.data.papers.map(p => p.doctrove_embedding_2d.x);
        const ys = state.data.papers.map(p => p.doctrove_embedding_2d.y);
        bbox = [
          Math.min(...xs),
          Math.min(...ys),
          Math.max(...xs),
          Math.max(...ys)
        ];
        console.log('Using bbox from papers extent:', bbox);
      }
      
      // Compute clusters in frontend (KMeans + Voronoi)
      console.log('Computing clusters in frontend with bbox:', bbox);
      const { polygons, clusterCenters, titles } = computeClustersFrontend(
        state.data.papers,
        clusterCount,
        bbox
      );
      console.log('Clustering successful, got:', polygons.length, 'polygons');
      
      // Fetch LLM summaries from API
      const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';
      console.log('Fetching LLM summaries from API');
      const summariesProvider = createDefaultSummariesApiProvider(apiUrl);
      let summaries: string[];
      try {
        summaries = await getClusterSummaries(titles, summariesProvider);
        console.log('Got summaries from API:', summaries.length);
      } catch (error) {
        console.warn('Failed to get summaries from API, using fallback:', error);
        summaries = Array(clusterCenters.length).fill('Summary unavailable.');
      }
      
      // Create annotations from summaries
      const annotations = createClusterAnnotations(clusterCenters, summaries);
      
      // Set clusters visible with data and bbox
      const clusterData = { polygons, annotations };
      newEnrichment = setClustersVisible(newEnrichment, clusterData, bbox);
      dispatch({ type: 'ENRICHMENT_UPDATE', payload: newEnrichment });
      console.log('Set clusters visible with data and bbox:', bbox);
    } catch (error) {
      console.error('Error computing clusters:', error);
      console.error('Error details:', error instanceof Error ? error.message : String(error));
      // Reset computing state on error
      const newEnrichment = setClusterComputing(state.enrichment, false);
      dispatch({ type: 'ENRICHMENT_UPDATE', payload: newEnrichment });
      
      // Show error to user
      alert(`Error computing clusters: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  // Handle hide clusters button - uses pure function from logic layer
  const handleHideClusters = () => {
    const newEnrichment = hideClusters(state.enrichment);
    dispatch({ type: 'ENRICHMENT_UPDATE', payload: newEnrichment });
  };

  // Handle cluster count input change - uses pure parsing function
  const handleClusterCountChange = (value: string) => {
    // Debounce any potential downstream effects (currently only validation)
    if (clusterDebounceRef.current) {
      window.clearTimeout(clusterDebounceRef.current);
    }
    clusterDebounceRef.current = window.setTimeout(() => {
      // Validate input; actual compute happens on button click
      const _parsed = parseClusterCount(value);
    }, 1000);
  };

  // Handle limit/fetch input change - uses pure functions from logic layer
  const handleLimitChange = (value: string) => {
    // Debounce to avoid fetching on every keystroke
    if (limitDebounceRef.current) {
      window.clearTimeout(limitDebounceRef.current);
    }
    limitDebounceRef.current = window.setTimeout(async () => {
      const limit = parseLimit(value);
      if (limit !== null) {
        const newView = updateViewLimit(state.view, limit);
        if (newView) {
          dispatch({ type: 'VIEW_UPDATE', payload: newView });
          const fetchRequest = createFetchRequest(newView, state.filter, state.enrichment);
          await fetchPapers(fetchRequest);
        }
      }
    }, 1000);
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

  // Handle symbolization application - uses pure functions from logic layer
  const handleSymbolizationApply = async (symbolizationId: number | null) => {
    let updatedEnrichment: EnrichmentState;
    
    if (symbolizationId !== null) {
      // Find the selected symbolization to get color_map and enrichment_field
      const selectedSymbolization = symbolizations.find(s => s.id === symbolizationId);
      if (selectedSymbolization) {
        updatedEnrichment = setSymbolization(
          state.enrichment,
          symbolizationId,
          selectedSymbolization.color_map,
          selectedSymbolization.enrichment_field
        );
      } else {
        // Fallback if symbolization not found
        updatedEnrichment = setSymbolization(state.enrichment, symbolizationId);
      }
    } else {
      updatedEnrichment = clearSymbolization(state.enrichment);
    }
    
    dispatch({
      type: 'ENRICHMENT_UPDATE',
      payload: updatedEnrichment,
    });

    // Trigger data fetch with updated enrichment
    const fetchRequest = createFetchRequest(state.view, state.filter, updatedEnrichment);
    await fetchPapers(fetchRequest);
  };

  // Handle LLM SQL generation - uses pure functions from logic layer
  const handleGenerateSql = async (naturalLanguage: string) => {
    // Load documentation files
    let guideContent = '';
    let schemaContent = '';

    try {
      const guideResponse = await fetch('/docs/UNIVERSE_FILTER_GUIDE.md');
      if (guideResponse.ok) {
        guideContent = await guideResponse.text();
      } else {
        throw new Error('Failed to load UNIVERSE_FILTER_GUIDE.md');
      }

      const schemaResponse = await fetch('/docs/DATABASE_SCHEMA.md');
      if (schemaResponse.ok) {
        schemaContent = await schemaResponse.text();
      } else {
        throw new Error('Failed to load DATABASE_SCHEMA.md');
      }
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? `Failed to load documentation: ${error.message}` 
          : 'Failed to load documentation files'
      );
    }

    // Create API provider (uses backend /api/generate-sql endpoint)
    const apiProvider = createDefaultLlmApiProvider(import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001');

    // Use pure function from logic layer
    return generateSqlFromNaturalLanguage(naturalLanguage, guideContent, schemaContent, apiProvider);
  };

  // Handle View Schema - loads schema document
  const handleViewSchema = async (): Promise<string> => {
    try {
      const response = await fetch('/docs/DATABASE_SCHEMA.md');
      if (!response.ok) {
        throw new Error(`Failed to load DATABASE_SCHEMA.md: ${response.status}`);
      }
      return await response.text();
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? `Failed to load schema: ${error.message}` 
          : 'Failed to load schema document'
      );
    }
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
          onHideClusters={handleHideClusters}
          onClusterCountChange={handleClusterCountChange}
          onLimitChange={handleLimitChange}
          onUniverseFilterOpen={() => setUniverseFilterOpen(true)}
          onSemanticFilterOpen={() => setSemanticFilterOpen(true)}
          onSymbolizationOpen={() => setSymbolizationOpen(true)}
          onSortClick={() => {
            setSortActive(!sortActive);
            // TODO: Implement sort functionality
          }}
          symbolizationActive={state.enrichment.symbolizationId !== null}
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
          onGenerateSql={handleGenerateSql}
          onViewSchema={handleViewSchema}
        />
      )}

      {/* Symbolization Modal */}
      {symbolizationOpen && (
        <SymbolizationModal
          state={state}
          symbolizations={symbolizations}
          loading={symbolizationsLoading}
          onClose={() => setSymbolizationOpen(false)}
          onApply={handleSymbolizationApply}
        />
      )}
    </div>
  );
}

export default App;
