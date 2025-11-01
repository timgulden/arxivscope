# DocScope Platform Repository Architecture Strategy

> **Purpose**: Define the monorepo structure and operational strategy for organizing DocTrove (backend) and DocScope (frontend) services with clear boundaries, shared resources, and complete legacy preservation.

> **Decision Required**: This document requires approval before migration begins, as it affects infrastructure, deployment, and team organization.

---

## **Executive Summary**

**Current Problem**: Single monolithic repository (3.3GB) with mixed backend/frontend concerns, 4,452 test files, and significant technical debt.

**Proposed Solution**: Single monorepo with clear service boundaries:
- **DocTrove Service**: Backend services (data, API, ML processing)  
- **DocScope Service**: Frontend application (React UI, visualization, user experience)
- **Shared Resources**: Active models, data, and utilities used by both services
- **Legacy Archive**: Reference-only archive of current implementation

**Benefits**: Clean development environments, independent deployment, specialized teams, operational continuity.

**Timeline**: Repository setup in Week 1, parallel development thereafter.

---

## **Current State Analysis**

### **Repository Bloat Assessment**

```bash
Current Repository Size: 3.3GB
├── embedding-enrichment/: 2.3GB  # ML models and processing
├── arxivscope/: 596MB            # Virtual environment  
├── data/: 374MB                  # Test and sample data
├── docscope/: 1.3MB              # Frontend code
├── doctrove-api/: 536KB          # Backend API
└── 4,452 test_*.py files         # One-off debugging scripts
```

**Problems with Current Structure:**
- Mixed backend and frontend concerns in single repository
- Massive bloat from development artifacts and debugging scripts
- Unclear ownership boundaries between components
- Difficult to maintain and navigate
- Virtual environments and ML models tracked in git

### **Service Boundary Analysis**

**Current Coupling Issues:**
```python
# Frontend directly imports backend utilities
from doctrove_api.config import API_BASE_URL
from embedding_enrichment.some_utility import helper_function

# Mixed responsibilities in single files
# Frontend logic mixed with backend data processing
# Shared configuration files with conflicting concerns
```

**Target Separation:**
```
DocTrove (Backend)     ←→ HTTP API ←→     DocScope (Frontend)
- Data storage                              - Data visualization
- API endpoints                             - User interactions  
- ML processing                             - Client-side logic
- Database management                       - UI state management
```

---

## **Proposed Repository Architecture**

### **Monorepo Structure with Clear Service Boundaries**

