#!/bin/bash
# PostgreSQL Recovery Script for DocTrove
# This script restores database from backup files

set -e

# Configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5434}"
DB_NAME="${DB_NAME:-doctrove}"
DB_USER="${DB_USER:-doctrove_admin}"
DB_PASSWORD="${DB_PASSWORD}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"

# Azure Storage Configuration
STORAGE_ACCOUNT="${STORAGE_ACCOUNT}"
STORAGE_KEY="${STORAGE_KEY}"
CONTAINER_NAME="${CONTAINER_NAME:-backups}"

# Logging
LOG_FILE="${BACKUP_DIR}/recovery.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Function to log messages
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Function to check if Azure CLI is available
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        log_message "ERROR: Azure CLI is not installed or not in PATH"
        return 1
    fi
}

# Function to check database connectivity
check_db_connectivity() {
    log_message "Checking database connectivity..."
    if ! PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
        log_message "ERROR: Cannot connect to database"
        return 1
    fi
    log_message "Database connectivity confirmed"
}

# Function to list available backups
list_backups() {
    log_message "Available local backups:"
    if [ -d "$BACKUP_DIR" ]; then
        find "$BACKUP_DIR" -name "doctrove_backup_*.sql*" -type f | sort -r | head -10
    else
        log_message "No local backup directory found"
    fi
    
    if [ -n "$STORAGE_ACCOUNT" ] && [ -n "$STORAGE_KEY" ]; then
        log_message "Available Azure backups:"
        az storage blob list \
            --account-name "$STORAGE_ACCOUNT" \
            --container-name "$CONTAINER_NAME" \
            --auth-mode key \
            --account-key "$STORAGE_KEY" \
            --query "[?contains(name, 'doctrove_backup_')].{name:name, lastModified:lastModified}" \
            --output table 2>/dev/null || log_message "Unable to list Azure backups"
    fi
}

# Function to download backup from Azure
download_from_azure() {
    local backup_file="$1"
    local local_path="$BACKUP_DIR/$(basename "$backup_file")"
    
    log_message "Downloading backup from Azure: $backup_file"
    
    if az storage blob download \
        --account-name "$STORAGE_ACCOUNT" \
        --container-name "$CONTAINER_NAME" \
        --name "$backup_file" \
        --file "$local_path" \
        --auth-mode key \
        --account-key "$STORAGE_KEY" \
        --timeout 3600 > /dev/null 2>&1; then
        
        log_message "Download completed: $local_path"
        echo "$local_path"
    else
        log_message "ERROR: Failed to download backup from Azure"
        return 1
    fi
}

# Function to verify backup file
verify_backup_file() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log_message "ERROR: Backup file not found: $backup_file"
        return 1
    fi
    
    log_message "Verifying backup file: $backup_file"
    
    # Check if it's a compressed file
    if [[ "$backup_file" == *.gz ]]; then
        if gunzip -t "$backup_file" 2>/dev/null; then
            log_message "Compressed backup file verified"
        else
            log_message "ERROR: Invalid compressed backup file"
            return 1
        fi
    else
        # Check if it's a PostgreSQL dump
        if file "$backup_file" | grep -q "PostgreSQL custom database dump"; then
            log_message "PostgreSQL backup file verified"
        else
            log_message "ERROR: Invalid PostgreSQL backup file"
            return 1
        fi
    fi
}

# Function to create recovery database
create_recovery_db() {
    local recovery_db="${DB_NAME}_recovery_$(date +%Y%m%d_%H%M%S)"
    
    log_message "Creating recovery database: $recovery_db"
    
    PGPASSWORD="$DB_PASSWORD" createdb \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        "$recovery_db" 2>/dev/null || {
        log_message "WARNING: Could not create recovery database, using existing one"
        recovery_db="$DB_NAME"
    }
    
    echo "$recovery_db"
}

# Function to restore database
restore_database() {
    local backup_file="$1"
    local target_db="$2"
    
    log_message "Restoring database from backup: $backup_file"
    log_message "Target database: $target_db"
    
    # Determine if we need to decompress
    local restore_file="$backup_file"
    if [[ "$backup_file" == *.gz ]]; then
        restore_file="${backup_file%.gz}"
        log_message "Decompressing backup file..."
        gunzip -c "$backup_file" > "$restore_file"
    fi
    
    # Restore the database
    log_message "Starting database restoration..."
    
    PGPASSWORD="$DB_PASSWORD" pg_restore \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$target_db" \
        --verbose \
        --clean \
        --no-owner \
        --no-privileges \
        --single-transaction \
        "$restore_file" 2>&1 | tee -a "$LOG_FILE"
    
    # Clean up temporary file if we decompressed
    if [[ "$backup_file" == *.gz ]]; then
        rm -f "$restore_file"
    fi
    
    log_message "Database restoration completed"
}

