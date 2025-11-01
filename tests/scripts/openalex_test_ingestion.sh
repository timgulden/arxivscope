#!/bin/bash

# OpenAlex Test Ingestion Script
# Downloads and ingests just 2 files for testing the process
# This is a limited version to verify the pipeline works

set -e  # Exit on any error

# Configuration
TEMP_DIR="$HOME/Documents/doctrove-data/openalex/temp"
PROJECT_DIR="/Users/tgulden/Documents/ArXivScope/arxivscope-back-end"
S3_BASE_URL="https://openalex.s3.us-east-1.amazonaws.com/data/works"

# Test configuration - just 2 files
MAX_FILES=2
TEST_DATES=("2025-01-01" "2025-01-02")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}OpenAlex Test Ingestion Script${NC}"
echo "=================================="
echo "This will ingest exactly $MAX_FILES files for testing"
echo ""

# Create temp directory
mkdir -p "$TEMP_DIR"
echo -e "${GREEN}✓ Temp directory: $TEMP_DIR${NC}"

# Function to download and ingest one file
process_file() {
    local s3_url=$1
    local filename=$2
    local local_file="$TEMP_DIR/$filename"
    local file_num=$3
    
    echo -e "${YELLOW}Processing file $file_num of $MAX_FILES: $filename${NC}"
    echo "=================================================="
    
    # Step 1: Download file
    echo "  Downloading..."
    if curl -s -o "$local_file" "$s3_url"; then
        echo -e "    ${GREEN}✓ Downloaded $filename${NC}"
        
        # Show file size
        local file_size=$(ls -lh "$local_file" | awk '{print $5}')
        echo "    File size: $file_size"
    else
        echo -e "    ${RED}✗ Failed to download $filename${NC}"
        return 1
    fi
    
    # Step 1.5: Decompress file
    echo "  Decompressing..."
    local decompressed_file="${local_file%.gz}"
    if gunzip -c "$local_file" > "$decompressed_file"; then
        echo -e "    ${GREEN}✓ Decompressed $filename${NC}"
    else
        echo -e "    ${RED}✗ Failed to decompress $filename${NC}"
        return 1
    fi
    
    # Step 2: Ingest file using OpenAlex ingester
    echo "  Ingesting..."
    cd "$PROJECT_DIR"
    source arxivscope/bin/activate
    
    if python -c "
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'openalex'))
sys.path.append(os.path.join(os.getcwd(), 'doc-ingestor'))

from db import insert_paper_and_metadata, create_connection_factory
from generic_transformers import transform_json_to_papers, load_data_with_config
from source_configs import get_source_config
import pathlib
import json
import gzip

# Get OpenAlex source configuration
source_config = get_source_config('openalex')

# Create database connection
connection_factory = create_connection_factory()
conn = connection_factory()
cur = conn.cursor()

try:
    # Process the gzipped file directly
    file_path = pathlib.Path('$local_file')
    processed_count = 0
    
    print(f'Processing file: {file_path}')
    
    # Load and transform data using the generic system
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        json_data = []
        for line_num, line in enumerate(f, 1):
            try:
                work_data = json.loads(line.strip())
                json_data.append(work_data)
            except json.JSONDecodeError as e:
                print(f'Invalid JSON on line {line_num}: {e}')
                continue
    
    print(f'Loaded {len(json_data)} records from file')
    
    # Transform using the generic system (this will create proper metadata)
    papers, metadata_list = transform_json_to_papers(json_data, source_config)
    
    print(f'Transformed to {len(papers)} papers with metadata')
    
    # Insert papers and metadata using the main ingestor system
    for paper, metadata in zip(papers, metadata_list):
        if insert_paper_and_metadata(cur, paper, metadata):
            processed_count += 1
            
            # Commit every 100 records
            if processed_count % 100 == 0:
                conn.commit()
                print(f'Processed {processed_count} records...')
    
    # Final commit
    conn.commit()
    print(f'Successfully processed {processed_count} records')
    
except Exception as e:
    print(f'Error: {e}')
    conn.rollback()
    sys.exit(1)
finally:
    cur.close()
    conn.close()
"; then
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

# Function to check database count before and after
check_database_count() {
    local label=$1
    local count=$(psql -h localhost -U tgulden -d doctrove -t -c "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';" | tr -d ' ')
    echo -e "${BLUE}$label: $count OpenAlex papers${NC}"
}

# Main test process
main() {
    echo "Starting test ingestion process..."
    echo "Configuration:"
    echo "  - Temp directory: $TEMP_DIR"
    echo "  - Project directory: $PROJECT_DIR"
    echo "  - Max files: $MAX_FILES"
    echo "  - Test dates: ${TEST_DATES[*]}"
    echo ""
    
    # Check initial database count
    check_database_count "Initial database count"
    echo ""
    
    local files_processed=0
    local files_failed=0
    
    # Process each test date
    for date in "${TEST_DATES[@]}"; do
        echo -e "${BLUE}Processing date: $date${NC}"
        
        # Check if this date has data
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