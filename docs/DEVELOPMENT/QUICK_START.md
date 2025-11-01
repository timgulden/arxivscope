# DocScope/DocTrove Quick Start Guide

> **Current Environment (October 2025)**: This system runs on a local laptop environment. API on port 5001, React Frontend on port 3000, PostgreSQL on port 5432. All data is stored on the internal drive. See [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md) for current setup details.

## Prerequisites

### System Requirements
- **Python 3.10+**
- **PostgreSQL 14+** with **pgvector** extension (running on port 5432, internal drive)
- **Node.js** (for React frontend)
- **Git** for version control
- **Virtual environment** (recommended)

### Database Setup
1. **Install PostgreSQL** with pgvector extension (on internal drive)
2. **Create database**: `createdb doctrove`
3. **Run schema setup**: 
   ```bash
   psql -d doctrove -f "doctrove_schema.sql"
   psql -d doctrove -f "embedding-enrichment/setup_database_functions.sql"
   
   # Create enrichment queue table (REQUIRED for event triggers)
   psql -d doctrove -c "CREATE TABLE IF NOT EXISTS enrichment_queue (
       id SERIAL PRIMARY KEY,
       paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
       enrichment_type TEXT NOT NULL,
       priority INTEGER DEFAULT 1,
       created_at TIMESTAMP DEFAULT NOW(),
       processed_at TIMESTAMP,
       status TEXT DEFAULT 'pending'
   );"
   
   psql -d doctrove -f "embedding-enrichment/event_triggers.sql"  # REQUIRED for enrichment triggers
   ```

## Environment Setup

### 1. Clone and Setup
```bash
git clone <repository-url>
cd arxivscope-back-end
python -m venv arxivscope
source arxivscope/bin/activate  # On Windows: arxivscope\Scripts\activate
```

### 2. Install Dependencies
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Core dependencies
pip install -r requirements.txt

# Component-specific dependencies
pip install -r doc-ingestor/requirements.txt
pip install -r embedding-enrichment/requirements.txt
pip install -r doctrove-api/requirements.txt

# React frontend dependencies (if React frontend exists)
cd docscope-platform/services/docscope/react
npm install
cd ../../../../..
```

### 3. Configuration
Create `.env.local` file (from template):
```bash
cp env.local.example .env.local
```

Key configuration settings:
- Database connection (port 5432, internal drive)
- API port (5001)
- Frontend port (3000 for React)
- UMAP model path (internal drive)

## Quick Start Workflows

### 1. Ingest Data
```bash
# Ingest AiPickle dataset (limit to 10 for testing)
cd doc-ingestor
python main.py --source aipickle --limit 10

# Ingest full dataset
python main.py --source aipickle

# Ingest from custom file
python main.py --source custom --file-path /path/to/your/data.pkl --limit 100
```

### 2. Run Enrichment
```bash
# Generate 2D embeddings for all papers
cd embedding-enrichment
python main.py --mode enrich_all

# Train new UMAP model
python main.py --mode train_model

# Enrich specific papers
python main.py --mode enrich_papers --paper_ids 1,2,3
```

### 3. Start API Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start API server
cd doctrove-api
python api.py

# API will run on http://localhost:5001
```

### 4. Launch React Frontend (Recommended)
```bash
# Start React frontend
cd docscope-platform/services/docscope/react
npm run dev

# Frontend will run on http://localhost:3000
```

### Legacy Dash Frontend (For Reference Only)
```bash
# Activate virtual environment
source venv/bin/activate

# Start legacy Dash frontend
python -m docscope.app

# Frontend will run on http://localhost:8050 (frozen, bug fixes only)
```

## Performance and Cost Estimates

### Embedding Generation (Batch Processing)
- **Speed:** ~50,000 papers per hour (title + abstract) using Azure OpenAI API
- **Cost:** $10 per million papers (conservative estimate)
- **Examples:**
  - 1M papers: ~20 hours, $10
  - 5M papers: ~100 hours, $50
  - 10M papers: ~200 hours, $100

These estimates assume typical scientific metadata lengths and continuous operation. Actual performance may vary with text length, API rate limits, or infrastructure changes.

## Common Commands

### Database Operations
```bash
# Check database connection
psql -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"

# View recent papers
psql -d doctrove -c "SELECT title, source FROM doctrove_papers ORDER BY created_at DESC LIMIT 5;"

# Check enrichment status
psql -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers WHERE embedding_2d IS NOT NULL;"
```

