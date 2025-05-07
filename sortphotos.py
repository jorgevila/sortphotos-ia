import os
import shutil
import hashlib
import re
import subprocess
import argparse
import json
from datetime import datetime
from collections import OrderedDict

TMP_DIR = "/tmp/sortphotos"  # Temporary directory for JSON files

# Ensure TMP_DIR exists
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR, exist_ok=True)

DATE_FORMATS = [
    "%Y:%m:%d %H:%M:%S",          # Standard EXIF format
    "%Y-%m-%d %H:%M:%S",          # ISO-like format
    "%Y/%m/%d %H:%M:%S",          # Slash-separated format
    "%Y:%m:%d %H:%M:%S%z",        # EXIF format with timezone
    "%Y-%m-%d %H:%M:%S%z",        # ISO format with timezone
    "%Y/%m/%d %H:%M:%S%z",        # Slash-separated with timezone
    "%Y-%m-%d",                   # Date only
    "%Y/%m/%d",                   # Date only with slashes
    "%d-%m-%Y %H:%M:%S",          # Day-Month-Year with time
    "%d/%m/%Y %H:%M:%S",          # Day/Month/Year with time
    "%d-%m-%Y",                   # Day-Month-Year
    "%d/%m/%Y",                   # Day/Month/Year
    "%Y-%m-%dT%H:%M:%S",          # ISO format with 'T' separator
]

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
    exiftool_cmd = ["exiftool", "-json", "-time:all", "-s", "-G", "-ImageWidth", "-ImageHeight", "-Duration", "-VideoStreamType", folder_path]
    result = subprocess.run(exiftool_cmd, capture_output=True, text=True)

    try:
        # Check if the output is valid JSON
        if not result.stdout.strip():
            raise RuntimeError(f"ExifTool returned no output for {folder_path}")
        
        json_data = json.loads(result.stdout)
        for file_data in json_data:
            file_path = file_data.get("SourceFile")
            dates = []
            image_width = None
            image_height = None
            duration = None
            video_stream_type = None

            # Extract date information and other attributes
            for key, value in file_data.items():
                #print(f"Processing {key}: {value}")
                # Ignore specified tags and groups
                if isinstance(value, str) and key.strip() not in ignored_tags:
                    group, tag = key.split(" ", 1) if " " in key else ("", key)
                    if group.strip() not in ignored_groups:
                        try:
                            # Attempt to parse the date value using multiple formats
                            for date_format in DATE_FORMATS:
                                try:
                                    parsed_date = datetime.strptime(value.strip(), date_format)
                                    # Normalize to offset-naive by removing timezone
                                    if parsed_date.tzinfo is not None:
                                        parsed_date = parsed_date.replace(tzinfo=None)
                                    dates.append(parsed_date)
                                    break  # Stop trying other formats once successful
                                except ValueError:
                                    continue  # Try the next format
                        except ValueError:
                            print(f"Warning: Invalid date format for {file_path}: {value}")
                            continue  # Skip invalid formats

                # Dynamically find and store specific attributes
                if "ImageWidth" in key:
                    image_width = value
                elif "ImageHeight" in key:
                    image_height = value
                elif "Duration" in key:
                    duration = value
                elif "VideoStreamType" in key:
                    video_stream_type = value
            
            # Store the metadata
            metadata[file_path] = {
                "Date": min(dates).isoformat() if dates else None,
                "Image Width": image_width,
                "Image Height": image_height,
                "Duration": duration,
                "Video Stream Type": video_stream_type
            }

        # Save metadata to a JSON file for fast lookup
        with open(json_path, "w") as json_file:
            json.dump(metadata, json_file, default=str)

    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON output from ExifTool for {folder_path}: {e}")
        return None
    except RuntimeError as e:
        print(e)
        return None

    return json_path

def get_exif_date(file_path, json_path):
    """Retrieve EXIF date from the cached JSON file and return it as a datetime object."""
    with open(json_path, "r") as json_file:
        metadata = json.load(json_file)

    # Retrieve the metadata for the specific file
    exif_data = metadata.get(file_path, {})
    
    # Ensure exif_data is a dictionary
    if not isinstance(exif_data, dict):
        print(f"Warning: Invalid metadata for {file_path}. Skipping EXIF date retrieval.")
        return None

    # Extract the 'Date' field
    date_str = exif_data.get("Date")
    if date_str:
        for date_format in DATE_FORMATS:
            try:
                # Attempt to parse the date string with the current format
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue  # Try the next format

        # If no format matches, print an error and return None
        print(f"Error parsing EXIF date for {file_path}: {date_str}")
        # print(exif_data)
    else:
        print(f"Warning: No EXIF date found for {file_path}")
    return None

