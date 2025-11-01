# DocScope/DocTrove Context Summary

## 📚 Documentation

**Documentation is now organized in the `docs/` folder for easy navigation. Start with [docs/README.md](docs/README.md) for complete navigation.**

---

## Recent Setup & Workflow Updates (2024)

**This section highlights the latest setup, ingestion, and workflow conventions for initializing a new session.**

- **Current Environment:**
  - **Location**: Running on personal laptop (macOS) on home network
  - **Previous**: System migrated from AWS server to local laptop (October 2025)
  - **Database**: PostgreSQL 14 running on internal drive (58GB database)
  - **Storage**: Internal drive (database + models), external drive used only for backups
  - **Environment File**: `.env.local` contains local configuration (in .gitignore)
  - **See**: `MULTI_ENVIRONMENT_SETUP.md` for multi-environment setup (if needed in future)
- **Unified Environment Setup:**
  - Use `scripts/setup_environment.sh` to auto-detect platform, install dependencies, set up Python environment, and create necessary directories.
- **Automated Database Setup:**
  - Run `bash "Design documents/setup_postgres_pgvector.sh"` to install PostgreSQL 15, pgvector, create the `doctrove` database, and apply schema.
- **Service Startup (Unified):**
  - Use `./services.sh start --enrichment` to start React + API (+ enrichment) in screen sessions.
  - Or run individually: `./docscope.sh start` (frontend), `./doctrove.sh start --enrichment` (backend).
- **Data Ingestion:**
  - **Pickle:** `python main_ingestor.py --file-path /path/to/data.pkl --source arxivscope`
  - **MARC:** `python main_ingestor.py --file-path ~/Documents/doctrove-data/marc-files/randpubs.mrc --source marc`
  - Large MARC files should be stored in `~/Documents/doctrove-data/marc-files/` (e.g., `randpubs.mrc`, `external_authors.mrc`).
- **Service Status Check:**
  - Use a script like `check_services.sh` (see chat history) to check API, enrichment, Dash app, and Docker status at once.
- **Key Docs:**
  - `DATABASE_SETUP_GUIDE.md`, `MARC_DATA_PROCESSING.md`, `QUICK_STARTUP.md`, `STARTUP_GUIDE.md`
- **Current Configuration (Local Laptop):**
  - **API**: Port 5001 (standard Flask API port)
  - **Frontend**: Port 3000 (React standard dev port)
  - **PostgreSQL**: Port 5432 (standard PostgreSQL port)
  - **Database**: Internal drive (`/opt/homebrew/var/postgresql@14`), 58GB
  - **Models**: Internal drive (`models/umap_model.pkl`), 1.1GB
  - **Configuration**: `.env.local` file (in .gitignore, accessible via `cat .env.local` in Cursor)
  - **Database Credentials**: Trust authentication (local setup, no password needed)

---

## Quick Start for New Conversations

**IMPORTANT**: This system is currently running on a **personal laptop (macOS) on a home network**, having been migrated from an AWS server to local laptop in October 2025. All references to "server" or "remote" environments are historical - the system now operates entirely locally.

This document provides a concise overview of the current state of the DocScope/DocTrove system for new conversations.

**📖 For comprehensive details, see:**
- **[docs/README.md](docs/README.md)** - Complete documentation index and navigation
- **[QUICK_START.md](QUICK_START.md)** - Detailed setup instructions, workflows, and troubleshooting
- **[MULTI_ENVIRONMENT_SETUP.md](MULTI_ENVIRONMENT_SETUP.md)** - Multi-environment development setup and port management

## System Overview

**DocScope/DocTrove** is a comprehensive document analysis and visualization system with:
- **Document Ingestion Pipeline** (doc-ingestor/)
- **Enrichment Framework** (embedding-enrichment/)
- **API Server** (doctrove-api/)
- **Frontend Application** (docscope/) - Legacy Dash app (port 8050, frozen)
- **React Migration Workspace** (docscope-platform/) - React + TypeScript frontend (port 3000, configured in `.env.local`)

## Frontend Architecture

### Two Frontends, One Shared Backend

The system currently has **two frontend applications** that share a **single backend API**:

