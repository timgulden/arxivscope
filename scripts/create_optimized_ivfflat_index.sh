#!/bin/bash
# Create optimized IVFFlat index with proper memory settings
# Usage: ./scripts/create_optimized_ivfflat_index.sh

set -e  # Exit on any error

echo "🚀 Creating optimized IVFFlat index..."
echo "Timestamp: $(date)"
echo "=========================================="

# Database connection parameters
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_HOST="localhost"
DB_PORT="5434"

# Set memory parameters and create index
echo "⚙️  Setting memory parameters and creating index..."
PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF'
-- Set memory parameters for optimal index building
SET maintenance_work_mem = '2GB';
SET work_mem = '256MB';
SET effective_cache_size = '6GB';

-- Create optimized IVFFlat index
CREATE INDEX CONCURRENTLY idx_papers_embedding_ivfflat_optimized 
ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 20000);
EOF

echo "✅ Optimized IVFFlat index creation initiated!"
echo "This will take 2-4 hours to complete."
echo "Use ./scripts/monitor_index_build.sh to check progress."













