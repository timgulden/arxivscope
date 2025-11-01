#!/bin/bash

# Script to consolidate workspace by moving files from nested arxivscope-back-end to root level
echo "Consolidating workspace..."

# Move main application files (these should replace any existing ones)
echo "Moving main application files..."
cp arxivscope-back-end/dash_app_country.py ./
cp arxivscope-back-end/custom.css ./
cp arxivscope-back-end/custom.js ./
cp arxivscope-back-end/Dockerfile ./
cp arxivscope-back-end/final_df_country.pkl ./

# Move assets directory (merge if exists)
echo "Moving assets directory..."
if [ -d "assets" ]; then
    echo "Merging assets directory..."
    cp -r arxivscope-back-end/assets/* assets/ 2>/dev/null || true
else
    cp -r arxivscope-back-end/assets ./
fi

# Move requirements.txt (merge if needed)
echo "Merging requirements.txt..."
if [ -f "requirements.txt" ]; then
    echo "Backing up existing requirements.txt..."
    cp requirements.txt requirements_backup.txt
    # Combine requirements, removing duplicates
    cat requirements.txt arxivscope-back-end/requirements.txt | sort | uniq > requirements_combined.txt
    mv requirements_combined.txt requirements.txt
else
    cp arxivscope-back-end/requirements.txt ./
fi

# Move README.md (backup existing if different)
echo "Handling README.md..."
if [ -f "README.md" ]; then
    echo "Backing up existing README.md..."
    cp README.md README_backup.md
fi
cp arxivscope-back-end/README.md ./

# Move .gitignore (merge if needed)
echo "Merging .gitignore..."
if [ -f ".gitignore" ]; then
    echo "Backing up existing .gitignore..."
    cp .gitignore .gitignore_backup
    # Combine gitignore files, removing duplicates
    cat .gitignore arxivscope-back-end/.gitignore | sort | uniq > .gitignore_combined
    mv .gitignore_combined .gitignore
else
    cp arxivscope-back-end/.gitignore ./
fi

# Check if nested doc-ingestor has different content
echo "Checking nested doc-ingestor directory..."
if [ -d "arxivscope-back-end/doc-ingestor" ]; then
    echo "Nested doc-ingestor found. Checking for differences..."
    if [ "$(ls -A arxivscope-back-end/doc-ingestor)" ]; then
        echo "Nested doc-ingestor has content. Backing up..."
        cp -r arxivscope-back-end/doc-ingestor doc-ingestor_nested_backup
    fi
fi

# Remove the nested directory (after backing up everything)
echo "Removing nested directory..."
rm -rf arxivscope-back-end

echo "Consolidation complete!"
echo "Files moved to root level:"
echo "- dash_app_country.py"
echo "- custom.css"
echo "- custom.js"
echo "- Dockerfile"
echo "- final_df_country.pkl"
echo "- assets/ (merged)"
echo "- requirements.txt (merged)"
echo "- README.md (replaced)"
echo "- .gitignore (merged)"
echo ""
echo "Backup files created:"
echo "- requirements_backup.txt"
echo "- README_backup.md"
echo "- .gitignore_backup"
echo "- doc-ingestor_nested_backup/ (if nested had content)" 