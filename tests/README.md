# Tests Directory

This directory contains all project tests organized by category. The main test runner is `run_comprehensive_tests.sh` in the project root.

## 🏗️ Test Organization

### **`performance/`** - Performance and Benchmark Tests
- **`test_embedding_performance.py`** - Tests embedding generation performance
- **`test_performance.py`** - Tests API and frontend performance
- **`test_performance_local.py`** - Local performance testing utilities
- **`test_embedding.py`** - Basic embedding functionality tests

### **`integration/`** - Integration and End-to-End Tests
- **`test_openalex_integration.py`** - OpenAlex API integration tests
- **`test_docscope_v2_integration.py`** - DocScope v2 integration tests
- **`test_full_execution.py`** - Full workflow execution tests

### **`ingestion/`** - Data Ingestion and Processing Tests
- **`test_openalex_ingester.py`** - OpenAlex data ingestion tests
- **`test_marc_ingester.py`** - MARC data ingestion tests
- **`test_metadata_insertion.py`** - Metadata insertion tests
- **`test_field_replacement.py`** - Field replacement logic tests
- **`test_query_building.py`** - Query building functionality tests

### **`enrichment/`** - Data Enrichment and Analysis Tests
- **`test_enrichment_minimal.py`** - Minimal enrichment tests
- **`test_embedding_costs.py`** - Embedding cost analysis tests
- **`test_aipickle_ingester.py`** - AI Pickle ingestion tests

### **`utilities/`** - Utility and Functional Tests
- **`test_functional_minimal.py`** - Minimal functional tests
- **`test_event_driven_ingestion.py`** - Event-driven ingestion tests

### **`scripts/`** - Test Scripts and SQL Files
- **`test_openalex_s3_access.sh`** - S3 access testing script
- **`openalex_test_ingestion.sh`** - OpenAlex ingestion test script
- **`openalex_test_ingestion_fixed.sh`** - Fixed version of ingestion test
- **`test_semantic_search_performance.sql`** - SQL performance test
- **`test_semantic_search_with_vector.sql`** - Vector search SQL test

## 🚀 Running Tests

### **Comprehensive Test Suite** (Recommended)
```bash
# From project root
./run_comprehensive_tests.sh
```

### **Individual Test Categories**
```bash
# Performance tests
python -m pytest tests/performance/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Ingestion tests
python -m pytest tests/ingestion/ -v

# Enrichment tests
python -m pytest tests/enrichment/ -v

# Utility tests
python -m pytest tests/utilities/ -v
```

### **Shell Scripts**
```bash
# From tests/scripts/ directory
cd tests/scripts/
./test_openalex_s3_access.sh
./openalex_test_ingestion.sh
```

## ⚠️ Important Notes

- **These tests are NOT part of the main comprehensive test suite**
- **Many tests require specific data or services to be running**
- **Some tests are designed to be run from specific directories**
- **Check individual test files for specific requirements and setup**

## 🔧 Test Requirements

Most tests require:
- Database connection (PostgreSQL with pgvector)
- API services running
- Appropriate environment variables set
- Test data available

## 📝 Adding New Tests

When adding new tests:
1. Place them in the appropriate subdirectory
2. Update this README with a description
3. Ensure they can be run independently
4. Add any specific setup requirements to the test file

---

*For the main test suite that runs in CI/CD, see the tests in `docscope/tests/`, `docscope/components/`, and `doctrove-api/` directories.*


