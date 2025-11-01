# Root Utility Scripts - Moved from Project Root

## ⚠️ IMPORTANT WARNINGS

These utility scripts were originally designed to run from the **project root directory** (`arxivscope-back-end/`). Moving them here may cause **path and import issues**.

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

1. **Run from Project Root**: `cd /path/to/arxivscope-back-end && python scripts/ROOT_SCRIPTS/script.py`
2. **Fix Import Paths**: Update any hardcoded relative imports
3. **Update File References**: Ensure all file paths are correct
4. **Test Thoroughly**: Verify functionality before production use

## Scripts in This Directory

### Utility Scripts
- `migrate_code_standardization.sh` - Code standardization migration
- `consolidate_workspace.sh` - Workspace consolidation
- `fix_database_setup.sh` - Database setup fixes
- `server-setup.sh` - Server setup
- `azure-deploy.sh` - Azure deployment
- `setup_accs_amazon_linux.sh` - Amazon Linux setup
- `monitoring-setup.sh` - Monitoring setup
- `remote_debug_setup.sh` - Remote debug setup

### Service Management
- `startup.sh` - Main startup script
- `startup_debug.sh` - Debug startup script
- `stop_services.sh` - Service stopping
- `start_api.sh` - API startup
- `check_services.sh` - Service health check
- `check_remote_health.sh` - Remote health check

### Testing Scripts
- `run_fast_tests.sh` - Fast test execution

## Last Updated

Moved from project root on $(date)