#### 1. **Legacy Dash Frontend** (FROZEN - No New Development)
- **Location**: `docscope/` directory
- **Technology**: Python Dash
- **Port**: 8050 (or 8051 for local development)
- **Status**: **Frozen for new development** - bug fixes only
- **Purpose**: Production system currently in use
- **Start**: Deprecated (use React). `start_docscope.sh` is legacy.
- **Stop**: Deprecated (legacy).

#### 2. **React Frontend** (REBUILD IN PROGRESS)
- **Location**: `docscope-platform/services/docscope/react/`
- **Technology**: React + TypeScript + Vite
- **Port**: 3000 (configured in `.env.local` as `NEW_UI_PORT`)
- **Status**: **Rebuild in progress** - React frontend code was lost (submodule not bundled), currently rebuilding
- **Purpose**: Modern replacement for Dash frontend
- **Start**: Not yet functional (rebuild in progress)
- **Rebuild Documentation**: 
  - **Rebuild Plan**: `docscope-platform/services/docscope/react/REBUILD_PLAN.md`
  - **State Management**: `docscope-platform/services/docscope/react/STATE_MANAGEMENT_STRATEGY.md`
- **Reference**: Legacy Dash frontend in `docscope/` provides functionality reference
- **Note**: Following functional programming principles and Interceptor pattern (see `REBUILD_PLAN.md`)

#### 3. **Shared Backend API** (ACTIVE - Used by Both Frontends)
- **Location**: `doctrove-api/` directory
- **Technology**: Python Flask
- **Port**: 5001 (configured in `.env.local` as `DOCTROVE_API_PORT`)
- **Status**: **Actively maintained** - serves both frontends
- **Purpose**: All data access, SQL generation, paper queries
- **Start (Recommended)**: `./doctrove.sh start` (screen session `doctrove_api`)
- **Start (Manual)**: `cd doctrove-api && source ../venv/bin/activate && python api.py`
- **Stop**: `./STOP_SERVICES.sh` or `pkill -f "python api.py"`
- **View Logs**: `screen -r doctrove_api`
- **Health Check**: `curl http://localhost:5001/api/health`

### Service Startup Procedures

#### ⭐ RECOMMENDED: Quick Start with Screen (Survives Terminal Restarts)
```bash
# Start both API and React (with enrichment) in screen sessions
./services.sh start --enrichment

# Access screen sessions:
screen -r doctrove_api    # View API logs
screen -r docscope_react  # View React logs
# Press Ctrl+A then D to detach (keeps running)

# Stop all services:
./services.sh stop --enrichment
```

#### Alternative: Manual Startup (For Quick Testing)
```bash
# Start backend API (runs in foreground - will die if terminal closes)
cd doctrove-api
source ../venv/bin/activate
python api.py

# Start React frontend (runs in foreground - will die if terminal closes)
cd docscope-platform/services/docscope/react
npm run dev              # Direct npm command (foreground)

# OR start legacy Dash frontend (if needed)
cd docscope
source ../venv/bin/activate
python app.py
```

#### ⭐ NEW: Smart DocTrove Backend Service Manager (Recommended)
```bash
# Start backend services (API only by default)
./doctrove.sh start

# Start backend services with enrichment workers
./doctrove.sh start --enrichment

# Restart services (kills and restarts)
./doctrove.sh restart
./doctrove.sh restart --enrichment

# Stop backend services
./doctrove.sh stop              # Stops API only
./doctrove.sh stop --enrichment # Stops API + enrichment workers
./doctrove.sh stop --all        # Same as --enrichment

# Features:
# - Smart detection: only starts services not already running
# - Graceful restart: --restart flag kills and restarts
# - Configurable: --enrichment flag controls enrichment workers
# - Health checks: validates services started correctly
# - Background services: runs in screen sessions
```

#### Verify Services Are Running
```bash
# Check API (should return "healthy")
curl -s http://localhost:5001/api/health | jq -r '.status'

# Check React app (should show LISTEN on port 3000)
lsof -i :3000 | grep LISTEN

# Check Dash app (should show LISTEN on port 8050)
lsof -i :8050 | grep LISTEN

# List all screen sessions
screen -ls
```

#### Accessing Logs
```bash
# View logs in real-time (screen sessions)
screen -r doctrove_api     # API logs
screen -r docscope_react   # React logs
# Detach: Ctrl+A then D

# View logs from files (if configured)
tail -f doctrove-api/api.log
tail -f docscope-platform/services/docscope/react/react.log
```

