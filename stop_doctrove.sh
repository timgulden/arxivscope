#!/bin/bash
# Smart DocTrove Backend Service Shutdown Script
# Stops backend services (API + enrichment workers)
# Frontend services (React/Dash) are stopped separately
#
# Usage:
#   ./stop_doctrove.sh                # Stop API only
#   ./stop_doctrove.sh --enrichment   # Stop API + enrichment workers
#   ./stop_doctrove.sh --all          # Stop everything (API + enrichment)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
STOP_ENRICHMENT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --enrichment|--all)
            STOP_ENRICHMENT=true
            shift
            ;;
        --help)
            echo "DocTrove Backend Service Shutdown Script"
            echo ""
            echo "Usage:"
            echo "  $0                  # Stop API only"
            echo "  $0 --enrichment     # Stop API + enrichment workers"
            echo "  $0 --all            # Stop everything"
            echo ""
            echo "Backend Services:"
            echo "  - API Server"
            echo ""
            echo "Enrichment Workers:"
            echo "  - Vector Embeddings"
            echo "  - 2D Projections"
            echo "  - OpenAlex Details"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper function
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to safely kill a screen session
kill_screen() {
    local session_name=$1
    local service_name=$2
    
    if screen -list 2>/dev/null | grep -q "\\.$session_name"; then
        print_status "Stopping $service_name..."
        screen -S "$session_name" -X quit 2>/dev/null || true
        sleep 1
        print_success "$service_name stopped"
    else
        echo "  ℹ️  $service_name not running"
    fi
}

# Main execution
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}DocTrove Backend Service Shutdown${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Stop API
kill_screen "doctrove_api" "API Server"
echo ""

# Stop enrichment workers if requested
if [ "$STOP_ENRICHMENT" = true ]; then
    echo -e "${BLUE}Stopping Enrichment Workers${NC}"
    echo ""
    
    kill_screen "enrichment_embeddings" "Vector Embedding Worker"
    kill_screen "embedding_2d" "2D Projection Worker"
    kill_screen "openalex_details" "OpenAlex Details Worker"
    
    # Also kill any enrichment processes not in screen
    print_status "Checking for orphan enrichment processes..."
    pkill -f "event_listener_functional.py" 2>/dev/null && echo "  ✅ Stopped orphan vector embedding process" || true
    pkill -f "queue_2d_worker.py" 2>/dev/null && echo "  ✅ Stopped orphan 2D worker process" || true
    pkill -f "queue_openalex_details_worker.py" 2>/dev/null && echo "  ✅ Stopped orphan details worker process" || true
    
    echo ""
fi

# Also kill any API processes not in screen
print_status "Checking for orphan API processes..."
pkill -f "doctrove-api/api.py" 2>/dev/null && echo "  ✅ Stopped orphan API process" || true

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}Backend Services Stopped${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Show remaining screen sessions
echo "Remaining screen sessions:"
screen -ls 2>/dev/null | grep -v "^There" || echo "  (none)"
echo ""

if [ "$STOP_ENRICHMENT" = false ]; then
    echo -e "${YELLOW}Note: Enrichment workers still running${NC}"
    echo "  Use --enrichment or --all to stop them"
    echo ""
fi

print_success "Shutdown complete!"





