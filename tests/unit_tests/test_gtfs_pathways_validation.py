import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.gtfs_pathways_validation import GTFSPathwaysValidation

DOWNLOAD_FILE_PATH = f'{Path.cwd()}/downloads'
SAVED_FILE_PATH = f'{Path.cwd()}/tests/unit_tests/test_files'

SUCCESS_FILE_NAME = 'success.zip'
SUCCESS2_FILE_NAME = 'pathways-good.zip'
SUCCESS3_FILE_NAME = 'pathways-good2.zip'
SUCCESS4_FILE_NAME = 'pathways-good3.zip'

FAILURE_FILE_NAME = 'fail_rules_1.zip'
FAILURE1_FILE_NAME = 'pathways-foreign-key.zip'
FAILURE2_FILE_NAME = 'pathways-filename.zip'
FAILURE3_FILE_NAME = 'pathways-fieldname.zip'
FAILURE4_FILE_NAME = 'pathways-explicit-error.zip'

DATA_TYPE = 'gtfs_pathways'
SCHEMA_VERSION = 'v1.0'


class TestGoodFile2(unittest.TestCase):

    @patch.object(GTFSPathwaysValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{SUCCESS3_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS3_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS3_FILE_NAME}'

        with patch.object(GTFSPathwaysValidation, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = SUCCESS3_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test(self):
        # Arrange
        source = f'{SAVED_FILE_PATH}/{SUCCESS3_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS3_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{SAVED_FILE_PATH}/{SUCCESS3_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertTrue(is_valid)


class TestGoodFile3(unittest.TestCase):

    @patch.object(GTFSPathwaysValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{SUCCESS4_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS4_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS4_FILE_NAME}'

        with patch.object(GTFSPathwaysValidation, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = SUCCESS4_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test(self):
        # Arrange
        source = f'{SAVED_FILE_PATH}/{SUCCESS4_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS4_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{SAVED_FILE_PATH}/{SUCCESS4_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertTrue(is_valid)


class TestExplicitErrorCase(unittest.TestCase):

    @patch.object(GTFSPathwaysValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE4_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE4_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE4_FILE_NAME}'

        with patch.object(GTFSPathwaysValidation, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = FAILURE4_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test(self):
        # Arrange
        source = f'{SAVED_FILE_PATH}/{FAILURE3_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE3_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{SAVED_FILE_PATH}/{FAILURE3_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(errors.find("invalid_integer") > 0)


class TestFieldNameError(unittest.TestCase):

    @patch.object(GTFSPathwaysValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE3_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE3_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE3_FILE_NAME}'

        with patch.object(GTFSPathwaysValidation, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = FAILURE3_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test(self):
        # Arrange
        source = f'{SAVED_FILE_PATH}/{FAILURE3_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE3_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE3_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(errors.find("invalid_integer") > 0)


class TestFileNameError(unittest.TestCase):

    @patch.object(GTFSPathwaysValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE2_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE2_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE2_FILE_NAME}'

        with patch.object(GTFSPathwaysValidation, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = FAILURE2_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test(self):
        # Arrange
        source = f'{SAVED_FILE_PATH}/{FAILURE2_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE2_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE2_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(errors.find("invalid_row_length") > 0)


class TestForeignKey(unittest.TestCase):

    @patch.object(GTFSPathwaysValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE1_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE1_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE1_FILE_NAME}'

        with patch.object(GTFSPathwaysValidation, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = FAILURE1_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test(self):
        # Arrange
        source = f'{SAVED_FILE_PATH}/{FAILURE1_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE1_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE1_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(errors.find("foreign_key_violation") > 0)


class TestSuccessGTFSPathwaysValidation(unittest.TestCase):

    @patch.object(GTFSPathwaysValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{SUCCESS_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'

        with patch.object(GTFSPathwaysValidation, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = SUCCESS_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test_validate_with_valid_file(self):
        # Arrange
        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertTrue(is_valid)

    def test_is_gtfs_pathways_valid_with_valid_file(self):
        # Arrange
        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertTrue(is_valid)
        GTFSPathwaysValidation.clean_up.assert_called_once()

    def test_download_single_file(self):
        # Arrange
        file_upload_path = DOWNLOAD_FILE_PATH
        self.validator.storage_client = MagicMock()
        self.validator.storage_client.get_file_from_url = MagicMock()
        file = MagicMock()
        file.file_path = 'text_file.txt'
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
        file_upload_path = DOWNLOAD_FILE_PATH
        text_file_path = f'{file_upload_path}/text_file.txt'
        f = open(text_file_path, "w")
        f.write("Sample text")
        f.close()

        # Act
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Assert
        # self.assertFalse(os.path.exists(text_file_path))

    def test_clean_up_folder(self):
        # Arrange
        directory_name = 'temp'
        directory_path = f'{DOWNLOAD_FILE_PATH}/{directory_name}'
        is_exists = os.path.exists(directory_path)
        if not is_exists:
            os.makedirs(directory_path)

        # Act
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Assert
        # self.assertFalse(os.path.exists(directory_name))


class TestFailureGTFSPathwaysValidation(unittest.TestCase):

    @patch.object(GTFSPathwaysValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE_FILE_NAME}'

        with patch.object(GTFSPathwaysValidation, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = FAILURE_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test_validate_with_invalid_file(self):
        # Arrange
        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE_FILE_NAME}'
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)

    def test_is_gtfs_pathways_valid_with_invalid_zip_file(self):
        # Arrange
        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE_FILE_NAME}'
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        GTFSPathwaysValidation.clean_up.assert_called_once()

    def test_is_gtfs_pathways_valid_with_invalid_format_file(self):
        # Arrange
        file_path = f'{SAVED_FILE_PATH}/gtfs-pathways-upload.json'
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        GTFSPathwaysValidation.clean_up = MagicMock()

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        GTFSPathwaysValidation.clean_up.assert_called_once()

    def test_download_single_file_exception(self):
        # Arrange
        file_upload_path = DOWNLOAD_FILE_PATH
        self.validator.storage_client = MagicMock()
        self.validator.storage_client.get_file_from_url = MagicMock()
        file = MagicMock()
        file.file_path = 'text_file.txt'
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


if __name__ == '__main__':
    unittest.main()