### Managing Background Enrichment Processes

**All enrichment processes now run as trigger-based queue workers!**

#### Check What's Running
```bash
screen -ls                           # List all screen sessions
./doctrove.sh start --enrichment     # Start enrichment workers
./doctrove.sh stop --enrichment      # Stop enrichment workers
```

#### Active Enrichment Workers (Trigger-Based)

**1. OpenAlex Details Worker** (NEW!)
```bash
# Automatically started by START_SERVICES.sh
screen -r openalex_details           # View worker logs
# Extracts: journal names, citations, topics, institutions from raw JSON
# Status: ~50 papers/sec, 16.8M papers queued
# Database trigger: Auto-queues new OpenAlex papers on insert
```

**2. 2D Embedding Worker**
```bash
screen -r embedding_2d              # View worker logs
# Generates: 2D UMAP coordinates from 1D embeddings
# Status: Usually idle (queue empty)
# Database trigger: Auto-queues papers when 1D embedding is added
```

**3. 1D Embedding Worker** (started by startup.sh --with-enrichment)
```bash
# Generates: 1D embeddings from title/abstract
# Status: Started manually when needed
# Database trigger: Auto-queues papers without embeddings
```

#### Queue-Based Architecture Benefits
- ✅ **No expensive COUNT queries** - just polls queue table
- ✅ **Minimal performance impact** - React app still loads in ~3s
- ✅ **Automatic processing** - new papers queued by database triggers
- ✅ **Resumable** - workers pick up where they left off
- ✅ **Monitorable** - check queue progress anytime

#### Monitor Queue Progress
```bash
# Check all enrichment queues
cd doctrove-api && source ../venv/bin/activate && python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
cur.execute(\"\"\"
    SELECT enrichment_type, 
           COUNT(*) FILTER (WHERE status = 'pending') as pending,
           COUNT(*) FILTER (WHERE status = 'completed') as completed
    FROM enrichment_queue
    GROUP BY enrichment_type
\"\"\")
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]:,} pending, {row[2]:,} completed')
"
```

#### Performance Impact
- **Queue-based workers**: Minimal impact on frontend (~3s load time)
- **Old batch scripts**: Heavy impact (30s+ load time with COUNT queries)
- **Best Practice**: Use queue workers (trigger-based) instead of batch scripts

### Important Notes
- **Backend changes** affect both frontends (they share the same API)
- **Frontend-specific changes** only affect the respective frontend
- **React development** should use the design patterns from the Dash app (functional programming, separation of concerns)
- **Port conflicts**: All ports configured via `.env.local` file (see current configuration above)
- **The React app** uses Vite dev server, not create-react-app
- **Screen sessions are RECOMMENDED** for development:
  - Services survive terminal/Cursor restarts
  - Can reattach to view logs anytime
  - Easy to manage with `./START_SERVICES.sh` and `./STOP_SERVICES.sh`
  - Better than running in Cursor terminals (which die when Cursor restarts)
- **Pause enrichment during development** to maintain fast response times

## Current State

### Environment (Updated October 2025)
- **Location**: Personal laptop (macOS) on home network
- **Migration**: Successfully migrated from AWS server to local laptop (October 2025)
- **Database**: PostgreSQL 14 running on internal drive (58GB, ~2.9M papers)
- **Storage**: Internal drive for operations, external drive used only for backups
- **PostgreSQL**: Managed via Homebrew, data directory: `/opt/homebrew/var/postgresql@14`
- **Python Environment**: Virtual environment at `venv/` in project root
- **No External Dependencies**: System fully operational without external drive mounted

### Data (Updated October 2025)
- **~2.9M total papers** in database (focused dataset):
  - **2.8M arXiv papers** (1986-2025 complete, cutting-edge research)
  - **71.6K RAND publications** (randpub - 1945-2025)
  - **10.2K RAND external publications** (extpub - 1952-2025)
- **Database Streamlining (Oct 10, 2025):**
  - Removed 17.8M OpenAlex papers (incomplete sample)
  - Removed 2,749 aipickle papers (redundant with arXiv)
  - **Result**: 86% reduction in records, 95.5% reduction in storage (358GB → 16GB)
  - Refocused on cutting-edge arXiv research + RAND analysis
