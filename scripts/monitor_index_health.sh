#!/bin/bash
# Index Health Monitor for Bursty Ingestion
# Monitors when HNSW reindexing is needed based on unindexed papers

set -e

# Database connection parameters
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_HOST="localhost"
DB_PORT="5434"

# Thresholds for reindexing
BULK_INGESTION_THRESHOLD=500000  # 500K papers during bulk ingestion
STEADY_STATE_THRESHOLD=100000    # 100K papers during steady state
PERFORMANCE_THRESHOLD=500        # 500ms query threshold

# Log file
LOG_FILE="/opt/arxivscope/logs/index_monitor_$(date +%Y%m%d_%H%M%S).log"

echo "🔍 Starting index health monitoring..."
echo "Timestamp: $(date)"
echo "=========================================="

# Get current statistics
echo "📊 Current database statistics..."

TOTAL_PAPERS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM doctrove_papers;
" | xargs)

PAPERS_WITH_FULL_EMBEDDINGS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL;
" | xargs)

PAPERS_WITH_2D_EMBEDDINGS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding_2d IS NOT NULL;
" | xargs)

echo "Total papers: $TOTAL_PAPERS"
echo "Papers with full embeddings: $PAPERS_WITH_FULL_EMBEDDINGS"
echo "Papers with 2D embeddings: $PAPERS_WITH_2D_EMBEDDINGS"

# Check if HNSW index exists
HNSW_EXISTS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname = 'idx_papers_embedding_hnsw';
" | xargs)

if [ "$HNSW_EXISTS" -eq 0 ]; then
    echo "⚠️  HNSW index does not exist!"
    echo "🚨 RECOMMENDATION: Create HNSW index immediately"
    echo "   Run: CREATE INDEX CONCURRENTLY idx_papers_embedding_hnsw ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 128, ef = 64);"
    exit 1
fi

# Estimate unindexed papers (approximation)
# This is a rough estimate since we can't directly query HNSW index contents
echo "🔍 Estimating unindexed papers..."

# Get papers added recently that might not be indexed
RECENT_PAPERS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL 
AND created_at >= CURRENT_DATE - INTERVAL '7 days';
" | xargs)

echo "Papers with full embeddings added in last 7 days: $RECENT_PAPERS"

# Determine reindexing recommendation
if [ "$RECENT_PAPERS" -gt "$BULK_INGESTION_THRESHOLD" ]; then
    echo "🚨 BULK INGESTION DETECTED: $RECENT_PAPERS papers added in 7 days"
    echo "📋 RECOMMENDATION: Reindex HNSW immediately"
    echo "   Threshold exceeded: $RECENT_PAPERS > $BULK_INGESTION_THRESHOLD"
elif [ "$RECENT_PAPERS" -gt "$STEADY_STATE_THRESHOLD" ]; then
    echo "⚠️  HIGH INGESTION RATE: $RECENT_PAPERS papers added in 7 days"
    echo "📋 RECOMMENDATION: Schedule HNSW reindexing soon"
    echo "   Threshold exceeded: $RECENT_PAPERS > $STEADY_STATE_THRESHOLD"
else
    echo "✅ INGESTION RATE ACCEPTABLE: $RECENT_PAPERS papers added in 7 days"
    echo "📋 RECOMMENDATION: No reindexing needed yet"
fi

# Test query performance
echo "🧪 Testing query performance..."

QUERY_TIME=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
\timing on
SELECT doctrove_paper_id, doctrove_title
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector 
LIMIT 10;
" 2>&1 | grep "Time:" | sed 's/Time: //' | sed 's/ ms//')

if [ -n "$QUERY_TIME" ] && [ "$QUERY_TIME" -gt "$PERFORMANCE_THRESHOLD" ]; then
    echo "⚠️  PERFORMANCE DEGRADATION DETECTED: ${QUERY_TIME}ms query time"
    echo "📋 RECOMMENDATION: Reindex HNSW for performance improvement"
else
    echo "✅ QUERY PERFORMANCE ACCEPTABLE: ${QUERY_TIME}ms"
fi

# Check index size
INDEX_SIZE=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT pg_size_pretty(pg_relation_size('idx_papers_embedding_hnsw'));
" | xargs)

echo "📏 HNSW index size: $INDEX_SIZE"

echo "📝 Log file saved to: $LOG_FILE"
echo "🎯 Index health monitoring complete!"




