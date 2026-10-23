import logging
import statistics
from collections import defaultdict
from typing import Callable, List, Optional, Tuple

from .gtfs_feed import GtfsFeed
from .pathways_model import (BOARDING_AREA, ELEVATOR, ENTRANCE, ESCALATOR, EXIT_GATE, FARE_GATE, GENERIC_NODE,
                             MOVING_SIDEWALK, STAIRS, STATION, STEP_FREE_MODES, STOP_OR_PLATFORM, WALKWAY, PathwaysModel,
                             distance_m, to_float, to_int)

logging.basicConfig()
logger = logging.getLogger('TDEI_CHECKS')
logger.setLevel(logging.INFO)

# How many example rows a notice keeps: as many as MobilityData's validator does, so the report lists
# (nearly) every problem
MAX_SAMPLE_NOTICES = 1000

ERROR = 'ERROR'
WARNING = 'WARNING'
INFO = 'INFO'

# How far apart a pathway's two stops can plausibly be, in a straight line, by pathway_mode, and how
# far a stop can be from its station (tuned on MBTA and Baltimore Metro: MBTA's real maximums are
# 283 m for walkways, 113 m for stairs, 28 m for elevators and 297 m from a station)
MAX_PATHWAY_SPAN_METERS = {WALKWAY: 500, MOVING_SIDEWALK: 500, STAIRS: 150, ESCALATOR: 150,
                           ELEVATOR: 50, FARE_GATE: 50, EXIT_GATE: 50}
MAX_STOP_FROM_STATION_METERS = 500
# Fewer steps than this on one level is a short flight within it, e.g. into a lobby (MBTA's are 2-8;
# a full storey takes about 16)
MIN_SAME_LEVEL_STAIR_COUNT = 10

# TDEI's own pathways checks, from the Workspaces pathways editor's (workspaces-frontend
# services/gtfs-*.ts), restated for GTFS files; [editor: <name>] is the editor's check.
# Severities were set in review (2026-10-22). An ERROR means riders would be routed wrongly or not at all;
# it fails the upload only in strict mode (see pathways_strict in config.py). See PathwaysModel
# for what "station", "route" and "step-free" mean here. docs/validation-rules.md lists them all;
# keep it current (a test checks its codes and severities).
#
# Not checked here:
#
# Already checked by MobilityData (its code in brackets):
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
# Editor only: about level outlines, which GTFS doesn't have; not portable.
# - level outline without level_id [editor: level_area_no_id]
# - level outline much larger than its stops [editor: large_outline]
# - stop or pathway outside its level's outline [editor: outside_level]
# - station without stop_id [editor: station_no_stop_id] (in GTFS, stop_id is required)
# - pathway end that isn't a stop [editor: pathway_end] (in GTFS, the ends are stop_ids)

CHECKS: List[Tuple[str, str, Callable[[PathwaysModel], List[dict]]]] = []


def check(code: str, severity: str):
    """Registers a check: a function from the feed's PathwaysModel to its samples, one per problem."""
    def register(fn):
        CHECKS.append((code, severity, fn))
        return fn
    return register


def make_notice(code: str, severity: str, samples: List[dict]) -> Optional[dict]:
    """
    A notice in MobilityData's report format, so TDEI's notices and MobilityData's are
    reported and judged (see pathways_config.py) the same way:
    `{'code', 'severity', 'totalNotices', 'sampleNotices'}`. Each sample describes one
    occurrence, with MobilityData's field names where they apply, e.g.
    `{'filename': 'pathways.txt', 'csvRowNumber': 4, 'pathwayId': 'p1', 'fieldName': 'length'}`,
    plus a `defectId` (see `defect_id`). Returns `None` when there are no samples, so callers can
    skip empty checks.
    """
    if not samples:
        return None
    return {
        'code': code,
        'severity': severity,
        'totalNotices': len(samples),
        'sampleNotices': [{**sample, 'defectId': defect_id(code, sample)} for sample in samples[:MAX_SAMPLE_NOTICES]],
        'source': 'tdei',
    }


def defect_id(code: str, sample: dict) -> str:
    """
    An id for one problem that stays the same while the problem does, from the code and what it's
    about rather than row numbers: e.g. `tdei_stairs_same_level:p1`, `tdei_no_step_free_transfer:P1:P2`
    (from one platform to another), or `tdei_level_unreachable:S:L3` (a level in a station).
    """
    if sample.get('pathwayId'):
        parts = [sample['pathwayId']]
    elif sample.get('stopId'):
        parts = [sample['stopId'], sample.get('toStopId')]
    else:
        parts = [sample.get('stationId'), sample.get('levelId')]
    return ':'.join([code] + [str(part) for part in parts if part])


