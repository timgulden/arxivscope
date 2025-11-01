#!/bin/bash
# DocScope/DocTrove Service Status Checker
# Checks the status of API, frontend, and enrichment services

set -e

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    echo "[INFO] Loaded local environment configuration from .env.local"
    export $(grep -v '^#' .env.local | xargs)
elif [ -f ".env.remote" ]; then
    echo "[INFO] Loaded remote environment configuration from .env.remote"
    export $(grep -v '^#' .env.remote | xargs)
else
    echo "[WARNING] No environment file found, using default configuration"
fi

# Set default ports from environment variables or use defaults
API_PORT=${NEW_API_PORT:-${DOCTROVE_API_PORT:-5001}}
FRONTEND_PORT=${NEW_UI_PORT:-${DOCSCOPE_PORT:-3000}}
REACT_PORT=${NEW_UI_PORT:-3000}
LEGACY_DASH_PORT=${DOCSCOPE_PORT:-8050}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[RUNNING]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

EXIT_CODE=0

# Check API server
print_status "Checking DocTrove API server (port $API_PORT)..."
if curl -s http://localhost:$API_PORT/api/health | grep -q '"status": "healthy"'; then
    print_success "API server is responding on port $API_PORT."
else
    print_error "API server is NOT responding on port $API_PORT."
    EXIT_CODE=1
fi

# Check React frontend (recommended)
print_status "Checking React frontend (port $REACT_PORT)..."
if curl -s http://localhost:$REACT_PORT/ >/dev/null 2>&1 && curl -s http://localhost:$REACT_PORT/ | grep -q '<html'; then
    print_success "React frontend is responding on port $REACT_PORT."
else
    print_warning "React frontend is NOT responding on port $REACT_PORT."
    # Check legacy Dash frontend as fallback
    print_status "Checking legacy Dash frontend (port $LEGACY_DASH_PORT)..."
    if curl -s http://localhost:$LEGACY_DASH_PORT/ >/dev/null 2>&1 && curl -s http://localhost:$LEGACY_DASH_PORT/ | grep -q '<html'; then
        print_success "Legacy Dash frontend is responding on port $LEGACY_DASH_PORT."
    else
        print_error "No frontend is responding (checked React on $REACT_PORT and Dash on $LEGACY_DASH_PORT)."
        EXIT_CODE=1
    fi
fi

# Check enrichment event listener
print_status "Checking enrichment event listener..."
if curl -s http://localhost:$API_PORT/api/health/enrichment | grep -q '"status": "healthy"'; then
    ENRICHMENT_PID=$(pgrep -f 'event_listener.py' || true)
    if [ ! -z "$ENRICHMENT_PID" ]; then
        print_success "Enrichment event listener is running (PID: $ENRICHMENT_PID)."
    else
        print_warning "Enrichment event listener is NOT running. (This is only required if you use --with-enrichment)"
    fi
else
    print_warning "Enrichment health check failed. (This is only required if you use --with-enrichment)"
fi

# Check system-wide health
print_status "Checking system-wide health..."
if curl -s http://localhost:$API_PORT/api/health/system | grep -q '"status": "healthy"'; then
    print_success "All services are healthy."
else
    print_warning "Some services may have issues. Check individual service health endpoints."
fi

# Summary
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}All required services are running and responding.${NC}"
else
    echo -e "\n${RED}One or more required services are NOT running or not responding.${NC}"
fi

exit $EXIT_CODE 