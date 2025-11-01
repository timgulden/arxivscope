#!/bin/bash
# Create optimized HNSW index with 8GB memory and better parameters

echo "🏗️  Creating optimized HNSW index with 8GB memory..."
echo "Parameters: m=8, ef_construction=64"
echo "Timestamp: $(date)"
echo "=========================================="

PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -d doctrove -U doctrove_admin << 'EOF'
-- Set memory for this session
SET maintenance_work_mem = '8GB';

-- Verify memory setting
SHOW maintenance_work_mem;

-- Create optimized HNSW index
CREATE INDEX idx_papers_embedding_hnsw 
ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops)
WITH (m = 8, ef_construction = 64);
EOF

echo "✅ Optimized HNSW index creation started!"
echo "Expected time: 4-8 hours (regular CREATE INDEX, no CONCURRENTLY)"
