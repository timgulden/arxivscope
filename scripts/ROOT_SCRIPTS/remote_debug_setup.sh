#!/bin/bash

# Remote Debug Setup Script
# This script sets up enhanced logging and monitoring for server deployment

set -e

echo "🔧 Setting up remote debugging tools..."

# Create enhanced logging directory
mkdir -p logs/remote_debug

# Create a comprehensive health check script
cat > check_remote_health.sh << 'EOF'
#!/bin/bash

# Remote Health Check Script
# Run this on the server to get comprehensive system status

echo "=== REMOTE SERVER HEALTH CHECK ==="
echo "Timestamp: $(date)"
echo "Hostname: $(hostname)"
echo ""

echo "=== SYSTEM RESOURCES ==="
echo "Memory:"
free -h
echo ""
echo "Disk Space:"
df -h
echo ""
echo "CPU Load:"
uptime
echo ""

echo "=== NETWORK CONNECTIVITY ==="
echo "Testing OpenAlex S3 access..."
curl -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/2025-01-01/part_000.gz" 2>/dev/null | head -1 || echo "❌ S3 access failed"
echo ""

echo "=== DATABASE STATUS ==="
if command -v psql &> /dev/null; then
    psql -h localhost -U $USER -d doctrove -c "
    SELECT 
        doctrove_source,
        COUNT(*) as total_papers,
        COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings,
        COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_2d_embeddings
    FROM doctrove_papers 
    GROUP BY doctrove_source 
    ORDER BY total_papers DESC;" 2>/dev/null || echo "❌ Database connection failed"
else
    echo "❌ PostgreSQL not found"
fi
echo ""

echo "=== SERVICE STATUS ==="
echo "Python processes:"
ps aux | grep -E "(python.*app|python.*api|python.*main)" | grep -v grep || echo "No Python services running"
echo ""

echo "=== LOG FILES ==="
echo "Recent enrichment log entries:"
tail -10 logs/enrichment.log 2>/dev/null || echo "No enrichment log found"
echo ""

echo "=== ENVIRONMENT ==="
echo "Python version: $(python3 --version 2>/dev/null || echo 'Python not found')"
echo "Virtual environment: $VIRTUAL_ENV"
echo "Working directory: $(pwd)"
echo ""

echo "=== GIT STATUS ==="
git status --porcelain 2>/dev/null || echo "Not a git repository"
echo ""

echo "=== REMOTE DEBUG COMPLETE ==="
EOF

chmod +x check_remote_health.sh

# Create a log streaming script
cat > stream_logs.sh << 'EOF'
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
EOF

chmod +x stream_logs.sh

# Create a comprehensive error reporting script
cat > report_error.sh << 'EOF'
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
EOF

chmod +x report_error.sh

# Create a quick status script
cat > quick_status.sh << 'EOF'
#!/bin/bash

# Quick Status Script
# Fast status check for remote monitoring

echo "🔍 Quick Status Check - $(date)"
echo ""

# Database count
if command -v psql &> /dev/null; then
    echo "📊 Database:"
    psql -h localhost -U $USER -d doctrove -c "
    SELECT 
        COUNT(*) as total_papers,
        COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings
    FROM doctrove_papers;" 2>/dev/null | grep -E "[0-9]+" | head -1 || echo "❌ DB error"
fi

# Service check
echo "🔄 Services:"
ps aux | grep -E "(python.*app|python.*api)" | grep -v grep | wc -l | xargs echo "  Running:"

# Recent activity
echo "📝 Recent activity:"
tail -5 logs/enrichment.log 2>/dev/null | grep -E "(INFO|ERROR|WARNING)" | tail -3 || echo "  No recent activity"
EOF

chmod +x quick_status.sh

echo "✅ Remote debugging tools created:"
echo "  📋 check_remote_health.sh - Comprehensive health check"
echo "  📊 stream_logs.sh - Real-time log streaming"
echo "  🐛 report_error.sh - Error diagnostic collection"
echo "  🔍 quick_status.sh - Quick status check"
echo ""
echo "🚀 Ready for server deployment!"
echo ""
echo "📝 Next steps:"
echo "1. Copy these scripts to your server"
echo "2. Set up SSH access in Cursor (recommended)"
echo "3. Run check_remote_health.sh on the server"
echo "4. Use report_error.sh when issues occur" 