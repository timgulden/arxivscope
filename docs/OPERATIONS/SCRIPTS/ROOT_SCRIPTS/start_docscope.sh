#!/bin/bash

# DocScope Startup Script

echo "Starting DocScope..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: Virtual environment not detected. Please activate your virtual environment first."
    echo "Run: source arxivscope/bin/activate"
    exit 1
fi

# Check if API server is running
echo "Checking if API server is running..."
if ! curl -s http://localhost:5001/api/health > /dev/null; then
    echo "Error: API server is not running on http://localhost:5001"
    echo "Please start the API server first:"
    echo "cd doctrove-api && python api.py"
    exit 1
fi

echo "API server is running. Starting DocScope..."
echo "DocScope will be available at http://localhost:8050"
echo "Data will load automatically at startup and on zoom"
echo "Press Ctrl+C to stop the server"
echo ""

python docscope.py 