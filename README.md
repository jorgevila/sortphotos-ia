# SortPhotos-IA

SortPhotos-IA is a Python-based tool designed to organize photos and files by their oldest available date, extracted from EXIF metadata or filenames. The project helps you clean up and structure your photo library by moving or copying files into organized directories based on their dates.

## Features

- Extracts EXIF metadata using `exiftool` to determine file dates.
- Falls back to extracting dates from filenames if EXIF data is unavailable.
- Organizes files into directories named by date (`YYYY-MM-DD`).
- Ensures no duplicate files are moved or copied by comparing MD5 checksums.
- Supports ignoring specific EXIF tags, groups, or file extensions.
- Option to copy files instead of moving them.

## Requirements

The project requires the following dependencies, which are listed in the `requirements.txt` file:

- `exiftool`
- `shutil`
- `hashlib`
- `re`
- `subprocess`
- `argparse`
- `json`
- `datetime`

## Installation

1. Clone the repository to your local machine.
2. Ensure you have Python 3 installed.
3. Run the `run.sh` script to set up a virtual environment and install dependencies.

```bash
bash run.sh <source_dir> <dest_dir>
```

## Usage

The main script is `sortphotos.py`, which organizes files based on their dates. You can run it directly or use the `run.sh` script for a streamlined process.

### Command-Line Arguments

- `source_dir`: The source directory containing files to organize.
- `destination_dir`: The destination directory where organized files will be stored.
- `--ignore-tags`: EXIF tags to ignore (e.g., `ModifyDate`, `CreateDate`).
- `--ignore-groups`: EXIF groups to ignore (e.g., `File`, `Composite`).
- `--ignore-ext`: File extensions to ignore (e.g., `.txt`, `.pdf`).
- `--copy`: Copy files instead of moving them.

### Example

```bash
python sortphotos.py /path/to/source /path/to/destination --ignore-tags ModifyDate CreateDate --ignore-groups File Composite --ignore-ext .txt .pdf --copy
```

## Workflow

1. **Remove Duplicates**: The `run.sh` script uses `fdupes` to remove duplicate files in the source directory.
2. **Set Up Environment**: A virtual environment is created, and dependencies are installed.
3. **Organize Files**: Files are sorted into date-based directories in the destination folder.

## Notes

- Ensure `exiftool` is installed on your system, as it is required for extracting EXIF metadata.
- The script skips files with ignored extensions or without valid dates.

## License

This project is licensed under the MIT License.
