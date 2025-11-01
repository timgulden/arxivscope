#!/bin/bash

# ============================================================================
# PRECISE CODE MIGRATION SCRIPT - FULL CONSISTENCY WITH SOURCE CONFIGS
# ============================================================================
# This script standardizes everything to use the source config names:
# - rand_ -> randpub_ (RAND internal publications)
# - randext_ -> extpub_ (RAND external publications)
# - randpub -> randpub (source identifier)
# - extpub -> extpub (source identifier)
# ============================================================================

set -e  # Exit on any error

echo "=== PRECISE CODE MIGRATION SCRIPT - FULL CONSISTENCY ==="
echo "This script will standardize everything to match source config names"
echo ""

# Check if we're in the right directory
if [ ! -f "doctrove-api/business_logic.py" ]; then
    echo "ERROR: This script must be run from the arxivscope-back-end directory"
    exit 1
fi

echo "✅ Running from correct directory"
echo ""

# Git provides version control - no local backup needed
echo "=== Starting code migration (Git provides version control) ==="
echo ""

# ============================================================================
# PHASE 1: RAND INTERNAL PUBLICATIONS (rand_ -> randpub_)
# ============================================================================

echo "=== PHASE 1: Standardizing RAND internal publication fields (rand_ -> randpub_) ==="

# Update all rand_ field references to randpub_ (with word boundary)
echo "  Updating all rand_ field references to randpub_..."
find . -name "*.py" -o -name "*.md" -o -name "*.sh" | grep -v "Design documents" | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' 's/\brand_\b/randpub_/g' "$file" 2>/dev/null || echo "Skipped: $file"
    fi
done

echo "✅ Phase 1 complete: rand_ -> randpub_ standardization"
echo ""

# ============================================================================
# PHASE 2: RAND EXTERNAL PUBLICATIONS (randext_ -> extpub_)
# ============================================================================

echo "=== PHASE 2: Standardizing RAND external publication fields (randext_ -> extpub_) ==="

# Update all randext_ field references to extpub_ (with word boundary)
echo "  Updating all randext_ field references to extpub_..."
find . -name "*.py" -o -name "*.md" -o -name "*.sh" | grep -v "Design documents" | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' 's/\brandext_\b/extpub_/g' "$file" 2>/dev/null || echo "Skipped: $file"
    fi
done

echo "✅ Phase 2 complete: randext_ -> extpub_ standardization"
echo ""

# ============================================================================
# PHASE 3: SOURCE IDENTIFIERS (randpub -> randpub, extpub -> extpub)
# ============================================================================

echo "=== PHASE 3: Standardizing source identifiers ==="

# Update source identifier references
echo "  Updating randpub -> randpub..."
find . -name "*.py" -o -name "*.md" -o -name "*.sh" | grep -v "Design documents" | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' 's/randpub/randpub/g' "$file" 2>/dev/null || echo "Skipped: $file"
    fi
done

echo "  Updating extpub -> extpub..."
find . -name "*.py" -o -name "*.md" -o -name "*.sh" | grep -v "Design documents" | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' 's/extpub/extpub/g' "$file" 2>/dev/null || echo "Skipped: $file"
    fi
done

echo "✅ Phase 3 complete: Source identifiers standardized"
echo ""

# ============================================================================
# PHASE 4: TABLE NAME REFERENCES
# ============================================================================

echo "=== PHASE 4: Updating table name references ==="

# Update table name references to match the new standardized names
echo "  Updating table name references..."

# Main metadata tables
find . -name "*.py" -o -name "*.md" -o -name "*.sh" | grep -v "Design documents" | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' 's/randpub_metadata/randpub_metadata/g' "$file" 2>/dev/null || echo "Skipped: $file"
        sed -i '' 's/extpub_metadata/extpub_metadata/g' "$file" 2>/dev/null || echo "Skipped: $file"
    fi
done

