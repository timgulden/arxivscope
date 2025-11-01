#!/bin/bash

# DocScope Team Server Setup - Complete Database Rebuild and Deployment
# This script sets up a fresh DocScope installation in a shared location
# Run as: sudo ./scripts/server_setup_team.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}DocScope Team Server Setup - Complete Database Rebuild${NC}"
echo "=================================================="
echo "This script will:"
echo "1. Set up PostgreSQL with pgvector"
echo "2. Create fresh doctrove database"
echo "3. Apply schema and performance indexes"
echo "4. Set up Python environment in shared location"
echo "5. Create systemd services for team management"
echo "6. Set up proper permissions for team access"
echo ""

# Configuration
INSTALL_DIR="/opt/arxivscope"
SERVICE_USER="arxivscope"
SERVICE_GROUP="arxivscope"
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

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to create service user and group
create_service_user() {
    log_step "Creating service user and group..."
    
    # Create group if it doesn't exist
    if ! getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
        groupadd "$SERVICE_GROUP"
        log_success "Created group: $SERVICE_GROUP"
    else
        log_warning "Group $SERVICE_GROUP already exists"
    fi
    
    # Create user if it doesn't exist
    if ! getent passwd "$SERVICE_USER" >/dev/null 2>&1; then
        useradd -r -g "$SERVICE_GROUP" -s /bin/bash -d "$INSTALL_DIR" "$SERVICE_USER"
        log_success "Created user: $SERVICE_USER"
    else
        log_warning "User $SERVICE_USER already exists"
    fi
}

# Function to set up installation directory
setup_install_directory() {
    log_step "Setting up installation directory..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy project files
    cp -r . "$INSTALL_DIR/"
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    
    # Set permissions
    chmod -R 755 "$INSTALL_DIR"
    chmod -R 644 "$INSTALL_DIR"/*.py 2>/dev/null || true
    chmod -R 644 "$INSTALL_DIR"/*.sql 2>/dev/null || true
    chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true
    chmod +x "$INSTALL_DIR"/scripts/*.sh 2>/dev/null || true
    
    log_success "Installation directory set up at $INSTALL_DIR"
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
    apt install -y postgresql postgresql-contrib
    
    # Install build dependencies for pgvector
    apt install -y build-essential git postgresql-server-dev-17
    
    # Clone and build pgvector
    cd /tmp
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    make install
    
    log_success "PostgreSQL and pgvector installed"
}

# Function to configure PostgreSQL
configure_postgresql() {
    log_step "Configuring PostgreSQL..."
    
    # Start PostgreSQL service
    systemctl start postgresql
    systemctl enable postgresql
    
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
    
    cd "$INSTALL_DIR"
    
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
    
    cd "$INSTALL_DIR"
    
    # Run the performance index script with proper environment
    DB_USER=postgres DB_HOST=localhost DB_PORT=5432 DB_NAME=doctrove ./scripts/apply_performance_indexes.sh
    
    log_success "Performance indexes applied"
}

# Function to set up Python environment
setup_python_environment() {
    log_step "Setting up Python environment..."
    
    cd "$INSTALL_DIR"
    
    # Install Python if not present
    if ! command_exists python3; then
        apt install -y python3 python3-pip python3-venv
    fi
    
    # Create virtual environment
    sudo -u "$SERVICE_USER" python3 -m venv arxivscope
    
    # Activate virtual environment and install requirements
    sudo -u "$SERVICE_USER" bash -c "
        source arxivscope/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r doc-ingestor/requirements.txt
        pip install -r embedding-enrichment/requirements.txt
        pip install -r doctrove-api/requirements.txt
    "
    
    log_success "Python environment set up"
}

# Function to set up startup script permissions
setup_startup_script() {
    log_step "Setting up startup script permissions..."
    
    # Ensure startup script is executable
    chmod +x "$INSTALL_DIR/startup.sh"
    chmod +x "$INSTALL_DIR/stop_services.sh"
    chmod +x "$INSTALL_DIR/check_services.sh"
    
    # Set proper ownership
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/startup.sh"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/stop_services.sh"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/check_services.sh"
    
    log_success "Startup script permissions configured"
}

# Function to set up team access
setup_team_access() {
    log_step "Setting up team access..."
    
    # Create arxivscope group if it doesn't exist
    if ! getent group arxivscope >/dev/null 2>&1; then
        groupadd arxivscope
    fi
    
    # Add current user to arxivscope group
    usermod -a -G arxivscope "$SUDO_USER"
    
    # Set up sudo access for arxivscope management
    cat > /etc/sudoers.d/arxivscope << EOF
# DocScope management commands
%arxivscope ALL=(ALL) NOPASSWD: /usr/local/bin/arxivscope-start
%arxivscope ALL=(ALL) NOPASSWD: /usr/local/bin/arxivscope-stop
%arxivscope ALL=(ALL) NOPASSWD: /usr/local/bin/arxivscope-status
%arxivscope ALL=(ALL) NOPASSWD: /bin/systemctl status arxivscope-*
%arxivscope ALL=(ALL) NOPASSWD: /bin/systemctl restart arxivscope-*
EOF

    log_success "Team access configured"
}

# Main execution
main() {
    echo "Starting DocScope team server setup..."
    echo "Install directory: $INSTALL_DIR"
    echo "Service user: $SERVICE_USER"
    echo "Database: $DB_NAME"
    echo ""
    
    check_root
    create_service_user
    setup_install_directory
    install_postgresql
    configure_postgresql
    apply_database_schema
    apply_performance_indexes
    setup_python_environment
    setup_startup_script
    setup_team_access
    
    echo ""
    echo -e "${GREEN}DocScope team setup completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Add team members to the arxivscope group: sudo usermod -a -G arxivscope <username>"
    echo "2. Start services: cd $INSTALL_DIR && ./startup.sh --with-enrichment --background"
    echo "3. Check status: cd $INSTALL_DIR && ./check_services.sh"
    echo "4. Stop services: cd $INSTALL_DIR && ./stop_services.sh"
    echo ""
    echo "Installation location: $INSTALL_DIR"
    echo "Logs: $INSTALL_DIR/startup.log"
}

# Run main function
main "$@" 