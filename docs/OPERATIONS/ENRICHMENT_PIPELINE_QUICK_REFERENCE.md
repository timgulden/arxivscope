# Enrichment Pipeline Quick Reference

## Database-Driven Pipeline (Current Recommended)

### 1. Start Database-Driven Event Listener
```bash
cd embedding-enrichment

# Start in screen session (survives disconnections)
screen -dmS embedding_1d bash -c "python event_listener_functional.py"

# Check if running
screen -list
```

**Expected Output:**
```
Database-Driven Functional Event Listener started!
Using database functions and continuous processing...
250 records per batch, one API call per batch
Press Ctrl+C to stop
```

### 2. Monitor Processing
```bash
# View logs
tail -f enrichment.log

# Expected log format:
# Found 13,332,459 papers needing embeddings
# Processed 1,500/13,332,459 (0.01%)
# Processed 3,000/13,332,459 (0.02%)
```

### 3. Ingest Papers (Optional)
```bash
cd doc-ingestor
python main.py --source aipickle --limit 20  # Test with 20 papers
# or
python main.py --source aipickle  # Full dataset
```

### 4. Watch Automatic Processing
The database-driven event listener will automatically:
- Generate embeddings for new papers using database functions
- Process continuously (handles new ingestions automatically)
- Show progress: "Processed 15,000/13,000,000 (11.5%)"
- Run reliably in background screen session

## Manual Pipeline (For Testing/Development)

### 1. Ingest Papers
```bash
cd doc-ingestor
python main.py --source aipickle --limit 20
```

### 2. Generate Embeddings
```bash
cd embedding-enrichment
python embedding_service.py --embedding-type title --limit 20
```

### 3. Generate 2D Projections
```bash
python main.py --mode incremental --embedding-type title
```

## Service Management

### Start Services
```bash
# Start 1D embedding service
screen -dmS embedding_1d bash -c "cd /opt/arxivscope/embedding-enrichment && python event_listener_functional.py"

# Start 2D embedding service
screen -dmS functional_2d_continuous bash -c "cd /opt/arxivscope/embedding-enrichment && python run_functional_2d_continuous.py"

# Check all services
screen -list
```

### Monitor Services
```bash
# Attach to 1D service
screen -r embedding_1d

# Attach to 2D service  
screen -r functional_2d_continuous

# Detach from service (Ctrl+A, D)

# View logs
tail -f /opt/arxivscope/embedding-enrichment/enrichment.log
```

### Stop Services
```bash
# Stop specific service
screen -S embedding_1d -X quit

# Stop all embedding services
pkill -f event_listener_functional.py
pkill -f run_functional_2d_continuous.py
```

## Status Checking

### Check Paper Counts
```bash
psql -U doctrove_admin -d doctrove -h localhost -p 5434 -c "
SELECT 
    COUNT(*) as total_papers,
    COUNT(CASE WHEN doctrove_embedding IS NOT NULL THEN 1 END) as with_embeddings,
    COUNT(CASE WHEN doctrove_embedding_2d IS NOT NULL THEN 1 END) as with_2d
FROM doctrove_papers;"
```

### Check Embedding Service Status
```bash
cd embedding-enrichment
python embedding_service.py --status
```

### Check Event Listener
```bash
ps aux | grep event_listener_functional
screen -list
```

### Check Database Functions
```bash
psql -U doctrove_admin -d doctrove -h localhost -p 5434 -c "
SELECT get_papers_needing_embeddings_count() as papers_needing_1d,
       get_papers_needing_2d_embeddings_count() as papers_needing_2d;"
```

## Troubleshooting

### Event Listener Not Processing
- **Problem:** Service not running in screen session
- **Solution:** Start with `screen -dmS embedding_1d bash -c "cd /opt/arxivscope/embedding-enrichment && python event_listener_functional.py"`

### Service Disconnected
- **Problem:** Screen session detached
- **Solution:** Reattach with `screen -r embedding_1d`

### Multiple Event Listeners
- **Problem:** Multiple processes running
- **Solution:** `pkill -f event_listener_functional.py` then restart

### Database Connection Issues
- **Problem:** Connection to database failed
- **Solution:** Check database is running and credentials in `doctrove-api/config.py`

## Key Files

- **Database-Driven Event Listener:** `embedding-enrichment/event_listener_functional.py`
- **Embedding Service:** `embedding-enrichment/embedding_service.py`
- **2D Processor:** `embedding-enrichment/functional_2d_processor.py`
- **2D Service Runner:** `embedding-enrichment/run_functional_2d_continuous.py`
- **Ingestion:** `doc-ingestor/main.py`
- **Database Functions:** `embedding-enrichment/event_triggers.sql`
- **Test Suite:** `embedding-enrichment/test_event_listener_functional.py`

## Pipeline Flow

```
Ingestion → Database Functions → Database-Driven Event Listener → Embedding Generation → 2D Processing → Ready for Visualization
```

## Performance Metrics

### Current Performance
- **1D Processing**: ~7.8 seconds per 250 papers
- **2D Processing**: ~7.0 seconds per 1,000 papers  
- **Processing Rate**: ~2,500 papers/minute (1D), ~8,500 papers/minute (2D)
- **Database Updates**: Batch operations for efficiency
- **Continuous Processing**: Handles new papers automatically

### Batch Processing
- **1D Batches**: 250 papers per batch, one API call per batch
- **2D Batches**: 1,000 papers per batch, UMAP transformation per batch
- **Database Functions**: Real-time counting for progress tracking
- **Background Services**: Screen sessions for reliability 