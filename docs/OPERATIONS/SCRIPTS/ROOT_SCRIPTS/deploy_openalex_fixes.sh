#!/bin/bash

# OpenAlex Ingestion Fixes Deployment Script
# Deploys the transaction abort fixes to the server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Server configuration
SERVER_HOST="10.22.198.120"
SERVER_USER="tgulden"
SERVER_PATH="/opt/arxivscope"

echo -e "${BLUE}=== OpenAlex Ingestion Fixes Deployment ===${NC}"
echo "Server: $SERVER_USER@$SERVER_HOST"
echo "Path: $SERVER_PATH"
echo ""

# Function to run command on server
run_on_server() {
    local command="$1"
    echo -e "${YELLOW}Running: $command${NC}"
    ssh "$SERVER_USER@$SERVER_HOST" "$command"
}

# Function to check if command succeeded
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Success${NC}"
    else
        echo -e "${RED}❌ Failed${NC}"
        exit 1
    fi
}

echo -e "${BLUE}Step 1: Checking server connectivity...${NC}"
run_on_server "echo 'Server connection test successful'"
check_result

echo -e "${BLUE}Step 2: Checking current server status...${NC}"
run_on_server "cd $SERVER_PATH && ls -la | head -5"
check_result

echo -e "${BLUE}Step 3: Temporarily changing ownership for Git operations...${NC}"
run_on_server "cd $SERVER_PATH && sudo chown -R tgulden:tgulden ."
check_result

echo -e "${BLUE}Step 4: Pulling latest changes from repository...${NC}"
run_on_server "cd $SERVER_PATH && git pull"
check_result

echo -e "${BLUE}Step 5: Restoring ownership to arxivscope...${NC}"
run_on_server "cd $SERVER_PATH && sudo chown -R arxivscope:arxivscope ."
check_result

echo -e "${BLUE}Step 6: Verifying file permissions...${NC}"
run_on_server "cd $SERVER_PATH && ls -la | head -5"
check_result

echo -e "${BLUE}Step 7: Testing the fixes locally...${NC}"
run_on_server "cd $SERVER_PATH/openalex && python test_fixes.py"
check_result

echo -e "${BLUE}Step 8: Checking current OpenAlex papers count...${NC}"
run_on_server "cd $SERVER_PATH && psql -h localhost -U doctrove_admin -d doctrove -t -c \"SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';\""
check_result

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Test the fixes with real data:"
echo "   ssh $SERVER_USER@$SERVER_HOST"
echo "   cd $SERVER_PATH/openalex"
echo "   python test_real_data.py"
echo ""
echo "2. Run the full OpenAlex ingestion:"
echo "   cd $SERVER_PATH"
echo "   ./openalex_incremental_files.sh --max-files 5"
echo ""
echo "3. Monitor the ingestion process:"
echo "   tail -f /opt/arxivscope/logs/openalex_ingestion.log"
echo ""
echo -e "${GREEN}✅ OpenAlex ingestion fixes have been deployed to the server!${NC}" 