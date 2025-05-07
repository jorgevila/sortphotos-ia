import unittest
import os
from sortphotos import organize_files

class TestAllowedExtensions(unittest.TestCase):
    def setUp(self):
        """Set up test directories and files."""
        self.source_dir = "tests/test_files"
        self.destination_dir = "tests/output"
        self.allowed_extensions = [".jpg", ".jpeg", ".png", ".mp4", ".mov"]

        # Create test directories
        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(self.destination_dir, exist_ok=True)

        # Create test files
        self.test_files = {
            "test_image.jpg": True,
            "test_image.jpeg": True,
            "test_image.png": True,
            "test_video.mp4": True,
            "test_video.mov": True,
            "test_ignored.txt": False,
            "test_ignored.pdf": False,
        }

        for file_name in self.test_files:
            with open(os.path.join(self.source_dir, file_name), "w") as f:
                f.write("Test content")

    def tearDown(self):
        """Clean up test directories and files."""
        for root, dirs, files in os.walk(self.source_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        for root, dirs, files in os.walk(self.destination_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))

    def test_allowed_extensions(self):
        """Test that only files with allowed extensions are processed."""
        organize_files(
            source_dir=self.source_dir,
            destination_dir=self.destination_dir,
            ignored_tags=[],
            ignored_groups=[],
            allowed_extensions=self.allowed_extensions,
            copy=True,
            include_relative_path=False,
        )

        # Check which files were moved/copied
        processed_files = []
        for root, dirs, files in os.walk(self.destination_dir):
            for file in files:
                processed_files.append(file)

        # Verify that only allowed files were processed
        for file_name, is_allowed in self.test_files.items():
            # Check if the original filename (without prefix) is in any processed file
            matching_files = [processed_file for processed_file in processed_files if file_name in processed_file]
            if is_allowed:
                self.assertTrue(
                    matching_files,
                    f"{file_name} should have been processed, but no matching file was found."
                )
            else:
                self.assertFalse(
                    matching_files,
                    f"{file_name} should not have been processed, but a matching file was found."
                )

if __name__ == "__main__":
    unittest.main()