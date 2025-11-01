# OpenAlex Details Enrichment Processing Guide

## Overview

This document describes the trigger-based enrichment system for extracting detailed metadata from OpenAlex papers (journal names, citations, topics, institutions, etc.).

## Architecture

### Trigger-Based Queue System

**When a new OpenAlex paper is ingested:**
1. Database trigger fires on INSERT to `doctrove_papers`
2. Paper is queued in `enrichment_queue` with type `openalex_details`
3. Background workers process the queue automatically
4. Details are stored in `openalex_details_enrichment` table

### Components

#### 1. Database Trigger
- **File**: `embedding-enrichment/setup_openalex_details_trigger.sql`
- **Function**: `queue_openalex_details_enrichment()`
- **Trigger**: `trigger_queue_openalex_details`
- **Action**: Queues new OpenAlex papers automatically

#### 2. Backlog Processor (For Processing Existing Papers)
- **File**: `embedding-enrichment/openalex_details_backlog_processor.py`
- **Purpose**: Fast processing of existing papers with raw data
- **Method**: Reads directly from `openalex_metadata` using UUID ranges
- **Performance**: ~500-600 papers/sec per worker
- **Parallel**: Supports multiple workers with `--worker-id`

#### 3. Queue Worker (For Real-time Processing)
- **File**: `embedding-enrichment/queue_openalex_details_worker.py`
- **Purpose**: Process papers queued by database triggers
- **Method**: Polls `enrichment_queue` table
- **Use**: After backlog is cleared, for ongoing real-time processing

## Enrichment Types

### Vector Embeddings
- **Purpose**: Generate 1536-dimensional semantic embeddings for similarity search
- **Model**: OpenAI text-embedding-3-small
- **Queue Type**: `embedding_generation`
- **Processing**: Automatic via database triggers

### 2D Projections (UMAP)
- **Purpose**: Project high-dimensional embeddings to 2D for visualization
- **Method**: UMAP dimensionality reduction
- **Queue Type**: `embedding_2d`
- **Dependency**: Requires vector embeddings to be generated first

### OpenAlex Details
- **Purpose**: Extract metadata from raw OpenAlex JSON
- **Fields**: Journal names, citations, topics, institutions, etc.
- **Queue Type**: `openalex_details`
- **Source**: Papers with `openalex_raw_data` field populated

## Current Processing Status (Oct 9, 2025)

### Backlog Processing
- **Total OpenAlex papers**: 17,785,865
- **Papers enriched**: ~1.8M (10%)
- **Papers remaining**: ~16M
- **Workers running**: 4 parallel workers
- **Combined rate**: ~2,304 papers/sec
- **ETA**: ~2 hours to complete

### Performance Metrics (Per Worker)
- **Batch size**: 20,000 papers
- **Fetch time**: ~14s (ORDER BY for progress tracking)
- **Process time**: ~2-4s (extracting from JSON)
- **Insert time**: ~20s (bulk insert with ON CONFLICT)
- **Total**: ~40s per batch
- **Rate**: ~500-600 papers/sec

## Running the Backlog Processor

### Start Single Worker
```bash
cd /opt/arxivscope/embedding-enrichment
screen -dmS openalex_backlog \
    /opt/arxivscope/arxivscope/bin/python \
    openalex_details_backlog_processor.py \
    --batch-size 20000 \
    --worker-id main
```

### Start Multiple Parallel Workers (Recommended for Backlog)
```bash
# Start 4 workers for 4x speedup
for i in {1..4}; do
    cd /opt/arxivscope/embedding-enrichment
    screen -dmS openalex_backlog_$i \
        /opt/arxivscope/arxivscope/bin/python \
        openalex_details_backlog_processor.py \
        --batch-size 20000 \
        --worker-id worker$i
    sleep 1
done
```

### Monitor Progress
```bash
# View logs for a specific worker
screen -r openalex_backlog_1
# Press Ctrl+A then D to detach

# Check enrichment count
cd /opt/arxivscope/doctrove-api && python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM openalex_details_enrichment')
print(f'Enriched: {cur.fetchone()[0]:,}')
"

# Check all workers at once
for i in {1..4}; do 
    echo "Worker $i:" 
    screen -S openalex_backlog_$i -X hardcopy /tmp/w$i.log 2>/dev/null
    tail -3 /tmp/w$i.log 2>&1 | strings | grep "Overall rate" | tail -1
done
```

### Stop All Workers
```bash
# Stop all backlog workers
for i in {1..4}; do
    screen -S openalex_backlog_$i -X quit 2>/dev/null
done

# Or kill processes directly
pkill -f openalex_details_backlog_processor
```

## State Files and Resume Capability

Each worker maintains its own state file:
- **Location**: `/tmp/openalex_backlog_{worker_id}_last_uuid.txt`
- **Content**: Last processed UUID (e.g., `03f4a2b1-1234-5678-abcd-ef0123456789`)
- **Purpose**: Workers can resume from where they left off after restart

**To reset a worker's progress:**
```bash
rm /tmp/openalex_backlog_worker1_last_uuid.txt
# Worker will start from beginning on next run
```

## Performance Optimizations Applied

### 1. Removed ORDER BY from Initial Queries
- Saves time but made it hard to track progress
- **Reverted**: Kept ORDER BY for reliable progress tracking

### 2. UUID Range Tracking
- Each worker tracks last processed UUID
- Ensures coverage of entire dataset
- Workers don't duplicate work

### 3. Single Table SELECT (No JOIN)
- Reads directly from `openalex_metadata`
- Uses `ON CONFLICT DO NOTHING` in insert to skip duplicates
- Much faster than LEFT JOIN to check what's processed

