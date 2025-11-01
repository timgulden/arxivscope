#!/bin/bash
# Full OpenAlex Details Enrichment Runner
# Processes all OpenAlex papers with raw data in chunks of 100k

set -e

LOG_FILE="/opt/arxivscope/openalex_enrichment_full.log"
CHUNK_SIZE=100000
BATCH_SIZE=1000
TOTAL_PROCESSED=0

echo "========================================" | tee -a "$LOG_FILE"
echo "Starting Full OpenAlex Enrichment" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Get total count
cd /opt/arxivscope/doctrove-api
TOTAL_PAPERS=$(/opt/arxivscope/arxivscope/bin/python -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
cur.execute(\"SELECT COUNT(*) FROM openalex_metadata WHERE openalex_raw_data IS NOT NULL AND openalex_raw_data != '{}'\")
print(cur.fetchone()[0])
")

echo "Total papers to process: $TOTAL_PAPERS" | tee -a "$LOG_FILE"
echo "Chunk size: $CHUNK_SIZE" | tee -a "$LOG_FILE"
echo "Batch size: $BATCH_SIZE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Calculate number of chunks needed
NUM_CHUNKS=$(( ($TOTAL_PAPERS + $CHUNK_SIZE - 1) / $CHUNK_SIZE ))
echo "Will process in $NUM_CHUNKS chunks" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Process each chunk
CHUNK=1
while [ $TOTAL_PROCESSED -lt $TOTAL_PAPERS ]; do
    echo "========================================" | tee -a "$LOG_FILE"
    echo "Processing chunk $CHUNK of $NUM_CHUNKS" | tee -a "$LOG_FILE"
    echo "Progress: $TOTAL_PROCESSED / $TOTAL_PAPERS papers" | tee -a "$LOG_FILE"
    echo "$(date)" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    
    # Run enrichment for this chunk
    /opt/arxivscope/arxivscope/bin/python ../doc-ingestor/ROOT_SCRIPTS/openalex_details_enrichment_functional.py \
        --batch-size $BATCH_SIZE \
        --limit $CHUNK_SIZE \
        2>&1 | tee -a "$LOG_FILE"
    
    TOTAL_PROCESSED=$(( $TOTAL_PROCESSED + $CHUNK_SIZE ))
    CHUNK=$(( $CHUNK + 1 ))
    
    echo "" | tee -a "$LOG_FILE"
    echo "Chunk $((CHUNK - 1)) complete. Total processed: $TOTAL_PROCESSED" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Small pause between chunks
    sleep 2
done

echo "========================================" | tee -a "$LOG_FILE"
echo "Full enrichment complete!" | tee -a "$LOG_FILE"
echo "Completed at: $(date)" | tee -a "$LOG_FILE"
echo "Total papers processed: $TOTAL_PROCESSED" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

