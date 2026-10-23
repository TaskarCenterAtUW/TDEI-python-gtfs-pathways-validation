import copy
import unittest
from unittest.mock import patch

from src import custom_checks
from src.custom_checks import CHECKS, ERROR, run_custom_checks
from src.gtfs_feed import GtfsFeed
from src.pathways_metrics import measure_feed


def stop(stop_id, location_type, level_id, lat, lon, parent='S'):
    return {'stop_id': stop_id, 'stop_name': stop_id, 'location_type': location_type, 'parent_station': parent,
            'level_id': level_id, 'stop_lat': lat, 'stop_lon': lon}


def pathway(pathway_id, from_stop, to_stop, mode, bidirectional=1, **fields):
    return {'pathway_id': pathway_id, 'from_stop_id': from_stop, 'to_stop_id': to_stop, 'pathway_mode': mode,
            'is_bidirectional': bidirectional, 'length': '', 'traversal_time': '', 'stair_count': '',
            'max_slope': '', **fields}


# The standard station: street-level entrance E1 -> node NT -> (ramp, stairs or elevator) down to
# concourse node C -> (one-way escalator or elevator) down to platform P1, or ramp down to boarding
# area B2a of platform P2. P1 and B2a are joined by a walkway. It passes every check.
STATION = {
    'levels': [
        {'level_id': 'L0', 'level_index': 0},
        {'level_id': 'Lm1', 'level_index': -1},
        {'level_id': 'Lm2', 'level_index': -2},
    ],
    'stops': [
        stop('S', 1, '', 39.30000, -76.60000, parent=''),
        stop('E1', 2, 'L0', 39.30000, -76.60000),
        stop('NT', 3, 'L0', 39.30005, -76.60000),
        stop('C', 3, 'Lm1', 39.30010, -76.60000),
        stop('P1', 0, 'Lm2', 39.30015, -76.60000),
        stop('P2', 0, 'Lm2', 39.30015, -76.60010),
        stop('B2a', 4, 'Lm2', 39.30015, -76.60008, parent='P2'),
        stop('B2b', 4, 'Lm2', 39.30015, -76.60012, parent='P2'),
    ],
    'pathways': [
        pathway('walk_e', 'E1', 'NT', 1, length=6),
        pathway('ramp_top', 'NT', 'C', 1, length=8, max_slope=0.05),
        pathway('stairs_top', 'NT', 'C', 2, stair_count=-20),
        pathway('elev_top', 'NT', 'C', 5),
        pathway('esc_down', 'C', 'P1', 4, bidirectional=0, length=15, traversal_time=30),
        pathway('elev_low', 'C', 'P1', 5),
        pathway('ramp_low', 'C', 'B2a', 1, length=10, max_slope=0.05),
        pathway('walk_ba', 'B2a', 'B2b', 1, length=4),
        pathway('transfer', 'P1', 'B2a', 1, length=6),
    ],
}
ID_FIELDS = {'levels': 'level_id', 'stops': 'stop_id', 'pathways': 'pathway_id'}


class StationTestCase(unittest.TestCase):
    """Each test starts from the standard station, changes it, and checks what's flagged."""

    def setUp(self):
        self.tables = copy.deepcopy(STATION)

    def row(self, table, row_id):
        return next(r for r in self.tables[table] if r[ID_FIELDS[table]] == row_id)

    def edit(self, table, row_id, **fields):
        self.row(table, row_id).update(fields)

    def remove(self, table, row_id):
        self.tables[table].remove(self.row(table, row_id))

    def add(self, table, row):
        self.tables[table].append(row)

    def notices(self):
        return {n['code']: n for n in run_custom_checks(GtfsFeed.from_rows(**self.tables))}

    def samples(self, code):
        notice = self.notices().get(code)
        return notice['sampleNotices'] if notice else []

    def flagged(self, code):
        """The ids of what a check flagged: pathway, stop or level ids."""
        return [s.get('pathwayId') or s.get('stopId') or s.get('levelId') for s in self.samples(code)]


class TestStandardStation(StationTestCase):

    def test_passes_every_check(self):
        self.assertEqual(self.notices(), {})

    def test_has_28_checks(self):
        self.assertEqual(len(CHECKS), 28)
        self.assertEqual(len({code for code, _, _ in CHECKS}), 28)

    def test_samples_point_at_the_row(self):
        self.edit('pathways', 'esc_down', is_bidirectional=1)

        notice = self.notices()['tdei_escalator_two_way']

        self.assertEqual(notice['severity'], 'WARNING')
        self.assertEqual(notice['source'], 'tdei')
        self.assertEqual(notice['sampleNotices'], [{'filename': 'pathways.txt', 'csvRowNumber': 6,
                                                    'pathwayId': 'esc_down', 'fromStopId': 'C', 'toStopId': 'P1',
                                                    'defectId': 'tdei_escalator_two_way:esc_down'}])

    def test_skips_a_check_that_crashes(self):
        def crash(model):
            raise ValueError('bug')
        self.edit('pathways', 'esc_down', is_bidirectional=1)

        with patch.object(custom_checks, 'CHECKS', [('tdei_crash', ERROR, crash)] + CHECKS), \
                self.assertLogs('TDEI_CHECKS', level='ERROR'):
            codes = list(self.notices())

        self.assertEqual(codes, ['tdei_escalator_two_way'])


