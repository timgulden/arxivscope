#!/bin/bash
# Monitor IVFFlat index build progress
# Usage: ./scripts/monitor_index_build.sh

echo "🔍 Monitoring IVFFlat index build progress..."
echo "Timestamp: $(date)"
echo "=========================================="

# Database connection parameters
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_HOST="localhost"
DB_PORT="5434"

# Check if index exists and get its size
echo "📊 Checking index status..."
PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size,
    CASE 
        WHEN pg_relation_size(indexname::regclass) > 0 THEN 'Building/Complete'
        ELSE 'Not Started'
    END as status
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname LIKE '%ivfflat%';
"

# Check build progress if available
echo "📈 Checking build progress..."
PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    pid,
    state,
    query_start,
    now() - query_start as duration,
    LEFT(query, 100) as query_preview
FROM pg_stat_activity 
WHERE query LIKE '%CREATE INDEX%ivfflat%'
AND state = 'active';
"

echo "✅ Monitoring complete!"
echo "Run this script periodically to check progress."













