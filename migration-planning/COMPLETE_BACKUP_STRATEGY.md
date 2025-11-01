# Complete Backup Strategy for DocScope Platform

> **Purpose**: Create comprehensive backup of entire DocScope system to external SSD  
> **Target**: 2TB USB-C SSD (when connected to your laptop)  
> **Strategy**: Full backup now, filter later if needed  

---

## **I. BACKUP OVERVIEW**

### **A. Why This Approach is Perfect**

**Advantages**:
- ✅ **No immediate filtering needed** - backup everything while you have access
- ✅ **Future flexibility** - can filter later if you change jobs
- ✅ **Complete preservation** - nothing lost, all relationships intact
- ✅ **Time efficient** - single backup operation vs. complex filtering
- ✅ **Risk mitigation** - have everything safely backed up

**Timeline**: 
- **Setup**: 1 hour to create scripts
- **Execution**: 4-8 hours for full backup (can run overnight)
- **Verification**: 1 hour to test restoration

### **B. Backup Scope**

**Database**: 393GB PostgreSQL database (complete)
**Application**: ~5GB source code, configuration, documentation
**Total**: ~400GB (fits comfortably on 2TB SSD)

---

## **II. COMPLETE BACKUP SCRIPTS**

### **A. Master Backup Script**

```bash
#!/bin/bash
# master-backup.sh - Complete DocScope Platform Backup

# Configuration
EXTERNAL_SSD="/media/your-username/YourSSDName"  # Adjust for your SSD mount point
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$EXTERNAL_SSD/docscope-complete-backup-$BACKUP_DATE"

echo "🚀 Starting Complete DocScope Platform Backup"
echo "📅 Backup Date: $BACKUP_DATE"
echo "💾 Target: $BACKUP_DIR"

# Check if external SSD is mounted
if [ ! -d "$EXTERNAL_SSD" ]; then
    echo "❌ External SSD not found at $EXTERNAL_SSD"
    echo "Please mount your external SSD and update the path in this script"
    exit 1
fi

# Check available space
AVAILABLE_GB=$(df "$EXTERNAL_SSD" | tail -1 | awk '{print int($4/1024/1024)}')
echo "💽 Available space: ${AVAILABLE_GB}GB"

if [ $AVAILABLE_GB -lt 500 ]; then
    echo "⚠️  Warning: Less than 500GB available. Backup may not complete."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create backup directory structure
mkdir -p "$BACKUP_DIR"/{database,application,documentation,scripts}

echo "📁 Created backup directory structure"

# Start logging
LOG_FILE="$BACKUP_DIR/backup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "📝 Logging to: $LOG_FILE"
echo "⏰ Backup started at: $(date)"

# Run backup components
./backup-database.sh "$BACKUP_DIR/database"
./backup-application.sh "$BACKUP_DIR/application"
./backup-documentation.sh "$BACKUP_DIR/documentation"
./create-restoration-scripts.sh "$BACKUP_DIR/scripts"

echo "✅ Complete backup finished at: $(date)"
echo "📊 Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "💾 Location: $BACKUP_DIR"
```

### **B. Database Backup Script**

```bash
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
```

### **C. Application Backup Script**

