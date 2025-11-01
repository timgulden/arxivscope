#!/bin/bash

# OpenAlex Test Ingestion Script (Fixed Port Configuration)
# Tests ingestion with 2 specific files to validate the pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(pwd)"
S3_BASE_URL="https://openalex.s3.us-east-1.amazonaws.com/data/works"
TEMP_DIR="$(pwd)/data/openalex/temp"
MAX_FILES=2

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Database configuration - FIXED to use correct port and user
DB_HOST="${DOC_TROVE_HOST:-localhost}"
DB_PORT="${DOC_TROVE_PORT:-5434}"
DB_USER="${DOC_TROVE_USER:-doctrove_admin}"
DB_PASSWORD="${DOC_TROVE_PASSWORD:-doctrove_admin}"
DB_NAME="${DOC_TROVE_DB:-doctrove}"

# Test dates - using recent dates that should have data
TEST_DATES=("2025-01-01" "2025-01-02")

echo -e "${BLUE}=== OpenAlex Test Ingestion (Fixed Configuration) ===${NC}"
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME (user: $DB_USER)"
echo "Max files: $MAX_FILES"
echo "Test dates: ${TEST_DATES[*]}"
echo "S3 Base URL: $S3_BASE_URL"
echo ""

# Ensure temp directory exists
mkdir -p "$TEMP_DIR"

# Function to run database commands with correct configuration
run_db_command() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$1"
}

# Function to check database count before and after
check_database_count() {
    local label=$1
    local count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';" | tr -d ' ')
    echo -e "${BLUE}$label: $count OpenAlex papers${NC}"
}

# Function to process a single file
process_file() {
    local s3_url="$1"
    local filename="$2"
    local file_number="$3"
    
    echo -e "  ${BLUE}Processing file $file_number: $filename${NC}"
    
    # Step 1: Download and decompress
    echo "  Downloading from S3..."
    local local_file="$TEMP_DIR/$filename"
    local decompressed_file="$TEMP_DIR/${filename%.gz}"
    
    if curl -s -o "$local_file" "$s3_url"; then
        echo -e "    ${GREEN}✓ Downloaded $filename${NC}"
    else
        echo -e "    ${RED}✗ Failed to download $filename${NC}"
        return 1
    fi
    
    echo "  Decompressing file..."
    if gunzip -f "$local_file"; then
        echo -e "    ${GREEN}✓ Decompressed $filename${NC}"
    else
        echo -e "    ${RED}✗ Failed to decompress $filename${NC}"
        rm -f "$local_file"
        return 1
    fi
    
    # Step 2: Ingest using the new Python ingester
    echo "  Ingesting with Python ingester..."
    if cd "$PROJECT_DIR" && python openalex_ingester.py "$decompressed_file" --limit 1000; then
        echo -e "    ${GREEN}✓ Ingested $filename${NC}"
    else
        echo -e "    ${RED}✗ Failed to ingest $filename${NC}"
        # Don't delete the file if ingestion failed
        return 1
    fi
    
    # Step 3: Delete files
    echo "  Cleaning up..."
    rm -f "$local_file" "$decompressed_file"
    echo -e "    ${GREEN}✓ Deleted $filename and decompressed file${NC}"
    
    return 0
}

# Main test process
main() {
    echo "Starting test ingestion process..."
    echo "Configuration:"
    echo "  - Temp directory: $TEMP_DIR"
    echo "  - Project directory: $PROJECT_DIR"
    echo "  - Max files: $MAX_FILES"
    echo "  - Test dates: ${TEST_DATES[*]}"
    echo "  - Database: $DB_HOST:$DB_PORT/$DB_NAME"
    echo "  - S3 Base URL: $S3_BASE_URL"
    echo ""
    
    # Test database connection first
    echo "Testing database connection..."
    if run_db_command "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database connection successful${NC}"
    else
        echo -e "${RED}✗ Database connection failed${NC}"
        echo "Please check your database configuration in .env file"
        exit 1
    fi
    echo ""
    
    # Check initial database count
    check_database_count "Initial database count"
    echo ""
    
    local files_processed=0
    local files_failed=0
    
    # Process each test date
    for date in "${TEST_DATES[@]}"; do
        echo -e "${BLUE}Processing date: $date${NC}"
        
        # Check if this date has data (using updated_date= prefix)
        local s3_url="$S3_BASE_URL/updated_date=$date/part_000.gz"
        if curl -s --head "$s3_url" | head -n 1 | grep -q "200 OK"; then
            local filename="part_000.gz"
            local full_s3_url="$s3_url"
            
            if process_file "$full_s3_url" "$filename" $((files_processed + 1)); then
                files_processed=$((files_processed + 1))
                
                # Check database count after each file
                check_database_count "After file $files_processed"
                echo ""
            else
                files_failed=$((files_failed + 1))
            fi
            
            # Stop if we've processed enough files
            if [ $files_processed -ge $MAX_FILES ]; then
                break
            fi
        else
            echo -e "${YELLOW}  No data available for $date${NC}"
        fi
    done
    
    echo ""
    echo -e "${GREEN}✓ Test ingestion completed!${NC}"
    echo ""
    echo "Summary:"
    echo "  Files processed: $files_processed"
    echo "  Files failed: $files_failed"
    echo ""
    
    # Final database count
    check_database_count "Final database count"
    echo ""
    
    if [ $files_processed -gt 0 ]; then
        echo -e "${GREEN}✓ Test successful! OpenAlex papers have been ingested.${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Check DocScope: Verify papers appear in the viewer"
        echo "  2. Monitor enrichment: Check embedding generation progress"
        echo "  3. Scale up: Run full streaming ingestion if test is successful"
    else
        echo -e "${RED}✗ Test failed! No files were processed successfully.${NC}"
    fi
}

# Run main function
main "$@"
