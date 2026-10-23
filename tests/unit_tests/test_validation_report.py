import io
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch

from src.custom_checks import make_notice, MAX_SAMPLE_NOTICES
from src.gtfs_feed import GtfsFeed
from src.pathways_feed_validation import PathwaysFeedValidation
from src.mobility_data_validator import MobilityDataResult
from src.validation_report import (ValidationReport, notice_outcome, FAILS_UPLOAD, DOWNGRADED, WARNING, INFO)

TEST_FILES = os.path.join(os.path.dirname(__file__), 'test_files')


def notice(code, severity, **sample):
    return {'code': code, 'severity': severity, 'totalNotices': 1, 'sampleNotices': [sample] if sample else []}


class TestNoticeOutcome(unittest.TestCase):

    def test_errors_fail_the_upload_unless_downgraded(self):
        self.assertEqual(notice_outcome(notice('foreign_key_violation', 'ERROR', childFilename='trips.txt')),
                         FAILS_UPLOAD)
        self.assertEqual(notice_outcome({**notice('tdei_example', 'ERROR'), 'source': 'tdei'}), FAILS_UPLOAD)
        self.assertEqual(notice_outcome(notice('invalid_url', 'ERROR', filename='pathways.txt')), DOWNGRADED)
        self.assertEqual(notice_outcome(notice('expired_calendar', 'WARNING')), WARNING)
        self.assertEqual(notice_outcome(notice('unknown_file', 'INFO')), INFO)

    def test_unreadable_feeds_fail_the_upload_even_with_a_downgraded_code(self):
        self.assertEqual(notice_outcome({**notice('u_r_i_syntax_error', 'ERROR'), 'feedUnreadable': True}), FAILS_UPLOAD)


class TestValidationReport(unittest.TestCase):

    def setUp(self):
        self.report = ValidationReport(
            feed_name='feed.zip',
            is_valid=False,
            mobility_data_notices=[notice('unknown_file', 'INFO', filename='x.txt'),
                                   notice('foreign_key_violation', 'ERROR', childFilename='pathways.txt')],
            custom_notices=[notice('tdei_example', 'WARNING', pathwayId='<p1>')],
            validator_version='8.0.1')

    def test_lists_every_notice_with_its_source_and_outcome_worst_first(self):
        notices = self.report.to_json()['notices']

        self.assertEqual([(n['code'], n['source'], n['outcome']) for n in notices], [
            ('foreign_key_violation', 'mobilitydata', FAILS_UPLOAD),
            ('tdei_example', 'tdei', WARNING),
            ('unknown_file', 'mobilitydata', INFO),
        ])

    def test_summarizes(self):
        summary = self.report.summary

        self.assertFalse(summary['valid'])
        self.assertEqual(summary['feed'], 'feed.zip')
        self.assertEqual(summary['gtfsValidatorVersion'], '8.0.1')
        self.assertEqual(summary['codesByOutcome'],
                         {FAILS_UPLOAD: 1, DOWNGRADED: 0, WARNING: 1, INFO: 1})

    def test_includes_metrics_in_the_summary_and_html(self):
        metrics = {'completeness': {'pathwaysWithLength': {'count': 6, 'total': 9, 'percent': 66.7}},
                   'connectivity': {}}
        report = ValidationReport(feed_name='feed.zip', is_valid=True, mobility_data_notices=[],
                                  custom_notices=[], metrics=metrics)

        self.assertEqual(report.summary['metrics'], metrics)
        self.assertIn('<td>Pathways with a length</td><td>6 of 9</td><td>66.7%</td>', report.to_html())
        self.assertIsNone(self.report.summary['metrics'])
        self.assertNotIn('Metrics', self.report.to_html())

    def test_renders_html_with_escaped_values(self):
        page = self.report.to_html()

        self.assertIn('Failed', page)
        self.assertIn('foreign_key_violation', page)
        self.assertIn('&lt;p1&gt;', page)
        self.assertNotIn('<p1>', page)

    def test_zips_the_reports_with_mobility_datas_own(self):
        mobility_data_dir = tempfile.mkdtemp()
        try:
            for name in ['report.json', 'report.html']:
                with open(os.path.join(mobility_data_dir, name), 'w') as f:
                    f.write('{}')
            self.report.mobility_data_dir = mobility_data_dir

            with zipfile.ZipFile(io.BytesIO(self.report.to_zip())) as archive:
                names = sorted(archive.namelist())
                report = json.loads(archive.read('report.json'))
        finally:
            shutil.rmtree(mobility_data_dir)

        self.assertEqual(names, ['mobilitydata/report.html', 'mobilitydata/report.json', 'report.html', 'report.json'])
        self.assertEqual(len(report['notices']), 3)


class TestMakeNotice(unittest.TestCase):

    def test_keeps_a_few_samples_and_the_total(self):
        samples = [{'csvRowNumber': i} for i in range(MAX_SAMPLE_NOTICES + 3)]

        made = make_notice('tdei_example', 'WARNING', samples)

        self.assertEqual(made['totalNotices'], MAX_SAMPLE_NOTICES + 3)
        self.assertEqual(len(made['sampleNotices']), MAX_SAMPLE_NOTICES)
        self.assertEqual(made['source'], 'tdei')

    def test_skips_checks_that_found_nothing(self):
        self.assertIsNone(make_notice('tdei_example', 'WARNING', []))


