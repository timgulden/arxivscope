#!/bin/bash
# Monitor VACUUM ANALYZE progress

echo "🔍 Monitoring VACUUM ANALYZE progress..."
echo "=========================================="

while true; do
    echo "📊 Status at $(date):"
    
    # Check if VACUUM is still running
    VACUUM_PID=$(PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -d doctrove -U doctrove_admin -t -c "SELECT pid FROM pg_stat_activity WHERE query LIKE '%VACUUM ANALYZE doctrove_papers%' AND state = 'active';" 2>/dev/null | xargs)
    
    if [ -z "$VACUUM_PID" ]; then
        echo "✅ VACUUM ANALYZE completed!"
        break
    fi
    
    # Show duration
    DURATION=$(PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -d doctrove -U doctrove_admin -t -c "SELECT now() - query_start FROM pg_stat_activity WHERE pid = $VACUUM_PID;" 2>/dev/null | xargs)
    echo "⏱️  Running for: $DURATION"
    
    # Show table stats
    echo "📈 Table Statistics:"
    PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -d doctrove -U doctrove_admin -c "SELECT n_tup_ins, n_tup_upd, n_tup_del, n_dead_tup FROM pg_stat_user_tables WHERE relname = 'doctrove_papers';" 2>/dev/null
    
    # Show sizes
    echo "💾 Storage Sizes:"
    PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -d doctrove -U doctrove_admin -c "SELECT pg_size_pretty(pg_total_relation_size('doctrove_papers')) as total_size, pg_size_pretty(pg_relation_size('doctrove_papers')) as table_size, pg_size_pretty(pg_total_relation_size('doctrove_papers') - pg_relation_size('doctrove_papers')) as index_size;" 2>/dev/null
    
    echo "=========================================="
    sleep 30
done

echo "🎉 VACUUM ANALYZE monitoring complete!"


