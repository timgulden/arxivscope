# OpenAlex Ingestion Guide

This guide documents the complete process for ingesting OpenAlex data into the DocScope/DocTrove system, including historical data ingestion, incremental updates, and enrichment.

## Table of Contents

1. [Overview](#overview)
2. [Modern Ingestion Architecture: Shared Framework & Parallelization](#modern-ingestion-architecture-shared-framework--parallelization)
3. [Prerequisites](#prerequisites)
4. [Database Setup](#database-setup)
5. [Historical Data Ingestion](#historical-data-ingestion)
6. [Incremental Updates](#incremental-updates)
7. [Enrichment Process](#enrichment-process)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Scripts Reference](#scripts-reference)

## Overview

The OpenAlex ingestion process consists of three main phases:

1. **Historical Data Ingestion**: Bulk ingestion of existing OpenAlex data from S3
2. **Incremental Updates**: Daily file-based updates for new/updated papers
3. **Enrichment**: Generation of embeddings and 2D visualizations

### Data Flow

```
S3 OpenAlex Files → Download → Transform → Ingest → Enrich → Visualize
```

---

## Modern Ingestion Architecture: Shared Framework & Parallelization

### Overview

As of 2025, the OpenAlex ingestion system uses a **shared functional ingestion framework** for all major data sources (OpenAlex, MARC, etc.). This approach provides:

- **Functional programming principles**: Pure transformation functions, immutable data structures, and clear separation of pure/impure code.
- **Testability**: All pure functions are unit tested.
- **Code reuse**: The same ingestion logic is used for OpenAlex, MARC, and other sources.
- **Parallelization**: Ingestion can be run in parallel across multiple files or file chunks for high throughput.

### Key Components

- `shared_ingestion_framework.py`: Core ingestion logic, database operations, error handling, and functional patterns.
- `openalex_ingester.py`: OpenAlex-specific file reading, transformation, and metadata extraction, using the shared framework.
- `test_openalex_ingester.py`: Unit tests for all pure OpenAlex ingestion functions.

### How Parallel Ingestion Works

- **Multiple files**: Use Python’s `concurrent.futures.ProcessPoolExecutor` to run multiple ingester processes in parallel, each on a different file.
- **Single large file**: Split the file into chunks and process each chunk in a separate process.
- **Batch inserts**: The framework supports efficient, reliable inserts with proper error handling.

**Example: Parallel Ingestion Script**

```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from openalex_ingester import process_openalex_file_unified

def ingest_file(file_path):
    return process_openalex_file_unified(Path(file_path), limit=10000)  # or whatever limit

if __name__ == '__main__':
    files = list(Path('data/openalex/').glob('*.jsonl.gz'))
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(ingest_file, files))
    print('All files ingested!')
```

### Design Principles

- **Functional programming**: All data transformations are pure functions.
- **Immutability**: Data structures are immutable for safety and testability.
- **Separation of concerns**: File reading, transformation, and database operations are clearly separated.
- **Testability**: All pure functions are unit tested (see `test_openalex_ingester.py`).

---

## Prerequisites

### System Requirements

- Python 3.10+
- PostgreSQL with pgvector extension
- curl (for file downloads) - **REQUIRED**
- AWS CLI (optional, not needed for our approach)
- Sufficient disk space (~50GB for full dataset)

### Environment Setup

1. **Virtual Environment**: Ensure the `arxivscope` virtual environment is activated
2. **Database Connection**: Verify PostgreSQL connection in `doc-ingestor/config.py`
3. **Azure OpenAI**: Ensure API key is configured for embeddings

### Required Dependencies

All dependencies are included in the project's `requirements.txt`:

```bash
pip install -r requirements.txt
```

## S3 Data Access

### ⚠️ Critical: URL Format Requirements

OpenAlex data is stored in AWS S3 and can be accessed in two different ways. **Our system uses the HTTP/HTTPS format for reliability and simplicity.**

#### Correct Access Method (HTTP/HTTPS)

**Base URL:** `https://openalex.s3.us-east-1.amazonaws.com/data/works/`

**File Structure:**
```
https://openalex.s3.us-east-1.amazonaws.com/data/works/
├── 2025-01-01/
│   ├── part_000.gz
│   ├── part_001.gz
│   └── ...
├── 2025-01-02/
│   ├── part_000.gz
│   └── ...
└── ...
```

**Access Commands:**
```bash
# List available dates
curl -s "https://openalex.s3.us-east-1.amazonaws.com/data/works/" | grep -o '2025-[0-9-]*'

# Download a specific file
curl -o local_file.gz "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"

# Check file size
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"
```

#### Incorrect Access Method (s3:// protocol)

**❌ DO NOT USE THIS APPROACH:**
```bash
# This will NOT work for public access
aws s3 ls s3://openalex/data/works/ --no-sign-request
aws s3 sync s3://openalex/data/works/ ./local-dir --no-sign-request
```

**Why s3:// doesn't work:**
- Requires AWS CLI installation
- May require credentials even for public data
- More complex error handling
- Our scripts use `curl` for simplicity and reliability

### Data Format

- **File Format**: Gzipped JSONL (one JSON object per line)
- **Compression**: Each file is compressed with gzip
- **Content**: Each line contains a complete OpenAlex work object
- **Size**: Files range from ~50MB to ~200MB each

### Testing S3 Access

Before running ingestion, always test S3 access:

```bash
# Test 1: Check if you can access the base URL
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/"

# Test 2: Check if you can list available dates
curl -s "https://openalex.s3.us-east-1.amazonaws.com/data/works/" | head -10

# Test 3: Check if you can download a small file
curl -o test_file.gz "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"
ls -la test_file.gz
rm test_file.gz

# Test 4: Verify the file is valid gzip
curl -s "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz" | gunzip -t
```

### Common S3 Access Issues

1. **Network Connectivity**: Ensure internet access to AWS S3
2. **Firewall**: Some corporate networks block S3 access
3. **DNS Resolution**: Ensure `openalex.s3.us-east-1.amazonaws.com` resolves
4. **Rate Limiting**: AWS may throttle requests if too frequent

### Alternative Access Methods

If direct S3 access fails, consider:

1. **Proxy Configuration**: Configure HTTP proxy if behind corporate firewall
2. **VPN**: Use VPN to bypass network restrictions
3. **Mirror Sites**: Check if OpenAlex data is mirrored elsewhere
4. **Contact OpenAlex**: Reach out to OpenAlex team for alternative access

## Database Setup

### Schema Requirements

The system uses the existing `doctrove_papers` table with OpenAlex-specific fields:

```sql
-- OpenAlex-specific fields in doctrove_papers
openalex_updated_date TIMESTAMP,
openalex_work_type TEXT,
openalex_venue TEXT,
openalex_raw_data JSONB
```

### Metadata Tables

The system automatically creates source-specific metadata tables:

```sql
-- Created automatically by create_source_metadata_table()
CREATE TABLE openalex_metadata (
    doctrove_paper_id UUID PRIMARY KEY REFERENCES doctrove_papers(doctrove_paper_id),
    openalex_updated_date TIMESTAMP,
    openalex_work_type TEXT,
    openalex_venue TEXT,
    openalex_raw_data JSONB
);
```

### Ingestion Log Table

For tracking file processing progress:

```sql
CREATE TABLE openalex_ingestion_log (
    id SERIAL PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_date DATE NOT NULL,
    records_ingested INTEGER,
    ingestion_started_at TIMESTAMP DEFAULT NOW(),
    ingestion_completed_at TIMESTAMP,
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT
);

CREATE INDEX idx_openalex_ingestion_log_file_path ON openalex_ingestion_log (file_path);
CREATE INDEX idx_openalex_ingestion_log_file_date ON openalex_ingestion_log (file_date);
CREATE INDEX idx_openalex_ingestion_log_status ON openalex_ingestion_log (status);
```

## Historical Data Ingestion

### Step 1: Cleanup Existing Data (if needed)

If you need to start fresh or remove test data:

```bash
# Run cleanup with visible progress
./run_cleanup_visible.sh

# Or run cleanup in background
./cleanup_openalex_batch.sh
```

### Step 2: Test Ingestion (Recommended)

Start with a small test to verify the pipeline using the new Python ingester:

```bash
# Ingest a single file for testing
python openalex_ingester.py data/openalex/2025-01-01/part_000.jsonl.gz --limit 1000
```

Or, for parallel ingestion:

```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from openalex_ingester import process_openalex_file_unified

def ingest_file(file_path):
    return process_openalex_file_unified(Path(file_path), limit=10000)

files = list(Path('data/openalex/').glob('*.jsonl.gz'))
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(ingest_file, files))
```

### Step 3: Full Historical Ingestion

For production ingestion of historical data, use the parallel Python approach above. The ingestion scripts (`openalex_incremental_files.sh`, etc.) can be updated to call the new Python ingester in parallel for each file.

---

## Incremental Updates

The incremental update scripts should use the new `openalex_ingester.py` for ingestion. For high throughput, run multiple instances in parallel, each on a different file or date range.

Example:

```bash
# Ingest new files in parallel
python openalex_ingester.py data/openalex/2025-01-02/part_000.jsonl.gz &
python openalex_ingester.py data/openalex/2025-01-02/part_001.jsonl.gz &
wait
```

Or use the Python parallelization example above.

---

## Enrichment Process

### Starting Enrichment Service

The enrichment service generates embeddings and 2D visualizations:

```bash
# Start all services with enrichment
./startup.sh --with-enrichment --background

# Or start enrichment only
cd embedding-enrichment
python main.py
```

### Enrichment Workflow

1. **Unified Embeddings**: Combines title and abstract text
2. **2D Visualizations**: Uses UMAP for dimensionality reduction
3. **Batch Processing**: Processes papers in configurable batches

### Monitoring Enrichment Progress

```bash
# Check enrichment logs
tail -f enrichment.log

# Check database status
psql -h localhost -U tgulden -d doctrove -c "
SELECT 
    COUNT(*) as total_papers,
    COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_2d_embeddings
FROM doctrove_papers 
WHERE doctrove_source = 'openalex';"
```

## Monitoring and Maintenance

### Database Monitoring

```sql
-- Check OpenAlex paper counts
SELECT 
    COUNT(*) as total_openalex,
    COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_2d_embeddings
FROM doctrove_papers 
WHERE doctrove_source = 'openalex';

-- Check ingestion log status
SELECT 
    status,
    COUNT(*) as file_count,
    SUM(records_ingested) as total_records
FROM openalex_ingestion_log 
GROUP BY status;

-- Check recent ingestions
SELECT 
    file_path,
    file_date,
    records_ingested,
    ingestion_started_at,
    ingestion_completed_at,
    status
FROM openalex_ingestion_log 
ORDER BY ingestion_started_at DESC 
LIMIT 10;
```

### Log Monitoring

```bash
# Enrichment service logs
tail -f enrichment.log

# API server logs
tail -f api.log

# Frontend logs
tail -f frontend.log
```

### Performance Monitoring

```bash
# Check database size
psql -h localhost -U tgulden -d doctrove -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Test database connection
psql -h localhost -U tgulden -d doctrove -c "SELECT 1;"

# Check connection parameters in config.py
cat doc-ingestor/config.py
```

#### 2. File Download Issues

**⚠️ CRITICAL: S3 URL Format**

The OpenAlex S3 data can be accessed in two different formats, and using the wrong one will cause failures:

**Correct Format (HTTP/HTTPS):**
```bash
# Direct HTTP access - WORKS
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"

# List available files
curl -s "https://openalex.s3.us-east-1.amazonaws.com/data/works/" | grep -o '2025-[0-9-]*'
```

**Incorrect Format (s3:// protocol):**
```bash
# AWS CLI s3:// format - DOES NOT WORK for public access
aws s3 ls s3://openalex/data/works/ --no-sign-request
aws s3 sync s3://openalex/data/works/ ./local-dir --no-sign-request
```

**Why This Matters:**
- The `s3://` protocol requires AWS CLI and proper credentials
- The `https://` format works with standard HTTP tools (curl, wget)
- Our scripts use `curl` for reliability and simplicity
- Using the wrong format will cause "access denied" or "not found" errors

**Testing S3 Access:**
```bash
# Test direct file access
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"

# Test directory listing
curl -s "https://openalex.s3.us-east-1.amazonaws.com/data/works/" | head -20

# Test file download (small test)
curl -o test_file.gz "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"
ls -la test_file.gz
rm test_file.gz
```

#### 3. Memory Issues

```bash
# Monitor memory usage
top -p $(pgrep -f "python.*main.py")

# Reduce batch sizes in scripts if needed
# Edit BATCH_SIZE variable in ingestion scripts
```

#### 4. Embedding API Issues

```bash
# Test Azure OpenAI connection
python -c "
import openai
openai.api_key = 'your-key'
response = openai.Embedding.create(
    input=['test text'],
    model='text-embedding-ada-002'
)
print('API working:', len(response['data'][0]['embedding']))
"
```

### Error Recovery

#### Failed Ingestion Recovery

```bash
# Check failed files
psql -h localhost -U tgulden -d doctrove -c "
SELECT file_path, error_message 
FROM openalex_ingestion_log 
WHERE status = 'failed';"

# Retry failed files
./openalex_incremental_files.sh --retry-failed
```

#### Partial Enrichment Recovery

```bash
# Reset 2D embeddings
cd embedding-enrichment
python reset_umap_environment.py

# Restart enrichment
python main.py
```

## Scripts Reference

### Core Ingestion Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `openalex_test_ingestion.sh` | Test ingestion with 2 specific files | `./openalex_test_ingestion.sh` |
| `openalex_incremental_files.sh` | Main file-based ingestion with tracking | `./openalex_incremental_files.sh [options]` |

### Support Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `openalex_metadata_patch_final.sh` | Patch metadata for existing papers | `./openalex_metadata_patch_final.sh` |
| `check_openalex_ingestion_status.sh` | Check ingestion status and progress | `./check_openalex_ingestion_status.sh` |

### Service Management

| Script | Purpose | Usage |
|--------|---------|-------|
| `startup.sh` | Start all services | `./startup.sh --with-enrichment --background` |
| `stop_services.sh` | Stop all services | `./stop_services.sh` |

### Command Line Options

#### openalex_incremental_files.sh

```bash
./openalex_incremental_files.sh [OPTIONS]

Options:
  --earliest-date DATE    Start date for file processing (default: 2025-01-01)
  --max-files N           Maximum files to process (default: 10)
  --dry-run              Simulate ingestion without database changes
  --retry-failed         Retry files that previously failed
```

#### openalex_test_ingestion.sh

```bash
./openalex_test_ingestion.sh

# No options - processes exactly 2 test files
```

## Production Deployment

### Server Setup

1. **Database**: Ensure PostgreSQL with pgvector is installed
2. **Python Environment**: Set up virtual environment with all dependencies
3. **Storage**: Ensure sufficient disk space (~50GB)
4. **Monitoring**: Set up log rotation and monitoring

### Automated Scheduling

For production, consider setting up cron jobs:

```bash
# Daily incremental updates at 2 AM
0 2 * * * /path/to/project/openalex_incremental_files.sh

# Weekly full enrichment run
0 3 * * 0 /path/to/project/startup.sh --with-enrichment --background
```

### Backup Strategy

```bash
# Database backup
pg_dump -h localhost -U tgulden -d doctrove > backup_$(date +%Y%m%d).sql

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz *.sh *.py config/
```

## Performance Optimization

### Parallel Processing (Updated)

For high-performance environments, use Python’s `ProcessPoolExecutor` to run multiple ingestion processes in parallel, as shown above. Adjust the number of parallel processes based on available CPU and memory.

### Batch Size Optimization

Adjust batch sizes in the Python ingester as needed for your environment.

---

## Design Principles and Testability

- All ingestion logic is written in a functional style for reliability and maintainability.
- All pure functions are unit tested (see `test_openalex_ingester.py`).
- The ingestion framework is designed for code reuse and easy extension to new data sources.

---

## Conclusion

This guide provides a complete reference for OpenAlex ingestion in the DocScope/DocTrove system. The process is designed to be robust, scalable, and maintainable for production use.

For questions or issues, refer to the troubleshooting section or check the project's issue tracker. 