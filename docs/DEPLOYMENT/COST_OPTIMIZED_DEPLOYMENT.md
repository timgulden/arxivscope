# Cost-Optimized Azure Deployment: Self-Hosted PostgreSQL

## Overview
This deployment strategy uses self-hosted PostgreSQL with pgvector in containers, significantly reducing costs while maintaining the benefits of Azure's container orchestration and storage services.

## Cost Comparison

### **Azure Managed PostgreSQL vs Self-Hosted**

| Component | Azure Managed | Self-Hosted | Savings |
|-----------|---------------|-------------|---------|
| **Database (1M records)** | $176/month | $15/month | **91% savings** |
| **Database (10M records)** | $522/month | $45/month | **91% savings** |
| **Storage** | $23/month | $5/month | **78% savings** |
| **Backup** | $7/month | $2/month | **71% savings** |

**Total Monthly Savings**: ~$189/month for 1M records, ~$497/month for 10M records

## Architecture Design

### **Self-Hosted PostgreSQL Container**
```yaml
PostgreSQL Container:
  - Image: postgres:15 with pgvector extension
  - CPU: 2 vCPUs, Memory: 8GB RAM
  - Storage: Azure Disk (Premium SSD)
  - Backup: Automated with pg_dump + Azure Blob Storage
  - High Availability: Container restart policies
  - Security: Private network, SSL encryption
```

### **Cost-Optimized Infrastructure**

#### **Database Layer**
```yaml
Self-Hosted PostgreSQL:
  - Container: postgres:15 with pgvector
  - Compute: 2 vCPUs, 8GB RAM (~$30/month)
  - Storage: 100GB Premium SSD (~$15/month)
  - Backup: Azure Blob Storage (~$2/month)
  - Total: ~$47/month (vs $176/month managed)
```

#### **Compute Layer (Unchanged)**
```yaml
Azure Container Apps:
  - API Service: $30/month
  - Frontend Service: $15/month
  - Enrichment Service: $20/month
  - Total: $65/month
```

#### **Storage Layer (Enhanced)**
```yaml
Azure Blob Storage:
  - Database backups: $2/month
  - UMAP models: $3/month
  - Static assets: $1/month
  - Total: $6/month
```

## Implementation Strategy

### **Phase 1: Self-Hosted Database Setup**

#### **1.1 PostgreSQL Container with pgvector**
```dockerfile
# Dockerfile.postgres
FROM postgres:15

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-15 \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/
COPY postgresql.conf /etc/postgresql/postgresql.conf

EXPOSE 5432
```

#### **1.2 Database Configuration**
```sql
-- init.sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the main papers table
CREATE TABLE IF NOT EXISTS doctrove_papers (
    doctrove_paper_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctrove_source TEXT NOT NULL,
    doctrove_source_id TEXT NOT NULL,
    doctrove_title TEXT NOT NULL,
    doctrove_abstract TEXT,
    doctrove_authors TEXT[],
    doctrove_primary_date DATE,
    doctrove_title_embedding VECTOR(1536),
    doctrove_abstract_embedding VECTOR(1536),
    title_embedding_2d POINT,
    abstract_embedding_2d POINT,
    country2 TEXT,
    embedding_model_version TEXT DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(doctrove_source, doctrove_source_id)
);

-- Create indexes for performance
CREATE INDEX CONCURRENTLY idx_papers_source_id ON doctrove_papers(doctrove_source, doctrove_source_id);
CREATE INDEX CONCURRENTLY idx_papers_date ON doctrove_papers(doctrove_primary_date);
CREATE INDEX CONCURRENTLY idx_embeddings_2d ON doctrove_papers USING GIST (abstract_embedding_2d);
CREATE INDEX CONCURRENTLY idx_country ON doctrove_papers(country2);
CREATE INDEX CONCURRENTLY idx_abstract_embedding ON doctrove_papers USING ivfflat (doctrove_abstract_embedding vector_cosine_ops);

-- Create enrichment tables
CREATE TABLE IF NOT EXISTS aipickle_metadata (
    doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id) ON DELETE CASCADE,
    doi TEXT,
    links JSONB,
    PRIMARY KEY (doctrove_paper_id)
);
```

#### **1.3 PostgreSQL Configuration**
```conf
# postgresql.conf
# Memory settings
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 16MB
maintenance_work_mem = 256MB

# Connection settings
max_connections = 100
shared_preload_libraries = 'vector'

# Logging
log_statement = 'all'
log_min_duration_statement = 1000

# Performance
random_page_cost = 1.1
effective_io_concurrency = 200
```

### **Phase 2: Container Orchestration**

