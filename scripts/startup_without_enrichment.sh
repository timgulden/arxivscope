#!/bin/bash
# DocScope/DocTrove Startup Script (Without Enrichment)
# Starts API and frontend only - enrichment should be managed independently
#
# Usage:
#   ./scripts/startup_without_enrichment.sh                    # Start API and frontend only
#   ./scripts/startup_without_enrichment.sh --background       # Start in background mode
#   ./scripts/startup_without_enrichment.sh --force            # Force restart

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
BACKGROUND_MODE=false
FORCE_START=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --background)
            BACKGROUND_MODE=true
            shift
            ;;
        --force|--restart)
            FORCE_START=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            print_error "Usage: $0 [--background] [--force|--restart]"
            exit 1
            ;;
    esac
done

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    print_status "Loaded local environment configuration from .env.local"
    set -a  # automatically export all variables
    source .env.local
    set +a  # turn off automatic export
else
    print_error "CRITICAL: .env.local file not found!"
    exit 1
fi

# Validate required configuration
print_status "Validating required configuration..."

MISSING_CONFIG=false

if [ -z "$DOCTROVE_API_PORT" ]; then
    print_error "CRITICAL: DOCTROVE_API_PORT is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ -z "$DOCSCOPE_PORT" ]; then
    print_error "CRITICAL: DOCSCOPE_PORT is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ -z "$DOCTROVE_API_URL" ]; then
    print_error "CRITICAL: DOCTROVE_API_URL is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ "$MISSING_CONFIG" = true ]; then
    print_error "Configuration validation failed! Please fix the missing values in .env.local"
    exit 1
fi

# Set ports from validated environment variables
API_PORT="$DOCTROVE_API_PORT"
FRONTEND_PORT="$DOCSCOPE_PORT"

print_success "Configuration validation passed!"
print_status "Using ports - API: $API_PORT, Frontend: $FRONTEND_PORT"
print_status "API URL: $DOCTROVE_API_URL"

# Function to check port availability
check_port_available() {
    local port="$1"
    local service_name="$2"
    
    if command -v lsof >/dev/null 2>&1; then
        local port_users=$(lsof -i :$port 2>/dev/null | wc -l)
        if [ $port_users -gt 0 ]; then
            print_warning "$service_name port $port is already in use"
            return 1
        fi
    fi
    return 0
}

# Function to handle existing processes
handle_existing_processes() {
    local has_existing=false
    
    # Check if ports are in use
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i :$API_PORT >/dev/null 2>&1; then
            print_warning "API server port $API_PORT is already in use"
            has_existing=true
        fi
        
        if lsof -i :$FRONTEND_PORT >/dev/null 2>&1; then
            print_warning "Frontend port $FRONTEND_PORT is already in use"
            has_existing=true
        fi
    fi
    
    if [ "$has_existing" = true ]; then
        if [ "$FORCE_START" = true ]; then
            print_status "Force flag detected. Stopping existing processes..."
            ./stop_services.sh >/dev/null 2>&1
            sleep 2
        else
            print_error "Services are already running. Use --force or --restart to stop existing services and restart."
            exit 1
        fi
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    if [ ! -z "$API_PID" ]; then
        print_status "Stopping API server (PID: $API_PID)"
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    print_success "Cleanup complete"
    exit 0
}

# Set up trap for cleanup (only in foreground mode)
if [ "$BACKGROUND_MODE" = false ]; then
    trap cleanup INT TERM EXIT
fi

# Check if we're in the right directory
if [ ! -f "doctrove-api/api.py" ] || [ ! -d "docscope" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

print_status "Starting DocScope/DocTrove system (API and Frontend only)..."
print_warning "NOTE: Enrichment services are managed independently"
print_status "To start enrichment services, run: ./scripts/start_independent_enrichment.sh"

# Check for existing processes and handle them
handle_existing_processes

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "arxivscope" ]; then
        print_status "Activating virtual environment..."
        source arxivscope/bin/activate
    else
        print_error "Virtual environment directory 'arxivscope' not found. Please create it with 'python -m venv arxivscope' and install dependencies."
        exit 1
    fi
fi

