# 2025-09-03 Cleanup - Deprecated Files

## Overview
This folder contains files that were moved from the main `embedding-enrichment/` directory on September 3, 2025, as part of a cleanup effort to reduce confusion about which scripts are part of the current production workflow.

## Why This Cleanup Was Needed
During development of the 2D embedding processing system, we created many experimental scripts, debugging tools, and alternative approaches. This led to confusion about which scripts were actually part of the production workflow.

## Current Production Workflow (After Cleanup)
- **1D Process**: `event_listener_functional.py` → `embedding_service.py`
- **2D Process**: `queue_2d_worker.py` (fast standalone, 100 papers/sec)
- **Future 2D Process**: `event_listener_2d.py` + `functional_embedding_2d_enrichment.py` (needs fixing)

## Files Moved to This Folder

### Abandoned 2D Processing Scripts
- `functional_2d_processor.py` - Direct query approach, gets stuck at high IDs
- `functional_2d_processor_backup.py` - Backup of functional processor
- `umap_2d_embedding_service.py` - Legacy service approach
- `combined_2d_processor.py` - Experimental combined approach
- `event_listener_2d_simple.py` - Simplified event listener (unused)

### Debugging Scripts
- `debug_2d_issue.py` - Debugging script
- `systematic_2d_debug.py` - Systematic debugging
- `simple_test.py` - Simple test script

### Unused Processing Scripts
- `run_2d_incremental.py` - Incremental processing
- `run_functional_2d_continuous.py` - Continuous functional processing
- `run_functional_2d_service.py` - Functional service runner
- `run_functional_2d_tests.py` - Test runner

### Unused Database Scripts
- `add_queue_columns.sql` - Queue column definitions (not applied)
- `create_2d_queue.sql` - Queue table creation (not used)
- `create_2d_index.sql` - Index creation scripts
- `create_hnsw_index.sql` - HNSW index creation

### Performance Testing Scripts
- `test_2d_performance.py` - Performance testing
- `test_improved_2d_performance.py` - Improved performance testing
- `test_real_save.py` - Real save testing
- `test_db_save.py` - Database save testing

### Monitoring Scripts
- `quick_progress_check.py` - Quick progress checks
- `hybrid_progress_check.py` - Hybrid progress checks
- `accurate_progress_check.py` - Accurate progress checks
- `simple_progress_check.py` - Simple progress checks
- `manual_progress_check.py` - Manual progress checks
- `ultra_simple_progress.py` - Ultra simple progress
- `real_progress_tracker.py` - Real progress tracker
- `simple_progress_tracker.py` - Simple progress tracker

### Progress Reports
- `complete_progress_report.txt` - Complete progress report
- `2d_progress_report.txt` - 2D progress report
- `event_listener_progress_report.txt` - Event listener progress report
- `real_token_analysis_report.txt` - Real token analysis report
- `real_progress_history.json` - Real progress history
- `real_progress_report.txt` - Real progress report
- `progress_report.txt` - Progress report
- `progress_history.json` - Progress history
- `embedding_progress_history.json` - Embedding progress history
- `embedding_progress_report.txt` - Embedding progress report

## Key Discovery During Cleanup
We discovered that we had been running the wrong script initially:
- **Wrong**: `functional_2d_processor.py` (direct query, gets stuck at high IDs)
- **Right**: `queue_2d_worker.py` (queue-based, 100 papers/sec)

The queue-based approach is 12x faster and more robust than the direct query approach.

## Files Kept in Main Directory
After cleanup, the main directory contains only:
- **Active production scripts** (3 files)
- **Future production scripts** (2 files)
- **Essential testing scripts** (3 files)
- **Essential monitoring scripts** (3 files)
- **Essential utility scripts** (2 files)
- **Documentation files** (multiple)

## Recovery Instructions
If you need to recover any of these files:
1. They are preserved in this folder
2. Check the file modification dates to understand when they were last used
3. Review the original `FILES_TO_DEPRECATE.md` for detailed explanations
4. Most files are experimental or debugging tools that are no longer needed

## Future Cleanups
This cleanup approach can be repeated in the future by:
1. Creating a new dated subfolder (e.g., `2025-XX-XX-cleanup`)
2. Moving unused files to the new folder
3. Creating a README explaining what was moved and why
4. Updating the main documentation to reflect the current state

---
*Cleanup performed on September 3, 2025*
*Total files moved: 40+ files*
*Main directory reduced from 80+ files to 13 essential files*
















