# Database-Driven Functional Event Listener Guide

## Overview

The Database-Driven Functional Event Listener (`event_listener_functional.py`) is a robust, continuous processing system that generates 1D embeddings for papers using functional programming principles and database-driven architecture. It's designed to handle large-scale processing (13+ million papers) with high performance and reliability.

## Architecture

### Core Design Principles

1. **Database-Driven**: Uses PostgreSQL functions for real-time paper counting
2. **Functional Programming**: Pure functions with immutable dataclasses
3. **Continuous Processing**: Always checks for new papers (like 2D system)
4. **Background Service**: Runs in screen sessions for reliability
5. **Batch Processing**: 250 papers per batch, one API call per batch

### Key Components

#### 1. Database Functions
```sql
-- Real-time paper counting
SELECT get_papers_needing_embeddings_count();

-- Returns count of papers needing 1D embeddings
```

#### 2. Functional Data Structures
```python
@dataclass(frozen=True)
class ProcessingResult:
    """Immutable processing result."""
    successful: int
    failed: int
    timestamp: float
```

#### 3. Pure Functions
- `get_papers_needing_embeddings_count_db()` - Database function wrapper
- `process_embedding_batch()` - Single batch processing
- `process_embeddings_continuously()` - Continuous processing loop

## Installation and Setup

### Prerequisites
- PostgreSQL with `pgvector` extension
- Python 3.10+
- Required packages: `psycopg2`, `numpy`, `openai`
- Database functions from `event_triggers.sql`

### Database Setup
```sql
-- Ensure database functions exist
\i embedding-enrichment/event_triggers.sql

-- Verify functions
SELECT get_papers_needing_embeddings_count();
```

### Environment Configuration
```bash
# Database connection (from doctrove-api/config.py)
DB_HOST=localhost
DB_PORT=5434
DB_NAME=doctrove
DB_USER=doctrove_admin
DB_PASSWORD=doctrove_admin
```

## Usage

### Starting the Service

#### Method 1: Screen Session (Recommended)
```bash
cd /opt/arxivscope/embedding-enrichment

# Start in detached screen session
screen -dmS embedding_1d bash -c "python event_listener_functional.py"

# Verify it's running
screen -list
```

#### Method 2: Direct Execution
```bash
cd /opt/arxivscope/embedding-enrichment
python event_listener_functional.py
```

### Monitoring

#### View Logs
```bash
# Real-time log monitoring
tail -f enrichment.log

# Expected output format:
# 2025-09-01 23:31:29,905 - Found 13,332,459 papers needing embeddings
# 2025-09-01 23:31:38,844 - Processed 1,500/13,332,459 (0.01%)
# 2025-09-01 23:31:47,261 - Processed 3,000/13,332,459 (0.02%)
```

#### Attach to Screen Session
```bash
# Attach to service for direct monitoring
screen -r embedding_1d

# Detach (Ctrl+A, D)
```

#### Check Service Status
```bash
# Check if process is running
ps aux | grep event_listener_functional

# Check screen sessions
screen -list

# Check database progress
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "
SELECT COUNT(*) as total_papers,
       COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings,
       COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_2d
FROM doctrove_papers;"
```

### Stopping the Service

#### Method 1: Screen Session
```bash
# Stop specific session
screen -S embedding_1d -X quit

# Or attach and use Ctrl+C
screen -r embedding_1d
# Then Ctrl+C to stop
```

#### Method 2: Process Kill
```bash
pkill -f event_listener_functional.py
```

## Performance

### Current Metrics
- **Batch Size**: 250 papers per batch
- **Batch Time**: 7.5-8.5 seconds per batch
- **Processing Rate**: ~2,500 papers/minute
- **API Calls**: One per batch (250 papers)
- **Database Updates**: Batch operations using `executemany()`

### Performance Breakdown
```
Total: 7.8s
├── API (Embedding Generation): 4.4s (56%)
├── Database Updates: 2.8s (36%)  
└── Paper Fetching: 0.1s (1%)
```

### Optimization Features
1. **Database Index**: `idx_doctrove_embedding_null` for fast paper fetching
2. **Batch Updates**: Single `executemany()` call per batch
3. **Database Functions**: Optimized counting queries
4. **Continuous Processing**: No restart needed for new papers

