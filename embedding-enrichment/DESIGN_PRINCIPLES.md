# Design Principles

## Overview

This document outlines the core design principles that guide our development of the DocTrove system and its microservices. These principles ensure consistency, maintainability, and scalability across all components.

## Core Principles

### 1. **Functional Programming First**

**Pure Functions**: All business logic should be implemented as pure functions with no side effects.

```python
# ✅ Good: Pure function
def calculate_credibility_score(paper: Dict, metadata: Dict) -> float:
    """Calculate credibility score from paper and metadata."""
    factors = {}
    total_score = 0.0
    
    if 'journal_impact_factor' in metadata:
        impact_factor = float(metadata['journal_impact_factor'])
        journal_score = min(impact_factor / 50.0, 1.0)
        factors['journal_impact'] = journal_score
        total_score += journal_score * 0.3
    
    return total_score

# ❌ Bad: Impure function with side effects
def calculate_credibility_score(paper: Dict, metadata: Dict) -> float:
    """Calculate credibility score and log to database."""
    score = some_calculation(paper, metadata)
    log_to_database(score)  # Side effect!
    return score
```

**Benefits**:
- Easy to test in isolation
- Predictable outputs for given inputs
- No hidden dependencies or side effects
- Composable and reusable

### 2. **Interceptor Pattern for Cross-Cutting Concerns**

**Definition**: An interceptor is a data structure with 0-3 functions:
- `enter`: Called on the way into the stack
- `leave`: Called on the way out of the stack
- `error`: Called if an error occurs

**Key Rules**:
- All functions have the same signature: `(context: Dict) -> Dict`
- Interceptors should do ONE thing only
- More interceptors are preferred to larger interceptors
- No error handling except as required for side-effecting APIs

```python
# ✅ Good: Simple, focused interceptor
def log_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log entry into a phase"""
    phase = ctx.get('phase', 'unknown')
    logger.info(f"Entering phase: {phase}")
    return ctx

# ❌ Bad: Interceptor doing multiple things
def complex_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log, validate, and transform data"""
    # Too many responsibilities!
    ctx = log_enter(ctx)
    ctx = validate_data(ctx)
    ctx = transform_data(ctx)
    return ctx
```

**Benefits**:
- Composable service logic
- Consistent error handling
- Resource management (connections, cleanup)
- Testable in isolation

### 3. **Dependency Injection**

**Connection Factory Pattern**: Use factory functions for database connections and other dependencies.

```python
# ✅ Good: Dependency injection
def create_connection_factory():
    """Creates a database connection factory."""
    def get_connection():
        return psycopg2.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
    return get_connection

def get_papers_with_embeddings(connection_factory: Callable, limit: int = None):
    """Uses injected connection factory."""
    with connection_factory() as conn:
        # Database operations here
        pass

# ❌ Bad: Hard-coded dependencies
def get_papers_with_embeddings(limit: int = None):
    """Hard-coded database connection."""
    conn = psycopg2.connect(host="localhost", ...)  # Hard-coded!
    # Database operations here
```

**Benefits**:
- Easy to test with mock dependencies
- Flexible configuration
- No hard-coded dependencies
- Consistent resource management

### 4. **Comprehensive Testing Strategy**

**Three-Layer Testing**:
1. **Unit Tests**: Pure functions with no dependencies
2. **Integration Tests**: Full workflows with real dependencies
3. **Framework Tests**: Test the framework itself

```python
# ✅ Good: Comprehensive test coverage
class TestEnrichmentFunctions(unittest.TestCase):
    def test_calculate_credibility_score_pure(self):
        """Test pure function with known inputs/outputs."""
        paper = {'source': 'nature', 'title': 'Test Paper'}
        metadata = {'journal_impact_factor': '45.0', 'citation_count': '500'}
        
        score = calculate_credibility_score(paper, metadata)
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIsInstance(score, float)

class TestEnrichmentIntegration(unittest.TestCase):
    @patch('db.create_connection_factory')
    def test_full_enrichment_pipeline(self, mock_factory):
        """Test complete enrichment workflow."""
        # Integration test with mocked database
        pass
```