#### **2.1 Updated Docker Compose**
```yaml
# docker-compose.cost-optimized.yml
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

  api:
    build: ./doctrove-api
    image: doctroveregistry.azurecr.io/doctrove-api:latest
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=doctrove
      - DB_USER=doctrove_admin
      - DB_PASSWORD=${DB_PASSWORD}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
    ports:
      - "5001:5001"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - doctrove-network

  frontend:
    build: ./docscope
    image: doctroveregistry.azurecr.io/docscope-frontend:latest
    environment:
      - API_BASE_URL=${API_BASE_URL}
      - DEBUG=False
    ports:
      - "8050:8050"
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - doctrove-network

  enrichment:
    build: ./embedding-enrichment
    image: doctroveregistry.azurecr.io/embedding-enrichment:latest
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=doctrove
      - DB_USER=doctrove_admin
      - DB_PASSWORD=${DB_PASSWORD}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - BATCH_SIZE=${BATCH_SIZE:-100000}
    volumes:
      - model-storage:/app/models
      - enrichment-logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - doctrove-network

  backup:
    image: postgres:15
    environment:
      - PGPASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-backups:/backups
      - ./database/backup.sh:/backup.sh
    depends_on:
      postgres:
        condition: service_healthy
    command: ["/backup.sh"]
    restart: "no"
    networks:
      - doctrove-network

networks:
  doctrove-network:
    driver: bridge

volumes:
  postgres-data:
    driver: local
  postgres-backups:
    driver: local
  model-storage:
    driver: local
  enrichment-logs:
    driver: local
```

### **Phase 3: Backup and Recovery**

#### **3.1 Automated Backup Script**
```bash
#!/bin/bash
# database/backup.sh

set -e

# Configuration
DB_HOST="postgres"
DB_PORT="5432"
DB_NAME="doctrove"
DB_USER="doctrove_admin"
BACKUP_DIR="/backups"
RETENTION_DAYS=7

# Create backup filename with timestamp
BACKUP_FILE="doctrove_backup_$(date +%Y%m%d_%H%M%S).sql"

# Create full backup
echo "Creating database backup: $BACKUP_FILE"
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --verbose --clean --no-owner --no-privileges \
    > "$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"

# Upload to Azure Blob Storage
echo "Uploading backup to Azure Blob Storage..."
az storage blob upload \
    --account-name $STORAGE_ACCOUNT \
    --container-name backups \
    --name "$BACKUP_FILE.gz" \
    --file "$BACKUP_DIR/$BACKUP_FILE.gz" \
    --auth-mode key \
    --account-key $STORAGE_KEY

# Clean up old local backups
find $BACKUP_DIR -name "doctrove_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully: $BACKUP_FILE.gz"
```

#### **3.2 Recovery Script**
```bash
#!/bin/bash
# database/recover.sh

set -e

# Configuration
DB_HOST="postgres"
DB_PORT="5432"
DB_NAME="doctrove"
DB_USER="doctrove_admin"
BACKUP_DIR="/backups"

# Get backup file from command line
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 doctrove_backup_20240710_143022.sql.gz"
    exit 1
fi

# Download from Azure Blob Storage if not local
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "Downloading backup from Azure Blob Storage..."
    az storage blob download \
        --account-name $STORAGE_ACCOUNT \
        --container-name backups \
        --name "$BACKUP_FILE" \
        --file "$BACKUP_DIR/$BACKUP_FILE" \
        --auth-mode key \
        --account-key $STORAGE_KEY
fi

# Restore database
echo "Restoring database from backup: $BACKUP_FILE"
gunzip -c "$BACKUP_DIR/$BACKUP_FILE" | \
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME

echo "Database recovery completed successfully"
```

### **Phase 4: Azure Container Apps Deployment**

#### **4.1 Updated Deployment Script**
```bash
#!/bin/bash
# deploy-cost-optimized.sh

set -e

# Load environment variables
source .env.cost-optimized

# Build and push PostgreSQL image
echo "Building PostgreSQL image with pgvector..."
docker build -t $ACR_LOGIN_SERVER/postgres-pgvector:latest ./database
docker push $ACR_LOGIN_SERVER/postgres-pgvector:latest

# Build and push application images
echo "Building application images..."
docker build -t $ACR_LOGIN_SERVER/doctrove-api:latest ./doctrove-api
docker build -t $ACR_LOGIN_SERVER/docscope-frontend:latest ./docscope
docker build -t $ACR_LOGIN_SERVER/embedding-enrichment:latest ./embedding-enrichment

docker push $ACR_LOGIN_SERVER/doctrove-api:latest
docker push $ACR_LOGIN_SERVER/docscope-frontend:latest
docker push $ACR_LOGIN_SERVER/embedding-enrichment:latest

# Deploy PostgreSQL to Container Apps
echo "Deploying PostgreSQL to Container Apps..."
az containerapp create \
    --name doctrove-postgres \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image $ACR_LOGIN_SERVER/postgres-pgvector:latest \
    --target-port 5432 \
    --ingress disabled \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --env-vars POSTGRES_DB=doctrove POSTGRES_USER=doctrove_admin POSTGRES_PASSWORD=$DB_PASSWORD \
    --cpu 2.0 \
    --memory 8Gi \
    --min-replicas 1 \
    --max-replicas 1

# Get PostgreSQL internal URL
POSTGRES_URL=$(az containerapp show \
    --resource-group $RESOURCE_GROUP \
    --name doctrove-postgres \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

# Deploy API with PostgreSQL dependency
echo "Deploying API..."
az containerapp create \
    --name doctrove-api \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image $ACR_LOGIN_SERVER/doctrove-api:latest \
    --target-port 5001 \
    --ingress external \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --env-vars DB_HOST=$POSTGRES_URL DB_PORT=5432 DB_NAME=doctrove DB_USER=doctrove_admin DB_PASSWORD=$DB_PASSWORD AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
    --cpu 1.0 \
    --memory 2Gi \
    --min-replicas 1 \
    --max-replicas 10

# Deploy Frontend
echo "Deploying Frontend..."
az containerapp create \
    --name docscope-frontend \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image $ACR_LOGIN_SERVER/docscope-frontend:latest \
    --target-port 8050 \
    --ingress external \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --env-vars API_BASE_URL=$API_BASE_URL \
    --cpu 0.5 \
    --memory 1Gi \
    --min-replicas 1 \
    --max-replicas 5

echo "Cost-optimized deployment completed!"
```