```
docscope-platform/               # Single repository with service separation
├── README.md                    # Platform overview and navigation
├── services/                    # Service implementations
│   ├── doctrove/               # Backend service
│   │   ├── api/                # REST API implementation
│   │   │   ├── src/routes/     # API endpoints (/papers, /search, /clusters)
│   │   │   ├── src/services/   # Business logic (data processing)
│   │   │   ├── src/middleware/ # Request/response processing
│   │   │   └── tests/          # API testing
│   │   ├── ingestion/          # Data ingestion pipeline
│   │   │   ├── src/sources/    # ArXiv, RAND, OpenAlex ingestors
│   │   │   ├── src/processors/ # Data normalization and validation
│   │   │   └── tests/          # Ingestion testing
│   │   ├── enrichment/         # ML processing services
│   │   │   ├── src/embedding/  # Text embedding generation
│   │   │   ├── src/clustering/ # 2D UMAP processing
│   │   │   └── tests/          # ML processing tests
│   │   ├── database/           # Database management
│   │   │   ├── schema/         # SQL schema definitions
│   │   │   ├── migrations/     # Database migrations
│   │   │   └── functions/      # PostgreSQL functions
│   │   └── package.json        # Backend dependencies
│   └── docscope/               # Frontend service
│       ├── logic/              # Frontend business logic
│       │   ├── src/api/        # DocTrove API client
│       │   ├── src/services/   # Data transformation for UI
│       │   ├── src/functions/  # Pure functions for visualization
│       │   └── tests/          # Logic testing
│       ├── contracts/          # API contracts (shared interface)
│       │   ├── src/api/        # DocTrove API interface definitions
│       │   ├── src/types/      # Shared type definitions
│       │   ├── src/mocks/      # Mock DocTrove implementations
│       │   └── tests/          # Contract testing
│       ├── react/              # React UI application
│       │   ├── src/components/ # React components
│       │   ├── src/hooks/      # Custom React hooks
│       │   ├── src/store/      # Redux state management
│       │   ├── src/styles/     # Styling and themes
│       │   └── tests/          # UI testing
│       └── package.json        # Frontend dependencies
├── shared/                      # ACTIVE shared resources (used by new code)
│   ├── models/                 # ML models and trained data
│   │   ├── umap_model.pkl      # UMAP dimensionality reduction model
│   │   ├── clustering_models/  # Other trained models
│   │   └── ModelLoader.ts      # Utilities for loading models
│   ├── data/                   # Datasets and test data
│   │   ├── test-datasets/      # For testing new implementations
│   │   ├── sample-papers/      # Sample data for development
│   │   ├── reference-data/     # Known-good data for validation
│   │   └── DataLoader.ts       # Utilities for loading test data
│   ├── types/                  # Common TypeScript types
│   │   ├── Paper.ts            # Core Paper interface
│   │   ├── Filter.ts           # Filter definitions
│   │   └── ApiTypes.ts         # Shared API types
│   ├── utils/                  # Shared utilities
│   │   ├── validation.ts       # Common validation functions
│   │   ├── transformations.ts  # Data transformation utilities
│   │   └── constants.ts        # Platform constants
│   ├── configs/                # Shared configurations
│   │   ├── database.ts         # Database configuration
│   │   ├── api.ts              # API configuration
│   │   └── environment.ts      # Environment management
│   └── docs/                   # Platform documentation
│       ├── MIGRATION_GUIDE.md  # Complete migration guide
│       ├── API_DOCUMENTATION.md # API specifications
│       └── ARCHITECTURE.md     # Platform architecture
├── legacy/                      # Reference-only archive (read-only)
│   ├── complete-system/        # All 127 current items
│   │   ├── docscope/          # Current Dash implementation
│   │   ├── doctrove-api/      # Current API implementation
│   │   ├── embedding-enrichment/ # Current ML processing
│   │   ├── doc-ingestor/      # Current ingestion pipeline
│   │   └── [all other files]  # Complete current system
│   ├── algorithms/             # Key algorithms for reference
│   │   ├── clustering_service.py # Copy of key algorithm
│   │   └── data_service.py    # Copy of key patterns
│   └── README-LEGACY.md        # How to reference legacy code
├── tools/                       # Development and deployment tools
│   ├── scripts/                # Build, test, and deployment scripts
│   ├── configs/                # Shared tool configurations (ESLint, TypeScript)
│   └── workflows/              # GitHub Actions workflows
├── package.json                 # Root package.json with workspaces
├── .gitignore                   # Smart ignore rules for large files
└── docker-compose.yml           # Development environment setup
```

### **Service Responsibilities**

**DocTrove Service (Backend):**
- Data storage and retrieval
- Paper ingestion from multiple sources
- Embedding generation and management  
- Semantic search algorithms
- API endpoint implementation
- Database schema and optimization
- ML model management using shared/models/
- Performance and scalability

**DocScope Service (Frontend):**
- Data visualization and user interface
- User interaction handling (clicks, filters, search)
- Client-side data transformation (for display purposes only)
- UI state management (filters, selections, view state)
- User experience optimization
- Responsive design and accessibility
- Testing with shared/data/ test datasets

---

## **Key Differences Highlighted**

### **What's ONLY in DocTrove:**
```typescript
// DocTrove contains backend-specific code:
interface DocTroveComponents {
    dataIngestion: "Processing files from ArXiv, RAND, etc.";
    databaseOperations: "PostgreSQL queries, indexing, optimization";
    mlProcessing: "Embedding generation, UMAP clustering";
    apiImplementation: "REST endpoints, authentication, rate limiting";
    infrastructure: "Docker, deployment, monitoring";
}
```

