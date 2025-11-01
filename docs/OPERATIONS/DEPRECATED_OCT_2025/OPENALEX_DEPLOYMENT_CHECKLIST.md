# OpenAlex Deployment Checklist

This checklist ensures all components are properly set up for OpenAlex ingestion on a new server.

## ✅ Pre-Deployment Checklist

### System Requirements
- [ ] **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- [ ] **Python**: 3.10+ installed
- [ ] **PostgreSQL**: 13+ with pgvector extension
- [ ] **Memory**: 8GB+ RAM (16GB+ recommended)
- [ ] **Storage**: 50GB+ free disk space
- [ ] **Network**: Internet access for S3 and API calls

### Environment Setup
- [ ] **Virtual Environment**: `arxivscope` environment created and activated
- [ ] **Dependencies**: All requirements installed (`pip install -r requirements.txt`)
- [ ] **Database User**: PostgreSQL user with appropriate permissions
- [ ] **Azure OpenAI**: API key configured and accessible

## 🗄️ Database Setup

### PostgreSQL Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
```

### pgvector Extension
```bash
# Install pgvector
sudo apt install postgresql-13-pgvector  # Adjust version as needed

# Or compile from source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Database Creation
```sql
-- Create database
CREATE DATABASE doctrove;

-- Create user (if needed)
CREATE USER doctrove_admin WITH PASSWORD 'your_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE doctrove TO doctrove_admin;

-- Connect to database and create extension
\c doctrove
CREATE EXTENSION IF NOT EXISTS vector;
```

### Schema Setup
```sql
-- Run the main schema
\i doctrove_schema.sql

-- Create OpenAlex-specific tables
CREATE TABLE openalex_ingestion_log (
    id SERIAL PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_date DATE NOT NULL,
    records_ingested INTEGER,
    ingestion_started_at TIMESTAMP DEFAULT NOW(),
    ingestion_completed_at TIMESTAMP,
    status TEXT DEFAULT 'pending',
    error_message TEXT
);

CREATE INDEX idx_openalex_ingestion_log_file_path ON openalex_ingestion_log (file_path);
CREATE INDEX idx_openalex_ingestion_log_file_date ON openalex_ingestion_log (file_date);
CREATE INDEX idx_openalex_ingestion_log_status ON openalex_ingestion_log (status);
```

## 🔧 Configuration Files

### Database Configuration
- [ ] **`doc-ingestor/config.py`**: Update database connection parameters
- [ ] **`doctrove-api/config.py`**: Verify API database settings
- [ ] **`embedding-enrichment/config.py`**: Check enrichment database settings

### Azure OpenAI Configuration
- [ ] **Environment Variables**: Set `AZURE_OPENAI_API_KEY`
- [ ] **API Endpoint**: Verify endpoint URL in configuration files
- [ ] **Rate Limits**: Understand and plan for API limits

### File Paths
- [ ] **Temporary Directory**: Create `/tmp/doctrove-data/openalex/` or equivalent
- [ ] **Log Directory**: Ensure write permissions for log files
- [ ] **Script Permissions**: Make all shell scripts executable (`chmod +x *.sh`)

## 📦 Code Deployment

### Repository Setup
```bash
# Clone or copy the repository
git clone <repository-url>
cd arxivscope-back-end

# Or copy files to server
scp -r /path/to/local/project user@server:/path/to/deployment/
```

### File Verification
- [ ] **Core Scripts**: All `.sh` files present and executable
- [ ] **Python Modules**: `openalex/`, `doc-ingestor/`, `embedding-enrichment/` directories
- [ ] **Configuration**: All config files updated for server environment
- [ ] **Dependencies**: `requirements.txt` installed

### Script Permissions
```bash
# Make all scripts executable
chmod +x *.sh
chmod +x openalex/*.sh
chmod +x doc-ingestor/*.sh
chmod +x embedding-enrichment/*.sh
```

## 🧪 Testing Phase

### 1. Database Connection Test
```bash
# Test PostgreSQL connection
psql -h localhost -U doctrove_admin -d doctrove -c "SELECT 1;"

# Test pgvector extension
psql -h localhost -U doctrove_admin -d doctrove -c "SELECT vector_version();"
```

### 2. S3 Access Test
```bash
# ⚠️ CRITICAL: Test OpenAlex S3 access (use HTTPS, not s3://)
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"

# Test file listing
curl -s "https://openalex.s3.us-east-1.amazonaws.com/data/works/" | head -20

# Test file download
curl -o test_file.gz "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"
ls -la test_file.gz
rm test_file.gz

# ❌ DO NOT USE: aws s3 ls s3://openalex/data/works/ --no-sign-request
```

### 3. Azure OpenAI Test
```bash
# Test embedding API
python -c "
import openai
import os
openai.api_key = os.getenv('AZURE_OPENAI_API_KEY')
openai.api_base = 'https://apigw.rand.org/openai/RAND/inference/deployments/text-embedding-ada-002'
openai.api_version = '2024-02-01'
response = openai.Embedding.create(input=['test text'])
print('API working:', len(response['data'][0]['embedding']))
"
```

### 4. Small Scale Test
```bash
# Run test ingestion
./openalex_test_ingestion.sh

# Verify results
psql -h localhost -U doctrove_admin -d doctrove -c "
SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';"
```

## 🚀 Production Deployment

### 1. Initial Setup
```bash
# Clean any existing data (if needed)
./run_cleanup_visible.sh

# Test the complete pipeline
./openalex_test_ingestion.sh

# Start enrichment service
./startup.sh --with-enrichment --background
```

### 2. Historical Data Ingestion
```bash
# Start with small batch
./openalex_streaming_ingestion.sh

# Monitor progress
tail -f enrichment.log

# Check database status periodically
psql -h localhost -U doctrove_admin -d doctrove -c "
SELECT 
    COUNT(*) as total_openalex,
    COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings
FROM doctrove_papers 
WHERE doctrove_source = 'openalex';"
```