def run_custom_checks(feed: GtfsFeed) -> List[dict]:
    """
    TDEI's own pathways checks, run after MobilityData's validator on the same feed.
    Returns notices made with `make_notice` (codes prefixed `tdei_`); each one's
    severity, and pathways_config.py, decide whether it fails the upload. A check that
    crashes is logged and skipped, so the others still run.
    """
    model = PathwaysModel(feed)
    notices = []
    for code, severity, fn in CHECKS:
        try:
            notices.append(make_notice(code, severity, fn(model)))
        except Exception as e:
            logger.exception(f' TDEI check {code} failed: {e}')
    return [notice for notice in notices if notice]


def stop_sample(stop: dict, **extra) -> dict:
    return {'filename': 'stops.txt', 'csvRowNumber': stop.get('csvRowNumber'), 'stopId': stop.get('stop_id'),
            'stopName': stop.get('stop_name', ''), **extra}


def pathway_sample(pathway: dict, **extra) -> dict:
    return {'filename': 'pathways.txt', 'csvRowNumber': pathway.get('csvRowNumber'),
            'pathwayId': pathway.get('pathway_id'), 'fromStopId': pathway.get('from_stop_id'),
            'toStopId': pathway.get('to_stop_id'), **extra}


def level_sample(model: PathwaysModel, level_id: str, **extra) -> dict:
    level = model.levels_by_id.get(level_id, {})
    return {'filename': 'levels.txt', 'csvRowNumber': level.get('csvRowNumber'), 'levelId': level_id, **extra}


def pathway_ends(model: PathwaysModel, pathway: dict) -> Tuple[dict, dict]:
    return model.stops_by_id[pathway['from_stop_id']], model.stops_by_id[pathway['to_stop_id']]


def mode(pathway: dict) -> Optional[int]:
    return to_int(pathway.get('pathway_mode'))


def positive(value) -> Optional[float]:
    number = to_float(value)
    return number if number is not None and number > 0 else None


# Pathways

def is_short_flight(pathway: dict) -> bool:
    """Stairs whose stair_count says they're a short flight within a level (under MIN_SAME_LEVEL_STAIR_COUNT steps)."""
    stair_count = to_int(pathway.get('stair_count'))
    return mode(pathway) == STAIRS and bool(stair_count) and abs(stair_count) < MIN_SAME_LEVEL_STAIR_COUNT


def same_level_pathways(model: PathwaysModel, modes: tuple, short_flights: bool = False) -> List[dict]:
    """Pathways of these modes whose two stops have the same level_id; short flights of stairs only if asked."""
    samples = []
    for pathway in model.pathways:
        if is_short_flight(pathway) != short_flights:
            continue
        if mode(pathway) in modes:
            a, b = pathway_ends(model, pathway)
            if a.get('level_id') and a.get('level_id') == b.get('level_id'):
                samples.append(pathway_sample(pathway, levelId=a['level_id']))
    return samples


@check('tdei_level_change_same_level', WARNING)
def level_change_same_level(model: PathwaysModel) -> List[dict]:
    """An escalator or elevator (pathway_mode 4, 5) whose two stops have the same level_id. [editor: same_level]"""
    return same_level_pathways(model, (ESCALATOR, ELEVATOR))


@check('tdei_stairs_same_level', WARNING)
def stairs_same_level(model: PathwaysModel) -> List[dict]:
    """
    Stairs (pathway_mode 2) whose two stops have the same level_id, unless stair_count says it's a short
    flight (under MIN_SAME_LEVEL_STAIR_COUNT steps) within the level. [editor: same_level]
    """
    return same_level_pathways(model, (STAIRS,))


@check('tdei_stairs_short_within_level', INFO)
def stairs_short_within_level(model: PathwaysModel) -> List[dict]:
    """
    Stairs whose two stops have the same level_id, with a stair_count under MIN_SAME_LEVEL_STAIR_COUNT: a
    short flight within the level, e.g. into a lobby. Reported so it can be confirmed. [editor: same_level]
    """
    return same_level_pathways(model, (STAIRS,), short_flights=True)