def extract_date_from_filename(filename):
    """Attempts to extract a date from filename using an ordered map of patterns and multiple formats."""
    # Define common separators and base patterns
    separators = ["-", "_", r"\.", ""]  # Includes -, _, ., and no separator
    base_patterns = {
        r"(\d{4}{sep}\d{2}{sep}\d{2})": ["%Y{sep}%m{sep}%d"],  # YYYY-MM-DD, YYYY.MM.DD, YYYY_MM_DD
        r"(\d{2}{sep}\d{2}{sep}\d{4})": ["%d{sep}%m{sep}%Y"],  # DD-MM-YYYY, DD.MM.YYYY, DD_MM_YYYY
        r"(\d{2}{sep}\d{2}{sep}\d{2})": ["%m{sep}%d{sep}%y", "%d{sep}%m{sep}%y"],             # MM-DD-YY, DD-MM-YY (2-digit year)
        r"(\d{4}{sep}\d{2})": ["%Y{sep}%m"],                     # YYYY-MM, YYYY.MM, YYYY_MM
    }

    # Add static patterns for formats with text or fixed separators
    pattern_format_map = OrderedDict([
        (r"(\d{4})", ["%Y"]),  # Year only: YYYY
        (r"(\d{4}\s*Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec\s*\d{1,2})", ["%Y %b %d"]),  # YYYY Month DD
        (r"(\d{1,2}\s*Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec\s*\d{4})", ["%d %b %Y"]),  # DD Month YYYY
        (r"(\d{8})", ["%Y%m%d", "%d%m%Y"]),                                        # Compact format: YYYYMMDD
    ])

    # Dynamically generate patterns for base patterns with separators
    for base_pattern, formats in reversed(base_patterns.items()):
        for sep in separators:
            pattern = base_pattern.replace("{sep}", sep)
            base_formats = []
            for base_format in formats:
                format = base_format.replace("{sep}", sep)
                base_formats.append(format)
            pattern_format_map[pattern] = base_formats

    # Try to match each pattern and parse the date
    for pattern, date_formats in reversed(pattern_format_map.items()):
        match = re.search(pattern, filename, re.IGNORECASE)
        # print(f"Trying pattern: {pattern} in {filename}")
        # print(f"Match: {match}")
        # print(f"Date formats: {date_formats}")
        # If a match is found, extract the date components
        # and try to parse them with the corresponding formats
        if match:
            for date_format in date_formats:
                # print(f"Trying date format: {date_format}")
                # Extract the matched groups and join them with the appropriate separator
                try:
                    # Join groups with appropriate separators if needed
                    date_string = "".join(match.groups())
                    parsed_date = datetime.strptime(date_string, date_format)
                    # print(f"Parsed date: {parsed_date}")
                    # Validate the date (must be greater than 1950 or less than today)
                    today = datetime.now()
                    if parsed_date.year > 1950 and parsed_date < today:
                        return parsed_date
                except ValueError as e:
                    print(f"Error parsing date with format {date_format}: {e}")
                    continue  # Try the next format for this pattern

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

def move_or_copy_file(file_path, target_dir, file_date, json_path, source_dir, include_relative_path=False, copy=False):
    """Moves or copies file to correct 'year-month-day' directory, prefixing date, dimensions, duration, codec, or relative path to filename."""
    os.makedirs(target_dir, exist_ok=True)
    md5_hash = get_md5(file_path)

    original_filename = os.path.basename(file_path)
    date_prefix = file_date.strftime("%Y-%m-%d")

    # Check if the file date is in the future
    today = datetime.now()
    if file_date > today:
        print(f"Error: File {file_path} has a future date ({date_prefix}). Skipping.")
        return

    # Extract metadata from EXIF JSON
    metadata_info = ""
    with open(json_path, "r") as json_file:
        metadata = json.load(json_file)
        exif_data = metadata.get(file_path, {})

        # Ensure exif_data is a dictionary
        if not isinstance(exif_data, dict):
            print(f"Warning: Invalid metadata for {file_path}. Skipping file.")
            return

        # Check if the file is an image and extract dimensions
        image_width = exif_data.get("Image Width")
        image_height = exif_data.get("Image Height")
        if image_width and image_height:
            metadata_info = f"_{image_width}x{image_height}"

        # Check if the file is a video and extract duration and codec
        duration = exif_data.get("Duration")
        codec = exif_data.get("Video Stream Type")
        if duration:
            metadata_info = f"{metadata_info}_{duration.replace(':', '-')}"  # Replace colons with dashes for filename safety
        if codec:
            metadata_info = f"{metadata_info}_{codec.replace('/', '-').replace(' ', '_')}"  # Replace slashes and spaces for filename safety

    # Include relative path in the filename if the option is enabled
    relative_path_info = ""
    if include_relative_path:
        relative_path = os.path.relpath(os.path.dirname(file_path), source_dir)
        relative_path_info = f"_{relative_path.replace(os.sep, '_')}"  # Replace path separators with underscores

    # Construct the new filename
    new_filename = f"{date_prefix}{metadata_info}{relative_path_info}_{original_filename}"
    new_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', new_filename)  # Sanitize filename
    new_filename = re.sub(r'_{2,}', '_', new_filename)  # Remove duplicate underscores
    new_filename = new_filename[:255]  # Limit filename length to 255 characters
    new_filename = new_filename.strip('_')  # Remove trailing underscores

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

