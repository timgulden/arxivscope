# Component Documentation

This section provides links to component-specific documentation that is co-located with the code. This approach keeps detailed implementation docs close to the code while providing a centralized index.

## 🔍 Core Components

### DocScope Frontend
- **Location**: `docscope/`
- **Main App**: `docscope/app.py` - Dash application entry point
- **Components**: `docscope/components/` - Core UI components and orchestration
- **Configuration**: `docscope/config/` - App configuration and settings
- **Documentation**: 
  - `docscope/README.md` - Component overview
  - `docscope/DEVELOPER_QUICK_REFERENCE.md` - Developer guide
  - `docscope/CALLBACK_ARCHITECTURE_DESIGN.md` - Callback system design
  - `docscope/CONFIGURATION.md` - Configuration guide

### DocTrove API Backend
- **Location**: `doctrove-api/`
- **Main API**: `doctrove-api/api.py` - Flask API server
- **Business Logic**: `doctrove-api/business_logic.py` - Core business logic
- **Interceptors**: `doctrove-api/interceptor.py` - API interceptor pattern
- **Documentation**: 
  - `doctrove-api/README.md` - API overview
  - `doctrove-api/API_DOCUMENTATION.md` - API endpoints and usage
  - `doctrove-api/QUICK_START_GUIDE.md` - Quick start guide

### Data Ingestion System
- **Location**: `doc-ingestor/`
- **Main Scripts**: `doc-ingestor/main.py` - Main ingestion orchestration
- **Transformers**: `doc-ingestor/transformers.py` - Data transformation logic
- **Documentation**: 
  - `doc-ingestor/README.md` - Ingestion system overview

### Embedding Enrichment System
- **Location**: `embedding-enrichment/`
- **Main Scripts**: `embedding-enrichment/main.py` - Enrichment orchestration
- **Services**: `embedding-enrichment/embedding_service.py` - Embedding generation
- **Documentation**: 
  - `embedding-enrichment/README.md` - Enrichment system overview
  - `embedding-enrichment/README_ENRICHMENT_SCRIPTS.md` - Script documentation

### OpenAlex Integration
- **Location**: `openalex/`
- **Main Scripts**: `openalex/openalex_ingester.py` - OpenAlex data ingestion
- **Documentation**: 
  - `openalex/README.md` - OpenAlex integration overview

## 🔗 Integration Points

### Data Flow
1. **Ingestion** → `doc-ingestor/` processes raw data
2. **Enrichment** → `embedding-enrichment/` adds embeddings
3. **API** → `doctrove-api/` serves processed data
4. **Frontend** → `docscope/` visualizes data

### Shared Components
- **Database**: PostgreSQL with pgvector extension
- **Configuration**: Environment-based configuration
- **Logging**: Standardized logging across components
- **Testing**: Comprehensive test suites for each component

## 📚 Documentation Standards

### Co-located Documentation
- **README.md**: Component overview and quick start
- **API docs**: For components with external interfaces
- **Design docs**: For complex architectural decisions
- **Configuration**: Environment and setup instructions

### Cross-References
- Component docs link back to centralized documentation
- Centralized docs provide overview and navigation
- Clear mapping between high-level and detailed docs

## 🚀 Getting Started with Components

1. **Start with centralized docs** in the main `docs/` folder
2. **Navigate to component-specific docs** for implementation details
3. **Use cross-references** to understand integration points
4. **Check component READMEs** for component-specific setup

---

*This index is maintained alongside the centralized documentation structure*

