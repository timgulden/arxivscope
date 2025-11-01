#!/bin/bash

# Log Streaming Script
# Use this to stream logs in real-time for remote debugging

LOG_DIR="logs"
TAIL_LINES=50

echo "📊 Streaming logs from $LOG_DIR..."
echo "Press Ctrl+C to stop"
echo ""

# Stream multiple log files
tail -f -n $TAIL_LINES \
    $LOG_DIR/enrichment.log \
    $LOG_DIR/api.log \
    $LOG_DIR/frontend.log \
    $LOG_DIR/remote_debug/$(date +%Y-%m-%d).log 2>/dev/null | \
    while read line; do
        echo "[$(date '+%H:%M:%S')] $line"
    done