@check('tdei_escalator_two_way', WARNING)
def escalator_two_way(model: PathwaysModel) -> List[dict]:
    """An escalator (pathway_mode 4) with is_bidirectional 1. [editor: escalator_two_way]"""
    return [pathway_sample(p) for p in model.pathways
            if mode(p) == ESCALATOR and p.get('is_bidirectional', '').strip() == '1']


@check('tdei_walkway_changes_level', WARNING)
def walkway_changes_level(model: PathwaysModel) -> List[dict]:
    """
    A walkway, moving sidewalk, fare gate or exit gate (pathway_mode 1, 3, 6, 7) between stops on
    different levels, with no max_slope (a ramp would have one). Levels with the same level_index
    are at the same height, so they don't count as different. [editor: walkway_changes_level]
    """
    samples = []
    for pathway in model.pathways:
        if mode(pathway) not in (WALKWAY, MOVING_SIDEWALK, FARE_GATE, EXIT_GATE) or pathway.get('max_slope', '').strip():
            continue
        a, b = pathway_ends(model, pathway)
        if not a.get('level_id') or not b.get('level_id') or a['level_id'] == b['level_id']:
            continue
        index_a, index_b = model.level_index(a), model.level_index(b)
        if index_a is not None and index_a == index_b:
            continue
        samples.append(pathway_sample(pathway, fromLevelId=a['level_id'], toLevelId=b['level_id']))
    return samples


@check('tdei_stair_count_direction', WARNING)
def stair_count_direction(model: PathwaysModel) -> List[dict]:
    """
    Stairs (pathway_mode 2) whose stair_count sign doesn't match the direction: positive should go
    up (to_stop's level_index higher than from_stop's), negative down. Skipped when either
    level_index is missing or they're equal, or stair_count is 0. [editor: stair_count_direction]
    """
    samples = []
    for pathway in model.pathways:
        stair_count = to_int(pathway.get('stair_count'))
        if mode(pathway) != STAIRS or not stair_count:
            continue
        a, b = pathway_ends(model, pathway)
        index_a, index_b = model.level_index(a), model.level_index(b)
        if index_a is None or index_b is None or index_a == index_b:
            continue
        if (stair_count > 0) != (index_b > index_a):
            samples.append(pathway_sample(pathway, fieldName='stair_count', fieldValue=stair_count))
    return samples


def length_samples(model: PathwaysModel, too_short: bool) -> List[dict]:
    """
    Pathways of mode 1, 3, 6 or 7 whose length is under 0.5x (too_short) or over 2x the straight-line
    distance between its stops, and at least 10 m off. Skipped when either stop has no coordinates, or
    they're less than 1 m apart (likely copied). [editor: length_too_short, length_too_long]
    """
    samples = []
    for pathway in model.pathways:
        length = positive(pathway.get('length'))
        if mode(pathway) not in (WALKWAY, MOVING_SIDEWALK, FARE_GATE, EXIT_GATE) or length is None:
            continue
        ends = pathway_ends(model, pathway)
        distance = distance_m(*ends)
        if distance is None or distance < 1 or abs(length - distance) < 10:
            continue
        # A platform or boarding area is an area placed at one point, so a path into it can be
        # shorter than the line to that point
        if too_short and any(model.location_type(end) in (STOP_OR_PLATFORM, BOARDING_AREA) for end in ends):
            continue
        if (length < 0.5 * distance) if too_short else (length > 2 * distance):
            samples.append(pathway_sample(pathway, fieldName='length', fieldValue=length,
                                          straightLineDistance=round(distance, 1)))
    return samples


@check('tdei_length_too_short', WARNING)
def length_too_short(model: PathwaysModel) -> List[dict]:
    """
    A pathway whose length is under half the straight-line distance between its stops (see
    length_samples), neither of which is a platform or boarding area. A path can't be shorter than
    the line between two points, so the length or a stop is wrong.
    """
    return length_samples(model, too_short=True)


@check('tdei_length_too_long', INFO)
def length_too_long(model: PathwaysModel) -> List[dict]:
    """
    A pathway whose length is over twice the straight-line distance between its stops (see
    length_samples). Usually a winding route, so worth a look rather than wrong.
    """
    return length_samples(model, too_short=False)


