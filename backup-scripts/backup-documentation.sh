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


