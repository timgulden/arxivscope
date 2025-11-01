#!/bin/bash

# Database Backup Script for Schema Standardization Migration
# This script creates a complete backup of the database before making schema changes
#
# IMPORTANT: Run this BEFORE executing any migration scripts!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./database_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="doctrove_backup_${TIMESTAMP}"
FULL_BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Database connection details (from environment or config)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-doctrove}"
DB_USER="${DB_USER:-tgulden}"
DB_PASSWORD="${DB_PASSWORD:-}"

echo -e "${BLUE}=== Database Backup Script ===${NC}"
echo "This script will create a complete backup of your database."
echo ""

# Check if we're in the right directory
if [ ! -f "doctrove_schema.sql" ]; then
    echo -e "${RED}ERROR: This script must be run from the arxivscope-back-end directory${NC}"
    exit 1
fi

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    echo -e "${RED}ERROR: pg_dump not found. Please install PostgreSQL client tools.${NC}"
    exit 1
fi

# Function to test database connection
test_connection() {
    echo "Testing database connection..."
    
    if command -v psql &> /dev/null; then
        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Database connection successful${NC}"
            return 0
        else
            echo -e "${RED}✗ Database connection failed${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Warning: psql not available, skipping connection test${NC}"
        return 0
    fi
}

# Function to create backup
create_backup() {
    echo "Creating database backup..."
    echo "Backup path: $FULL_BACKUP_PATH"
    echo ""
    
    # Set password for pg_dump
    export PGPASSWORD="$DB_PASSWORD"
    
    # Create the backup
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose \
        --clean \
        --create \
        --if-exists \
        --no-owner \
        --no-privileges \
        --format=custom \
        --file="$FULL_BACKUP_PATH.sql" 2>&1; then
        
        echo -e "${GREEN}✓ Database backup created successfully!${NC}"
        echo "Backup file: $FULL_BACKUP_PATH.sql"
        
        # Get file size
        if command -v du &> /dev/null; then
            BACKUP_SIZE=$(du -h "$FULL_BACKUP_PATH.sql" | cut -f1)
            echo "Backup size: $BACKUP_SIZE"
        fi
        
        return 0
    else
        echo -e "${RED}✗ Database backup failed!${NC}"
        return 1
    fi
}

# Function to verify backup
verify_backup() {
    echo ""
    echo "Verifying backup integrity..."
    
    if [ ! -f "$FULL_BACKUP_PATH.sql" ]; then
        echo -e "${RED}✗ Backup file not found!${NC}"
        return 1
    fi
    
    # Check if file has content
    if [ ! -s "$FULL_BACKUP_PATH.sql" ]; then
        echo -e "${RED}✗ Backup file is empty!${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Backup file exists and has content${NC}"
    
    # Try to list backup contents (if pg_restore is available)
    if command -v pg_restore &> /dev/null; then
        echo "Listing backup contents..."
        if pg_restore --list "$FULL_BACKUP_PATH.sql" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backup file is valid and readable${NC}"
        else
            echo -e "${YELLOW}Warning: Could not read backup file contents${NC}"
        fi
    fi
    
    return 0
}

# Function to create backup info file
create_backup_info() {
    local info_file="${FULL_BACKUP_PATH}.info"
    
    cat > "$info_file" << EOF
Database Backup Information
==========================

Backup Date: $(date)
Backup File: ${BACKUP_NAME}.sql
Full Path: $(pwd)/${FULL_BACKUP_PATH}.sql

Database Details:
- Host: ${DB_HOST}
- Port: ${DB_PORT}
- Database: ${DB_NAME}
- User: ${DB_USER}

Migration Context:
- Migration ID: SCHEMA_STANDARDIZATION_001
- Purpose: Standardize field naming across metadata tables
- Status: Pre-migration backup

Backup Commands Used:
- pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} --format=custom

Restore Commands:
- pg_restore -h <host> -p <port> -U <user> -d <database> ${BACKUP_NAME}.sql

Notes:
- This backup was created before schema standardization migration
- All field names are in their original (pre-migration) state
- Use this backup to restore the database if migration fails

Created by: $(whoami)@$(hostname)
EOF

    echo "Backup info file created: ${BACKUP_NAME}.info"
}

# Main execution
main() {
    echo "Starting database backup process..."
    echo ""
    
    # Test connection
    if ! test_connection; then
        echo -e "${RED}ERROR: Cannot connect to database. Please check your connection details.${NC}"
        echo "Current settings:"
        echo "  Host: $DB_HOST"
        echo "  Port: $DB_PORT"
        echo "  Database: $DB_NAME"
        echo "  User: $DB_USER"
        exit 1
    fi
    
    # Create backup
    if ! create_backup; then
        echo -e "${RED}ERROR: Backup creation failed${NC}"
        exit 1
    fi
    
    # Verify backup
    if ! verify_backup; then
        echo -e "${RED}ERROR: Backup verification failed${NC}"
        exit 1
    fi
    
    # Create backup info file
    create_backup_info
    
    echo ""
    echo -e "${GREEN}=== Backup Complete! ===${NC}"
    echo ""
    echo "Your database has been backed up to:"
    echo "  $FULL_BACKUP_PATH.sql"
    echo ""
    echo "Next steps:"
    echo "1. Verify the backup file exists and has content"
    echo "2. Test the migration on a copy of your database"
    echo "3. Keep this backup safe until migration is complete"
    echo ""
    echo "To restore this backup if needed:"
    echo "  pg_restore -h <host> -p <port> -U <user> -d <database> $FULL_BACKUP_PATH.sql"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Do not delete this backup until migration is fully tested!${NC}"
}

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "Environment variables:"
    echo "  DB_HOST     Database host (default: localhost)"
    echo "  DB_PORT     Database port (default: 5432)"
    echo "  DB_NAME     Database name (default: doctrove)"
    echo "  DB_USER     Database user (default: tgulden)"
    echo "  DB_PASSWORD Database password (default: empty for local)"
    echo ""
    echo "Example:"
    echo "  export DB_PASSWORD='mypassword'"
    echo "  ./backup_database.sh"
    exit 0
fi

# Run main function
main "$@"
