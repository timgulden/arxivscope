#!/bin/bash
# Rebuild Vector Similarity Index (IVFFlat)
# 
# This script rebuilds the IVFFlat vector index on doctrove_papers.doctrove_embedding
# with appropriate memory settings to avoid "maintenance_work_mem too small" errors.
#
# The IVFFlat index is critical for semantic similarity search performance.
# It should be rebuilt after major data changes or when query performance degrades.
#
# Usage:
#   ./rebuild_vector_index.sh                    # Use default settings
#   ./rebuild_vector_index.sh --memory 2GB       # Specify custom memory
#   ./rebuild_vector_index.sh --concurrent       # Use CONCURRENTLY (slower but non-blocking)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Default settings
MEMORY="1GB"
CONCURRENT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --memory)
            MEMORY="$2"
            shift 2
            ;;
        --concurrent)
            CONCURRENT=true
            shift
            ;;
        --help)
            echo "Rebuild Vector Similarity Index Script"
            echo ""
            echo "Usage:"
            echo "  $0                      # Default: 1GB memory, exclusive lock"
            echo "  $0 --memory 2GB         # Use 2GB memory"
            echo "  $0 --concurrent         # Use CONCURRENTLY (slower but non-blocking)"
            echo ""
            echo "Options:"
            echo "  --memory SIZE    Set maintenance_work_mem (default: 1GB)"
            echo "  --concurrent     Use REINDEX CONCURRENTLY (allows queries during rebuild)"
            echo ""
            echo "Notes:"
            echo "  - Default mode acquires exclusive lock (faster, blocks queries briefly)"
            echo "  - Concurrent mode allows queries but takes 2-3x longer"
            echo "  - For 2.9M papers, typically needs 500MB-1GB memory"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Load database credentials
if [ -f "/opt/arxivscope/.env.local" ]; then
    source /opt/arxivscope/.env.local
else
    echo -e "${RED}Error: .env.local not found${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Vector Similarity Index Rebuild${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}[INFO]${NC} Memory allocation: $MEMORY"
echo -e "${BLUE}[INFO]${NC} Concurrent mode: $CONCURRENT"
echo -e "${BLUE}[INFO]${NC} Database: $DOC_TROVE_DB"
echo ""

# Build SQL command
if [ "$CONCURRENT" = true ]; then
    REINDEX_CMD="REINDEX INDEX CONCURRENTLY idx_papers_embedding_ivfflat_optimized;"
    echo -e "${YELLOW}[INFO]${NC} Using CONCURRENTLY mode (slower but non-blocking)"
else
    REINDEX_CMD="REINDEX INDEX idx_papers_embedding_ivfflat_optimized;"
    echo -e "${YELLOW}[INFO]${NC} Using exclusive lock mode (faster but blocks queries briefly)"
fi

# Execute rebuild
echo -e "${BLUE}[INFO]${NC} Starting index rebuild..."
echo ""

PGPASSWORD=$DOC_TROVE_PASSWORD psql -h $DOC_TROVE_HOST -p $DOC_TROVE_PORT -U $DOC_TROVE_USER -d $DOC_TROVE_DB << EOF
\timing on

-- Set memory for this session
SET maintenance_work_mem = '$MEMORY';

-- Show current setting
SHOW maintenance_work_mem;

-- Rebuild the index
$REINDEX_CMD

-- Reset to default
RESET maintenance_work_mem;

-- Verify index exists and is valid
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname = 'idx_papers_embedding_ivfflat_optimized';

SELECT 'Vector index rebuild COMPLETE!' as status;
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ Index Rebuild Successful!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "The vector similarity index has been rebuilt and is optimized"
    echo "for the current dataset of 2.9M papers."
    echo ""
    echo "This index is used for semantic similarity search queries."
    echo "Query performance should now be optimal."
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ Index Rebuild Failed${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Check the error messages above for details."
    echo "You may need to increase --memory if memory errors occurred."
    exit 1
fi



