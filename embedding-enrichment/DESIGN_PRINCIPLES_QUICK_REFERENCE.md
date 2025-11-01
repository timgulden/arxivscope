# Design Principles Quick Reference

## 🎯 Core Principles

### 1. **Functional Programming First**
- ✅ **Pure Functions**: No side effects, predictable outputs
- ✅ **Testable**: Easy to test in isolation
- ✅ **Composable**: Functions can be combined and reused

### 2. **Interceptor Pattern**
- ✅ **Single Responsibility**: Each interceptor does ONE thing
- ✅ **Consistent Signature**: `(context: Dict) -> Dict`
- ✅ **Error Handling**: Built-in error recovery

### 3. **Dependency Injection**
- ✅ **Connection Factory**: `create_connection_factory()`
- ✅ **Testable**: Easy to mock dependencies
- ✅ **Flexible**: No hard-coded dependencies

### 4. **Comprehensive Testing**
- ✅ **Unit Tests**: Pure functions with known inputs/outputs
- ✅ **Integration Tests**: Full workflows with mocked dependencies
- ✅ **Framework Tests**: Test the framework itself

### 5. **Data Integrity**
- ✅ **Source Tables Sacred**: Never modify source metadata tables
- ✅ **Read-Only Access**: Enrichments read from source tables only
- ✅ **Clear Separation**: Raw data vs. computed data

## 📝 Code Patterns

### Pure Function Pattern
```python
def calculate_score(data: Dict) -> float:
    """Pure function with no side effects."""
    # Business logic here
    return score
```

### Interceptor Pattern
```python
def log_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Simple, focused interceptor."""
    phase = ctx.get('phase', 'unknown')
    logger.info(f"Entering phase: {phase}")
    return ctx
```

### Dependency Injection Pattern
```python
def get_data(connection_factory: Callable) -> List[Dict]:
    """Uses injected connection factory."""
    with connection_factory() as conn:
        # Database operations
        pass
```

### Enrichment Pattern
```python
class MyEnrichment(BaseEnrichment):
    def __init__(self):
        super().__init__("my_enrichment", "derived")
    
    def process_papers(self, papers: List[Dict]) -> List[Dict]:
        # Pure enrichment logic
        pass
```

## 🚫 Anti-Patterns to Avoid

### ❌ Impure Functions
```python
def bad_function(data: Dict) -> float:
    score = calculate(data)
    log_to_database(score)  # Side effect!
    return score
```

### ❌ Complex Interceptors
```python
def bad_interceptor(ctx: Dict) -> Dict:
    # Too many responsibilities!
    ctx = log_enter(ctx)
    ctx = validate_data(ctx)
    ctx = transform_data(ctx)
    return ctx
```

### ❌ Hard-Coded Dependencies
```python
def bad_function():
    conn = psycopg2.connect(host="localhost", ...)  # Hard-coded!
    # Database operations
```

### ❌ Writing to Source Tables
```python
def bad_enrichment(paper: Dict, connection_factory):
    with connection_factory() as conn:
        # Don't write to source tables!
        cur.execute("UPDATE aipickle_metadata SET enriched = true")
```

## 🧪 Testing Strategy

### Unit Tests (Pure Functions)
```python
def test_calculate_score():
    data = {'value': 10}
    result = calculate_score(data)
    assert result == 5.0
```

### Integration Tests (Workflows)
```python
@patch('db.create_connection_factory')
def test_full_workflow(mock_factory):
    # Test complete workflow with mocked dependencies
    pass
```

## 📊 Error Handling

### Pure Functions
- Let errors bubble up
- No error handling needed

### Impure Functions
- Handle errors and log appropriately
- Graceful degradation

### Interceptors
- Handle errors in error functions
- Clean up resources

## 🔧 Implementation Guidelines

### File Organization
```
service/
├── main.py              # Entry point with interceptors
├── business_logic.py    # Pure functions
├── db.py               # Database operations with DI
├── interceptor.py      # Interceptor framework
├── config.py           # Configuration
├── tests/              # Comprehensive tests
└── README.md           # Documentation
```

### Naming Conventions
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case`

## 🎯 Key Benefits

- **Maintainable**: Clear patterns and comprehensive testing
- **Scalable**: Adaptive design and efficient resource usage
- **Reliable**: Robust error handling and data integrity
- **Testable**: Pure functions and dependency injection
- **Observable**: Comprehensive logging and monitoring
- **Performant**: Optimized database queries and strategic indexing

## 🚀 Recent Performance Improvements

### Database Optimization
- **Strategic Indexing**: Multiple indexes for common query patterns
- **Composite Indexes**: Optimized join performance
- **Covering Indexes**: Reduced table lookups
- **Spatial Indexes**: GiST indexes for 2D embedding queries
- **Query Performance**: 95%+ improvement in response times

### System Integration
- **Ingestion Pipeline**: Fixed limit handling and validation
- **Enrichment Framework**: Asynchronous processing with model caching
- **API Performance**: Response times reduced from seconds to milliseconds
- **Data Quality**: Standardized field mapping and deduplication

## 📚 Related Documents

- `DESIGN_PRINCIPLES.md` - Detailed design principles
- `enrichment_architecture.md` - Enrichment architecture
- `interceptor101.md` - Interceptor pattern details
- `README.md` - Service documentation 