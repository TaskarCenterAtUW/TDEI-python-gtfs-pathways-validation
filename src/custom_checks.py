from typing import List, Optional

from .gtfs_feed import GtfsFeed

# How many example rows a notice keeps, as MobilityData does
MAX_SAMPLE_NOTICES = 5

ERROR = 'ERROR'
WARNING = 'WARNING'
INFO = 'INFO'


def make_notice(code: str, severity: str, samples: List[dict]) -> Optional[dict]:
    """
    A notice in MobilityData's report format, so TDEI's notices and MobilityData's are
    reported and judged (see pathways_config.py) the same way:
    `{'code', 'severity', 'totalNotices', 'sampleNotices'}`. Each sample describes one
    occurrence, with MobilityData's field names where they apply, e.g.
    `{'filename': 'pathways.txt', 'csvRowNumber': 4, 'pathwayId': 'p1', 'fieldName': 'length'}`.
    Returns `None` when there are no samples, so callers can skip empty checks.
    """
    if not samples:
        return None
    return {
        'code': code,
        'severity': severity,
        'totalNotices': len(samples),
        'sampleNotices': samples[:MAX_SAMPLE_NOTICES],
        'source': 'tdei',
    }


def run_custom_checks(feed: GtfsFeed) -> List[dict]:
    """
    TDEI's own pathways checks, run after MobilityData's validator on the same feed.
    Returns notices made with `make_notice` (codes prefixed `tdei_`); each one's
    severity, and pathways_config.py, decide whether it fails the upload.
    """
    # The checks, from the Workspaces pathways editor's (workspaces-frontend services/gtfs-*.ts),
    # restated for GTFS files. [editor: <name>] is the editor's check. Severities follow the
    # editor's: its warnings are WARNING, its suggestions INFO; none fail an upload unless
    # made ERROR. Edit, add or delete lines; each line left becomes a check and its tests.
    #
    # Notes for all of them:
    # - "Stop" means any row of stops.txt; a stop's type is its location_type (empty means 0).
    # - A pathway goes from_stop_id -> to_stop_id, and back too unless is_bidirectional is 0.
    # - GTFS has no pathway geometry, so "distance" is the straight line between the two
    #   stops' stop_lat/stop_lon, and checks that need it skip stops without coordinates
    #   (generic nodes and boarding areas may have none).
    # - A station's stops are those whose parent_station is the station, or is a platform
    #   in it (for boarding areas).
    #
    # 1. Not checked by MobilityData: port these.
    #
    # @test unit: tdei_level_change_same_level (WARNING): a stairs, escalator or elevator pathway
    #   (pathway_mode 2, 4, 5) whose two stops have the same level_id. [editor: same_level]
    # @test unit: tdei_escalator_two_way (INFO): an escalator (pathway_mode 4) with
    #   is_bidirectional 1. [editor: escalator_two_way]
    # @test unit: tdei_walkway_changes_level (INFO): a walkway, moving sidewalk, fare gate or exit
    #   gate (pathway_mode 1, 3, 6, 7) between stops on different levels, with no max_slope
    #   (a ramp would have one). [editor: walkway_changes_level]
    # @test unit: tdei_stair_count_direction (WARNING): stairs (pathway_mode 2) whose stair_count
    #   sign doesn't match the direction: positive should go up (to_stop's level_index higher
    #   than from_stop's), negative down. Skipped when either level_index is missing or they're
    #   equal, or stair_count is 0. [editor: stair_count_direction]
    # @test unit: tdei_length_mismatch (INFO): a pathway of mode 1, 3, 6 or 7 whose length is
    #   under 0.5x or over 2x the distance between its stops, and at least 10 m off. (Paths
    #   aren't straight, so this may need a looser upper bound than the editor's, which measures
    #   the drawn line.) [editor: length_mismatch]
    # @test unit: tdei_traversal_time_mismatch (INFO): a moving sidewalk or escalator
    #   (pathway_mode 3, 4) whose distance / traversal_time is under 0.1 m/s or over 5 m/s.
    #   [editor: traversal_time_mismatch]
    # @test unit: tdei_duplicate_pathway (WARNING): two pathways of the same pathway_mode joining
    #   the same two stops the same way (both two-way, or both one-way in the same direction).
    #   The editor also requires the drawn lengths to be within 10%, so side-by-side routes
    #   aren't flagged; here, compare length when both have one. [editor: duplicate_pathway]
    # @test unit: tdei_boarding_area_level (WARNING): a boarding area (type 4) whose level_id differs
    #   from its platform's (its parent_station's). [editor: boarding_area_level]
    # @test unit: tdei_no_step_free_route (INFO): a platform or boarding area that can be reached
    #   from its station's entrances only through stairs or escalators (pathway_mode 2, 4).
    #   [editor: no_step_free]
    # @test unit: tdei_elevator_only_route (INFO): a platform or boarding area that has a step-free
    #   route from an entrance, but only through an elevator (pathway_mode 5). [editor: elevator_only]
    # @test unit: tdei_level_unreachable (WARNING): a level_id that stops in a station use, where
    #   none of those stops can be reached from any station's entrances. [editor: level_unreachable]
    # @test unit: tdei_empty_level (WARNING): a level in levels.txt that no stop's level_id names.
    #   [editor: empty_level]
    # @test unit: tdei_level_index_repeated (WARNING): a station with two levels (used by its stops)
    #   that have the same level_index. [editor: station_level_order]
    # @test unit: tdei_level_index_far_from_street (INFO): a station whose levels' level_index are
    #   all more than 20 from 0 (street level), e.g. numbered across the whole feed.
    #   [editor: station_level_order]
    # @test unit: tdei_stop_far_from_level (INFO): a stop at least 500 m from the median location of
    #   the other stops on its level (levels with 3 or more located stops). [editor: far_stop]
    # @test unit: tdei_missing_level_id (INFO): a platform, generic node or boarding area (type 0,
    #   3, 4) in a station that uses levels, with no level_id. (MobilityData only requires level_id
    #   at elevators.) [editor: missing_level]
    #
    # 2. Partly checked by MobilityData. It reports these cases, but only as
    #    pathway_unreachable_location; keep them only if a clearer message is worth it.
    #
    # @test unit: tdei_station_without_entrance (WARNING): a station with pathways but no entrance
    #   (type 2) among its stops. [editor: no_entrance]
    # @test unit: tdei_stop_without_pathway (WARNING): a stop in a station with pathways that no
    #   pathway touches (skipping the station itself, and platforms with boarding areas).
    #   [editor: isolated]
    #
    # 3. Already checked by MobilityData (its code in brackets): delete unless the report
    #    should repeat them.
    #
    # - unreachable / no way back to an entrance [pathway_unreachable_location]
    # - exit gate two-way [bidirectional_exit_gate]
    # - pathway ends at a station [pathway_to_wrong_location_type]
    # - pathway ends at a platform with boarding areas [pathway_to_platform_with_boarding_areas]
    # - pathway loop [pathway_loop]
    # - pathway to a stop_access 1 stop [pathway_to_stop_with_access_outside_of_station_pathways]
    # - elevator end without level_id [missing_level_id]
    # - generic node dead end [pathway_dangling_generic_node]
    # - duplicate stop_id / pathway_id [duplicate_key]
    # - parent_station / level_id / from_stop_id / to_stop_id not found [foreign_key_violation]
    # - parent_station of the wrong type [wrong_parent_location_type]
    # - entrance, generic node or boarding area without parent_station [location_without_parent_station]
    # - station with parent_station [station_with_parent_station]
    # - missing stop_name for types 0-2 [missing_stop_name]
    # - missing pathway_mode, is_bidirectional, level_index [missing_required_field]
    # - station no stop belongs to [unused_station]
    #
    # 4. Editor only: about level outlines, which GTFS doesn't have; not portable.
    #
    # - level outline without level_id [editor: level_area_no_id]
    # - level outline much larger than its stops [editor: large_outline]
    # - stop or pathway outside its level's outline [editor: outside_level]
    # - station without stop_id [editor: station_no_stop_id] (in GTFS, stop_id is required)
    # - pathway end that isn't a stop [editor: pathway_end] (in GTFS, the ends are stop_ids)
    notices: List[Optional[dict]] = []
    return [notice for notice in notices if notice]
