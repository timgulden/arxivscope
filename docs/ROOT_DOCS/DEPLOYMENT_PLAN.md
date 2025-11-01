# DocScope/DocTrove Azure Deployment Plan

## Overview
This document outlines the migration strategy from local development (Mac laptop) to Azure production infrastructure, designed to handle multi-million record datasets with high availability and persistence.

## Current Architecture Assessment

### Strengths
- ✅ Microservice architecture ready for containerization
- ✅ Database abstraction with PostgreSQL + pgvector
- ✅ Azure-focused design in existing documentation
- ✅ Dockerfiles already present
- ✅ Comprehensive logging and monitoring patterns

### Areas Needing Enhancement
- 🔄 Environment configuration management
- 🔄 Secrets management (API keys, database credentials)
- 🔄 Health checks and monitoring
- 🔄 Backup and disaster recovery procedures
- 🔄 CI/CD pipeline

## Azure Infrastructure Design

### 1. Database Layer (Critical for Persistence)

#### Azure Database for PostgreSQL Flexible Server
```yaml
Configuration:
  - Tier: General Purpose (GP_Standard_D4s_v3)
  - Storage: 100GB initial, auto-scaling up to 16TB
  - High Availability: Zone-redundant deployment
  - Backup: 35-day retention with point-in-time recovery
  - Network: Private endpoint for security
  - Extensions: pgvector, uuid-ossp

Estimated Costs (1M records):
  - Compute: $146/month (4 vCores, 16GB RAM)
  - Storage: $23/month (100GB)
  - Backup: $7/month
  - Total: ~$176/month
```

#### Database Scaling Strategy
```sql
-- Performance optimizations for large datasets
CREATE INDEX CONCURRENTLY idx_papers_source_id ON doctrove_papers(doctrove_source, doctrove_source_id);
CREATE INDEX CONCURRENTLY idx_papers_date ON doctrove_papers(doctrove_primary_date);
CREATE INDEX CONCURRENTLY idx_embeddings_2d ON doctrove_papers USING GIST (abstract_embedding_2d);
CREATE INDEX CONCURRENTLY idx_country ON doctrove_papers(country2);

-- Partitioning for very large datasets (>10M records)
CREATE TABLE doctrove_papers_2024 PARTITION OF doctrove_papers
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### 2. Compute Layer

#### Azure Container Apps
```yaml
Services:
  - doctrove-api:
      - CPU: 1.0 vCPU, Memory: 2GB
      - Min replicas: 1, Max replicas: 10
      - Scaling: HTTP requests, CPU usage
      
  - docscope-frontend:
      - CPU: 0.5 vCPU, Memory: 1GB
      - Min replicas: 1, Max replicas: 5
      - Scaling: HTTP requests
      
  - embedding-enrichment:
      - CPU: 2.0 vCPU, Memory: 4GB
      - Min replicas: 0, Max replicas: 3
      - Scaling: Queue depth, CPU usage
      
  - doc-ingestor:
      - CPU: 1.0 vCPU, Memory: 2GB
      - Min replicas: 0, Max replicas: 2
      - Scaling: Manual (batch processing)
```

#### Container Registry
```yaml
Azure Container Registry:
  - Premium tier for geo-replication
  - Managed identity for secure access
  - Vulnerability scanning
  - Image lifecycle management
```

### 3. Storage Layer

#### Azure Blob Storage
```yaml
Containers:
  - models: UMAP models, trained embeddings
  - backups: Database dumps, configuration backups
  - assets: Static files, documentation
  - temp: Temporary processing files

Lifecycle Management:
  - Hot tier: Recent models and active data
  - Cool tier: Older models and backups
  - Archive tier: Historical data (>90 days)
```

### 4. Networking

#### Virtual Network
```yaml
Components:
  - Private endpoints for database and storage
  - Application Gateway for SSL termination
  - Azure Front Door for global distribution
  - Network Security Groups for access control
```

## Migration Phases

### Phase 1: Infrastructure Setup (Week 1-2)

#### 1.1 Azure Resource Creation
```bash
# Create resource group
az group create --name doctrove-prod --location eastus

# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group doctrove-prod \
  --name doctrove-db-prod \
  --admin-user doctrove-admin \
  --admin-password <secure-password> \
  --sku-name Standard_D4s_v3 \
  --storage-size 100 \
  --version 15 \
  --zone 1

# Enable pgvector extension
az postgres flexible-server parameter set \
  --resource-group doctrove-prod \
  --server-name doctrove-db-prod \
  --name shared_preload_libraries \
  --value vector

# Create Container Registry
az acr create \
  --resource-group doctrove-prod \
  --name doctroveregistry \
  --sku Premium \
  --admin-enabled true
```

#### 1.2 Database Migration
```bash
# Export current schema and data
pg_dump -h localhost -U tgulden -d doctrove --schema-only > schema.sql
pg_dump -h localhost -U tgulden -d doctrove --data-only > data.sql

# Import to Azure PostgreSQL
psql -h doctrove-db-prod.postgres.database.azure.com -U doctrove-admin -d postgres -f schema.sql
psql -h doctrove-db-prod.postgres.database.azure.com -U doctrove-admin -d postgres -f data.sql
```

### Phase 2: Containerization (Week 3)

#### 2.1 Docker Compose for Production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    build: ./doctrove-api
    environment:
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
    ports:
      - "5001:5001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./docscope
    environment:
      - API_BASE_URL=${API_BASE_URL}
    ports:
      - "8050:8050"
    depends_on:
      - api

  enrichment:
    build: ./embedding-enrichment
    environment:
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
    volumes:
      - model-storage:/app/models
    depends_on:
      - api
```

#### 2.2 Environment Configuration
```bash
# .env.production
DB_HOST=doctrove-db-prod.postgres.database.azure.com
DB_PORT=5432
DB_NAME=doctrove
DB_USER=doctrove-admin
DB_PASSWORD=<secure-password>
AZURE_OPENAI_KEY=<azure-openai-key>
API_BASE_URL=https://doctrove-api.azurecontainerapps.io
```

### Phase 3: Azure Container Apps Deployment (Week 4)

#### 3.1 Build and Push Images
```bash
# Build images
docker build -t doctroveregistry.azurecr.io/doctrove-api:latest ./doctrove-api
docker build -t doctroveregistry.azurecr.io/docscope-frontend:latest ./docscope
docker build -t doctroveregistry.azurecr.io/embedding-enrichment:latest ./embedding-enrichment

# Push to registry
az acr login --name doctroveregistry
docker push doctroveregistry.azurecr.io/doctrove-api:latest
docker push doctroveregistry.azurecr.io/docscope-frontend:latest
docker push doctroveregistry.azurecr.io/embedding-enrichment:latest
```

#### 3.2 Deploy to Container Apps
```bash
# Create Container Apps Environment
az containerapp env create \
  --name doctrove-env \
  --resource-group doctrove-prod \
  --location eastus

# Deploy API
az containerapp create \
  --name doctrove-api \
  --resource-group doctrove-prod \
  --environment doctrove-env \
  --image doctroveregistry.azurecr.io/doctrove-api:latest \
  --target-port 5001 \
  --ingress external \
  --registry-server doctroveregistry.azurecr.io \
  --registry-username <acr-username> \
  --registry-password <acr-password> \
  --env-vars DB_HOST=$DB_HOST DB_PORT=$DB_PORT DB_NAME=$DB_NAME DB_USER=$DB_USER DB_PASSWORD=$DB_PASSWORD

# Deploy Frontend
az containerapp create \
  --name docscope-frontend \
  --resource-group doctrove-prod \
  --environment doctrove-env \
  --image doctroveregistry.azurecr.io/docscope-frontend:latest \
  --target-port 8050 \
  --ingress external \
  --registry-server doctroveregistry.azurecr.io \
  --registry-username <acr-username> \
  --registry-password <acr-password> \
  --env-vars API_BASE_URL=https://doctrove-api.azurecontainerapps.io
```

### Phase 4: Monitoring and Optimization (Week 5-6)

#### 4.1 Azure Monitor Setup
```yaml
Monitoring:
  - Application Insights for application performance
  - Log Analytics for centralized logging
  - Metrics for database and container performance
  - Alerts for critical failures and performance degradation
```

