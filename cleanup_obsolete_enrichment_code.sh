#!/bin/bash

# Cleanup Obsolete Enrichment Code
# This script removes obsolete Python modules, test files, and scripts
# that reference the dropped enrichment tables

set -e  # Exit on any error

echo "🧹 Cleaning up obsolete enrichment code..."
echo "=========================================="
echo ""

echo "📋 Files to be removed:"
echo "1. Obsolete Python modules:"
echo "   - openalex_country_enrichment_enhanced.py"
echo "   - openalex_country_enrichment_three_phase.py"
echo ""
echo "2. Obsolete test files:"
echo "   - test_enhanced_approach.py"
echo "   - test_three_phase_*.py (all three-phase test files)"
echo "   - test_functional_vs_original.py"
echo "   - test_pure_functional.py"
echo ""
echo "3. Obsolete scripts:"
echo "   - check_remaining_papers.py"
echo "   - run_enhanced_enrichment_production_DEPRECATED.py"
echo "   - country_enrichment_correct.py"
echo "   - apply_simplified_countries.py"
echo "   - openalex_country_enrichment_optimized.py"
echo ""
echo "4. Legacy test files:"
echo "   - docs/LEGACY/SCRIPTS/test_country_enrichment_sample.py"
echo ""

# Confirm before proceeding
read -p "Are you sure you want to remove these obsolete files? Type 'YES' to confirm: " confirmation
if [ "$confirmation" != "YES" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🗑️  Starting cleanup process..."

# Function to safely remove files
remove_file() {
    if [ -f "$1" ]; then
        echo "   Removing: $1"
        rm "$1"
    else
        echo "   File not found: $1"
    fi
}

# Function to safely remove directories
remove_dir() {
    if [ -d "$1" ]; then
        echo "   Removing directory: $1"
        rm -rf "$1"
    else
        echo "   Directory not found: $1"
    fi
}

echo ""
echo "📁 Step 1: Removing obsolete Python modules..."

# Remove obsolete enrichment modules
remove_file "embedding-enrichment/openalex_country_enrichment_enhanced.py"
remove_file "embedding-enrichment/openalex_country_enrichment_three_phase.py"

echo ""
echo "🧪 Step 2: Removing obsolete test files..."

# Remove obsolete test files
remove_file "embedding-enrichment/test_enhanced_approach.py"
remove_file "embedding-enrichment/test_three_phase_comprehensive.py"
remove_file "embedding-enrichment/test_three_phase_simple_validation.py"
remove_file "embedding-enrichment/test_three_phase_final_validation.py"
remove_file "embedding-enrichment/test_functional_vs_original.py"
remove_file "embedding-enrichment/test_pure_functional.py"

echo ""
echo "📜 Step 3: Removing obsolete scripts..."

# Remove obsolete scripts
remove_file "embedding-enrichment/check_remaining_papers.py"
remove_file "embedding-enrichment/run_enhanced_enrichment_production_DEPRECATED.py"
remove_file "embedding-enrichment/country_enrichment_correct.py"
remove_file "embedding-enrichment/apply_simplified_countries.py"
remove_file "embedding-enrichment/openalex_country_enrichment_optimized.py"

echo ""
echo "📚 Step 4: Removing legacy test files..."

# Remove legacy test files
remove_file "docs/LEGACY/SCRIPTS/test_country_enrichment_sample.py"

echo ""
echo "🔍 Step 5: Verifying cleanup..."

# Check if any references remain
echo "   Checking for remaining references to obsolete modules..."
remaining_refs=$(grep -r "openalex_country_enrichment_enhanced\|openalex_country_enrichment_three_phase" . --exclude-dir=".git" --exclude-dir="__pycache__" --exclude="*.pyc" --exclude="*.pyo" --exclude="cleanup_obsolete_enrichment_code.sh" || true)

if [ -n "$remaining_refs" ]; then
    echo "   ⚠️  Found remaining references:"
    echo "$remaining_refs"
    echo ""
    echo "   These may need manual cleanup or are in documentation."
else
    echo "   ✅ No remaining code references found"
fi

echo ""
echo "📊 Step 6: Checking current enrichment system..."

# Verify the current system still works
echo "   Current enrichment tables:"
psql -h localhost -U tgulden -d doctrove -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%openalex%' ORDER BY table_name;" 2>/dev/null || echo "   (Database connection not available)"

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "🎯 What was removed:"
echo "   - Obsolete enrichment modules (enhanced, three-phase)"
echo "   - Obsolete test files (all three-phase tests)"
echo "   - Obsolete scripts (deprecated enrichment runners)"
echo "   - Legacy test files"
echo ""
echo "🎯 What remains (working system):"
echo "   - openalex_enrichment_country table (UUID type, correct)"
echo "   - Current field definitions pointing to working table"
echo "   - Functional enrichment framework"
echo ""
echo "🚀 Next steps:"
echo "   1. Restart the API server to clear any cached references"
echo "   2. Test the universe filter - it should now work properly"
echo "   3. The system is now cleaner and more maintainable"


