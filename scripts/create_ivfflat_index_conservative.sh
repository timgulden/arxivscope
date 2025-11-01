#!/bin/bash
set -e

# Database connection parameters
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_HOST="localhost"
DB_PORT="5434"
DB_PASSWORD="doctrove_admin"

# Log file
LOG_FILE="/tmp/ivfflat_index_build_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 Creating conservative IVFFlat index..."
echo "Timestamp: $(date)"
echo "=========================================="

# Set memory parameters first
echo "⚙️  Setting memory parameters..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SET maintenance_work_mem = '4GB';" >> "$LOG_FILE" 2>&1
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SET work_mem = '256MB';" >> "$LOG_FILE" 2>&1
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SET effective_cache_size = '6GB';" >> "$LOG_FILE" 2>&1

echo "🏗️  Creating IVFFlat index with conservative parameters..."
echo "   - Lists: 15000 (reasonable for 10M vectors)"
echo "   - Memory: 4GB maintenance_work_mem"
echo "   - This should take 30-60 minutes"

START_TIME=$(date +%s)

# Create the index
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "CREATE INDEX CONCURRENTLY idx_papers_embedding_ivfflat_optimized ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops) WITH (lists = 15000);" >> "$LOG_FILE" 2>&1

END_TIME=$(date +%s)
BUILD_DURATION=$((END_TIME - START_TIME))

echo "✅ IVFFlat index creation complete!"
echo "Build duration: ${BUILD_DURATION} seconds ($(($BUILD_DURATION / 60)) minutes)"
echo "📝 Log file saved to: $LOG_FILE"

# Check the final index status
echo "📊 Final index status:"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass)) as size, CASE WHEN indisvalid THEN 'Valid' ELSE 'Building' END as status FROM pg_indexes JOIN pg_index ON pg_indexes.indexname = pg_index.indexrelid::regclass::text WHERE tablename = 'doctrove_papers' AND indexname LIKE '%ivfflat_optimized%';"

echo "🎯 Next steps:"
echo "   1. Test query performance with: ./scripts/run_focused_performance_tests.py"
echo "   2. Set ivfflat.probes = 10 for better recall"
echo "   3. Monitor with: ./scripts/monitor_index_build.sh"













