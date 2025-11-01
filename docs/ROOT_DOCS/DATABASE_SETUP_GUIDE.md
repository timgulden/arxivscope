# Database Setup Guide: PostgreSQL + pgvector

> **Current Environment (October 2025)**: This system runs on a local laptop environment. PostgreSQL runs on port 5432 on the internal drive (`/opt/homebrew/var/postgresql@14`). See [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md) for current setup details.

## Overview

This guide provides comprehensive instructions for setting up the PostgreSQL database with pgvector extension for the DocScope/DocTrove system. The database is the core component that stores papers, embeddings, and enrichment data.

## ⚠️ Critical Setup Requirements

**For the enrichment system to work properly, you MUST follow these steps in order:**

1. **Apply main schema** (`doctrove_schema.sql`)
2. **Apply database functions** (`setup_database_functions.sql`) 
3. **Create enrichment queue table** (see step 4 in each setup section)
4. **Apply event triggers** (`event_triggers.sql`)

**Missing any of these steps will cause the enrichment system to fail silently.**

## Quick Start (Choose Your Path)

### 🚀 **Option 1: Automated Setup (Recommended)**
- **Local Development**: Use `Design documents/setup_postgres_pgvector.sh`
- **Production Server**: Use `server-setup.sh`

### 📖 **Option 2: Manual Setup**
- Follow the step-by-step instructions below

### ☁️ **Option 3: Cloud Deployment**
- **Azure**: Use `COST_OPTIMIZED_DEPLOYMENT.md`
- **AWS**: Use `OPEN_SOURCE_DEPLOYMENT.md`

---

## Local Development Setup (Cross-Platform)

### Prerequisites
- **macOS**: Homebrew installed
- **Windows**: Chocolatey installed (or manual installation)
- **Linux**: Package manager (apt/yum) access
- Git for version control
- Terminal access

### Automated Setup (Recommended)
```bash
# Navigate to the project directory
cd /path/to/arxivscope-back-end

# Run the automated setup script
bash "Design documents/setup_postgres_pgvector.sh"
```

This script will:
- ✅ Install PostgreSQL 15 via platform-appropriate package manager
- ✅ Install pgvector extension
- ✅ Start PostgreSQL service
- ✅ Create `doctrove` database
- ✅ Enable pgvector extension
- ✅ Create initial schema and tables

### Manual Setup (Alternative)
If you prefer manual setup or the script fails:

#### **macOS (Homebrew) - Current Setup**
```bash
# Install PostgreSQL 14 (current version on local laptop)
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Install pgvector (compiled for PostgreSQL 14)
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
PG_CONFIG_PATH=$(brew --prefix postgresql@14)/bin/pg_config make
PG_CONFIG_PATH=$(brew --prefix postgresql@14)/bin/pg_config make install

# Database location (internal drive)
# Default: /opt/homebrew/var/postgresql@14
```

#### **Windows (Chocolatey)**
```powershell
# Install PostgreSQL
choco install postgresql

# Start PostgreSQL service
net start postgresql

# Install pgvector (manual installation required)
# Download from: https://github.com/pgvector/pgvector/releases
```

#### **Linux (Ubuntu/Debian)**
```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL
sudo apt install -y postgresql-15 postgresql-contrib-15 postgresql-server-dev-15

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install pgvector
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### **Linux (CentOS/RHEL/Fedora)**
```bash
# Install PostgreSQL
sudo yum install -y postgresql15 postgresql15-server postgresql15-devel

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install pgvector
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### Step 3: Create Database and Enable Extension
```bash
# Create the database
createdb doctrove

# Connect to database and enable pgvector
psql doctrove -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Step 4: Apply Schema
```bash
# Apply the main schema
psql -d doctrove -f "doctrove_schema.sql"

# Apply enrichment functions
psql -d doctrove -f "embedding-enrichment/setup_database_functions.sql"

# Create the enrichment queue table (REQUIRED for event triggers)
psql -d doctrove -c "CREATE TABLE IF NOT EXISTS enrichment_queue (
    id SERIAL PRIMARY KEY,
    paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    enrichment_type TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    status TEXT DEFAULT 'pending'
);"

# Apply event triggers and enrichment triggers (REQUIRED for enrichment system)
psql -d doctrove -f "embedding-enrichment/event_triggers.sql"
```

### Verification
```bash
# Check if database exists
psql -l | grep doctrove

