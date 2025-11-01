#!/bin/bash

# Unified frontend (React) manager
# Usage:
#   ./docscope.sh start|stop|restart|status

set -e

SESSION_NAME="docscope_react"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REACT_DIR="${SCRIPT_DIR}/docscope-platform/services/docscope/react"
START_CMD="npm run dev"
PORT="${NEW_UI_PORT:-3000}"

print() { echo -e "$1"; }

ensure_screen() {
    if ! command -v screen >/dev/null 2>&1; then
        print "❌ screen not installed."
        print "   macOS: brew install screen"
        print "   Linux: sudo apt-get install screen"
        exit 1
    fi
}

check_port() {
    local port=$1
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        lsof -i :${port} >/dev/null 2>&1
    else
        # Linux
        ss -tlnp 2>/dev/null | grep -q ":${port}" || lsof -i :${port} >/dev/null 2>&1
    fi
}

start_react() {
    ensure_screen
    if [ ! -d "$REACT_DIR" ]; then
        print "❌ React directory not found at ${REACT_DIR}"
        print "   Expected React frontend at: docscope-platform/services/docscope/react"
        exit 1
    fi
    if screen -list 2>/dev/null | grep -q "\.${SESSION_NAME}"; then
        print "ℹ️  React already running in screen (${SESSION_NAME})"
        return 0
    fi
    cd "$REACT_DIR"
    # Load .env.local if it exists (from project root)
    if [ -f "${SCRIPT_DIR}/.env.local" ]; then
        # Source the file and export variables (handles comments and empty lines)
        set -a
        source "${SCRIPT_DIR}/.env.local"
        set +a
    fi
    # Set API URL (default to localhost for local setup)
    export VITE_API_BASE_URL="${NEW_API_BASE_URL:-http://localhost:5001}"
    screen -dmS "$SESSION_NAME" bash -c "export VITE_API_BASE_URL='${VITE_API_BASE_URL}' && $START_CMD"
    sleep 5
    if check_port ${PORT}; then
        print "✅ React started on port ${PORT} (session: ${SESSION_NAME})"
        print "🔗 Frontend: http://localhost:${PORT}"
        print "🔗 API URL: ${VITE_API_BASE_URL}"
    else
        print "⚠️  React may not have started correctly; check: screen -r ${SESSION_NAME}"
    fi
}

stop_react() {
    if screen -list 2>/dev/null | grep -q "\.${SESSION_NAME}"; then
        screen -S "$SESSION_NAME" -X quit 2>/dev/null || true
        sleep 1
        print "✅ Stopped screen session ${SESSION_NAME}"
    else
        print "ℹ️  Screen session ${SESSION_NAME} not running"
    fi
    # Also kill any vite processes if lingering
    pkill -f "vite" 2>/dev/null && print "✅ Killed lingering Vite processes" || true
}

status_react() {
    if screen -list 2>/dev/null | grep -q "\.${SESSION_NAME}"; then
        print "🟢 React screen session running (${SESSION_NAME})"
    else
        print "🔴 React screen session not running"
    fi
    if check_port ${PORT}; then
        print "🟢 Port ${PORT} is LISTENing"
    else
        print "🔴 Port ${PORT} is not open"
    fi
}

case "$1" in
    start|"" ) start_react ;;
    stop) stop_react ;;
    restart) stop_react; start_react ;;
    status) status_react ;;
    *) print "Usage: $0 {start|stop|restart|status}"; exit 1 ;;
esac