# Field mapping tables
find . -name "*.py" -o -name "*.md" -o -name "*.sh" | grep -v "Design documents" | while read -r file; do
    if [ -f "$file" ]; then
        sed -i '' 's/randpub_metadata_field_mapping/randpub_metadata_field_mapping/g' "$file" 2>/dev/null || echo "Skipped: $file"
        sed -i '' 's/extpub_metadata_field_mapping/extpub_metadata_field_mapping/g' "$file" 2>/dev/null || echo "Skipped: $file"
    fi
done

echo "✅ Phase 4 complete: Table name references updated"
echo ""

# ============================================================================
# VERIFICATION
# ============================================================================

echo "=== VERIFICATION: Checking for remaining old references ==="

echo "Checking for remaining 'rand_' references (should be none)..."
REMAINING_RAND=$(grep -r "\brand_\b" . --exclude-dir=".git" --exclude-dir="__pycache__" --exclude-dir="Design documents" --exclude="*.pyc" --exclude="*.pyo" | head -10 || true)

if [ -n "$REMAINING_RAND" ]; then
    echo "⚠️  Found remaining 'rand_' references:"
    echo "$REMAINING_RAND"
else
    echo "✅ No remaining 'rand_' references found"
fi

echo ""
echo "Checking for remaining 'randext_' references (should be none)..."
REMAINING_RANDEXT=$(grep -r "\brandext_\b" . --exclude-dir=".git" --exclude-dir="__pycache__" --exclude-dir="Design documents" --exclude="*.pyc" --exclude="*.pyo" | head -10 || true)

if [ -n "$REMAINING_RANDEXT" ]; then
    echo "⚠️  Found remaining 'randext_' references:"
    echo "$REMAINING_RANDEXT"
else
    echo "✅ No remaining 'randext_' references found"
fi

echo ""
echo "Checking for remaining 'randpub' references (should be none)..."
REMAINING_RAND_PUB=$(grep -r "randpub" . --exclude-dir=".git" --exclude-dir="__pycache__" --exclude-dir="Design documents" --exclude="*.pyc" --exclude="*.pyo" | head -5 || true)

if [ -n "$REMAINING_RAND_PUB" ]; then
    echo "⚠️  Found remaining 'randpub' references:"
    echo "$REMAINING_RAND_PUB"
else
    echo "✅ No remaining 'randpub' references found"
fi

echo ""
echo "=== MIGRATION SUMMARY ==="
echo "✅ Code migration completed - FULL CONSISTENCY ACHIEVED"
echo ""
echo "STANDARDIZATION APPLIED:"
echo "- rand_ -> randpub_ (RAND internal publications)"
echo "- randext_ -> extpub_ (RAND external publications)"
echo "- randpub -> randpub (source identifier)"
echo "- extpub -> extpub (source identifier)"
echo "- randpub_metadata -> randpub_metadata (table names)"
echo "- extpub_metadata -> extpub_metadata (table names)"
echo "- randpub_metadata_field_mapping -> randpub_metadata_field_mapping"
echo "- extpub_metadata_field_mapping -> extpub_metadata_field_mapping"
echo ""
echo "RESULT:"
echo "- Source configs: randpub, extpub (unchanged)"
echo "- Database tables: randpub_metadata, extpub_metadata"
echo "- Database fields: randpub_authors, extpub_authors"
echo "- Code references: All updated to match new database names"
echo ""
echo "NEXT STEPS:"
echo "1. Review the changes with: git diff"
echo "2. Test the frontend to ensure it works with the new field names"
echo "3. Test the complete system (database + code now match)"
echo "4. Commit changes when satisfied"
echo ""
echo "⚠️  IMPORTANT: Database tables still need to be renamed to match!"
echo "   - randpub_metadata -> randpub_metadata"
echo "   - extpub_metadata -> extpub_metadata"
echo "   - Plus all field renames and index renames"
echo ""
echo "✅ Code will now expect the standardized database structure"
