import os
import shutil
import logging
import traceback
import json
import urllib.parse
import uuid
from pathlib import Path
from typing import Union, Any, Optional
from .config import Settings
from .custom_checks import run_custom_checks
from .gtfs_feed import GtfsFeed
from .mobility_data_validator import MobilityDataResult, MobilityDataValidator
from .validation_report import ValidationReport
from .pathways_config import CHANGE_ERROR_TO_WARNING, PATHWAYS_FATAL_ERROR_CODES, PATHWAYS_FIELDS, PATHWAYS_FILES

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Path used for download file generation.
DOWNLOAD_FILE_PATH = f'{Path.cwd()}/downloads'

logging.basicConfig()
logger = logging.getLogger('PATHWAYS_VALIDATION')
logger.setLevel(logging.INFO)


class GTFSPathwaysValidation:
    def __init__(self, file_path=None, storage_client=None):
        settings = Settings()
        self.container_name = settings.storage_container_name
        self.storage_client = storage_client
        self.file_path = file_path
        self.file_relative_path = file_path.split('/')[-1]
        self.client = self.storage_client.get_container(container_name=self.container_name)
        self.settings = settings
        self.report: Optional[ValidationReport] = None
        self.report_url: Optional[str] = None

    # Facade function to validate the file
    # Focuses on the file name with file name validation
    # Use `is_gtfs_pathways_valid` to do more processing
    def validate(self) -> tuple[bool, str]:
        return self.is_gtfs_pathways_valid()

    # use this method to do the actual validation
    # when ready to replace, replace the call in the
    # above function.
    def is_gtfs_pathways_valid(self) -> tuple[Union[bool, Any], Union[str, Any]]:
        is_valid = False
        validation_message = ''
        root, ext = os.path.splitext(self.file_relative_path)
        if ext and ext.lower() == '.zip':
            downloaded_file_path = self.download_single_file(self.file_path)
            logger.info(f' Downloaded file path: {downloaded_file_path}')
            pathways_validator = MobilityDataValidator(zip_file=downloaded_file_path)
            result = pathways_validator.validate()

            # TDEI's own checks are judged by the same rules as MobilityData's notices
            custom_notices = self.run_custom_checks(downloaded_file_path)
            custom_errors = [notice for notice in custom_notices if notice.get('severity') == 'ERROR']

            validation_errors = self.parse_validation_errors(result.error)
            validation_info = self.parse_validation_errors(result.info)
            mobility_data_notices = list(validation_info) if isinstance(validation_info, list) \
                else list(validation_errors) if isinstance(validation_errors, list) else []
            if custom_errors:
                validation_errors = (validation_errors if isinstance(validation_errors, list) else []) + custom_errors
                result.error = validation_errors
            is_valid = result.status and not custom_errors
            if result.error is not None:
                validation_message = self.format_validation_errors(validation_errors)
                logger.error(f' Error While Validating File: {validation_message}')

            if isinstance(validation_errors, list):
                for error in validation_errors[:]:
                    # change some smaller errors to warnings instead to relax the strict validation MD gives us
                    if error['code'] in CHANGE_ERROR_TO_WARNING:
                        if not isinstance(validation_info, list):
                            validation_info = []

                        validation_info.append(error)
                        result.info = validation_info
                        validation_errors.remove(error)
                        continue

                    # these are error codes from MD that relate to pathways that are fatal
                    if error['code'] in PATHWAYS_FATAL_ERROR_CODES:
                        is_valid = False
                        continue

                    # some of the notices relate to pathways, but there's no way to tell except with this logic:
                    for notice in error['sampleNotices']:
                        # one of the fields in a given file is a pathway-spec field--if it's flagged, fail
                        if 'fieldName' in notice and 'filename' in notice:
                            if notice['filename'] in PATHWAYS_FIELDS and \
                                    notice['fieldName'] in PATHWAYS_FIELDS[notice['filename']]:
                                is_valid = False
                                continue

                        # one of the pathways spec'd files has an error--if so, fail
                        if 'filename' in notice:
                            if notice['filename'] in PATHWAYS_FILES:
                                is_valid = False
                                continue

                        # similar to the above, but the field for the filename is parent/child
                        if 'childFilename' in notice:
                            if notice['childFilename'] in PATHWAYS_FILES:
                                is_valid = False
                                continue

                # if all errors have been downgraded to warnings, mark us as a success
                if len(validation_errors) == 0:
                    is_valid = True

                if validation_errors is not None:
                    validation_message = self.format_validation_errors(validation_errors)
                    logger.error(f' Error While Validating File: {validation_message}')

            self.report = ValidationReport(
                feed_name=self.file_relative_path,
                is_valid=bool(is_valid),
                mobility_data_notices=mobility_data_notices,
                custom_notices=custom_notices,
                validator_version=getattr(result, 'validator_version', None),
                mobility_data_dir=getattr(result, 'output_dir', None),
            )
            self.report_url = self.upload_report(self.report)
            if isinstance(result, MobilityDataResult):
                result.clean_up()
            GTFSPathwaysValidation.clean_up(os.path.dirname(downloaded_file_path))
        else:
            logger.error(f' Failed to validate because unknown file format')

        return is_valid, validation_message

    @staticmethod
    def run_custom_checks(zip_path: str) -> list:
        # A problem in TDEI's own checks shouldn't block an upload MobilityData's validator accepts
        try:
            return run_custom_checks(GtfsFeed.from_zip(zip_path))
        except Exception as e:
            traceback.print_exc()
            logger.error(f' TDEI pathways checks failed: {e}')
            return []

    def report_blob_name(self) -> Optional[str]:
        """
        Where the report goes: next to the uploaded feed, e.g. `a/b/feed.zip` ->
        `a/b/feed-validation-report-1a2b3c4d.zip`. Uploads can't overwrite, so each report
        gets its own name, in case a feed is validated again.
        """
        path = urllib.parse.unquote(urllib.parse.urlparse(self.file_path or '').path).lstrip('/')
        container_prefix = f'{self.container_name}/'
        if self.container_name and path.startswith(container_prefix):
            path = path[len(container_prefix):]
        if not path:
            return None
        root, _ = os.path.splitext(path)
        return f'{root}-validation-report-{uuid.uuid4().hex[:8]}.zip'

    def upload_report(self, report: ValidationReport) -> Optional[str]:
        """Uploads the report zip, and returns its URL, or None if it couldn't be uploaded."""
        name = self.report_blob_name()
        container = getattr(self, 'client', None)
        if not name or container is None:
            return None
        try:
            report_file = container.create_file(name)
            report_file.upload(report.to_zip())
            url = report_file.get_remote_url()
            logger.info(f' Validation report uploaded to: {url}')
            return url
        except Exception as e:
            traceback.print_exc()
            logger.error(f' Could not upload the validation report: {e}')
            return None

    @staticmethod
    def parse_validation_errors(errors: Any) -> Any:
        if isinstance(errors, str):
            try:
                return json.loads(errors)
            except json.JSONDecodeError:
                return errors

        return errors

    @staticmethod
    def format_validation_errors(errors: Any) -> str:
        if isinstance(errors, str):
            return errors

        return json.dumps(errors, default=str)

    # Downloads the file to local folder of the server
    # file_upload_path is the fullUrl of where the
    # file is uploaded.
    def download_single_file(self, file_upload_path=None) -> str:
        unique_folder = self.settings.get_unique_id()
        dl_folder_path = os.path.join(DOWNLOAD_FILE_PATH, unique_folder)

        if not os.path.exists(dl_folder_path):
            os.makedirs(dl_folder_path)

        try:
            file = self.storage_client.get_file_from_url(self.container_name, file_upload_path)
            if file.file_path:
                file_path = os.path.basename(file.file_path)
                with open(f'{dl_folder_path}/{file_path}', 'wb') as blob:
                    blob.write(file.get_stream())
                logger.info(f' File downloaded to location: {dl_folder_path}/{file_path}')
                return f'{dl_folder_path}/{file_path}'
            else:
                logger.info(' File not found!')
        except Exception as e:
            traceback.print_exc()
            logger.error(e)

    @staticmethod
    def clean_up(path):
        if os.path.isfile(path):
            logger.info(f' Removing File: {path}')
            os.remove(path)
        else:
            folder = os.path.join(DOWNLOAD_FILE_PATH, path)
            logger.info(f' Removing Folder: {folder}')
            shutil.rmtree(folder, ignore_errors=False)
