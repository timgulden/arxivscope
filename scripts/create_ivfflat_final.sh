#!/bin/bash
set -euo pipefail

echo "🚀 Creating final IVFFlat index with proper memory settings..."
echo "Timestamp: $(date)"
echo "=========================================="

# Kill any existing build first
echo "🛑 Stopping any existing index build..."
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "DROP INDEX CONCURRENTLY IF EXISTS idx_papers_embedding_ivfflat_optimized;" || true

echo "⚙️  Setting memory parameters and creating index..."
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove << 'SQL'
SET maintenance_work_mem = '5GB';
SET work_mem = '256MB';
SET effective_cache_size = '6GB';
CREATE INDEX idx_papers_embedding_ivfflat_optimized 
ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 4000);
SQL

echo "✅ Index creation completed!"
echo "📊 Final index status:"
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "SELECT i.indexname, pg_size_pretty(pg_relation_size(i.indexname::regclass)) AS size, ix.indisvalid, ix.indisready FROM pg_indexes i JOIN pg_index ix ON i.indexname = ix.indexrelid::regclass::text WHERE i.tablename='doctrove_papers' AND i.indexname='idx_papers_embedding_ivfflat_optimized';"
