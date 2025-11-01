#!/bin/bash
# Azure Deployment Script for DocScope/DocTrove
# This script sets up the complete Azure infrastructure for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
RESOURCE_GROUP="doctrove-prod"
LOCATION="eastus"
DB_SERVER_NAME="doctrove-db-prod"
ACR_NAME="doctroveregistry"
CONTAINER_APP_ENV="doctrove-env"
STORAGE_ACCOUNT="doctrovestorage"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

print_status "Starting Azure infrastructure deployment..."

# Step 1: Create Resource Group
print_status "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION
print_success "Resource group created: $RESOURCE_GROUP"

# Step 2: Create PostgreSQL Flexible Server
print_status "Creating PostgreSQL Flexible Server..."
az postgres flexible-server create \
    --resource-group $RESOURCE_GROUP \
    --name $DB_SERVER_NAME \
    --admin-user doctrove-admin \
    --admin-password $(openssl rand -base64 32) \
    --sku-name Standard_D4s_v3 \
    --storage-size 100 \
    --version 15 \
    --zone 1 \
    --yes

print_success "PostgreSQL server created: $DB_SERVER_NAME"

# Step 3: Enable pgvector extension
print_status "Enabling pgvector extension..."
az postgres flexible-server parameter set \
    --resource-group $RESOURCE_GROUP \
    --server-name $DB_SERVER_NAME \
    --name shared_preload_libraries \
    --value vector

# Restart server to apply changes
az postgres flexible-server restart \
    --resource-group $RESOURCE_GROUP \
    --name $DB_SERVER_NAME

print_success "pgvector extension enabled"

# Step 4: Create Container Registry
print_status "Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Premium \
    --admin-enabled true

print_success "Container Registry created: $ACR_NAME"

# Step 5: Create Storage Account
print_status "Creating Storage Account..."
az storage account create \
    --resource-group $RESOURCE_GROUP \
    --name $STORAGE_ACCOUNT \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2

# Create containers
az storage container create --name models --account-name $STORAGE_ACCOUNT
az storage container create --name backups --account-name $STORAGE_ACCOUNT
az storage container create --name assets --account-name $STORAGE_ACCOUNT
az storage container create --name temp --account-name $STORAGE_ACCOUNT

print_success "Storage Account created: $STORAGE_ACCOUNT"

# Step 6: Create Container Apps Environment
print_status "Creating Container Apps Environment..."
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

print_success "Container Apps Environment created: $CONTAINER_APP_ENV"

# Step 7: Get connection information
print_status "Retrieving connection information..."

DB_HOST=$(az postgres flexible-server show \
    --resource-group $RESOURCE_GROUP \
    --name $DB_SERVER_NAME \
    --query "fullyQualifiedDomainName" \
    --output tsv)

ACR_LOGIN_SERVER=$(az acr show \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --query "loginServer" \
    --output tsv)

ACR_USERNAME=$(az acr credential show \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --query "username" \
    --output tsv)

ACR_PASSWORD=$(az acr credential show \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --query "passwords[0].value" \
    --output tsv)

STORAGE_KEY=$(az storage account keys list \
    --resource-group $RESOURCE_GROUP \
    --account-name $STORAGE_ACCOUNT \
    --query "[0].value" \
    --output tsv)

# Step 8: Create environment file
print_status "Creating environment configuration file..."
cat > .env.production << EOF
# Database Configuration
DB_HOST=$DB_HOST
DB_PORT=5434
DB_NAME=doctrove
DB_USER=doctrove-admin
DB_PASSWORD=<REPLACE_WITH_ACTUAL_PASSWORD>

# Azure OpenAI Configuration
AZURE_OPENAI_KEY=<REPLACE_WITH_YOUR_AZURE_OPENAI_KEY>
AZURE_OPENAI_ENDPOINT=<REPLACE_WITH_YOUR_AZURE_OPENAI_ENDPOINT>

# API Configuration
API_BASE_URL=https://doctrove-api.azurecontainerapps.io

# Container Registry
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
ACR_USERNAME=$ACR_USERNAME
ACR_PASSWORD=$ACR_PASSWORD

# Storage Account
STORAGE_ACCOUNT=$STORAGE_ACCOUNT
STORAGE_KEY=$STORAGE_KEY

# Processing Configuration
BATCH_SIZE=100000
EOF