### **What's ONLY in DocScope:**
```typescript
// DocScope contains frontend-specific code:
interface DocScopeComponents {
    visualization: "React components for charts and graphs";
    userInteraction: "Click handlers, form inputs, navigation";
    clientLogic: "Data transformation for display purposes";
    stateManagement: "Redux for UI state, filters, selections";
    styling: "CSS, themes, responsive design";
}
```

### **What's Shared (via API Contract):**
```typescript
// Only data types and API interfaces are shared:
interface SharedContracts {
    paperTypes: "Paper, Filter, SearchQuery data structures";
    apiEndpoints: "REST API interface definitions";
    responseFormats: "Standardized response structures";
}
```

---

## **Operational Strategy**

### **Current System Preservation**
```bash
# UNCHANGED: Original system continues operating
/opt/arxivscope/                 # Current location - UNTOUCHED during development
├── Current Dash frontend        # Continues serving users
├── Current API backend          # Continues processing requests
└── All services                 # Continue running normally

# Access: http://localhost:8050 (users continue working)
```

### **New Development (Monorepo)**
```bash
# NEW: Integrated platform development
/opt/docscope-platform/          # Single monorepo with service boundaries
├── services/doctrove/          # Backend service (port 5001)
├── services/docscope/          # Frontend service (port 8050)
├── shared/                     # Active resources (models, data, types)
└── legacy/                     # Complete archive for reference

# Development access:
# Integrated platform: http://localhost:8050 (new) + http://localhost:5001 (new API)
# Original system: http://localhost:8051 (fallback, different port)
```

### **Integration Strategy**
```bash
# Phase 1: Develop services using shared resources
# New DocTrove uses shared/models/umap_model.pkl
# New DocScope uses shared/data/test-datasets/

# Phase 2: Integrated testing and optimization
# Both services developed together with coordinated changes
# Single command testing across entire platform

# Phase 3: Replace original system
# New platform takes over production ports
# Original system archived but available for rollback
```

---

## **Implementation Plan**

### **Week 1: Monorepo Setup with Smart Resource Management**