class TestPathwayChecks(StationTestCase):

    def test_level_change_same_level(self):
        self.add('pathways', pathway('elev_flat', 'E1', 'NT', 5))

        self.assertEqual(self.flagged('tdei_level_change_same_level'), ['elev_flat'])
        self.assertEqual(self.notices()['tdei_level_change_same_level']['severity'], 'ERROR')

    def test_stairs_same_level(self):
        self.add('pathways', pathway('stairs_flat', 'E1', 'NT', 2, stair_count=10))

        self.assertEqual(self.flagged('tdei_stairs_same_level'), ['stairs_flat'])
        self.assertEqual(self.flagged('tdei_level_change_same_level'), [])
        self.assertEqual(self.notices()['tdei_stairs_same_level']['severity'], 'WARNING')

    def test_escalator_two_way(self):
        self.edit('pathways', 'esc_down', is_bidirectional=1)

        self.assertEqual(self.flagged('tdei_escalator_two_way'), ['esc_down'])

    def test_walkway_changes_level(self):
        self.edit('pathways', 'ramp_top', max_slope='')

        self.assertEqual(self.flagged('tdei_walkway_changes_level'), ['ramp_top'])

    def test_walkway_between_levels_at_the_same_height_is_fine(self):
        self.edit('pathways', 'ramp_top', max_slope='')
        self.edit('levels', 'Lm1', level_index=0)

        self.assertEqual(self.flagged('tdei_walkway_changes_level'), [])

    def test_stair_count_direction(self):
        self.edit('pathways', 'stairs_top', stair_count=20)

        self.assertEqual(self.flagged('tdei_stair_count_direction'), ['stairs_top'])
        self.assertEqual(self.notices()['tdei_stair_count_direction']['severity'], 'WARNING')

    def test_stair_count_zero_is_skipped(self):
        self.edit('pathways', 'stairs_top', stair_count=0)

        self.assertEqual(self.flagged('tdei_stair_count_direction'), [])

    def test_length_too_long(self):
        self.edit('pathways', 'walk_e', length=500)

        self.assertEqual(self.flagged('tdei_length_too_long'), ['walk_e'])
        self.assertEqual(self.notices()['tdei_length_too_long']['severity'], 'INFO')

    def test_length_too_short(self):
        self.edit('stops', 'E1', stop_lat=39.29975)  # about 33 m from NT, but walk_e says 6 m

        self.assertEqual(self.flagged('tdei_length_too_short'), ['walk_e'])
        self.assertEqual(self.flagged('tdei_length_too_long'), [])
        self.assertEqual(self.notices()['tdei_length_too_short']['severity'], 'WARNING')

    def test_length_short_of_a_platform_is_fine(self):
        self.edit('stops', 'P1', stop_lat=39.30045)  # P1's point is 33 m from B2a; the transfer is 6 m
        self.edit('stops', 'P1', stop_lon=-76.60008)

        self.assertEqual(self.flagged('tdei_length_too_short'), [])

    def test_length_over_twice_the_distance_but_under_10_m_off_is_fine(self):
        self.edit('pathways', 'walk_e', length=12)

        self.assertEqual(self.flagged('tdei_length_too_long'), [])

    def test_traversal_time_mismatch(self):
        self.edit('pathways', 'esc_down', traversal_time=1)

        self.assertEqual(self.flagged('tdei_traversal_time_mismatch'), ['esc_down'])

    def test_traversal_time_uses_the_distance_without_a_length(self):
        self.edit('pathways', 'esc_down', length='', traversal_time=600)

        self.assertEqual(self.flagged('tdei_traversal_time_mismatch'), ['esc_down'])

    def test_duplicate_pathway(self):
        self.add('pathways', pathway('walk_ba2', 'B2b', 'B2a', 1, length=4))

        self.assertEqual(self.flagged('tdei_duplicate_pathway'), ['walk_ba2'])
        self.assertEqual(self.samples('tdei_duplicate_pathway')[0]['duplicateOfPathwayId'], 'walk_ba')

    def test_pathway_ends_far_apart(self):
        self.edit('stops', 'P1', stop_lat=39.30070)  # about 60 m from C: too far for an elevator, not an escalator

        self.assertEqual(self.flagged('tdei_pathway_ends_far_apart'), ['elev_low'])
        self.assertEqual(self.samples('tdei_pathway_ends_far_apart')[0]['maxDistance'], 50)

    def test_side_by_side_and_opposite_one_way_pathways_are_fine(self):
        self.add('pathways', pathway('walk_ba_long', 'B2a', 'B2b', 1, length=8))
        self.add('pathways', pathway('one_way_out', 'B2a', 'B2b', 1, bidirectional=0))
        self.add('pathways', pathway('one_way_back', 'B2b', 'B2a', 1, bidirectional=0))

        self.assertEqual(self.flagged('tdei_duplicate_pathway'), [])


