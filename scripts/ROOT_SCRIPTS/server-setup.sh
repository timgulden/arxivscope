#!/bin/bash
# Open-Source Server Setup Script for DocTrove
# This script automates the setup of a dedicated server for DocTrove deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
DOCTROVE_USER="doctrove"
DOCTROVE_HOME="/opt/doctrove"
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_PASSWORD=""

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Function to check system requirements
check_system_requirements() {
    print_status "Checking system requirements..."
    
    # Check OS
    if ! grep -q "Ubuntu 22.04" /etc/os-release; then
        print_warning "This script is designed for Ubuntu 22.04 LTS"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check available memory
    local mem_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$mem_gb" -lt 16 ]; then
        print_warning "Recommended: 32GB RAM, found: ${mem_gb}GB"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check available disk space
    local disk_gb=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$disk_gb" -lt 100 ]; then
        print_warning "Recommended: 1TB free space, found: ${disk_gb}GB"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "System requirements check completed"
}

# Function to update system
update_system() {
    print_status "Updating system packages..."
    
    apt update
    apt upgrade -y
    
    # Install essential packages
    apt install -y curl wget git htop vim nano unzip software-properties-common \
                   apt-transport-https ca-certificates gnupg lsb-release
    
    print_success "System updated successfully"
}

# Function to create doctrove user
create_doctrove_user() {
    print_status "Creating doctrove user..."
    
    if ! id "$DOCTROVE_USER" &>/dev/null; then
        useradd -m -s /bin/bash -d "$DOCTROVE_HOME" "$DOCTROVE_USER"
        usermod -aG sudo "$DOCTROVE_USER"
        print_success "User $DOCTROVE_USER created"
    else
        print_status "User $DOCTROVE_USER already exists"
    fi
    
    # Create directories
    mkdir -p "$DOCTROVE_HOME"/{logs,backups,models,config}
    chown -R "$DOCTROVE_USER:$DOCTROVE_USER" "$DOCTROVE_HOME"
}

# Function to install PostgreSQL
install_postgresql() {
    print_status "Installing PostgreSQL 15..."
    
    # Add PostgreSQL repository
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
    apt update
    
    # Install PostgreSQL
    apt install -y postgresql-15 postgresql-contrib-15 postgresql-server-dev-15
    
    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    print_success "PostgreSQL 15 installed and started"
}

# Function to install pgvector
install_pgvector() {
    print_status "Installing pgvector extension..."
    
    # Install build dependencies
    apt install -y build-essential git
    
    # Clone and compile pgvector
    cd /tmp
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    make install
    
    print_success "pgvector extension installed"
}

# Function to configure PostgreSQL
configure_postgresql() {
    print_status "Configuring PostgreSQL..."
    
    # Generate secure password if not provided
    if [ -z "$DB_PASSWORD" ]; then
        DB_PASSWORD=$(openssl rand -base64 32)
    fi
    
    # Create database and user
    sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    
    # Configure PostgreSQL for better performance
    cat >> /etc/postgresql/15/main/postgresql.conf << EOF

# Doctrove optimizations
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
log_statement = 'none'
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = off
log_disconnections = off
EOF
    
    # Configure PostgreSQL to accept connections from Docker
    echo "host    $DB_NAME    $DB_USER    172.16.0.0/12    md5" >> /etc/postgresql/15/main/pg_hba.conf
    echo "host    $DB_NAME    $DB_USER    192.168.0.0/16    md5" >> /etc/postgresql/15/main/pg_hba.conf
    
    # Restart PostgreSQL
    systemctl restart postgresql
    
    print_success "PostgreSQL configured successfully"
}

# Function to install Docker
install_docker() {
    print_status "Installing Docker..."
    
    # Add Docker repository
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add doctrove user to docker group
    usermod -aG docker "$DOCTROVE_USER"
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    print_success "Docker installed successfully"
}

