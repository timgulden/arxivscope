#!/bin/bash
echo "🔄 Continuous IVFFlat Index Build Monitor"
echo "Press Ctrl+C to stop monitoring"
echo "=========================================="

while true; do
    echo ""
    echo "⏰ $(date)"
    echo "----------------------------------------"
    
    # Check index status
    echo "📊 Index Status:"
    PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "
    SELECT 
        i.indexname,
        pg_size_pretty(pg_relation_size(i.indexname::regclass)) AS size,
        CASE WHEN ix.indisvalid THEN '✅ Valid' ELSE '🔄 Building' END as status,
        CASE WHEN ix.indisready THEN '✅ Ready' ELSE '⏳ Not Ready' END as ready
    FROM pg_indexes i 
    JOIN pg_index ix ON i.indexname = ix.indexrelid::regclass::text 
    WHERE i.tablename='doctrove_papers' AND i.indexname='idx_papers_embedding_ivfflat_optimized';"
    
    # Check active processes
    echo ""
    echo "🔍 Active Build Process:"
    PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "
    SELECT 
        pid,
        state,
        query_start,
        now() - query_start as duration,
        LEFT(query, 80) as query_preview
    FROM pg_stat_activity 
    WHERE query LIKE '%CREATE INDEX CONCURRENTLY%idx_papers_embedding_ivfflat_optimized%'
    AND state = 'active';"
    
    # Check system resources
    echo ""
    echo "💾 System Resources:"
    echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2 " (" $3*100/$2 "%)"}')"
    echo "Disk I/O: $(iostat -x 1 1 | tail -n +4 | head -1 | awk '{print "Read: " $4 "KB/s, Write: " $5 "KB/s"}')"
    
    sleep 30
done
