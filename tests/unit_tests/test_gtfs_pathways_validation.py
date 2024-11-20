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


class TestGTFSPathwaysValidationInit(unittest.TestCase):
    @patch('src.gtfs_pathways_validation.Settings')
    def test_initialization(self, mock_settings):
        # Arrange
        mock_storage_client = MagicMock()
        mock_container = MagicMock()
        mock_storage_client.get_container.return_value = mock_container

        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.storage_container_name = "test_container"
        mock_settings_instance.get_unique_id.return_value = "unique_prefix"

        file_path = "path/to/file.zip"

        # Act
        validation_instance = GTFSPathwaysValidation(
            file_path=file_path,
            storage_client=mock_storage_client,
        )

        # Assert
        self.assertEqual(validation_instance.file_path, file_path)
        self.assertEqual(validation_instance.file_relative_path, "file.zip")
        self.assertEqual(validation_instance.container_name, "test_container")
        self.assertEqual(validation_instance.client, mock_container)

        mock_storage_client.get_container.assert_called_once_with(container_name="test_container")

    @patch('src.gtfs_pathways_validation.Settings')
    def test_initialization_with_prefix(self, mock_settings):
        # Arrange
        mock_storage_client = MagicMock()
        mock_container = MagicMock()
        mock_storage_client.get_container.return_value = mock_container

        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.storage_container_name = "test_container"

        file_path = "path/to/file.zip"
        custom_prefix = "custom_prefix"

        # Act
        validation_instance = GTFSPathwaysValidation(
            file_path=file_path,
            storage_client=mock_storage_client
        )

        # Assert
        self.assertEqual(validation_instance.container_name, "test_container")
        self.assertEqual(validation_instance.file_relative_path, "file.zip")

        mock_storage_client.get_container.assert_called_once_with(container_name="test_container")


class TestGTFSPathwaysValidationOther(unittest.TestCase):

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
            self.validator.clean_up = MagicMock()

    def tearDown(self):
        pass

    def test_clean_up_non_existent_path(self):
        # Arrange
        non_existent_path = f'{DOWNLOAD_FILE_PATH}/non_existent_file_or_folder'

        # Act
        try:
            GTFSPathwaysValidation.clean_up(non_existent_path)
            success = True
        except Exception:
            success = False
        # Assert
        self.assertTrue(success)


    def test_is_pathways_valid_with_wrong_file_extension(self):

        self.validator.file_relative_path = f'{DOWNLOAD_FILE_PATH}/test.txt'
        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.gtfs_pathways_validation.CanonicalValidator')
    def test_is_pathways_valid_with_errors(self, mock_canonical_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'INVALID_FIELD', 'sampleNotices': [{'fieldName': 'invalid_field', 'filename': 'pathways_data'}]}
        ]
        mock_canonical_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)
        self.assertIn('INVALID_FIELD', validation_message)

    @patch('src.gtfs_pathways_validation.CanonicalValidator')
    def test_is_pathways_valid_to_convert_error_to_warning(self, mock_canonical_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'block_trips_with_overlapping_stop_times',
             'sampleNotices': [{'fieldName': 'invalid_field', 'filename': 'pathways_data'}]}
        ]
        mock_result.info = None
        mock_canonical_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertTrue(is_valid)

    @patch('src.gtfs_pathways_validation.CanonicalValidator')
    def test_is_pathways_valid_for_fatal_errors(self, mock_canonical_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'bidirectional_exit_gate',
             'sampleNotices': [{'fieldName': 'wheelchair_accessible', 'filename': 'trips.txt'}]}
        ]
        mock_result.info = None
        mock_canonical_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.gtfs_pathways_validation.CanonicalValidator')
    def test_is_pathways_valid_with_other(self, mock_canonical_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'sample_code',
             'sampleNotices': [{'fieldName': 'wheelchair_accessible', 'filename': 'trips.txt'}]}
        ]
        mock_result.info = None
        mock_canonical_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.gtfs_pathways_validation.CanonicalValidator')
    def test_is_pathways_valid_with_invalid_pathways_file(self, mock_canonical_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'sample_code',
             'sampleNotices': [{'fieldName': 'wheelchair_accessible', 'filename': 'pathways.txt'}]}
        ]
        mock_result.info = None
        mock_canonical_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.gtfs_pathways_validation.CanonicalValidator')
    def test_is_pathways_valid_with_child_reference(self, mock_canonical_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'sample_code',
             'sampleNotices': [{'fieldName': 'wheelchair_accessible', 'childFilename': 'pathways.txt'}]}
        ]
        mock_result.info = None
        mock_canonical_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.gtfs_pathways_validation.logger')
    def test_download_single_file_with_no_file_path(self, mock_logger):
        validator = GTFSPathwaysValidation(file_path="mock_path", storage_client=MagicMock())
        validator.storage_client.get_file_from_url.return_value = MagicMock(file_path=None)

        # Act
        result = validator.download_single_file(file_upload_path="mock_file_path.zip")

        # Assert
        assert result is None
        mock_logger.info.assert_called_once_with(' File not found!')

    @patch('src.gtfs_pathways_validation.logger')
    def test_download_single_file_with_exception(self, mock_logger):
        # Arrange
        validator = GTFSPathwaysValidation(file_path="mock_path", storage_client=MagicMock())
        validator.storage_client.get_file_from_url.side_effect = Exception("Mocked exception")

        # Act
        result = validator.download_single_file(file_upload_path="mock_file_path.zip")

        # Assert
        assert result is None
        mock_logger.error.assert_called_once()
        # Extract the exception passed to logger.error and check its message
        logged_exception = mock_logger.error.call_args[0][0]
        assert isinstance(logged_exception, Exception)
        assert str(logged_exception) == "Mocked exception"


if __name__ == '__main__':
    unittest.main()