class TestLevelChecks(StationTestCase):

    def test_boarding_area_level(self):
        self.edit('stops', 'B2b', level_id='Lm1')

        self.assertEqual(self.flagged('tdei_boarding_area_level'), ['B2b'])
        self.assertEqual(self.notices()['tdei_boarding_area_level']['severity'], 'ERROR')

    def test_level_unreachable(self):
        self.add('levels', {'level_id': 'Lm3', 'level_index': -3})
        self.add('stops', stop('X', 3, 'Lm3', 39.30015, -76.60005))

        self.assertEqual(self.flagged('tdei_level_unreachable'), ['Lm3'])
        self.assertEqual(self.samples('tdei_level_unreachable')[0]['defectId'], 'tdei_level_unreachable:S:Lm3')

    def test_empty_level(self):
        self.add('levels', {'level_id': 'L9', 'level_index': 5})

        self.assertEqual(self.flagged('tdei_empty_level'), ['L9'])

    def test_level_index_repeated(self):
        self.edit('levels', 'Lm1', level_index=-2)

        samples = self.samples('tdei_level_index_repeated')

        self.assertEqual([(s['levelId'], s['sameIndexAsLevelId']) for s in samples], [('Lm2', 'Lm1')])

    def test_level_index_far_from_street(self):
        for level_id, index in (('L0', 100), ('Lm1', 99), ('Lm2', 98)):
            self.edit('levels', level_id, level_index=index)

        self.assertEqual(self.flagged('tdei_level_index_far_from_street'), ['S'])

    def test_stop_far_from_level(self):
        self.edit('stops', 'B2b', stop_lat=39.31)

        self.assertEqual(self.flagged('tdei_stop_far_from_level'), ['B2b'])

    def test_missing_level_id(self):
        self.edit('stops', 'C', level_id='')

        self.assertEqual(self.flagged('tdei_missing_level_id'), ['C'])


class TestStationChecks(StationTestCase):

    def test_station_without_entrance(self):
        self.edit('stops', 'E1', location_type=3)

        self.assertEqual(self.flagged('tdei_station_without_entrance'), ['S'])

    def test_stop_far_from_station(self):
        for stop_id in ('P1', 'P2', 'B2a', 'B2b'):  # the whole platform level, moved about 1.1 km
            self.edit('stops', stop_id, stop_lat=float(self.row('stops', stop_id)['stop_lat']) + 0.01)

        self.assertEqual(self.flagged('tdei_stop_far_from_station'), ['P1', 'P2', 'B2a', 'B2b'])
        self.assertEqual(self.flagged('tdei_stop_far_from_level'), [])  # they're still together

    def test_stop_without_pathway(self):
        self.add('stops', stop('P3', 0, 'Lm2', 39.30015, -76.60005))

        self.assertEqual(self.flagged('tdei_stop_without_pathway'), ['P3'])


