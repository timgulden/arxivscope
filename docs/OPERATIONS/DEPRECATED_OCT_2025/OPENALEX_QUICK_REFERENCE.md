# OpenAlex Quick Reference

## 🚀 Quick Start Commands

### 1. Test the Pipeline
```bash
# Test with 2 specific files
./openalex_test_ingestion.sh
```

### 2. Start Enrichment
```bash
# Start all services with enrichment
./startup.sh --with-enrichment --background
```

### 3. Monitor Progress
```bash
# Check database status
psql -h localhost -U tgulden -d doctrove -c "
SELECT 
    COUNT(*) as total_openalex,
    COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_2d_embeddings
FROM doctrove_papers 
WHERE doctrove_source = 'openalex';"

# Watch enrichment logs
tail -f enrichment.log
```

### 4. Stop Services
```bash
./stop_services.sh
```

## 📊 Status Check Commands

### Database Status
```sql
-- OpenAlex papers count
SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';

-- Embedding status
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_2d_embeddings
FROM doctrove_papers 
WHERE doctrove_source = 'openalex';

-- Recent ingestions
SELECT file_path, records_ingested, status, ingestion_completed_at
FROM openalex_ingestion_log 
ORDER BY ingestion_started_at DESC 
LIMIT 5;
```

### Service Status
```bash
# Check if services are running
ps aux | grep -E "(main.py|api.py|app.py)" | grep -v grep

# Check log files
ls -la *.log
```

## 🔧 Common Operations

### Incremental Updates
```bash
# Main file-based ingestion (recommended)
./openalex_incremental_files.sh

# With custom parameters
./openalex_incremental_files.sh --earliest-date 2025-01-15 --max-files 5

# Dry run (test without changes)
./openalex_incremental_files.sh --dry-run
```

### Troubleshooting
```bash
# ⚠️ CRITICAL: Test S3 access (use HTTPS, not s3://)
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"

# Test database connection
psql -h localhost -U tgulden -d doctrove -c "SELECT 1;"

# Check failed ingestions
psql -h localhost -U tgulden -d doctrove -c "
SELECT file_path, error_message 
FROM openalex_ingestion_log 
WHERE status = 'failed';"

# Test S3 file download
curl -o test_file.gz "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"
ls -la test_file.gz
rm test_file.gz
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `openalex_test_ingestion.sh` | Test ingestion with 2 files |
| `openalex_incremental_files.sh` | Main file-based ingestion with tracking |
| `openalex_metadata_patch_final.sh` | Patch metadata for existing papers |
| `check_openalex_ingestion_status.sh` | Check ingestion status |
| `startup.sh` | Start all services |
| `stop_services.sh` | Stop all services |

## 🎯 Production Workflow

### 1. Initial Setup
```bash
# Test the pipeline
./openalex_test_ingestion.sh

# Start enrichment
./startup.sh --with-enrichment --background
```

### 2. Daily Operations
```bash
# Run incremental updates
./openalex_incremental_files.sh

# Monitor enrichment progress
tail -f enrichment.log
```

### 3. Metadata Management
```bash
# Patch metadata for existing papers (if needed)
./openalex_metadata_patch_final.sh

# Check metadata status
psql -h localhost -U tgulden -d doctrove -c "
SELECT 
    COUNT(*) as total_papers,
    COUNT(*) FILTER (WHERE om.doctrove_paper_id IS NOT NULL) as with_metadata
FROM doctrove_papers dp
LEFT JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
WHERE dp.doctrove_source = 'openalex';"
```

### 3. Monitoring
```bash
# Check overall status
psql -h localhost -U tgulden -d doctrove -c "
SELECT 
    'OpenAlex Papers' as metric,
    COUNT(*) as count
FROM doctrove_papers 
WHERE doctrove_source = 'openalex'
UNION ALL
SELECT 
    'With Embeddings',
    COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL)
FROM doctrove_papers 
WHERE doctrove_source = 'openalex'
UNION ALL
SELECT 
    'With 2D Embeddings',
    COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL)
FROM doctrove_papers 
WHERE doctrove_source = 'openalex';"
```

## ⚠️ Important Notes

- **S3 Access**: Use HTTPS URLs, NOT s3:// protocol (see troubleshooting)
- **Memory**: Enrichment requires significant memory (~8GB+ recommended)
- **Storage**: Full dataset requires ~50GB disk space
- **API Limits**: Azure OpenAI has rate limits for embeddings
- **Backup**: Always backup database before major operations
- **Logs**: Check `enrichment.log`, `api.log`, `frontend.log` for issues

## 🆘 Emergency Commands

```bash
# Force stop all services
pkill -f "python.*main.py"
pkill -f "python.*api.py"
pkill -f "python.*app.py"

# Reset 2D embeddings
cd embedding-enrichment
python reset_umap_environment.py

# Emergency database cleanup (use with caution)
psql -h localhost -U tgulden -d doctrove -c "
DELETE FROM openalex_metadata;
DELETE FROM doctrove_papers WHERE doctrove_source = 'openalex';"
```

## 📞 Support

- **Full Guide**: See `OPENALEX_INGESTION_GUIDE.md`
- **Logs**: Check `*.log` files for detailed error messages
- **Database**: Use `psql` for direct database queries
- **Scripts**: All scripts have `--help` or inline documentation 