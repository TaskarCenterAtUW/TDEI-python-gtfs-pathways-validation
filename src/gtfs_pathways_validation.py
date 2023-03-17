import os
import shutil
import logging
import traceback
from pathlib import Path
from typing import Union, Any
from .config import Settings

from python_ms_core import Core
from tdei_gtfs_csv_validator import gcv_test_release
from tdei_gtfs_csv_validator import exceptions as gcvex

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Path used for download file generation.
DOWNLOAD_FILE_PATH = f'{Path.cwd()}/downloads'

logging.basicConfig()
logger = logging.getLogger('PATHWAYS_VALIDATION')
logger.setLevel(logging.INFO)

DATA_TYPE = 'gtfs_pathways'
SCHEMA_VERSION = 'v1.0'


class GTFSPathwaysValidation:
    def __init__(self, file_path=None):
        core = Core()
        settings = Settings()
        self.container_name = settings.storage_container_name
        self.storage_client = core.get_storage_client()
        self.file_path = file_path
        self.file_relative_path = file_path.split('/')[-1]
        self.client = self.storage_client.get_container(container_name=self.container_name)

    # Facade function to validate the file
    # Focuses on the file name with file name validation
    # Use `is_gtfs_pathways_valid` to do more processing
    def validate(self) -> tuple[bool, str]:
        return self.is_gtfs_pathways_valid()

    # use this method to do the actual validation
    # when ready to replace, replace the call in the
    # above function.
    def is_gtfs_pathways_valid(self) -> tuple[Union[bool, Any], Union[str, Any]]:
        dest = DOWNLOAD_FILE_PATH
        is_valid = False
        validation_message = ''
        root, ext = os.path.splitext(self.file_relative_path)
        if ext:
            downloaded_file_path = self.download_single_file(self.file_path)
            try:
                logger.info(f' Downloaded file path: {downloaded_file_path}')
                gcv_test_release.test_release(DATA_TYPE, SCHEMA_VERSION, downloaded_file_path)
                is_valid = True
            except Exception as err:
                traceback.print_exc()
                validation_message = str(err)
                logger.error(f' Error While Validating File: {str(err)}')
        else:
            source = '/'.join(self.file_path.split('/')[4:])
            blobs = self.ls_files(source, recursive=True)
            if blobs:
                if not source == '' and not source.endswith('/'):
                    source += '/'
                if not dest.endswith('/'):
                    dest += '/'
                dest += os.path.basename(os.path.normpath(source)) + '/'
                blobs = [source + blob for blob in blobs]
                for blob in blobs:
                    blob_dest = dest + os.path.relpath(blob, source)
                    self.download_file(blob, blob_dest)
            else:
                self.download_file(source, dest)
            try:
                gcv_test_release.test_release(DATA_TYPE, SCHEMA_VERSION, dest)
                is_valid = True
            except Exception as err:
                traceback.print_exc()
                logger.error(f' Error While Validating Folder: {str(err)}')
                validation_message = str(err)
            finally:
                downloaded_file_path = dest

        GTFSPathwaysValidation.clean_up(downloaded_file_path)
        return is_valid, validation_message

    # Downloads the file to local folder of the server
    # file_upload_path is the fullUrl of where the
    # file is uploaded.
    def download_single_file(self, file_upload_path=None) -> str:
        is_exists = os.path.exists(DOWNLOAD_FILE_PATH)
        if not is_exists:
            os.makedirs(DOWNLOAD_FILE_PATH)

        file = self.storage_client.get_file_from_url(self.container_name, file_upload_path)
        try:
            if file.file_path:
                file_path = file.file_path.split('/')[-1]
                with open(f'{DOWNLOAD_FILE_PATH}/{file_path}', 'wb') as blob:
                    blob.write(file.get_stream())
                logger.info(f' File downloaded to location: {DOWNLOAD_FILE_PATH}/{file_path}')
                return f'{DOWNLOAD_FILE_PATH}/{file_path}'
            else:
                logger.info(' File not found!')
        except Exception as e:
            traceback.print_exc()
            logger.error(e)

    def download_file(self, source, dest):
        # dest is a directory if ending with '/' or '.', otherwise it's a file
        if dest.endswith('.'):
            dest += '/'
        blob_dest = dest + os.path.basename(source) if dest.endswith('/') else dest

        logger.info(f' Downloading {source} to {blob_dest}')
        os.makedirs(os.path.dirname(blob_dest), exist_ok=True)
        bc = self.storage_client.get_file(container_name=self.container_name, file_name=source)

        with open(blob_dest, 'wb') as file:
            file.write(bc.get_stream())
        return blob_dest

    def ls_files(self, path, recursive=False):
        if not path == '' and not path.endswith('/'):
            path += '/'

        blob_iter = self.client.list_files(name_starts_with=path)
        files = []
        for blob in blob_iter:
            relative_path = os.path.relpath(blob.name, path)
            if recursive or not '/' in relative_path:
                files.append(relative_path)
        return files

    @staticmethod
    def clean_up(path):
        if os.path.isfile(path):
            logger.info(f' Removing File: {path}')
            os.remove(path)
        else:
            folder = os.path.join(DOWNLOAD_FILE_PATH, path)
            logger.info(f' Removing Folder: {folder}')
            shutil.rmtree(folder, ignore_errors=False)