- **Embedding Status (Updated January 2025):**
  - **2.92M papers** with vector embeddings (1536-d, **100% complete** ✅)
  - **2D projections:** All papers have 2D UMAP embeddings (100% complete ✅)
  - **Zero papers** pending embedding generation
- **Event-driven enrichment** system running automatically (mostly idle - work complete)

### Performance
- **API response times**: 50-200ms (down from 2-5 seconds)
- **Database indexes**: Strategic indexing with 95%+ coverage
- **Query optimization**: Composite and spatial indexes implemented
- **Batch embedding**: 500 texts per API call (vs individual calls)

### Recent Major Work
- **2D Embedding Reset**: Successfully reset and regenerated all 2D embeddings using `reset_umap_environment.py`
- **True Batch Processing**: Implemented efficient batch API calls for embedding generation
- **Memory Optimization**: Fixed memory allocation errors with proper batch sizing
- **Automated Enrichment**: Event-driven system with database triggers
- **UMAP Model Retraining**: Fresh model trained on current dataset of ~51,000 papers
- **Local Environment Setup**: Port configuration via `.env.local` file for local laptop development
- **Progress Monitoring**: Real-time progress tracking for large-scale vector embedding generation using event listener logs

### Recent Improvements (October 2025)

#### arXiv Bulk Metadata Ingestion (NEW!)
- **Successfully ingested 2.8M arXiv papers** (1986-2025):
  - Kaggle dataset: Cornell University arXiv metadata snapshot
  - JSON Lines format with batch processing (5000 papers/batch)
  - Optimized duplicate handling with `ON CONFLICT DO NOTHING`
  - **Performance:** 897 papers/second (~52 minutes for full ingestion)
- **Data coverage:**
  - Full arXiv history from 1986 to October 2025
  - Strong 2024-2025 coverage (addressing OpenAlex gap)
  - Complements OpenAlex historical data (2010-2017)
- **Automatic enrichment:**
  - Vector embeddings: 44.6% complete (1.26M/2.8M papers)
  - 2D projections: Nearly caught up with embeddings
  - Trigger-based queuing system
- **Ingestion script:** `doc-ingestor/arxiv_bulk_ingester.py`
  - Supports year/date filtering, category filtering
  - Detailed progress tracking and error handling
  - Can be re-run for incremental updates
- **Documentation:** See `ARXIV_INGESTION_PLAN.md`

#### Smart Service Management Scripts (NEW!)
- **`start_doctrove.sh`**: Intelligent backend service startup
  - Detects running services, only starts what's needed
  - `--restart` flag for clean restarts
  - `--enrichment` flag for enrichment workers
  - Health checks and validation
  - Runs in screen sessions (survives terminal restarts)
- **`stop_doctrove.sh`**: Clean service shutdown
  - Gracefully stops API and/or enrichment workers
  - `--enrichment` or `--all` flags for full shutdown
  - Cleans up orphan processes
- **Benefits:**
  - Consistent service management
  - No duplicate processes
  - Easy monitoring with screen sessions
  - Professional development workflow

#### Custom Universe Filter Enhancements (React App)
- **Removed restrictive SQL validation from backend** - now accepts any valid WHERE clause (IS NULL, BETWEEN, etc.)
- **Added shared `testQuery()` validation logic** - DRY principle, validates queries by running them
- **Apply Filter now tests query before applying** - prevents broken SQL from being applied
- **Zero-result query detection** - warns if query returns no papers (likely an error)
- **Enhanced LLM prompt** with NULL checks, negation, ranges, and other common SQL patterns
- **Improved messaging** - professional tone, removed misleading paper counts
- **Full schema viewer** - integrated `react-markdown` to display formatted DATABASE_SCHEMA.md in-app
- **Better error feedback** - shows generated SQL when validation fails for debugging

#### OpenAlex Details Enrichment System (Trigger-Based)
- **Converted to trigger-based architecture**:
  - Database trigger automatically queues new OpenAlex papers for enrichment
  - Queue workers process papers in background (similar to 1D/2D embeddings)
  - Extracts 60+ fields from raw OpenAlex JSON (journals, citations, topics, institutions, etc.)
