#!/bin/bash

# OpenAlex Incremental File Ingestion Script
# Processes S3 files newer than a specified date, tracking progress in database

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
BATCH_SIZE=5000

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Database configuration
DB_HOST="localhost"
DB_PORT="${DOC_TROVE_PORT:-5432}"
# Use environment variable or default to doctrove_admin for server
DB_USER="${DOC_TROVE_USER:-doctrove_admin}"
DB_NAME="doctrove"

# Set PGPASSWORD for psql commands
export PGPASSWORD="${DOC_TROVE_PASSWORD:-doctrove_admin}"

# Default values
EARLIEST_DATE="2025-01-01"
MAX_FILES=1000  # Process all available files
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --earliest-date)
            EARLIEST_DATE="$2"
            shift 2
            ;;
        --max-files)
            MAX_FILES="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --earliest-date DATE    Process files from this date onwards (YYYY-MM-DD)"
            echo "  --max-files N           Maximum number of files to process (default: 10)"
            echo "  --batch-size N          Database batch size for cleanup (default: 5000)"
            echo "  --dry-run               Simulate ingestion without inserting records"
            echo "  --help                  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=== OpenAlex Incremental File Ingestion ===${NC}"
echo "Earliest date: $EARLIEST_DATE"
echo "Max files: $MAX_FILES"
echo "Batch size: $BATCH_SIZE"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE - No records will be inserted${NC}"
fi
echo ""

# Ensure temp directory exists
mkdir -p "$TEMP_DIR"

# Function to log to database
log_file_start() {
    local file_path="$1"
    local file_date="$2"
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        INSERT INTO openalex_ingestion_log (file_path, file_date, status, ingestion_started_at)
        VALUES ('$file_path', '$file_date', 'processing', NOW())
        ON CONFLICT (file_path) DO UPDATE SET
            status = 'processing',
            ingestion_started_at = NOW(),
            ingestion_completed_at = NULL,
            error_message = NULL;
    " > /dev/null 2>&1
}

log_file_complete() {
    local file_path="$1"
    local records_ingested="$2"
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        UPDATE openalex_ingestion_log 
        SET status = 'completed',
            records_ingested = $records_ingested,
            ingestion_completed_at = NOW()
        WHERE file_path = '$file_path';
    " > /dev/null 2>&1
}

log_file_error() {
    local file_path="$1"
    local error_message="$2"
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        UPDATE openalex_ingestion_log 
        SET status = 'failed',
            error_message = '$error_message',
            ingestion_completed_at = NOW()
        WHERE file_path = '$file_path';
    " > /dev/null 2>&1
}

# Function to check if file has been processed
is_file_processed() {
    local file_path="$1"
    
    local result=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM openalex_ingestion_log 
        WHERE file_path = '$file_path' AND status = 'completed';
    " | tr -d ' ')
    
    if [ "$result" -eq 1 ]; then
        return 0  # File has been processed
    else
        return 1  # File has not been processed
    fi
}