**Day 1: Create Monorepo Structure**
```bash
#!/bin/bash
# create-monorepo-platform.sh

echo "🏗️ Creating DocScope Platform monorepo..."

# =============================================================================
# STEP 1: CREATE MONOREPO STRUCTURE
# =============================================================================

mkdir -p /opt/docscope-platform
cd /opt/docscope-platform
git init
git remote add origin https://github.com/your-org/docscope-platform.git

# Create service structure
mkdir -p services/{doctrove,docscope}
mkdir -p services/doctrove/{api,ingestion,enrichment,database}
mkdir -p services/docscope/{logic,contracts,react}

# Create shared resources structure (ACTIVE, not legacy)
mkdir -p shared/{models,data,types,utils,configs,docs}

# Create legacy archive structure
mkdir -p legacy/{complete-system,algorithms}

# Create tools structure
mkdir -p tools/{scripts,configs,workflows}

echo "✅ Monorepo structure created"

# =============================================================================
# STEP 2: MOVE LARGE FILES TO SHARED RESOURCES
# =============================================================================

cd /opt/arxivscope

echo "🤖 Moving ML models to shared/models/ (active resources)..."
# These are ACTIVE resources, not legacy - new code will use them
find embedding-enrichment/ -name "*.pkl" -size +10M -exec cp {} /opt/docscope-platform/shared/models/ \; 2>/dev/null || true
find . -name "umap_model*" -exec cp {} /opt/docscope-platform/shared/models/ \; 2>/dev/null || true

echo "📊 Moving data files to shared/data/ (active resources)..."
# Test data and samples - new code will use these
cp -r data/ /opt/docscope-platform/shared/data/test-datasets/ 2>/dev/null || true
cp -r Documents/ /opt/docscope-platform/shared/data/documents/ 2>/dev/null || true

echo "📝 Moving configurations to shared/configs/ (active resources)..."
# Configurations that new services will use
cp docscope/config/settings.py /opt/docscope-platform/shared/configs/
cp env.*.example /opt/docscope-platform/shared/configs/

# =============================================================================
# STEP 3: ARCHIVE COMPLETE LEGACY SYSTEM
# =============================================================================

echo "📚 Creating complete legacy archive..."
rsync -av \
    --exclude='.git/' \
    --exclude='DOCSCOPE_REACT_MIGRATION_GUIDE.md' \
    --exclude='REPOSITORY_ARCHITECTURE_STRATEGY.md' \
    ./ /opt/docscope-platform/legacy/complete-system/

# Create quick-access symlinks to key algorithms
ln -s complete-system/docscope/components/clustering_service.py /opt/docscope-platform/legacy/algorithms/
ln -s complete-system/docscope/components/data_service.py /opt/docscope-platform/legacy/algorithms/
ln -s complete-system/doctrove-api/ /opt/docscope-platform/legacy/api-reference

echo "✅ Complete legacy system archived"

# =============================================================================
# STEP 4: SET UP MONOREPO TOOLING
# =============================================================================

cd /opt/docscope-platform

# Root package.json with workspaces
cat > package.json << 'EOF'
{
  "name": "docscope-platform",
  "version": "2.0.0",
  "description": "Document visualization and processing platform",
  "workspaces": [
    "services/doctrove/*",
    "services/docscope/*",
    "shared/*"
  ],
  "scripts": {
    "dev": "concurrently \"npm run dev:doctrove\" \"npm run dev:docscope\"",
    "dev:doctrove": "cd services/doctrove && npm run dev",
    "dev:docscope": "cd services/docscope/react && npm run dev",
    "dev:debug": "concurrently --names \"API,UI\" \"npm run dev:doctrove\" \"npm run dev:docscope\"",
    "test:all": "npm run test --workspaces",
    "build:all": "npm run build --workspaces",
    "lint:all": "npm run lint --workspaces",
    "deploy:platform": "npm run deploy:doctrove && npm run deploy:docscope"
  },
  "devDependencies": {
    "concurrently": "^8.0.0",
    "lerna": "^7.0.0"
  }
}
EOF

# Smart .gitignore for monorepo
cat > .gitignore << 'EOF'
# Node modules
node_modules/
*/node_modules/

# Large shared files (not tracked)
shared/models/*.pkl
shared/models/*.joblib
shared/data/large-datasets/

# Small shared files (tracked)
!shared/types/
!shared/utils/
!shared/configs/

# Legacy system (code tracked, large files excluded)
legacy/complete-system/
!legacy/complete-system/**/*.pkl
!legacy/complete-system/**/*.log
!legacy/complete-system/arxivscope/
!legacy/complete-system/.local/

# Environment files
.env*
*.env

# Logs
*.log
logs/

# OS files
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
EOF

echo "✅ Monorepo tooling configured"
```

**Day 2-3: Service Setup**
```bash
# Set up DocTrove service
cd /opt/docscope-platform/services/doctrove
npm init -y
npm install typescript @types/node express fastify

# Set up DocScope service  
cd /opt/docscope-platform/services/docscope/react
npx create-react-app . --template typescript
npm install @reduxjs/toolkit react-redux

# Set up shared utilities
cd /opt/docscope-platform/shared/types
npm init -y
npm install typescript

# Install all dependencies
cd /opt/docscope-platform
npm install  # Installs all workspace dependencies

echo "✅ All services configured in monorepo"
```

**Verification: Integrated Development Environment**
```bash
# Single command starts entire platform:
cd /opt/docscope-platform
npm run dev:debug

# Output shows both services:
# [API] DocTrove API starting on port 5001...
# [UI]  DocScope UI starting on port 8050...
# [API] Using models from shared/models/umap_model.pkl
# [UI]  Connected to DocTrove API at localhost:5001

# Integrated debugging:
# API call logs appear together with UI logs
# Easy to trace requests from frontend through backend
# Single git history shows coordinated changes
```

### **Development Workflow**
```bash
# Your typical day with monorepo:

# 1. Start entire platform for integrated development
cd /opt/docscope-platform
npm run dev:debug
# Starts both DocTrove API and DocScope UI with correlated logging

# 2. Develop backend service (your domain)
cd services/doctrove/api
# Edit API code, immediately see impact on frontend logs

# 3. Develop frontend logic (collaboration with Mo)
cd services/docscope/logic  
# Edit business logic, test against real backend

# 4. Use active shared resources
python load_model.py ../../shared/models/umap_model.pkl
node test-data.js ../../shared/data/test-datasets/sample.json

# 5. Reference legacy patterns when needed
grep -r "clustering" legacy/algorithms/
cat legacy/complete-system/docscope/components/clustering_service.py

# 6. Make coordinated changes across services
git add services/doctrove/api/papers.ts services/docscope/react/PaperList.tsx
git commit -m "feat: add paper filtering to API and UI"
```

