#!/bin/bash
# Adaptive HNSW Reindexing for Bursty Ingestion
# Automatically determines when to reindex based on ingestion rate and performance

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
MIN_INDEXED_PAPERS=1000000       # Minimum papers to index before reindexing

# Log file
LOG_FILE="/opt/arxivscope/logs/adaptive_reindex_$(date +%Y%m%d_%H%M%S).log"

echo "🔄 Starting adaptive HNSW reindexing analysis..."
echo "Timestamp: $(date)"
echo "=========================================="

# Check if HNSW index exists
HNSW_EXISTS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname = 'idx_papers_embedding_hnsw';
" | xargs)

if [ "$HNSW_EXISTS" -eq 0 ]; then
    echo "🚨 HNSW index does not exist! Creating initial index..."
    
    # Check if we have enough papers to index
    PAPERS_WITH_FULL_EMBEDDINGS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL;
    " | xargs)
    
    if [ "$PAPERS_WITH_FULL_EMBEDDINGS" -lt "$MIN_INDEXED_PAPERS" ]; then
        echo "⚠️  Not enough papers with full embeddings ($PAPERS_WITH_FULL_EMBEDDINGS < $MIN_INDEXED_PAPERS)"
        echo "📋 RECOMMENDATION: Wait for more papers to be processed before creating index"
        exit 0
    fi
    
    echo "🏗️  Creating initial HNSW index on $PAPERS_WITH_FULL_EMBEDDINGS papers..."
    START_TIME=$(date +%s)
    
    PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF' >> "$LOG_FILE" 2>&1
SET maintenance_work_mem = '4GB';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_embedding_hnsw 
ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128);
EOF
    
    END_TIME=$(date +%s)
    BUILD_DURATION=$((END_TIME - START_TIME))
    
    echo "✅ Initial HNSW index created in ${BUILD_DURATION} seconds ($(($BUILD_DURATION / 60)) minutes)"
    echo "📝 Log file saved to: $LOG_FILE"
    exit 0
fi

# Get current statistics
echo "📊 Analyzing current database state..."

TOTAL_PAPERS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM doctrove_papers;
" | xargs)

PAPERS_WITH_FULL_EMBEDDINGS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL;
" | xargs)

# Get papers added recently
RECENT_PAPERS=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL 
AND created_at >= CURRENT_DATE - INTERVAL '7 days';
" | xargs)

# Test current performance
echo "🧪 Testing current query performance..."

QUERY_TIME=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
\timing on
SELECT doctrove_paper_id, doctrove_title
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector 
LIMIT 10;
" 2>&1 | grep "Time:" | sed 's/Time: //' | sed 's/ ms//')

echo "Current query time: ${QUERY_TIME}ms"

# Determine if reindexing is needed
REINDEX_NEEDED=false
REASON=""

if [ "$RECENT_PAPERS" -gt "$BULK_INGESTION_THRESHOLD" ]; then
    REINDEX_NEEDED=true
    REASON="Bulk ingestion detected: $RECENT_PAPERS papers added in 7 days"
elif [ "$RECENT_PAPERS" -gt "$STEADY_STATE_THRESHOLD" ]; then
    REINDEX_NEEDED=true
    REASON="High ingestion rate: $RECENT_PAPERS papers added in 7 days"
elif [ -n "$QUERY_TIME" ] && [ "$QUERY_TIME" -gt "$PERFORMANCE_THRESHOLD" ]; then
    REINDEX_NEEDED=true
    REASON="Performance degradation: ${QUERY_TIME}ms query time"
fi

if [ "$REINDEX_NEEDED" = true ]; then
    echo "🚨 REINDEXING NEEDED: $REASON"
    echo "🔄 Starting HNSW reindexing..."
    
    # Get current index size
    OLD_INDEX_SIZE=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT pg_size_pretty(pg_relation_size('idx_papers_embedding_hnsw'));
    " | xargs)
    
    echo "📏 Current index size: $OLD_INDEX_SIZE"
    echo "📊 Reindexing $PAPERS_WITH_FULL_EMBEDDINGS papers with full embeddings..."
    
    START_TIME=$(date +%s)
    
    # Drop old index and create new one
    echo "🗑️  Dropping old HNSW index..."
    PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    DROP INDEX CONCURRENTLY IF EXISTS idx_papers_embedding_hnsw;
    " >> "$LOG_FILE" 2>&1
    
    echo "🏗️  Creating new HNSW index..."
    PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF' >> "$LOG_FILE" 2>&1
SET maintenance_work_mem = '4GB';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_embedding_hnsw 
ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128);
EOF
    
    END_TIME=$(date +%s)
    BUILD_DURATION=$((END_TIME - START_TIME))
    
    # Verify index creation
    NEW_INDEX_SIZE=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT pg_size_pretty(pg_relation_size('idx_papers_embedding_hnsw'));
    " | xargs)
    
    echo "✅ HNSW reindexing complete!"
    echo "Build duration: ${BUILD_DURATION} seconds ($(($BUILD_DURATION / 60)) minutes)"
    echo "Index size: $OLD_INDEX_SIZE → $NEW_INDEX_SIZE"
    
    # Test performance after reindexing
    echo "🧪 Testing performance after reindexing..."
    NEW_QUERY_TIME=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    \timing on
    SELECT doctrove_paper_id, doctrove_title
    FROM doctrove_papers 
    WHERE doctrove_embedding IS NOT NULL
    ORDER BY doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector 
    LIMIT 10;
    " 2>&1 | grep "Time:" | sed 's/Time: //' | sed 's/ ms//')
    
    echo "Performance improvement: ${QUERY_TIME}ms → ${NEW_QUERY_TIME}ms"
    
else
    echo "✅ No reindexing needed at this time"
    echo "📊 Current state:"
    echo "   - Total papers: $TOTAL_PAPERS"
    echo "   - Papers with full embeddings: $PAPERS_WITH_FULL_EMBEDDINGS"
    echo "   - Recent papers (7 days): $RECENT_PAPERS"
    echo "   - Query performance: ${QUERY_TIME}ms"
fi

echo "📝 Log file saved to: $LOG_FILE"
echo "🎯 Adaptive reindexing analysis complete!"
