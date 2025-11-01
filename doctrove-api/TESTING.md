# Backend API Testing Guide

This document describes how to test the `doctrove-api` backend service.

## Test Structure

The backend API tests are organized in the `doctrove-api/` directory:

```
doctrove-api/
├── test_api_simple.py           # Simple API endpoint tests
├── test_api_comprehensive.py    # Comprehensive API endpoint tests
├── test_api_v2_demo.py          # V2 API demo/test script (requires running server)
├── test_business_logic.py       # Comprehensive business logic tests
├── test_business_logic_fast.py  # Fast business logic tests (pure functions)
└── test_interceptors.py         # API interceptor pattern tests
```

## Test Types

### 1. Unit Tests (Pure Functions)
**Files**: `test_business_logic.py`, `test_business_logic_fast.py`

These tests validate pure functions without database connections:
- Validation functions (`validate_bbox`, `validate_sql_filter`, etc.)
- Mathematical functions (`calculate_cosine_similarity`, etc.)
- Query building functions (`build_optimized_query_v2`, etc.)

**Run fast tests:**
```bash
cd doctrove-api
python test_business_logic_fast.py
```

**Run comprehensive tests:**
```bash
cd doctrove-api
python test_business_logic.py
```

### 2. API Endpoint Tests (Flask Test Client)
**Files**: `test_api_simple.py`, `test_api_comprehensive.py`

These tests use Flask's test client (no external server needed):
- Health endpoint tests
- Papers endpoint tests (basic, with filters, etc.)
- Validation tests
- Error handling tests

**Run simple tests:**
```bash
cd doctrove-api
python test_api_simple.py
```

**Run comprehensive tests:**
```bash
cd doctrove-api
python test_api_comprehensive.py
```

Or using pytest:
```bash
pytest doctrove-api/test_api_comprehensive.py -v
```

### 3. Integration Tests (Requires Running Server)
**File**: `test_api_v2_demo.py`

This test script makes actual HTTP requests to a running API server:
- Tests all v2 API features
- Requires the API server to be running
- Uses environment variables for configuration

**Run integration tests:**
```bash
# Start the API server first
cd doctrove-api
python api.py

# In another terminal, run the demo
python test_api_v2_demo.py
```

## Configuration

All tests read configuration from `.env.local` in the project root:

```env
# API Configuration
NEW_API_PORT=5001              # API port (preferred)
DOCTROVE_API_PORT=5001        # Fallback API port
NEW_API_BASE_URL=http://localhost:5001

# Database Configuration
DOC_TROVE_HOST=localhost
DOC_TROVE_PORT=5432           # PostgreSQL port (changed from 5434)
DOC_TROVE_DB=doctrove
DOC_TROVE_USER=doctrove_admin
DOC_TROVE_PASSWORD=
```

## Current Setup (Local Laptop)

- **API Port**: 5001 (from `NEW_API_PORT` or `DOCTROVE_API_PORT` in `.env.local`)
- **Database Port**: 5432 (from `DOC_TROVE_PORT` in `.env.local`)
- **Database Location**: Internal drive (`/opt/homebrew/var/postgresql@14`)

## Running All Tests

### From Project Root
```bash
# Run comprehensive test suite
./run_comprehensive_tests.sh

# Run only backend tests
pytest doctrove-api/ -v

# Run fast tests
./scripts/ROOT_SCRIPTS/run_fast_tests.sh
```

### Individual Test Files
```bash
cd doctrove-api

# Fast unit tests (~0.001 seconds)
python test_business_logic_fast.py

# Comprehensive unit tests
python test_business_logic.py

# Simple API tests
python test_api_simple.py

# Comprehensive API tests
python test_api_comprehensive.py

# Integration tests (requires running server)
python test_api_v2_demo.py
```

## Test Coverage

### Business Logic Tests
- ✅ Validation functions (bbox, SQL filter, limit, offset, fields, etc.)
- ✅ Mathematical functions (cosine similarity, embeddings)
- ✅ Query building functions
- ✅ Error handling and edge cases

### API Endpoint Tests
- ✅ Health endpoint
- ✅ Papers endpoint (basic, with filters, pagination, sorting)
- ✅ Input validation
- ✅ Error responses
- ✅ Field selection
- ✅ SQL filtering
- ✅ Bounding box filtering

### Integration Tests
- ✅ V2 API endpoint (`/api/papers/v2`)
- ✅ Semantic search
- ✅ Combined filters
- ✅ Complex queries
- ✅ Error scenarios

## Test Best Practices

1. **Fast Tests First**: Run `test_business_logic_fast.py` for quick feedback
2. **Unit Tests Before Integration**: Test pure functions before testing with database
3. **Mock External Dependencies**: Use Flask test client for endpoint tests (no real server needed)
4. **Use Environment Variables**: Always read from `.env.local` for configuration
5. **Test Edge Cases**: Include invalid inputs, boundary conditions, error scenarios

## Troubleshooting

### Tests Failing with Database Connection Errors
- Ensure PostgreSQL is running: `brew services list | grep postgresql`
- Check database port in `.env.local`: `DOC_TROVE_PORT=5432`
- Verify database exists: `psql -U doctrove_admin -d doctrove -c "SELECT 1;"`

### Tests Failing with Port Already in Use
- Check if API server is already running: `lsof -i :5001`
- Stop existing server or use a different port in `.env.local`

### Tests Failing with Import Errors
- Ensure virtual environment is activated: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

## Test Requirements

### Unit Tests (No External Dependencies)
- ✅ Python virtual environment
- ✅ Required Python packages
- ✅ No database connection needed
- ✅ No API server needed

### API Endpoint Tests (Flask Test Client)
- ✅ Python virtual environment
- ✅ Required Python packages
- ✅ Database connection (for endpoint tests that query database)
- ✅ No external API server needed (uses Flask test client)

### Integration Tests (HTTP Requests)
- ✅ API server must be running
- ✅ Database must be accessible
- ✅ Environment variables configured in `.env.local`

## Migration Notes

**Changed Configuration:**
- Database port: `5434` → `5432` (standard PostgreSQL port)
- API port: `5002` → `5001` (standardized)
- Paths: `/opt/arxivscope/` → relative paths (local laptop setup)

**Tests Updated:**
- All tests now read from `.env.local` in project root
- Port configurations use environment variables
- No hardcoded paths or ports