**Benefits**:
- Confidence in code correctness
- Easy refactoring
- Documentation through tests
- Regression prevention

### 5. **Data Integrity and Separation**

**Source Tables Are Sacred**: Never modify source metadata tables.

```python
# ✅ Good: Read-only access to source tables
def get_source_metadata(paper: Dict, connection_factory) -> Dict[str, Any]:
    """READ from source metadata tables (never write)."""
    source = paper.get('doctrove_source', '').lower()
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # READ ONLY from source table
            cur.execute(f"SELECT * FROM {source}_metadata WHERE doctrove_paper_id = %s", 
                       (paper['doctrove_paper_id'],))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
    return {}

# ❌ Bad: Writing to source tables
def process_enrichment(paper: Dict, connection_factory) -> None:
    """Process enrichment and update source table."""
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Don't write to source tables!
            cur.execute("UPDATE aipickle_metadata SET enriched = true WHERE ...")
```

**Benefits**:
- Preserves data integrity
- Clear separation of raw vs. computed data
- No risk of corrupting source data
- Audit trail of enrichment processes

### 6. **Standardized Patterns**

**Consistent Architecture**: All components follow the same patterns.

**Enrichment Pattern**:
```python
class BaseEnrichment(ABC):
    """Base class for all enrichment modules."""
    
    def __init__(self, enrichment_name: str, enrichment_type: str):
        self.enrichment_name = enrichment_name
        self.enrichment_type = enrichment_type
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Fields required from main table or source metadata."""
        pass
    
    @abstractmethod
    def process_papers(self, papers: List[Dict]) -> List[Dict]:
        """Process papers and return enrichment results."""
        pass
```

**Database Pattern**:
```python
def create_connection_factory():
    """Standard connection factory pattern."""
    def get_connection():
        return psycopg2.connect(...)
    return get_connection

def get_data(connection_factory: Callable, **kwargs) -> List[Dict]:
    """Standard data retrieval pattern."""
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Database operations
            pass
```

**Benefits**:
- Consistent codebase
- Easy onboarding for new developers
- Predictable behavior
- Reduced cognitive load

### 7. **Error Handling and Resilience**

**Graceful Degradation**: Handle errors without stopping the entire process.

```python
# ✅ Good: Graceful error handling
def process_papers_batch(papers: List[Dict], enrichment) -> int:
    """Process papers with individual error handling."""
    successful_count = 0
    
    for paper in papers:
        try:
            result = enrichment.process_single_paper(paper)
            if result:
                successful_count += 1
        except Exception as e:
            logger.error(f"Error processing paper {paper.get('id')}: {e}")
            continue  # Continue with next paper
    
    return successful_count

# ❌ Bad: All-or-nothing processing
def process_papers_batch(papers: List[Dict], enrichment) -> int:
    """Process all papers or fail completely."""
    results = [enrichment.process_single_paper(paper) for paper in papers]
    return len(results)  # Fails if any paper fails
```

**Benefits**:
- Robust production systems
- Partial success handling
- Better user experience
- Easier debugging

### 8. **Performance and Scalability**

**Adaptive Design**: Systems should adapt to different scales and requirements.

```python
# ✅ Good: Adaptive batch sizing
def get_adaptive_batch_size(total_papers: int) -> int:
    """Determine optimal batch size based on dataset size."""
    if total_papers <= 5000:
        return 500
    elif total_papers <= 50000:
        return 2000
    elif total_papers <= 500000:
        return 10000
    else:
        return 20000

# ❌ Bad: Fixed batch sizes
def process_papers(papers: List[Dict]) -> None:
    """Process papers in fixed batches."""
    batch_size = 1000  # Fixed size regardless of dataset
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]
        process_batch(batch)
```

**Benefits**:
- Optimal performance at different scales
- Resource efficiency
- Better user experience
- Future-proof design

### 9. **Documentation and Transparency**

**Self-Documenting Code**: Code should be clear and well-documented.

