#!/bin/bash
# Optimized VACUUM ANALYZE with increased memory settings

echo "🧹 Starting optimized VACUUM ANALYZE..."
echo "Memory settings: work_mem=512MB, maintenance_work_mem=4GB"
echo "Timestamp: $(date)"
echo "=========================================="

PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -d doctrove -U doctrove_admin << 'EOF'
-- Set memory for this session
SET work_mem = '512MB';
SET maintenance_work_mem = '4GB';

-- Verify memory settings
SHOW work_mem;
SHOW maintenance_work_mem;

-- Run optimized VACUUM ANALYZE
VACUUM ANALYZE doctrove_papers;
EOF

echo "✅ Optimized VACUUM ANALYZE completed!"
echo "Statistics updated and dead tuples cleaned up"
