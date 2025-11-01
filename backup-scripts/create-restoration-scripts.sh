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


