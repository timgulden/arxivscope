#!/bin/bash
# master-backup.sh - Complete DocScope Platform Backup

# Configuration
EXTERNAL_SSD="/media/your-username/YourSSDName"  # UPDATE THIS PATH FOR YOUR SSD
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$EXTERNAL_SSD/docscope-complete-backup-$BACKUP_DATE"

echo "🚀 Starting Complete DocScope Platform Backup"
echo "📅 Backup Date: $BACKUP_DATE"
echo "💾 Target: $BACKUP_DIR"

# Check if external SSD is mounted
if [ ! -d "$EXTERNAL_SSD" ]; then
    echo "❌ External SSD not found at $EXTERNAL_SSD"
    echo "Please mount your external SSD and update the path in this script"
    echo "Common mount points:"
    echo "  - /media/\$USER/SSDName"
    echo "  - /mnt/external-ssd"
    echo "  - /Volumes/SSDName (macOS)"
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
echo "🗄️ Starting database backup..."
./backup-database.sh "$BACKUP_DIR/database"

echo "📁 Starting application backup..."
./backup-application.sh "$BACKUP_DIR/application"

echo "📚 Starting documentation backup..."
./backup-documentation.sh "$BACKUP_DIR/documentation"

echo "🔧 Creating restoration scripts..."
./create-restoration-scripts.sh "$BACKUP_DIR/scripts"

echo "✅ Complete backup finished at: $(date)"
echo "📊 Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "💾 Location: $BACKUP_DIR"

# Create quick access symlink
ln -sf "$BACKUP_DIR" "$EXTERNAL_SSD/docscope-latest-backup"
echo "🔗 Quick access link: $EXTERNAL_SSD/docscope-latest-backup"


