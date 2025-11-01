#!/bin/bash

# OpenAlex Incremental Sync Runner
# Runs the daily incremental sync to get new/updated papers

set -e  # Exit on any error

# Configuration
PROJECT_DIR="/Users/tgulden/Documents/ArXivScope/arxivscope-back-end"
LOG_FILE="openalex_incremental_sync.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}OpenAlex Incremental Sync Runner${NC}"
echo "====================================="
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment
echo "Activating virtual environment..."
source arxivscope/bin/activate

# Check if services are running
echo "Checking if services are running..."
if ! curl -s http://localhost:5001/health > /dev/null; then
    echo -e "${RED}✗ API server is not running on port 5001${NC}"
    echo "Please start the services first: ./startup.sh --with-enrichment --background"
    exit 1
fi

echo -e "${GREEN}✓ API server is running${NC}"

# Run the incremental sync
echo ""
echo -e "${YELLOW}Starting incremental sync...${NC}"
echo "This will get new/updated papers since the last ingestion"
echo ""

python openalex_incremental_sync.py

# Check the results
echo ""
echo -e "${BLUE}Sync completed!${NC}"
echo ""

# Show recent log entries
if [ -f "$LOG_FILE" ]; then
    echo -e "${BLUE}Recent log entries:${NC}"
    tail -10 "$LOG_FILE"
    echo ""
fi

# Show current database count
echo -e "${BLUE}Current OpenAlex papers in database:${NC}"
psql -h localhost -U tgulden -d doctrove -c "SELECT COUNT(*) as openalex_papers FROM doctrove_papers WHERE doctrove_source = 'openalex';"

echo ""
echo -e "${GREEN}✓ Incremental sync completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Check DocScope: Verify new papers appear in the viewer"
echo "  2. Monitor enrichment: Check embedding generation progress"
echo "  3. Set up automation: Add this to cron for daily runs" 