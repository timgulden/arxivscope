#!/bin/bash
# Create HNSW Index with Proper Memory Settings
# This script sets maintenance_work_mem and creates the index properly

set -e

echo "🏗️  Creating HNSW index with 4GB memory..."
echo "Timestamp: $(date)"
echo "=========================================="

# Database connection parameters
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_HOST="localhost"
DB_PORT="5434"

# Create the HNSW index with memory setting in same session
echo "🔧 Setting maintenance_work_mem to 4GB and creating index..."
echo "Expected time: 1-2 hours"
echo "Papers to index: ~8.5M"

PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF'
SET maintenance_work_mem = '4GB';
SHOW maintenance_work_mem;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_embedding_hnsw 
ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128);
EOF

echo "✅ HNSW index creation complete!"
echo "🎯 Expected performance improvement: 10-40x faster queries"
