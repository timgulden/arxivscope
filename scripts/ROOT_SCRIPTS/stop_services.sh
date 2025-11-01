#!/bin/bash
# DocScope/DocTrove Stop Script
# Gracefully stops all running services

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

print_status "Stopping DocScope/DocTrove services..."

# Function to stop processes by pattern
stop_processes() {
    local pattern="$1"
    local service_name="$2"
    
    local pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        print_status "Found $service_name processes: $pids"
        for pid in $pids; do
            print_status "Stopping $service_name (PID: $pid)"
            kill $pid 2>/dev/null || true
        done
        print_success "$service_name stopped"
        return 0
    else
        print_warning "No $service_name processes found"
        return 1
    fi
}

# Stop API server (multiple possible patterns)
API_STOPPED=false
stop_processes "python.*api.py" "API server" && API_STOPPED=true
stop_processes "python.*doctrove-api/api.py" "API server" && API_STOPPED=true
stop_processes "python.*api.py" "API server" && API_STOPPED=true

# Stop enrichment systems (multiple possible patterns)
ENRICHMENT_STOPPED=false
stop_processes "python.*event_listener_functional.py" "1D enrichment system" && ENRICHMENT_STOPPED=true
stop_processes "python.*embedding-enrichment/event_listener_functional.py" "1D enrichment system" && ENRICHMENT_STOPPED=true
stop_processes "python.*event_listener_2d.py" "2D enrichment system" && ENRICHMENT_STOPPED=true
stop_processes "python.*embedding-enrichment/event_listener_2d.py" "2D enrichment system" && ENRICHMENT_STOPPED=true

# Stop frontend (multiple possible patterns)
FRONTEND_STOPPED=false
# React frontend (Vite)
stop_processes "vite" "React frontend" && FRONTEND_STOPPED=true
stop_processes "npm.*dev" "React frontend" && FRONTEND_STOPPED=true
# Legacy Dash frontend
stop_processes "python.*-m docscope.app" "Dash frontend" && FRONTEND_STOPPED=true
stop_processes "python.*docscope/app.py" "Dash frontend" && FRONTEND_STOPPED=true
stop_processes "python.*-m docscope" "Dash frontend" && FRONTEND_STOPPED=true

# Stop any other potential DocScope/DocTrove processes
stop_processes "python.*main.py" "main processes"
stop_processes "python.*ingestor.py" "ingestion processes"
stop_processes "python.*enrichment" "enrichment processes"
stop_processes "python.*functional_2d_processor" "functional 2D processor"
stop_processes "python.*embedding_service" "embedding service"
stop_processes "python.*docscope.py" "docscope processes"

# Wait a moment for processes to terminate
sleep 2

# Check if any processes are still running
REMAINING_API=$(ps aux | grep -E "(python.*api\.py|python.*doctrove-api)" | grep -v grep | wc -l)
REMAINING_ENRICHMENT=$(ps aux | grep -E "(python.*event_listener_functional\.py|python.*event_listener_2d\.py|python.*embedding-enrichment)" | grep -v grep | wc -l)
REMAINING_FRONTEND=$(ps aux | grep -E "(vite|npm.*dev|python.*-m docscope|python.*docscope/app\.py)" | grep -v grep | wc -l)
REMAINING_OTHER=$(ps aux | grep -E "(python.*main\.py|python.*ingestor\.py|python.*enrichment|python.*docscope\.py)" | grep -v grep | wc -l)

if [ $REMAINING_API -eq 0 ] && [ $REMAINING_ENRICHMENT -eq 0 ] && [ $REMAINING_FRONTEND -eq 0 ] && [ $REMAINING_OTHER -eq 0 ]; then
    print_success "All services stopped successfully"
else
    print_warning "Some processes may still be running"
    if [ $REMAINING_API -gt 0 ]; then
        print_warning "API processes still running: $REMAINING_API"
    fi
    if [ $REMAINING_ENRICHMENT -gt 0 ]; then
        print_warning "Enrichment processes (1D/2D) still running: $REMAINING_ENRICHMENT"
    fi
    if [ $REMAINING_FRONTEND -gt 0 ]; then
        print_warning "Frontend processes still running: $REMAINING_FRONTEND"
    fi
    if [ $REMAINING_OTHER -gt 0 ]; then
        print_warning "Other DocScope/DocTrove processes still running: $REMAINING_OTHER"
    fi
fi

# Check if ports are still in use
if command -v lsof >/dev/null 2>&1; then
    PORT_5001=$(lsof -i :5001 2>/dev/null | wc -l)
    PORT_3000=$(lsof -i :3000 2>/dev/null | wc -l)
    PORT_8050=$(lsof -i :8050 2>/dev/null | wc -l)
    
    if [ $PORT_5001 -eq 0 ] && [ $PORT_3000 -eq 0 ] && [ $PORT_8050 -eq 0 ]; then
        print_success "All ports are now free"
    else
        print_warning "Some ports may still be in use:"
        if [ $PORT_5001 -gt 0 ]; then
            print_warning "Port 5001 (API) still in use"
        fi
        if [ $PORT_3000 -gt 0 ]; then
            print_warning "Port 3000 (React Frontend) still in use"
        fi
        if [ $PORT_8050 -gt 0 ]; then
            print_warning "Port 8050 (Legacy Dash Frontend) still in use"
        fi
    fi
fi

print_status "Stop script completed" 