# Check database connectivity
print_status "Checking database connectivity..."
if command -v psql >/dev/null 2>&1; then
    DB_HOST=${DOC_TROVE_HOST:-localhost}
    DB_PORT=${DOC_TROVE_PORT:-5434}
    DB_USER=${DOC_TROVE_USER:-tgulden}
    DB_PASSWORD=${DOC_TROVE_PASSWORD:-}
    DB_NAME=${DOC_TROVE_DB:-doctrove}
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connected successfully"
    else
        print_error "Failed to connect to database"
        exit 1
    fi
else
    print_warning "psql not available, skipping database connectivity check"
fi

# Check port availability for API server
if ! check_port_available "$API_PORT" "API server"; then
    if [ "$FORCE_START" = true ]; then
        print_status "Force flag detected. Attempting to start API server anyway..."
    else
        print_error "Cannot start API server. Port $API_PORT is already in use."
        exit 1
    fi
fi

# Start API server
print_status "Starting DocTrove API server..."
cd doctrove-api
if [ "$BACKGROUND_MODE" = true ]; then
    python api.py > ../api.log 2>&1 &
else
    python api.py &
fi
API_PID=$!
cd ..

# Wait for API to start
print_status "Waiting for API server to start..."
sleep 3

# Test API health endpoint
print_status "Testing API health endpoint..."
for i in {1..10}; do
    if curl -s http://localhost:$API_PORT/api/health >/dev/null 2>&1; then
        print_success "API server is responding"
        break
    fi
    if [ $i -eq 10 ]; then
        print_error "API server failed to start after 10 attempts"
        if [ "$BACKGROUND_MODE" = true ]; then
            print_error "Check api.log for details"
        fi
        exit 1
    fi
    print_status "Waiting for API... (attempt $i/10)"
    sleep 2
done

# Check port availability for frontend
if ! check_port_available "$FRONTEND_PORT" "frontend"; then
    if [ "$FORCE_START" = true ]; then
        print_status "Force flag detected. Attempting to start frontend anyway..."
    else
        print_error "Cannot start frontend. Port $FRONTEND_PORT is already in use."
        exit 1
    fi
fi

# Start frontend
print_status "Starting DocScope frontend..."
export DOCTROVE_API_URL="http://localhost:$API_PORT/api"
if [ "$BACKGROUND_MODE" = true ]; then
    python -m docscope.app > frontend.log 2>&1 &
else
    python -m docscope.app &
fi
FRONTEND_PID=$!

# Wait for frontend to start
print_status "Waiting for frontend to start..."
sleep 5

# Test frontend
print_status "Testing frontend..."
for i in {1..10}; do
    if curl -s http://localhost:$FRONTEND_PORT/ >/dev/null 2>&1; then
        print_success "Frontend is responding"
        break
    fi
    if [ $i -eq 10 ]; then
        print_error "Frontend failed to start after 10 attempts"
        if [ "$BACKGROUND_MODE" = true ]; then
            print_error "Check frontend.log for details"
        fi
        exit 1
    fi
    print_status "Waiting for frontend... (attempt $i/10)"
    sleep 2
done

# Show final status
echo ""
print_success "DocScope/DocTrove system started successfully!"
echo ""
echo -e "${GREEN}Services:${NC}"
echo -e "  API Server: ${BLUE}http://localhost:$API_PORT${NC}"
echo -e "  Frontend:   ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo ""
echo -e "${GREEN}Process IDs:${NC}"
echo -e "  API Server: ${YELLOW}$API_PID${NC}"
echo -e "  Frontend:   ${YELLOW}$FRONTEND_PID${NC}"
echo ""
echo -e "${GREEN}Log Files:${NC}"
echo -e "  API:        ${YELLOW}api.log${NC}"
echo -e "  Frontend:   ${YELLOW}frontend.log${NC}"
echo ""
print_warning "Enrichment services are managed independently!"
print_status "To start enrichment services:"
print_status "  ./scripts/start_independent_enrichment.sh"
echo ""
print_status "To check enrichment status:"
print_status "  ./scripts/start_independent_enrichment.sh --status"
echo ""

if [ "$BACKGROUND_MODE" = true ]; then
    print_success "All services started in background mode"
    print_status "To stop services, run: ./stop_services.sh"
else
    print_status "Press Ctrl+C to stop all services"
    print_status "Or run: ./stop_services.sh"
    wait
fi









