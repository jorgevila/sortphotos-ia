#!/bin/bash

# Ensure source and destination directories are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source_dir> <dest_dir>"
    exit 1
fi

SOURCE_DIR="$1"
DEST_DIR="$2"

# Step 1: Remove duplicate files using fdupes
echo "Removing duplicates in $SOURCE_DIR..."
fdupes -rdN "$SOURCE_DIR"

# Step 2: Set up virtual environment (if not exists)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Step 3: Run sorting script
echo "Sorting files from $SOURCE_DIR to $DEST_DIR..."
python sortphotos.py "$SOURCE_DIR" "$DEST_DIR" --ignore-tags ModifyDate CreateDate --ignore-groups File Composite --ignore-ext .txt .pdf --copy

echo "Process complete!"