- **Performance optimizations**:
  - **CRITICAL FIX**: Removed expensive COUNT(*) queries (16.5s each!) that caused 10x slowdown
  - Optimized to use LEFT JOIN instead of NOT EXISTS (1.6s vs timeout)
  - Further optimized to use UUID range tracking with ORDER BY for reliable progress
  - Single table SELECT with ON CONFLICT for idempotent inserts
  - **Result**: ~500-600 papers/sec per worker (4 workers = ~2,304 papers/sec)
- **Parallel backlog processing**:
  - Created dedicated backlog processor for processing existing 17.7M papers
  - Supports multiple parallel workers with independent state files
  - ETA: ~2 hours for full backlog with 4 workers
  - Minimal frontend impact (3-4s load time with processing running)
- **See**: `ENRICHMENT_PROCESSING_GUIDE.md` for complete documentation

#### Service Management with Screen Sessions
- **Created `START_SERVICES.sh` and `STOP_SERVICES.sh`** for reliable service management
- **Services run in screen sessions** that survive Cursor/terminal restarts
- **Easy log access** with `screen -r <session_name>`
- **Includes enrichment workers**: API, React, vector embeddings, 2D embeddings, OpenAlex details
- **Best Practice**: Use screen sessions for all background services

#### Code Quality & Architecture
- **Functional Programming Refactoring**: Replaced `for` loops with `map`, `filter`, and `reduce` patterns
- **Large-Scale Ingestion**: Enhanced system to handle up to 5 million papers with streaming processing
- **Testability**: Pure functions enable easier unit testing and better code composition

## Key Files to Reference

**💡 NEW: Documentation is now organized in the `docs/` folder for easy navigation!**

### Core Applications
- `doc-ingestor/main_ingestor.py` - Main ingestion pipeline (legacy)
- `doc-ingestor/arxiv_bulk_ingester.py` - arXiv bulk metadata ingester (NEW!)
- `doc-ingestor/arxiv_ingester.py` - arXiv API ingester for updates
- `doctrove-api/api.py` - API server (runs on port 5001, not 5000)
- `embedding-enrichment/embedding_service.py` - True batch embedding service
- `embedding-enrichment/reset_umap_environment.py` - UMAP environment management
- `docscope.py` - Main DocScope frontend (not app.py)

### Progress Monitoring
- `embedding-enrichment/monitor_event_listener.py` - Real-time progress monitoring for 1D embeddings
- `embedding-enrichment/analyze_real_token_counts.py` - Token count analysis for cost estimation
- `embedding-enrichment/event_listener_functional.py` - Database-driven 1D embedding service
- `embedding-enrichment/functional_2d_processor.py` - 2D embedding generation service

### Service Management
- `doctrove.sh` - Unified backend manager (API + enrichment workers)
- `docscope.sh` - Unified frontend (React) manager
- `services.sh` - Master orchestrator (frontend + backend)
- `startup.sh` - Legacy master startup script (deprecated)
- `stop_services.sh` - Legacy service shutdown (deprecated)
- `start_docscope.sh` - Legacy Dash startup (deprecated)
- `scripts/start_embedding_enrichment_only.sh` - Vector embedding worker only

### Configuration
- `doc-ingestor/source_configs.py` - Data source configurations
- `doctrove-api/config.py` - API configuration
- `docscope/config/settings.py` - Frontend settings
- `env.local.example` / `env.remote.example` - Environment configuration templates

### Documentation

- **[docs/README.md](docs/README.md)** - **Main documentation index** - Start here for navigation
- **[QUICK_STARTUP.md](QUICK_STARTUP.md)** - Fast startup commands (start here!)
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Comprehensive system overview and architecture
- **[STARTUP_GUIDE.md](STARTUP_GUIDE.md)** - Complete startup procedure and troubleshooting
- **[QUICK_START.md](QUICK_START.md)** - Setup and usage instructions
- **[MULTI_ENVIRONMENT_SETUP.md](MULTI_ENVIRONMENT_SETUP.md)** - Multi-environment development setup
- **[ARXIV_INGESTION_PLAN.md](ARXIV_INGESTION_PLAN.md)** - arXiv data ingestion guide (NEW!)
- **[ENRICHMENT_PROCESSING_GUIDE.md](ENRICHMENT_PROCESSING_GUIDE.md)** - Enrichment system documentation (NEW!)
- **[FUNCTIONAL_PROGRAMMING_GUIDE.md](FUNCTIONAL_PROGRAMMING_GUIDE.md)** - Functional programming principles and refactoring guide
- **[FUNCTIONAL_TESTING_GUIDE.md](FUNCTIONAL_TESTING_GUIDE.md)** - Testing functional programming patterns
- `Design documents/PreviousDiscussion.md` - Detailed development history
- `embedding-enrichment/DESIGN_PRINCIPLES_QUICK_REFERENCE.md` - Design principles
- `doctrove-api/API_DOCUMENTATION.md` - API reference