# Function to install monitoring tools
install_monitoring() {
    print_status "Installing monitoring tools..."
    
    # Install Node Exporter for system metrics
    docker run -d \
        --name node-exporter \
        --restart unless-stopped \
        -p 9100:9100 \
        -v "/:/host:ro,rslave" \
        prom/node-exporter:latest \
        --path.rootfs=/host
    
    # Install PostgreSQL Exporter
    docker run -d \
        --name postgres-exporter \
        --restart unless-stopped \
        -p 9187:9187 \
        -e DATA_SOURCE_NAME="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME?sslmode=disable" \
        prometheuscommunity/postgres-exporter:latest
    
    print_success "Monitoring tools installed"
}

# Function to configure firewall
configure_firewall() {
    print_status "Configuring firewall..."
    
    # Install UFW if not present
    apt install -y ufw
    
    # Configure firewall rules
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 5001/tcp
    ufw allow 8050/tcp
    ufw allow 3000/tcp
    ufw allow 9090/tcp
    ufw allow 9100/tcp
    ufw allow 9187/tcp
    
    # Enable firewall
    ufw --force enable
    
    print_success "Firewall configured successfully"
}

# Function to create backup script
create_backup_script() {
    print_status "Creating backup script..."
    
    cat > "$DOCTROVE_HOME/backup.sh" << 'EOF'
#!/bin/bash
# Automated PostgreSQL Backup Script

set -e

# Configuration
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_PASSWORD=""
BACKUP_DIR="/opt/doctrove/backups"
RETENTION_DAYS=30

# Load password from environment or config
if [ -f /opt/doctrove/config/db_password ]; then
    DB_PASSWORD=$(cat /opt/doctrove/config/db_password)
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup filename
BACKUP_FILE="doctrove_backup_$(date +%Y%m%d_%H%M%S).sql"

# Create backup
echo "Creating database backup: $BACKUP_FILE"
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
EOF
    
    chmod +x "$DOCTROVE_HOME/backup.sh"
    chown "$DOCTROVE_USER:$DOCTROVE_USER" "$DOCTROVE_HOME/backup.sh"
    
    # Store database password securely
    echo "$DB_PASSWORD" > "$DOCTROVE_HOME/config/db_password"
    chmod 600 "$DOCTROVE_HOME/config/db_password"
    chown "$DOCTROVE_USER:$DOCTROVE_USER" "$DOCTROVE_HOME/config/db_password"
    
    print_success "Backup script created"
}

# Function to create systemd services
create_systemd_services() {
    print_status "Creating systemd services..."
    
    # Backup service
    cat > /etc/systemd/system/doctrove-backup.service << EOF
[Unit]
Description=Doctrove Database Backup
After=network.target postgresql.service

[Service]
Type=oneshot
User=$DOCTROVE_USER
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$DOCTROVE_HOME/backup.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Backup timer
    cat > /etc/systemd/system/doctrove-backup.timer << EOF
[Unit]
Description=Run Doctrove backup daily
Requires=doctrove-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF
    
    # Enable services
    systemctl daemon-reload
    systemctl enable doctrove-backup.timer
    systemctl start doctrove-backup.timer
    
    print_success "Systemd services created"
}

# Function to create deployment script
create_deployment_script() {
    print_status "Creating deployment script..."
    
    cat > "$DOCTROVE_HOME/deploy.sh" << 'EOF'
#!/bin/bash
# DocTrove Deployment Script

set -e

cd /opt/doctrove

# Pull latest code
if [ -d "arxivscope-back-end" ]; then
    cd arxivscope-back-end
    git pull origin main
else
    git clone https://code.rand.org/arxivscope-projects/arxivscope-back-end.git
    cd arxivscope-back-end
fi

# Build and deploy containers
docker-compose build
docker-compose up -d

echo "Deployment completed successfully!"
echo "Services available at:"
echo "  - API: http://localhost:5001"
echo "  - Frontend: http://localhost:8050"
echo "  - Grafana: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
EOF
    
    chmod +x "$DOCTROVE_HOME/deploy.sh"
    chown "$DOCTROVE_USER:$DOCTROVE_USER" "$DOCTROVE_HOME/deploy.sh"
    
    print_success "Deployment script created"
}