@check('tdei_stops_share_location', INFO)
def stops_share_location(model: PathwaysModel) -> List[dict]:
    """
    A walkway, moving sidewalk or gate whose stops are under 1 m apart, but whose length is 10 m or more: one
    stop's coordinates are likely copied from the other's. (The length checks skip stops this close;
    elevators' stops are often stacked, so they're not included.)
    """
    samples = []
    for pathway in model.pathways:
        length = positive(pathway.get('length'))
        if mode(pathway) not in (WALKWAY, MOVING_SIDEWALK, FARE_GATE, EXIT_GATE) or length is None or length < 10:
            continue
        distance = distance_m(*pathway_ends(model, pathway))
        if distance is not None and distance < 1:
            samples.append(pathway_sample(pathway, fieldName='length', fieldValue=length,
                                          straightLineDistance=round(distance, 1)))
    return samples


@check('tdei_traversal_time_mismatch', WARNING)
def traversal_time_mismatch(model: PathwaysModel) -> List[dict]:
    """
    A moving sidewalk or escalator (pathway_mode 3, 4) whose speed (its length, or else the
    straight-line distance between its stops, over traversal_time) is under 0.1 m/s or over 5 m/s.
    Skipped without a length when the stops are less than 1 m apart. [editor: traversal_time_mismatch]
    """
    samples = []
    for pathway in model.pathways:
        seconds = positive(pathway.get('traversal_time'))
        if mode(pathway) not in (MOVING_SIDEWALK, ESCALATOR) or seconds is None:
            continue
        distance = positive(pathway.get('length')) or distance_m(*pathway_ends(model, pathway))
        if distance is None or distance < 1:
            continue
        speed = distance / seconds
        if speed < 0.1 or speed > 5:
            samples.append(pathway_sample(pathway, fieldName='traversal_time', fieldValue=seconds,
                                          speedMetersPerSecond=round(speed, 2)))
    return samples


@check('tdei_duplicate_pathway', WARNING)
def duplicate_pathway(model: PathwaysModel) -> List[dict]:
    """
    Two pathways of the same pathway_mode joining the same two stops the same way (both two-way, or
    both one-way in the same direction). When both have a length, they must be within 10%, so
    side-by-side routes aren't flagged. [editor: duplicate_pathway]
    """
    groups = defaultdict(list)
    for pathway in model.pathways:
        a, b = pathway['from_stop_id'], pathway['to_stop_id']
        if pathway.get('is_bidirectional', '').strip() == '1':
            groups[(mode(pathway), 'two-way', frozenset((a, b)))].append(pathway)
        else:
            groups[(mode(pathway), 'one-way', a, b)].append(pathway)
    samples = []
    for pathways in groups.values():
        flagged = set()
        for i, first in enumerate(pathways):
            for second in pathways[i + 1:]:
                if id(second) in flagged:
                    continue
                l1, l2 = positive(first.get('length')), positive(second.get('length'))
                if l1 is None or l2 is None or abs(l1 - l2) <= 0.1 * max(l1, l2):
                    flagged.add(id(second))
                    samples.append(pathway_sample(second, duplicateOfPathwayId=first.get('pathway_id')))
    return samples


@check('tdei_pathway_ends_far_apart', WARNING)
def pathway_ends_far_apart(model: PathwaysModel) -> List[dict]:
    """
    A pathway whose two stops are farther apart in a straight line than its mode plausibly spans
    (see MAX_PATHWAY_SPAN_METERS), whatever its length says: likely a stop placed in the wrong spot.
    """
    samples = []
    for pathway in model.pathways:
        limit = MAX_PATHWAY_SPAN_METERS.get(mode(pathway))
        distance = distance_m(*pathway_ends(model, pathway))
        if limit is not None and distance is not None and distance > limit:
            samples.append(pathway_sample(pathway, straightLineDistance=round(distance, 1), maxDistance=limit))
    return samples


# Levels

@check('tdei_boarding_area_level', WARNING)
def boarding_area_level(model: PathwaysModel) -> List[dict]:
    """A boarding area (type 4) whose level_id differs from its platform's (its parent_station's). [editor: boarding_area_level]"""
    samples = []
    for stop in model.stops:
        platform = model.stops_by_id.get(stop.get('parent_station'))
        if model.location_type(stop) == BOARDING_AREA and platform and stop.get('level_id') \
                and platform.get('level_id') and stop['level_id'] != platform['level_id']:
            samples.append(stop_sample(stop, levelId=stop['level_id'], platformLevelId=platform['level_id']))
    return samples


