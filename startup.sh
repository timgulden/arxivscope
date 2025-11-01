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
#   ./startup.sh --restart          # Same as --force (more intuitive name)
#   ./startup.sh --with-enrichment --background --force  # Force restart in background
#   ./startup.sh --with-enrichment --background --restart  # Restart in background
#
# The enrichment system automatically processes papers for embeddings and 2D projections
# when new papers are ingested into the database.

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
        --force|--restart)
            FORCE_START=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            print_error "Usage: $0 [--with-enrichment] [--background] [--force|--restart]"
            exit 1
            ;;
    esac
done

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    print_status "Loaded local environment configuration from .env.local"
    # Use source instead of export to ensure variables persist
    set -a  # automatically export all variables
    source .env.local
    set +a  # turn off automatic export
else
    print_error "CRITICAL: .env.local file not found!"
    print_error "This file contains required configuration for ports, database, and API settings."
    print_error "Please create .env.local with the required configuration."
    exit 1
fi

# Validate required configuration - FAIL FAST if missing
print_status "Validating required configuration..."

# Check for required environment variables
MISSING_CONFIG=false

if [ -z "$DOCTROVE_API_PORT" ]; then
    print_error "CRITICAL: DOCTROVE_API_PORT is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ -z "$NEW_UI_PORT" ] && [ -z "$DOCSCOPE_PORT" ]; then
    print_error "CRITICAL: NEW_UI_PORT is not set in .env.local"
    print_error "  (Using NEW_UI_PORT for React frontend, DOCSCOPE_PORT is legacy)"
    MISSING_CONFIG=true
fi

if [ -z "$DOCTROVE_API_URL" ]; then
    print_error "CRITICAL: DOCTROVE_API_URL is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ -z "$DOC_TROVE_HOST" ]; then
    print_error "CRITICAL: DOC_TROVE_HOST is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ -z "$DOC_TROVE_PORT" ]; then
    print_error "CRITICAL: DOC_TROVE_PORT is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ -z "$DOC_TROVE_DB" ]; then
    print_error "CRITICAL: DOC_TROVE_DB is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ -z "$DOC_TROVE_USER" ]; then
    print_error "CRITICAL: DOC_TROVE_USER is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ -z "$DOC_TROVE_PASSWORD" ]; then
    print_error "CRITICAL: DOC_TROVE_PASSWORD is not set in .env.local"
    MISSING_CONFIG=true
fi

if [ "$MISSING_CONFIG" = true ]; then
    print_error "Configuration validation failed! Please fix the missing values in .env.local"
    print_error "Example .env.local structure:"
    print_error "  DOCTROVE_API_PORT=5001"
    print_error "  NEW_UI_PORT=3000  # React frontend"
    print_error "  DOCSCOPE_PORT=8050  # Legacy Dash (optional)"
    print_error "  DOCTROVE_API_URL=http://localhost:5001/api"
    print_error "  DOC_TROVE_HOST=localhost"
    print_error "  DOC_TROVE_PORT=5432"
    print_error "  DOC_TROVE_DB=doctrove"
    print_error "  DOC_TROVE_USER=doctrove_admin"
    print_error "  DOC_TROVE_PASSWORD=doctrove_admin"
    exit 1
fi

# Set ports from validated environment variables - NO FALLBACKS
API_PORT="${NEW_API_PORT:-${DOCTROVE_API_PORT:-5001}}"
FRONTEND_PORT="${NEW_UI_PORT:-${DOCSCOPE_PORT:-3000}}"

print_success "Configuration validation passed!"
print_status "Using ports - API: $API_PORT, Frontend: $FRONTEND_PORT"
print_status "API URL: $DOCTROVE_API_URL"
print_status "Database: $DOC_TROVE_HOST:$DOC_TROVE_PORT/$DOC_TROVE_DB (user: $DOC_TROVE_USER)"

