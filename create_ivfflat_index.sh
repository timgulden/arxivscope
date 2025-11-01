#!/bin/bash
# Create IVFFlat index for immediate functionality while HNSW builds

echo "🚀 Creating IVFFlat index for immediate functionality..."
echo "This will run in parallel with the HNSW index creation"
echo "Timestamp: $(date)"
echo "=========================================="

PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -d doctrove -U doctrove_admin << 'EOF'
-- Set memory for this session
SET maintenance_work_mem = '4GB';

-- Verify memory setting
SHOW maintenance_work_mem;

-- Create IVFFlat index (much faster than HNSW)
CREATE INDEX CONCURRENTLY idx_papers_embedding_ivfflat 
ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 1000);
EOF

echo "✅ IVFFlat index creation started!"
echo "Expected time: 30-60 minutes (much faster than HNSW)"
echo "Both indexes will coexist and PostgreSQL will choose the best one"


