#!/bin/bash
# Rebuild All Critical Indexes After Major Database Changes
#
# This script rebuilds indexes that benefit from periodic rebuilding,
# especially after major data changes like bulk deletions or migrations.
#
# Indexes rebuilt:
#   1. IVFFlat vector index (semantic similarity) - CRITICAL, needs extra memory
#   2. GIST 2D spatial index (visualization) - CRITICAL for UI
#   3. GIN authors array index (author search) - Important for filtering
#   4. BRIN date index (efficient date range queries)
#
# Indexes NOT rebuilt (PostgreSQL maintains automatically):
#   - All BTREE indexes (source, source_id, primary_date, etc.)
#   - Primary key and unique constraints
#   - These are efficiently maintained by PostgreSQL and don't need manual rebuilding
#
# Usage:
#   ./rebuild_all_indexes.sh              # Rebuild all critical indexes
#   ./rebuild_all_indexes.sh --dry-run    # Show what would be done

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Load database credentials
if [ -f "/opt/arxivscope/.env.local" ]; then
    source /opt/arxivscope/.env.local
else
    echo -e "${RED}Error: .env.local not found${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Critical Index Rebuild${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN MODE]${NC} - No changes will be made"
    echo ""
fi

echo "Indexes to rebuild:"
echo "  1. IVFFlat vector index (22GB) - semantic similarity search"
echo "  2. GIST 2D spatial index (232MB) - visualization queries"
echo "  3. GIN authors index (241MB) - author search"
echo "  4. BRIN date index (168KB) - date range queries"
echo ""
echo "Indexes NOT rebuilt (automatically maintained by PostgreSQL):"
echo "  - BTREE indexes (source, source_id, primary_date, composite)"
echo "  - Primary key (doctrove_paper_id)"
echo "  - Unique constraints"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Dry run complete. Use without --dry-run to execute.${NC}"
    exit 0
fi

read -p "Continue with index rebuild? This will take 20-30 minutes. (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}[INFO]${NC} Starting index rebuild..."
echo ""

# Execute rebuild
PGPASSWORD=$DOC_TROVE_PASSWORD psql -h $DOC_TROVE_HOST -p $DOC_TROVE_PORT -U $DOC_TROVE_USER -d $DOC_TROVE_DB << 'EOF'
\timing on

-- Set higher memory for vector index rebuild
SET maintenance_work_mem = '1GB';

SHOW maintenance_work_mem;

-- Clean up any leftover concurrent rebuild indexes first
DROP INDEX IF EXISTS idx_papers_embedding_ivfflat_optimized_ccnew;
DROP INDEX IF EXISTS idx_doctrove_embedding_2d_ccnew;
DROP INDEX IF EXISTS idx_papers_authors_ccnew;
DROP INDEX IF EXISTS idx_papers_date_brin_ccnew;

-- 1. Rebuild IVFFlat vector index (largest, most critical)
-- This is the most important index for semantic similarity search
\echo '=== Rebuilding IVFFlat vector index (this takes ~20 minutes)...'
REINDEX INDEX idx_papers_embedding_ivfflat_optimized;

-- Reset memory for other indexes
RESET maintenance_work_mem;

-- 2. Rebuild GIST 2D spatial index (used for visualization bounding box queries)
\echo '=== Rebuilding GIST 2D spatial index...'
REINDEX INDEX idx_doctrove_embedding_2d;

-- 3. Rebuild GIN authors array index (used for author search)
\echo '=== Rebuilding GIN authors index...'
REINDEX INDEX idx_papers_authors;

-- 4. Rebuild BRIN date index (efficient for date range queries)
\echo '=== Rebuilding BRIN date index...'
REINDEX INDEX idx_papers_date_brin;

-- Summary
\echo ''
\echo '=== Index Rebuild Summary ==='
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size,
    CASE 
        WHEN indexdef LIKE '%ivfflat%' THEN 'IVFFlat (vector similarity)'
        WHEN indexdef LIKE '%gist%' THEN 'GIST (spatial queries)'
        WHEN indexdef LIKE '%gin%' THEN 'GIN (array search)'
        WHEN indexdef LIKE '%brin%' THEN 'BRIN (range queries)'
        ELSE 'Standard'
    END as index_type
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname IN (
    'idx_papers_embedding_ivfflat_optimized',
    'idx_doctrove_embedding_2d',
    'idx_papers_authors',
    'idx_papers_date_brin'
)
ORDER BY pg_relation_size(indexname::regclass) DESC;

SELECT '✅ All critical indexes rebuilt successfully!' as status;
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ All Indexes Rebuilt Successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "All critical indexes have been rebuilt and optimized."
    echo ""
    echo "Next steps:"
    echo "  1. Run VACUUM ANALYZE to update statistics"
    echo "  2. Test query performance"
    echo "  3. Monitor application performance"
    echo ""
else
    echo ""
    echo -e "${RED}Index rebuild encountered errors${NC}"
    exit 1
fi