```python
# ✅ Good: Clear, documented code
def calculate_credibility_score(paper: Dict, source_metadata: Dict) -> Tuple[float, float, Dict, Dict]:
    """
    Calculate credibility score from paper and metadata.
    
    Args:
        paper: Paper dictionary with source information
        source_metadata: Source-specific metadata (journal impact, citations, etc.)
        
    Returns:
        Tuple of (score, confidence, factors, metadata):
        - score: Credibility score between 0.0 and 1.0
        - confidence: Confidence in the score between 0.0 and 1.0
        - factors: Contributing factors and their weights
        - metadata: Raw metadata used in calculation
    """
    factors = {}
    total_score = 0.0
    
    # Journal impact factor (30% weight)
    if 'journal_impact_factor' in source_metadata:
        impact_factor = float(source_metadata['journal_impact_factor'])
        journal_score = min(impact_factor / 50.0, 1.0)
        factors['journal_impact'] = journal_score
        total_score += journal_score * 0.3
    
    return total_score, confidence, factors, metadata

# ❌ Bad: Unclear, undocumented code
def calc_score(p, m):
    """Calculate score."""
    s = 0
    if 'jif' in m:
        s += min(float(m['jif']) / 50, 1) * 0.3
    return s
```

**Benefits**:
- Easy to understand and maintain
- Better onboarding for new developers
- Reduced bugs from misunderstandings
- Self-documenting system

### 10. **Monitoring and Observability**

**Comprehensive Logging**: Log important events and state changes.

```python
# ✅ Good: Comprehensive logging
def run_enrichment(enrichment, papers: List[Dict]) -> int:
    """Run enrichment with detailed logging."""
    logger.info(f"Starting {enrichment.enrichment_name} enrichment for {len(papers)} papers")
    
    start_time = time.time()
    results = enrichment.process_papers(papers)
    processing_time = time.time() - start_time
    
    inserted_count = enrichment.insert_results(results)
    
    logger.info(f"Completed {enrichment.enrichment_name} enrichment: "
                f"{inserted_count}/{len(papers)} papers enriched in {processing_time:.2f}s")
    
    return inserted_count

# ❌ Bad: Minimal logging
def run_enrichment(enrichment, papers: List[Dict]) -> int:
    """Run enrichment with minimal logging."""
    results = enrichment.process_papers(papers)
    return len(results)
```

**Benefits**:
- Easy debugging in production
- Performance monitoring
- Audit trails
- Better user support

## Implementation Guidelines

### Code Organization

```
service/
├── main.py              # Entry point with interceptors
├── business_logic.py    # Pure functions
├── db.py               # Database operations with DI
├── interceptor.py      # Interceptor framework
├── config.py           # Configuration management
├── tests/
│   ├── test_business_logic.py  # Unit tests for pure functions
│   └── test_integration.py     # Integration tests
└── README.md           # Service documentation
```

### Naming Conventions

- **Functions**: `snake_case` for all functions
- **Classes**: `PascalCase` for classes
- **Constants**: `UPPER_SNAKE_CASE` for constants
- **Files**: `snake_case` for Python files
- **Tables**: `snake_case` for database tables

### Error Handling

- **Pure Functions**: Should not handle errors (let them bubble up)
- **Impure Functions**: Should handle errors and log appropriately
- **Interceptors**: Should handle errors in error functions
- **Main Entry Points**: Should catch and log all unhandled errors

### Testing Strategy

- **Unit Tests**: Test pure functions with known inputs/outputs
- **Integration Tests**: Test complete workflows with mocked dependencies
- **Framework Tests**: Test the framework itself (interceptors, DI, etc.)
- **Coverage**: Aim for >90% code coverage

## Frontend Design Principles (DocScope)

### Overview

While the core principles apply to all components, frontend applications like DocScope have unique requirements and constraints that necessitate adapted design principles focused on user experience, performance, and interactive behavior.

### Frontend-Specific Principles

#### 1. **Component-Based Architecture**

**Separation of UI Logic**: Break the application into logical, reusable components.

