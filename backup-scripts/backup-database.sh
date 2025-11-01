#!/bin/bash
# backup-database.sh - Complete PostgreSQL Database Backup

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "🗄️ Starting database backup..."

# Create database backup directory
mkdir -p "$BACKUP_DIR"

# Database connection settings
export PGPORT=5434
export PGPASSWORD=doctrove_admin
export PGHOST=localhost
export PGUSER=doctrove_admin

echo "📊 Analyzing database size..."
DB_SIZE=$(psql -d doctrove -t -c "SELECT pg_size_pretty(pg_database_size('doctrove'));" | xargs)
echo "Database size: $DB_SIZE"

echo "💾 Creating multiple backup formats for maximum flexibility..."

# 1. Complete SQL dump (most portable, compressed)
echo "Creating compressed SQL dump..."
pg_dump --no-owner --no-privileges --compress=9 \
    --verbose doctrove > "$BACKUP_DIR/doctrove_complete.sql.gz" 2>&1

# 2. Custom format backup (fastest restore, parallel)
echo "Creating custom format backup..."
pg_dump --format=custom --compress=9 --verbose \
    doctrove > "$BACKUP_DIR/doctrove_complete.backup" 2>&1

# 3. Directory format (parallel restore capability)
echo "Creating directory format backup..."
pg_dump --format=directory --compress=9 --jobs=4 --verbose \
    doctrove --file="$BACKUP_DIR/doctrove_complete_dir" 2>&1

# 4. Schema-only backup (for quick structure recreation)
echo "Creating schema-only backup..."
pg_dump --schema-only --no-owner --no-privileges \
    doctrove > "$BACKUP_DIR/doctrove_schema_only.sql" 2>&1

# 5. Backup database globals (users, roles, etc.)
echo "Creating globals backup..."
pg_dumpall --globals-only > "$BACKUP_DIR/postgresql_globals.sql" 2>&1

# Create database info file
cat > "$BACKUP_DIR/database_info.txt" << EOF
DocScope Database Backup Information
===================================
Backup Date: $(date)
Database Name: doctrove
Database Size: $DB_SIZE
PostgreSQL Version: $(psql -d doctrove -t -c "SELECT version();" | head -1 | xargs)
Total Tables: $(psql -d doctrove -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
Total Records in doctrove_papers: $(psql -d doctrove -t -c "SELECT COUNT(*) FROM doctrove_papers;" | xargs)

Data Sources:
$(psql -d doctrove -t -c "SELECT doctrove_source, COUNT(*) FROM doctrove_papers GROUP BY doctrove_source ORDER BY doctrove_source;")

Backup Files:
- doctrove_complete.sql.gz      : Complete compressed SQL dump
- doctrove_complete.backup      : Custom format (use pg_restore)
- doctrove_complete_dir/        : Directory format (parallel restore)
- doctrove_schema_only.sql      : Database structure only
- postgresql_globals.sql        : Users and roles

Connection Settings Used:
- Host: $PGHOST
- Port: $PGPORT  
- User: $PGUSER
- Database: doctrove
EOF

echo "✅ Database backup complete"
echo "📁 Backup location: $BACKUP_DIR"
echo "📊 Backup files:"
ls -lh "$BACKUP_DIR"