# Check if pgvector is enabled
psql -d doctrove -c "\dx"

# Check if tables exist
psql -d doctrove -c "\dt"
```

---

## Production Server Setup (Ubuntu/Debian)

### Prerequisites
- Ubuntu 20.04+ or Debian 11+
- Sudo privileges
- SSH access to server

### Automated Setup (Recommended)
```bash
# Download and run the server setup script
wget https://raw.githubusercontent.com/your-repo/arxivscope-back-end/main/server-setup.sh
chmod +x server-setup.sh
sudo ./server-setup.sh
```

### Manual Setup (Alternative)

#### Step 1: System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git htop vim nano unzip \
    software-properties-common apt-transport-https \
    ca-certificates gnupg lsb-release
```

#### Step 2: Install PostgreSQL 15
```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL
sudo apt install -y postgresql-15 postgresql-contrib-15 postgresql-server-dev-15

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Step 3: Install pgvector
```bash
# Install build dependencies
sudo apt install -y build-essential git

# Clone and compile pgvector
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### Step 4: Configure PostgreSQL
```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32)

# Create database and user
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -c "CREATE DATABASE doctrove;"
sudo -u postgres psql -c "CREATE USER doctrove_admin WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE doctrove TO doctrove_admin;"

# Save password securely
echo "$DB_PASSWORD" | sudo tee /opt/doctrove/config/db_password
sudo chmod 600 /opt/doctrove/config/db_password
```

#### Step 5: Optimize PostgreSQL Configuration
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/15/main/postgresql.conf

# Add these optimizations:
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 16MB
maintenance_work_mem = 256MB
shared_preload_libraries = 'vector'
random_page_cost = 1.1
effective_io_concurrency = 200
checkpoint_completion_target = 0.9
wal_buffers = 64MB
max_wal_size = 2GB
min_wal_size = 1GB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Step 6: Apply Schema
```bash
# Apply the main schema
psql -h localhost -U doctrove_admin -d doctrove -f "doctrove_schema.sql"

# Apply enrichment functions
psql -h localhost -U doctrove_admin -d doctrove -f "embedding-enrichment/setup_database_functions.sql"

# Create the enrichment queue table (REQUIRED for event triggers)
psql -h localhost -U doctrove_admin -d doctrove -c "CREATE TABLE IF NOT EXISTS enrichment_queue (
    id SERIAL PRIMARY KEY,
    paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    enrichment_type TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    status TEXT DEFAULT 'pending'
);"

# Apply event triggers and enrichment triggers (REQUIRED for enrichment system)
psql -h localhost -U doctrove_admin -d doctrove -f "embedding-enrichment/event_triggers.sql"
```

---

## Docker Setup (Containerized)

### Prerequisites
- Docker and Docker Compose installed
- Git for version control

### Setup
```bash
# Navigate to project directory
cd /path/to/arxivscope-back-end

# Build and start PostgreSQL container
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for container to be ready
docker-compose -f docker-compose.prod.yml logs postgres

# Apply schema
docker exec -i doctrove-postgres psql -U doctrove_admin -d doctrove < "doctrove_schema.sql"
docker exec -i doctrove-postgres psql -U doctrove_admin -d doctrove < "embedding-enrichment/setup_database_functions.sql"

# Create the enrichment queue table (REQUIRED for event triggers)
docker exec -i doctrove-postgres psql -U doctrove_admin -d doctrove -c "CREATE TABLE IF NOT EXISTS enrichment_queue (
    id SERIAL PRIMARY KEY,
    paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    enrichment_type TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    status TEXT DEFAULT 'pending'
);"

# Apply event triggers and enrichment triggers (REQUIRED for enrichment system)
docker exec -i doctrove-postgres psql -U doctrove_admin -d doctrove < "embedding-enrichment/event_triggers.sql"
```

### Docker Compose Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    build:
      context: ./database
      dockerfile: Dockerfile.postgres
    image: doctroveregistry.azurecr.io/postgres-pgvector:latest
    environment:
      - POSTGRES_DB=doctrove
      - POSTGRES_USER=doctrove_admin
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - postgres-backups:/backups
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./database/postgresql.conf:/etc/postgresql/postgresql.conf
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U doctrove_admin -d doctrove"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - doctrove-network
    command: ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]