---

## **Smart File Management Strategy**

### **Problem Solved: Massive File Duplication**

**Original Repository Size**: 8.7GB total
```bash
Current Repository Analysis:
├── Code and documentation: ~100MB
├── Virtual environment (arxivscope/): 596MB  
├── ML models (*.pkl files): 100s of MB
├── Data files (data/, Documents/): 374MB+
├── Database backups: Potentially GB-sized
├── Log files and caches: 100s of MB
└── 4,452 test_*.py debugging scripts
```

**Without Smart Management** (naive approach):
- Complete duplication in monorepo: 8.7GB × 2 (legacy + new) = 17.4GB
- **Total**: 17.4GB (2x duplication of everything!)

**With Smart Management** (monorepo approach):
- Monorepo with shared resources: ~100MB (code + small files)
- Shared large files: ~3GB (models, data, environments - exist once)
- Legacy archive: ~100MB (code only, large files excluded)
- **Total**: ~3.2GB (**63% reduction, zero duplication**)

### **Shared Resources Architecture (Active vs Legacy)**

```
/opt/docscope-platform/
├── shared/                      # ACTIVE resources (used by new services)
│   ├── models/                 # ML models and trained data
│   │   ├── umap_model.pkl      # UMAP model (used by new DocTrove clustering)
│   │   ├── *.pkl               # Other trained models
│   │   ├── *.joblib            # Scikit-learn models
│   │   └── ModelLoader.ts      # TypeScript utilities for loading models
│   ├── data/                   # Test datasets and samples
│   │   ├── test-datasets/      # For testing new implementations
│   │   ├── sample-papers/      # Sample data for development
│   │   ├── reference-data/     # Known-good data for validation
│   │   └── DataLoader.ts       # TypeScript utilities for loading data
│   ├── types/                  # Common TypeScript types (tracked in git)
│   │   ├── Paper.ts            # Core Paper interface
│   │   ├── Filter.ts           # Filter definitions
│   │   └── ApiTypes.ts         # Shared API types
│   └── configs/                # Active configurations (tracked in git)
│       ├── database.ts         # Database configuration
│       ├── api.ts              # API configuration
│       └── environment.ts      # Environment management
└── legacy/                      # REFERENCE-ONLY archive (read-only)
    ├── complete-system/        # All 127 current items (code tracked, large files ignored)
    │   ├── docscope/          # Current Dash implementation
    │   ├── doctrove-api/      # Current API implementation
    │   ├── embedding-enrichment/ # Current ML processing
    │   └── [all other files]  # Complete current system
    └── algorithms/             # Quick-access symlinks to key algorithms
        ├── clustering_service.py → complete-system/docscope/components/clustering_service.py
        └── data_service.py → complete-system/docscope/components/data_service.py
```

### **Resource Usage Patterns**

```typescript
// NEW SERVICES use shared/ resources directly:

// DocTrove service uses shared models:
// services/doctrove/src/clustering/ClusterService.ts
import { loadUmapModel } from '../../../shared/models/ModelLoader';

export class ClusterService {
    private umapModel = loadUmapModel('shared/models/umap_model.pkl');
    
    async generateClusters(papers: Paper[]): Promise<ClusterResult> {
        // Use existing trained UMAP model in new service
        const embeddings = await this.umapModel.transform(papers);
        return this.performClustering(embeddings);
    }
}

// DocScope service uses shared test data:
// services/docscope/react/src/components/__tests__/ScatterPlot.test.tsx
import { loadTestPapers } from '../../../../shared/data/DataLoader';

describe('ScatterPlot Component', () => {
    test('renders with realistic data', () => {
        const testPapers = loadTestPapers('shared/data/test-datasets/sample-1000.json');
        render(<ScatterPlot papers={testPapers} />);
        expect(screen.getByTestId('scatter-plot')).toBeInTheDocument();
    });
});

// LEGACY CODE used for reference only:
// Study legacy/algorithms/clustering_service.py
// Understand the approach and parameters
// Reimplement in services/doctrove/src/clustering/ using new patterns
```