```python
# ✅ Good: Separated concerns
class PapersDataService:
    """Pure data service with no UI dependencies."""
    def fetch_papers(self, bbox: str, limit: int) -> pd.DataFrame:
        # Pure data logic only
        pass

class VisualizationComponent:
    """Pure visualization component."""
    def update_plot(self, data: pd.DataFrame) -> go.Figure:
        # Pure visualization logic only
        pass

# ❌ Bad: Mixed concerns
def handle_zoom_data_fetching(relayoutData, data_loaded):
    """Mixed data fetching, state management, and UI updates."""
    # Too many responsibilities in one function
```

**Benefits**:
- Easier to test individual components
- Reusable components
- Clear separation of concerns
- Better maintainability

#### 2. **Reactive State Management**

**Unidirectional Data Flow**: State changes flow in one direction, triggering UI updates.

```python
# ✅ Good: Centralized state management
app.layout = html.Div([
    dcc.Store(id='papers-data', data=[]),
    dcc.Store(id='view-coverage', data=None),
    dcc.Store(id='cache-stats', data={'hits': 0, 'misses': 0}),
    # UI components that react to state changes
])

# ❌ Bad: Global variables
df = pd.DataFrame()  # Global state
countries = []       # Global state
data_cache = {}      # Global state
```

**Benefits**:
- Predictable state changes
- Easier debugging
- Better performance
- Clear data flow

#### 3. **Performance-First Design**

**User Experience Priority**: Optimize for responsiveness and smooth interactions.

```python
# ✅ Good: Efficient data fetching
def fetch_papers_with_caching(bbox: str, limit: int) -> pd.DataFrame:
    """Fetch with intelligent caching."""
    cache_key = get_cache_key(bbox, limit)
    if cache_key in data_cache:
        return data_cache[cache_key]  # Fast cache hit
    # Fetch from API only when needed

# ❌ Bad: Inefficient fetching
def fetch_papers(bbox: str, limit: int) -> pd.DataFrame:
    """Always fetch from API."""
    return fetch_from_api(bbox, limit)  # Always slow
```

**Benefits**:
- Fast user interactions
- Reduced server load
- Better user experience
- Scalable to large datasets

#### 4. **Progressive Enhancement**

**Graceful Degradation**: Core functionality works without advanced features.

```python
# ✅ Good: Progressive enhancement
@app.callback(Output('graph-3', 'figure'), [Input('data-loaded', 'data')])
def update_visualization(data_loaded):
    if not data_loaded:
        return create_loading_figure()  # Basic functionality
    return create_full_visualization()  # Enhanced functionality

# ❌ Bad: All-or-nothing approach
@app.callback(Output('graph-3', 'figure'), [Input('data-loaded', 'data')])
def update_visualization(data_loaded):
    if not data_loaded:
        return None  # No functionality
    return create_full_visualization()
```

**Benefits**:
- Works in all environments
- Better accessibility
- Faster initial load
- Robust error handling

#### 5. **Configuration-Driven Design**

**Environment-Specific Settings**: Centralized configuration for different environments.

```python
# ✅ Good: Configuration-driven
class Config:
    TARGET_RECORDS_PER_VIEW = int(os.getenv('TARGET_RECORDS', 500))
    MAX_CACHE_SIZE = int(os.getenv('MAX_CACHE_SIZE', 50))
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')

# ❌ Bad: Hard-coded values
TARGET_RECORDS_PER_VIEW = 500  # Hard-coded
MAX_CACHE_SIZE = 50            # Hard-coded
API_BASE_URL = "http://localhost:5000/api"  # Hard-coded
```

**Benefits**:
- Easy environment switching
- No code changes for deployment
- Consistent configuration
- Better testing

#### 6. **Intelligent Caching Strategy**

**Multi-Level Caching**: Cache at appropriate levels for optimal performance.

```python
# ✅ Good: Multi-level caching
def fetch_papers_with_caching(bbox: str, limit: int) -> pd.DataFrame:
    # Level 1: Memory cache
    cache_key = get_cache_key(bbox, limit)
    if cache_key in data_cache:
        return data_cache[cache_key]
    
    # Level 2: API call with caching
    df = fetch_papers_from_api(bbox, limit)
    data_cache[cache_key] = df
    return df

# ❌ Bad: No caching
def fetch_papers(bbox: str, limit: int) -> pd.DataFrame:
    return fetch_papers_from_api(bbox, limit)  # Always slow
```