# Function to check if a service is running
check_service_running() {
    local pattern="$1"
    local service_name="$2"
    
    # Use pgrep for more reliable process checking
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
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

# Function to detect if running in a remote session
is_remote_session() {
    # Check for SSH connection
    if [ ! -z "$SSH_CLIENT" ] || [ ! -z "$SSH_TTY" ]; then
        return 0  # True - remote session
    fi
    
    # Check for screen/tmux session (indicates remote work)
    if [ ! -z "$STY" ] || [ ! -z "$TMUX" ]; then
        return 0  # True - remote session
    fi
    
    # Check if we're in a remote terminal
    if [ "$TERM" = "screen" ]; then
        # Additional check for common remote scenarios
        if [ ! -z "$SSH_CONNECTION" ] || [ ! -z "$SSH_AUTH_SOCK" ]; then
            return 0  # True - remote session
        fi
    fi
    
    # Don't treat xterm-256color as remote - this is common in modern local terminals
    # Only treat as remote if we have SSH indicators
    
    return 1  # False - local session
}



# Function to handle existing processes
handle_existing_processes() {
    # Simple port-based checking instead of process checking
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
            print_error "Or run ./stop_services.sh first, then run this script again."
            exit 1
        fi
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    ENRICHMENT_PIDS=$(pgrep -f "event_listener.py" 2>/dev/null || true)
    if [ ! -z "$ENRICHMENT_PIDS" ]; then
        print_status "Stopping enrichment system (PIDs: $ENRICHMENT_PIDS)"
        echo "$ENRICHMENT_PIDS" | xargs kill 2>/dev/null || true
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

# Check if we should use screen for background mode in remote sessions
if [ "$BACKGROUND_MODE" = true ] && is_remote_session; then
    print_status "Detected remote session with background mode - using screen for persistent operation"
    
    # Check if screen is available
    if ! command -v screen >/dev/null 2>&1; then
        print_error "screen is not available. Please install screen or use regular background mode."
        exit 1
    fi
    
    # Check if session already exists
    if screen -list | grep -q "doctrove"; then
        if [ "$FORCE_START" = true ]; then
            print_status "Force flag detected. Stopping existing screen session..."
            screen -S "doctrove" -X quit 2>/dev/null || true
            sleep 2
        else
            print_warning "Screen session 'doctrove' already exists"
            print_status "Use --restart or --force to stop existing session and create new one"
            print_status "Or manually run: screen -r doctrove"
            exit 1
        fi
    fi
    
    # Create new screen session
    print_status "Creating screen session 'doctrove' for persistent background operation..."
    print_status "Services will continue running even if you disconnect from this session."
    echo ""
    
    # Create screen session with the startup command (without --background to avoid recursion)
    startup_cmd="./startup.sh"
    if [ "$WITH_ENRICHMENT" = true ]; then
        startup_cmd="$startup_cmd --with-enrichment"
    fi
    if [ "$FORCE_START" = true ]; then
        startup_cmd="$startup_cmd --force"
    fi
    
    screen -dmS "doctrove" bash -c "cd $(pwd) && source venv/bin/activate && $startup_cmd; exec bash"
    
    # Wait a moment for screen to start
    sleep 2
    
    # Check if screen session was created successfully
    if screen -list | grep -q "doctrove"; then
        print_success "Screen session 'doctrove' created successfully!"
        print_status "Services are now running in the background and will survive disconnection."
        echo ""
        print_status "To attach to the screen session and see logs:"
        print_status "  screen -r doctrove"
        print_status ""
        print_status "To detach from screen session (services keep running):"
        print_status "  Press Ctrl+A, then D"
        print_status ""
        print_status "To stop services:"
        print_status "  ./stop_services.sh"
        echo ""
        print_status "Automatically attaching to screen session to show startup progress..."
        sleep 2
        screen -r "doctrove"
    else
        print_error "Failed to create screen session"
        exit 1
    fi
    exit 0
fi

# Check for existing processes and handle them
handle_existing_processes

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    elif [ -d "arxivscope" ]; then
        print_warning "Found legacy 'arxivscope' virtual environment. Consider migrating to 'venv'."
        print_status "Activating virtual environment..."
        source arxivscope/bin/activate
    else
        print_error "Virtual environment directory 'venv' not found. Please create it with 'python -m venv venv' and install dependencies."
        exit 1
    fi
fi

# Check database connectivity
print_status "Checking database connectivity..."
if command -v psql >/dev/null 2>&1; then
    # Load environment variables from .env file if it exists
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Use environment variables or fall back to defaults
    DB_HOST=${DOC_TROVE_HOST:-localhost}
    DB_PORT=${DOC_TROVE_PORT:-5432}
    DB_USER=${DOC_TROVE_USER:-tgulden}
    DB_PASSWORD=${DOC_TROVE_PASSWORD:-}
    DB_NAME=${DOC_TROVE_DB:-doctrove}
    
    # Try connection with environment variables
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connected successfully"
    else
        print_error "Failed to connect to database"
        print_error "Please check your database configuration in .env.local"
        print_error "Host: $DB_HOST, Port: $DB_PORT, User: $DB_USER, Database: $DB_NAME"
        exit 1
    fi
else
    print_warning "psql not available, skipping database connectivity check"
fi

# Check if event-driven enrichment should be started
if [ "$WITH_ENRICHMENT" = true ]; then
    print_status "Starting event-driven enrichment systems..."
    cd embedding-enrichment
    
    # Start enrichment event listener (1D embeddings)
    print_status "Starting enrichment event listener (1D embeddings)..."
    if [ "$BACKGROUND_MODE" = true ]; then
        # In background mode, redirect output to log file
        python event_listener.py > ../enrichment_1d.log 2>&1 &
    else
        # In foreground mode, show output
        python event_listener.py &
    fi
    ENRICHMENT_1D_PID=$!
    
    # Note: 2D enrichment is handled by the event listener automatically
    # No separate 2D worker needed with current architecture
    ENRICHMENT_2D_PID=""
    
    cd ..
    
    # Wait for enrichment systems to start
    print_status "Waiting for enrichment systems to start..."
    sleep 3
    
    # Check if 1D enrichment process is running
    if kill -0 $ENRICHMENT_1D_PID 2>/dev/null; then
        print_success "1D enrichment system started (PID: $ENRICHMENT_1D_PID)"
    else
        print_error "1D enrichment system failed to start"
        if [ "$BACKGROUND_MODE" = true ]; then
            print_error "Check enrichment_1d.log for details"
        fi
        exit 1
    fi
    
    # Note: 2D enrichment is handled automatically by the event listener
    print_success "Enrichment event listener started (handles both 1D embeddings and 2D projections)"
else
    print_status "Skipping event-driven enrichment systems (use --with-enrichment to enable)"
    ENRICHMENT_1D_PID=""
    ENRICHMENT_2D_PID=""
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

print_status "Starting frontend..."
# Check if React frontend exists
REACT_DIR="docscope-platform/services/docscope/react"
if [ -d "$REACT_DIR" ]; then
    print_status "Starting React frontend (port $FRONTEND_PORT)..."
    cd "$REACT_DIR"
    # Load .env.local if it exists
    if [ -f "../../../.env.local" ]; then
        set -a
        source ../../../.env.local
        set +a
    fi
    export VITE_API_BASE_URL="${NEW_API_BASE_URL:-http://localhost:$API_PORT}"
    if [ "$BACKGROUND_MODE" = true ]; then
        npm run dev > ../../../frontend.log 2>&1 &
    else
        npm run dev &
    fi
    FRONTEND_PID=$!
    cd ../../..
else
    print_warning "React frontend not found at $REACT_DIR, starting legacy Dash frontend..."
    # Ensure the API URL is set correctly for the frontend (honor pre-set value)
    if [ -z "$DOCTROVE_API_URL" ]; then
        export DOCTROVE_API_URL="http://localhost:$API_PORT/api"
    fi
    if [ "$BACKGROUND_MODE" = true ]; then
        # In background mode, redirect output to log file
        python -m docscope.app > frontend.log 2>&1 &
    else
        # In foreground mode, show output
        python -m docscope.app &
    fi
    FRONTEND_PID=$!
    # Note: Legacy Dash runs on port 8050, but we're using FRONTEND_PORT variable
    print_warning "Legacy Dash frontend starting on default port 8050 (may differ from configured $FRONTEND_PORT)"
fi

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
    if [ ! -z "$ENRICHMENT_1D_PID" ]; then
        echo -e "  Enrichment: ${BLUE}Event-driven processing${NC}"
    fi
echo ""
echo -e "${GREEN}Process IDs:${NC}"
if [ ! -z "$ENRICHMENT_1D_PID" ]; then
    echo -e "  Enrichment: ${YELLOW}$ENRICHMENT_1D_PID${NC}"
fi
echo -e "  API Server: ${YELLOW}$API_PID${NC}"
echo -e "  Frontend:   ${YELLOW}$FRONTEND_PID${NC}"
echo ""
echo -e "${GREEN}Log Files:${NC}"
if [ ! -z "$ENRICHMENT_1D_PID" ]; then
    echo -e "  Enrichment: ${YELLOW}enrichment_1d.log${NC}"
fi
echo -e "  API:        ${YELLOW}api.log${NC}"
echo -e "  Frontend:   ${YELLOW}frontend.log${NC}"
echo ""

if [ "$BACKGROUND_MODE" = true ]; then
    print_success "All services started in background mode"
    print_status "To stop services, run: ./stop_services.sh"
    print_status "To view logs, check the log files listed above"
    
    # Add screen information if this is a remote session
    if is_remote_session; then
        echo ""
        print_warning "Note: You are in a remote session. Services may stop if you disconnect."
        print_status "For persistent operation, use: ./startup.sh --with-enrichment --background"
        print_status "This will automatically create a screen session that survives disconnection."
    fi
else
    print_status "Press Ctrl+C to stop all services"
    print_status "Or run: ./stop_services.sh"
    
    # Keep script running and wait for interrupt (foreground mode only)
    wait
fi 