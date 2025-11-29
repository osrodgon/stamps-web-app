#!/bin/bash

# --- Django Migration Cleanup Script ---
#
# This script deletes all files inside the 'migrations' folders of all
# your Django apps, *except* for the essential '__init__.py' files.
#
# USAGE: 
# 1. Save this file as 'clean_migrations.sh' in your project root.
# 2. Make it executable: chmod +x clean_migrations.sh
# 3. Run it: ./clean_migrations.sh
# ----------------------------------------

echo "Starting Django migration cleanup..."

# Find all 'migrations' directories recursively
find . -type d -name "migrations" -print0 | while IFS= read -r -d $'\0' dir; do
    echo "Processing directory: $dir"
    
    # Check if the directory is valid and not a virtual environment directory
    if [[ "$dir" != *"venv"* ]] && [[ "$dir" != *".git"* ]]; then
        
        # Find and delete all files in the directory *except* __init__.py
        # -mindepth 1 ensures we don't try to delete the directory itself
        # -not -name '__init__.py' excludes the init file
        # -delete performs the deletion
        find "$dir" -mindepth 1 -type f -not -name "__init__.py" -delete
        
        # Count remaining files (should only be __init__.py)
        remaining_files=$(ls -A "$dir" | wc -l)
        if [ "$remaining_files" -eq 1 ] || [ "$remaining_files" -eq 0 ]; then
            echo "  -> Cleaned successfully (only __init__.py remains, or directory was empty)."
        else
            echo "  -> WARNING: Directory still contains unexpected files!"
            ls "$dir"
        fi
    fi
done

echo "---"
echo "Migration cleanup complete. Remaining steps:"
echo "1. DELETE your existing database file (e.g., db.sqlite3)."
echo "2. Run: python manage.py makemigrations"
echo "3. Run: python manage.py migrate"
echo "4. Run: python manage.py createsuperuser"
