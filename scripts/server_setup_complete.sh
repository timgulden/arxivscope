#!/bin/bash

# DocScope Server Setup - Complete Database Rebuild and Deployment
# This script sets up a fresh DocScope installation with performance optimizations
# Run as: ./scripts/server_setup_complete.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}DocScope Server Setup - Complete Database Rebuild${NC}"
echo "=================================================="
echo "This script will:"
echo "1. Set up PostgreSQL with pgvector"
echo "2. Create fresh doctrove database"
echo "3. Apply schema and performance indexes"
echo "4. Set up Python environment"
echo "5. Prepare for data ingestion"
echo ""

# Configuration
PROJECT_DIR="/home/tgulden/arxivscope-back-end-v2"
DB_NAME="doctrove"
DB_USER="postgres"
PYTHON_VERSION="3.10"

# Function to log steps
log_step() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_system_requirements() {
    log_step "Checking system requirements..."
    
    # Check if running as tgulden user
    if [ "$USER" != "tgulden" ]; then
        log_error "This script must be run as tgulden user"
        exit 1
    fi
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    log_success "System requirements check passed"
}

# Function to update system packages
update_system() {
    log_step "Updating system packages..."
    
    sudo apt update
    sudo apt upgrade -y
    
    log_success "System packages updated"
}

# Function to install PostgreSQL and pgvector
install_postgresql() {
    log_step "Installing PostgreSQL and pgvector..."
    
    # Check if PostgreSQL is already installed
    if command_exists psql; then
        log_warning "PostgreSQL is already installed"
        return 0
    fi
    
    # Install PostgreSQL
    sudo apt install -y postgresql postgresql-contrib
    
    # Install build dependencies for pgvector
    sudo apt install -y build-essential git postgresql-server-dev-15
    
    # Clone and build pgvector
    cd /tmp
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    sudo make install
    
    log_success "PostgreSQL and pgvector installed"
}

# Function to configure PostgreSQL
configure_postgresql() {
    log_step "Configuring PostgreSQL..."
    
    # Start PostgreSQL service
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Drop existing database if it exists and create fresh
    sudo -u postgres dropdb "$DB_NAME" 2>/dev/null || true
    sudo -u postgres createdb "$DB_NAME"
    
    # Enable pgvector extension
    sudo -u postgres psql -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"
    
    log_success "PostgreSQL configured with doctrove database"
}

# Function to apply database schema
apply_database_schema() {
    log_step "Applying database schema..."
    
    cd "$PROJECT_DIR"
    
    # Apply main schema
    sudo -u postgres psql -d "$DB_NAME" -f "doctrove_schema.sql"
    
    # Apply database functions
    sudo -u postgres psql -d "$DB_NAME" -f "embedding-enrichment/setup_database_functions.sql"
    
    # Create enrichment queue table
    sudo -u postgres psql -d "$DB_NAME" -c "
        CREATE TABLE IF NOT EXISTS enrichment_queue (
            id SERIAL PRIMARY KEY,
            paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
            enrichment_type TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            processed_at TIMESTAMP,
            status TEXT DEFAULT 'pending'
        );
    "
    
    # Apply event triggers
    sudo -u postgres psql -d "$DB_NAME" -f "embedding-enrichment/event_triggers.sql"
    
    log_success "Database schema applied"
}

# Function to apply performance indexes
apply_performance_indexes() {
    log_step "Applying performance indexes..."
    
    cd "$PROJECT_DIR"
    
    # Run the performance index script with sudo
    sudo ./scripts/apply_performance_indexes.sh
    
    log_success "Performance indexes applied"
}

# Function to set up Python environment
setup_python_environment() {
    log_step "Setting up Python environment..."
    
    cd "$PROJECT_DIR"
    
    # Install Python if not present
    if ! command_exists python3; then
        sudo apt install -y python3 python3-pip python3-venv
    fi
    
    # Create virtual environment
    python3 -m venv arxivscope
    
    # Activate virtual environment
    source arxivscope/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    # Install component-specific requirements
    pip install -r doc-ingestor/requirements.txt
    pip install -r embedding-enrichment/requirements.txt
    pip install -r doctrove-api/requirements.txt
    
    log_success "Python environment set up"
}

# Function to create configuration files
create_config_files() {
    log_step "Creating configuration files..."
    
    cd "$PROJECT_DIR"
    
    # Create database configuration
    cat > doc-ingestor/config.local.py << EOF
# Database configuration for server
DATABASE_URL = "postgresql://postgres@localhost/doctrove"
EOF
    
    # Create API configuration
    cat > doctrove-api/config.local.py << EOF
# API configuration for server
DEBUG = False
HOST = "0.0.0.0"
PORT = 5001
DATABASE_URL = "postgresql://postgres@localhost/doctrove"
EOF
    
    # Create frontend configuration
    cat > docscope/config/local.py << EOF
# Frontend configuration for server
API_BASE_URL = "http://localhost:5001"
DEBUG = False
EOF
    
    log_success "Configuration files created"
}

