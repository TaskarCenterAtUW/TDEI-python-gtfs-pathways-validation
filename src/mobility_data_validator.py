import json
import logging
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional

from .config import Settings

logging.basicConfig()
logger = logging.getLogger('MOBILITY_DATA_VALIDATOR')
logger.setLevel(logging.INFO)


class MobilityDataValidatorError(Exception):
    pass


class MobilityDataResult:
    """
    The result of a validation run, in the shape `gtfs_canonical_validator` returned,
    so the pass/fail rules apply unchanged:
    - `status`: whether there were no ERROR notices
    - `error`: the ERROR notices, or `None` if there are none
    - `info`: all notices
    Also keeps where MobilityData wrote its own reports.
    """

    def __init__(self, report: dict, output_dir: str, load_errors: Optional[List[dict]] = None):
        self.report = report
        self.output_dir = output_dir
        notices = report.get('notices', []) + (load_errors or [])
        self.error = [notice for notice in notices if notice.get('severity') == 'ERROR'] or None
        self.info = notices
        self.status = self.error is None

    @property
    def validator_version(self) -> Optional[str]:
        return self.report.get('summary', {}).get('validatorVersion')

    @property
    def report_json_path(self) -> str:
        return os.path.join(self.output_dir, 'report.json')

    @property
    def report_html_path(self) -> str:
        return os.path.join(self.output_dir, 'report.html')

    def clean_up(self) -> None:
        """Removes MobilityData's output."""
        shutil.rmtree(self.output_dir, ignore_errors=True)


class MobilityDataValidator:
    """
    Runs MobilityData's GTFS validator (https://github.com/MobilityData/gtfs-validator)
    on a feed, locally, so the feed doesn't leave TDEI and the validator version is pinned.
    """

    def __init__(self, zip_file: str, output_dir: Optional[str] = None, settings: Optional[Settings] = None):
        self.file = zip_file
        # By default, each run writes to its own temporary folder; remove it with `MobilityDataResult.clean_up`
        self.output_dir = output_dir or tempfile.mkdtemp(prefix='mobilitydata-')
        self.settings = settings or Settings()

    def validate(self) -> MobilityDataResult:
        jar = self.settings.gtfs_validator_jar
        if not os.path.isfile(jar):
            raise MobilityDataValidatorError(
                f'GTFS validator not found at {jar}; run scripts/download-gtfs-validator.sh')

        # Never read a report left from an earlier run
        shutil.rmtree(self.output_dir, ignore_errors=True)
        os.makedirs(self.output_dir)
        command = [
            self.settings.java_path, '-jar', jar,
            '--input', self.file,
            '--output_base', self.output_dir,
            '--country_code', self.settings.gtfs_validator_country_code,
        ]
        logger.info(f' Running {" ".join(command)}')
        try:
            completed = subprocess.run(command, capture_output=True, text=True,
                                       timeout=int(self.settings.gtfs_validator_timeout))
        except (OSError, subprocess.TimeoutExpired) as e:
            raise MobilityDataValidatorError(f'Could not run the GTFS validator: {e}') from e

        report_path = os.path.join(self.output_dir, 'report.json')
        if not os.path.isfile(report_path):
            details = (completed.stderr or completed.stdout or '').strip()[-2000:]
            raise MobilityDataValidatorError(
                f'The GTFS validator failed (exit code {completed.returncode}): {details}')

        with open(report_path, encoding='utf-8') as report_file:
            report = json.load(report_file)

        # MobilityData reports its own failures separately from the feed's problems. When it
        # couldn't load the feed at all (e.g. it isn't a zip), it exits with an error, and those
        # failures are the feed's problem; otherwise (e.g. one rule crashed) they're only logged.
        system_errors = self._system_errors()
        for notice in system_errors:
            logger.warning(f' GTFS validator system error: {notice.get("code")}')
        # Marked so they fail the upload: a feed that can't be read can't have its pathways checked
        load_errors = [{**notice, 'feedUnreadable': True} for notice in system_errors
                       if notice.get('severity') == 'ERROR'] if completed.returncode != 0 else []

        return MobilityDataResult(report, self.output_dir, load_errors)

    def _system_errors(self) -> List[dict]:
        path = os.path.join(self.output_dir, 'system_errors.json')
        if not os.path.isfile(path):
            return []
        with open(path, encoding='utf-8') as errors_file:
            return json.load(errors_file).get('notices', [])
