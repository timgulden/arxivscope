#!/bin/bash
# Smart DocTrove Backend Service Startup Script
# Intelligently starts backend services (API + enrichment) only if not running
# Frontend services (React/Dash) are started separately
#
# Usage:
#   ./start_doctrove.sh                    # Start API only
#   ./start_doctrove.sh --restart          # Kill and restart API
#   ./start_doctrove.sh --enrichment       # Start API + enrichment workers
#   ./start_doctrove.sh --restart --enrichment  # Restart all backend services
#   ./start_doctrove.sh --help             # Show this help

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
RESTART=false
ENRICHMENT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --restart)
            RESTART=true
            shift
            ;;
        --enrichment)
            ENRICHMENT=true
            shift
            ;;
        --help)
            echo "DocTrove Backend Service Startup Script"
            echo ""
            echo "Usage:"
            echo "  $0                      # Start API if not running"
            echo "  $0 --restart           # Kill and restart API"
            echo "  $0 --enrichment        # Start API + enrichment workers"
            echo "  $0 --restart --enrichment"
            echo ""
            echo "Backend Services:"
            echo "  - API Server (port 5001)"
            echo ""
            echo "Enrichment Workers (with --enrichment flag):"
            echo "  - Vector Embeddings (1536-d semantic embeddings)"
            echo "  - 2D Projections (UMAP visualizations)"
            echo ""
            echo "Frontend Services (started separately):"
            echo "  - React:  cd docscope-platform/services/docscope/react && npm run dev"
            echo "  - Dash:   ./start_docscope.sh"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
}

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

# Check if screen session exists
check_screen() {
    local session_name=$1
    screen -list 2>/dev/null | grep -q "\\.$session_name" 2>/dev/null
}

# Stop a screen session
stop_screen() {
    local session_name=$1
    if check_screen "$session_name"; then
        screen -S "$session_name" -X quit 2>/dev/null || true
        sleep 1
    fi
}

# Start a service if not running
start_service() {
    local session_name=$1
    local service_name=$2
    local start_command=$3
    local verify_command=$4
    local working_dir=${5:-.}
    
    if check_screen "$session_name"; then
        if [ "$RESTART" = true ]; then
            print_status "Restarting $service_name..."
            stop_screen "$session_name"
        else
            print_success "$service_name already running"
            return 0
        fi
    fi
    
    print_status "Starting $service_name..."
    (cd "$working_dir" && screen -dmS "$session_name" bash -c "$start_command")
    sleep 3
    
    # Verify service started
    if eval "$verify_command"; then
        print_success "$service_name started successfully"
        return 0
    else
        print_error "$service_name may not have started correctly"
        return 1
    fi
}

# Main execution
print_header "DocTrove Service Startup"

# Check if screen is installed
if ! command -v screen &> /dev/null; then
    print_error "screen is not installed"
    echo "   macOS: brew install screen"
    echo "   Linux: sudo apt-get install screen"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at ${VENV_DIR}"
    echo "   Create it with: python -m venv venv"
    exit 1
fi

# Load environment variables
if [ -f ".env.local" ]; then
    print_status "Loading .env.local configuration"
    set -a
    source .env.local
    set +a
else
    print_warning ".env.local not found, using defaults"
fi

echo ""
if [ "$RESTART" = true ]; then
    print_status "Mode: RESTART (killing existing services)"
else
    print_status "Mode: SMART (only starting services that aren't running)"
fi

if [ "$ENRICHMENT" = true ]; then
    print_status "Enrichment: ENABLED (will start enrichment workers)"
else
    print_status "Enrichment: DISABLED (use --enrichment to enable)"
fi
echo ""

# Determine script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
API_DIR="${SCRIPT_DIR}/doctrove-api"
ENRICH_DIR="${SCRIPT_DIR}/embedding-enrichment"

# 1. Start API Server
start_service "doctrove_api" \
    "API Server (port ${NEW_API_PORT:-${DOCTROVE_API_PORT:-5001}})" \
    "source ${VENV_DIR}/bin/activate && python api.py" \
    "curl -s http://localhost:${NEW_API_PORT:-${DOCTROVE_API_PORT:-5001}}/api/health | grep -q 'healthy'" \
    "$API_DIR"

echo ""

# 2. Start Enrichment Workers (if --enrichment flag set)
if [ "$ENRICHMENT" = true ]; then
    print_header "Starting Enrichment Workers"
    
    # 2a. Vector Embedding Worker
    start_service "enrichment_embeddings" \
        "Vector Embedding Enrichment" \
        "source ${VENV_DIR}/bin/activate && python event_listener.py" \
        "check_screen enrichment_embeddings" \
        "$ENRICH_DIR"
    
    echo ""
    
    # 2b. 2D Projection Worker
    start_service "embedding_2d" \
        "2D Projection Enrichment" \
        "source ${VENV_DIR}/bin/activate && python queue_2d_worker.py --batch-size 1000 --sleep 5" \
        "check_screen embedding_2d" \
        "$ENRICH_DIR"
    
    echo ""
    
    # 2c. OpenAlex Details Worker - REMOVED (Oct 2025)
    # OpenAlex data removed during system refocus migration
    # This worker is no longer needed
    
    echo ""
fi

# Summary
print_header "Startup Complete"

echo "Running backend services:"
screen -ls 2>/dev/null | grep -E "doctrove_api|enrichment|embedding" || echo "  (none)"
echo ""

echo "Backend access:"
echo "  - API:   http://localhost:${NEW_API_PORT:-${DOCTROVE_API_PORT:-5001}}/api/health"
echo ""

if [ "$ENRICHMENT" = true ]; then
    echo "Enrichment workers started:"
    echo "  - Vector embeddings: screen -r enrichment_embeddings"
    echo "  - 2D projections:    screen -r embedding_2d"
    echo ""
fi

echo "Frontend (start separately):"
echo "  - React:  cd docscope-platform/services/docscope/react && npm run dev"
echo "  - Dash:   ./start_docscope.sh"
echo ""

echo "Useful commands:"
echo "  View logs:     screen -r <session_name>"
echo "  List all:      screen -ls"
echo "  Detach:        Ctrl+A then D"
echo "  Stop backend:  ./stop_doctrove.sh  (if exists)"
echo ""

print_success "Backend services started!"

