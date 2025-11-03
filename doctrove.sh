#!/bin/bash

# Unified backend (API + optional enrichment) manager
# Usage:
#   ./doctrove.sh start|stop|restart|status [--enrichment]

set -e

API_SESSION="doctrove_api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="${SCRIPT_DIR}/doctrove-api"
VENV_DIR="${SCRIPT_DIR}/venv"
# Use system Python with venv site-packages due to venv Python binary corruption
# The venv's Python binary has broken library paths, so we use /usr/bin/python3
# with the venv's site-packages in PYTHONPATH instead
VENV_SITE_PACKAGES="${VENV_DIR}/lib/python3.9/site-packages"
API_CMD="cd ${API_DIR} && PYTHONPATH=${VENV_SITE_PACKAGES}:\$PYTHONPATH /usr/bin/python3 api.py"
API_PORT="${NEW_API_PORT:-${DOCTROVE_API_PORT:-5001}}"

EMB_SESSION="enrichment_embeddings"
EMB2D_SESSION="embedding_2d"
ENRICH_DIR="${SCRIPT_DIR}/embedding-enrichment"
# Use system Python with venv site-packages for enrichment workers too
EMB_CMD="cd ${ENRICH_DIR} && PYTHONPATH=${VENV_SITE_PACKAGES}:\$PYTHONPATH /usr/bin/python3 event_listener.py"
EMB2D_CMD="cd ${ENRICH_DIR} && PYTHONPATH=${VENV_SITE_PACKAGES}:\$PYTHONPATH /usr/bin/python3 queue_2d_worker.py --batch-size 1000 --sleep 5"

print() { echo -e "$1"; }

ensure_screen() {
    if ! command -v screen >/dev/null 2>&1; then
        print "❌ screen not installed."
        print "   macOS: brew install screen"
        print "   Linux: sudo apt-get install screen"
        exit 1
    fi
}

ensure_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print "❌ Virtual environment not found at ${VENV_DIR}"
        print "   Create it with: python -m venv venv"
        exit 1
    fi
}

has_flag() {
    for arg in "$@"; do
        if [ "$arg" = "--enrichment" ] || [ "$arg" = "--all" ]; then
            return 0
        fi
    done
    return 1
}

start_api() {
    ensure_screen
    ensure_venv
    if screen -list 2>/dev/null | grep -q "\.${API_SESSION}"; then
        print "ℹ️  API already running in screen (${API_SESSION})"
    else
        (cd "$API_DIR" && screen -dmS "$API_SESSION" bash -c "$API_CMD")
        sleep 3
    fi
    if curl -s "http://localhost:${API_PORT}/api/health" >/dev/null 2>&1 && curl -s "http://localhost:${API_PORT}/api/health" | grep -q healthy; then
        print "✅ API healthy on port ${API_PORT} (session: ${API_SESSION})"
    else
        print "⚠️  API may not have started correctly; check: screen -r ${API_SESSION}"
    fi
}

stop_api() {
    if screen -list 2>/dev/null | grep -q "\.${API_SESSION}"; then
        screen -S "$API_SESSION" -X quit 2>/dev/null || true
        sleep 1
        print "✅ Stopped API session ${API_SESSION}"
    else
        print "ℹ️  API session ${API_SESSION} not running"
    fi
    pkill -f "doctrove-api/api.py" 2>/dev/null && print "✅ Killed orphan API process" || true
}

status_api() {
    if screen -list 2>/dev/null | grep -q "\.${API_SESSION}"; then
        print "🟢 API screen session running (${API_SESSION})"
    else
        print "🔴 API screen session not running"
    fi
    if curl -s "http://localhost:${API_PORT}/api/health" | grep -q healthy; then
        print "🟢 API health endpoint responsive"
    else
        print "🔴 API health endpoint not responsive"
    fi
}

start_enrichment() {
    ensure_screen
    ensure_venv
    if ! screen -list 2>/dev/null | grep -q "\.${EMB_SESSION}"; then
        (cd "$ENRICH_DIR" && screen -dmS "$EMB_SESSION" bash -c "$EMB_CMD")
        sleep 2
    fi
    if ! screen -list 2>/dev/null | grep -q "\.${EMB2D_SESSION}"; then
        (cd "$ENRICH_DIR" && screen -dmS "$EMB2D_SESSION" bash -c "$EMB2D_CMD")
        sleep 2
    fi
    print "✅ Enrichment workers ensured (sessions: ${EMB_SESSION}, ${EMB2D_SESSION})"
}

stop_enrichment() {
    for s in "$EMB_SESSION" "$EMB2D_SESSION"; do
        if screen -list 2>/dev/null | grep -q "\.${s}"; then
            screen -S "$s" -X quit 2>/dev/null || true
            print "✅ Stopped ${s}"
        fi
    done
    pkill -f "event_listener_functional.py" 2>/dev/null || true
    pkill -f "queue_2d_worker.py" 2>/dev/null || true
}

status_enrichment() {
    for s in "$EMB_SESSION" "$EMB2D_SESSION"; do
        if screen -list 2>/dev/null | grep -q "\.${s}"; then
            print "🟢 ${s} running"
        else
            print "🔴 ${s} not running"
        fi
    done
}

ACTION="$1"; shift || true
WITH_ENRICH=false
if has_flag "$@"; then WITH_ENRICH=true; fi

case "$ACTION" in
    start|"")
        start_api
        if [ "$WITH_ENRICH" = true ]; then start_enrichment; fi
        ;;
    stop)
        if [ "$WITH_ENRICH" = true ]; then stop_enrichment; fi
        stop_api
        ;;
    restart)
        if [ "$WITH_ENRICH" = true ]; then stop_enrichment; fi
        stop_api
        start_api
        if [ "$WITH_ENRICH" = true ]; then start_enrichment; fi
        ;;
    status)
        status_api
        if [ "$WITH_ENRICH" = true ]; then status_enrichment; fi
        ;;
    *)
        print "Usage: $0 {start|stop|restart|status} [--enrichment]"
        exit 1
        ;;
esac