### 3. Incremental Updates Setup
```bash
# Test incremental updates
./openalex_incremental_files.sh --dry-run

# Run first incremental update
./openalex_incremental_files.sh --max-files 5
```

## 📊 Monitoring Setup

### Log Monitoring
```bash
# Set up log rotation
sudo logrotate -f /etc/logrotate.conf

# Monitor key logs
tail -f enrichment.log
tail -f api.log
tail -f frontend.log
```

### Database Monitoring
```sql
-- Create monitoring views
CREATE VIEW openalex_status AS
SELECT 
    COUNT(*) as total_papers,
    COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_2d_embeddings,
    MIN(doctrove_primary_date) as earliest_date,
    MAX(doctrove_primary_date) as latest_date
FROM doctrove_papers 
WHERE doctrove_source = 'openalex';

-- Check ingestion progress
SELECT 
    status,
    COUNT(*) as file_count,
    SUM(records_ingested) as total_records
FROM openalex_ingestion_log 
GROUP BY status;
```

### System Monitoring
```bash
# Monitor system resources
htop
df -h
free -h

# Monitor PostgreSQL
pg_stat_statements  # Enable if needed
```

## 🔄 Automation Setup

### Cron Jobs
```bash
# Edit crontab
crontab -e

# Add daily incremental updates (2 AM)
0 2 * * * /path/to/project/openalex_incremental_files.sh >> /path/to/project/cron.log 2>&1

# Add weekly enrichment restart (3 AM Sunday)
0 3 * * 0 /path/to/project/startup.sh --with-enrichment --background >> /path/to/project/cron.log 2>&1
```

### Health Checks
```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
# Check if services are running
if ! pgrep -f "python.*main.py" > /dev/null; then
    echo "Enrichment service down, restarting..."
    cd /path/to/project
    ./startup.sh --with-enrichment --background
fi
EOF

chmod +x health_check.sh

# Add to crontab (every 15 minutes)
*/15 * * * * /path/to/project/health_check.sh
```

## 🛡️ Backup Strategy

### Database Backups
```bash
# Create backup script
cat > backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U doctrove_admin -d doctrove > "$BACKUP_DIR/doctrove_$DATE.sql"
# Keep only last 7 days
find "$BACKUP_DIR" -name "doctrove_*.sql" -mtime +7 -delete
EOF

chmod +x backup_database.sh

# Add to crontab (daily at 1 AM)
0 1 * * * /path/to/project/backup_database.sh
```

### Configuration Backups
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz *.sh *.py config/ openalex/ doc-ingestor/ embedding-enrichment/
```

## 🚨 Emergency Procedures

### Service Recovery
```bash
# Force stop all services
pkill -f "python.*main.py"
pkill -f "python.*api.py"
pkill -f "python.*app.py"

# Restart services
./startup.sh --with-enrichment --background
```

### Database Recovery
```bash
# Restore from backup
psql -h localhost -U doctrove_admin -d doctrove < backup_file.sql

# Reset 2D embeddings if needed
cd embedding-enrichment
python reset_umap_environment.py
```

### Emergency Cleanup
```bash
# Emergency data cleanup
psql -h localhost -U doctrove_admin -d doctrove -c "
DELETE FROM doctrove_papers WHERE doctrove_source = 'openalex';"
```

## ✅ Final Verification

### System Health Check
- [ ] **Services**: All services running and responding
- [ ] **Database**: Connection stable, indexes created
- [ ] **API**: Azure OpenAI responding within rate limits
- [ ] **Storage**: Sufficient disk space available
- [ ] **Memory**: System not running out of memory

### Data Verification
- [ ] **Test Data**: Small ingestion test completed successfully
- [ ] **Embeddings**: Embeddings being generated correctly
- [ ] **2D Visualizations**: 2D embeddings being created
- [ ] **API Access**: Papers accessible via DocTrove API
- [ ] **Frontend**: Papers visible in DocScope interface

### Performance Verification
- [ ] **Ingestion Rate**: Acceptable papers per minute
- [ ] **Embedding Rate**: Embeddings generated within API limits
- [ ] **Database Performance**: Queries completing in reasonable time
- [ ] **Memory Usage**: System memory usage stable

## 📋 Post-Deployment Checklist

### Documentation
- [ ] **Server Details**: Document server IP, credentials, access methods
- [ ] **Configuration**: Document all configuration changes made
- [ ] **Monitoring**: Set up monitoring and alerting
- [ ] **Backup**: Verify backup procedures are working

### Training
- [ ] **Team Access**: Ensure team has access to server
- [ ] **Procedures**: Document emergency procedures
- [ ] **Monitoring**: Train team on monitoring and maintenance
- [ ] **Updates**: Document update procedures

### Maintenance Schedule
- [ ] **Daily**: Monitor logs and system health
- [ ] **Weekly**: Review performance and adjust as needed
- [ ] **Monthly**: Full system health check and optimization
- [ ] **Quarterly**: Review and update documentation

---

## 🎯 Success Criteria

The deployment is successful when:

1. **Test ingestion** processes 2 files without errors
2. **Enrichment service** generates embeddings automatically
3. **Incremental updates** run daily without intervention
4. **Monitoring** provides visibility into system health
5. **Backup procedures** are tested and working
6. **Team** can access and maintain the system

## 📞 Support

- **Documentation**: Refer to `OPENALEX_INGESTION_GUIDE.md`
- **Quick Reference**: Use `OPENALEX_QUICK_REFERENCE.md`
- **Logs**: Check `*.log` files for detailed error messages
- **Database**: Use `psql` for direct database queries 