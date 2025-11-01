# Quick Start: Open-Source Server Deployment

> **Note**: This document describes server deployment procedures. The current system (October 2025) runs on a local laptop environment. For current setup information, see [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md).
>
> This guide is preserved for reference if server deployment is needed in the future.

## Overview
This guide helps you deploy DocTrove on an existing server with minimal cost and maximum control. Perfect for internal research use with access to server capacity.

## Prerequisites

### **Server Requirements**
```yaml
Minimum (for 1M records):
  - CPU: 4 cores
  - RAM: 16GB
  - Storage: 500GB available space
  - OS: Ubuntu 20.04+ or CentOS 8+

Recommended (for 10M+ records):
  - CPU: 8+ cores
  - RAM: 32GB+
  - Storage: 1TB+ available space
  - OS: Ubuntu 22.04 LTS
```

### **Access Requirements**
- SSH access to the server
- Sudo privileges
- Port access (80, 443, 5001, 3000, 8050, 9090)
  - **Note**: Current local setup uses ports 5001 (API), 3000 (React Frontend), 5432 (PostgreSQL)

## Quick Deployment Steps

### **Step 1: Server Preparation (30 minutes)**

```bash
# Connect to your server
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git htop vim docker.io docker-compose

# Create doctrove user
sudo useradd -m -s /bin/bash doctrove
sudo usermod -aG docker doctrove
sudo usermod -aG sudo doctrove

# Create application directory
sudo mkdir -p /opt/doctrove
sudo chown doctrove:doctrove /opt/doctrove
```

### **Step 2: PostgreSQL Setup (20 minutes)**

```bash
# Switch to doctrove user
sudo su - doctrove

# Install PostgreSQL
sudo apt install -y postgresql-15 postgresql-contrib-15 postgresql-server-dev-15

# Install pgvector
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Configure PostgreSQL
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -c "CREATE DATABASE doctrove;"
sudo -u postgres psql -c "CREATE USER doctrove_admin WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE doctrove TO doctrove_admin;"

# Test connection
psql -h localhost -U doctrove_admin -d doctrove -c "SELECT version();"
```

### **Step 3: Application Deployment (30 minutes)**

```bash
# Clone your repository
cd /opt/doctrove
git clone https://code.rand.org/arxivscope-projects/arxivscope-back-end.git
cd arxivscope-back-end

# Create environment file
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=doctrove
DB_USER=doctrove_admin
DB_PASSWORD=your_secure_password
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
BATCH_SIZE=100000
EOF

# Create Docker Compose file
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  api:
    build: ./doctrove-api
    image: doctrove-api:latest
    environment:
      - DB_HOST=host.docker.internal
      - DB_PORT=5432
      - DB_NAME=doctrove
      - DB_USER=doctrove_admin
      - DB_PASSWORD=${DB_PASSWORD}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
    ports:
      - "5001:5001"
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"

  frontend:
    build: ./docscope
    image: doctrove-frontend:latest
    environment:
      - API_BASE_URL=http://localhost:5001
      - DEBUG=False
    ports:
      - "8050:8050"
    depends_on:
      - api
    restart: unless-stopped

  enrichment:
    build: ./embedding-enrichment
    image: doctrove-enrichment:latest
    environment:
      - DB_HOST=host.docker.internal
      - DB_PORT=5432
      - DB_NAME=doctrove
      - DB_USER=doctrove_admin
      - DB_PASSWORD=${DB_PASSWORD}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - BATCH_SIZE=${BATCH_SIZE}
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    depends_on:
      - api
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped

volumes:
  grafana_data:
EOF

# Build and start services
docker-compose build
docker-compose up -d
```

### **Step 4: Data Migration (15 minutes)**

```bash
# Export current data from your local machine
pg_dump -h localhost -U tgulden -d doctrove --schema-only > schema.sql
pg_dump -h localhost -U tgulden -d doctrove --data-only > data.sql

# Transfer to server (from your local machine)
scp schema.sql data.sql user@your-server-ip:/tmp/

# Import on server
psql -h localhost -U doctrove_admin -d doctrove -f /tmp/schema.sql
psql -h localhost -U doctrove_admin -d doctrove -f /tmp/data.sql
```