# Function to create status script
create_status_script() {
    print_status "Creating status script..."
    
    cat > "$DOCTROVE_HOME/status.sh" << 'EOF'
#!/bin/bash
# DocTrove Status Script

echo "=== DocTrove Server Status ==="
echo

echo "System Information:"
echo "  Hostname: $(hostname)"
echo "  Uptime: $(uptime -p)"
echo "  Load Average: $(uptime | awk -F'load average:' '{print $2}')"
echo

echo "Disk Usage:"
df -h / | awk 'NR==2{print "  Root: " $3 " used of " $2 " (" $5 ")"}'
df -h /opt/doctrove | awk 'NR==2{print "  DocTrove: " $3 " used of " $2 " (" $5 ")"}'
echo

echo "Memory Usage:"
free -h | awk '/^Mem:/{print "  " $3 " used of " $2 " (" $3/$2*100 "%)"}'
echo

echo "PostgreSQL Status:"
systemctl is-active postgresql
echo

echo "Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

echo "Recent Backups:"
ls -la /opt/doctrove/backups/doctrove_backup_*.sql.gz 2>/dev/null | tail -5 || echo "  No backups found"
echo

echo "Service URLs:"
echo "  - API: http://localhost:5001"
echo "  - Frontend: http://localhost:8050"
echo "  - Grafana: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
EOF
    
    chmod +x "$DOCTROVE_HOME/status.sh"
    chown "$DOCTROVE_USER:$DOCTROVE_USER" "$DOCTROVE_HOME/status.sh"
    
    print_success "Status script created"
}

# Function to display final information
display_final_info() {
    print_success "Server setup completed successfully!"
    echo
    echo "=== Setup Summary ==="
    echo "User: $DOCTROVE_USER"
    echo "Home Directory: $DOCTROVE_HOME"
    echo "Database: $DB_NAME"
    echo "Database User: $DB_USER"
    echo "Database Password: $DB_PASSWORD"
    echo
    echo "=== Next Steps ==="
    echo "1. Clone your repository:"
    echo "   sudo -u $DOCTROVE_USER git clone https://code.rand.org/arxivscope-projects/arxivscope-back-end.git $DOCTROVE_HOME/arxivscope-back-end"
    echo
    echo "2. Configure environment variables:"
    echo "   sudo -u $DOCTROVE_USER nano $DOCTROVE_HOME/arxivscope-back-end/.env"
    echo
    echo "3. Deploy the application:"
    echo "   sudo -u $DOCTROVE_USER $DOCTROVE_HOME/deploy.sh"
    echo
    echo "4. Check status:"
    echo "   sudo -u $DOCTROVE_USER $DOCTROVE_HOME/status.sh"
    echo
    echo "=== Important Notes ==="
    echo "- Database password is stored in: $DOCTROVE_HOME/config/db_password"
    echo "- Backups run daily at 2:00 AM"
    echo "- Firewall is configured to allow necessary ports"
    echo "- Monitoring is available at http://localhost:3000 (Grafana)"
    echo
    echo "=== Security Recommendations ==="
    echo "- Change default passwords"
    echo "- Configure SSL certificates"
    echo "- Set up regular security updates"
    echo "- Monitor system logs"
}

# Main execution
main() {
    print_status "Starting DocTrove server setup..."
    
    # Check if running as root
    check_root
    
    # Get database password
    read -s -p "Enter database password (or press Enter to generate): " DB_PASSWORD
    echo
    
    # Run setup steps
    check_system_requirements
    update_system
    create_doctrove_user
    install_postgresql
    install_pgvector
    configure_postgresql
    install_docker
    install_monitoring
    configure_firewall
    create_backup_script
    create_systemd_services
    create_deployment_script
    create_status_script
    
    # Display final information
    display_final_info
}

# Run main function
main "$@" 