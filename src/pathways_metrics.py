from typing import Iterable

from .gtfs_feed import GtfsFeed
from .pathways_model import (BOARDING_AREA, ENTRANCE, GENERIC_NODE, STATION, STEP_FREE_MODES, STOP_OR_PLATFORM,
                             PathwaysModel, to_float)

# Labels for report.html, in order
METRIC_LABELS = {
    'completeness': {
        'stationsWithPathways': 'Stations with pathways',
        'stopsWithLevelId': 'Platforms, entrances, nodes and boarding areas with a level_id',
        'stopsWithWheelchairBoarding': 'Platforms and entrances with wheelchair_boarding filled in',
        'pathwaysWithLength': 'Pathways with a length',
        'pathwaysWithTraversalTime': 'Pathways with a traversal_time',
    },
    'connectivity': {
        'platformsStepFree': 'Platforms and boarding areas with a step-free way in and out',
        'entrancesReachingPlatformStepFree': 'Entrances that reach a platform step-free',
        'stationsStepFree': 'Stations where every platform is step-free',
    },
}


def share(items: Iterable[bool]) -> dict:
    """How many of some things meet a condition: `{'count', 'total', 'percent'}` (percent is None when there are none)."""
    items = list(items)
    count, total = sum(items), len(items)
    return {'count': count, 'total': total, 'percent': round(100 * count / total, 1) if total else None}


def measure_feed(feed: GtfsFeed) -> dict:
    return measure(PathwaysModel(feed))


def measure(model: PathwaysModel) -> dict:
    """
    Dataset-level metrics. Except for stationsWithPathways, they count within stations that have
    pathways, so stops without pathways (e.g. bus stops) don't count against a feed. Connectivity
    uses the same routes as the step-free checks (see PathwaysModel).
    """
    station_stops = [stop for station in model.stations_with_pathways for stop in model.station_stops[station]]
    stations = [s for s in model.stops if model.location_type(s) == STATION]

    step_free_in = model.from_entrances(STEP_FREE_MODES)
    step_free_out = model.to_entrances(STEP_FREE_MODES)
    targets = {s['stop_id'] for s in model.platform_targets}
    step_free_targets = {t for t in targets if t in step_free_in and t in step_free_out}
    stations_with_targets = {model.station_of[t] for t in targets}

    return {
        'completeness': {
            'stationsWithPathways': share(s['stop_id'] in model.stations_with_pathways for s in stations),
            'stopsWithLevelId': share(
                bool(s.get('level_id')) for s in station_stops
                if model.location_type(s) in (STOP_OR_PLATFORM, ENTRANCE, GENERIC_NODE, BOARDING_AREA)),
            'stopsWithWheelchairBoarding': share(
                (s.get('wheelchair_boarding') or '').strip() in ('1', '2') for s in station_stops
                if model.location_type(s) in (STOP_OR_PLATFORM, ENTRANCE)),
            'pathwaysWithLength': share(to_float(p.get('length')) is not None for p in model.pathways),
            'pathwaysWithTraversalTime': share(to_float(p.get('traversal_time')) is not None for p in model.pathways),
        },
        'connectivity': {
            'platformsStepFree': share(t in step_free_targets for t in targets),
            'entrancesReachingPlatformStepFree': share(
                bool(model.reachable([e['stop_id']], STEP_FREE_MODES) & targets) for e in model.pathway_entrances),
            'stationsStepFree': share(
                all(t in step_free_targets for t in targets if model.station_of[t] == station)
                for station in sorted(stations_with_targets)),
        },
    }
