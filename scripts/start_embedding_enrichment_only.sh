#!/bin/bash
# Start Only Vector Embedding Enrichment
# Simple script to start just the vector embedding enrichment process
#
# Usage:
#   ./scripts/start_embedding_enrichment_only.sh                    # Start embedding enrichment
#   ./scripts/start_embedding_enrichment_only.sh --force            # Force restart
#   ./scripts/start_embedding_enrichment_only.sh --stop             # Stop embedding enrichment
#   ./scripts/start_embedding_enrichment_only.sh --status           # Check status

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

# Vector embedding enrichment session name
ENRICHMENT_SESSION="enrichment_embeddings"

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
    print_status "Vector Embedding Enrichment Status"
    echo ""
    
    # Check embedding enrichment
    print_status "Vector Embedding Enrichment (event_listener_functional.py):"
    if check_screen_session "$ENRICHMENT_SESSION"; then
        print_success "  ✅ Screen session '$ENRICHMENT_SESSION' is running"
        if check_process_running "event_listener_functional.py" >/dev/null; then
            print_success "  ✅ Process is active"
        else
            print_warning "  ⚠️  Screen session exists but process not running"
        fi
    else
        print_error "  ❌ Screen session '$ENRICHMENT_SESSION' not found"
    fi
    
    echo ""
    
    # Show embedding progress
    print_status "Embedding progress:"
    if command -v psql >/dev/null 2>&1; then
        PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
            SELECT 
                COUNT(*) as total_papers,
                COUNT(doctrove_embedding) as papers_with_embeddings,
                ROUND(COUNT(doctrove_embedding)::numeric / COUNT(*) * 100, 2) as embedding_percentage
            FROM doctrove_papers;
        " 2>/dev/null || print_warning "  ⚠️  Could not query embedding progress"
    fi
}

# Function to stop embedding enrichment
stop_embedding_enrichment() {
    print_status "Stopping vector embedding enrichment..."
    
    # Stop screen session
    if check_screen_session "$ENRICHMENT_SESSION"; then
        print_status "Stopping embedding enrichment screen session..."
        screen -S "$ENRICHMENT_SESSION" -X quit 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    print_status "Killing any remaining enrichment processes..."
    pkill -f "event_listener_functional.py" 2>/dev/null || true
    
    sleep 2
    print_success "Embedding enrichment stopped"
}

# Function to start embedding enrichment
start_embedding_enrichment() {
    print_status "Starting vector embedding enrichment system..."
    
    # Start embedding enrichment
    if check_screen_session "$ENRICHMENT_SESSION"; then
        if [ "$FORCE_START" = true ]; then
            print_status "Force flag detected. Stopping existing enrichment session..."
            screen -S "$ENRICHMENT_SESSION" -X quit 2>/dev/null || true
            sleep 2
        else
            print_warning "Embedding enrichment screen session '$ENRICHMENT_SESSION' already exists"
            print_status "Use --force to restart or run: screen -r $ENRICHMENT_SESSION"
            return 0
        fi
    fi
    
    if ! check_screen_session "$ENRICHMENT_SESSION"; then
        print_status "Starting embedding enrichment system in screen session '$ENRICHMENT_SESSION'..."
        screen -dmS "$ENRICHMENT_SESSION" bash -c "cd $(pwd)/embedding-enrichment && source ../arxivscope/bin/activate && python event_listener_functional.py; exec bash"
        sleep 2
        
        if check_screen_session "$ENRICHMENT_SESSION"; then
            print_success "Embedding enrichment started successfully"
        else
            print_error "Failed to start embedding enrichment"
            return 1
        fi
    fi
    
    echo ""
    print_success "Vector embedding enrichment service started successfully!"
    echo ""
    print_status "Screen session created:"
    print_status "  - $ENRICHMENT_SESSION: Vector embedding generation"
    echo ""
    print_status "To monitor enrichment:"
    print_status "  screen -r $ENRICHMENT_SESSION    # View enrichment logs"
    print_status "  screen -list                      # List all screen sessions"
    echo ""
    print_status "To check status:"
    print_status "  $0 --status"
    echo ""
    print_status "To stop enrichment:"
    print_status "  $0 --stop"
    echo ""
    print_status "This process will continue running even if you disconnect from this session!"
}

# Main execution
if [ "$STOP_ONLY" = true ]; then
    stop_embedding_enrichment
    exit 0
fi

if [ "$STATUS_ONLY" = true ]; then
    show_status
    exit 0
fi

# Start embedding enrichment
start_embedding_enrichment