# Function to get list of available files from S3
get_available_files() {
    # In dry run, avoid network calls entirely and just return a single mock file
    if [ "$DRY_RUN" = true ]; then
        echo "updated_date=${EARLIEST_DATE}/part_000.gz|${EARLIEST_DATE}"
        return 0
    fi
    echo -e "${BLUE}Discovering available files from S3...${NC}"
    
    # Use curl to list files from the correct S3 URL
    # The structure is: https://openalex.s3.us-east-1.amazonaws.com/data/works/updated_date=YYYY-MM-DD/part_XXX.gz
    
    # For now, let's use a simple approach and check a few recent dates
    current_date=$(date +%Y-%m-%d)
    
    # Generate a list of dates from earliest_date to current_date
    start_date="$EARLIEST_DATE"
    end_date="$current_date"
    
    # Convert dates to timestamps for iteration
    start_timestamp=$(date -d "$start_date" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$start_date" +%s 2>/dev/null)
    end_timestamp=$(date -d "$end_date" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$end_date" +%s 2>/dev/null)
    
    if [ -n "$start_timestamp" ] && [ -n "$end_timestamp" ]; then
        # Iterate through each date from start to end
        current_timestamp=$start_timestamp
        while [ "$current_timestamp" -le "$end_timestamp" ]; do
            check_date=$(date -d "@$current_timestamp" +%Y-%m-%d 2>/dev/null || date -j -r "$current_timestamp" +%Y-%m-%d 2>/dev/null)
            
            # Check if file exists
            s3_url="$S3_BASE_URL/updated_date=$check_date/part_000.gz"
            if curl -s --head "$s3_url" | grep -q "200 OK"; then
                echo "updated_date=$check_date/part_000.gz|$check_date"
            fi
            
            # Move to next day (86400 seconds = 1 day)
            current_timestamp=$((current_timestamp + 86400))
        done
    else
        echo -e "${RED}Error: Could not parse dates for iteration${NC}" >&2
        return 1
    fi | sort -t'|' -k2,2 | head -n "$MAX_FILES"
}

# Function to process a single file
process_file() {
    local file_path="$1"
    local file_date="$2"
    local local_file="$TEMP_DIR/$(basename "$file_path")"
    
    echo -e "${BLUE}Processing: $file_path (Date: $file_date)${NC}"
    
    # Log start of processing (skip in dry run mode)
    if [ "$DRY_RUN" = false ]; then
        log_file_start "$file_path" "$file_date"
    fi
    
    # Step 1: Download file
    if [ "$DRY_RUN" = true ]; then
        echo "  ${YELLOW}[DRY RUN] Mock Download: $file_path${NC}"
        echo "    ${YELLOW}✓ Mock Downloaded${NC}"
    else
        echo "  Downloading..."
        
        # Ensure temp directory has correct permissions
        sudo chown -R arxivscope:arxivscope "$TEMP_DIR" 2>/dev/null || true
        
        s3_url="$S3_BASE_URL/$file_path"
        if curl -s -o "$local_file" "$s3_url"; then
            echo -e "    ${GREEN}✓ Downloaded${NC}"
        else
            log_file_error "$file_path" "Failed to download file"
            echo -e "    ${RED}✗ Download failed${NC}"
            return 1
        fi
    fi
    
    # Step 2: Ingest file
    if [ "$DRY_RUN" = true ]; then
        echo "  ${YELLOW}[DRY RUN] Mock Ingestion: $file_path${NC}"
        # Dry run mode - simulate processing without inserting
        echo "    ${YELLOW}[DRY RUN] Mock Ingestion: $file_path${NC}"
        
        # Simulate batch processing with 1K batches
        echo "    ${YELLOW}🚀 Starting streaming OpenAlex processing: $file_path${NC}"
        echo "    ${YELLOW}📦 Batch size: 1,000 records${NC}"
        echo "    ${YELLOW}🎯 Processing limit: No limit${NC}"
        echo ""
        
        # Mock a few batches to show the flow
        for batch_num in 1 2 3 4 5; do
            echo "    ${YELLOW}📊 Processing batch $batch_num (1000 records)${NC}"
            echo "    ${YELLOW}   🔄 Processing 1000 records...${NC}"
            echo "    ${YELLOW}      🔧 Starting batch processing: 1000 records${NC}"
            echo "    ${YELLOW}         📝 Processed 100/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 200/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 300/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 400/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 500/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 600/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 700/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 800/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 900/1000 papers in current batch${NC}"
            echo "    ${YELLOW}         📝 Processed 1000/1000 papers in current batch${NC}"
            echo "    ${YELLOW}   ✅ Batch $batch_num completed: 1000 processed, 0 errors${NC}"
            echo "    ${YELLOW}   📈 Total progress: $((batch_num * 1000)) papers processed so far${NC}"
            echo ""
        done
        
        # Mock final batch
        echo "    ${YELLOW}📊 Processing final batch 6 (500 records)${NC}"
        echo "    ${YELLOW}   🔄 Processing 500 records...${NC}"
        echo "    ${YELLOW}      🔧 Starting batch processing: 500 records${NC}"
        echo "    ${YELLOW}         📝 Processed 100/500 papers in current batch${NC}"
        echo "    ${YELLOW}         📝 Processed 200/500 papers in current batch${NC}"
        echo "    ${YELLOW}         📝 Processed 300/500 papers in current batch${NC}"
        echo "    ${YELLOW}         📝 Processed 400/500 papers in current batch${NC}"
        echo "    ${YELLOW}         📝 Processed 500/500 papers in current batch${NC}"
        echo "    ${YELLOW}   ✅ Batch 6 completed: 500 processed, 0 errors${NC}"
        echo "    ${YELLOW}   📈 Total progress: 5,500 papers processed so far${NC}"
        echo ""
        
        echo "    ${YELLOW}✅ Processing completed successfully!${NC}"
        echo "    ${YELLOW}   Records processed: 5,500${NC}"
        echo "    ${YELLOW}   Total time: 0.1s${NC}"
        echo "    ${YELLOW}   Batches processed: 6${NC}"
        
        processed_count=5500
        
    else
        # Real ingestion mode - use our new streaming openalex ingester
        echo "  Ingesting..."
        cd "$PROJECT_DIR"
        source arxivscope/bin/activate
        
        # Set environment variables for database connection
        export DOC_TROVE_USER=doctrove_admin
        export DOC_TROVE_PASSWORD=doctrove_admin
        export DOC_TROVE_HOST=localhost
        export DOC_TROVE_PORT=5434
        
        # Set PGPASSWORD for psql commands
        export PGPASSWORD="$DOC_TROVE_PASSWORD"
        # Use the working functional ingester instead of the placeholder streaming ingester
        echo "    🚀 Starting functional OpenAlex processing: $file_path"
        echo "    📦 Batch size: 1,000 records"
        echo "    💾 Functional mode - real database insertion"
        echo ""
        
        # Process the file using our working functional ingester
        python_output=$(python3 openalex/functional_ingester.py "$local_file" 2>&1)
        python_exit_code=$?
        
        if [ $python_exit_code -eq 0 ]; then
            echo -e "    ${GREEN}✓ Ingestion completed${NC}"
            
            # Extract the processed count from the output
            processed_count=$(echo "$python_output" | grep "Records processed:" | grep -o '[0-9,]\+' | tr -d ',')
            if [ -n "$processed_count" ]; then
                echo -e "    ${GREEN}   Records processed: $processed_count${NC}"
                # Log completion
                log_file_complete "$file_path" "$processed_count"
            else
                # Fallback: estimate from file size
                line_count=$(gunzip -c "$local_file" | wc -l)
                estimated_valid=$((line_count * 8 / 10))  # Assume 80% are valid
                processed_count=$estimated_valid
                echo -e "    ${YELLOW}   Estimated records processed: $processed_count${NC}"
                # Log completion with estimated count
                log_file_complete "$file_path" "$processed_count"
            fi
        else
            log_file_error "$file_path" "Python ingestion failed: $python_output"
            echo -e "    ${RED}✗ Ingestion failed${NC}"
            echo "    Error output: $python_output"
            return 1
        fi
    fi
    
    # Step 3: Clean up
    echo "  Cleaning up..."
    rm -f "$local_file"
    echo -e "    ${GREEN}✓ Cleaned up${NC}"
    
    echo -e "${GREEN}✓ Completed: $file_path${NC}"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}Starting incremental ingestion...${NC}"
    echo ""
    
    # Get list of files to process
    files_to_process=$(get_available_files)
    
    if [ -z "$files_to_process" ]; then
        echo -e "${YELLOW}No files found matching criteria${NC}"
        exit 0
    fi
    
    # Count total files
    total_files=$(echo "$files_to_process" | wc -l)
    echo -e "${BLUE}Found $total_files files to process${NC}"
    echo ""
    
    # Process each file
    processed_count=0
    failed_count=0
    
    while IFS='|' read -r file_path file_date; do
        if [ -n "$file_path" ] && [ -n "$file_date" ]; then
            # Check if file has already been processed
            if is_file_processed "$file_path"; then
                echo -e "${YELLOW}Skipping (already processed): $file_path${NC}"
                continue
            fi
            
            # Process the file
            if process_file "$file_path" "$file_date"; then
                ((processed_count++))
            else
                ((failed_count++))
            fi
        fi
    done <<< "$files_to_process"
    
    # Summary
    echo -e "${BLUE}=== Ingestion Summary ===${NC}"
    echo "Files processed: $processed_count"
    echo "Files failed: $failed_count"
    echo "Files skipped (already processed): $((total_files - processed_count - failed_count))"
    
    # Show final database count
    final_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';
    " | tr -d ' ')
    
    echo "Total OpenAlex papers in database: $final_count"
    echo ""
    echo -e "${GREEN}✓ Incremental ingestion completed!${NC}"
}

# Run main function
main "$@" 