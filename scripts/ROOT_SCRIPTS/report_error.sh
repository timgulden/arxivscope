#!/bin/bash

# Error Reporting Script
# Run this when you encounter an error to collect diagnostic information

ERROR_LOG="logs/remote_debug/error_$(date +%Y%m%d_%H%M%S).log"

echo "🐛 Collecting error diagnostic information..."
echo "Error report will be saved to: $ERROR_LOG"

{
    echo "=== ERROR DIAGNOSTIC REPORT ==="
    echo "Timestamp: $(date)"
    echo "Hostname: $(hostname)"
    echo "User: $(whoami)"
    echo ""
    
    echo "=== COMMAND HISTORY ==="
    history | tail -20
    echo ""
    
    echo "=== SYSTEM STATUS ==="
    ./check_remote_health.sh
    echo ""
    
    echo "=== RECENT LOGS ==="
    echo "Enrichment log (last 50 lines):"
    tail -50 logs/enrichment.log 2>/dev/null || echo "No enrichment log"
    echo ""
    echo "API log (last 50 lines):"
    tail -50 logs/api.log 2>/dev/null || echo "No API log"
    echo ""
    echo "Frontend log (last 50 lines):"
    tail -50 logs/frontend.log 2>/dev/null || echo "No frontend log"
    echo ""
    
    echo "=== ENVIRONMENT VARIABLES ==="
    env | grep -E "(PYTHON|PATH|VIRTUAL|CONDA)" | sort
    echo ""
    
    echo "=== PROCESS LIST ==="
    ps aux | grep -E "(python|postgres|nginx)" | grep -v grep
    echo ""
    
} > "$ERROR_LOG" 2>&1

echo "✅ Error report saved to: $ERROR_LOG"
echo "📋 Copy this file content to share with the assistant:"
echo "cat $ERROR_LOG"