## Integration with 2D System

### Automatic Flow
```
1D Embeddings → 2D Embeddings → Ready for Visualization
```

### Service Coordination
- **1D Service**: `embedding_1d` screen session
- **2D Service**: `functional_2d_continuous` screen session
- **Database**: Both services use database functions for real-time counts

### Monitoring Both Services
```bash
# Check all embedding services
screen -list

# Expected output:
# There are screens on:
#         4008810.embedding_1d    (09/01/25 23:30:49)     (Detached)
#         3960701.functional_2d_continuous        (09/01/25 21:56:54)     (Detached)

# Monitor both logs
tail -f enrichment.log  # 1D service
tail -f functional_2d_processor.log  # 2D service
```

## Testing

### Run Test Suite
```bash
cd /opt/arxivscope/embedding-enrichment
python -m pytest test_event_listener_functional.py -v
```

### Test Coverage
- **12 comprehensive tests** covering all functionality
- **Functional programming validation**
- **Database function testing**
- **Continuous processing testing**
- **Mock-based testing** for reliability

### Manual Testing
```bash
# Test single batch processing
python -c "from embedding_service import process_embedding_enrichment; result = process_embedding_enrichment(batch_size=250, limit=250); print('Result:', result)"

# Test database function
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "SELECT get_papers_needing_embeddings_count();"
```

## Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check database connection
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "SELECT 1;"

# Check Python dependencies
python -c "import psycopg2, openai, numpy; print('Dependencies OK')"
```

#### Service Stopped Unexpectedly
```bash
# Check logs for errors
tail -50 enrichment.log

# Restart service
screen -dmS embedding_1d bash -c "cd /opt/arxivscope/embedding-enrichment && python event_listener_functional.py"
```

#### No Progress
```bash
# Check if papers need processing
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "SELECT get_papers_needing_embeddings_count();"

# Check if service is processing
tail -f enrichment.log
```

#### Database Connection Issues
```bash
# Verify database is running
ps aux | grep postgres

# Check credentials in doctrove-api/config.py
cat ../doctrove-api/config.py
```

### Performance Issues

#### Slow Processing
```bash
# Check database indexes
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "\d+ doctrove_papers"

# Look for idx_doctrove_embedding_null index
```

#### High Memory Usage
```bash
# Check memory usage
ps aux | grep event_listener_functional

# Restart service if needed
pkill -f event_listener_functional.py
screen -dmS embedding_1d bash -c "cd /opt/arxivscope/embedding-enrichment && python event_listener_functional.py"
```

## Configuration

### Batch Size
```python
# In event_listener_functional.py
class FunctionalEventListener:
    def __init__(self, batch_size: int = 250):  # Configurable batch size
```

### Sleep Intervals
```python
# Between processing cycles
time.sleep(30)  # 30 seconds between cycles

# Between batches
time.sleep(1)   # 1 second between batches
```

### Logging
```python
# Log level and format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enrichment.log'),
        logging.StreamHandler()
    ]
)
```

## Future Enhancements

### Planned Improvements
1. **Database Triggers**: Event-driven processing using LISTEN/NOTIFY
2. **Connection Pooling**: Improved database connection management
3. **Parallel Processing**: Multiple API endpoints for higher throughput
4. **Streaming Processing**: Memory-efficient processing for very large datasets
5. **Health Checks**: Automated monitoring and restart capabilities

### Alternative Architectures
1. **Event-Driven**: Using PostgreSQL LISTEN/NOTIFY triggers
2. **Microservices**: Separate services for different embedding types
3. **Containerized**: Docker containers for deployment flexibility

## Related Documentation

- [Embedding Generation Performance](EMBEDDING_GENERATION_PERFORMANCE.md)
- [Enrichment Pipeline Quick Reference](ENRICHMENT_PIPELINE_QUICK_REFERENCE.md)
- [Large Scale Database Optimization](LARGE_SCALE_DATABASE_OPTIMIZATION_GUIDE.md)
- [Functional Programming Guide](../ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs in `enrichment.log`
3. Run the test suite to verify functionality
4. Check database connectivity and functions


