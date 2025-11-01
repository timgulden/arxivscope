#!/bin/bash
# Robust Enrichment Startup Script
# Ensures both 1D and 2D enrichment processes are running and can survive frontend restarts
#
# Usage:
#   ./scripts/start_enrichment_robust.sh                    # Start enrichment in screen sessions
#   ./scripts/start_enrichment_robust.sh --force            # Force restart existing processes
#   ./scripts/start_enrichment_robust.sh --check            # Check status only
#   ./scripts/start_enrichment_robust.sh --stop             # Stop all enrichment processes

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
FORCE_START=false
CHECK_ONLY=false
STOP_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_START=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --stop)
            STOP_ONLY=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            print_error "Usage: $0 [--force] [--check] [--stop]"
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

# Check if we're in the right directory
if [ ! -f "doctrove-api/api.py" ] || [ ! -d "embedding-enrichment" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Function to check if a screen session exists
check_screen_session() {
    local session_name="$1"
    screen -list | grep -q "$session_name" 2>/dev/null
}

# Function to check if a process is running
check_process_running() {
    local pattern="$1"
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ ! -z "$pids" ]; then
        echo "$pids"
        return 0
    else
        return 1
    fi
}

# Function to start 1D enrichment in screen session
start_1d_enrichment() {
    local session_name="enrichment_1d"
    
    if check_screen_session "$session_name"; then
        if [ "$FORCE_START" = true ]; then
            print_status "Force flag detected. Stopping existing 1D enrichment session..."
            screen -S "$session_name" -X quit 2>/dev/null || true
            sleep 2
        else
            print_warning "1D enrichment screen session '$session_name' already exists"
            print_status "Use --force to restart or run: screen -r $session_name"
            return 0
        fi
    fi
    
    print_status "Starting 1D enrichment system in screen session '$session_name'..."
    
    # Create screen session for 1D enrichment
    screen -dmS "$session_name" bash -c "cd $(pwd)/embedding-enrichment && source ../arxivscope/bin/activate && python event_listener_functional.py; exec bash"
    
    # Wait for screen to start
    sleep 2
    
    if check_screen_session "$session_name"; then
        print_success "1D enrichment screen session '$session_name' created successfully!"
        return 0
    else
        print_error "Failed to create 1D enrichment screen session"
        return 1
    fi
}

# Function to start 2D enrichment in screen session
start_2d_enrichment() {
    local session_name="embedding_2d"
    
    if check_screen_session "$session_name"; then
        if [ "$FORCE_START" = true ]; then
            print_status "Force flag detected. Stopping existing 2D enrichment session..."
            screen -S "$session_name" -X quit 2>/dev/null || true
            sleep 2
        else
            print_warning "2D enrichment screen session '$session_name' already exists"
            print_status "Use --force to restart or run: screen -r $session_name"
            return 0
        fi
    fi
    
    print_status "Starting 2D enrichment system in screen session '$session_name'..."
    
    # Create screen session for 2D enrichment
    screen -dmS "$session_name" bash -c "cd $(pwd)/embedding-enrichment && source ../arxivscope/bin/activate && python queue_2d_worker.py; exec bash"
    
    # Wait for screen to start
    sleep 2
    
    if check_screen_session "$session_name"; then
        print_success "2D enrichment screen session '$session_name' created successfully!"
        return 0
    else
        print_error "Failed to create 2D enrichment screen session"
        return 1
    fi
}