# Function to verify restoration
verify_restoration() {
    local target_db="$1"
    
    log_message "Verifying database restoration..."
    
    # Check if tables exist
    local table_count=$(PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$target_db" \
        -t \
        -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    
    if [ -n "$table_count" ] && [ "$table_count" -gt 0 ]; then
        log_message "Restoration verified: $table_count tables found"
        
        # Check for key tables
        local key_tables=("doctrove_papers" "aipickle_metadata")
        for table in "${key_tables[@]}"; do
            local exists=$(PGPASSWORD="$DB_PASSWORD" psql \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                -d "$target_db" \
                -t \
                -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$table');" 2>/dev/null | tr -d ' ')
            
            if [ "$exists" = "t" ]; then
                log_message "✓ Table '$table' exists"
            else
                log_message "⚠ Table '$table' not found"
            fi
        done
    else
        log_message "ERROR: Restoration verification failed - no tables found"
        return 1
    fi
}

# Function to switch databases (if using recovery database)
switch_databases() {
    local recovery_db="$1"
    local original_db="$2"
    
    if [ "$recovery_db" != "$original_db" ]; then
        log_message "Switching from recovery database to production database..."
        
        # Drop the original database
        PGPASSWORD="$DB_PASSWORD" dropdb \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            "$original_db" 2>/dev/null || log_message "WARNING: Could not drop original database"
        
        # Rename recovery database to original name
        PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d postgres \
            -c "ALTER DATABASE \"$recovery_db\" RENAME TO \"$original_db\";" 2>/dev/null || {
            log_message "ERROR: Could not rename recovery database"
            return 1
        }
        
        log_message "Database switch completed successfully"
    fi
}

# Function to show recovery options
show_recovery_options() {
    echo "Recovery Options:"
    echo "1. List available backups: $0 list"
    echo "2. Restore to new database: $0 restore <backup_file> [--new-db]"
    echo "3. Restore to existing database: $0 restore <backup_file> [--overwrite]"
    echo "4. Download from Azure: $0 download <azure_backup_name>"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 restore /backups/doctrove_backup_20240710_143022.sql.gz"
    echo "  $0 restore /backups/doctrove_backup_20240710_143022.sql.gz --new-db"
    echo "  $0 download doctrove_backup_20240710_143022.sql.gz"
}

# Main execution
main() {
    local backup_file="$1"
    local use_new_db="${2:-false}"
    
    log_message "Starting database recovery process"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Check prerequisites
    check_db_connectivity || exit 1
    
    # Verify backup file
    verify_backup_file "$backup_file" || exit 1
    
    # Create recovery database if requested
    local target_db="$DB_NAME"
    if [ "$use_new_db" = "true" ]; then
        target_db=$(create_recovery_db)
    fi
    
    # Restore database
    restore_database "$backup_file" "$target_db" || exit 1
    
    # Verify restoration
    verify_restoration "$target_db" || exit 1
    
    # Switch databases if using recovery database
    if [ "$use_new_db" = "true" ]; then
        switch_databases "$target_db" "$DB_NAME" || exit 1
    fi
    
    log_message "Database recovery completed successfully"
}

# Handle script arguments
case "${1:-help}" in
    "restore")
        if [ -n "$2" ]; then
            local use_new_db="false"
            if [ "$3" = "--new-db" ]; then
                use_new_db="true"
            fi
            main "$2" "$use_new_db"
        else
            echo "Usage: $0 restore <backup_file> [--new-db]"
            exit 1
        fi
        ;;
    "list")
        list_backups
        ;;
    "download")
        if [ -n "$2" ]; then
            download_from_azure "$2"
        else
            echo "Usage: $0 download <azure_backup_name>"
            exit 1
        fi
        ;;
    "verify")
        if [ -n "$2" ]; then
            verify_backup_file "$2"
        else
            echo "Usage: $0 verify <backup_file>"
            exit 1
        fi
        ;;
    "help"|*)
        show_recovery_options
        ;;
esac 