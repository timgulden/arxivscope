#!/bin/bash
# Independent Enrichment Service
# Runs enrichment processes independently of frontend restarts
# This service will NOT be affected by startup.sh --with-enrichment
#
# Usage:
#   ./scripts/start_independent_enrichment.sh                    # Start independent enrichment
#   ./scripts/start_independent_enrichment.sh --force            # Force restart
#   ./scripts/start_independent_enrichment.sh --stop             # Stop independent enrichment
#   ./scripts/start_independent_enrichment.sh --status           # Check status

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${CYAN}[HEADER]${NC} $1"
}

# Parse command line arguments
FORCE_START=false
STOP_ONLY=false
STATUS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_START=true
            shift
            ;;
        --stop)
            STOP_ONLY=true
            shift
            ;;
        --status)
            STATUS_ONLY=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            print_error "Usage: $0 [--force] [--stop] [--status]"
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

# Independent enrichment session names (different from startup.sh)
INDEPENDENT_1D_SESSION="independent_enrichment_1d"
INDEPENDENT_2D_SESSION="independent_embedding_2d"

# Function to check if a screen session exists
check_screen_session() {
    local session_name="$1"
    screen -list | grep -q "^.*\.$session_name" 2>/dev/null
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

# Function to show status
show_status() {
    print_header "Independent Enrichment Service Status"
    echo ""
    
    # Check 1D enrichment
    print_status "1D Enrichment (Independent):"
    if check_screen_session "$INDEPENDENT_1D_SESSION"; then
        print_success "  ✅ Screen session '$INDEPENDENT_1D_SESSION' is running"
        if check_process_running "event_listener_functional.py" >/dev/null; then
            print_success "  ✅ Process is active"
        else
            print_warning "  ⚠️  Screen session exists but process not running"
        fi
    else
        print_error "  ❌ Screen session '$INDEPENDENT_1D_SESSION' not found"
    fi
    
    echo ""
    
    # Check 2D enrichment
    print_status "2D Enrichment (Independent):"
    if check_screen_session "$INDEPENDENT_2D_SESSION"; then
        print_success "  ✅ Screen session '$INDEPENDENT_2D_SESSION' is running"
        if check_process_running "queue_2d_worker.py" >/dev/null; then
            print_success "  ✅ Process is active"
        else
            print_warning "  ⚠️  Screen session exists but process not running"
        fi
    else
        print_error "  ❌ Screen session '$INDEPENDENT_2D_SESSION' not found"
    fi
    
    echo ""
    
    # Check for conflicting sessions from startup.sh
    print_status "Conflicting Sessions (from startup.sh --with-enrichment):"
    if check_screen_session "enrichment_1d"; then
        print_warning "  ⚠️  Found 'enrichment_1d' session (from startup.sh)"
    else
        print_success "  ✅ No conflicting 'enrichment_1d' session"
    fi
    
    if check_screen_session "embedding_2d"; then
        print_warning "  ⚠️  Found 'embedding_2d' session (from startup.sh)"
    else
        print_success "  ✅ No conflicting 'embedding_2d' session"
    fi
    
    # Check for doctrove session (from startup.sh)
    if check_screen_session "doctrove"; then
        print_warning "  ⚠️  Found 'doctrove' session (from startup.sh)"
    else
        print_success "  ✅ No conflicting 'doctrove' session"
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

# Function to stop independent enrichment
stop_independent_enrichment() {
    print_status "Stopping independent enrichment service..."
    
    # Stop independent screen sessions
    if check_screen_session "$INDEPENDENT_1D_SESSION"; then
        print_status "Stopping independent 1D enrichment session..."
        screen -S "$INDEPENDENT_1D_SESSION" -X quit 2>/dev/null || true
    fi
    
    if check_screen_session "$INDEPENDENT_2D_SESSION"; then
        print_status "Stopping independent 2D enrichment session..."
        screen -S "$INDEPENDENT_2D_SESSION" -X quit 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    print_status "Killing any remaining independent enrichment processes..."
    pkill -f "event_listener_functional.py" 2>/dev/null || true
    pkill -f "queue_2d_worker.py" 2>/dev/null || true
    
    sleep 2
    print_success "Independent enrichment service stopped"
}

# Function to start independent enrichment
start_independent_enrichment() {
    print_header "Starting Independent Enrichment Service"
    print_status "This service runs independently and will NOT be affected by frontend restarts"
    echo ""
    
    # Start 1D enrichment
    if check_screen_session "$INDEPENDENT_1D_SESSION"; then
        if [ "$FORCE_START" = true ]; then
            print_status "Force flag detected. Stopping existing independent 1D enrichment session..."
            screen -S "$INDEPENDENT_1D_SESSION" -X quit 2>/dev/null || true
            sleep 2
        else
            print_warning "Independent 1D enrichment screen session '$INDEPENDENT_1D_SESSION' already exists"
            print_status "Use --force to restart or run: screen -r $INDEPENDENT_1D_SESSION"
        fi
    fi
    
    if ! check_screen_session "$INDEPENDENT_1D_SESSION"; then
        print_status "Starting independent 1D enrichment system..."
        screen -dmS "$INDEPENDENT_1D_SESSION" bash -c "cd $(pwd)/embedding-enrichment && source ../arxivscope/bin/activate && python event_listener_functional.py; exec bash"
        sleep 2
        
        if check_screen_session "$INDEPENDENT_1D_SESSION"; then
            print_success "Independent 1D enrichment started successfully"
        else
            print_error "Failed to start independent 1D enrichment"
            return 1
        fi
    fi
    
    # Start 2D enrichment
    if check_screen_session "$INDEPENDENT_2D_SESSION"; then
        if [ "$FORCE_START" = true ]; then
            print_status "Force flag detected. Stopping existing independent 2D enrichment session..."
            screen -S "$INDEPENDENT_2D_SESSION" -X quit 2>/dev/null || true
            sleep 2
        else
            print_warning "Independent 2D enrichment screen session '$INDEPENDENT_2D_SESSION' already exists"
            print_status "Use --force to restart or run: screen -r $INDEPENDENT_2D_SESSION"
        fi
    fi
    
    if ! check_screen_session "$INDEPENDENT_2D_SESSION"; then
        print_status "Starting independent 2D enrichment system..."
        screen -dmS "$INDEPENDENT_2D_SESSION" bash -c "cd $(pwd)/embedding-enrichment && source ../arxivscope/bin/activate && python queue_2d_worker.py; exec bash"
        sleep 2
        
        if check_screen_session "$INDEPENDENT_2D_SESSION"; then
            print_success "Independent 2D enrichment started successfully"
        else
            print_error "Failed to start independent 2D enrichment"
            return 1
        fi
    fi
    
    echo ""
    print_success "Independent enrichment service started successfully!"
    echo ""
    print_status "Screen sessions created:"
    print_status "  - $INDEPENDENT_1D_SESSION: Independent 1D embedding generation"
    print_status "  - $INDEPENDENT_2D_SESSION: Independent 2D embedding generation"
    echo ""
    print_status "To monitor enrichment processes:"
    print_status "  screen -r $INDEPENDENT_1D_SESSION    # View 1D enrichment logs"
    print_status "  screen -r $INDEPENDENT_2D_SESSION    # View 2D enrichment logs"
    print_status "  screen -list                         # List all screen sessions"
    echo ""
    print_status "To check status:"
    print_status "  $0 --status"
    echo ""
    print_status "To stop enrichment:"
    print_status "  $0 --stop"
    echo ""
    print_warning "IMPORTANT: This service is independent and will NOT be affected by:"
    print_warning "  - Frontend restarts"
    print_warning "  - startup.sh --with-enrichment"
    print_warning "  - API server restarts"
    echo ""
    print_status "These processes will continue running even if you disconnect from this session!"
}

# Main execution
if [ "$STOP_ONLY" = true ]; then
    stop_independent_enrichment
    exit 0
fi

if [ "$STATUS_ONLY" = true ]; then
    show_status
    exit 0
fi

# Start independent enrichment
start_independent_enrichment
