# DocScope/DocTrove Project Overview

## System Architecture

DocScope/DocTrove is a comprehensive document analysis and visualization system with the following components:

### Core Components

1. **Document Ingestion Pipeline** (`doc-ingestor/`)
   - Processes various document sources (arXiv, AiPickle, etc.)
   - Configurable transformers for data normalization
   - Validation and deduplication
   - Supports batch and streaming ingestion

2. **Enrichment Framework** (`embedding-enrichment/`)
   - Generates 2D embeddings using UMAP
   - Asynchronous processing with database triggers
   - Background worker for automatic enrichment
   - Caches trained models for efficiency

3. **API Server** (`doctrove-api/`)
   - RESTful API for data access
   - Optimized queries with database indexes
   - Interceptor pattern for request/response processing
   - Comprehensive test coverage

4. **Frontend Application** (`docscope/` → migrating to React)
   - React UI with logic in TypeScript modules (strict separation of UI and logic)
   - Functional programming patterns for testable pure logic
   - Data access exclusively via DocTrove API boundary
   - Dash legacy remains in `docs/LEGACY/` for reference during migration

### Database Architecture

- **PostgreSQL** with **pgvector** extension for vector operations
- Optimized schema with proper indexing
- Composite indexes for join performance
- Partial GiST indexes for spatial queries
- Database functions for enrichment triggers

## Recent Major Improvements

### 1. Ingestion Pipeline Enhancements
- **Fixed limit handling**: Corrected bug where ingestion limits weren't properly applied
- **Data validation**: Added comprehensive validation interceptors
- **Source configuration**: Flexible mapping system for different data sources
- **Deduplication**: Automatic handling of duplicate records

### 2. Enrichment Framework
- **Asynchronous processing**: Database triggers for automatic enrichment
- **Background workers**: Non-blocking enrichment operations
- **Model caching**: Persistent UMAP models for efficiency
- **Incremental updates**: Only process new or changed records

### 3. API Performance Optimizations
- **Database indexes**: Multiple strategic indexes for query performance
- **Composite indexes**: Optimized for common join patterns
- **Covering indexes**: Reduced table lookups
- **Spatial indexes**: GiST indexes for 2D embedding queries
- **Query optimization**: Execution times reduced from seconds to milliseconds

### 4. Data Quality Improvements
- **Country field standardization**: Simplified country codes (Country2)
- **Metadata consistency**: Proper field mapping across components
- **Data validation**: Comprehensive validation at ingestion time

## Key Design Principles

### Functional Programming Approach (React + TypeScript)
- Pure functions for domain logic (TypeScript `logic/` modules)
- Immutable data and small composable utilities (map/filter/reduce)
- Clear separation of concerns: presentational React components vs. logic/services
- DTO mappers validate API contracts; services remain thin and mockable

### Interceptor Pattern
- Request/response processing
- Validation and transformation
- Logging and monitoring
- Extensible architecture

### Database-First Design
- Optimized schema for performance
- Strategic indexing strategy
- Database functions for complex operations
- Proper constraint handling

### Multi-Environment Development
- **Environment-based configuration**: Ports and URLs configured via environment variables
- **Local Development**: Ports 5002/8051 for development without conflicts
- **Remote Development**: Ports 5001/8050 for staging/production
- **Simultaneous Operation**: Both environments can run simultaneously
- **Repo Safety**: Environment files are in .gitignore, won't break synchronization
- **Easy Switching**: Change .env file and restart services

## Current Data Sources

### AiPickle Dataset
- **2,749 papers** successfully ingested
- **Country data**: Simplified country codes (US, UK, etc.)
- **2D embeddings**: Generated for all papers
- **Metadata**: Comprehensive paper information

### arXiv Integration
- **Configurable ingestion**: Support for arXiv API
- **Metadata extraction**: Title, authors, abstracts, categories
- **Category mapping**: Standardized research areas

## Performance Metrics

### API Response Times
- **Before optimization**: 2-5 seconds for complex queries
- **After optimization**: 50-200ms for same queries
- **Index coverage**: 95%+ queries use indexes
- **Query plans**: Optimized execution paths

### Ingestion Performance
- **Batch processing**: 1000+ records per minute
- **Memory efficiency**: Streaming processing for large datasets
- **Error handling**: Graceful failure recovery
- **Validation**: Real-time data quality checks

## Known Issues and Workarounds

### 1. Duplicate Data Handling
- **Issue**: Multiple source names can create duplicates
- **Workaround**: Use consistent source naming and deduplication logic
- **Solution**: Implemented in ingestion pipeline

### 2. Memory Usage During Enrichment
- **Issue**: Large datasets can consume significant memory
- **Workaround**: Batch processing and model caching
- **Solution**: Implemented in enrichment framework

### 3. Database Connection Management
- **Issue**: Connection pooling for high concurrency
- **Workaround**: Proper connection handling in API
- **Solution**: Implemented connection pooling

## Development Workflow

### Local Development
1. **Database setup**: PostgreSQL with pgvector
2. **Environment**: Python virtual environment
3. **Dependencies**: Requirements files in each component
4. **Testing**: Comprehensive test suites

### Deployment Considerations
- **Database migrations**: Schema versioning
- **Configuration management**: Environment-specific configs
- **Monitoring**: Logging and performance metrics
- **Scaling**: Horizontal scaling strategies

## Future Enhancements

### Planned Improvements
1. **Real-time updates**: WebSocket integration
2. **Advanced analytics**: Machine learning insights
3. **Multi-tenant support**: User isolation
4. **API versioning**: Backward compatibility

### Technical Debt
1. **Code documentation**: API documentation updates
2. **Test coverage**: Additional integration tests
3. **Performance monitoring**: Real-time metrics
4. **Error handling**: Comprehensive error recovery

## Key Files and Directories

### Core Application Files
- `doc-ingestor/main_ingestor.py` - Main ingestion pipeline
- `doctrove-api/api.py` - API server (Python)
- `embedding-enrichment/enrichment_framework.py` - Enrichment system
- `docscope/` - Legacy Dash app; React app will live under `frontend/`

### Configuration Files
- `doc-ingestor/source_configs.py` - Data source configurations
- `doctrove-api/config.py` - API configuration
- `docscope/config/settings.py` - Frontend settings

### Database Files
- `doctrove_schema.sql` - Database schema
- `embedding-enrichment/setup_database_functions.sql` - Database functions
- `embedding-enrichment/event_triggers.sql` - Enrichment triggers (must be applied after schema and functions)

### Documentation
- `migration-planning/` - React + TypeScript migration plans and repository strategy
- `docs/DEVELOPMENT/REACT_TS_GUIDE.md` - React + TS patterns and testing strategy
- `embedding-enrichment/DESIGN_PRINCIPLES_QUICK_REFERENCE.md` - Design principles
- `doctrove-api/API_DOCUMENTATION.md` - API documentation (source of truth for endpoints)

## Getting Started

- Development quick start: `docs/DEVELOPMENT/QUICK_START.md`
- Multi-environment setup: `docs/DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md`
- React + TS guide: `docs/DEVELOPMENT/REACT_TS_GUIDE.md`

## Support and Maintenance

### Monitoring
- **API logs**: Request/response logging
- **Database performance**: Query execution monitoring
- **System health**: Resource usage tracking

### Troubleshooting
- **Common issues**: Documented in quick start guide
- **Debug mode**: Comprehensive logging
- **Performance analysis**: Query plan analysis tools

---

*Last updated: [Current Date]*
*Version: 1.0* 