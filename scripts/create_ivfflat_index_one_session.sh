#!/bin/bash
set -euo pipefail
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_HOST="localhost"
DB_PORT="5434"
DB_PASSWORD="doctrove_admin"
LOG_FILE="/tmp/ivfflat_index_one_session_$(date +%Y%m%d_%H%M%S).log"
{
  echo "🚀 One-session IVFFlat index build starting..."
  echo "Timestamp: $(date)"
  echo "=========================================="
} | tee -a "$LOG_FILE"
PGPASSWORD="$DB_PASSWORD" psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<SQL >> "$LOG_FILE" 2>&1
SET maintenance_work_mem = 4GB;
SET work_mem = 256MB;
SET effective_cache_size = 6GB;
CREATE INDEX CONCURRENTLY idx_papers_embedding_ivfflat_optimized 
ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 15000);
SQL
STATUS=$?
{
  if [ $STATUS -eq 0 ]; then
    echo "✅ IVFFlat index build completed."
  else
    echo "❌ IVFFlat index build failed with status $STATUS"
  fi
} | tee -a "$LOG_FILE"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass)) as size, CASE WHEN indisvalid THEN Valid ELSE Building END as status FROM pg_indexes JOIN pg_index ON pg_indexes.indexname = pg_index.indexrelid::regclass::text WHERE tablename = doctrove_papers AND indexname LIKE %ivfflat_optimized%;" | tee -a "$LOG_FILE"