```bash
#!/bin/bash
# backup-application.sh - Complete Application Code Backup

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "📁 Starting application backup..."

# Create application backup directory
mkdir -p "$BACKUP_DIR"

# Current working directory (should be /opt/arxivscope)
SOURCE_DIR="/opt/arxivscope"

echo "📦 Backing up complete source code..."

# Create tar archive of entire application
tar -czf "$BACKUP_DIR/docscope-complete-source.tar.gz" \
    --exclude='.git/objects' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='.env.local' \
    --exclude='.env.remote' \
    --exclude='*.log' \
    -C "$(dirname "$SOURCE_DIR")" "$(basename "$SOURCE_DIR")"

# Also create uncompressed copy for easy access
echo "📂 Creating uncompressed copy for easy access..."
cp -r "$SOURCE_DIR" "$BACKUP_DIR/docscope-source-code"

# Remove sensitive files from uncompressed copy
find "$BACKUP_DIR/docscope-source-code" -name ".env*" -delete
find "$BACKUP_DIR/docscope-source-code" -name "*.pyc" -delete
find "$BACKUP_DIR/docscope-source-code" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Create application info file
cat > "$BACKUP_DIR/application_info.txt" << EOF
DocScope Application Backup Information
======================================
Backup Date: $(date)
Source Directory: $SOURCE_DIR
Application Size: $(du -sh "$SOURCE_DIR" | cut -f1)

Git Information:
Repository: $(cd "$SOURCE_DIR" && git remote get-url origin 2>/dev/null || echo "No remote configured")
Current Branch: $(cd "$SOURCE_DIR" && git branch --show-current 2>/dev/null || echo "Not a git repository")
Last Commit: $(cd "$SOURCE_DIR" && git log -1 --oneline 2>/dev/null || echo "No git history")
Status: $(cd "$SOURCE_DIR" && git status --porcelain 2>/dev/null | wc -l) modified files

Directory Structure:
$(find "$SOURCE_DIR" -maxdepth 3 -type d | head -20)

Key Files:
- docscope-complete-source.tar.gz  : Complete compressed source code
- docscope-source-code/            : Uncompressed source (sensitive files removed)

Python Environment:
$(python3 --version 2>/dev/null || echo "Python not found")
$(pip3 list 2>/dev/null | head -10 || echo "Pip not available")
EOF

echo "✅ Application backup complete"
echo "📁 Backup location: $BACKUP_DIR"
echo "📊 Backup files:"
ls -lh "$BACKUP_DIR"
```

### **D. Documentation Backup Script**

```bash
#!/bin/bash
# backup-documentation.sh - Documentation and Migration Planning Backup

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "📚 Starting documentation backup..."

# Create documentation backup directory
mkdir -p "$BACKUP_DIR"

SOURCE_DIR="/opt/arxivscope"

# Copy all documentation
echo "📄 Backing up migration planning documents..."
if [ -d "$SOURCE_DIR/migration-planning" ]; then
    cp -r "$SOURCE_DIR/migration-planning" "$BACKUP_DIR/"
fi

echo "📖 Backing up existing documentation..."
if [ -d "$SOURCE_DIR/docs" ]; then
    cp -r "$SOURCE_DIR/docs" "$BACKUP_DIR/"
fi

# Copy any README files
echo "📝 Backing up README and markdown files..."
find "$SOURCE_DIR" -name "*.md" -not -path "*/.*" -exec cp {} "$BACKUP_DIR/" \; 2>/dev/null

# Create documentation index
cat > "$BACKUP_DIR/documentation_index.md" << EOF
# DocScope Documentation Backup

## Migration Planning Documents
$(find "$BACKUP_DIR/migration-planning" -name "*.md" 2>/dev/null | sed 's|.*/||' | sed 's/^/- /' || echo "No migration planning documents found")

## Technical Documentation  
$(find "$BACKUP_DIR/docs" -name "*.md" 2>/dev/null | sed 's|.*/||' | sed 's/^/- /' || echo "No docs directory found")

## Root Level Documentation
$(find "$BACKUP_DIR" -maxdepth 1 -name "*.md" | sed 's|.*/||' | sed 's/^/- /' | grep -v documentation_index.md)

## Backup Information
- Backup Date: $(date)
- Source: $SOURCE_DIR
- Total Documentation Files: $(find "$BACKUP_DIR" -name "*.md" | wc -l)
EOF

echo "✅ Documentation backup complete"
echo "📁 Backup location: $BACKUP_DIR"
```

### **E. Restoration Scripts Creation**

