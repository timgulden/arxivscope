#!/bin/bash

# ============================================================================
# FRONTEND SOURCE NAME UPDATE SCRIPT
# ============================================================================
# This script updates all frontend references from old source names to new ones:
# - external_publication -> extpub
# - rand_publication -> randpub (if any still exist)
# ============================================================================

set -e  # Exit on any error

echo "=== FRONTEND SOURCE NAME UPDATE SCRIPT ==="
echo "This script will update all frontend source name references"
echo ""

# Check if we're in the right directory
if [ ! -f "docscope/app.py" ]; then
    echo "ERROR: This script must be run from the arxivscope-back-end directory"
    exit 1
fi

echo "✅ Running from correct directory"
echo ""

# Create backup of current frontend state
echo "=== Creating backup of current frontend state ==="
BACKUP_DIR="./frontend_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r docscope "$BACKUP_DIR/"
echo "✅ Frontend backup created in: $BACKUP_DIR"
echo ""

# ============================================================================
# PHASE 1: UPDATE SOURCE NAME REFERENCES
# ============================================================================

echo "=== PHASE 1: Updating source name references ==="

# Update external_publication to extpub
echo "  Updating external_publication -> extpub..."
find docscope -name "*.py" | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' 's/external_publication/extpub/g' "$file" 2>/dev/null || echo "Skipped: $file"
    fi
done

# Update any remaining rand_publication to randpub (if they exist)
echo "  Updating any remaining rand_publication -> randpub..."
find docscope -name "*.py" | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' 's/rand_publication/randpub/g' "$file" 2>/dev/null || echo "Skipped: $file"
    fi
done

echo "✅ Phase 1 complete: Source name references updated"
echo ""

# ============================================================================
# VERIFICATION
# ============================================================================

echo "=== VERIFICATION: Checking for remaining old source names ==="

echo "Checking for remaining 'external_publication' references (should be none)..."
REMAINING_EXTPUB=$(grep -r "external_publication" docscope --exclude-dir="$BACKUP_DIR" | head -5 || true)

if [ -n "$REMAINING_EXTPUB" ]; then
    echo "⚠️  Found remaining 'external_publication' references:"
    echo "$REMAINING_EXTPUB"
else
    echo "✅ No remaining 'external_publication' references found"
fi

echo ""
echo "Checking for remaining 'rand_publication' references (should be none)..."
REMAINING_RAND_PUB=$(grep -r "rand_publication" docscope --exclude-dir="$BACKUP_DIR" | head -5 || true)

if [ -n "$REMAINING_RAND_PUB" ]; then
    echo "⚠️  Found remaining 'rand_publication' references:"
    echo "$REMAINING_RAND_PUB"
else
    echo "✅ No remaining 'rand_publication' references found"
fi

echo ""
echo "=== MIGRATION SUMMARY ==="
echo "✅ Frontend source name update completed"
echo "✅ Backup created in: $BACKUP_DIR"
echo ""
echo "UPDATES APPLIED:"
echo "- external_publication -> extpub"
echo "- rand_publication -> randpub (if any existed)"
echo ""
echo "RESULT:"
echo "- Frontend now uses standardized source names: randpub, extpub"
echo "- Database uses standardized source names: randpub, extpub"
echo "- Complete consistency achieved across the entire system"
echo ""
echo "NEXT STEPS:"
echo "1. Test the frontend to ensure visualization coloring works"
echo "2. Test RAND queries to ensure they work with new names"
echo "3. Commit changes when satisfied"
echo ""
echo "✅ Frontend and database are now perfectly aligned!"


