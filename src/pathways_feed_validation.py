import os
import shutil
import logging
import traceback
import json
import urllib.parse
import uuid
from pathlib import Path
from typing import Any, Optional
from .config import Settings
from .custom_checks import run_custom_checks
from .pathways_metrics import measure_feed
from .one_way_service import explain_one_way_locations
from .pathway_errors import lenient_replacements, pathway_stop_ids
from .gtfs_feed import GtfsFeed
from .mobility_data_validator import MobilityDataValidator
from .validation_report import ValidationReport, error_fails_upload

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Path used for download file generation.
DOWNLOAD_FILE_PATH = f'{Path.cwd()}/downloads'

logging.basicConfig()
logger = logging.getLogger('PATHWAYS_VALIDATION')
logger.setLevel(logging.INFO)


class FeedDownloadError(Exception):
    pass


class PathwaysFeedValidation:
    def __init__(self, file_path: str, storage_client=None):
        settings = Settings()
        self.container_name = settings.storage_container_name
        self.storage_client = storage_client
        self.file_path = file_path
        self.file_relative_path = file_path.split('/')[-1]
        self.client = self.storage_client.get_container(container_name=self.container_name)
        self.settings = settings
        self.report: Optional[ValidationReport] = None
        self.report_url: Optional[str] = None

    # Validates the feed; returns whether it passes, and the errors that failed it as JSON
    def validate(self) -> tuple[bool, str]:
        return self.is_gtfs_pathways_valid()

    def is_gtfs_pathways_valid(self) -> tuple[bool, str]:
        is_valid = False
        validation_message = ''
        root, ext = os.path.splitext(self.file_relative_path)
        if ext and ext.lower() == '.zip':
            downloaded_file_path = self.download_single_file(self.file_path)
            logger.info(f' Downloaded file path: {downloaded_file_path}')
            download_folder = os.path.dirname(downloaded_file_path)
            try:
                # MobilityData writes next to the feed, so removing the download folder removes its output too
                is_valid, validation_message, self.report = self.check_feed(
                    downloaded_file_path, self.file_relative_path, os.path.join(download_folder, 'mobilitydata'),
                    strict=getattr(getattr(self, 'settings', None), 'pathways_strict', False) is True)
                self.report_url = self.upload_report(self.report)
            finally:
                PathwaysFeedValidation.clean_up(download_folder)
        else:
            logger.error(f' Failed to validate because unknown file format')

        return is_valid, validation_message

    @classmethod
    def check_feed(cls, zip_path: str, feed_name: str, output_dir: str,
                   strict: bool = False) -> tuple[bool, str, ValidationReport]:
        """
        Validates a feed zip on disk: MobilityData's validator (writing its reports to output_dir), then
        TDEI's checks and metrics. Returns whether it passes, the errors that failed it as JSON, and the
        report. Unless strict, errors in pathways data are reported but don't fail it (see
        pathway_errors.py). The service and scripts/validate_feed.py both use it.
        """
        validation_message = ''
        result = MobilityDataValidator(zip_file=zip_path, output_dir=output_dir).validate()

        # TDEI's own checks are judged by the same rules as MobilityData's notices
        custom_notices, metrics = cls.run_custom_checks(zip_path)
        if not strict:  # TDEI's checks are all about pathways data
            custom_notices = [{**notice, 'pathwayData': True} if notice.get('severity') == 'ERROR' else notice
                              for notice in custom_notices]
        custom_errors = [{**notice, 'source': 'tdei'} for notice in custom_notices
                         if notice.get('severity') == 'ERROR']

        validation_errors = cls.parse_validation_errors(result.error)
        validation_info = cls.parse_validation_errors(result.info)
        if isinstance(validation_errors, list):
            validation_errors, validation_info = cls.explain_one_way_locations(zip_path, validation_errors, validation_info)
            if not strict:
                validation_errors, validation_info = cls.mark_pathway_errors(zip_path, validation_errors, validation_info)
        mobility_data_notices = list(validation_info) if isinstance(validation_info, list) \
            else list(validation_errors) if isinstance(validation_errors, list) else []

        # Every error fails the upload unless pathways_config.py downgrades it (see validation_report.error_fails_upload)
        if validation_errors is None or isinstance(validation_errors, list):
            failing_errors = [error for error in (validation_errors or []) + custom_errors
                              if error_fails_upload(error)]
        else:
            # An error that isn't a list of notices can't be judged, so it fails the upload
            failing_errors = validation_errors
        is_valid = not failing_errors
        if failing_errors:
            validation_message = cls.format_validation_errors(failing_errors)
            logger.error(f' Error While Validating File: {validation_message}')

        report = ValidationReport(
            feed_name=feed_name,
            is_valid=bool(is_valid),
            mobility_data_notices=mobility_data_notices,
            custom_notices=custom_notices,
            metrics=metrics,
            strict=strict,
            validator_version=getattr(result, 'validator_version', None),
            mobility_data_dir=getattr(result, 'output_dir', None),
        )
        return is_valid, validation_message, report

    @staticmethod
    def explain_one_way_locations(zip_path: str, errors: list, notices: Any) -> tuple[list, Any]:
        """
        Replaces MobilityData's unreachable-location errors for places that are one-way by design (e.g. a
        drop-off-only platform), which don't fail the upload (see one_way_service.py). A problem working
        that out leaves the errors as they are.
        """
        try:
            replacements = explain_one_way_locations(zip_path, errors)
        except Exception as e:
            traceback.print_exc()
            logger.error(f' Could not check one-way locations: {e}')
            return errors, notices
        replace = lambda items: [new for item in items for new in replacements.get(id(item), [item])]
        return replace(errors), replace(notices) if isinstance(notices, list) else notices

    @staticmethod
    def mark_pathway_errors(zip_path: str, errors: list, notices: Any) -> tuple[list, Any]:
        """
        For lenient mode: marks MobilityData's errors in pathways data so they don't fail the upload (see
        pathway_errors.py). A problem working that out leaves the errors as they are.
        """
        try:
            replacements = lenient_replacements(errors, pathway_stop_ids(zip_path))
        except Exception as e:
            traceback.print_exc()
            logger.error(f' Could not tell which errors are in pathways data: {e}')
            return errors, notices
        replace = lambda items: [new for item in items for new in replacements.get(id(item), [item])]
        return replace(errors), replace(notices) if isinstance(notices, list) else notices

    @staticmethod
    def run_custom_checks(zip_path: str) -> tuple[list, Optional[dict]]:
        """
        TDEI's own checks' notices, and the feed's metrics (None if they couldn't be measured). A
        problem in either shouldn't block an upload MobilityData's validator accepts.
        """
        try:
            feed = GtfsFeed.from_zip(zip_path)
        except Exception as e:
            logger.error(f' TDEI pathways checks failed: {e}')
            return [], None
        try:
            notices = run_custom_checks(feed)
        except Exception as e:
            traceback.print_exc()
            logger.error(f' TDEI pathways checks failed: {e}')
            notices = []
        try:
            metrics = measure_feed(feed)
        except Exception as e:
            traceback.print_exc()
            logger.error(f' TDEI pathways metrics failed: {e}')
            metrics = None
        return notices, metrics

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
    # Raises FeedDownloadError if it can't, leaving nothing behind.
    def download_single_file(self, file_upload_path=None) -> str:
        unique_folder = self.settings.get_unique_id()
        dl_folder_path = os.path.join(DOWNLOAD_FILE_PATH, unique_folder)

        if not os.path.exists(dl_folder_path):
            os.makedirs(dl_folder_path)

        try:
            file = self.storage_client.get_file_from_url(self.container_name, file_upload_path)
            if not file.file_path:
                raise FeedDownloadError(f'Could not download the feed: {file_upload_path} not found')
            file_path = os.path.basename(file.file_path)
            with open(f'{dl_folder_path}/{file_path}', 'wb') as blob:
                blob.write(file.get_stream())
            logger.info(f' File downloaded to location: {dl_folder_path}/{file_path}')
            return f'{dl_folder_path}/{file_path}'
        except Exception as e:
            shutil.rmtree(dl_folder_path, ignore_errors=True)
            logger.error(f' {e}')
            if isinstance(e, FeedDownloadError):
                raise
            traceback.print_exc()
            raise FeedDownloadError(f'Could not download the feed: {e}') from e

    # Removes a downloaded file or folder; refuses anything outside the downloads folder
    @staticmethod
    def clean_up(path):
        downloads = os.path.realpath(DOWNLOAD_FILE_PATH)
        target = os.path.realpath(os.path.join(DOWNLOAD_FILE_PATH, path))
        if target == downloads or os.path.commonpath([target, downloads]) != downloads:
            logger.warning(f' Not removing {target}: it is not inside {downloads}')
            return
        if os.path.isfile(target):
            logger.info(f' Removing File: {target}')
            os.remove(target)
        elif os.path.isdir(target):
            logger.info(f' Removing Folder: {target}')
            shutil.rmtree(target)
