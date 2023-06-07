import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.gtfs_pathways_validation import GTFSPathwaysValidation

from tdei_gtfs_csv_validator import gcv_test_release

DOWNLOAD_FILE_PATH = f'{Path.cwd()}/downloads/folder'


class TestGTFSPathwaysValidation(unittest.TestCase):
    def setUp(self):
        file_path = 'path/to/your/file.zip'  # Provide a valid file path here
        storage_client = MagicMock()
        storage_client.get_container = MagicMock()  # Mock the get_container method
        self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=storage_client)

    def tearDown(self):
        pass

    def test_is_gtfs_pathways_valid_valid(self):
        # Arrange
        self.validator.download_single_file = MagicMock(return_value='downloaded_file_path')
        gcv_test_release.test_release = MagicMock()  # Mock the gcv_test_release.test_release method
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, _ = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertTrue(is_valid)
        gcv_test_release.test_release.assert_called_once_with('gtfs_pathways', 'v1.0', 'downloaded_file_path')
        GTFSPathwaysValidation.clean_up.assert_called_once_with('downloaded_file_path')

    def test_is_gtfs_pathways_valid_invalid(self):
        # Arrange
        self.validator.download_single_file = MagicMock(return_value='downloaded_file_path')
        gcv_test_release.test_release = MagicMock(side_effect=Exception(
            'Validation failed'))  # Mock the gcv_test_release.test_release method to raise an exception
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)
        self.assertEqual(validation_message, 'Validation failed')
        gcv_test_release.test_release.assert_called_once_with('gtfs_pathways', 'v1.0', 'downloaded_file_path')
        GTFSPathwaysValidation.clean_up.assert_called_once_with('downloaded_file_path')

    def test_download_single_file(self):
        # Arrange
        file_upload_path = 'path/to/your/file.zip'  # Provide a valid file upload path here
        self.validator.storage_client.get_file_from_url = MagicMock()
        file = MagicMock()
        file.file_path = 'file_path.txt'
        file.get_stream = MagicMock(return_value=b'file_content')
        self.validator.storage_client.get_file_from_url.return_value = file

        # Act
        downloaded_file_path = self.validator.download_single_file(file_upload_path=file_upload_path)

        # Assert
        self.validator.storage_client.get_file_from_url.assert_called_once_with(self.validator.container_name,
                                                                                file_upload_path)
        file.get_stream.assert_called_once()
        with open(downloaded_file_path, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b'file_content')

    def test_clean_up_file(self):
        # Arrange
        path = 'file_path.txt'
        file_upload_path = 'path/to/your/file.zip'  # Provide a valid file upload path here
        self.validator.storage_client.get_file_from_url = MagicMock()
        file = MagicMock()
        file.file_path = 'file_path.txt'
        file.get_stream = MagicMock(return_value=b'file_content')
        self.validator.storage_client.get_file_from_url.return_value = file
        downloaded_file_path = self.validator.download_single_file(file_upload_path=file_upload_path)

        file.get_stream.assert_called_once()
        with open(downloaded_file_path, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b'file_content')

        # Act
        self.validator.clean_up(downloaded_file_path)

        # Assert
        self.assertFalse(os.path.exists(downloaded_file_path))

    def test_clean_up_folder(self):
        # Arrange
        is_exists = os.path.exists(DOWNLOAD_FILE_PATH)
        if not is_exists:
            os.makedirs(DOWNLOAD_FILE_PATH)
        path = 'folder'

        # Act
        self.validator.clean_up(path)

        # Assert
        self.assertFalse(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
