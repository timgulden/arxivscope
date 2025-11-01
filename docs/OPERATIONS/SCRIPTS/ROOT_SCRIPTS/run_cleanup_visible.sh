#!/bin/bash

# Run OpenAlex cleanup with visible progress
# This script will show progress in the current terminal

echo "Starting OpenAlex cleanup with visible progress..."
echo "This will delete all existing OpenAlex records from the database."
echo "Press Ctrl+C to stop at any time."
echo ""

# Change to the project directory
cd /Users/tgulden/Documents/ArXivScope/arxivscope-back-end

# Activate the virtual environment
source arxivscope/bin/activate

# Run the cleanup script
./cleanup_openalex_batch.sh

echo ""
echo "Cleanup completed!" 