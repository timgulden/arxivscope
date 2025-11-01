#!/bin/bash

# DocScope Server Update Script
# This script updates the server installation from the Git repository

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}DocScope Server Update${NC}"
echo "========================"

# Check if we're in the right directory
if [ ! -d "/opt/arxivscope" ]; then
    echo -e "${RED}Error: This script must be run from the server installation${NC}"
    exit 1
fi

cd /opt/arxivscope

# Check if Git is configured
if ! git config --get user.name >/dev/null 2>&1; then
    echo -e "${YELLOW}Configuring Git...${NC}"
    git config --global user.name "DocScope Team"
    git config --global user.email "team@arxivscope.org"
fi

# Check current status
echo -e "${YELLOW}Checking current status...${NC}"
git status --porcelain

# Fetch latest changes
echo -e "${YELLOW}Fetching latest changes...${NC}"
git fetch origin main

# Check if there are updates
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}Already up to date!${NC}"
    exit 0
fi

echo -e "${YELLOW}Updates available. Pulling latest changes...${NC}"

# Pull latest changes
git pull origin main

echo -e "${GREEN}Update completed successfully!${NC}"

# Optionally restart services
read -p "Do you want to restart services to apply changes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Restarting services...${NC}"
    ./scripts/ROOT_SCRIPTS/startup.sh --with-enrichment --background --restart
    echo -e "${GREEN}Services restarted!${NC}"
fi

echo -e "${GREEN}Server update completed!${NC}" 