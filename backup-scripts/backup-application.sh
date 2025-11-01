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