# Function to set up data directories
setup_data_directories() {
    log_step "Setting up data directories..."
    
    # Create data directories
    mkdir -p ~/Documents/doctrove-data
    mkdir -p ~/Documents/doctrove-data/marc-files
    mkdir -p ~/Documents/doctrove-data/openalex
    mkdir -p ~/Documents/doctrove-data/openalex/temp
    
    log_success "Data directories created"
}

# Function to test database connection
test_database_connection() {
    log_step "Testing database connection..."
    
    cd "$PROJECT_DIR"
    source arxivscope/bin/activate
    
    # Test database connection
    python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres@localhost/doctrove')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"
    
    log_success "Database connection test passed"
}

# Function to create startup scripts
create_startup_scripts() {
    log_step "Creating startup scripts..."
    
    cd "$PROJECT_DIR"
    
    # Create systemd service files
    sudo tee /etc/systemd/system/doctrove-api.service > /dev/null << EOF
[Unit]
Description=DocTrove API Server
After=network.target postgresql.service

[Service]
Type=simple
User=tgulden
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/arxivscope/bin
ExecStart=$PROJECT_DIR/arxivscope/bin/python doctrove-api/api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo tee /etc/systemd/system/doctrove-enrichment.service > /dev/null << EOF
[Unit]
Description=DocTrove Enrichment Service
After=network.target postgresql.service

[Service]
Type=simple
User=tgulden
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/arxivscope/bin
ExecStart=$PROJECT_DIR/arxivscope/bin/python embedding-enrichment/event_listener.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    log_success "Startup scripts created"
}

# Function to create deployment summary
create_deployment_summary() {
    log_step "Creating deployment summary..."
    
    cd "$PROJECT_DIR"
    
    cat > DEPLOYMENT_SUMMARY.md << EOF
# DocScope Server Deployment Summary

## Deployment Date
$(date)

## Server Information
- **Server IP**: 10.22.198.120
- **User**: tgulden
- **Project Directory**: $PROJECT_DIR
- **Database**: doctrove

## Components Installed
- ✅ PostgreSQL 15 with pgvector extension
- ✅ Python 3.10 virtual environment
- ✅ Database schema and performance indexes
- ✅ Event-driven enrichment system
- ✅ API server (port 5001)
- ✅ Frontend application (port 8050)

## Database Status
- **Database Name**: doctrove
- **Schema Applied**: doctrove_schema.sql
- **Performance Indexes**: Applied
- **Event Triggers**: Active

## Services
- **API Service**: doctrove-api.service
- **Enrichment Service**: doctrove-enrichment.service

## Data Directories
- **Main Data**: ~/Documents/doctrove-data/
- **MARC Files**: ~/Documents/doctrove-data/marc-files/
- **OpenAlex Data**: ~/Documents/doctrove-data/openalex/

## Next Steps
1. Copy data files to ~/Documents/doctrove-data/
2. Run data ingestion: \`cd $PROJECT_DIR && source arxivscope/bin/activate && python doc-ingestor/main_ingestor.py --file-path /path/to/data.pkl --source arxivscope\`
3. Start services: \`sudo systemctl start doctrove-api doctrove-enrichment\`
4. Access frontend: http://10.22.198.120:8050

## Performance Optimizations
- Composite indexes for bounding box queries
- Source-specific optimizations
- Metadata table indexes
- Monitoring functions installed

## Configuration Files
- doc-ingestor/config.local.py
- doctrove-api/config.local.py
- docscope/config/local.py
EOF
    
    log_success "Deployment summary created"
}

# Main execution function
main() {
    echo "Starting DocScope server setup..."
    echo "Project directory: $PROJECT_DIR"
    echo "Database: $DB_NAME"
    echo ""
    
    # Run setup steps
    check_system_requirements
    update_system
    install_postgresql
    configure_postgresql
    apply_database_schema
    apply_performance_indexes
    setup_python_environment
    create_config_files
    setup_data_directories
    test_database_connection
    create_startup_scripts
    create_deployment_summary
    
    echo ""
    echo -e "${GREEN}🎉 DocScope server setup completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Copy your data files to ~/Documents/doctrove-data/"
    echo "2. Run data ingestion with: python doc-ingestor/main_ingestor.py"
    echo "3. Start services with: sudo systemctl start doctrove-api doctrove-enrichment"
    echo "4. Access the application at: http://10.22.198.120:8050"
    echo ""
    echo -e "${BLUE}Deployment Summary:${NC}"
    echo "See DEPLOYMENT_SUMMARY.md for complete details"
    echo ""
    echo -e "${GREEN}Setup complete! 🚀${NC}"
}

# Run main function
main "$@" 