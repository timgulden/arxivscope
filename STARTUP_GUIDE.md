# DocScope/DocTrove Startup Guide [Current]

> **Current Environment (October 2025)**: This system runs on a local laptop environment. API on port 5001, React Frontend on port 3000, PostgreSQL on port 5432. All data is stored on the internal drive. See [CONTEXT_SUMMARY.md](CONTEXT_SUMMARY.md) for current setup details.
>
> For consolidated startup docs, see `docs/DEVELOPMENT/STARTUP_GUIDE.md`. For historical multi-environment setup, see `docs/DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md`.

## Overview

This guide covers the correct startup procedure for the DocScope/DocTrove system. The system consists of multiple components that need to be started in the proper order with the correct execution methods.

## System Components

1. **Database** (PostgreSQL) - Stores papers and embeddings on port 5432 (internal drive)
2. **Event-Driven Enrichment System** - Processes embeddings and 2D projections
3. **DocTrove API** (Flask) - Backend API server on port 5001
4. **React Frontend** - Modern frontend on port 3000 (recommended)
5. **Legacy Dash Frontend** - Legacy frontend on port 8050 (frozen, reference only)

## Current Setup (Local Laptop)

**Environment**: Single local laptop environment  
**Configuration**: `.env.local` file (in .gitignore)  
**Ports**: API 5001, React Frontend 3000, PostgreSQL 5432  
**Storage**: Internal drive (database and models)

> **Note**: For historical multi-environment setup information, see [docs/DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md](docs/DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md). The current system uses a single local environment configuration.

## Prerequisites

- PostgreSQL database named `doctrove` running on port 5432 (internal drive)
- Python virtual environment activated (typically `venv` in project root)
- All dependencies installed (`pip install -r requirements.txt`)
- `.env.local` file configured (see `env.local.example` for template)

## Startup Procedure

### Option 1: Automated Startup (Recommended)

The easiest way to start the system is using the automated startup script:

```bash
# Start basic services (API + Frontend)
./startup.sh --background

# Start all services including enrichment
./startup.sh --with-enrichment --background

# Restart all services (stops existing services first)
./startup.sh --with-enrichment --background --restart
```

**What the startup script does:**
- Automatically detects and handles existing processes
- Checks database connectivity
- Starts services in the correct order
- Tests all services for proper operation
- Provides detailed status information

### Option 2: Manual Startup

If you prefer manual control or need to troubleshoot, follow these steps:

#### 1. Verify Database Connection

First, ensure the database is accessible and contains data:

```bash
# Check database connectivity and data count
psql -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"
```

Expected output: Should show a count (e.g., `2749`)

### 2. Start Event-Driven Enrichment System (Optional)

**When to use:** When you want automatic processing of newly ingested papers  
**Location:** `embedding-enrichment/` directory  
**Execution Method:** Direct script execution

```bash
cd embedding-enrichment
python event_listener.py
```

**Expected Output:**
```
2025-07-09 14:47:53,014 - INFO - Registered listener for event: paper_added
2025-07-09 14:47:53,014 - INFO - Registered listener for event: embedding_ready
2025-07-09 14:47:53,014 - INFO - Registered listener for event: projection_ready
2025-07-09 14:47:53,014 - INFO - Starting enrichment orchestrator...
2025-07-09 14:47:53,014 - INFO - Starting event listener...
2025-07-09 14:47:53,015 - INFO - Event listener started
Event-driven enrichment system started!
Listening for database events...
Press Ctrl+C to stop
2025-07-09 14:47:54,333 - INFO - Event listener connection established
2025-07-09 14:47:54,347 - INFO - Listening for event: paper_added
2025-07-09 14:47:54,348 - INFO - Listening for event: embedding_ready
2025-07-09 14:47:54,349 - INFO - Listening for event: projection_ready
```

**What it does:**
- Listens for database events when papers are added
- Automatically generates embeddings for new papers
- Creates 2D projections for papers with embeddings
- Processes papers in batches for efficiency

**Verification:**
```bash
ps aux | grep event_listener
```

Should show the event listener process running.

### 3. Start DocTrove API Server

**Location:** `doctrove-api/` directory  
**Port:** 5001  
**Execution Method:** Direct script execution

```bash
cd doctrove-api
python api.py
```

**Expected Output:**
```
* Serving Flask app 'api'
* Debug mode: on
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5001
* Running on http://10.210.11.249:5001
```