@check('tdei_level_unreachable', ERROR)
def level_unreachable(model: PathwaysModel) -> List[dict]:
    """
    A level_id that stops in a station with pathways use, where none of those stops can be reached
    from any entrance. [editor: level_unreachable]
    """
    reached = model.from_entrances()
    samples = []
    for station in sorted(model.stations_with_pathways):
        by_level = defaultdict(list)
        for stop in model.station_stops[station]:
            if stop.get('level_id'):
                by_level[stop['level_id']].append(stop['stop_id'])
        for level_id, stop_ids in by_level.items():
            if not reached.intersection(stop_ids):
                samples.append(level_sample(model, level_id, stationId=station))
    return samples


@check('tdei_empty_level', WARNING)
def empty_level(model: PathwaysModel) -> List[dict]:
    """A level in levels.txt that no stop's level_id names. [editor: empty_level]"""
    used = {stop.get('level_id') for stop in model.stops}
    return [level_sample(model, level['level_id']) for level in model.levels
            if level.get('level_id') and level['level_id'] not in used]


def station_levels(model: PathwaysModel, station: str) -> dict:
    """The levels a station's stops use, with their level_index (None if missing)."""
    return {stop['level_id']: model.level_index(stop)
            for stop in model.station_stops[station] if stop.get('level_id') in model.levels_by_id}


@check('tdei_level_index_repeated', WARNING)
def level_index_repeated(model: PathwaysModel) -> List[dict]:
    """
    A station with two levels (used by its stops) that have the same level_index. GTFS allows it
    (e.g. separate street and median levels at height 0), so it doesn't fail. [editor: station_level_order]
    """
    samples = []
    for station in sorted(model.station_stops):
        by_index = defaultdict(list)
        for level_id, index in station_levels(model, station).items():
            if index is not None:
                by_index[index].append(level_id)
        for index, level_ids in by_index.items():
            if len(level_ids) > 1:
                samples.append(level_sample(model, sorted(level_ids)[1], stationId=station, levelIndex=index,
                                            sameIndexAsLevelId=sorted(level_ids)[0]))
    return samples


@check('tdei_level_index_far_from_street', WARNING)
def level_index_far_from_street(model: PathwaysModel) -> List[dict]:
    """
    A station whose levels' level_index are all more than 20 from 0 (street level), e.g. numbered
    across the whole feed. [editor: station_level_order]
    """
    samples = []
    for station in sorted(model.station_stops):
        indexes = [i for i in station_levels(model, station).values() if i is not None]
        if indexes and all(abs(i) > 20 for i in indexes):
            samples.append(stop_sample(model.stops_by_id[station], levelIndexes=sorted(indexes)))
    return samples


@check('tdei_stop_far_from_level', WARNING)
def stop_far_from_level(model: PathwaysModel) -> List[dict]:
    """
    A stop at least 500 m from the median location of the stops on its level in its station
    (levels with 3 or more located stops). [editor: far_stop]
    """
    samples = []
    for station in sorted(model.station_stops):
        by_level = defaultdict(list)
        for stop in model.station_stops[station]:
            if stop.get('level_id') and to_float(stop.get('stop_lat')) is not None \
                    and to_float(stop.get('stop_lon')) is not None:
                by_level[stop['level_id']].append(stop)
        for level_id, stops in by_level.items():
            if len(stops) < 3:
                continue
            middle = {'stop_lat': statistics.median(to_float(s['stop_lat']) for s in stops),
                      'stop_lon': statistics.median(to_float(s['stop_lon']) for s in stops)}
            for stop in stops:
                distance = distance_m(stop, middle)
                if distance >= 500:
                    samples.append(stop_sample(stop, levelId=level_id, distanceFromLevel=round(distance)))
    return samples


@check('tdei_missing_level_id', WARNING)
def missing_level_id(model: PathwaysModel) -> List[dict]:
    """
    A platform, generic node or boarding area (type 0, 3, 4) in a station that uses levels, with no
    level_id. (MobilityData only requires level_id at elevators.) [editor: missing_level]
    """
    samples = []
    for station, stops in sorted(model.station_stops.items()):
        if not any(stop.get('level_id') for stop in stops):
            continue
        samples += [stop_sample(stop, stationId=station) for stop in stops
                    if model.location_type(stop) in (STOP_OR_PLATFORM, GENERIC_NODE, BOARDING_AREA)
                    and not stop.get('level_id')]
    return samples


