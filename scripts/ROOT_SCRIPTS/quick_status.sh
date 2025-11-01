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