# Function to check enrichment status
check_enrichment_status() {
    print_status "Checking enrichment system status..."
    echo ""
    
    # Check 1D enrichment
    print_status "1D Enrichment (event_listener_functional.py):"
    if check_screen_session "enrichment_1d"; then
        print_success "  ✅ Screen session 'enrichment_1d' is running"
        if check_process_running "event_listener_functional.py" >/dev/null; then
            print_success "  ✅ Process is active"
        else
            print_warning "  ⚠️  Screen session exists but process not running"
        fi
    else
        print_error "  ❌ Screen session 'enrichment_1d' not found"
    fi
    
    echo ""
    
    # Check 2D enrichment
    print_status "2D Enrichment (queue_2d_worker.py):"
    if check_screen_session "embedding_2d"; then
        print_success "  ✅ Screen session 'embedding_2d' is running"
        if check_process_running "queue_2d_worker.py" >/dev/null; then
            print_success "  ✅ Process is active"
        else
            print_warning "  ⚠️  Screen session exists but process not running"
        fi
    else
        print_error "  ❌ Screen session 'embedding_2d' not found"
    fi
    
    echo ""
    
    # Check database connectivity
    print_status "Database connectivity:"
    if command -v psql >/dev/null 2>&1; then
        if PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "  ✅ Database connection successful"
        else
            print_error "  ❌ Database connection failed"
        fi
    else
        print_warning "  ⚠️  psql not available, cannot test database connection"
    fi
    
    echo ""
    
    # Show embedding progress
    print_status "Embedding progress:"
    if command -v psql >/dev/null 2>&1; then
        PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
            SELECT 
                COUNT(*) as total_papers,
                COUNT(doctrove_embedding) as papers_with_1d_embeddings,
                COUNT(doctrove_embedding_2d) as papers_with_2d_embeddings,
                ROUND(COUNT(doctrove_embedding)::numeric / COUNT(*) * 100, 2) as embedding_1d_percentage,
                ROUND(COUNT(doctrove_embedding_2d)::numeric / COUNT(*) * 100, 2) as embedding_2d_percentage
            FROM doctrove_papers;
        " 2>/dev/null || print_warning "  ⚠️  Could not query embedding progress"
    fi
}

# Function to stop all enrichment processes
stop_enrichment_processes() {
    print_status "Stopping all enrichment processes..."
    
    # Stop screen sessions
    if check_screen_session "enrichment_1d"; then
        print_status "Stopping 1D enrichment screen session..."
        screen -S "enrichment_1d" -X quit 2>/dev/null || true
    fi
    
    if check_screen_session "embedding_2d"; then
        print_status "Stopping 2D enrichment screen session..."
        screen -S "embedding_2d" -X quit 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    print_status "Killing any remaining enrichment processes..."
    pkill -f "event_listener_functional.py" 2>/dev/null || true
    pkill -f "queue_2d_worker.py" 2>/dev/null || true
    pkill -f "embedding_service.py" 2>/dev/null || true
    
    sleep 2
    print_success "All enrichment processes stopped"
}

# Main execution
if [ "$STOP_ONLY" = true ]; then
    stop_enrichment_processes
    exit 0
fi

if [ "$CHECK_ONLY" = true ]; then
    check_enrichment_status
    exit 0
fi

# Start enrichment processes
print_status "Starting robust enrichment system..."
echo ""

# Start 1D enrichment
if start_1d_enrichment; then
    print_success "1D enrichment started successfully"
else
    print_error "Failed to start 1D enrichment"
    exit 1
fi

# Start 2D enrichment
if start_2d_enrichment; then
    print_success "2D enrichment started successfully"
else
    print_error "Failed to start 2D enrichment"
    exit 1
fi

echo ""
print_success "Robust enrichment system started successfully!"
echo ""
print_status "Screen sessions created:"
print_status "  - enrichment_1d: 1D embedding generation"
print_status "  - embedding_2d:  2D embedding generation"
echo ""
print_status "To monitor enrichment processes:"
print_status "  screen -r enrichment_1d    # View 1D enrichment logs"
print_status "  screen -r embedding_2d     # View 2D enrichment logs"
print_status "  screen -list               # List all screen sessions"
echo ""
print_status "To check status:"
print_status "  $0 --check"
echo ""
print_status "To stop enrichment:"
print_status "  $0 --stop"
echo ""
print_status "These processes will continue running even if you disconnect from this session!"