# Stations

@check('tdei_station_without_pathways', INFO)
def station_without_pathways(model: PathwaysModel) -> List[dict]:
    """
    A station none of whose stops a pathway touches. The checks that need pathways skip it, since riders
    reach its stops from the street. Reported so missing pathways show.
    """
    return [stop_sample(s) for s in model.stops
            if model.location_type(s) == STATION and s.get('stop_id') not in model.stations_with_pathways]


@check('tdei_station_without_entrance', ERROR)
def station_without_entrance(model: PathwaysModel) -> List[dict]:
    """A station with pathways but no entrance (type 2) among its stops. [editor: no_entrance]"""
    return [stop_sample(model.stops_by_id[station]) for station in sorted(model.stations_with_pathways)
            if not any(model.location_type(s) == ENTRANCE for s in model.station_stops[station])]


@check('tdei_stop_far_from_station', WARNING)
def stop_far_from_station(model: PathwaysModel) -> List[dict]:
    """
    A stop more than MAX_STOP_FROM_STATION_METERS from its station, when both have coordinates: likely
    placed in the wrong spot, alone or with the rest of its level.
    """
    samples = []
    for station, stops in sorted(model.station_stops.items()):
        for stop in stops:
            distance = distance_m(stop, model.stops_by_id[station])
            if distance is not None and distance > MAX_STOP_FROM_STATION_METERS:
                samples.append(stop_sample(stop, stationId=station, distanceFromStation=round(distance)))
    return samples


@check('tdei_stops_share_position', INFO)
def stops_share_position(model: PathwaysModel) -> List[dict]:
    """
    Stops in a station with pathways on the same level (or both with none) at the same coordinates (to
    about 0.1 m), unless a fare gate, exit gate or elevator joins them directly (its sides are often one
    point). Often a placeholder or a duplicate; directional platforms sharing an island may be fine.
    One sample per group, at its first stop.
    """
    joined = {frozenset((p['from_stop_id'], p['to_stop_id'])) for p in model.pathways
              if mode(p) in (FARE_GATE, EXIT_GATE, ELEVATOR)}
    samples = []
    for station in sorted(model.stations_with_pathways):
        groups = defaultdict(list)
        for stop in model.station_stops[station]:
            lat, lon = to_float(stop.get('stop_lat')), to_float(stop.get('stop_lon'))
            if lat is not None and lon is not None:
                groups[(stop.get('level_id') or '', round(lat, 6), round(lon, 6))].append(stop)
        for stops in groups.values():
            ids = [s['stop_id'] for s in stops]
            shared = [s for s in stops if not any(frozenset((s['stop_id'], other)) in joined
                                                  for other in ids if other != s['stop_id'])]
            if len(shared) > 1:
                samples.append(stop_sample(shared[0], stationId=station,
                                           samePositionAs=[s['stop_id'] for s in shared[1:]]))
    return samples


@check('tdei_stop_without_pathway', WARNING)
def stop_without_pathway(model: PathwaysModel) -> List[dict]:
    """
    A stop in a station with pathways that no pathway touches (skipping the station itself, and
    platforms with boarding areas). [editor: isolated]
    """
    samples = []
    for station in sorted(model.stations_with_pathways):
        samples += [stop_sample(stop, stationId=station) for stop in model.station_stops[station]
                    if stop['stop_id'] not in model.touched and not model.has_boarding_areas(stop)]
    return samples


# Routes between entrances and platforms. MobilityData already checks that every platform can be
# reached from an entrance and can reach one, on all pathways [pathway_unreachable_location], so
# the step-free checks skip platforms and entrances with no route at all.

@check('tdei_entrance_reaches_no_platform', WARNING)
def entrance_reaches_no_platform(model: PathwaysModel) -> List[dict]:
    """
    An entrance (type 2), in a station with pathways, cut off from the platforms both ways: no platform
    or boarding area can be reached from it, or reach it. (An exit-only door, which riders only leave
    through, is fine.)
    """
    targets = {s['stop_id'] for s in model.platform_targets}
    from_platforms = model.reachable(targets)
    return [stop_sample(e) for e in model.pathway_entrances
            if e['stop_id'] not in from_platforms and not model.reachable([e['stop_id']]) & targets]


