# OpenAlex Deprecated Scripts

This folder contains OpenAlex-related scripts that are **not actively documented** in the current ingestion guides but may be useful for future reference.

## Archived Date
October 10, 2025

## Reason for Archival
As part of system refocusing on arXiv (cutting-edge research) + RAND publications, OpenAlex data (~18M papers) was removed. These scripts are archived for potential future use if large-scale OpenAlex ingestion is needed again.

## Archived Scripts

### From `doc-ingestor/ROOT_SCRIPTS/`
- **`openalex_details_enrichment.py`** - Original OpenAlex details enrichment
- **`openalex_details_enrichment_functional.py`** - Functional refactored version

### From `embedding-enrichment/`
- **`openalex_country_enrichment.py`** - Country extraction from OpenAlex institution data

## Active OpenAlex Scripts (Still in Use)

The following scripts remain active and are documented in current guides:

### In `doc-ingestor/ROOT_SCRIPTS/`
- `openalex_ingester.py` - Main ingester using shared framework
- `openalex_streaming_ingestion.py` - Streaming ingestion for updates

### In `embedding-enrichment/`
- `openalex_details_backlog_processor.py` - Backlog processor for existing papers
- `queue_openalex_details_worker.py` - Queue worker for real-time processing  
- `setup_openalex_details_trigger.sql` - Database trigger setup

## Documentation References

- **`docs/OPERATIONS/OPENALEX_INGESTION_GUIDE.md`** - Complete OpenAlex ingestion documentation
- **`ENRICHMENT_PROCESSING_GUIDE.md`** - Enrichment system documentation

## Notes

- These scripts were working at time of archival
- May require updates if used again in future
- Database schema for OpenAlex has been preserved for potential future use
- If re-ingesting OpenAlex at scale (100M+ papers), consider starting fresh with latest data format




