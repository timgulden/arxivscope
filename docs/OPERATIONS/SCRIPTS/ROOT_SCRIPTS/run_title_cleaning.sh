#!/bin/bash

echo "RAND Title Cleaning Script"
echo "=========================="
echo ""
echo "This script will clean up RAND paper titles by removing trailing ' /' and '.' characters."
echo "Found 66,354 RAND papers that need cleaning."
echo ""
echo "WARNING: This will update the database. Make sure you have a backup if needed."
echo ""
read -p "Do you want to proceed with cleaning the titles? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting title cleaning..."
    python clean_rand_titles_patch.py
    echo ""
    echo "Title cleaning complete!"
else
    echo "Title cleaning cancelled."
fi 