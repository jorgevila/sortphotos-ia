import unittest
from datetime import datetime
from sortphotos import extract_date_from_filename

class TestExtractDateFromFilename(unittest.TestCase):
    def test_compact_format(self):
        filename = "31122016-_DSC4310.jpg"
        expected_date = datetime(2016, 12, 31)
        self.assertEqual(extract_date_from_filename(filename), expected_date)

    def test_yyyy_mm_dd_format(self):
        filename = "photo_2023-05-09.jpg"
        expected_date = datetime(2023, 5, 9)
        self.assertEqual(extract_date_from_filename(filename), expected_date)

    def test_dd_mm_yyyy_format(self):
        filename = "document_09-05-2023.pdf"
        expected_date = datetime(2023, 5, 9)
        self.assertEqual(extract_date_from_filename(filename), expected_date)

    def test_compact_yyyymmdd_format(self):
        filename = "event_20230509.png"
        expected_date = datetime(2023, 5, 9)
        self.assertEqual(extract_date_from_filename(filename), expected_date)

    def test_custom_format(self):
        filename = "Cesaraugusto05052014-2.jpg"
        expected_date = datetime(2014, 5, 5)
        self.assertEqual(extract_date_from_filename(filename), expected_date)

    def test_no_valid_date(self):
        filename = "random_file_name.jpg"
        self.assertIsNone(extract_date_from_filename(filename))

if __name__ == "__main__":
    unittest.main()