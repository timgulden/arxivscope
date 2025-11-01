#!/bin/bash
# Start script for DocTrove API

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the API directory
cd "$SCRIPT_DIR/doctrove-api"

echo "Starting DocTrove API from: $(pwd)"
echo "API will be available at: http://localhost:5001"

# Start the API
python api.py 
# Start script for DocTrove API

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the API directory
cd "$SCRIPT_DIR/doctrove-api"

echo "Starting DocTrove API from: $(pwd)"
echo "API will be available at: http://localhost:5001"

# Start the API
python api.py 