```bash
#!/bin/bash
# create-restoration-scripts.sh - Create scripts for easy restoration

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "🔧 Creating restoration scripts..."

# Create restore database script
cat > "$BACKUP_DIR/restore-database.sh" << 'EOF'
#!/bin/bash
# restore-database.sh - Restore DocScope Database

echo "🔄 DocScope Database Restoration"
echo "================================"

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running or not accessible on port 5432"
    echo "Please start PostgreSQL and try again"
    exit 1
fi

# Configuration
DB_NAME="doctrove_restored"
DB_USER="doctrove_admin"

echo "📊 Available backup files:"
ls -lh *.sql.gz *.backup 2>/dev/null

echo ""
read -p "Enter database name to create [$DB_NAME]: " INPUT_DB_NAME
DB_NAME=${INPUT_DB_NAME:-$DB_NAME}

read -p "Enter database user [$DB_USER]: " INPUT_DB_USER  
DB_USER=${INPUT_DB_USER:-$DB_USER}

echo "🗄️ Creating database: $DB_NAME"
createdb -U "$DB_USER" "$DB_NAME"

echo "📥 Choose restoration method:"
echo "1. From compressed SQL dump (doctrove_complete.sql.gz)"
echo "2. From custom format backup (doctrove_complete.backup)"
echo "3. From directory format (doctrove_complete_dir)"

read -p "Choose method (1-3): " METHOD

case $METHOD in
    1)
        echo "📤 Restoring from compressed SQL dump..."
        gunzip -c doctrove_complete.sql.gz | psql -U "$DB_USER" -d "$DB_NAME"
        ;;
    2)
        echo "📤 Restoring from custom format backup..."
        pg_restore -U "$DB_USER" -d "$DB_NAME" --verbose doctrove_complete.backup
        ;;
    3)
        echo "📤 Restoring from directory format (parallel)..."
        pg_restore -U "$DB_USER" -d "$DB_NAME" --jobs=4 --verbose doctrove_complete_dir
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo "✅ Database restoration complete!"
echo "🔗 Connection details:"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Host: localhost"
echo "   Port: 5432"

# Test the restoration
echo "🧪 Testing restored database..."
PAPER_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM doctrove_papers;" 2>/dev/null | xargs)
if [ ! -z "$PAPER_COUNT" ]; then
    echo "✅ Test successful: $PAPER_COUNT papers found"
else
    echo "⚠️  Test failed: Could not count papers"
fi
EOF

# Create restore application script
cat > "$BACKUP_DIR/restore-application.sh" << 'EOF'
#!/bin/bash
# restore-application.sh - Restore DocScope Application

echo "📁 DocScope Application Restoration"
echo "==================================="

TARGET_DIR="$HOME/docscope-restored"
read -p "Enter target directory [$TARGET_DIR]: " INPUT_DIR
TARGET_DIR=${INPUT_DIR:-$TARGET_DIR}

echo "📦 Extracting application to: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

if [ -f "docscope-complete-source.tar.gz" ]; then
    tar -xzf docscope-complete-source.tar.gz -C "$TARGET_DIR" --strip-components=1
    echo "✅ Application extracted from archive"
elif [ -d "docscope-source-code" ]; then
    cp -r docscope-source-code/* "$TARGET_DIR/"
    echo "✅ Application copied from directory"
else
    echo "❌ No application backup found"
    exit 1
fi

echo "🔧 Setting up application..."
cd "$TARGET_DIR"

# Create basic environment file
cat > .env.local << 'ENVEOF'
# Restored DocScope Environment
# Update these settings for your environment

DATABASE_URL=postgresql://doctrove_admin:password@localhost:5432/doctrove_restored
API_BASE_URL=http://localhost:5000
DEBUG=true
ENVEOF

echo "✅ Application restoration complete!"
echo "📁 Location: $TARGET_DIR"
echo "🔧 Next steps:"
echo "   1. Update .env.local with your database credentials"
echo "   2. Install dependencies: pip install -r requirements.txt"
echo "   3. Start the application"
EOF

# Create complete restoration script
cat > "$BACKUP_DIR/restore-complete-system.sh" << 'EOF'
#!/bin/bash
# restore-complete-system.sh - Restore Complete DocScope System

echo "🚀 Complete DocScope System Restoration"
echo "======================================="

echo "This script will restore both the database and application"
echo "Make sure PostgreSQL is running before proceeding"
echo ""

read -p "Continue with complete restoration? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo "1️⃣ Restoring database..."
./restore-database.sh

if [ $? -eq 0 ]; then
    echo "2️⃣ Restoring application..."
    ./restore-application.sh
    
    if [ $? -eq 0 ]; then
        echo "✅ Complete system restoration successful!"
        echo ""
        echo "🎉 DocScope is ready to use!"
        echo "📁 Application: Check the application directory shown above"
        echo "🗄️ Database: doctrove_restored (or name you specified)"
    else
        echo "❌ Application restoration failed"
    fi
else
    echo "❌ Database restoration failed"
fi
EOF

# Make scripts executable
chmod +x "$BACKUP_DIR"/*.sh

# Create restoration guide
cat > "$BACKUP_DIR/RESTORATION_GUIDE.md" << EOF
# DocScope Restoration Guide

## Quick Start
1. \`./restore-complete-system.sh\` - Restore everything automatically
2. Follow the prompts to configure database and application

## Individual Restoration
- \`./restore-database.sh\` - Restore database only
- \`./restore-application.sh\` - Restore application only

## Manual Restoration
See database_info.txt and application_info.txt for detailed information about the backup contents.

## System Requirements
- PostgreSQL 14+ 
- Python 3.8+
- 500GB+ available disk space
- 8GB+ RAM recommended

## Backup Contents
- **Database**: $(ls -lh ../database/ 2>/dev/null | wc -l) files, ~400GB
- **Application**: Complete source code and configuration
- **Documentation**: All technical documentation and migration planning

Backup Date: $(date)
EOF

echo "✅ Restoration scripts created"
echo "📁 Scripts location: $BACKUP_DIR"
ls -la "$BACKUP_DIR"/*.sh
```

