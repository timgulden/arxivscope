#!/bin/bash

# Efficient chunked UPDATE script for publication_year
# This processes updates in batches to avoid locking issues

set -e

# Database connection parameters
DB_HOST="localhost"
DB_PORT="5434"
DB_USER="doctrove_admin"
DB_NAME="doctrove"
export PGPASSWORD="doctrove_admin"

echo "Starting efficient chunked UPDATE for publication_year..."
echo "=================================================="

# Function to run a single chunk
run_chunk() {
    echo "Processing batch of up to 50,000 records..."
    
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    WITH batch_to_update AS (
        SELECT doctrove_paper_id 
        FROM doctrove_papers 
        WHERE doctrove_primary_date IS NOT NULL 
        AND publication_year IS NULL 
        LIMIT 50000
    )
    UPDATE doctrove_papers 
    SET publication_year = EXTRACT(YEAR FROM doctrove_primary_date)
    WHERE doctrove_paper_id IN (SELECT doctrove_paper_id FROM batch_to_update);
    "
}

# Function to check progress
check_progress() {
    echo "Checking progress..."
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT 
        COUNT(CASE WHEN publication_year IS NOT NULL THEN 1 END) as updated_count,
        COUNT(CASE WHEN doctrove_primary_date IS NOT NULL AND publication_year IS NULL THEN 1 END) as remaining_count,
        ROUND(
            (COUNT(CASE WHEN publication_year IS NOT NULL THEN 1 END)::numeric / 
             COUNT(CASE WHEN doctrove_primary_date IS NOT NULL THEN 1 END)) * 100, 2
        ) as percent_complete
    FROM doctrove_papers;
    "
}

# Check initial status
echo "Initial status:"
check_progress

# Process chunks until complete
BATCH_NUM=1
while true; do
    echo ""
    echo "=== Batch $BATCH_NUM ==="
    
    # Run the chunk
    run_chunk
    
    # Check if we're done
    REMAINING=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_primary_date IS NOT NULL AND publication_year IS NULL;")
    REMAINING=$(echo $REMAINING | xargs)  # trim whitespace
    
    echo "Records remaining to update: $REMAINING"
    
    if [ "$REMAINING" -eq 0 ]; then
        echo "✅ Update complete! All records processed."
        break
    fi
    
    # Show progress
    check_progress
    
    # Wait a moment between batches to reduce load
    echo "Waiting 2 seconds before next batch..."
    sleep 2
    
    BATCH_NUM=$((BATCH_NUM + 1))
done

echo ""
echo "🎉 Final status:"
check_progress
echo "Update operation completed successfully!"

