import unittest

from src.pathway_errors import is_pathway_sample, lenient_replacements
from src.validation_report import DOWNGRADED, FAILS_UPLOAD, notice_outcome

PATHWAY_STOPS = {'node1', 'entrance1'}


def error(code, *samples, total=None):
    return {'code': code, 'severity': 'ERROR', 'totalNotices': total or len(samples), 'sampleNotices': list(samples)}


class TestPathwayErrors(unittest.TestCase):

    def test_tells_pathways_data_by_file_or_stop(self):
        self.assertTrue(is_pathway_sample({'filename': 'pathways.txt'}, PATHWAY_STOPS))
        self.assertTrue(is_pathway_sample({'childFilename': 'stops.txt', 'parentFilename': 'levels.txt'}, PATHWAY_STOPS))
        self.assertTrue(is_pathway_sample({'filename': 'stops.txt', 'stopId': 'node1'}, PATHWAY_STOPS))
        self.assertFalse(is_pathway_sample({'filename': 'stops.txt', 'stopId': 'platform1'}, PATHWAY_STOPS))
        self.assertFalse(is_pathway_sample({'filename': 'trips.txt'}, PATHWAY_STOPS))

    def test_marks_mobility_datas_pathway_codes(self):
        exit_gate = error('bidirectional_exit_gate', {'csvRowNumber': 4})

        [marked] = lenient_replacements([exit_gate], PATHWAY_STOPS)[id(exit_gate)]

        self.assertTrue(marked['pathwayData'])
        self.assertEqual(notice_outcome(marked), DOWNGRADED)

    def test_splits_an_error_in_and_outside_pathways_data(self):
        out_of_range = error('number_out_of_range', {'filename': 'pathways.txt'}, {'filename': 'routes.txt'}, total=5)

        core, local = lenient_replacements([out_of_range], PATHWAY_STOPS)[id(out_of_range)]

        self.assertEqual((core['totalNotices'], core['sampleNotices']), (4, [{'filename': 'routes.txt'}]))  # 3 unsampled
        self.assertEqual((local['totalNotices'], local['pathwayData']), (1, True))
        self.assertEqual((notice_outcome(core), notice_outcome(local)), (FAILS_UPLOAD, DOWNGRADED))

    def test_leaves_core_errors_and_unreadable_feeds(self):
        core = error('foreign_key_violation', {'childFilename': 'trips.txt', 'parentFilename': 'routes.txt'})
        unreadable = {**error('i_o_error', {'filename': 'pathways.txt'}), 'feedUnreadable': True}

        self.assertEqual(lenient_replacements([core, unreadable], PATHWAY_STOPS), {})


if __name__ == '__main__':
    unittest.main()
