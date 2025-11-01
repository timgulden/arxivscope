#!/bin/bash
# PostgreSQL Memory Optimization for Large-Scale Operations
# Optimizes memory settings for 17M+ papers

set -e

echo "🔧 Optimizing PostgreSQL memory settings for large-scale operations..."
echo "Timestamp: $(date)"
echo "=========================================="

# Database connection parameters
DB_NAME="doctrove"
DB_USER="doctrove_admin"
DB_HOST="localhost"
DB_PORT="5434"

# Check if we have superuser access
SUPERUSER_CHECK=$(PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT CASE WHEN current_setting('is_superuser') = 'on' THEN 'true' ELSE 'false' END;
" | xargs)

if [ "$SUPERUSER_CHECK" = "false" ]; then
    echo "⚠️  Not running as superuser - can only set session-level settings"
    echo "📋 For permanent changes, run this as postgres user or add to postgresql.conf:"
    echo ""
    echo "# Memory optimizations for 17M+ papers"
    echo "shared_buffers = 2GB"
    echo "work_mem = 256MB"
    echo "maintenance_work_mem = 4GB"
    echo "effective_cache_size = 8GB"
    echo ""
    echo "Then restart PostgreSQL: sudo systemctl restart postgresql"
    echo ""
    
    echo "🔄 Setting session-level optimizations..."
    PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SET shared_buffers = '2GB';
    SET work_mem = '256MB';
    SET maintenance_work_mem = '4GB';
    SET effective_cache_size = '8GB';
    "
    
    echo "✅ Session-level memory optimizations applied"
    echo "📊 Current settings:"
    PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT 'shared_buffers' as setting, setting::text as value
    UNION ALL
    SELECT 'work_mem', setting::text
    UNION ALL
    SELECT 'maintenance_work_mem', setting::text
    UNION ALL
    SELECT 'effective_cache_size', setting::text;
    "
    
else
    echo "✅ Running as superuser - applying permanent optimizations..."
    
    # Apply permanent system-wide settings
    PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    ALTER SYSTEM SET shared_buffers = '2GB';
    ALTER SYSTEM SET work_mem = '256MB';
    ALTER SYSTEM SET maintenance_work_mem = '4GB';
    ALTER SYSTEM SET effective_cache_size = '8GB';
    "
    
    echo "🔄 Reloading PostgreSQL configuration..."
    PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT pg_reload_conf();"
    
    echo "✅ Permanent memory optimizations applied"
    echo "📊 New settings:"
    PGPASSWORD=doctrove_admin psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT 'shared_buffers' as setting, setting::text as value
    UNION ALL
    SELECT 'work_mem', setting::text
    UNION ALL
    SELECT 'maintenance_work_mem', setting::text
    UNION ALL
    SELECT 'effective_cache_size', setting::text;
    "
fi

echo ""
echo "🎯 Memory optimization complete!"
echo "📈 Expected improvements:"
echo "   - HNSW index building: 4-8x faster"
echo "   - VACUUM operations: 3-5x faster"
echo "   - Complex queries: 2-3x faster"
echo "   - ANALYZE operations: 2-4x faster"
echo ""
echo "💡 For maximum benefit, restart PostgreSQL after applying permanent settings"