### Database
- `doctrove_schema.sql` - Database schema
- `embedding-enrichment/setup_database_functions.sql` - Database functions
- `embedding-enrichment/event_triggers.sql` - Enrichment triggers (must be applied after schema and functions)
- `fix_database_setup.sh` - Script to fix common database setup issues

## Design Principles

- **Functional Programming**: Pure functions, immutable data, map/filter/reduce patterns
- **Interceptor Pattern**: Request/response processing
- **Database-First**: Optimized schema with strategic indexing
- **Asynchronous Processing**: Background workers for enrichment
- **Testability**: Pure functions enable easier unit testing
- **Multi-Environment Support**: Environment-based configuration for development flexibility

## Common Workflows

### Development Setup (Local Laptop)
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Database is already set up on internal drive
# PostgreSQL running at: /opt/homebrew/var/postgresql@14
# Database: doctrove (58GB, ~2.9M papers)

# 3. Environment file already configured: .env.local
# Contains: Database credentials, ports (5001/3000), model paths

# 4. Start services
./services.sh start --enrichment
# OR start individually:
./doctrove.sh start          # API only
./docscope.sh start          # Frontend only

# 5. Ingest data (if needed)
cd doc-ingestor
source ../venv/bin/activate
python main_ingestor.py --file-path /path/to/data.pkl --source arxivscope
python main_ingestor.py --file-path ~/Documents/doctrove-data/marc-files/randpubs.mrc --source marc

# 6. Check service status
curl http://localhost:5001/api/health
lsof -i :3000 | grep LISTEN
```

### Starting Services (Local Laptop)
```bash
# Current configuration (ports 5001/3000)
# Environment file: .env.local (already configured)

# Start all services (API + enrichment workers)
./services.sh start --enrichment

# OR start individually:
./doctrove.sh start          # API only (port 5001)
./docscope.sh start          # Frontend only (port 3000)

# Access:
# - API: http://localhost:5001/api/health
# - Frontend: http://localhost:3000

# Services run in screen sessions (survive terminal restarts)
# View logs: screen -r doctrove_api (or docscope_react)
```

**Note**: Multi-environment setup (local/remote) can be configured in future if needed

### 2D Embedding Management
```bash
# Reset and regenerate 2D embeddings (when needed)
cd embedding-enrichment && python reset_umap_environment.py --sample-size 5000

# Check embedding status
cd embedding-enrichment && python embedding_service.py --status
```

### Progress Monitoring for Large-Scale Embedding Generation
```bash
# Monitor real-time progress of 1D embedding generation
cd embedding-enrichment && python monitor_event_listener.py

# Check event listener logs directly
screen -S embedding_1d -X hardcopy /tmp/event_listener_log.txt
tail -20 /tmp/event_listener_log.txt

# Monitor 2D embedding progress
cd embedding-enrichment && python functional_2d_processor.py --status
```

**Progress Monitoring Solution**: 
- **Real-time tracking**: Uses event listener logs to extract actual progress
- **Accurate rates**: Calculates processing rates from recent log entries
- **Cost analysis**: Real token count analysis shows ~$95 for 20M embeddings
- **No database timeouts**: Avoids expensive COUNT queries on large tables
- **Reliable estimates**: Based on actual processing data, not sampling

### Testing
```bash
# Run comprehensive test suite (recommended)
./run_comprehensive_tests.sh

