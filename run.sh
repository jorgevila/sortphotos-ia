#!/bin/bash

# Function to display help message
function show_help {
    echo "Usage: $0 <source_dir> <dest_dir> [OPTIONS]"
    echo ""
    echo "Automates duplicate removal and file sorting based on EXIF or filename date."
    echo ""
    echo "Required arguments:"
    echo "  source_dir          Source directory containing files."
    echo "  dest_dir            Destination directory where files will be organized."
    echo ""
    echo "Optional arguments:"
    echo "  --ignore-tags       EXIF tags to ignore (default: 'EXIF:CreateDate fileName')."
    echo "  --ignore-groups     EXIF groups to ignore (default: 'ICC_Profile MakerNotes IPTC')."
    echo "  --allowed-ext       File extensions to allow (default: '.jpg .jpeg .png .mp4 .mov')."
    echo "  --copy              Copy files instead of moving them."
    echo "  --include-relative-path Include the relative path in the filename."
    echo "  --cancel-remove-dups Skip duplicate removal (default: remove duplicates)."
    echo "  --help              Display this help message."
    echo ""
    echo "Example usage:"
    echo "  $0 /my/source /my/destination --ignore-tags 'ModifyDate' --ignore-groups 'File Composite' --allowed-ext '.jpg .png' --copy --include-relative-path --cancel-remove-dups"
    exit 0
}

# Check for --help argument
if [[ "$1" == "--help" ]]; then
    show_help
fi

# Ensure required arguments are provided
if [[ -z "$1" || -z "$2" ]]; then
    echo "Error: Missing required arguments."
    echo "Usage: $0 <source_dir> <dest_dir> [OPTIONS]"
    echo "Run '$0 --help' for more details."
    exit 1
fi

SOURCE_DIR="$1"
DEST_DIR="$2"
IGNORE_TAGS="${3:-'EXIF:CreateDate fileName'}"
IGNORE_GROUPS="${4:-'ICC_Profile MakerNotes IPTC'}"
ALLOWED_EXT="${5:-.png .jpg .avi .mp4 .3gp .mkv .JPG .m2ts .mov .AVI .NEF .jpeg .pdf .MOV .flv}"
COPY_MODE="${6:-false}"
INCLUDE_RELATIVE_PATH="${7:-true}"
REMOVE_DUPLICATES=true  # Default behavior is to remove duplicates

# Check for optional --cancel-remove-dups flag
for arg in "$@"; do
    if [[ "$arg" == "--cancel-remove-dups" ]]; then
        REMOVE_DUPLICATES=false
        break
    fi
done

LOG_FILE="/tmp/sortphotos.log"

# Step 1: Remove duplicate files using fdupes, excluding virtual environment directory
{
    echo "Remove empty directories in $SOURCE_DIR (excluding 'venv')..."
    find "$SOURCE_DIR" -mindepth 1 -type d -empty -not -path "*/venv/*" -exec rm -rvf {} +

    if [[ "$REMOVE_DUPLICATES" == "true" ]]; then
        echo "Removing duplicates in $SOURCE_DIR (excluding 'venv')..."
        find "$SOURCE_DIR" -type d -not -path "*venv*" -exec fdupes -rdN "{}" +
    else
        echo "Skipping duplicate removal as --cancel-remove-dups flag is set."
    fi

    # Extensions found
    echo "Extensions found"
    echo "<<<< extensions >>>>"
    find "$SOURCE_DIR" -type f | awk -F. '!a[$NF]++{print $NF}'
    echo "<<<< end extensions >>>>"

    echo "⚠️ Are you sure you want to continue? (y/n default: n)"
    read -r response

    if [[ "$response" == "y" ]]; then
        echo "✅ Proceeding..."
    else
        echo "❌ Cancelled."
        exit 1
    fi

    # Unzip all zip files and remove them
    echo "Unzip and remove zip files"
    find "$SOURCE_DIR" -type f -name "*.zip" -exec unzip -o {} -d $(dirname {}) \; -exec rm -v {} \;

    # Step 2: Locate requirements.txt relative to script location
    SCRIPT_DIR="$(dirname "$(realpath "$0")")"
    REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

    # Step 3: Set up virtual environment (if not exists)
    if [ ! -d "$SCRIPT_DIR/venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$SCRIPT_DIR/venv"
        source "$SCRIPT_DIR/venv/bin/activate"
        echo "Installing dependencies from $REQUIREMENTS_FILE..."
        pip install -r "$REQUIREMENTS_FILE"
    else
        echo "Activating virtual environment..."
        source "$SCRIPT_DIR/venv/bin/activate"
    fi

    # Step 4: Run sorting script with parsed arguments
    echo "Sorting files from $SOURCE_DIR to $DEST_DIR..."

    if [ "$COPY_MODE" == "true" ]; then
        COPY_FLAG="--copy"
    else
        COPY_FLAG=""
    fi

    if [ "$INCLUDE_RELATIVE_PATH" == "true" ]; then
        RELATIVE_PATH_FLAG="--include-relative-path"
    else
        RELATIVE_PATH_FLAG=""
    fi

    IFS=' ' read -r -a ALLOWED_EXT_ARRAY <<< "$ALLOWED_EXT"
    IFS=' ' read -r -a IGNORE_TAGS_ARRAY <<< "$IGNORE_TAGS"
    IFS=' ' read -r -a IGNORE_GROUPS_ARRAY <<< "$IGNORE_GROUPS"

    python "$SCRIPT_DIR/sortphotos.py" "$SOURCE_DIR" "$DEST_DIR" --ignore-tags "${IGNORE_TAGS_ARRAY[@]}" --ignore-groups "${IGNORE_GROUPS_ARRAY[@]}" --allowed-ext "${ALLOWED_EXT_ARRAY[@]}" $COPY_FLAG $RELATIVE_PATH_FLAG

    echo "Remove empty directories in $SOURCE_DIR..."
    find "$SOURCE_DIR" -mindepth 1 -type d -empty -not -path "*/venv/*" -exec rm -rvf {} +

    echo "Process complete!"
} 2>&1 | tee "$LOG_FILE"