def organize_files(source_dir, destination_dir, ignored_tags, ignored_groups, allowed_extensions, copy=False, include_relative_path=False):
    """Processes all files recursively, caching EXIF data first."""
    moved_count = 0
    skipped_count = 0
    error_count = 0

    for root, dirs, files in os.walk(source_dir):
        # Skip 'venv' directories
        if "venv" in dirs:
            print(f"Skipping 'venv' directory in {root}")
            dirs.remove("venv")  # Prevent descending into 'venv'
        if "." in dirs:
            print(f"Skipping '.' directory in {root}")
            dirs.remove(".")  # Prevent descending into '.'

        json_path = extract_exif_metadata(root, ignored_tags, ignored_groups)  # Cache EXIF data per subfolder

        for file_name in files:
            file_path = os.path.join(root, file_name)

            # Allow only files with specified extensions
            if not any(file_name.lower().endswith(ext.lower()) for ext in allowed_extensions):
                print(f"Skipping {file_name}: Not an allowed extension in {allowed_extensions}")                
                skipped_count += 1
                continue  # Skip files with disallowed extensions

            if os.path.isfile(file_path):
                try:
                    exif_date = get_exif_date(file_path, json_path)
                    
                    filename_date = extract_date_from_filename(
                        os.path.relpath(file_path, source_dir) if include_relative_path else file_name
                    )

                    # Use the oldest available date
                    file_date = min(filter(None, [exif_date, filename_date]), default=None)

                    if file_date:
                        target_dir = os.path.join(destination_dir, f"{file_date.year}-{file_date.month:02d}-{file_date.day:02d}")
                        move_or_copy_file(file_path, target_dir, file_date, json_path, source_dir, include_relative_path, copy)
                        moved_count += 1
                    else:
                        print(f"Skipping {file_path}: No valid date found. [{exif_date}, {filename_date}]")
                        skipped_count += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    error_count += 1

    # Print summary statistics
    print("\nSummary:")
    print(f"Moved files: {moved_count}")
    print(f"Skipped files: {skipped_count}")
    print(f"Errors: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize files by oldest EXIF or filename date.")
    parser.add_argument("source_dir", help="Source directory containing files.")
    parser.add_argument("destination_dir", help="Destination directory where files will be organized.")
    parser.add_argument("--ignore-tags", nargs="*", default=[], help="EXIF tags to ignore")
    parser.add_argument("--ignore-groups", nargs="*", default=[], help="EXIF groups to ignore")
    parser.add_argument("--allowed-ext", nargs="*", default=[".jpg", ".jpeg", ".png", ".mp4", ".mov"], help="File extensions to allow")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of moving them.")
    parser.add_argument("--include-relative-path", action="store_true", help="Include the relative path in the filename.")
    args = parser.parse_args()

    # Log the arguments used
    print("\nArguments used:")
    print(f"Source directory: {args.source_dir}")
    print(f"Destination directory: {args.destination_dir}")
    print(f"Ignore tags: {args.ignore_tags}")
    print(f"Ignore groups: {args.ignore_groups}")
    print(f"Allowed extensions: {args.allowed_ext}")
    print(f"Copy mode: {args.copy}")
    print(f"Include relative path: {args.include_relative_path}\n")

    organize_files(
        args.source_dir,
        args.destination_dir,
        args.ignore_tags,
        args.ignore_groups,
        args.allowed_ext,
        args.copy,
        args.include_relative_path
    )
