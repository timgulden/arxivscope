# Files to Move to DEPRECATED Folder

## Overview
These files are not part of the current production workflow and should be moved to the DEPRECATED folder to reduce confusion.

## Current Production Workflow
- **1D Process**: `event_listener_functional.py` → `embedding_service.py`
- **2D Process**: `queue_2d_worker.py` (fast standalone)
- **Future 2D Process**: `event_listener_2d.py` + `functional_embedding_2d_enrichment.py` (needs fixing)

## Files to Move to DEPRECATED

### Abandoned 2D Processing Scripts
- `functional_2d_processor.py` - Direct query approach, gets stuck at high IDs
- `functional_2d_processor_backup.py` - Backup of functional processor
- `umap_2d_embedding_service.py` - Legacy service approach
- `combined_2d_processor.py` - Experimental combined approach
- `event_listener_2d_simple.py` - Simplified event listener (unused)

### Abandoned Event Listeners
- `event_listener_original.py` - Original event listener (already in DEPRECATED)
- `event_listener_fast.py` - Fast event listener (already in DEPRECATED)

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

### Performance Testing Scripts (Keep for Reference)
- `test_2d_performance.py` - Performance testing
- `test_improved_2d_performance.py` - Improved performance testing
- `test_real_save.py` - Real save testing
- `test_db_save.py` - Database save testing

### Monitoring Scripts (Keep for Reference)
- `quick_progress_check.py` - Quick progress checks
- `hybrid_progress_check.py` - Hybrid progress checks
- `accurate_progress_check.py` - Accurate progress checks
- `simple_progress_check.py` - Simple progress checks
- `manual_progress_check.py` - Manual progress checks
- `ultra_simple_progress.py` - Ultra simple progress
- `real_progress_tracker.py` - Real progress tracker
- `simple_progress_tracker.py` - Simple progress tracker

### Progress Reports (Keep for Reference)
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

## Files to Keep in Main Directory

### Active Production Scripts
- `queue_2d_worker.py` - ✅ **ACTIVE** - Fast standalone 2D processing
- `event_listener_functional.py` - ✅ **ACTIVE** - 1D embedding event listener
- `embedding_service.py` - ✅ **ACTIVE** - 1D embedding generation service

### Future Production Scripts
- `event_listener_2d.py` - ❌ **BROKEN** - Slow database-driven 2D processing (needs fixing)
- `functional_embedding_2d_enrichment.py` - ✅ **READY** - Pure functional module for event listener

### Testing Scripts
- `test_functional_enrichment.py` - ✅ **READY** - Tests for functional enrichment
- `test_functional_2d_processor.py` - ✅ **READY** - Tests for functional processor
- `test_event_listener_functional.py` - ✅ **READY** - Tests for event listener

### Monitoring Scripts
- `monitor_2d_progress.py` - ✅ **READY** - 2D progress monitoring
- `monitor_embedding_progress.py` - ✅ **READY** - Overall embedding progress
- `monitor_event_listener.py` - ✅ **READY** - Event listener monitoring

### Utility Scripts
- `check_embedding_status.py` - ✅ **READY** - Embedding status check
- `clear_embeddings.py` - ✅ **READY** - Clear embeddings utility

## Move Command
```bash
# Create DEPRECATED directory with today's date subfolder
mkdir -p DEPRECATED/2025-09-03-cleanup

# Move abandoned scripts
mv functional_2d_processor.py DEPRECATED/2025-09-03-cleanup/
mv functional_2d_processor_backup.py DEPRECATED/2025-09-03-cleanup/
mv umap_2d_embedding_service.py DEPRECATED/2025-09-03-cleanup/
mv combined_2d_processor.py DEPRECATED/2025-09-03-cleanup/
mv event_listener_2d_simple.py DEPRECATED/2025-09-03-cleanup/

# Move debugging scripts
mv debug_2d_issue.py DEPRECATED/2025-09-03-cleanup/
mv systematic_2d_debug.py DEPRECATED/2025-09-03-cleanup/
mv simple_test.py DEPRECATED/2025-09-03-cleanup/

# Move unused processing scripts
mv run_2d_incremental.py DEPRECATED/2025-09-03-cleanup/
mv run_functional_2d_continuous.py DEPRECATED/2025-09-03-cleanup/
mv run_functional_2d_service.py DEPRECATED/2025-09-03-cleanup/
mv run_functional_2d_tests.py DEPRECATED/2025-09-03-cleanup/

# Move unused database scripts
mv add_queue_columns.sql DEPRECATED/2025-09-03-cleanup/
mv create_2d_queue.sql DEPRECATED/2025-09-03-cleanup/
mv create_2d_index.sql DEPRECATED/2025-09-03-cleanup/
mv create_hnsw_index.sql DEPRECATED/2025-09-03-cleanup/

# Move performance testing scripts
mv test_2d_performance.py DEPRECATED/2025-09-03-cleanup/
mv test_improved_2d_performance.py DEPRECATED/2025-09-03-cleanup/
mv test_real_save.py DEPRECATED/2025-09-03-cleanup/
mv test_db_save.py DEPRECATED/2025-09-03-cleanup/

# Move monitoring scripts
mv quick_progress_check.py DEPRECATED/2025-09-03-cleanup/
mv hybrid_progress_check.py DEPRECATED/2025-09-03-cleanup/
mv accurate_progress_check.py DEPRECATED/2025-09-03-cleanup/
mv simple_progress_check.py DEPRECATED/2025-09-03-cleanup/
mv manual_progress_check.py DEPRECATED/2025-09-03-cleanup/
mv ultra_simple_progress.py DEPRECATED/2025-09-03-cleanup/
mv real_progress_tracker.py DEPRECATED/2025-09-03-cleanup/
mv simple_progress_tracker.py DEPRECATED/2025-09-03-cleanup/

# Move progress reports
mv complete_progress_report.txt DEPRECATED/2025-09-03-cleanup/
mv 2d_progress_report.txt DEPRECATED/2025-09-03-cleanup/
mv event_listener_progress_report.txt DEPRECATED/2025-09-03-cleanup/
mv real_token_analysis_report.txt DEPRECATED/2025-09-03-cleanup/
mv real_progress_history.json DEPRECATED/2025-09-03-cleanup/
mv real_progress_report.txt DEPRECATED/2025-09-03-cleanup/
mv progress_report.txt DEPRECATED/2025-09-03-cleanup/
mv progress_history.json DEPRECATED/2025-09-03-cleanup/
mv embedding_progress_history.json DEPRECATED/2025-09-03-cleanup/
mv embedding_progress_report.txt DEPRECATED/2025-09-03-cleanup/
```

## Result
After moving these files, the main directory will contain only:
- **Active production scripts** (3 files)
- **Future production scripts** (2 files)
- **Essential testing scripts** (3 files)
- **Essential monitoring scripts** (3 files)
- **Essential utility scripts** (2 files)
- **Documentation files** (multiple)

This will make the workflow much clearer and reduce confusion about which scripts are actually part of the production system.

## README for Cleanup Folder
A README file has been created at `DEPRECATED/2025-09-03-cleanup/README.md` that explains:
- Why the cleanup was needed
- What files were moved and why
- The current production workflow
- Recovery instructions for future reference
- Key discoveries made during the cleanup process
