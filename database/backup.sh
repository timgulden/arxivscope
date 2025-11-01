#!/bin/bash
# Automated PostgreSQL Backup Script for DocTrove
# This script creates compressed backups and uploads them to Azure Blob Storage

set -e

# Configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5434}"
DB_NAME="${DB_NAME:-doctrove}"
DB_USER="${DB_USER:-doctrove_admin}"
DB_PASSWORD="${DB_PASSWORD}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
COMPRESSION="${COMPRESSION:-gzip}"

# Azure Storage Configuration
STORAGE_ACCOUNT="${STORAGE_ACCOUNT}"
STORAGE_KEY="${STORAGE_KEY}"
CONTAINER_NAME="${CONTAINER_NAME:-backups}"

# Logging
LOG_FILE="${BACKUP_DIR}/backup.log"
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

# Function to create backup
create_backup() {
    local backup_file="$1"
    local temp_file="${backup_file}.tmp"
    
    log_message "Creating database backup: $backup_file"
    
    # Create backup with progress
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --clean \
        --no-owner \
        --no-privileges \
        --format=custom \
        --compress=9 \
        --file="$temp_file" \
        2>&1 | tee -a "$LOG_FILE"
    
    # Move temp file to final location
    mv "$temp_file" "$backup_file"
    
    # Get backup size
    local backup_size=$(du -h "$backup_file" | cut -f1)
    log_message "Backup completed: $backup_file (Size: $backup_size)"
}

# Function to compress backup
compress_backup() {
    local backup_file="$1"
    local compressed_file="${backup_file}.gz"
    
    if [ "$COMPRESSION" = "gzip" ]; then
        log_message "Compressing backup with gzip..."
        gzip -9 "$backup_file"
        local compressed_size=$(du -h "$compressed_file" | cut -f1)
        log_message "Compression completed: $compressed_file (Size: $compressed_size)"
    fi
}

# Function to upload to Azure Blob Storage
upload_to_azure() {
    local backup_file="$1"
    local blob_name=$(basename "$backup_file")
    
    if [ -n "$STORAGE_ACCOUNT" ] && [ -n "$STORAGE_KEY" ]; then
        log_message "Uploading backup to Azure Blob Storage..."
        
        if az storage blob upload \
            --account-name "$STORAGE_ACCOUNT" \
            --container-name "$CONTAINER_NAME" \
            --name "$blob_name" \
            --file "$backup_file" \
            --auth-mode key \
            --account-key "$STORAGE_KEY" \
            --overwrite \
            --timeout 3600 \
            > /dev/null 2>&1; then
            
            log_message "Upload completed successfully: $blob_name"
        else
            log_message "WARNING: Upload to Azure failed, keeping local backup"
        fi
    else
        log_message "Azure storage configuration not provided, skipping upload"
    fi
}

# Function to clean up old backups
cleanup_old_backups() {
    log_message "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Clean up local backups
    find "$BACKUP_DIR" -name "doctrove_backup_*.sql*" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # Clean up Azure backups if configured
    if [ -n "$STORAGE_ACCOUNT" ] && [ -n "$STORAGE_KEY" ]; then
        log_message "Cleaning up old Azure backups..."
        
        # Get list of old backups from Azure
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +"%Y-%m-%d")
        
        az storage blob list \
            --account-name "$STORAGE_ACCOUNT" \
            --container-name "$CONTAINER_NAME" \
            --auth-mode key \
            --account-key "$STORAGE_KEY" \
            --query "[?contains(name, 'doctrove_backup_') && lastModified < '$cutoff_date'].name" \
            --output tsv | while read -r blob_name; do
            if [ -n "$blob_name" ]; then
                log_message "Deleting old Azure backup: $blob_name"
                az storage blob delete \
                    --account-name "$STORAGE_ACCOUNT" \
                    --container-name "$CONTAINER_NAME" \
                    --name "$blob_name" \
                    --auth-mode key \
                    --account-key "$STORAGE_KEY" \
                    > /dev/null 2>&1 || true
            fi
        done
    fi
}

# Function to verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    log_message "Verifying backup integrity..."
    
    if [ "$COMPRESSION" = "gzip" ]; then
        local uncompressed_file="${backup_file%.gz}"
        gunzip -t "$backup_file" 2>/dev/null
        if [ $? -eq 0 ]; then
            log_message "Backup integrity verified"
        else
            log_message "ERROR: Backup integrity check failed"
            return 1
        fi
    else
        # For uncompressed backups, try to read the header
        if file "$backup_file" | grep -q "PostgreSQL custom database dump"; then
            log_message "Backup integrity verified"
        else
            log_message "ERROR: Backup integrity check failed"
            return 1
        fi
    fi
}

# Function to get database statistics
get_db_stats() {
    log_message "Getting database statistics..."
    
    local stats_query="
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats 
        WHERE schemaname = 'public' 
        ORDER BY tablename, attname;
    "
    
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -c "$stats_query" \
        > "$BACKUP_DIR/db_stats_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || true
}

# Main execution
main() {
    log_message "Starting automated backup process"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Check prerequisites
    check_db_connectivity || exit 1
    
    # Create backup filename with timestamp
    local backup_file="doctrove_backup_$(date +%Y%m%d_%H%M%S).sql"
    local backup_path="$BACKUP_DIR/$backup_file"
    
    # Create backup
    create_backup "$backup_path" || exit 1
    
    # Compress backup
    compress_backup "$backup_path" || exit 1
    
    # Verify backup integrity
    local final_backup_file="$backup_path"
    if [ "$COMPRESSION" = "gzip" ]; then
        final_backup_file="${backup_path}.gz"
    fi
    verify_backup "$final_backup_file" || exit 1
    
    # Upload to Azure
    upload_to_azure "$final_backup_file"
    
    # Clean up old backups
    cleanup_old_backups
    
    # Get database statistics
    get_db_stats
    
    log_message "Backup process completed successfully"
    
    # Return the backup file path for external use
    echo "$final_backup_file"
}

# Handle script arguments
case "${1:-backup}" in
    "backup")
        main
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "verify")
        if [ -n "$2" ]; then
            verify_backup "$2"
        else
            echo "Usage: $0 verify <backup_file>"
            exit 1
        fi
        ;;
    "stats")
        get_db_stats
        ;;
    *)
        echo "Usage: $0 [backup|cleanup|verify <file>|stats]"
        exit 1
        ;;
esac 