@check('tdei_entrance_exit_only', INFO)
def entrance_exit_only(model: PathwaysModel) -> List[dict]:
    """
    An entrance, in a station with pathways, that riders can only leave through: no platform or boarding
    area can be reached from it, but some reach it. Reported so it can be confirmed.
    """
    targets = {s['stop_id'] for s in model.platform_targets}
    from_platforms = model.reachable(targets)
    return [stop_sample(e) for e in model.pathway_entrances
            if e['stop_id'] in from_platforms and not model.reachable([e['stop_id']]) & targets]


@check('tdei_entrance_reaches_no_platform_step_free', INFO)
def entrance_reaches_no_platform_step_free(model: PathwaysModel) -> List[dict]:
    """An entrance from which platforms can be reached, but none by a step-free route."""
    targets = {s['stop_id'] for s in model.platform_targets}
    return [stop_sample(e) for e in model.pathway_entrances
            if model.reachable([e['stop_id']]) & targets
            and not model.reachable([e['stop_id']], STEP_FREE_MODES) & targets]


@check('tdei_platform_no_step_free_route_in', INFO)
def platform_no_step_free_route_in(model: PathwaysModel) -> List[dict]:
    """A platform or boarding area that entrances reach, but none by a step-free route. [editor: no_step_free]"""
    reached, reached_step_free = model.from_entrances(), model.from_entrances(STEP_FREE_MODES)
    return [stop_sample(s) for s in model.platform_targets
            if s['stop_id'] in reached and s['stop_id'] not in reached_step_free]


@check('tdei_platform_no_step_free_exit', INFO)
def platform_no_step_free_exit(model: PathwaysModel) -> List[dict]:
    """A platform or boarding area that can reach an entrance, but none by a step-free route."""
    exits, exits_step_free = model.to_entrances(), model.to_entrances(STEP_FREE_MODES)
    return [stop_sample(s) for s in model.platform_targets
            if s['stop_id'] in exits and s['stop_id'] not in exits_step_free]


@check('tdei_elevator_only_route', INFO)
def elevator_only_route(model: PathwaysModel) -> List[dict]:
    """A platform or boarding area whose only step-free route from an entrance goes through an elevator (pathway_mode 5). [editor: elevator_only]"""
    step_free = model.from_entrances(STEP_FREE_MODES)
    without_elevators = model.from_entrances(STEP_FREE_MODES - {ELEVATOR})
    return [stop_sample(s) for s in model.platform_targets
            if s['stop_id'] in step_free and s['stop_id'] not in without_elevators]


@check('tdei_no_step_free_transfer', INFO)
def no_step_free_transfer(model: PathwaysModel) -> List[dict]:
    """
    Two platforms in one station with a route between them that doesn't pass through an entrance,
    but no such step-free route, in one direction or both. One sample per direction. (Platforms
    joined only through entrances, such as side platforms with their own entrances, are skipped.)
    """
    entrances = [e['stop_id'] for e in model.entrances]
    samples = []
    for station in sorted(model.stations_with_pathways):
        platforms = [s for s in model.station_stops[station] if model.location_type(s) == STOP_OR_PLATFORM]
        for a in platforms:
            nodes_a = model.platform_nodes(a)
            reached = model.reachable(nodes_a, blocked=entrances)
            reached_step_free = model.reachable(nodes_a, STEP_FREE_MODES, blocked=entrances)
            for b in platforms:
                nodes_b = set(model.platform_nodes(b))
                if b is not a and reached & nodes_b and not reached_step_free & nodes_b:
                    samples.append(stop_sample(a, toStopId=b['stop_id'], stationId=station))
    return samples


# Entrances

@check('tdei_entrance_without_location', WARNING)
def entrance_without_location(model: PathwaysModel) -> List[dict]:
    """An entrance (type 2) with no stop_lat or stop_lon, so outdoor (sidewalk) data can't connect to it."""
    return [stop_sample(e) for e in model.entrances
            if to_float(e.get('stop_lat')) is None or to_float(e.get('stop_lon')) is None]


@check('tdei_entrance_not_street_level', INFO)
def entrance_not_street_level(model: PathwaysModel) -> List[dict]:
    """An entrance whose level's level_index isn't 0 (street level). Skipped when it has no level or level_index."""
    samples = []
    for entrance in model.entrances:
        index = model.level_index(entrance)
        if index is not None and index != 0:
            samples.append(stop_sample(entrance, levelId=entrance['level_id'], levelIndex=index))
    return samples