class TestRouteChecks(StationTestCase):

    def test_entrance_reaches_no_platform(self):
        self.add('stops', stop('E2', 2, 'L0', 39.30000, -76.60005))
        self.add('stops', stop('N2', 3, 'L0', 39.30000, -76.60008))
        self.add('pathways', pathway('dead_end', 'E2', 'N2', 1))

        self.assertEqual(self.flagged('tdei_entrance_reaches_no_platform'), ['E2'])
        self.assertEqual(self.flagged('tdei_entrance_reaches_no_platform_step_free'), [])

    def test_entrance_reaches_no_platform_step_free(self):
        self.add('stops', stop('E3', 2, 'L0', 39.30008, -76.60003))
        self.add('pathways', pathway('stairs_e3', 'E3', 'C', 2, stair_count=-20))

        self.assertEqual(self.flagged('tdei_entrance_reaches_no_platform_step_free'), ['E3'])
        self.assertEqual(self.flagged('tdei_entrance_reaches_no_platform'), [])

    def test_platform_no_step_free_route_in(self):
        self.remove('pathways', 'elev_low')
        self.remove('pathways', 'transfer')

        self.assertEqual(self.flagged('tdei_platform_no_step_free_route_in'), ['P1'])
        # P1 has no way out at all, which MobilityData reports
        self.assertEqual(self.flagged('tdei_platform_no_step_free_exit'), [])

    def test_platform_no_step_free_exit(self):
        self.edit('pathways', 'elev_low', is_bidirectional=0)
        self.remove('pathways', 'transfer')
        self.add('pathways', pathway('stairs_up', 'P1', 'C', 2, bidirectional=0, stair_count=20))

        self.assertEqual(self.flagged('tdei_platform_no_step_free_exit'), ['P1'])
        self.assertEqual(self.flagged('tdei_platform_no_step_free_route_in'), [])

    def test_elevator_only_route(self):
        self.remove('pathways', 'ramp_top')

        self.assertEqual(self.flagged('tdei_elevator_only_route'), ['P1', 'B2a', 'B2b'])

    def test_no_step_free_transfer(self):
        self.remove('pathways', 'transfer')
        self.remove('pathways', 'elev_low')
        self.add('pathways', pathway('stairs_low', 'C', 'P1', 2, stair_count=-10))

        samples = self.samples('tdei_no_step_free_transfer')

        self.assertEqual([(s['stopId'], s['toStopId']) for s in samples], [('P1', 'P2'), ('P2', 'P1')])
        self.assertEqual([s['defectId'] for s in samples],
                         ['tdei_no_step_free_transfer:P1:P2', 'tdei_no_step_free_transfer:P2:P1'])

    def test_platforms_joined_only_through_entrances_are_skipped(self):
        self.add('stops', stop('E4', 2, 'L0', 39.30020, -76.60000))
        self.add('stops', stop('P3', 0, 'Lm2', 39.30020, -76.60002))
        self.add('pathways', pathway('elev_p3', 'E4', 'P3', 5))

        self.assertEqual(self.flagged('tdei_no_step_free_transfer'), [])


class TestEntranceChecks(StationTestCase):

    def test_entrance_without_location(self):
        self.edit('stops', 'E1', stop_lat='')

        self.assertEqual(self.flagged('tdei_entrance_without_location'), ['E1'])

    def test_entrance_not_street_level(self):
        self.edit('stops', 'E1', level_id='Lm1')

        self.assertEqual(self.flagged('tdei_entrance_not_street_level'), ['E1'])


class TestMetrics(StationTestCase):

    def metrics(self):
        return measure_feed(GtfsFeed.from_rows(**self.tables))

    def counts(self, group):
        return {key: (m['count'], m['total']) for key, m in self.metrics()[group].items()}

    def test_completeness_of_the_standard_station(self):
        self.assertEqual(self.counts('completeness'), {
            'stationsWithPathways': (1, 1),
            'stopsWithLevelId': (7, 7),
            'stopsWithWheelchairBoarding': (0, 3),
            'pathwaysWithLength': (6, 9),
            'pathwaysWithTraversalTime': (1, 9),
        })

    def test_connectivity_of_the_standard_station(self):
        self.assertEqual(self.counts('connectivity'), {
            'platformsStepFree': (3, 3),
            'entrancesReachingPlatformStepFree': (1, 1),
            'stationsStepFree': (1, 1),
        })
        self.assertEqual(self.metrics()['connectivity']['platformsStepFree']['percent'], 100.0)

    def test_connectivity_without_step_free_routes(self):
        self.remove('pathways', 'ramp_top')
        self.remove('pathways', 'elev_top')

        self.assertEqual(self.counts('connectivity'), {
            'platformsStepFree': (0, 3),
            'entrancesReachingPlatformStepFree': (0, 1),
            'stationsStepFree': (0, 1),
        })

    def test_counts_wheelchair_boarding_1_or_2(self):
        self.edit('stops', 'E1', wheelchair_boarding=1)
        self.edit('stops', 'P1', wheelchair_boarding=2)
        self.edit('stops', 'P2', wheelchair_boarding=0)

        self.assertEqual(self.counts('completeness')['stopsWithWheelchairBoarding'], (2, 3))

    def test_a_feed_without_pathways_has_no_percentages(self):
        metrics = measure_feed(GtfsFeed.from_rows(stops=[stop('S', 1, '', 39.3, -76.6, parent='')]))

        self.assertEqual(metrics['completeness']['stationsWithPathways'], {'count': 0, 'total': 1, 'percent': 0.0})
        self.assertEqual(metrics['connectivity']['platformsStepFree'], {'count': 0, 'total': 0, 'percent': None})


if __name__ == '__main__':
    unittest.main()