class TestGtfsFeed(unittest.TestCase):

    def test_reads_the_pathways_tables_with_row_numbers(self):
        feed = GtfsFeed.from_zip(os.path.join(TEST_FILES, 'pathways-good.zip'))

        self.assertTrue(feed.pathways and feed.stops and feed.levels)
        self.assertEqual(feed.pathways[0]['csvRowNumber'], 2)
        self.assertIn(feed.pathways[0]['from_stop_id'], feed.stops_by_id)

    def test_reads_a_byte_order_mark_and_a_folder_in_the_zip(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('feed/levels.txt', '﻿level_id, level_index\n L1 ,0\n'.encode('utf-8'))
        path = os.path.join(tempfile.mkdtemp(), 'feed.zip')
        with open(path, 'wb') as f:
            f.write(buffer.getvalue())

        feed = GtfsFeed.from_zip(path)

        self.assertEqual(feed.levels, [{'level_id': 'L1', 'level_index': '0', 'csvRowNumber': 2}])
        self.assertIn('L1', feed.levels_by_id)

    def test_builds_from_rows_for_tests(self):
        feed = GtfsFeed.from_rows(stops=[{'stop_id': 'S1', 'location_type': 1}])

        self.assertEqual(feed.stops_by_id['S1'], {'stop_id': 'S1', 'location_type': '1', 'csvRowNumber': 2})


class TestValidationWithCustomChecksAndReport(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.feed = shutil.copy(os.path.join(TEST_FILES, 'pathways-good.zip'), self.dir)
        with patch.object(PathwaysFeedValidation, '__init__', return_value=None):
            self.validator = PathwaysFeedValidation()
        self.validator.file_path = 'https://account.blob.core.windows.net/gtfspathways/2026/10/feed.zip'
        self.validator.file_relative_path = 'feed.zip'
        self.validator.container_name = 'gtfspathways'
        self.validator.client = MagicMock()
        self.validator.client.create_file.return_value.get_remote_url.return_value = 'https://reports/feed-report.zip'
        self.validator.download_single_file = MagicMock(return_value=self.feed)
        self.validator.report = None
        self.validator.report_url = None

        patcher = patch('src.pathways_feed_validation.MobilityDataValidator')
        self.mock_mobility_data = patcher.start()
        self.addCleanup(patcher.stop)
        self.mobility_data_notices = [notice('unknown_file', 'INFO')]
        self.mock_mobility_data.return_value.validate.side_effect = lambda: MobilityDataResult(
            {'notices': self.mobility_data_notices}, os.path.join(self.dir, 'mobilitydata'))

        clean_up = patch.object(PathwaysFeedValidation, 'clean_up')
        clean_up.start()
        self.addCleanup(clean_up.stop)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def validate_with(self, custom_notices):
        with patch('src.pathways_feed_validation.run_custom_checks', return_value=custom_notices):
            return self.validator.validate()

    def test_passes_with_only_custom_warnings(self):
        is_valid, message = self.validate_with([notice('tdei_example', 'WARNING')])

        self.assertTrue(is_valid)
        self.assertEqual(message, '')
        self.assertEqual([n['code'] for n in self.validator.report.notices], ['tdei_example', 'unknown_file'])

    def test_fails_with_a_custom_error(self):
        is_valid, message = self.validate_with([notice('tdei_example', 'ERROR')])

        self.assertFalse(is_valid)
        self.assertEqual([n['code'] for n in json.loads(message)], ['tdei_example'])
        self.assertFalse(self.validator.report.summary['valid'])

    def test_fails_with_mobility_data_and_custom_errors(self):
        self.mobility_data_notices = [notice('foreign_key_violation', 'ERROR', childFilename='pathways.txt')]

        is_valid, message = self.validate_with([notice('tdei_example', 'ERROR')])

        self.assertFalse(is_valid)
        self.assertEqual([n['code'] for n in json.loads(message)], ['foreign_key_violation', 'tdei_example'])

    def test_fails_with_any_mobility_data_error(self):
        self.mobility_data_notices = [notice('foreign_key_violation', 'ERROR', childFilename='trips.txt')]

        is_valid, message = self.validate_with([])

        self.assertFalse(is_valid)
        self.assertEqual([n['code'] for n in json.loads(message)], ['foreign_key_violation'])
        self.assertEqual(self.validator.report.summary['codesByOutcome'][FAILS_UPLOAD], 1)

    def test_reports_the_feeds_metrics(self):
        self.validate_with([])

        metrics = self.validator.report.summary['metrics']
        self.assertGreater(metrics['completeness']['stationsWithPathways']['count'], 0)
        self.assertIn('platformsStepFree', metrics['connectivity'])

    def test_ignores_custom_checks_that_crash(self):
        with patch('src.pathways_feed_validation.run_custom_checks', side_effect=ValueError('bug')):
            is_valid, _ = self.validator.validate()

        self.assertTrue(is_valid)
        self.assertIsNotNone(self.validator.report.summary['metrics'])

    def test_ignores_metrics_that_crash(self):
        with patch('src.pathways_feed_validation.measure_feed', side_effect=ValueError('bug')):
            is_valid, _ = self.validate_with([])

        self.assertTrue(is_valid)
        self.assertIsNone(self.validator.report.summary['metrics'])

    def test_uploads_the_report_next_to_the_feed(self):
        self.validate_with([])

        name = self.validator.client.create_file.call_args[0][0]
        self.assertRegex(name, r'^2026/10/feed-validation-report-[0-9a-f]{8}\.zip$')
        uploaded = self.validator.client.create_file.return_value.upload.call_args[0][0]
        with zipfile.ZipFile(io.BytesIO(uploaded)) as archive:
            self.assertIn('report.html', archive.namelist())
        self.assertEqual(self.validator.report_url, 'https://reports/feed-report.zip')

    def test_still_validates_when_the_upload_fails(self):
        self.validator.client.create_file.return_value.upload.side_effect = Exception('storage down')

        is_valid, _ = self.validate_with([])

        self.assertTrue(is_valid)
        self.assertIsNone(self.validator.report_url)


if __name__ == '__main__':
    unittest.main()