**Verification:**
```bash
# Check individual service health
curl http://localhost:5001/api/health

# Check system-wide health
curl http://localhost:5001/api/health/system

# Check all services status
./check_services.sh
```

Should return:
```json
{
  "service": "doctrove-api",
  "status": "healthy",
  "timestamp": "2025-07-09 11:54:37"
}
```

### 4. Start DocScope Frontend

**Location:** Project root directory  
**Port:** 8050  
**Execution Method:** Module execution (NOT direct script execution)

```bash
# From the project root directory (arxivscope-back-end)
python -m docscope.app
```

**Expected Output:**
```
Dash is running on http://0.0.0.0:8050/
* Serving Flask app 'app'
* Debug mode: on
```

**Verification:**
```bash
curl http://localhost:8050/ | head -10
```

Should return HTML content from the Dash application.

## Common Issues and Solutions

### Issue 1: ImportError with DocScope

**Problem:**
```
ImportError: attempted relative import with no known parent package
```

**Cause:** Trying to run `docscope/app.py` directly instead of as a module.

**Solution:** Use module execution from the project root:
```bash
# CORRECT
python -m docscope.app

# INCORRECT
cd docscope && python app.py
```

### Issue 2: ModuleNotFoundError

**Problem:**
```
ModuleNotFoundError: No module named 'components'
```

**Cause:** Changed relative imports to absolute imports, but the app is designed for relative imports.

**Solution:** Keep relative imports in `docscope/app.py`:
```python
# CORRECT
from .components.ui_components import (...)
from .components.callbacks import register_callbacks

# INCORRECT
from components.ui_components import (...)
from components.callbacks import register_callbacks
```

### Issue 3: Wrong Port for API

**Problem:** API calls failing on port 5000.

**Cause:** DocTrove API runs on port 5001, not 5000.

**Solution:** Use port 5001 for all API calls:
```bash
# CORRECT
curl http://localhost:5001/api/health

# INCORRECT
curl http://localhost:5000/api/health
```

### Issue 4: Database Connection Issues

**Problem:** API can't connect to database.

**Solution:** Check database configuration in `doctrove-api/config.py`:
```python
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'doctrove'
DB_USER = 'your_username'
DB_PASSWORD = 'your_password'
```

## Complete Startup Script

Create a startup script to automate the process:

```bash
#!/bin/bash
# startup.sh

echo "Starting DocScope/DocTrove system..."

# Check database
echo "Checking database..."
psql -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;" || {
    echo "ERROR: Database not accessible"
    exit 1
}

# Start API server
echo "Starting DocTrove API server..."
cd doctrove-api
python api.py &
API_PID=$!
cd ..

# Wait for API to start
echo "Waiting for API server..."
sleep 5

# Test API
curl -s http://localhost:5001/api/health > /dev/null || {
    echo "ERROR: API server not responding"
    kill $API_PID
    exit 1
}

# Start frontend
echo "Starting DocScope frontend..."
python -m docscope.app &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend..."
sleep 5

# Test frontend
curl -s http://localhost:8050/ > /dev/null || {
    echo "ERROR: Frontend not responding"
    kill $API_PID $FRONTEND_PID
    exit 1
}

echo "System started successfully!"
echo "API: http://localhost:5001"
echo "Frontend: http://localhost:8050"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo 'Stopping services...'; kill $API_PID $FRONTEND_PID; exit" INT
wait
```

## Ingestion and Enrichment Pipeline

### Complete Pipeline Workflow

The system supports a complete ingestion and enrichment pipeline:

1. **Ingestion:** Papers are ingested from source files (e.g., AiPickle)
2. **Event Processing:** Event-driven system automatically processes new papers
3. **Embedding Generation:** Fresh embeddings created using Azure OpenAI
4. **2D Projection:** UMAP creates 2D coordinates for visualization
5. **API/Frontend:** Papers are available for viewing and interaction

### Manual Ingestion Process

**Location:** `doc-ingestor/` directory

```bash
cd doc-ingestor

# Ingest with limit (for testing)
python main.py --source aipickle --limit 20

# Ingest full dataset
python main.py --source aipickle
```

**What happens during ingestion:**
- Papers are inserted into `doctrove_papers` table (without embeddings)
- Original embeddings are stored in source-specific metadata table
- Database triggers fire events for enrichment processing
- Event listener automatically processes papers for embeddings and 2D projections

