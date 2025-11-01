#!/bin/bash

# Code Migration Script for Database Schema Standardization
# This script helps migrate all code references from old field names to new standardized names
#
# IMPORTANT: Review all changes before applying! This script shows what would change.
# Run with --dry-run first to see what would change.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DRY_RUN=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--verbose]"
            echo "  --dry-run    Show what would change without making changes"
            echo "  --verbose    Show detailed output"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=== Database Schema Standardization - Code Migration Script ===${NC}"
echo "This script will migrate all code references to use standardized field names."
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE: No changes will be made${NC}"
    echo ""
fi

# Field mapping: old_name -> new_name (compatible with older bash/zsh)
# We'll use a simple approach with parallel arrays
OLD_NAMES=(
    "country2"
    "doi"
    "links"
    "country"
    "country_of_origin"
    "paper_id"
    "author_affiliations"
    "categories"
    "primary_category"
    "comment"
    "journal_ref"
    "category"
    "randpub_authors"
    "randpub_title"
    "randpub_abstract"
    "randpub_publication_date"
    "randpub_publication_type"
    "randpub_doi"
    "randpub_marc_id"
    "randpub_source_type"
    "randpub_document_type"
    "randpub_project"
    "randpub_links"
)

NEW_NAMES=(
    "aipickle_country"
    "aipickle_doi"
    "aipickle_links"
    "aipickle_country_alt"
    "aipickle_country_origin"
    "aipickle_paper_id"
    "aipickle_author_affiliations"
    "aipickle_categories"
    "aipickle_primary_category"
    "aipickle_comment"
    "aipickle_journal_ref"
    "aipickle_category"
    "rand_authors"
    "rand_title"
    "rand_abstract"
    "randpub_date"
    "rand_document_type"
    "rand_doi"
    "rand_marc_id"
    "rand_source_type"
    "rand_document_type"
    "rand_project"
    "rand_links"
)

# Function to find files that contain old field names
find_files_with_old_names() {
    echo -e "${BLUE}=== Finding files with old field names ===${NC}"
    
    local found_files=""
    
    for i in "${!OLD_NAMES[@]}"; do
        local old_name="${OLD_NAMES[$i]}"
        if [ "$VERBOSE" = true ]; then
            echo "Searching for: $old_name"
        fi
        
        # Find Python files containing the old field name
        local files=$(grep -l -r "$old_name" --include="*.py" . 2>/dev/null || true)
        
        if [ -n "$files" ]; then
            while IFS= read -r file; do
                if [[ ! "$found_files" =~ "$file" ]]; then
                    found_files="$found_files $file"
                fi
            done <<< "$files"
        fi
        
        # Also check SQL files
        local sql_files=$(grep -l -r "$old_name" --include="*.sql" . 2>/dev/null || true)
        if [ -n "$sql_files" ]; then
            while IFS= read -r file; do
                if [[ ! "$found_files" =~ "$file" ]]; then
                    found_files="$found_files $file"
                fi
            done <<< "$sql_files"
        fi
    done
    
    # Convert space-separated string to array
    local file_array=($found_files)
    echo "Found ${#file_array[@]} files that need updates:"
    for file in "${file_array[@]}"; do
        if [ -n "$file" ]; then
            echo "  - $file"
        fi
    done
    echo ""
    
    return "${#file_array[@]}"
}

# Function to show what would change in a file
show_changes_for_file() {
    local file="$1"
    
    echo -e "${BLUE}File: $file${NC}"
    
    for i in "${!OLD_NAMES[@]}"; do
        local old_name="${OLD_NAMES[$i]}"
        local new_name="${NEW_NAMES[$i]}"
        
        # Count occurrences
        local count=$(grep -c "$old_name" "$file" 2>/dev/null || echo "0")
        
        if [ "$count" -gt 0 ]; then
            echo "  $old_name -> $new_name ($count occurrences)"
            
            if [ "$VERBOSE" = true ]; then
                echo "    Context:"
                grep -n "$old_name" "$file" | head -3 | while IFS=: read -r line_num line_content; do
                    echo "      Line $line_num: ${line_content:0:80}..."
                done
            fi
        fi
    done
    echo ""
}

# Function to perform the actual migration
migrate_file() {
    local file="$1"
    
    echo -e "${BLUE}Migrating: $file${NC}"
    
    # Create backup
    local backup_file="${file}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$file" "$backup_file"
    echo "  Created backup: $backup_file"
    
    # Perform replacements
    for i in "${!OLD_NAMES[@]}"; do
        local old_name="${OLD_NAMES[$i]}"
        local new_name="${NEW_NAMES[$i]}"
        
        # Count before
        local before_count=$(grep -c "$old_name" "$file" 2>/dev/null || echo "0")
        
        if [ "$before_count" -gt 0 ]; then
            # Use sed to replace (handles special characters better than simple replacement)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/$old_name/$new_name/g" "$file"
            else
                # Linux
                sed -i "s/$old_name/$new_name/g" "$file"
            fi
            
            # Count after
            local after_count=$(grep -c "$old_name" "$file" 2>/dev/null || echo "0")
            local replaced_count=$((before_count - after_count))
            
            echo "  Replaced $replaced_count occurrences of $old_name -> $new_name"
        fi
    done
    
    echo "  Migration complete"
    echo ""
}

# Main execution
main() {
    echo "Starting code migration process..."
    echo ""
    
    # Find files that need updates
    local file_count
    find_files_with_old_names
    file_count=$?
    
    if [ "$file_count" -eq 0 ]; then
        echo -e "${GREEN}No files found that need updates!${NC}"
        exit 0
    fi
    
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}=== DRY RUN: Showing what would change ===${NC}"
        echo ""
        
        for file in $(find . -name "*.py" -o -name "*.sql" | grep -v __pycache__ | grep -v .git | sort); do
            if [ -f "$file" ]; then
                show_changes_for_file "$file"
            fi
        done
        
        echo -e "${YELLOW}DRY RUN COMPLETE${NC}"
        echo "To apply changes, run: $0"
        
    else
        echo -e "${GREEN}=== Performing actual migration ===${NC}"
        echo ""
        
        # Confirm before proceeding
        echo -e "${RED}WARNING: This will modify files in place!${NC}"
        echo "Make sure you have committed your current changes to git."
        echo ""
        read -p "Proceed with migration? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Proceeding with migration..."
            echo ""
            
            # Migrate each file
            for file in $(find . -name "*.py" -o -name "*.sql" | grep -v __pycache__ | grep -v .git | sort); do
                if [ -f "$file" ]; then
                    # Check if file contains any old field names
                    local needs_update=false
                    for i in "${!OLD_NAMES[@]}"; do
                        local old_name="${OLD_NAMES[$i]}"
                        if grep -q "$old_name" "$file" 2>/dev/null; then
                            needs_update=true
                            break
                        fi
                    done
                    
                    if [ "$needs_update" = true ]; then
                        migrate_file "$file"
                    fi
                fi
            done
            
            echo -e "${GREEN}=== Migration Complete! ===${NC}"
            echo ""
            echo "Next steps:"
            echo "1. Review the changes in each file"
            echo "2. Test your application thoroughly"
            echo "3. Run the database migration script"
            echo "4. Commit your changes to git"
            
        else
            echo "Migration cancelled."
            exit 0
        fi
    fi
}

# Run main function
main "$@"