---

## **III. EXECUTION PLAN**

### **A. Pre-Backup Checklist**

```bash
# 1. Connect your external SSD to your laptop
# 2. Mount the SSD and note the mount point
# 3. Update the EXTERNAL_SSD path in master-backup.sh
# 4. Ensure you have access to the database
# 5. Check available space on SSD (need ~500GB)
```

### **B. Running the Backup**

```bash
# 1. Copy all backup scripts to your system
# 2. Make them executable
chmod +x *.sh

# 3. Update the SSD path in master-backup.sh
# Edit the line: EXTERNAL_SSD="/media/your-username/YourSSDName"

# 4. Run the complete backup
./master-backup.sh

# This will create a timestamped backup directory with everything
```

### **C. Backup Verification**

```bash
# After backup completes, verify:
# 1. Check backup size
du -sh /path/to/backup/directory

# 2. Test database restoration (optional)
cd /path/to/backup/directory/scripts
./restore-database.sh

# 3. Verify application files
ls -la /path/to/backup/directory/application/
```

---

## **IV. FUTURE FILTERING STRATEGY**

### **A. When You Need to Filter (If You Leave)**

```bash
# 1. Restore complete database
./restore-database.sh

# 2. Create filtered version
psql -d doctrove_restored -c "
    CREATE DATABASE doctrove_public AS 
    SELECT * FROM doctrove_papers 
    WHERE doctrove_source IN ('openalex', 'aipickle');
"

# 3. Export filtered version
pg_dump doctrove_public > doctrove_public_only.sql
```

### **B. Repository Cleaning (If Needed)**

```bash
# Remove RAND-specific references from source code
find . -name "*.py" -exec sed -i 's/RAND Corporation/Organization/g' {} \;
find . -name "*.md" -exec sed -i 's/RAND/Organization/g' {} \;
```

---

## **V. BENEFITS OF THIS APPROACH**

### **✅ Immediate Benefits**
- **Complete preservation** of all your work
- **No data loss risk** - everything backed up
- **Future flexibility** - can filter later if needed
- **Professional portfolio** - complete working system

### **✅ Long-term Benefits**  
- **Career security** - own complete copy of your work
- **Demonstration ready** - can show full capabilities
- **Learning resource** - complete system for reference
- **Backup insurance** - never lose your work

### **✅ Risk Mitigation**
- **No immediate filtering** - avoid accidentally removing important data
- **Multiple backup formats** - maximum restoration flexibility
- **Complete documentation** - understand everything later
- **Professional compliance** - can filter appropriately when needed

---

**This approach gives you maximum security and flexibility while requiring minimal immediate effort!**


