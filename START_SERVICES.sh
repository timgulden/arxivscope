#!/bin/bash
# Comprehensive Service Startup Script
# Starts API and React frontend in screen sessions that survive terminal restarts

set -e

echo "========================================="
echo "DocScope/DocTrove Service Startup"
echo "========================================="
echo ""

# Check if screen is installed
if ! command -v screen &> /dev/null; then
    echo "❌ ERROR: screen is not installed"
    echo "   Install with: sudo apt-get install screen"
    exit 1
fi

# Load environment variables
if [ -f ".env.local" ]; then
    echo "✅ Loading .env.local configuration"
    set -a
    source .env.local
    set +a
else
    echo "⚠️  WARNING: .env.local not found, using defaults"
fi

echo ""
echo "Starting services in screen sessions..."
echo "(Services will survive terminal/Cursor restarts)"
echo ""

# 1. Start API in screen
echo "1. Starting API Server (port ${DOCTROVE_API_PORT:-5001})..."
if screen -list | grep -q "doctrove_api"; then
    echo "   ⚠️  API screen session already exists"
    read -p "   Kill and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        screen -S doctrove_api -X quit 2>/dev/null || true
        sleep 2
    else
        echo "   Skipping API startup"
    fi
fi

if ! screen -list | grep -q "doctrove_api"; then
    cd /opt/arxivscope/doctrove-api
    screen -dmS doctrove_api /opt/arxivscope/arxivscope/bin/python api.py
    sleep 3
    
    # Verify API started
    if curl -s http://localhost:${DOCTROVE_API_PORT:-5001}/api/health | grep -q "healthy"; then
        echo "   ✅ API started successfully"
    else
        echo "   ❌ API may not have started correctly"
    fi
fi

echo ""

# 2. Start React Frontend in screen
echo "2. Starting React Frontend (port 8052)..."
if screen -list | grep -q "docscope_react"; then
    echo "   ⚠️  React screen session already exists"
    read -p "   Kill and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        screen -S docscope_react -X quit 2>/dev/null || true
        sleep 2
    else
        echo "   Skipping React startup"
    fi
fi

if ! screen -list | grep -q "docscope_react"; then
    cd /opt/arxivscope/docscope-platform/services/docscope/react
    screen -dmS docscope_react npm run dev
    sleep 10
    
    # Verify React started
    if lsof -i :8052 2>/dev/null | grep -q LISTEN; then
        echo "   ✅ React frontend started successfully"
    else
        echo "   ❌ React may not have started correctly"
    fi
fi

echo ""

# 3. Start OpenAlex Details Worker (optional but recommended)
echo "3. Starting OpenAlex Details Enrichment Worker..."
if screen -list | grep -q "openalex_details"; then
    echo "   ℹ️  OpenAlex details worker already running"
else
    cd /opt/arxivscope/embedding-enrichment
    screen -dmS openalex_details /opt/arxivscope/arxivscope/bin/python queue_openalex_details_worker.py --batch-size 1000 --sleep 5
    sleep 2
    echo "   ✅ OpenAlex details worker started"
fi

echo ""
echo "========================================="
echo "✅ Services Started"
echo "========================================="
echo ""
echo "Access points:"
echo "  - API:   http://localhost:${DOCTROVE_API_PORT:-5001}"
echo "  - React: http://localhost:8052"
echo ""
echo "Screen sessions:"
echo "  - API:     screen -r doctrove_api"
echo "  - React:   screen -r docscope_react"
echo "  - Workers: screen -r openalex_details  (enrichment)"
echo ""
echo "View all sessions: screen -ls"
echo "Detach from session: Ctrl+A then D"
echo "Stop services: ./STOP_SERVICES.sh"
echo "========================================="