### 4. Removed Expensive COUNT Queries
- No table scans for statistics after each batch
- Removed from original batch script (caused 16s delays)

### 5. Partial Index on Queue
- `idx_queue_pending_openalex_details` for queue-based processing
- Speeds up queue polling (when used instead of backlog processor)

### 6. Parallel Processing
- 4 workers with staggered UUID starting points
- Linear speedup (4x faster)
- No lock contention (each works on different UUID ranges)

## Database Schema

### openalex_details_enrichment Table

Stores extracted details from OpenAlex raw JSON:

**Key Fields:**
- `source_name` - Journal name (e.g., "Nature", "Science")
- `source_type` - Type (journal, repository, conference)
- `source_publisher` - Publisher name
- `cited_by_count` - Citation count
- `fwci` - Field-weighted citation impact
- `primary_topic_name` - Main topic
- `best_author_country` - Country of primary author
- `best_author_institution` - Primary author institution
- Many more fields (see table definition in enrichment script)

**Total Columns**: ~60 fields extracted from OpenAlex JSON

## Switching Between Backlog and Queue Processing

### For Large Backlogs (Current Situation)
**Use**: `openalex_details_backlog_processor.py`
- Processes directly from `openalex_metadata`
- Fast UUID range scanning
- Supports parallel workers
- Best for bulk processing

### For Real-time Processing (After Backlog Complete)
**Use**: `queue_openalex_details_worker.py`
- Processes from `enrichment_queue`
- Responds to database triggers
- Single worker sufficient for normal ingestion rates
- Automatic processing as new papers arrive

## Integration with React UI

Once backlog processing is complete, the enriched fields will be available for:
- Custom Universe Filter queries (e.g., "papers from Nature journal")
- Symbolization by journal, publisher, topic, etc.
- Filtering by citation counts, impact metrics

**Next Steps:**
1. Add fields to `DATABASE_SCHEMA.md` documentation
2. Add field mappings to `business_logic.py` in API
3. Update React schema display in Custom Universe Modal

## Performance Impact on Frontend

### With Backlog Processing Running (4 workers)
- **React app load time**: ~3-4 seconds ✅
- **API response time**: ~3-4 seconds ✅
- **Minimal impact**: Queue-based approach avoids expensive COUNT queries

### Best Practices
- Run backlog processing during development (minimal impact)
- Monitor with `screen -r` to view logs
- Can pause anytime and resume later
- Frontend remains responsive throughout

## Monitoring Commands

```bash
# List all workers
screen -ls | grep openalex

# Check enrichment progress
cd /opt/arxivscope/doctrove-api && python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM openalex_details_enrichment')
enriched = cur.fetchone()[0]
total = 17785865
print(f'Progress: {enriched:,} / {total:,} ({enriched/total*100:.1f}%)')
print(f'Remaining: {total-enriched:,}')
"

# Check sample enriched data
cd /opt/arxivscope/doctrove-api && python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
cur.execute('''
    SELECT source_name, source_type, cited_by_count, primary_topic_name
    FROM openalex_details_enrichment
    WHERE source_name IS NOT NULL
    LIMIT 5
''')
print('Sample enriched data:')
for row in cur.fetchall():
    print(f'  {row[0]} ({row[1]}) - {row[2]} citations - {row[3]}')
"

# View live logs
screen -r openalex_backlog_1
# Ctrl+A then D to detach
```

## Troubleshooting

### Workers Stopped Unexpectedly
```bash
# Check if workers are running
ps aux | grep openalex_details_backlog_processor

# Restart workers
cd /opt/arxivscope/embedding-enrichment
for i in {1..4}; do
    screen -dmS openalex_backlog_$i \
        /opt/arxivscope/arxivscope/bin/python \
        openalex_details_backlog_processor.py \
        --batch-size 20000 \
        --worker-id worker$i
done
```

### Check for Errors
```bash
# View worker logs
cat /tmp/backlog_1.log
cat /tmp/backlog_2.log
cat /tmp/backlog_3.log
cat /tmp/backlog_4.log
```

### Database Performance Issues
```bash
# Check active queries
cd /opt/arxivscope/doctrove-api && python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
cur.execute('''
    SELECT pid, now() - query_start as duration, query
    FROM pg_stat_activity
    WHERE state = '\''active'\''
    ORDER BY duration DESC
    LIMIT 5
''')
for row in cur.fetchall():
    print(f'PID {row[0]}: {row[1]} - {row[2][:60]}...')
"
```

## After Backlog Completion

Once all 17.7M papers are processed:

1. **Stop backlog workers:**
   ```bash
   for i in {1..4}; do screen -S openalex_backlog_$i -X quit; done
   ```

2. **Start queue worker for real-time processing:**
   ```bash
   # This will be included in START_SERVICES.sh
   screen -dmS openalex_details \
       /opt/arxivscope/arxivscope/bin/python \
       queue_openalex_details_worker.py \
       --batch-size 1000 \
       --sleep 10
   ```

3. **New papers will be automatically enriched** via database triggers

## Summary

The OpenAlex details enrichment is now fully automated with:
- ✅ Database triggers for new papers
- ✅ Fast backlog processing (4 parallel workers)
- ✅ Minimal frontend impact (~3s load time)
- ✅ Resume capability (state files track progress)
- ✅ Comprehensive logging and monitoring
- ✅ Production-ready error handling

Expected completion: **~2 hours** from start time (Oct 9, 2025 ~2:50 PM)

