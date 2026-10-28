import csv
import io
import os
import shutil
import tempfile
import unittest
import zipfile

from src.one_way_service import ARRIVAL_ONLY, DEPARTURE_ONLY, explain_one_way_locations, platform_service
from src.validation_report import DOWNGRADED, FAILS_UPLOAD, notice_outcome


def write_feed(folder, **tables):
    path = os.path.join(folder, 'feed.zip')
    with zipfile.ZipFile(path, 'w') as archive:
        for name, rows in tables.items():
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            archive.writestr(f'{name}.txt', out.getvalue())
    return path


def stop(stop_id, location_type, parent='S'):
    return {'stop_id': stop_id, 'location_type': location_type, 'parent_station': parent}


def pathway(pathway_id, from_stop, to_stop, bidirectional=1):
    return {'pathway_id': pathway_id, 'from_stop_id': from_stop, 'to_stop_id': to_stop, 'pathway_mode': 1,
            'is_bidirectional': bidirectional}


def stop_time(trip, sequence, stop_id, pickup='', drop_off=''):
    return {'trip_id': trip, 'stop_sequence': sequence, 'stop_id': stop_id, 'pickup_type': pickup, 'drop_off_type': drop_off}


def unreachable(*samples):
    return {'code': 'pathway_unreachable_location', 'severity': 'ERROR', 'totalNotices': len(samples),
            'sampleNotices': list(samples)}


def sample(stop_id, has_entrance, has_exit):
    return {'stopId': stop_id, 'hasEntrance': has_entrance, 'hasExit': has_exit}


class TestOneWayService(unittest.TestCase):
    """
    A terminal: trains end at platform ARR (riders leave through its boarding area ARR-B, then node OUT)
    and start at DEP (riders reach its boarding area DEP-B through node IN). OUT also leads into a LOBBY
    that leads on to IN, as station lobbies do. MID is a through platform.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.feed = write_feed(
            self.dir,
            stops=[stop('S', 1, ''), stop('E', 2), stop('ARR', 0), stop('ARR-B', 4, 'ARR'), stop('DEP', 0),
                   stop('DEP-B', 4, 'DEP'), stop('MID', 0), stop('OUT', 3), stop('IN', 3), stop('LOST', 3),
                   stop('LOBBY', 3)],
            pathways=[pathway('out1', 'ARR-B', 'OUT', 0), pathway('out2', 'OUT', 'E', 0),
                      pathway('in1', 'E', 'IN', 0), pathway('in2', 'IN', 'DEP-B', 0), pathway('mid', 'E', 'MID', 0),
                      pathway('lobby1', 'OUT', 'LOBBY', 0), pathway('lobby2', 'LOBBY', 'IN', 0)],
            stop_times=[stop_time('t1', 1, 'MID'), stop_time('t1', 2, 'ARR'),
                        stop_time('t2', 1, 'DEP'), stop_time('t2', 2, 'MID'),
                        stop_time('t3', 1, 'X'), stop_time('t3', 2, 'MID'), stop_time('t3', 3, 'Y')])

    def test_finds_arrival_and_departure_only_platforms_from_the_trips(self):
        self.assertEqual(platform_service(self.feed, {'ARR', 'DEP', 'MID'}), {'ARR': ARRIVAL_ONLY, 'DEP': DEPARTURE_ONLY})

    def test_reads_pickup_and_drop_off_types_too(self):
        feed = write_feed(self.dir, stop_times=[
            stop_time('t1', 1, 'A'), stop_time('t1', 2, 'P', pickup='1'), stop_time('t1', 3, 'B'),
            stop_time('t2', 1, 'A'), stop_time('t2', 2, 'Q', drop_off='1'), stop_time('t2', 3, 'B')])

        self.assertEqual(platform_service(feed, {'P', 'Q'}), {'P': ARRIVAL_ONLY, 'Q': DEPARTURE_ONLY})

    def test_downgrades_locations_one_way_like_their_platforms_service(self):
        notice = unreachable(sample('ARR-B', False, True), sample('OUT', False, True),
                             sample('DEP-B', True, False), sample('IN', True, False),
                             sample('MID', False, True),  # a through platform: should be two-way
                             sample('LOST', False, False))  # cut off both ways

        still, one_way = explain_one_way_locations(self.feed, [notice])[id(notice)]

        self.assertEqual([s['stopId'] for s in still['sampleNotices']], ['MID', 'LOST'])
        self.assertEqual(still['totalNotices'], 2)
        self.assertEqual([(s['stopId'], s['oneWayService']) for s in one_way['sampleNotices']], [
            ('ARR-B', ARRIVAL_ONLY), ('OUT', ARRIVAL_ONLY), ('DEP-B', DEPARTURE_ONLY), ('IN', DEPARTURE_ONLY)])
        self.assertEqual((notice_outcome(still), notice_outcome(one_way)), (FAILS_UPLOAD, DOWNGRADED))

    def test_a_location_one_way_the_wrong_way_still_fails(self):
        notice = unreachable(sample('ARR-B', True, False))  # riders can get in to where trains only arrive

        self.assertEqual(explain_one_way_locations(self.feed, [notice]), {})

    def test_keeps_locations_mobility_data_didnt_sample_as_errors(self):
        notice = {**unreachable(sample('ARR-B', False, True)), 'totalNotices': 1001}

        still, one_way = explain_one_way_locations(self.feed, [notice])[id(notice)]

        self.assertEqual((still['totalNotices'], still['sampleNotices']), (1000, []))
        self.assertEqual(one_way['totalNotices'], 1)


if __name__ == '__main__':
    unittest.main()