volumes:
  postgres-data:
  postgres-backups:

networks:
  doctrove-network:
    driver: bridge
```

---

## Cloud Deployment Options

### Azure Deployment
For Azure deployment with managed PostgreSQL:
- **Guide**: `COST_OPTIMIZED_DEPLOYMENT.md`
- **Script**: `azure-deploy.sh`
- **Cost**: ~$176/month for 1M records

### AWS Deployment
For AWS deployment with self-managed PostgreSQL:
- **Guide**: `OPEN_SOURCE_DEPLOYMENT.md`
- **Cost**: ~$40-80/month for 1M records

### Self-Managed Cloud VM
For maximum cost savings:
- **Guide**: `QUICK_OPEN_SOURCE_START.md`
- **Cost**: ~$40-80/month for 1M records

---

## Database Schema Overview

### Core Tables
```sql
-- Main papers table
CREATE TABLE doctrove_papers (
    doctrove_paper_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctrove_source TEXT NOT NULL,
    doctrove_source_id TEXT NOT NULL,
    doctrove_title TEXT NOT NULL,
    doctrove_abstract TEXT,
    doctrove_authors TEXT[],
    doctrove_primary_date DATE,
    doctrove_embedding VECTOR(1536),
    doctrove_embedding_2d POINT,
    country2 TEXT,
    embedding_model_version TEXT DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(doctrove_source, doctrove_source_id)
);

-- Enrichment metadata table
CREATE TABLE aipickle_metadata (
    doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id) ON DELETE CASCADE,
    doi TEXT,
    links JSONB,
    PRIMARY KEY (doctrove_paper_id)
);

