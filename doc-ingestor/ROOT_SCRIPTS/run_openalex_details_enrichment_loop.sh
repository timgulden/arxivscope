#!/bin/bash
# OpenAlex Details Enrichment - Loop until complete
# Extracts journal names, citations, topics, institutions, etc. from OpenAlex raw JSON
# Processes all OpenAlex papers with raw data in 100k chunks until done

set -e

LOG_FILE="/opt/arxivscope/openalex_details_enrichment_full.log"
CHUNK_SIZE=100000
BATCH_SIZE=1000
CHUNK=1

echo "========================================" | tee -a "$LOG_FILE"
echo "Starting OpenAlex Details Enrichment Loop" | tee -a "$LOG_FILE"
echo "Extracts: journal names, citations, topics, institutions, etc." | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "Chunk size: $CHUNK_SIZE, Batch size: $BATCH_SIZE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Function to get remaining count
get_remaining() {
    cd /opt/arxivscope/doctrove-api
    /opt/arxivscope/arxivscope/bin/python -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
cur.execute('''
    SELECT COUNT(*)
    FROM openalex_metadata om
    LEFT JOIN openalex_details_enrichment e ON om.doctrove_paper_id = e.doctrove_paper_id
    WHERE om.openalex_raw_data IS NOT NULL
      AND om.openalex_raw_data != '{}'
      AND e.doctrove_paper_id IS NULL
    LIMIT 1000000
''')
print(cur.fetchone()[0])
"
}

# Main processing loop
while true; do
    # Check how many papers remain
    echo "Checking remaining papers..." | tee -a "$LOG_FILE"
    REMAINING=$(get_remaining)
    
    if [ "$REMAINING" -eq 0 ]; then
        echo "" | tee -a "$LOG_FILE"
        echo "========================================" | tee -a "$LOG_FILE"
        echo "✅ ALL PAPERS PROCESSED!" | tee -a "$LOG_FILE"
        echo "Completed at: $(date)" | tee -a "$LOG_FILE"
        echo "Total chunks processed: $((CHUNK - 1))" | tee -a "$LOG_FILE"
        echo "========================================" | tee -a "$LOG_FILE"
        break
    fi
    
    echo "" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    echo "Chunk $CHUNK" | tee -a "$LOG_FILE"
    echo "Papers remaining: $REMAINING" | tee -a "$LOG_FILE"
    echo "$(date)" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    
    # Run enrichment for this chunk
    cd /opt/arxivscope/doctrove-api
    /opt/arxivscope/arxivscope/bin/python ../doc-ingestor/ROOT_SCRIPTS/openalex_details_enrichment_functional.py \
        --batch-size $BATCH_SIZE \
        --limit $CHUNK_SIZE \
        2>&1 | tee -a "$LOG_FILE"
    
    echo "" | tee -a "$LOG_FILE"
    echo "✅ Chunk $CHUNK complete" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    CHUNK=$((CHUNK + 1))
    
    # Small pause between chunks
    sleep 2
done

echo "" | tee -a "$LOG_FILE"
echo "🎉 OpenAlex details enrichment complete!" | tee -a "$LOG_FILE"

