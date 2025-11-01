#!/bin/bash
# Database Setup Fix Script
# This script fixes common database setup issues, particularly missing enrichment components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Database connection parameters (can be overridden with environment variables)
DB_HOST=${DOC_TROVE_HOST:-localhost}
DB_PORT=${DOC_TROVE_PORT:-5434}  # PostgreSQL 14 on port 5434
DB_NAME=${DOC_TROVE_DB:-doctrove}
DB_USER=${DOC_TROVE_USER:-doctrove_admin}
DB_PASSWORD=${DOC_TROVE_PASSWORD:-doctrove_admin}

print_status "Fixing database setup for DocScope/DocTrove..."

# Check if database exists
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    print_error "Cannot connect to database $DB_NAME on $DB_HOST:$DB_PORT"
    print_error "Please ensure PostgreSQL is running and the database exists"
    exit 1
fi

print_success "Database connection verified"

# Check if main schema is applied
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d doctrove_papers" > /dev/null 2>&1; then
    print_warning "Main schema not found. Applying doctrove_schema.sql..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "doctrove_schema.sql"
    print_success "Main schema applied"
else
    print_success "Main schema already exists"
fi

# Check if database functions exist
FUNCTION_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_proc WHERE proname IN ('point_in_box', 'point_distance', 'papers_within_radius', 'get_paper_clusters');" | tr -d ' ')
if [ "$FUNCTION_COUNT" -lt 4 ]; then
    print_warning "Database functions missing. Applying setup_database_functions.sql..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "embedding-enrichment/setup_database_functions.sql"
    print_success "Database functions applied"
else
    print_success "Database functions already exist"
fi

# Check if enrichment queue table exists
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d enrichment_queue" > /dev/null 2>&1; then
    print_warning "Enrichment queue table missing. Creating it..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE TABLE IF NOT EXISTS enrichment_queue (
        id SERIAL PRIMARY KEY,
        paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
        enrichment_type TEXT NOT NULL,
        priority INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT NOW(),
        processed_at TIMESTAMP,
        status TEXT DEFAULT 'pending'
    );"
    print_success "Enrichment queue table created"
else
    print_success "Enrichment queue table already exists"
fi

# Check if enrichment functions exist
ENRICHMENT_FUNCTION_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_proc WHERE proname IN ('queue_2d_embedding_enrichment', 'queue_other_enrichments', 'get_papers_needing_embeddings_count', 'get_papers_needing_2d_embeddings_count');" | tr -d ' ')
if [ "$ENRICHMENT_FUNCTION_COUNT" -lt 4 ]; then
    print_warning "Enrichment functions missing. Applying event_triggers.sql..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "embedding-enrichment/event_triggers.sql"
    print_success "Enrichment functions applied"
else
    print_success "Enrichment functions already exist"
fi

# Check if pgvector extension is enabled
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" | grep -q 1; then
    print_warning "pgvector extension not enabled. Enabling it..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"
    print_success "pgvector extension enabled"
else
    print_success "pgvector extension already enabled"
fi

# Final verification
print_status "Performing final verification..."

# Check all critical components
COMPONENTS=(
    "doctrove_papers"
    "enrichment_queue"
    "vector"
    "point_in_box"
    "queue_2d_embedding_enrichment"
)

ALL_GOOD=true
for component in "${COMPONENTS[@]}"; do
    if [ "$component" = "vector" ]; then
        # Check pgvector extension
        if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" | grep -q 1; then
            print_error "pgvector extension not found"
            ALL_GOOD=false
        fi
    elif [ "$component" = "doctrove_papers" ] || [ "$component" = "enrichment_queue" ]; then
        # Check tables
        if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d $component" > /dev/null 2>&1; then
            print_error "Table $component not found"
            ALL_GOOD=false
        fi
    else
        # Check functions
        if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM pg_proc WHERE proname = '$component';" | grep -q 1; then
            print_error "Function $component not found"
            ALL_GOOD=false
        fi
    fi
done

if [ "$ALL_GOOD" = true ]; then
    print_success "All database components verified successfully!"
    print_success "The enrichment system should now work properly."
else
    print_error "Some components are still missing. Please check the errors above."
    exit 1
fi

print_status "Database setup fix completed successfully!" 