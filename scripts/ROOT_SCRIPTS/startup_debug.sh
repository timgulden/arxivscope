#!/bin/bash
# DocScope/DocTrove Startup Script
# Automates the startup of the entire system
#
# Usage:
#   ./startup.sh                    # Start API and frontend only (foreground)
#   ./startup.sh --with-enrichment  # Start API, frontend, and event-driven enrichment (foreground)
#   ./startup.sh --background       # Start in background mode
#   ./startup.sh --with-enrichment --background  # Start everything in background
#   ./startup.sh --force            # Force restart (stop existing services first)
#   ./startup.sh --with-enrichment --background --force  # Force restart in background
#
# The enrichment system automatically processes papers for embeddings and 2D projections
# when new papers are ingested into the database.

# set -e  # Exit on any error

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
WITH_ENRICHMENT=false
FORCE_START=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --background)
            BACKGROUND_MODE=true
            shift
            ;;
        --with-enrichment)
            WITH_ENRICHMENT=true
            shift
            ;;
        --force)
            FORCE_START=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            print_error "Usage: $0 [--with-enrichment] [--background] [--force]"
            exit 1
            ;;
    esac
done

# Function to check if a service is running
check_service_running() {
    local pattern="$1"
    local service_name="$2"
    
    local pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        echo "$pids"
        return 0
    else
        return 1
    fi
}

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
    local api_pids=$(check_service_running "python.*api.py" "API server")
    local frontend_pids=$(check_service_running "python.*-m docscope.app" "frontend")
    local enrichment_pids=""
    
    if [ "$WITH_ENRICHMENT" = true ]; then
        enrichment_pids=$(check_service_running "python.*event_listener.py" "enrichment system")
    fi
    
    local has_existing=false
    
    if [ ! -z "$api_pids" ]; then
        print_warning "API server is already running (PIDs: $api_pids)"
        has_existing=true
    fi
    
    if [ ! -z "$frontend_pids" ]; then
        print_warning "Frontend is already running (PIDs: $frontend_pids)"
        has_existing=true
    fi
    
    if [ ! -z "$enrichment_pids" ]; then
        print_warning "Enrichment system is already running (PIDs: $enrichment_pids)"
        has_existing=true
    fi
    
    if [ "$has_existing" = true ]; then
        if [ "$FORCE_START" = true ]; then
            print_status "Force flag detected. Stopping existing processes..."
            ./stop_services.sh >/dev/null 2>&1
            sleep 2
        else
            print_error "Services are already running. Use --force to stop existing services and restart."
            print_error "Or run ./stop_services.sh first, then run this script again."
            exit 1
        fi
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    if [ ! -z "$ENRICHMENT_PID" ]; then
        print_status "Stopping enrichment system (PID: $ENRICHMENT_PID)"
        kill $ENRICHMENT_PID 2>/dev/null || true
    fi
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
    print_error "This script must be run from the project root directory (arxivscope-back-end)"
    print_error "Current directory: $(pwd)"
    exit 1
fi

print_status "Starting DocScope/DocTrove system..."

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
    DB_COUNT=$(psql -d doctrove -t -c "SELECT COUNT(*) FROM doctrove_papers;" 2>/dev/null | xargs)
    if [ $? -eq 0 ] && [ ! -z "$DB_COUNT" ]; then
        print_success "Database connected. Found $DB_COUNT papers."
    else
        print_error "Database connection failed or no papers found"
        print_error "Make sure PostgreSQL is running and the 'doctrove' database exists"
        exit 1
    fi
else
    print_warning "psql not found. Skipping database check."
fi

# Check if event-driven enrichment should be started
if [ "$WITH_ENRICHMENT" = true ]; then
    print_status "Starting event-driven enrichment system..."
    cd embedding-enrichment
    if [ "$BACKGROUND_MODE" = true ]; then
        # In background mode, redirect output to log file
        python event_listener.py > ../enrichment.log 2>&1 &
    else
        # In foreground mode, show output
        python event_listener.py &
    fi
    ENRICHMENT_PID=$!
    cd ..
    
    # Wait for enrichment system to start
    print_status "Waiting for enrichment system to start..."
    sleep 3
    
    # Check if enrichment process is running
    if kill -0 $ENRICHMENT_PID 2>/dev/null; then
        print_success "Event-driven enrichment system started (PID: $ENRICHMENT_PID)"
    else
        print_error "Enrichment system failed to start"
        if [ "$BACKGROUND_MODE" = true ]; then
            print_error "Check enrichment.log for details"
        fi
        exit 1
    fi
else
    print_status "Skipping event-driven enrichment system (use --with-enrichment to enable)"
    ENRICHMENT_PID=""
fi

# Check port availability for API server
if ! check_port_available "5001" "API server"; then
    if [ "$FORCE_START" = true ]; then
        print_status "Force flag detected. Attempting to start API server anyway..."
    else
        print_error "Cannot start API server. Port 5001 is already in use."
        exit 1
    fi
fi

# Start API server
print_status "Starting DocTrove API server..."
cd doctrove-api
if [ "$BACKGROUND_MODE" = true ]; then
    # In background mode, redirect output to log file
    python api.py > ../api.log 2>&1 &
else
    # In foreground mode, show output
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
    if curl -s http://localhost:5001/api/health >/dev/null 2>&1; then
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
if ! check_port_available "8050" "frontend"; then
    if [ "$FORCE_START" = true ]; then
        print_status "Force flag detected. Attempting to start frontend anyway..."
    else
        print_error "Cannot start frontend. Port 8050 is already in use."
        exit 1
    fi
fi

# Start frontend
print_status "Starting DocScope frontend..."
if [ "$BACKGROUND_MODE" = true ]; then
    # In background mode, redirect output to log file
    python -m docscope.app > frontend.log 2>&1 &
else
    # In foreground mode, show output
    python -m docscope.app &
fi
FRONTEND_PID=$!

# Wait for frontend to start
print_status "Waiting for frontend to start..."
sleep 5

# Test frontend
print_status "Testing frontend..."
for i in {1..10}; do
    if curl -s http://localhost:8050/ >/dev/null 2>&1; then
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
echo -e "  API Server: ${BLUE}http://localhost:5001${NC}"
echo -e "  Frontend:   ${BLUE}http://localhost:8050${NC}"
if [ ! -z "$ENRICHMENT_PID" ]; then
    echo -e "  Enrichment: ${BLUE}Event-driven processing${NC}"
fi
echo ""
echo -e "${GREEN}Process IDs:${NC}"
if [ ! -z "$ENRICHMENT_PID" ]; then
    echo -e "  Enrichment: ${YELLOW}$ENRICHMENT_PID${NC}"
fi
echo -e "  API Server: ${YELLOW}$API_PID${NC}"
echo -e "  Frontend:   ${YELLOW}$FRONTEND_PID${NC}"
echo ""
echo -e "${GREEN}Log Files:${NC}"
if [ ! -z "$ENRICHMENT_PID" ]; then
    echo -e "  Enrichment: ${YELLOW}enrichment.log${NC}"
fi
echo -e "  API:        ${YELLOW}api.log${NC}"
echo -e "  Frontend:   ${YELLOW}frontend.log${NC}"
echo ""

if [ "$BACKGROUND_MODE" = true ]; then
    print_success "All services started in background mode"
    print_status "To stop services, run: ./stop_services.sh"
    print_status "To view logs, check the log files listed above"
else
    print_status "Press Ctrl+C to stop all services"
    print_status "Or run: ./stop_services.sh"
    
    # Keep script running and wait for interrupt (foreground mode only)
    wait
fi 