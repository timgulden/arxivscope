# DocTrove API

> **Current Environment (October 2025)**: This API runs on a local laptop environment. API on port 5001, PostgreSQL on port 5432 (internal drive). See [CONTEXT_SUMMARY.md](../CONTEXT_SUMMARY.md) for current setup details.

This is the backend API for the DocScope application, providing access to the DocTrove database of academic papers.

## Overview

The DocTrove API serves as the data layer for the DocScope visualization frontend. It provides endpoints for:

- Fetching papers with 2D embeddings for visualization
- Filtering papers by geographic bounding boxes
- Retrieving paper metadata (titles, abstracts, sources, etc.)
- Health checks and status monitoring

## Architecture

The API uses the **Interceptor Pattern** for clean separation of concerns:

- **`api.py`** - Main Flask application using interceptor pattern
- **`api_interceptors.py`** - Interceptor functions for validation, business logic, and response formatting
- **`business_logic.py`** - Core business logic functions
- **`interceptor.py`** - Interceptor framework implementation
- **`api_backup.py`** - Legacy monolithic API (backup)
- **`config.py`** - Configuration management and database connection
- **`db.py`** - Database utilities and query functions

### Interceptor Pattern Benefits

- **Separation of Concerns**: Validation, business logic, and response formatting are separated
- **Testability**: Each interceptor can be tested independently
- **Maintainability**: Changes to validation don't affect business logic
- **Reusability**: Interceptors can be reused across different endpoints
- **Error Handling**: Centralized error handling through error interceptors

## Quick Start

1. **Install dependencies** (from the main project root):
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   Create a `.env.local` file in the project root (from `env.local.example` template) with your database configuration:
   ```
   DB_HOST=localhost
   DOC_TROVE_PORT=5432
   DB_NAME=doctrove
   DB_USER=doctrove_admin
   DB_PASSWORD=  # Empty for trust authentication (local setup)
   ```
   
   The API reads configuration from `.env.local` via environment variables.

3. **Start the API**:
   ```bash
   # Activate virtual environment
   source ../venv/bin/activate
   
   # Start the API
   python api.py
   ```
   
   The API will run on http://localhost:5001
   
   Or use the convenience script:
   ```bash
   ./start_api.sh
   ```

4. **Verify it's running**:
   ```bash
   curl http://localhost:5001/api/health
   ```

## API Endpoints

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

**Quick Reference:**
- `GET /api/health` - Health check
- `GET /api/papers` - Fetch papers with optional filtering
  - Query parameters:
    - `limit`: Maximum number of papers to return (default: 500)
    - `fields`: Comma-separated list of fields to include
    - `bbox`: Geographic bounding box (x1,y1,x2,y2)
    - `sql_filter`: SQL WHERE clause for advanced filtering
    - `similar_to`: Text for similarity search

## Configuration

The API runs on port 5001 by default. Configuration is handled in `config.py` which reads from `.env.local` file:
- **Port**: 5001 (configured via environment variables)
- **Database**: PostgreSQL on port 5432 (internal drive)
- **Authentication**: Trust authentication (local setup)

## Integration with DocScope

The DocScope frontends connect to this API on port 5001:
- **React Frontend** (port 3000): Modern frontend - recommended
- **Legacy Dash Frontend** (port 8050): Frozen, bug fixes only

The API provides the 2D embeddings and metadata needed for the interactive scatter plot visualization. 