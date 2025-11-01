# DocTrove Doc-Ingestor

This service ingests documents from various sources (pickle files, CSV, APIs, bulk metadata) and inserts them into the `doctrove_papers` table in PostgreSQL. It is designed to be modular and extensible for future data sources.

## Available Ingesters

### 1. arXiv Bulk Ingester (✅ RECOMMENDED - Production Ready)

**Ingest arXiv papers from bulk metadata snapshot (2.8M papers successfully tested):**

```bash
# Full ingestion (all ~2.8M papers)
python arxiv_bulk_ingester.py --file /path/to/arxiv-metadata-oai-snapshot.json

# Test with limited papers
python arxiv_bulk_ingester.py --file /path/to/arxiv-metadata-oai-snapshot.json --limit 100

# Filter by year
python arxiv_bulk_ingester.py --file /path/to/arxiv-metadata-oai-snapshot.json --start-year 2024

# Filter by date range
python arxiv_bulk_ingester.py --file /path/to/arxiv-metadata-oai-snapshot.json \
    --start-date 2024-01-01 --end-date 2024-12-31

# Filter by categories (AI/ML only)
python arxiv_bulk_ingester.py --file /path/to/arxiv-metadata-oai-snapshot.json \
    --categories cs.AI cs.LG cs.CL cs.CV
```

**Features:**
- ✅ High performance: ~897 papers/second
- ✅ Batch processing: 5000 papers per batch
- ✅ Duplicate handling: `ON CONFLICT DO NOTHING`
- ✅ Automatic enrichment: Triggers vector embeddings + 2D projections
- ✅ Progress tracking: Real-time logging
- ✅ Error handling: 0.3% error rate (very robust)

**Data Source:** 
- Kaggle: https://www.kaggle.com/datasets/Cornell-University/arxiv
- File: `arxiv-metadata-oai-snapshot.json` (~4GB uncompressed)

### 2. OpenAlex Ingester

**Ingest papers from OpenAlex S3 snapshots:**

```bash
cd ROOT_SCRIPTS
python openalex_ingester.py --date 2025-01-15 --limit 1000
```

**Note:** OpenAlex coverage is strong for 2010-2017 but limited for 2018-2025.

### 3. Legacy Pickle/JSON Ingester

**For legacy datasets (AiPickle, custom formats):**

```bash
# Basic usage with defaults (AiPickle dataset)
python main.py

# Ingest with limit for testing
python main.py --source aipickle --limit 20

# Ingest from custom file
python main.py --source custom --file-path /path/to/your/data.pkl --limit 100
```

**Arguments:**
- `--source`: Source name for the data (default: 'aipickle')
- `--file-path`: Path to data file (supports .pkl, .pickle, .json)
- `--limit`: Limit number of papers to ingest (optional)

## Configuration
- Configure database connection in `config.py` or via environment variables.
- The service automatically creates source-specific metadata tables based on the data structure.

## Architecture
- Uses interceptor pattern with dependency injection for functional programming approach
- Batch processing for efficient database insertion
- Automatic metadata table creation based on data structure
- Integration with event-driven enrichment system

## Current Data Sources (October 2025)

**Successfully Ingested:**
- ✅ **arXiv:** 2.8M papers (1986-2025) - Primary current research source
- ✅ **OpenAlex:** 17.7M papers (2010-2017 strong) - Historical research baseline
- ✅ **Total:** ~20.5M papers in database

**Enrichment Status:**
- ✅ Automatic vector embeddings (1536-d) via OpenAI API
- ✅ Automatic 2D projections via UMAP
- ✅ Trigger-based enrichment queue system

## Future Extensions
- 📋 PubMed ingester for biomedical research
- 📋 Semantic Scholar API integration
- 📋 Periodic arXiv updates (weekly/monthly)
- 📋 REST API interface for ingestion jobs
- 📋 Web UI for monitoring ingestion progress

## Documentation

- **[ARXIV_INGESTION_PLAN.md](../ARXIV_INGESTION_PLAN.md)** - Complete arXiv ingestion guide
- **[ENRICHMENT_PROCESSING_GUIDE.md](../ENRICHMENT_PROCESSING_GUIDE.md)** - Enrichment system documentation
- **[CONTEXT_SUMMARY.md](../CONTEXT_SUMMARY.md)** - System overview and current state 