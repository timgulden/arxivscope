#!/bin/bash

# Comprehensive OpenAlex Cleanup Script
# This script removes ALL OpenAlex-related database objects and prepares for a complete fresh start

set -e  # Exit on any error

echo "🧹 Comprehensive OpenAlex Cleanup"
echo "================================="
echo ""
echo "This script will:"
echo "1. Drop all OpenAlex tables (metadata, ingestion_log, field_mapping)"
echo "2. Remove any OpenAlex-related database functions/procedures"
echo "3. Clean up any OpenAlex enrichment registrations"
echo "4. Verify complete cleanup"
echo "5. Test that the framework can rebuild everything"
echo ""
echo "⚠️  WARNING: This will permanently remove ALL OpenAlex database objects!"
echo "   The framework will automatically rebuild them when needed."
echo ""

# Confirm before proceeding
read -p "Are you sure you want to continue? Type 'YES' to confirm: " confirmation
if [ "$confirmation" != "YES" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🔄 Starting comprehensive cleanup process..."

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

echo "📊 Step 1: Checking current OpenAlex database objects..."

# Check what OpenAlex objects exist
echo "   Checking tables..."
tables=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%openalex%';" | tr -d ' ')
if [ -n "$tables" ]; then
    echo "   Found tables: $tables"
else
    echo "   No OpenAlex tables found"
fi

echo "   Checking functions..."
functions=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT routine_name FROM information_schema.routines WHERE routine_name LIKE '%openalex%';" | tr -d ' ')
if [ -n "$functions" ]; then
    echo "   Found functions: $functions"
else
    echo "   No OpenAlex functions found"
fi

echo "   Checking triggers..."
triggers=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT trigger_name FROM information_schema.triggers WHERE event_object_table LIKE '%openalex%';" | tr -d ' ')
if [ -n "$triggers" ]; then
    echo "   Found triggers: $triggers"
else
    echo "   No OpenAlex triggers found"
fi

echo ""
echo "🗑️  Step 2: Dropping OpenAlex tables..."

# Drop tables in the correct order (respecting foreign keys)
if [ -n "$tables" ]; then
    for table in $tables; do
        echo "   Dropping table: $table"
        run_db_command "DROP TABLE IF EXISTS $table CASCADE;"
        check_success "Dropped table $table"
    done
else
    echo "   No tables to drop"
fi

echo ""
echo "🗑️  Step 3: Removing OpenAlex functions..."

# Remove any OpenAlex functions
if [ -n "$functions" ]; then
    for func in $functions; do
        echo "   Dropping function: $func"
        run_db_command "DROP FUNCTION IF EXISTS $func CASCADE;"
        check_success "Dropped function $func"
    done
else
    echo "   No functions to drop"
fi

echo ""
echo "🗑️  Step 4: Removing OpenAlex triggers..."

# Remove any OpenAlex triggers
if [ -n "$triggers" ]; then
    for trigger in $triggers; do
        echo "   Dropping trigger: $trigger"
        run_db_command "DROP TRIGGER IF EXISTS $trigger ON ALL TABLES CASCADE;"
        check_success "Dropped trigger $trigger"
    done
else
    echo "   No triggers to drop"
fi

echo ""
echo "🧹 Step 5: Cleaning up enrichment registry..."

# Remove any OpenAlex enrichments from the registry
echo "   Checking for OpenAlex enrichments..."
openalex_enrichments=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT enrichment_name FROM enrichment_registry WHERE enrichment_name LIKE '%openalex%' OR table_name LIKE '%openalex%';" | tr -d ' ')

if [ -n "$openalex_enrichments" ]; then
    echo "   Found OpenAlex enrichments: $openalex_enrichments"
    for enrichment in $openalex_enrichments; do
        echo "   Removing enrichment: $enrichment"
        run_db_command "DELETE FROM enrichment_registry WHERE enrichment_name = '$enrichment';"
        check_success "Removed enrichment $enrichment"
    done
else
    echo "   No OpenAlex enrichments found"
fi

echo ""
echo "🧹 Step 6: Cleaning up local files..."

# Clean up local OpenAlex files
if [ -d "data/openalex" ]; then
    echo "   Removing local OpenAlex data directory..."
    rm -rf data/openalex
    check_success "Removed local OpenAlex data directory"
else
    echo "   No local OpenAlex data directory found"
fi

echo ""
echo "📁 Step 7: Creating fresh directory structure..."

# Create fresh directory structure
mkdir -p data/openalex/{2025-01-01,2025-01-02,2025-01-03}
check_success "Created fresh OpenAlex directory structure"

echo ""
echo "📊 Step 8: Verifying complete cleanup..."

# Verify all OpenAlex objects are gone
remaining_tables=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%openalex%';" | tr -d ' ')
remaining_functions=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT routine_name FROM information_schema.routines WHERE routine_name LIKE '%openalex%';" | tr -d ' ')
remaining_triggers=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT trigger_name FROM information_schema.triggers WHERE event_object_table LIKE '%openalex%';" | tr -d ' ')

echo "   Remaining tables: ${remaining_tables:-None}"
echo "   Remaining functions: ${remaining_functions:-None}"
echo "   Remaining triggers: ${remaining_triggers:-None}"

if [ -z "$remaining_tables" ] && [ -z "$remaining_functions" ] && [ -z "$remaining_triggers" ]; then
    echo ""
    echo "🎉 Comprehensive cleanup completed successfully!"
    echo ""
    echo "📁 Fresh directory structure created:"
    ls -la data/openalex/
    echo ""
    echo "🚀 Ready for complete fresh OpenAlex ingestion!"
    echo ""
    echo "Next steps:"
    echo "1. Test the framework's ability to rebuild tables:"
    echo "   python3 openalex_ingester.py /opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz --limit 10"
    echo "2. Verify tables are recreated automatically"
    echo "3. Start full ingestion pipeline"
else
    echo ""
    echo "⚠️  Cleanup may not be complete. Some OpenAlex objects remain."
    echo "   Remaining objects:"
    [ -n "$remaining_tables" ] && echo "   Tables: $remaining_tables"
    [ -n "$remaining_functions" ] && echo "   Functions: $remaining_functions"
    [ -n "$remaining_triggers" ] && echo "   Triggers: $remaining_triggers"
    exit 1
fi
