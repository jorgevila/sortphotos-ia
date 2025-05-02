import os
import shutil
import hashlib
import re
import subprocess
import argparse
import json
from datetime import datetime

TMP_DIR = "/tmp"

def get_md5(file_path):
    """Compute the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_exif_metadata(folder_path, ignored_tags, ignored_groups):
    """Extract EXIF metadata for all files in a subfolder and store it in a JSON file."""
    metadata = {}
    json_path = os.path.join(TMP_DIR, f"exif_metadata_{os.path.basename(folder_path)}.json")

    # Run ExifTool for all files at once
    exiftool_cmd = ["exiftool", "-json", "-time:all", "-s", "-G", folder_path]
    result = subprocess.run(exiftool_cmd, capture_output=True, text=True)

    try:
        json_data = json.loads(result.stdout)
        for file_data in json_data:
            file_path = file_data.get("SourceFile")
            dates = []

            for key, value in file_data.items():
                if isinstance(value, str) and key.strip() not in ignored_tags:
                    group, tag = key.split(" ", 1) if " " in key else ("", key)
                    if group.strip() not in ignored_groups:
                        try:
                            dates.append(datetime.strptime(value.strip(), "%Y:%m:%d %H:%M:%S"))
                        except ValueError:
                            continue  # Skip invalid formats
            
            metadata[file_path] = min(dates) if dates else None

        # Save metadata to a JSON file for fast lookup
        with open(json_path, "w") as json_file:
            json.dump(metadata, json_file, default=str)

    except json.JSONDecodeError:
        print(f"Error extracting EXIF data for {folder_path}")
    
    return json_path

def get_exif_date(file_path, json_path):
    """Retrieve EXIF date from the cached JSON file."""
    with open(json_path, "r") as json_file:
        metadata = json.load(json_file)

    return metadata.get(file_path)

def extract_date_from_filename(filename):
    """Attempts to extract a date from filename using multiple formats."""
    patterns = [
        r"(\d{4})[-_\.]?(\d{2})[-_\.]?(\d{2})",    # YYYY-MM-DD, YYYY.MM.DD, YYYY_MM_DD
        r"(\d{2})[-_\.]?(\d{2})[-_\.]?(\d{4})",    # DD-MM-YYYY, DD.MM.YYYY, DD_MM_YYYY
        r"(\d{2})[-_\.]?(\d{2})[-_\.]?(\d{2})",    # MM-DD-YY, DD-MM-YY (2-digit year)
        r"(\d{8})",                                # YYYYMMDD, DDMMYYYY, MMDDYYYY
        r"(\d{4})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})",  # YYYY Month DD
        r"(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})"  # DD Month YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            try:
                return datetime.strptime(" ".join(match.groups()), "%Y %m %d") if len(match.groups()) == 3 else datetime.strptime(match.group(1), "%Y%m%d")
            except ValueError:
                continue  # Skip invalid matches

    return None

def get_unique_filename(target_dir, filename, md5_hash):
    """Ensures uniqueness: same name with different MD5 gets suffixed."""
    base_name, ext = os.path.splitext(filename)
    counter = 1

    while True:
        target_path = os.path.join(target_dir, filename)
        if not os.path.exists(target_path):
            return target_path  # File doesn't exist, safe to move
        
        existing_md5 = get_md5(target_path)
        if existing_md5 == md5_hash:
            print(f"Skipping {filename}: Identical MD5 already exists.")
            return None  # File already exists, identical content

        filename = f"{base_name}_{counter}{ext}"
        counter += 1

def move_or_copy_file(file_path, target_dir, file_date, copy=False):
    """Moves or copies file to correct 'year-month-day' directory, prefixing date to filename."""
    os.makedirs(target_dir, exist_ok=True)
    md5_hash = get_md5(file_path)

    original_filename = os.path.basename(file_path)
    date_prefix = file_date.strftime("%Y-%m-%d")
    new_filename = f"{date_prefix}_{original_filename}"
    
    target_path = get_unique_filename(target_dir, new_filename, md5_hash)
    if target_path:
        if copy:
            shutil.copy2(file_path, target_path)
            print(f"Copied {file_path} -> {target_path}")
        else:
            shutil.move(file_path, target_path)
            print(f"Moved {file_path} -> {target_path}")
    else:
        print(f"Skipping {file_path}: Duplicate detected.")

def organize_files(source_dir, destination_dir, ignored_tags, ignored_groups, ignored_extensions, copy=False):
    """Processes all files recursively, caching EXIF data first."""
    for root, _, files in os.walk(source_dir):
        json_path = extract_exif_metadata(root, ignored_tags, ignored_groups)  # Cache EXIF data per subfolder

        for file_name in files:
            file_path = os.path.join(root, file_name)

            if any(file_name.lower().endswith(ext.lower()) for ext in ignored_extensions):
                print(f"Skipping {file_name}: Ignored extension.")
                continue  # Skip ignored extensions
            
            if os.path.isfile(file_path):
                exif_date = get_exif_date(file_path, json_path)
                filename_date = extract_date_from_filename(file_name)

                # Use the oldest available date
                file_date = min(filter(None, [exif_date, filename_date]), default=None)

                if file_date:
                    target_dir = os.path.join(destination_dir, f"{file_date.year}-{file_date.month:02d}-{file_date.day:02d}")
                    move_or_copy_file(file_path, target_dir, file_date, copy)
                else:
                    print(f"Skipping {file_name}: No valid date found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize files by oldest EXIF or filename date.")
    parser.add_argument("source_dir", help="Source directory containing files.")
    parser.add_argument("destination_dir", help="Destination directory for sorted files.")
    parser.add_argument("--ignore-tags", nargs="*", default=[], help="EXIF tags to ignore")
    parser.add_argument("--ignore-groups", nargs="*", default=[], help="EXIF groups to ignore")
    parser.add_argument("--ignore-ext", nargs="*", default=[], help="File extensions to ignore")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of moving them.")
    args = parser.parse_args()

    organize_files(args.source_dir, args.destination_dir, args.ignore_tags, args.ignore_groups, args.ignore_ext, args.copy)
