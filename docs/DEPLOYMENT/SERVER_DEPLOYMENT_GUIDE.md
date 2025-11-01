# Server Deployment Guide

> **Note**: This system has been migrated from a server installation to a local laptop environment (October 2025). The current setup runs on a local machine with:
> - **API**: Port 5001 (changed from server configuration)
> - **Frontend**: Port 3000 (React, changed from server configuration)
> - **PostgreSQL**: Port 5432 on internal drive (changed from server paths)
> - **Database Location**: `/opt/homebrew/var/postgresql@14` (macOS with Homebrew)
> - **Models**: Stored on internal drive (not external/server paths)
>
> This deployment guide is preserved for reference if server deployment is needed in the future. For current setup information, see [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md).

## 🚀 Quick Start

### Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- SSH access
- Root or sudo privileges
- At least 8GB RAM, 50GB disk space

### Option 1: Remote Development with Cursor (Recommended)

1. **Install Remote Development Extension** in Cursor
2. **Connect to server via SSH**:
   ```bash
   # In Cursor: Cmd+Shift+P → "Remote-SSH: Connect to Host"
   # Add your server: ssh username@your-server-ip
   ```
3. **Open remote workspace** in Cursor
4. **Clone the repository** on the server:
   ```bash
   git clone https://github.com/your-org/arxivscope-back-end.git
   cd arxivscope-back-end
   ```

### Option 2: Traditional SSH + Git

1. **SSH to your server**
2. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/arxivscope-back-end.git
   cd arxivscope-back-end
   ```

## 🔧 Server Setup

### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib curl git

# Install pgvector extension
sudo apt install -y postgresql-14-pgvector  # Adjust version as needed
```

### 2. Database Setup

```bash
# Create database and user
sudo -u postgres createuser --interactive
# Enter your username when prompted

sudo -u postgres createdb doctrove

# Enable pgvector extension
sudo -u postgres psql -d doctrove -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Python Environment

```bash
# Create virtual environment
python3 -m venv arxivscope
source arxivscope/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
# Copy and edit configuration
cp config/settings.example.py config/settings.py

# Edit database connection settings
nano config/settings.py
```

## 🐛 Remote Debugging Setup

### 1. Install Debugging Tools

```bash
# Run the remote debug setup script
chmod +x remote_debug_setup.sh
./remote_debug_setup.sh
```

### 2. Test System Health

```bash
# Run comprehensive health check
./check_remote_health.sh
```

### 3. Test OpenAlex S3 Access

```bash
# Test S3 connectivity (CRITICAL)
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"

# Test file download
curl -o test_file.gz "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"
ls -la test_file.gz
rm test_file.gz
```

## 🚀 Deployment Steps

### 1. Initial Setup

```bash
# Run the setup script
./scripts/setup_environment.sh

# Check services
./check_services.sh
```

### 2. Database Migration

```bash
# Run database setup
psql -h localhost -U $USER -d doctrove -f doctrove_schema.sql

# Create OpenAlex ingestion log table
psql -h localhost -U $USER -d doctrove -c "
CREATE TABLE IF NOT EXISTS openalex_ingestion_log (
    id SERIAL PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_date DATE NOT NULL,
    records_ingested INTEGER,
    ingestion_started_at TIMESTAMP DEFAULT NOW(),
    ingestion_completed_at TIMESTAMP,
    status TEXT DEFAULT 'pending',
    error_message TEXT
);"
```

### 3. Start Services

```bash
# Start all services
./startup.sh --with-enrichment --background

# Check status
./check_services.sh
```

### 4. Test OpenAlex Ingestion

```bash
# Test with a small sample
./openalex_test_ingestion.sh

# Check results
./check_openalex_ingestion_status.sh
```

## 📊 Monitoring and Debugging

### Real-time Monitoring

```bash
# Stream logs in real-time
./stream_logs.sh

# Quick status check
./quick_status.sh
```

### When Issues Occur

```bash
# Collect comprehensive error report
./report_error.sh

# Copy the error log content to share with assistant
cat logs/remote_debug/error_*.log
```

### Common Issues and Solutions

#### 1. S3 Access Issues
```bash
# Test S3 connectivity
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz"

# If failed, check firewall/proxy settings
sudo ufw status
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U $USER -d doctrove -c "SELECT 1;"
```

#### 3. Python Environment Issues
```bash
# Check Python version
python3 --version

# Check virtual environment
echo $VIRTUAL_ENV

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 4. Memory Issues
```bash
# Check memory usage
free -h

# Check swap
swapon --show

# If low memory, consider adding swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 🔄 Continuous Deployment

### Automated Updates

```bash
# Pull latest changes
git pull origin main

# Restart services
./stop_services.sh
./startup.sh --with-enrichment --background

# Check health
./check_remote_health.sh
```

### Backup Strategy

```bash
# Database backup
pg_dump -h localhost -U $USER -d doctrove > backup_$(date +%Y%m%d).sql

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/ logs/
```

## 📞 Getting Help

### When You Need Assistant Help

1. **Run error report**:
   ```bash
   ./report_error.sh
   ```

2. **Copy error log content** and share with assistant

3. **Provide context**:
   - What you were trying to do
   - What error occurred
   - Server environment details

### Remote Development Tips

1. **Use Cursor's Remote-SSH** for best experience
2. **Keep terminal sessions open** for real-time monitoring
3. **Use `screen` or `tmux`** for persistent sessions
4. **Set up log forwarding** if needed

## ✅ Success Checklist

- [ ] Server environment setup complete
- [ ] Database configured with pgvector
- [ ] Python environment activated
- [ ] S3 access working (HTTPS URLs)
- [ ] Services starting successfully
- [ ] OpenAlex test ingestion working
- [ ] Enrichment system processing papers
- [ ] Monitoring tools installed
- [ ] Backup strategy in place

## 🎯 Next Steps

1. **Start with small ingestion** to test the system
2. **Monitor resource usage** during processing
3. **Scale up gradually** based on server capacity
4. **Set up automated monitoring** for production
5. **Document server-specific configurations**

---

**Need help?** Run `./report_error.sh` and share the output with the assistant! 