### Manual Enrichment Processing

**Location:** `embedding-enrichment/` directory

```bash
cd embedding-enrichment

# Generate embeddings for papers that need them
python embedding_service.py --embedding-type title --limit 20

# Generate 2D projections for papers with embeddings
python main.py --mode incremental --embedding-type title

# Check status
python embedding_service.py --status
```

### Event-Driven vs Manual Processing

**Event-Driven (Recommended):**
- Start event listener before ingestion
- Automatic processing as papers are added
- No manual intervention needed
- Best for production use

**Manual Processing:**
- Run enrichment services after ingestion
- More control over timing and batches
- Good for development and testing
- Can process specific subsets

## Development Workflow

### Starting for Development

1. **Terminal 1 - Event Listener (Optional):**
   ```bash
   cd embedding-enrichment
   python event_listener.py
   ```

2. **Terminal 2 - API Server:**
   ```bash
   cd doctrove-api
   python api.py
   ```

3. **Terminal 3 - Frontend:**
   ```bash
   python -m docscope.app
   ```

### Stopping Services

#### Automated Stopping
```bash
# Stop all services
./stop_services.sh
```

#### Manual Stopping
- **API Server:** Ctrl+C in the API terminal
- **Frontend:** Ctrl+C in the frontend terminal
- **Both:** Use the startup script and Ctrl+C

### Restarting Services

```bash
# Restart all services (stops existing services first)
./startup.sh --with-enrichment --background --restart

# Or use the force flag (same as restart)
./startup.sh --with-enrichment --background --force
```

## Troubleshooting

### Check Service Status

#### Automated Health Checks
```bash
# Check all services status
./check_services.sh

# Check individual service health
curl http://localhost:5001/api/health
curl http://localhost:5001/api/health/enrichment
curl http://localhost:5001/api/health/system
```

#### Manual Process Checking
```bash
# Check if processes are running
ps aux | grep "python api.py" | grep -v grep
ps aux | grep "python -m docscope.app" | grep -v grep

# Check ports in use
lsof -i :5001
lsof -i :8050
```

### Logs and Debugging

- **API Logs:** Check the terminal running the API server
- **Frontend Logs:** Check the terminal running the frontend
- **Database Logs:** Check PostgreSQL logs

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ImportError: attempted relative import` | Wrong execution method | Use `python -m docscope.app` |
| `ModuleNotFoundError: No module named 'components'` | Wrong import style | Keep relative imports |
| `Connection refused` | Wrong port | Use port 5001 for API |
| `Database connection failed` | Database not running | Start PostgreSQL |
| `Cannot use scipy.linalg.eigh for sparse A` | UMAP with small dataset | Use simple projection for <5 papers |
| `Event listener not processing papers` | Papers already in DB | Clear DB and restart event listener |
| `Embedding generation failed` | Azure OpenAI connection | Check API keys and network |

## Configuration Files

### API Configuration
- **File:** `doctrove-api/config.py`
- **Key Settings:** Database connection, batch sizing

### Frontend Configuration
- **File:** `docscope/config/settings.py`
- **Key Settings:** API base URL, target records per view

### Database Configuration
- **File:** `doctrove_schema.sql`
- **Purpose:** Database schema and functions

## Performance Notes

- **API Response Time:** 50-200ms (optimized with strategic indexing)
- **Frontend Load Time:** Depends on data size and network
- **Memory Usage:** Batch processing implemented for large datasets
- **Scalability:** Supports up to 5 million papers with streaming processing

## Security Notes

- **Development Mode:** Both services run in debug mode
- **CORS:** Enabled for frontend integration
- **Database:** Use proper authentication
- **Production:** Use production WSGI servers

## Next Steps

After successful startup:

1. **Verify Data Loading:** Check that papers appear in the visualization
2. **Test Interactions:** Try clicking on points, using filters
3. **Check Embeddings:** Verify 2D embeddings are displayed
4. **Test API Endpoints:** Use the API documentation for testing

## Support

If you encounter issues:

1. Check this guide for common solutions
2. Review the logs for error messages
3. Verify all prerequisites are met
4. Check the `CONTEXT_SUMMARY.md` for system overview
5. Refer to `FUNCTIONAL_PROGRAMMING_GUIDE.md` for code patterns 