# Run specific test suites
pytest docscope/tests/ -v                    # Main DocScope tests
pytest docscope/components/ -v               # Functional programming components
pytest doctrove-api/ -v                      # Backend API tests
python test_embedding_performance.py         # Root level tests
```

**Testing Status**: All test suites passing (194 tests, 0 failures, 0 warnings)
- **Unit Tests**: Fast execution, pure functions, no external dependencies
- **Integration Tests**: Marked with `@pytest.mark.skip` for external dependencies
- **Performance Tests**: 5s baseline threshold with realistic variance tolerance

**📖 For comprehensive testing details, see [COMPREHENSIVE_TESTING_GUIDE.md](COMPREHENSIVE_TESTING_GUIDE.md)**

### Performance Analysis
```bash
# Check query performance
psql -d doctrove -c "EXPLAIN ANALYZE SELECT * FROM papers WHERE source = 'aipickle';"

# Monitor API performance
tail -f doctrove-api/api.log
```

## Development Workflow Best Practices

### Running Sustained Processes
**Preferred Pattern**: Use `is_background: true` when running long-running commands to:
- Open processes in visible terminal tabs (not inline in chat)
- Keep chat interface responsive and unblocked
- Allow real-time monitoring of output and logs
- Enable easy interaction (Ctrl+C, restart, etc.)

**Example**:
```python
run_terminal_cmd(
    command="./startup.sh --with-enrichment --background",
    is_background=True  # Opens in terminal tab, doesn't block chat
)
```

**Benefits**:
- Professional development workflow
- No lost output or hidden processes
- Easy debugging and monitoring
- Mimics real development environment

### Current Environment Configuration
**Best Practice**: Use `.env.local` file for local configuration:
- **Local Development**: `.env.local` with ports 5001/3000 (API/Frontend)
- **PostgreSQL**: Standard port 5432 (configured in PostgreSQL, not env file)
- **No Hardcoded Ports**: All services use environment variables
- **Configuration Location**: Project root `.env.local` file (gitignored)
- **Note**: Multi-environment setup (local/remote) can be configured if needed in future

## Current Configuration

### Embedding Service
- **Batch Sizes**: 500 for titles, 250 for abstracts
- **True Batch API**: Single API calls for multiple texts
- **Memory Optimized**: Prevents allocation errors

### DocScope Frontend
- **Default Paper Limit**: 5000 papers (adjustable via Max Dots control)
- **Country Colors**: US (blue), China (red), Rest of World (green), RAND (purple)
- **Voronoi Boundaries**: Only appear when "Compute clusters" button is clicked
- **Home Button**: Custom "🏠 Home" button to reset to full dataset view
- **Extent Management**: Autorange only on initial load, pan/zoom preserved for filters

### Service Ports (Current Configuration)
- **API**: http://localhost:5001 (configured via `DOCTROVE_API_PORT` in `.env.local`)
- **Frontend**: http://localhost:3000 (configured via `NEW_UI_PORT` in `.env.local`)
- **Database**: PostgreSQL on port 5432 (standard PostgreSQL port)
- **Configuration**: All ports configured via `.env.local` file, not hardcoded
- **Environment**: Local laptop development - no remote server environment currently active

## Known Issues & Solutions

- **Duplicate data**: Use consistent source naming (lowercase "aipickle")
- **Memory usage**: Batch processing and model caching implemented
- **Query performance**: Strategic indexing strategy in place
- **Field mapping**: API handles relationships between `doctrove_papers` and `aipickle_metadata`
- **Voronoi Boundaries**: Only display when clustering is explicitly requested
- **Repository size**: UMAP model files (2.2GB) removed from git tracking to reduce repo size
- **Virtual environment**: `arxivscope/` directory removed from git tracking (use `source arxivscope/bin/activate` to activate)
- **Port conflicts**: Use multi-environment setup with .env files to avoid conflicts

### Database Setup Issues
- **Enrichment system not working**: Run `./fix_database_setup.sh` to check and fix missing components
- **Missing enrichment queue table**: This is a common issue - the table must be created manually before applying event triggers
- **Database functions missing**: Reapply `setup_database_functions.sql` and `event_triggers.sql` in the correct order

### Multi-Environment Issues
- **Port configuration**: All ports configured via `.env.local` file (see configuration section above)
- **Environment not loading**: Check if .env file exists and has correct format
- **Services not starting**: Verify port availability and environment variable loading

## Next Steps

Potential areas for improvement:
1. Real-time updates with WebSocket integration
2. Advanced analytics and machine learning insights
3. Multi-tenant support and user isolation
4. API versioning for backward compatibility
5. Enhanced multi-environment management tools

**📋 For planned development tasks, see [TODO.md](TODO.md)**

## **🚀 React Frontend Rebuild**

**Current Status**: React frontend code was lost during migration (submodule not bundled). Rebuilding from scratch using Dash code as reference.

**Rebuild Documentation**:
- **📋 [REBUILD_PLAN.md](docscope-platform/services/docscope/react/REBUILD_PLAN.md)** - Complete rebuild plan with phased approach
- **📋 [STATE_MANAGEMENT_STRATEGY.md](docscope-platform/services/docscope/react/STATE_MANAGEMENT_STRATEGY.md)** - State management architecture (single source of truth)

**Approach**:
- **Logic Layer First**: Implement pure functions with tests before UI
- **Functional Programming**: All business logic as pure functions (no side effects)
- **Interceptor Pattern**: Use interceptors for cross-cutting concerns (logging, validation, error handling)
- **State Management**: Single source of truth in logic layer (see `STATE_MANAGEMENT_STRATEGY.md`)

**Reference Materials**:
- **Legacy Dash Code**: `docscope/components/` - Contains functional programming components to port:
  - `view_management_fp.py` - View state management (pure functions)
  - `data_fetching_fp.py` - Data fetching (pure functions)
  - `interceptor_orchestrator.py` - Interceptor pattern implementation
  - `component_contracts_fp.py` - Component contracts
- **Design Principles**: `embedding-enrichment/DESIGN_PRINCIPLES.md`
- **Interceptor Pattern**: `docs/ARCHITECTURE/interceptor101.md`
- **Functional Programming Guide**: `docs/ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md`

**Historical Migration Planning** (for reference):
- **📁 [migration-planning/](migration-planning/)** - Original migration planning documentation
- **📋 [MIGRATION_PLANNING_INDEX.md](MIGRATION_PLANNING_INDEX.md)** - Quick reference and overview

## 🎯 For New Conversations

**Start here:** This document provides the essential context to understand the current state of the DocScope/DocTrove system.

### Current Environment Summary
- **Location**: Personal laptop (macOS) on home network
- **Database**: PostgreSQL 14 on internal drive (58GB, ~2.9M papers)
- **Ports**: API 5001, Frontend 3000, Database 5432
- **Configuration**: `.env.local` file in project root
- **No External Dependencies**: System fully operational without external drive
- **Previous**: Migrated from AWS server to local laptop (October 2025)

### If Working on React Frontend Rebuild

**If you're working on the React frontend rebuild, read these in order:**

1. **This Document** (`CONTEXT_SUMMARY.md`) - Big picture and system overview
2. **Rebuild Plan** - `docscope-platform/services/docscope/react/REBUILD_PLAN.md`
   - Complete phased approach (Logic → Testing → UI)
   - Functional programming principles
   - Interceptor pattern usage
3. **State Management Strategy** - `docscope-platform/services/docscope/react/STATE_MANAGEMENT_STRATEGY.md`
   - Single source of truth approach
   - Where state lives and how to access it
4. **Key Reference Documents**:
   - `embedding-enrichment/DESIGN_PRINCIPLES.md` - Core design principles
   - `docs/ARCHITECTURE/interceptor101.md` - Interceptor pattern specification
   - `docs/ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md` - Functional programming guide
   - `docscope/components/` - Dash code reference (view_management_fp.py, data_fetching_fp.py, etc.)

**Quick Context Check for React Rebuild**:
- ✅ React frontend code was lost (submodule not bundled during migration)
- ✅ Rebuilding from scratch using Dash code as reference
- ✅ Approach: Logic layer first with tests, then UI
- ✅ Must follow functional programming principles (pure functions)
- ✅ Must use Interceptor pattern for cross-cutting concerns
- ✅ State management: Single source of truth in logic layer

**📚 For comprehensive documentation, start with:**
- **[docs/README.md](docs/README.md)** - **Main documentation index** - Complete navigation to all documentation

**For legacy documentation references:**
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Complete system architecture and technical details
- **[QUICK_START.md](QUICK_START.md)** - Step-by-step setup and usage instructions
- **[MULTI_ENVIRONMENT_SETUP.md](MULTI_ENVIRONMENT_SETUP.md)** - Multi-environment development setup

---

*This summary should be referenced at the start of new conversations to quickly establish context.*