import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.config import Settings
from src.mobility_data_validator import MobilityDataResult, MobilityDataValidator, MobilityDataValidatorError

TEST_FILES = os.path.join(os.path.dirname(__file__), 'test_files')
JAR_AVAILABLE = os.path.isfile(Settings().gtfs_validator_jar) and shutil.which(Settings().java_path) is not None


def write_outputs(output_dir, notices=None, system_errors=None):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'report.json'), 'w') as f:
        json.dump({'summary': {'validatorVersion': '8.0.1'}, 'notices': notices or []}, f)
    with open(os.path.join(output_dir, 'system_errors.json'), 'w') as f:
        json.dump({'notices': system_errors or []}, f)


class TestMobilityDataResult(unittest.TestCase):

    def test_splits_errors_from_other_notices(self):
        notices = [{'code': 'a', 'severity': 'ERROR'}, {'code': 'b', 'severity': 'WARNING'}]
        result = MobilityDataResult({'summary': {'validatorVersion': '8.0.1'}, 'notices': notices}, '/out')

        self.assertFalse(result.status)
        self.assertEqual(result.error, [notices[0]])
        self.assertEqual(result.info, notices)
        self.assertEqual(result.validator_version, '8.0.1')
        self.assertEqual(result.report_html_path, os.path.join('/out', 'report.html'))

    def test_has_no_errors_like_the_hosted_validator_did(self):
        result = MobilityDataResult({'notices': [{'code': 'b', 'severity': 'WARNING'}]}, '/out')

        self.assertTrue(result.status)
        self.assertIsNone(result.error)


class TestMobilityDataValidator(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.jar = os.path.join(self.dir, 'validator.jar')
        open(self.jar, 'w').close()
        self.settings = MagicMock(gtfs_validator_jar=self.jar, gtfs_validator_country_code='us',
                                  gtfs_validator_timeout=60, java_path='java')
        self.output_dir = os.path.join(self.dir, 'out')
        self.validator = MobilityDataValidator(os.path.join(self.dir, 'feed.zip'), self.output_dir, self.settings)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_needs_the_validator_jar(self):
        self.settings.gtfs_validator_jar = os.path.join(self.dir, 'missing.jar')

        with self.assertRaises(MobilityDataValidatorError):
            self.validator.validate()

    @patch('src.mobility_data_validator.subprocess.run')
    def test_runs_the_jar_on_the_feed(self, mock_run):
        mock_run.side_effect = lambda *args, **kwargs: (
            write_outputs(self.output_dir, [{'code': 'a', 'severity': 'ERROR'}]), MagicMock(returncode=0))[1]

        result = self.validator.validate()

        command = mock_run.call_args[0][0]
        self.assertEqual(command[:3], ['java', '-jar', self.jar])
        self.assertIn(os.path.join(self.dir, 'feed.zip'), command)
        self.assertEqual(command[command.index('--country_code') + 1], 'us')
        self.assertEqual([n['code'] for n in result.error], ['a'])

    @patch('src.mobility_data_validator.subprocess.run')
    def test_fails_without_a_report(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='boom', stdout='')

        with self.assertRaises(MobilityDataValidatorError) as raised:
            self.validator.validate()
        self.assertIn('boom', str(raised.exception))

    @patch('src.mobility_data_validator.subprocess.run')
    def test_fails_when_it_cannot_run(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired('java', 60)

        with self.assertRaises(MobilityDataValidatorError):
            self.validator.validate()

    @patch('src.mobility_data_validator.subprocess.run')
    def test_counts_load_failures_as_feed_errors(self, mock_run):
        load_error = {'code': 'i_o_error', 'severity': 'ERROR', 'totalNotices': 1, 'sampleNotices': []}
        mock_run.side_effect = lambda *args, **kwargs: (
            write_outputs(self.output_dir, system_errors=[load_error]), MagicMock(returncode=255))[1]

        result = self.validator.validate()

        self.assertFalse(result.status)
        self.assertEqual(result.error, [{**load_error, 'feedUnreadable': True}])

    @patch('src.mobility_data_validator.subprocess.run')
    def test_only_logs_system_errors_after_a_normal_run(self, mock_run):
        crash = {'code': 'runtime_exception_in_validator_error', 'severity': 'ERROR'}
        mock_run.side_effect = lambda *args, **kwargs: (
            write_outputs(self.output_dir, system_errors=[crash]), MagicMock(returncode=0))[1]

        result = self.validator.validate()

        self.assertTrue(result.status)


@unittest.skipUnless(JAR_AVAILABLE, 'needs java and scripts/download-gtfs-validator.sh')
class TestMobilityDataValidatorJar(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_reports_a_feeds_errors(self):
        feed = shutil.copy(os.path.join(TEST_FILES, 'pathways-foreign-key.zip'), self.dir)

        result = MobilityDataValidator(feed).validate()

        self.assertIn('foreign_key_violation', [n['code'] for n in result.error])
        self.assertTrue(os.path.isfile(result.report_html_path))
        result.clean_up()
        self.assertFalse(os.path.exists(result.output_dir))

    def test_writes_each_run_to_its_own_folder(self):
        feed = shutil.copy(os.path.join(TEST_FILES, 'pathways-good.zip'), self.dir)

        first = MobilityDataValidator(feed).validate()
        second = MobilityDataValidator(feed).validate()

        self.assertNotEqual(first.output_dir, second.output_dir)
        self.assertNotEqual(os.path.dirname(first.output_dir), self.dir)
        first.clean_up()
        second.clean_up()

    def test_reports_a_feed_it_cannot_read(self):
        feed = os.path.join(self.dir, 'feed.zip')
        with open(feed, 'w') as f:
            f.write('not a zip')

        result = MobilityDataValidator(feed).validate()

        self.assertIn('i_o_error', [n['code'] for n in result.error])


if __name__ == '__main__':
    unittest.main()