### Testing
```bash
# Run all tests
pytest

# Test specific components
pytest doc-ingestor/tests/
pytest doctrove-api/tests/
pytest embedding-enrichment/tests/

# Test API endpoints
python doctrove-api/test_api_simple.py
```

### Performance Analysis
```bash
# Analyze query performance
psql -d doctrove -c "EXPLAIN ANALYZE SELECT * FROM papers WHERE source = 'aipickle';"

# Check index usage
psql -d doctrove -c "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes;"
```

## Configuration Files

### Database Configuration
```python
# doc-ingestor/config.local.py
DATABASE_URL = "postgresql://username:password@localhost/doctrove"
```

### Environment Configuration
The system uses `.env.local` file for configuration (see `env.local.example` for template):

```bash
# Database
DB_HOST=localhost
DOC_TROVE_PORT=5432
DB_NAME=doctrove
DB_USER=doctrove_admin
DB_PASSWORD=

# API
NEW_API_BASE_URL=http://localhost:5001
LEGACY_API_BASE_URL=http://localhost:5001

# Frontend
NEW_UI_PORT=3000
NEW_UI_PUBLIC_URL=http://localhost:3000

# Models
UMAP_MODEL_PATH=/Users/tgulden/Documents/DocTrove/arxivscope/models/umap_model.pkl
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL status (macOS with Homebrew)
brew services list | grep postgresql

# Test connection (trust authentication - local setup)
psql -d doctrove

# Verify pgvector extension
psql -d doctrove -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check database location (internal drive)
psql -d doctrove -c "SHOW data_directory;"
```

#### 2. Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check virtual environment
which python
```

#### 3. Memory Issues During Enrichment
```bash
# Monitor memory usage
htop

# Reduce batch size in enrichment
python main.py --mode enrich_all --batch_size 100
```

#### 4. API Performance Issues
```bash
# Check database indexes
psql -d doctrove -c "\d+ papers"

# Analyze slow queries
psql -d doctrove -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Debug Mode

#### Enable Debug Logging
```python
# Add to configuration files
DEBUG = True
LOG_LEVEL = "DEBUG"
```

#### API Debug Mode
```bash
# Start API with debug
cd doctrove-api
FLASK_ENV=development python api.py
```

#### Frontend Debug Mode
```bash
# Start DocScope with debug
cd docscope
python app.py --debug
```

## Data Management

### Backup and Restore
```bash
# Backup database
pg_dump doctrove > backup.sql

# Restore database
psql -d doctrove < backup.sql
```

### Data Cleanup
```bash
# Remove duplicate records
psql -d doctrove -c "DELETE FROM papers WHERE id NOT IN (SELECT MIN(id) FROM papers GROUP BY title, source);"

# Reset enrichment data
psql -d doctrove -c "UPDATE papers SET embedding_2d = NULL;"
```

### Performance Optimization
```bash
# Create additional indexes
psql -d doctrove -c "CREATE INDEX CONCURRENTLY idx_papers_source_created ON papers(source, created_at);"

# Analyze table statistics
psql -d doctrove -c "ANALYZE papers;"
```

## Monitoring and Logs

### Log Locations
- **API logs**: `doctrove-api/api.log`
- **Ingestion logs**: Console output
- **Enrichment logs**: Console output
- **Frontend logs**: Console output

### Performance Monitoring
```bash
# Monitor API requests
tail -f doctrove-api/api.log

# Check database performance
psql -d doctrove -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Monitor system resources
htop
iostat 1
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
pytest

# Commit changes
git add .
git commit -m "Add new feature"

# Push and create PR
git push origin feature/new-feature
```

### 2. Testing Changes
```bash
# Run full test suite
pytest --cov=.

# Test specific functionality
python -m pytest tests/test_specific_feature.py -v

# Integration testing
python test_integration.py
```

### 3. Deployment
```bash
# Update dependencies
pip install -r requirements.txt

# Run database migrations
psql -d doctrove -f migrations/latest.sql

# Restart services
sudo systemctl restart postgresql
```

## Support Resources

### Documentation
- `PROJECT_OVERVIEW.md` - System architecture and design
- `Design documents/` - Technical specifications
- `API_DOCUMENTATION.md` - API reference

### Key Files Reference
- **Main applications**: See `PROJECT_OVERVIEW.md` for file locations
- **Configuration**: Component-specific config files
- **Database**: Schema and function files in Design documents

### Getting Help
1. Check this guide for common issues
2. Review logs for error messages
3. Check database status and performance
4. Consult design documents for architecture details

---

*Last updated: [Current Date]*
*Version: 1.0* 