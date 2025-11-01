#!/bin/bash

# Master orchestrator for frontend + backend
# Usage:
#   ./services.sh start|stop|restart|status [--enrichment]

set -e

ACTION="$1"; shift || true

case "$ACTION" in
    start|"" )
        ./docscope.sh start || true
        ./doctrove.sh start "$@"
        ;;
    stop)
        ./doctrove.sh stop "$@" || true
        ./docscope.sh stop || true
        ;;
    restart)
        ./docscope.sh stop || true
        ./doctrove.sh stop "$@" || true
        ./docscope.sh start || true
        ./doctrove.sh start "$@"
        ;;
    status)
        echo "== Frontend =="; ./docscope.sh status || true
        echo "== Backend =="; ./doctrove.sh status "$@" || true
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status} [--enrichment]"; exit 1 ;;
esac