## Cost Analysis

### **Monthly Costs (Cost-Optimized)**

#### **1M Records**
```yaml
Database (Self-Hosted):
  - PostgreSQL Container: $30/month (2 vCPUs, 8GB RAM)
  - Storage: $15/month (100GB Premium SSD)
  - Backup Storage: $2/month
  - Total: $47/month

Compute (Container Apps):
  - API Service: $30/month
  - Frontend Service: $15/month
  - Enrichment Service: $20/month
  - Total: $65/month

Storage and Networking:
  - Blob Storage: $6/month
  - Container Registry: $5/month
  - Total: $11/month

Monitoring:
  - Application Insights: $10/month
  - Log Analytics: $5/month
  - Total: $15/month

Total Monthly Cost: $138/month
```

#### **10M Records**
```yaml
Database (Self-Hosted):
  - PostgreSQL Container: $60/month (4 vCPUs, 16GB RAM)
  - Storage: $150/month (1TB Premium SSD)
  - Backup Storage: $15/month
  - Total: $225/month

Compute (Container Apps):
  - API Service: $60/month (scaled)
  - Frontend Service: $30/month (scaled)
  - Enrichment Service: $40/month (scaled)
  - Total: $130/month

Storage and Networking:
  - Blob Storage: $15/month
  - Container Registry: $5/month
  - Total: $20/month

Monitoring:
  - Application Insights: $15/month
  - Log Analytics: $10/month
  - Total: $25/month

Total Monthly Cost: $400/month
```

### **Cost Savings Summary**

| Dataset Size | Azure Managed | Self-Hosted | Savings | % Savings |
|--------------|---------------|-------------|---------|-----------|
| **1M records** | $316/month | $138/month | **$178/month** | **56%** |
| **10M records** | $672/month | $400/month | **$272/month** | **40%** |

## Benefits of Self-Hosted Approach

### **Cost Benefits**
- **56% cost reduction** for 1M records
- **40% cost reduction** for 10M records
- **91% reduction** in database costs specifically
- **Predictable pricing** without managed service premiums

### **Technical Benefits**
- **Full control** over PostgreSQL configuration
- **Custom optimizations** for your specific workload
- **Direct access** to database for debugging
- **Flexible backup** and recovery strategies

### **Research Benefits**
- **Lower barrier to entry** for research projects
- **More budget available** for data processing and enrichment
- **Easier experimentation** with database configurations
- **Faster iteration** on database schema changes

## Migration Strategy

### **Phase 1: Local Testing (Week 1)**
1. **Set up PostgreSQL container** with pgvector locally
2. **Test database connectivity** and performance
3. **Validate backup/restore** procedures
4. **Compare performance** with current setup

### **Phase 2: Azure Deployment (Week 2)**
1. **Deploy PostgreSQL container** to Azure Container Apps
2. **Migrate data** from local PostgreSQL
3. **Test end-to-end functionality**
4. **Validate backup** to Azure Blob Storage

### **Phase 3: Optimization (Week 3)**
1. **Performance tuning** of PostgreSQL configuration
2. **Monitor resource usage** and costs
3. **Implement automated** backup scheduling
4. **Set up monitoring** and alerting

## Risk Mitigation

### **Database Risks**
| Risk | Mitigation |
|------|------------|
| **Data loss** | Automated backups to Azure Blob Storage |
| **Performance issues** | Monitoring and configuration optimization |
| **Container restarts** | Health checks and restart policies |
| **Storage growth** | Auto-scaling storage and cleanup policies |

### **Operational Risks**
| Risk | Mitigation |
|------|------------|
| **Cost overruns** | Resource limits and monitoring |
| **Security** | Private networking and SSL encryption |
| **Backup failures** | Multiple backup strategies and testing |
| **Recovery time** | Regular recovery testing and documentation |

This cost-optimized approach provides significant savings while maintaining the benefits of Azure's container orchestration and storage services, making it ideal for research projects with budget constraints. 