### **Step 5: Verification (10 minutes)**

```bash
# Check services
docker-compose ps

# Test API
curl http://localhost:5001/api/health

# Test frontend
curl http://localhost:8050

# Check database
psql -h localhost -U doctrove_admin -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"
```

## Configuration Files

### **PostgreSQL Optimization**
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

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### **Backup Script**
```bash
# Create backup script
cat > /opt/doctrove/backup.sh << 'EOF'
#!/bin/bash
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_PASSWORD="your_secure_password"
BACKUP_DIR="/opt/doctrove/backups"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="doctrove_backup_$(date +%Y%m%d_%H%M%S).sql"

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

gzip "$BACKUP_DIR/$BACKUP_FILE"
find "$BACKUP_DIR" -name "doctrove_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE.gz"
EOF

chmod +x /opt/doctrove/backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/doctrove/backup.sh") | crontab -
```

## Monitoring Setup

### **Basic Monitoring**
```bash
# Install monitoring containers
docker run -d \
    --name node-exporter \
    --restart unless-stopped \
    -p 9100:9100 \
    -v "/:/host:ro,rslave" \
    prom/node-exporter:latest \
    --path.rootfs=/host

docker run -d \
    --name postgres-exporter \
    --restart unless-stopped \
    -p 9187:9187 \
    -e DATA_SOURCE_NAME="postgresql://doctrove_admin:your_secure_password@host.docker.internal:5432/doctrove?sslmode=disable" \
    prometheuscommunity/postgres-exporter:latest

# Access Grafana at http://your-server-ip:3000
# Username: admin, Password: admin
```

## Access URLs

Once deployed, your services will be available at:

```yaml
React Frontend: http://your-server-ip:3000
Legacy Dash Frontend: http://your-server-ip:8050
API: http://your-server-ip:5001
Grafana: http://your-server-ip:3000 (if using Grafana)
PostgreSQL: localhost:5432 (from server)
```

> **Note**: Current local laptop setup:
> - React Frontend: http://localhost:3000
> - API: http://localhost:5001
> - PostgreSQL: localhost:5432 (internal drive)

## Maintenance Commands

### **Daily Operations**
```bash
# Check service status
docker-compose ps
docker stats

# View logs
docker-compose logs api
docker-compose logs frontend

# Restart services
docker-compose restart

# Update application
git pull origin main
docker-compose build
docker-compose up -d
```

### **Database Maintenance**
```bash
# Connect to database
psql -h localhost -U doctrove_admin -d doctrove

# Run maintenance
VACUUM ANALYZE;
REINDEX DATABASE doctrove;

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Troubleshooting

### **Common Issues**

**Service won't start:**
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h
```

**Database connection issues:**
```bash
# Test connection
psql -h localhost -U doctrove_admin -d doctrove

# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

**Port conflicts:**
```bash
# Check what's using ports
sudo netstat -tlnp | grep :5001  # API
sudo netstat -tlnp | grep :3000  # React Frontend
sudo netstat -tlnp | grep :8050  # Legacy Dash Frontend
```

## Cost Analysis

### **Your Open-Source Deployment**
```yaml
One-time Costs:
  - Hardware: $0 (using existing server)
  - Setup time: 2-3 hours

Ongoing Costs:
  - Electricity: $0 (server already running)
  - Internet: $0 (existing connection)
  - Maintenance: $0 (DIY)
  - Total: $0/month

Annual Cost: $0
3-Year Cost: $0
```

### **Savings Comparison**
```yaml
vs Azure Managed: $9,432 savings over 3 years
vs Self-Hosted Azure: $4,788 savings over 3 years
vs Open-Source with new hardware: $7,100 savings over 3 years
```

## Next Steps

1. **Deploy and test** the basic setup
2. **Migrate your data** from local development
3. **Configure monitoring** and alerts
4. **Set up automated backups**
5. **Optimize performance** based on usage patterns
6. **Consider scaling** if needed (add more resources)

This approach gives you maximum control and zero ongoing costs while leveraging existing infrastructure. Perfect for research projects! 