print_success "Environment file created: .env.production"

# Step 9: Create deployment script
print_status "Creating deployment script..."
cat > deploy-containers.sh << 'EOF'
#!/bin/bash
# Container deployment script

set -e

# Load environment variables
source .env.production

# Login to Azure Container Registry
echo "Logging in to Azure Container Registry..."
az acr login --name $ACR_NAME

# Build and push images
echo "Building and pushing container images..."

# API
docker build -t $ACR_LOGIN_SERVER/doctrove-api:latest ./doctrove-api
docker push $ACR_LOGIN_SERVER/doctrove-api:latest

# Frontend
docker build -t $ACR_LOGIN_SERVER/docscope-frontend:latest ./docscope
docker push $ACR_LOGIN_SERVER/docscope-frontend:latest

# Enrichment
docker build -t $ACR_LOGIN_SERVER/embedding-enrichment:latest ./embedding-enrichment
docker push $ACR_LOGIN_SERVER/embedding-enrichment:latest

# Ingestor
docker build -t $ACR_LOGIN_SERVER/doc-ingestor:latest ./doc-ingestor
docker push $ACR_LOGIN_SERVER/doc-ingestor:latest

echo "Images built and pushed successfully!"

# Deploy to Container Apps
echo "Deploying to Azure Container Apps..."

# Deploy API
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
    --env-vars DB_HOST=$DB_HOST DB_PORT=$DB_PORT DB_NAME=$DB_NAME DB_USER=$DB_USER DB_PASSWORD=$DB_PASSWORD AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
    --cpu 1.0 \
    --memory 2Gi \
    --min-replicas 1 \
    --max-replicas 10

# Deploy Frontend
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

# Deploy Enrichment (manual scaling)
az containerapp create \
    --name embedding-enrichment \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image $ACR_LOGIN_SERVER/embedding-enrichment:latest \
    --target-port 8000 \
    --ingress disabled \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --env-vars DB_HOST=$DB_HOST DB_PORT=$DB_PORT DB_NAME=$DB_NAME DB_USER=$DB_USER DB_PASSWORD=$DB_PASSWORD AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT BATCH_SIZE=$BATCH_SIZE \
    --cpu 2.0 \
    --memory 4Gi \
    --min-replicas 0 \
    --max-replicas 3

echo "Deployment completed successfully!"
echo ""
echo "Access URLs:"
echo "API: https://doctrove-api.azurecontainerapps.io"
echo "Frontend: https://docscope-frontend.azurecontainerapps.io"
EOF

chmod +x deploy-containers.sh
print_success "Deployment script created: deploy-containers.sh"

# Step 10: Create database migration script
print_status "Creating database migration script..."
cat > migrate-database.sh << 'EOF'
#!/bin/bash
# Database migration script

set -e

source .env.production

echo "Starting database migration..."

# Export current schema and data from local database
echo "Exporting current database..."
pg_dump -h localhost -U tgulden -d doctrove --schema-only > schema.sql
pg_dump -h localhost -U tgulden -d doctrove --data-only > data.sql

# Create database on Azure
echo "Creating database on Azure..."
psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE doctrove;"

# Import schema
echo "Importing schema..."
psql -h $DB_HOST -U $DB_USER -d doctrove -f schema.sql

# Import data
echo "Importing data..."
psql -h $DB_HOST -U $DB_USER -d doctrove -f data.sql

# Enable pgvector extension
echo "Enabling pgvector extension..."
psql -h $DB_HOST -U $DB_USER -d doctrove -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "Database migration completed successfully!"
EOF

chmod +x migrate-database.sh
print_success "Database migration script created: migrate-database.sh"

# Summary
print_success "Azure infrastructure deployment completed!"
echo ""
echo "Next steps:"
echo "1. Update .env.production with your actual passwords and API keys"
echo "2. Run ./migrate-database.sh to migrate your data"
echo "3. Run ./deploy-containers.sh to deploy the applications"
echo ""
echo "Resource Information:"
echo "Resource Group: $RESOURCE_GROUP"
echo "Database Server: $DB_HOST"
echo "Container Registry: $ACR_LOGIN_SERVER"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Container Apps Environment: $CONTAINER_APP_ENV"
echo ""
echo "Estimated monthly cost: ~$271/month for 1M records"
echo "Estimated monthly cost: ~$702/month for 10M records" 