**Benefits**:
- Fast repeated requests
- Reduced server load
- Better user experience
- Efficient resource usage

#### 7. **Responsive Error Handling**

**User-Friendly Errors**: Provide clear feedback for different error scenarios.

```python
# ✅ Good: User-friendly error handling
def fetch_papers_from_api(bbox: str, limit: int) -> pd.DataFrame:
    try:
        response = requests.get(f"{API_BASE_URL}/papers", params=params)
        response.raise_for_status()
        return pd.DataFrame(response.json()['papers'])
    except requests.exceptions.ConnectionError:
        return pd.DataFrame()  # Graceful degradation
    except requests.exceptions.RequestException as e:
        logger.error(f"API error: {e}")
        return pd.DataFrame()  # Graceful degradation

# ❌ Bad: Crashing on errors
def fetch_papers_from_api(bbox: str, limit: int) -> pd.DataFrame:
    response = requests.get(f"{API_BASE_URL}/papers", params=params)
    return pd.DataFrame(response.json()['papers'])  # Crashes on error
```

**Benefits**:
- Better user experience
- Robust application
- Clear error feedback
- Graceful degradation

### Frontend Implementation Guidelines

#### Code Organization

```
docscope/
├── docscope.py              # Main application
├── components/
│   ├── data_service.py      # Pure data logic
│   ├── visualization.py     # Pure visualization logic
│   └── state_manager.py     # State management
├── config/
│   └── settings.py          # Configuration management
├── utils/
│   ├── caching.py           # Caching utilities
│   └── helpers.py           # Helper functions
└── tests/
    ├── test_data_service.py # Unit tests
    └── test_components.py   # Component tests
```

#### State Management Patterns

```python
# Use dcc.Store for state
app.layout = html.Div([
    # Data state
    dcc.Store(id='papers-data', data=[]),
    dcc.Store(id='view-coverage', data=None),
    
    # UI state
    dcc.Store(id='selected-papers', data=[]),
    dcc.Store(id='filter-settings', data={}),
    
    # Cache state
    dcc.Store(id='cache-stats', data={'hits': 0, 'misses': 0}),
    
    # UI components
    html.Div(id='visualization-area'),
    html.Div(id='controls-area'),
])
```

#### Performance Optimization

```python
# Debounce user interactions
@app.callback(
    Output('graph-3', 'figure'),
    [Input('graph-3', 'relayoutData')],
    [State('graph-3', 'figure')],
    prevent_initial_call=True
)
def debounced_zoom_update(relayoutData, current_figure):
    # Add debouncing logic here
    pass

# Efficient data updates
def update_visualization(data: pd.DataFrame, filters: Dict) -> go.Figure:
    # Only update what changed
    if not data.empty:
        return create_figure(data, filters)
    return current_figure
```

### Frontend Testing Strategy

#### Component Testing

```python
class TestDataService(unittest.TestCase):
    def test_fetch_papers_pure(self):
        """Test pure data fetching logic."""
        service = PapersDataService()
        result = service.fetch_papers("0,0,1,1", 100)
        self.assertIsInstance(result, pd.DataFrame)

class TestVisualizationComponent(unittest.TestCase):
    def test_figure_creation(self):
        """Test visualization component."""
        component = VisualizationComponent()
        fig = component.create_figure(sample_data)
        self.assertIsInstance(fig, go.Figure)
```

#### Integration Testing

```python
class TestDocScopeIntegration(unittest.TestCase):
    def test_full_user_workflow(self):
        """Test complete user interaction workflow."""
        # Simulate user interactions
        # Test data flow
        # Verify UI updates
        pass
```

## Conclusion

These design principles ensure that our codebase is:
- **Maintainable**: Clear patterns and comprehensive testing
- **Scalable**: Adaptive design and efficient resource usage
- **Reliable**: Robust error handling and data integrity
- **Testable**: Pure functions and dependency injection
- **Observable**: Comprehensive logging and monitoring
- **User-Friendly**: Fast, responsive, and intuitive interfaces

Following these principles consistently across all services will result in a robust, maintainable, and scalable system that provides excellent user experiences. 