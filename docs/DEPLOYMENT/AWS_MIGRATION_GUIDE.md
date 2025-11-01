# AWS Migration Guide: Test Environment Setup

> **Note**: This system has been migrated from a server installation to a local laptop environment (October 2025). The AWS migration described in this guide has been completed, and the system now runs locally with:
> - **API**: Port 5001 (changed from server/AWS configuration)
> - **Frontend**: Port 3000 (React, changed from server/AWS configuration)
> - **PostgreSQL**: Port 5432 on internal drive (changed from server/AWS paths)
> - **Database Location**: `/opt/homebrew/var/postgresql@14` (macOS with Homebrew)
> - **Models**: Stored on internal drive (not external/server paths)
>
> This migration guide is preserved for reference if AWS deployment is needed in the future. For current setup information, see [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md).

## Overview

This guide provides step-by-step instructions for migrating your local DocScope/DocTrove system to an AWS EC2 instance for testing purposes. This focuses on getting the system running quickly without advanced features like SSL, hardening, or automated backups.

## Prerequisites

### **AWS Account Requirements**
- AWS account with billing enabled
- Access to EC2, VPC, and Security Groups
- SSH key pair for EC2 access
- Basic familiarity with AWS console

### **Local System Requirements**
- SSH client (built into macOS/Linux, PuTTY for Windows)
- Git for code deployment
- Local database dump (if migrating existing data)

## Step 1: AWS Infrastructure Setup

### **1.1 Launch EC2 Instance**

#### **Instance Configuration**
```yaml
Instance Type: t3.xlarge (4 vCPU, 16GB RAM)
AMI: Ubuntu 22.04 LTS (ami-0c7217cdde317cfec for us-east-1)
Storage: 100GB gp3 EBS volume
Key Pair: Create or select existing SSH key pair
Security Group: Create new (see below)
```

#### **Security Group Configuration**
Create a new security group with these rules:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | Your IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP access |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS access |
| Custom TCP | TCP | 5001 | 0.0.0.0/0 | DocTrove API |
| Custom TCP | TCP | 8050 | 0.0.0.0/0 | DocScope Frontend |
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | Grafana Monitoring |

#### **AWS Console Steps**
1. **EC2 Dashboard** → **Launch Instance**
2. **Name**: `doctrove-test`
3. **AMI**: Ubuntu 22.04 LTS
4. **Instance Type**: t3.xlarge
5. **Key Pair**: Create new or select existing
6. **Network Settings**: Create security group (see above)
7. **Storage**: 100GB gp3
8. **Launch Instance**

### **1.2 Allocate Elastic IP (Optional but Recommended)**

1. **EC2 Dashboard** → **Elastic IPs** → **Allocate Elastic IP**
2. **Allocate** → **Associate with Instance**
3. **Select your instance** → **Associate**

**Note**: Elastic IP costs ~$3-4/month when not attached to running instances.

### **1.3 Connect to Your Instance**

**macOS/Linux:**
```bash
# Replace with your key file and instance IP
ssh -i ~/.ssh/your-key.pem ubuntu@your-instance-ip

# Or with Elastic IP
ssh -i ~/.ssh/your-key.pem ubuntu@your-elastic-ip
```

**Windows (PowerShell):**
```powershell
# Replace with your key file and instance IP
ssh -i C:\Users\YourUser\.ssh\your-key.pem ubuntu@your-instance-ip

# Or with Elastic IP
ssh -i C:\Users\YourUser\.ssh\your-key.pem ubuntu@your-elastic-ip
```

**Windows (Git Bash):**
```bash
# Replace with your key file and instance IP
ssh -i ~/.ssh/your-key.pem ubuntu@your-instance-ip

# Or with Elastic IP
ssh -i ~/.ssh/your-key.pem ubuntu@your-elastic-ip
```

## Step 2: Server Preparation

### **2.1 System Updates and Basic Setup**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git htop vim nano unzip \
    software-properties-common apt-transport-https \
    ca-certificates gnupg lsb-release

# Create application user
sudo useradd -m -s /bin/bash doctrove
sudo usermod -aG sudo doctrove
sudo usermod -aG docker doctrove

# Create application directory
sudo mkdir -p /opt/doctrove
sudo chown doctrove:doctrove /opt/doctrove
```

### **2.2 Install Docker and Docker Compose**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## Step 3: Database Setup

### **3.1 Install PostgreSQL and pgvector**

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

# Install pgvector
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### **3.2 Configure Database**

```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32)
echo "Database password: $DB_PASSWORD"

# Create database and user
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -c "CREATE DATABASE doctrove;"
sudo -u postgres psql -c "CREATE USER doctrove_admin WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE doctrove TO doctrove_admin;"

# Test connection
psql -h localhost -U doctrove_admin -d doctrove -c "SELECT version();"
```

## Step 4: Application Deployment

### **4.1 Clone and Configure Application**

```bash
# Switch to doctrove user
sudo su - doctrove

# Clone repository
cd /opt/doctrove
git clone https://code.rand.org/arxivscope-projects/arxivscope-back-end.git
cd arxivscope-back-end

# Create environment file
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=doctrove
DB_USER=doctrove_admin
DB_PASSWORD=$DB_PASSWORD
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
BATCH_SIZE=100000
EOF

# Apply database schema
psql -h localhost -U doctrove_admin -d doctrove -f "doctrove_schema.sql"
psql -h localhost -U doctrove_admin -d doctrove -f "embedding-enrichment/setup_database_functions.sql"
psql -h localhost -U doctrove_admin -d doctrove -f "embedding-enrichment/event_triggers.sql"  # REQUIRED for enrichment triggers
```

### **4.2 Create Docker Compose Configuration**

```bash
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
```

### **4.3 Build and Deploy**

```bash
# Build Docker images
docker-compose build

