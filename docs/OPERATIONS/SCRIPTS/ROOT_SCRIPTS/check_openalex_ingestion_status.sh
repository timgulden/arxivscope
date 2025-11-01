#!/bin/bash

# Check OpenAlex Ingestion Status Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration
DB_HOST="localhost"
DB_USER="tgulden"
DB_NAME="doctrove"

echo -e "${BLUE}=== OpenAlex Ingestion Status ===${NC}"
echo ""

# Check database counts
echo -e "${BLUE}Database Counts:${NC}"
total_papers=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT COUNT(*) FROM doctrove_papers;
" | tr -d ' ')

openalex_papers=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';
" | tr -d ' ')

echo "Total papers: $total_papers"
echo "OpenAlex papers: $openalex_papers"
echo ""

# Check ingestion log status
echo -e "${BLUE}Ingestion Log Status:${NC}"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT 
        status,
        COUNT(*) as file_count,
        SUM(records_ingested) as total_records,
        MIN(ingestion_started_at) as earliest_start,
        MAX(ingestion_completed_at) as latest_completion
    FROM openalex_ingestion_log 
    GROUP BY status
    ORDER BY status;
"

echo ""

# Show recent activity
echo -e "${BLUE}Recent Activity (last 10 entries):${NC}"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT 
        file_path,
        file_date,
        status,
        records_ingested,
        ingestion_started_at,
        ingestion_completed_at
    FROM openalex_ingestion_log 
    ORDER BY ingestion_started_at DESC 
    LIMIT 10;
"

echo ""

# Show failed files if any
failed_count=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT COUNT(*) FROM openalex_ingestion_log WHERE status = 'failed';
" | tr -d ' ')

if [ "$failed_count" -gt 0 ]; then
    echo -e "${RED}Failed Files:${NC}"
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT file_path, file_date, error_message, ingestion_started_at
        FROM openalex_ingestion_log 
        WHERE status = 'failed'
        ORDER BY ingestion_started_at DESC;
    "
    echo ""
fi

# Show processing files if any
processing_count=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT COUNT(*) FROM openalex_ingestion_log WHERE status = 'processing';
" | tr -d ' ')

if [ "$processing_count" -gt 0 ]; then
    echo -e "${YELLOW}Currently Processing:${NC}"
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT file_path, file_date, ingestion_started_at
        FROM openalex_ingestion_log 
        WHERE status = 'processing'
        ORDER BY ingestion_started_at DESC;
    "
    echo ""
fi

echo -e "${GREEN}Status check completed!${NC}" 