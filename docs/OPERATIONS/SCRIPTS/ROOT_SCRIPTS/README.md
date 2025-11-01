# Root Analysis Scripts - Moved from Project Root

## ⚠️ IMPORTANT WARNINGS

These analysis and utility scripts were originally designed to run from the **project root directory** (`arxivscope-back-end/`). Moving them here may cause **path and import issues**.

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

1. **Run from Project Root**: `cd /path/to/arxivscope-back-end && python docs/OPERATIONS/SCRIPTS/ROOT_SCRIPTS/script.py`
2. **Fix Import Paths**: Update any hardcoded relative imports
3. **Update File References**: Ensure all file paths are correct
4. **Test Thoroughly**: Verify functionality before production use

## Scripts in This Directory

### Analysis Scripts
- `find_institutional_papers.py` - Institutional paper analysis
- `simple_author_analysis.py` - Author analysis
- `check_pickle_data.py` - Data checking utility
- `check_data_sizes.py` - Data size analysis

### Shell Scripts
- `stream_logs.sh` - Log streaming
- `start_docscope.sh` - DocScope startup
- `openalex_incremental_files.sh` - OpenAlex incremental processing
- `run_title_cleaning.sh` - Title cleaning
- `cleanup_openalex_comprehensive.sh` - OpenAlex cleanup
- `cleanup_openalex_fresh_start.sh` - Fresh start cleanup
- `openalex_metadata_patch_optimized.sh` - Metadata patching
- `openalex_metadata_patch_final.sh` - Final metadata patch
- `deploy_openalex_fixes.sh` - OpenAlex fixes deployment
- `run_incremental_sync.sh` - Incremental synchronization
- `run_cleanup_visible.sh` - Visible cleanup
- `check_openalex_ingestion_status.sh` - Ingestion status check

## Last Updated

Moved from project root on $(date)