# Start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 5: Data Migration (Optional)

### **5.1 Export Local Data**

On your local machine:

```bash
# Export schema and data
pg_dump -h localhost -U your_local_user -d doctrove --schema-only > schema.sql
pg_dump -h localhost -U your_local_user -d doctrove --data-only > data.sql

# Or export everything
pg_dump -h localhost -U your_local_user -d doctrove > full_backup.sql
```

### **5.2 Import to AWS Instance**

On your AWS instance:

```bash
# Copy files to instance (from local machine)
# macOS/Linux:
scp -i ~/.ssh/your-key.pem schema.sql ubuntu@your-instance-ip:/tmp/
scp -i ~/.ssh/your-key.pem data.sql ubuntu@your-instance-ip:/tmp/

# Windows (PowerShell):
scp -i C:\Users\YourUser\.ssh\your-key.pem schema.sql ubuntu@your-instance-ip:/tmp/
scp -i C:\Users\YourUser\.ssh\your-key.pem data.sql ubuntu@your-instance-ip:/tmp/

# Windows (Git Bash):
scp -i ~/.ssh/your-key.pem schema.sql ubuntu@your-instance-ip:/tmp/
scp -i ~/.ssh/your-key.pem data.sql ubuntu@your-instance-ip:/tmp/

# Import data (on AWS instance)
sudo su - doctrove
cd /opt/doctrove/arxivscope-back-end

# Import schema and data
psql -h localhost -U doctrove_admin -d doctrove -f /tmp/schema.sql
psql -h localhost -U doctrove_admin -d doctrove -f /tmp/data.sql
```

## Step 6: Verification and Testing

### **6.1 Check Service Status**

```bash
# Check all services are running
docker-compose ps

# Check API health
curl http://localhost:5001/api/health

# Check database connection
psql -h localhost -U doctrove_admin -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"
```

### **6.2 Access Applications**

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| **DocScope Frontend** | `http://your-instance-ip:8050` | None |
| **DocTrove API** | `http://your-instance-ip:5001` | None |
| **Grafana Monitoring** | `http://your-instance-ip:3000` | admin/admin |

### **6.3 Test Basic Functionality**

```bash
# Test API endpoints
curl http://your-instance-ip:5001/api/papers?limit=5
curl http://your-instance-ip:5001/api/countries

# Test frontend (open in browser)
# Navigate to http://your-instance-ip:8050
# Try loading the visualization
```

## Step 7: Basic Monitoring and Management

### **7.1 Create Management Scripts**

```bash
# Create status script
cat > /opt/doctrove/status.sh << 'EOF'
#!/bin/bash
echo "=== DocTrove Status ==="
echo "Docker Services:"
docker-compose ps
echo
echo "Database Connection:"
psql -h localhost -U doctrove_admin -d doctrove -c "SELECT COUNT(*) as paper_count FROM doctrove_papers;" 2>/dev/null || echo "Database connection failed"
echo
echo "API Health:"
curl -s http://localhost:5001/api/health || echo "API not responding"
echo
echo "System Resources:"
df -h /
free -h
EOF

chmod +x /opt/doctrove/status.sh

# Create restart script
cat > /opt/doctrove/restart.sh << 'EOF'
#!/bin/bash
cd /opt/doctrove/arxivscope-back-end
docker-compose down
docker-compose up -d
echo "Services restarted"
EOF

chmod +x /opt/doctrove/restart.sh
```

### **7.2 Basic Log Monitoring**

```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f enrichment
```

## Troubleshooting

### **Common Issues and Solutions**

#### **1. Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Test connection
psql -h localhost -U doctrove_admin -d doctrove -c "SELECT 1;"
```

#### **2. Docker Build Failures**
```bash
# Check Docker daemon
sudo systemctl status docker

# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

#### **3. Port Conflicts**
```bash
# Check what's using ports
sudo netstat -tlnp | grep :5001
sudo netstat -tlnp | grep :8050

# Kill processes if needed
sudo kill -9 <PID>
```

#### **4. Memory Issues**
```bash
# Check memory usage
free -h

# Increase swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Cost Optimization

### **Instance Management**
```bash
# Stop services when not testing
docker-compose down

# Stop instance when not in use
# AWS Console → EC2 → Instances → Stop Instance

# Resume testing
# AWS Console → EC2 → Instances → Start Instance
# Wait 1-2 minutes, then SSH and restart services
```

### **Estimated Monthly Costs**
- **t3.xlarge**: ~$50/month (on-demand)
- **EBS Storage**: ~$10/month (100GB)
- **Elastic IP**: ~$3/month
- **Data Transfer**: ~$5-10/month
- **Total**: ~$70-80/month

## Next Steps

Once your test environment is running:

1. **Test all functionality** thoroughly
2. **Migrate your data** if needed
3. **Configure monitoring** (Grafana dashboards)
4. **Set up SSL certificates** (Let's Encrypt)
5. **Implement backup strategy** (S3 + pg_dump)
6. **Security hardening** (firewall rules, user management)
7. **Performance optimization** (database tuning, caching)

## Support

If you encounter issues:

1. **Check logs**: `docker-compose logs -f`
2. **Verify configuration**: Review `.env` and `docker-compose.yml`
3. **Test connectivity**: Use `curl` and `psql` commands
4. **Check resources**: Monitor CPU, memory, and disk usage
5. **Review security groups**: Ensure ports are open in AWS console

---

**Note**: This guide focuses on getting a test environment running quickly. For production deployment, additional security, monitoring, and backup measures should be implemented. 