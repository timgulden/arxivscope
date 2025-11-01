# Root Scripts - Moved from Project Root

## ⚠️ IMPORTANT WARNINGS

These scripts were originally designed to run from the **project root directory** (`arxivscope-back-end/`). Moving them here may cause **path and import issues**.

## Before Running These Scripts

1. **Check Import Paths**: Scripts may have hardcoded relative imports that expect to run from root
2. **Verify Dependencies**: Some scripts may reference files or modules that are no longer accessible
3. **Test in Isolation**: Run with small datasets first to identify any path issues
4. **Check Logs**: Monitor for import errors or missing file references

## Common Issues

- **Import Errors**: `ModuleNotFoundError` or `ImportError` due to changed relative paths
- **File Not Found**: Scripts looking for configuration files in wrong locations
- **Database Connection**: Connection strings may reference incorrect paths
- **Output Paths**: Generated files may be created in unexpected locations

## Recommended Approach

1. **Run from Project Root**: `cd /path/to/arxivscope-back-end && python doc-ingestor/ROOT_SCRIPTS/script.py`
2. **Fix Import Paths**: Update any hardcoded relative imports
3. **Update File References**: Ensure all file paths are correct
4. **Test Thoroughly**: Verify functionality before production use

## Scripts in This Directory

- `marc_ingester.py` - MARC data ingestion
- `marc_to_json.py` - MARC to JSON conversion  
- `openalex_ingester.py` - OpenAlex ingestion
- `openalex_streaming_ingestion.py` - Streaming ingestion
- `openalex_details_enrichment.py` - OpenAlex enrichment
- `openalex_details_enrichment_functional.py` - Functional enrichment
- `shared_ingestion_framework.py` - Shared framework

## Last Updated

Moved from project root on $(date)