### **Development Benefits**

**Integrated Development Experience:**
```bash
# Single repository, integrated workflow:
git clone docscope-platform.git    # ~100MB download (code + small shared files)
cd docscope-platform
npm run dev:debug                   # Starts entire platform
git status                          # See changes across both services
git log --oneline services/         # History of coordinated changes
```

**Seamless Resource Access:**
```bash
# Direct access to shared resources from new code:
cd /opt/docscope-platform/services/doctrove
python load_model.py ../../shared/models/umap_model.pkl  # Direct path, no symlinks

cd /opt/docscope-platform/services/docscope/react  
node test-with-data.js ../../../shared/data/test-datasets/sample.json  # Direct path
```

**Integrated Debugging:**
```bash
# Correlated logging across services:
npm run dev:debug
# [API] 08:30:15 Received request: GET /papers?source=openalex
# [UI]  08:30:15 Making API call: GET /papers?source=openalex  
# [API] 08:30:16 Query executed: 1,234 papers found
# [UI]  08:30:16 Received response: 1,234 papers, rendering...

# Single git history for coordinated changes:
git log --oneline --grep="clustering"
# Shows both API and UI changes for clustering features together
```

**Protected Large Files:**
```bash
# .gitignore prevents large files from entering git:
git add .                       # Only adds code and small config files
git status                      # Shows "ignored" for *.pkl, large datasets
# Impossible to accidentally commit 596MB virtual environment!
# But new code can still use shared/models/umap_model.pkl directly
```

---

## **Benefits Summary**

### **✅ Operational Continuity:**
- Current system remains fully operational
- Zero user disruption during development
- Safe rollback capability throughout migration
- Gradual transition when new system is ready

### **✅ Clean Development with Integrated Workflow:**
- Single repository (~100MB) with clear service boundaries
- Integrated debugging and development experience
- Shared tooling and configurations across services
- Modern monorepo best practices with workspace management
- Fast git operations with coordinated change history

### **✅ Complete Preservation with Smart Resource Management:**
- **All 127 top-level items** archived in legacy/complete-system/
- **All 4,452 test files** preserved for reference
- **All documentation and configuration** archived
- **Active shared resources** (models, data) available to new services
- **Legacy code** available for reference but separate from active development
- **No accidental commits** of large files (protected by .gitignore)

### **✅ Superior Debugging and Coordination:**
- **Integrated logging**: See API and UI logs together in single terminal
- **Atomic changes**: Single commit updates both frontend and backend
- **Coordinated testing**: Test entire platform with single command
- **Shared types**: No version mismatches between services
- **Easy tracing**: Follow API calls from UI through backend in same codebase

### **✅ Future Flexibility with Current Efficiency:**
- **Service boundaries maintained**: Clear separation of concerns
- **DocTrove independence**: Can be extracted to separate repo later if needed
- **Multiple frontend potential**: Other UIs can be added to services/ directory
- **Technology evolution**: Each service can evolve independently within monorepo
- **Easy extraction**: Git subtree can create separate repos when/if needed
- **Shared resource evolution**: Models and data can be upgraded centrally

---

*This repository strategy enables the migration while ensuring zero operational disruption and maximum development efficiency.*

---

## **📋 Related Documentation**

**After approving this repository strategy, see:**
- **[DOCSCOPE_REACT_MIGRATION_GUIDE.md](DOCSCOPE_REACT_MIGRATION_GUIDE.md)** - Complete technical migration guide with implementation details

**For current system reference:**
- **[CONTEXT_SUMMARY.md](CONTEXT_SUMMARY.md)** - Current system overview and status
- **[docs/ARCHITECTURE/](docs/ARCHITECTURE/)** - Current architecture documentation

---

*Document created: September 18, 2025*
*Version: 1.0*
*Status: Awaiting approval for implementation*
