#!/bin/bash

# DocScope API Startup Script

echo "Starting DocScope API..."

# Determine script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/venv"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -d "$VENV_DIR" ]; then
        echo "Activating virtual environment..."
        source "$VENV_DIR/bin/activate"
    elif [ -d "${PROJECT_ROOT}/arxivscope" ]; then
        echo "Warning: Found legacy 'arxivscope' virtual environment. Consider migrating to 'venv'."
        source "${PROJECT_ROOT}/arxivscope/bin/activate"
    else
        echo "Error: Virtual environment not found."
        echo "   Expected: $VENV_DIR"
        echo "   Create it with: python -m venv venv"
        exit 1
    fi
fi

# Check if .env.local file exists (project root)
if [[ ! -f "${PROJECT_ROOT}/.env.local" ]]; then
    echo "Error: .env.local file not found at ${PROJECT_ROOT}/.env.local"
    echo "   Create one with your database configuration (see env.local.example)"
    exit 1
fi

# Load environment variables from .env.local
set -a
source "${PROJECT_ROOT}/.env.local"
set +a

# Install dependencies if needed
echo "Checking dependencies..."
pip install -r requirements.txt

# Get database configuration from environment
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DOC_TROVE_PORT:-5432}"
DB_NAME="${DB_NAME:-doctrove}"
DB_USER="${DB_USER:-doctrove_admin}"

# Test database connection
echo "Testing database connection..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✓ Database connection successful"
else
    echo "✗ Database connection failed"
    echo "   Host: $DB_HOST, Port: $DB_PORT, Database: $DB_NAME, User: $DB_USER"
    exit 1
fi

# Start the API server
API_PORT="${NEW_API_PORT:-${DOCTROVE_API_PORT:-5001}}"
echo "Starting Flask API server on http://localhost:${API_PORT}"
echo "Press Ctrl+C to stop the server"
echo ""

cd "$SCRIPT_DIR"
python api.py 