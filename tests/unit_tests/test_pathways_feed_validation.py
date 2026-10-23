import json
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.pathways_feed_validation import PathwaysFeedValidation, FeedDownloadError

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


# The "good" feeds are real Baltimore Metro data. MobilityData accepts them, but they have four
# escalators, stairs and elevators between stops on the same level, which TDEI's checks fail.
GOOD_FEED_FAILURES = ['tdei_level_change_same_level']


def failing_codes(validation_message):
    return [error['code'] for error in json.loads(validation_message)]


def patch_clean_up(test):
    """Replaces PathwaysFeedValidation.clean_up until the end of one test."""
    patcher = patch.object(PathwaysFeedValidation, 'clean_up')
    test.addCleanup(patcher.stop)
    return patcher.start()

DATA_TYPE = 'gtfs_pathways'
SCHEMA_VERSION = 'v1.0'


class TestGoodFile2(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{SUCCESS3_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS3_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS3_FILE_NAME}'

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
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

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS3_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        patch_clean_up(self)

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertTrue(is_valid)


class TestGoodFile3(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{SUCCESS4_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS4_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS4_FILE_NAME}'

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
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

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS4_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        patch_clean_up(self)

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertEqual(failing_codes(errors), GOOD_FEED_FAILURES)


class TestExplicitErrorCase(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE4_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE4_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE4_FILE_NAME}'

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
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

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE3_FILE_NAME}'

        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        patch_clean_up(self)

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(errors.find("invalid_integer") > 0)


class TestFieldNameError(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE3_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE3_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE3_FILE_NAME}'

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
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
        patch_clean_up(self)

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(errors.find("invalid_integer") > 0)


class TestFileNameError(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE2_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE2_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE2_FILE_NAME}'

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
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
        patch_clean_up(self)

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(errors.find("invalid_row_length") > 0)


class TestForeignKey(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE1_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE1_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE1_FILE_NAME}'

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
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
        patch_clean_up(self)

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(errors.find("foreign_key_violation") > 0)


class TestSuccessPathwaysFeedValidation(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{SUCCESS_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
            self.validator.file_path = file_path
            self.validator.file_relative_path = SUCCESS_FILE_NAME
            self.validator.container_name = None
            self.validator.settings = MagicMock()
            mock_download_single_file.return_value = file_path

    def tearDown(self):
        pass

    def test_validate_with_good_feed(self):
        # Arrange
        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        patch_clean_up(self)

        # Act
        is_valid, errors = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertEqual(failing_codes(errors), GOOD_FEED_FAILURES)

    def test_is_gtfs_pathways_valid_with_good_feed_cleans_up(self):
        # Arrange
        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        patch_clean_up(self)

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        PathwaysFeedValidation.clean_up.assert_called_once()

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
        with open(text_file_path, "w") as f:
            f.write("Sample text")

        # Act
        PathwaysFeedValidation.clean_up(text_file_path)

        # Assert
        self.assertFalse(os.path.exists(text_file_path))

    def test_clean_up_folder(self):
        # Arrange
        directory_name = 'temp'
        directory_path = f'{DOWNLOAD_FILE_PATH}/{directory_name}'
        is_exists = os.path.exists(directory_path)
        if not is_exists:
            os.makedirs(directory_path)

        # Act
        PathwaysFeedValidation.clean_up(directory_path)

        # Assert
        self.assertFalse(os.path.exists(directory_path))

    def test_clean_up_refuses_paths_outside_downloads(self):
        # Arrange
        outside = SAVED_FILE_PATH

        # Act
        PathwaysFeedValidation.clean_up(outside)

        # Assert
        self.assertTrue(os.path.isdir(outside))


class TestFailurePathwaysFeedValidation(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{FAILURE_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{FAILURE_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE_FILE_NAME}'

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
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
        patch_clean_up(self)

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)

    def test_is_gtfs_pathways_valid_with_invalid_zip_file(self):
        # Arrange
        file_path = f'{DOWNLOAD_FILE_PATH}/{FAILURE_FILE_NAME}'
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        patch_clean_up(self)

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        PathwaysFeedValidation.clean_up.assert_called_once()

    def test_is_gtfs_pathways_valid_with_invalid_format_file(self):
        # Arrange
        file_path = f'{DOWNLOAD_FILE_PATH}/gtfs-pathways-upload.json'
        shutil.copyfile(f'{Path.cwd()}/src/assets/gtfs-pathways-upload.json', file_path)
        expected_downloaded_file_path = file_path
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)
        patch_clean_up(self)

        # Act
        is_valid, _ = self.validator.validate()

        # Assert
        self.assertFalse(is_valid)
        PathwaysFeedValidation.clean_up.assert_called_once()

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


class TestPathwaysFeedValidationInit(unittest.TestCase):
    @patch('src.pathways_feed_validation.Settings')
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
        validation_instance = PathwaysFeedValidation(
            file_path=file_path,
            storage_client=mock_storage_client,
        )

        # Assert
        self.assertEqual(validation_instance.file_path, file_path)
        self.assertEqual(validation_instance.file_relative_path, "file.zip")
        self.assertEqual(validation_instance.container_name, "test_container")
        self.assertEqual(validation_instance.client, mock_container)

        mock_storage_client.get_container.assert_called_once_with(container_name="test_container")

    @patch('src.pathways_feed_validation.Settings')
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
        validation_instance = PathwaysFeedValidation(
            file_path=file_path,
            storage_client=mock_storage_client
        )

        # Assert
        self.assertEqual(validation_instance.container_name, "test_container")
        self.assertEqual(validation_instance.file_relative_path, "file.zip")

        mock_storage_client.get_container.assert_called_once_with(container_name="test_container")


class TestPathwaysFeedValidationOther(unittest.TestCase):

    @patch.object(PathwaysFeedValidation, 'download_single_file')
    def setUp(self, mock_download_single_file):
        os.makedirs(DOWNLOAD_FILE_PATH, exist_ok=True)
        source = f'{SAVED_FILE_PATH}/{SUCCESS_FILE_NAME}'
        destination = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'

        if not os.path.isfile(destination):
            shutil.copyfile(source, destination)

        file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'

        # These tests are about MobilityData's results, so TDEI's own checks find nothing
        custom_checks = patch('src.pathways_feed_validation.run_custom_checks', return_value=[])
        custom_checks.start()
        self.addCleanup(custom_checks.stop)

        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation(file_path=file_path, storage_client=MagicMock())
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
            PathwaysFeedValidation.clean_up(non_existent_path)
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

    def test_parse_validation_errors_reads_validator_json_text(self):
        # Arrange
        errors = '[{"code": "INVALID_FIELD", "sampleNotices": []}]'

        # Act
        validation_errors = PathwaysFeedValidation.parse_validation_errors(errors)

        # Assert
        self.assertEqual(validation_errors, [{'code': 'INVALID_FIELD', 'sampleNotices': []}])

    def test_format_validation_errors_serializes_errors_as_json_text(self):
        # Arrange
        errors = [{'code': 'INVALID_FIELD', 'sampleNotices': [{'fieldName': 'invalid_field'}]}]

        # Act
        validation_message = PathwaysFeedValidation.format_validation_errors(errors)

        # Assert
        self.assertEqual(
            json.loads(validation_message),
            [{'code': 'INVALID_FIELD', 'sampleNotices': [{'fieldName': 'invalid_field'}]}]
        )
        self.assertNotIn("'", validation_message)
        self.assertFalse(validation_message.startswith('"'))

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_with_errors(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'INVALID_FIELD', 'sampleNotices': [{'fieldName': 'invalid_field', 'filename': 'pathways.txt'}]}
        ]
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)
        self.assertIn('INVALID_FIELD', validation_message)
        self.assertEqual(json.loads(validation_message), mock_result.error)

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_with_json_string_errors(self, mock_mobility_data_validator):
        # Arrange
        validation_errors = [
            {'code': 'INVALID_FIELD', 'sampleNotices': [{'fieldName': 'invalid_field', 'filename': 'pathways.txt'}]}
        ]
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = json.dumps(validation_errors)
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)
        self.assertFalse(validation_message.startswith('"'))
        self.assertEqual(json.loads(validation_message), validation_errors)

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_with_json_string_info(self, mock_mobility_data_validator):
        # Arrange
        validation_errors = [
            {'code': 'block_trips_with_overlapping_stop_times',
             'sampleNotices': [{'fieldName': 'invalid_field', 'filename': 'pathways_data'}]}
        ]
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = json.dumps(validation_errors)
        mock_result.info = '[]'
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertTrue(is_valid)
        self.assertEqual(validation_message, '')

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_to_convert_error_to_warning(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'block_trips_with_overlapping_stop_times',
             'sampleNotices': [{'fieldName': 'invalid_field', 'filename': 'pathways_data'}]}
        ]
        mock_result.info = None
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertTrue(is_valid)

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_for_fatal_errors(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'bidirectional_exit_gate',
             'sampleNotices': [{'fieldName': 'wheelchair_accessible', 'filename': 'trips.txt'}]}
        ]
        mock_result.info = None
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_with_other(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'sample_code',
             'sampleNotices': [{'fieldName': 'wheelchair_accessible', 'filename': 'trips.txt'}]}
        ]
        mock_result.info = None
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_cleans_up_when_validation_fails(self, mock_mobility_data_validator):
        # Arrange
        mock_mobility_data_validator.return_value.validate.side_effect = RuntimeError('validator crashed')
        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/abc/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act / Assert
        with patch.object(PathwaysFeedValidation, 'clean_up') as mock_clean_up:
            with self.assertRaisesRegex(RuntimeError, 'validator crashed'):
                self.validator.is_gtfs_pathways_valid()
        mock_clean_up.assert_called_once_with(f'{DOWNLOAD_FILE_PATH}/abc')
        self.assertEqual(mock_mobility_data_validator.call_args.kwargs['output_dir'],
                         f'{DOWNLOAD_FILE_PATH}/abc/mobilitydata')

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_fails_with_any_error(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'sample_code',
             'sampleNotices': [{'fieldName': 'route_color', 'filename': 'routes.txt'}]}
        ]
        mock_result.info = None
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)
        self.assertEqual([error['code'] for error in json.loads(validation_message)], ['sample_code'])

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_lists_errors_but_not_downgraded_ones(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'sample_code',
             'sampleNotices': [{'fieldName': 'route_color', 'filename': 'routes.txt'}]},
            {'code': 'invalid_url',
             'sampleNotices': [{'filename': 'agency.txt'}]}
        ]
        mock_result.info = None
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)
        self.assertEqual([error['code'] for error in json.loads(validation_message)], ['sample_code'])

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_with_missing_required_file(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'missing_required_file', 'sampleNotices': [{'filename': 'agency.txt'}]}
        ]
        mock_result.info = None
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_with_invalid_pathways_file(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'sample_code',
             'sampleNotices': [{'fieldName': 'wheelchair_accessible', 'filename': 'pathways.txt'}]}
        ]
        mock_result.info = None
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.pathways_feed_validation.MobilityDataValidator')
    def test_is_pathways_valid_with_child_reference(self, mock_mobility_data_validator):
        # Arrange
        mock_result = MagicMock()
        mock_result.status = False
        mock_result.error = [
            {'code': 'sample_code',
             'sampleNotices': [{'fieldName': 'wheelchair_accessible', 'childFilename': 'pathways.txt'}]}
        ]
        mock_result.info = None
        mock_mobility_data_validator.return_value.validate.return_value = mock_result

        expected_downloaded_file_path = f'{DOWNLOAD_FILE_PATH}/{SUCCESS_FILE_NAME}'
        self.validator.download_single_file = MagicMock(return_value=expected_downloaded_file_path)

        # Act
        is_valid, validation_message = self.validator.is_gtfs_pathways_valid()

        # Assert
        self.assertFalse(is_valid)

    @patch('src.pathways_feed_validation.logger')
    def test_download_single_file_with_no_file_path(self, mock_logger):
        validator = PathwaysFeedValidation(file_path="mock_path", storage_client=MagicMock())
        validator.storage_client.get_file_from_url.return_value = MagicMock(file_path=None)

        # Act / Assert
        with self.assertRaisesRegex(FeedDownloadError, 'mock_file_path.zip not found'):
            validator.download_single_file(file_upload_path="mock_file_path.zip")

    @patch('src.pathways_feed_validation.logger')
    def test_download_single_file_with_exception(self, mock_logger):
        # Arrange
        validator = PathwaysFeedValidation(file_path="mock_path", storage_client=MagicMock())
        validator.storage_client.get_file_from_url.side_effect = Exception("Mocked exception")

        # Act / Assert
        with self.assertRaisesRegex(FeedDownloadError, 'Could not download the feed: Mocked exception'):
            validator.download_single_file(file_upload_path="mock_file_path.zip")
        mock_logger.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
