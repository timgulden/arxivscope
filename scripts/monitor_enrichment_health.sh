#!/bin/bash
# Enrichment Health Monitoring Script
# Monitors the health and progress of enrichment processes
#
# Usage:
#   ./scripts/monitor_enrichment_health.sh                    # Show current status
#   ./scripts/monitor_enrichment_health.sh --watch            # Watch mode (refresh every 30s)
#   ./scripts/monitor_enrichment_health.sh --detailed         # Show detailed logs

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
WATCH_MODE=false
DETAILED_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --detailed)
            DETAILED_MODE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            print_error "Usage: $0 [--watch] [--detailed]"
            exit 1
            ;;
    esac
done

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    set -a  # automatically export all variables
    source .env.local
    set +a  # turn off automatic export
else
    print_error "CRITICAL: .env.local file not found!"
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

# Function to get screen session output
get_screen_output() {
    local session_name="$1"
    local output_file="/tmp/screen_${session_name}_output.txt"
    screen -S "$session_name" -X hardcopy "$output_file" 2>/dev/null
    if [ -f "$output_file" ]; then
        cat "$output_file"
        rm -f "$output_file"
    else
        echo "No output available"
    fi
}

# Function to show enrichment status
show_enrichment_status() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    print_header "Enrichment Health Monitor - $timestamp"
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
    
    echo ""
    
    # Show recent activity if detailed mode
    if [ "$DETAILED_MODE" = true ]; then
        print_status "Recent 1D enrichment activity:"
        echo "  $(get_screen_output 'enrichment_1d' | tail -5)"
        echo ""
        
        print_status "Recent 2D enrichment activity:"
        echo "  $(get_screen_output 'embedding_2d' | tail -5)"
        echo ""
    fi
    
    # Show system resources
    print_status "System resources:"
    echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "  Memory: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
    echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
}

# Function to watch mode
watch_mode() {
    while true; do
        clear
        show_enrichment_status
        echo ""
        print_status "Press Ctrl+C to stop watching..."
        sleep 30
    done
}

# Main execution
if [ "$WATCH_MODE" = true ]; then
    watch_mode
else
    show_enrichment_status
fi









