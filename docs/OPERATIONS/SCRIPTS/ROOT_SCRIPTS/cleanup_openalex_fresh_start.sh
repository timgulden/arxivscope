#!/bin/bash

# OpenAlex Fresh Start Cleanup Script
# This script removes all OpenAlex data and prepares for a fresh ingestion

set -e  # Exit on any error

echo "🚀 OpenAlex Fresh Start Cleanup"
echo "================================="
echo ""
echo "This script will:"
echo "1. Remove all OpenAlex papers from doctrove_papers"
echo "2. Clear OpenAlex metadata table"
echo "3. Reset ingestion log"
echo "4. Clean up local OpenAlex files"
echo "5. Verify cleanup completion"
echo ""
echo "⚠️  WARNING: This will permanently delete 51,553 OpenAlex papers"
echo "   and all their embeddings and 2D projections!"
echo ""

# Confirm before proceeding
read -p "Are you sure you want to continue? Type 'YES' to confirm: " confirmation
if [ "$confirmation" != "YES" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🔄 Starting cleanup process..."

# Database connection details
DB_HOST="localhost"
DB_PORT="5434"
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_PASSWORD="doctrove_admin"

# Function to run database commands
run_db_command() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$1"
}

# Function to check if command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

echo "📊 Checking current OpenAlex data..."
current_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';" | xargs)
echo "   Current OpenAlex papers: $current_count"

if [ "$current_count" -eq 0 ]; then
    echo "ℹ️  No OpenAlex papers found. Nothing to clean up."
    exit 0
fi

echo ""
echo "🗑️  Step 1: Removing OpenAlex papers from main table..."
run_db_command "DELETE FROM doctrove_papers WHERE doctrove_source = 'openalex';"
check_success "Removed OpenAlex papers from main table"

echo ""
echo "🗑️  Step 2: Clearing OpenAlex metadata table..."
run_db_command "TRUNCATE TABLE openalex_metadata;"
check_success "Cleared OpenAlex metadata table"

echo ""
echo "🗑️  Step 3: Resetting ingestion log..."
run_db_command "TRUNCATE TABLE openalex_ingestion_log;"
check_success "Reset OpenAlex ingestion log"

echo ""
echo "🗑️  Step 4: Cleaning up local OpenAlex files..."
if [ -d "data/openalex" ]; then
    echo "   Removing data/openalex directory..."
    rm -rf data/openalex
    check_success "Removed local OpenAlex data directory"
else
    echo "   No local OpenAlex data directory found"
fi

echo ""
echo "🧹 Step 5: Creating fresh directory structure..."
mkdir -p data/openalex/{2025-01-01,2025-01-02,2025-01-03}
check_success "Created fresh OpenAlex directory structure"

echo ""
echo "📊 Step 6: Verifying cleanup completion..."
final_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';" | xargs)
metadata_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM openalex_metadata;" | xargs)
log_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM openalex_ingestion_log;" | xargs)

echo "   OpenAlex papers remaining: $final_count"
echo "   OpenAlex metadata records: $metadata_count"
echo "   Ingestion log records: $log_count"

if [ "$final_count" -eq 0 ] && [ "$metadata_count" -eq 0 ] && [ "$log_count" -eq 0 ]; then
    echo ""
    echo "🎉 Cleanup completed successfully!"
    echo ""
    echo "📁 Fresh directory structure created:"
    ls -la data/openalex/
    echo ""
    echo "🚀 Ready for fresh OpenAlex ingestion!"
    echo ""
    echo "Next steps:"
    echo "1. Test S3 access: curl -I 'https://openalex.s3.us-east-1.amazonaws.com/data/works/'"
    echo "2. Download test files to data/openalex/2025-01-01/"
    echo "3. Run test ingestion: python openalex_ingester.py data/openalex/2025-01-01/part_000.gz --limit 1000"
    echo "4. Start full ingestion pipeline"
else
    echo ""
    echo "⚠️  Cleanup may not be complete. Please check manually."
    exit 1
fi
