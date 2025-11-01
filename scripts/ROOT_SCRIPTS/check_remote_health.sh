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