#### 4.2 Backup Strategy
```bash
# Automated database backups
az postgres flexible-server backup create \
  --resource-group doctrove-prod \
  --server-name doctrove-db-prod \
  --backup-name daily-backup

# Blob storage backup for models
az storage blob copy start \
  --account-name doctrovestorage \
  --container-name models \
  --name umap_model.pkl \
  --source-uri https://doctrovestorage.blob.core.windows.net/models/umap_model.pkl
```

## Cost Estimation

### Monthly Costs (1M records)
```yaml
Database (PostgreSQL Flexible Server):
  - Compute: $146/month
  - Storage: $23/month
  - Backup: $7/month
  - Total: $176/month

Container Apps:
  - API (1 replica): $30/month
  - Frontend (1 replica): $15/month
  - Enrichment (on-demand): $20/month
  - Total: $65/month

Storage (Blob Storage):
  - Models and backups: $5/month
  - Data transfer: $10/month
  - Total: $15/month

Monitoring and Networking:
  - Application Insights: $10/month
  - Container Registry: $5/month
  - Total: $15/month

Estimated Total: $271/month
```

### Scaling Costs (10M records)
```yaml
Database scaling:
  - Compute: $292/month (8 vCores, 32GB RAM)
  - Storage: $230/month (1TB)
  - Total: $522/month

Container Apps scaling:
  - Additional replicas: $100/month
  - Total: $165/month

Estimated Total: $702/month
```

## Security Considerations

### 1. Network Security
```yaml
- Private endpoints for database and storage
- Network Security Groups with minimal required access
- Azure Front Door for DDoS protection
- SSL/TLS encryption for all communications
```

### 2. Identity and Access Management
```yaml
- Managed identities for service-to-service authentication
- Azure Key Vault for secrets management
- Role-based access control (RBAC)
- Just-in-time access for administrative tasks
```

### 3. Data Protection
```yaml
- Encryption at rest for all data
- Encryption in transit (TLS 1.3)
- Regular security updates and patches
- Compliance with Azure security standards
```

## Disaster Recovery Plan

### 1. Backup Strategy
```yaml
Database:
  - Automated daily backups (35-day retention)
  - Point-in-time recovery capability
  - Cross-region backup replication

Application:
  - Container images in Azure Container Registry
  - Configuration in Azure Key Vault
  - Infrastructure as Code (Terraform/ARM templates)
```

### 2. Recovery Procedures
```yaml
RTO (Recovery Time Objective): 4 hours
RPO (Recovery Point Objective): 1 hour

Recovery Steps:
  1. Restore database from backup
  2. Redeploy container applications
  3. Update DNS and load balancer configuration
  4. Verify application functionality
```

## Next Steps

### Immediate Actions (This Week)
1. **Set up Azure subscription and resource group**
2. **Create PostgreSQL Flexible Server with pgvector**
3. **Test database connectivity from local environment**
4. **Begin containerization of services**

### Short-term Goals (Next 2-4 Weeks)
1. **Complete containerization and testing**
2. **Deploy to Azure Container Apps**
3. **Set up monitoring and alerting**
4. **Implement backup procedures**

### Long-term Goals (Next 2-3 Months)
1. **Scale to handle 1M+ records**
2. **Implement advanced monitoring and optimization**
3. **Add CI/CD pipeline for automated deployments**
4. **Consider multi-region deployment for global access**

## Risk Mitigation

### Technical Risks
- **Database performance**: Implement proper indexing and partitioning
- **Container scaling**: Test auto-scaling under load
- **Data loss**: Implement comprehensive backup strategy
- **API rate limits**: Monitor Azure OpenAI usage and implement caching

### Operational Risks
- **Cost overruns**: Set up budget alerts and monitoring
- **Security breaches**: Regular security audits and updates
- **Service downtime**: Implement health checks and automated recovery
- **Data corruption**: Regular integrity checks and validation

This deployment plan provides a roadmap for transitioning from local development to a production-ready Azure infrastructure capable of handling multi-million record datasets with high availability and persistence. 