-- Enrichment registry
CREATE TABLE enrichment_registry (
    enrichment_name TEXT PRIMARY KEY,
    table_name TEXT NOT NULL,
    description TEXT,
    fields JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Performance Indexes
```sql
-- Strategic indexes for performance
CREATE INDEX CONCURRENTLY idx_papers_source_id ON doctrove_papers(doctrove_source, doctrove_source_id);
CREATE INDEX CONCURRENTLY idx_papers_date ON doctrove_papers(doctrove_primary_date);
CREATE INDEX CONCURRENTLY idx_embeddings_2d ON doctrove_papers USING GIST (doctrove_embedding_2d);
CREATE INDEX CONCURRENTLY idx_country ON doctrove_papers(country2);
CREATE INDEX CONCURRENTLY idx_embedding ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops);
```

---

## Configuration and Environment Variables

### Local Development (Current Setup)
```bash
# Environment variables for local development (via .env.local)
# Database runs on internal drive, port 5432, trust authentication
DB_HOST=localhost
DOC_TROVE_PORT=5432
DB_NAME=doctrove
DB_USER=doctrove_admin
DB_PASSWORD=  # Empty for trust authentication (local setup)

# Database location (macOS with Homebrew)
# Default: /opt/homebrew/var/postgresql@14
```

### Production
```bash
# Environment variables for production
export DOC_TROVE_HOST=your-db-host
export DOC_TROVE_PORT=5432
export DOC_TROVE_DB=doctrove
export DOC_TROVE_USER=doctrove_admin
export DOC_TROVE_PASSWORD=your_secure_password
```

### Configuration Files
- **`doctrove-api/config.py`** - API configuration (reads from `.env.local`)
- **`.env.local`** - Environment variables (local development, in .gitignore)
- **`env.local.example`** - Template for `.env.local` file
- **PostgreSQL configuration** - Managed by Homebrew (macOS) or system package manager

---

## Testing and Verification

### Connection Test
```bash
# Test database connection
psql -h $DOC_TROVE_HOST -p $DOC_TROVE_PORT -U $DOC_TROVE_USER -d $DOC_TROVE_DB -c "SELECT version();"
```

### Schema Verification
```bash
# Check if tables exist
psql -d doctrove -c "\dt"

# Check if pgvector is enabled
psql -d doctrove -c "\dx"

# Check table structure
psql -d doctrove -c "\d doctrove_papers"
```

### Performance Test
```bash
# Test vector operations
psql -d doctrove -c "
SELECT 
    doctrove_paper_id,
    doctrove_title,
    doctrove_embedding <=> '[0.1, 0.2, ...]'::vector as distance
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL 
LIMIT 5;
"
```

---

## Backup and Recovery

### Automated Backup Script
```bash
#!/bin/bash
# Automated PostgreSQL Backup Script

DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_PASSWORD="your_password"
BACKUP_DIR="/opt/doctrove/backups"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup filename
BACKUP_FILE="doctrove_backup_$(date +%Y%m%d_%H%M%S).sql"

# Create backup
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h localhost \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"

# Clean up old backups
find "$BACKUP_DIR" -name "doctrove_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### Recovery
```bash
# Restore from backup
gunzip -c /opt/doctrove/backups/doctrove_backup_20250101_120000.sql.gz | \
psql -h localhost -U doctrove_admin -d doctrove
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused
```bash
# Check if PostgreSQL is running (macOS with Homebrew)
brew services list | grep postgresql

# Start PostgreSQL if not running (macOS with Homebrew)
brew services start postgresql@14

# Check if PostgreSQL is running (Linux)
sudo systemctl status postgresql

# Start PostgreSQL if not running (Linux)
sudo systemctl start postgresql
```

#### 2. pgvector Extension Not Found
```bash
# Check if pgvector is installed
psql -d doctrove -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# Install pgvector if missing
# Follow the installation steps above
```

#### 3. Permission Denied
```bash
# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Check user permissions
sudo -u postgres psql -c "\du"
```

#### 4. Memory Issues
```bash
# Check PostgreSQL memory usage
psql -d doctrove -c "SHOW shared_buffers;"
psql -d doctrove -c "SHOW work_mem;"

# Adjust configuration in postgresql.conf
```

#### 5. Enrichment System Issues
```bash
# Check if enrichment queue table exists
psql -d doctrove -c "\d enrichment_queue"

# If table doesn't exist, create it:
psql -d doctrove -c "CREATE TABLE IF NOT EXISTS enrichment_queue (
    id SERIAL PRIMARY KEY,
    paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    enrichment_type TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    status TEXT DEFAULT 'pending'
);"

# Check if enrichment functions exist
psql -d doctrove -c "SELECT proname FROM pg_proc WHERE proname LIKE '%enrichment%';"

# If functions are missing, reapply the setup scripts:
psql -d doctrove -f "embedding-enrichment/setup_database_functions.sql"
psql -d doctrove -f "embedding-enrichment/event_triggers.sql"
```

### Performance Optimization

#### 1. Query Performance
```sql
-- Analyze table statistics
ANALYZE doctrove_papers;

-- Check query execution plans
EXPLAIN ANALYZE SELECT * FROM doctrove_papers WHERE doctrove_source = 'aipickle';
```

#### 2. Index Optimization
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

#### 3. Connection Pooling
```bash
# Install and configure PgBouncer for connection pooling
sudo apt install pgbouncer
```

---

## Security Considerations

### 1. Network Security
```bash
# Configure PostgreSQL to accept connections only from trusted hosts
# Edit pg_hba.conf
echo "host    doctrove    doctrove_admin    127.0.0.1/32    md5" >> /etc/postgresql/15/main/pg_hba.conf
echo "host    doctrove    doctrove_admin    192.168.1.0/24    md5" >> /etc/postgresql/15/main/pg_hba.conf
```

### 2. SSL Configuration
```bash
# Enable SSL in postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

### 3. Password Security
```bash
# Use strong passwords
# Store passwords securely (not in plain text)
# Rotate passwords regularly
```

---

## Monitoring and Maintenance

### 1. Database Monitoring
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('doctrove'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 2. Performance Monitoring
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 3. Maintenance Tasks
```bash
# Set up automated maintenance
# Add to crontab
0 2 * * * /usr/bin/vacuumdb --all --analyze
0 3 * * * /opt/doctrove/backup.sh
```

---

## Next Steps

After setting up the database:

1. **Test the connection** with the verification commands above
2. **Apply the schema** using the provided SQL files
3. **Configure environment variables** for your application
4. **Run the application** following the startup guide
5. **Monitor performance** and adjust configuration as needed

For additional help:
- Check the troubleshooting section above
- Review the application logs
- Consult the project documentation
- Contact the development team

---

*This guide consolidates database setup information from multiple project files. For specific deployment scenarios, refer to the individual deployment guides mentioned in the Quick Start section.* 