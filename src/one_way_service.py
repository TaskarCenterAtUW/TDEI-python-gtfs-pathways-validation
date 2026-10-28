import csv
import io
import zipfile
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set

from .gtfs_feed import GtfsFeed
from .pathways_model import BOARDING_AREA, STOP_OR_PLATFORM, PathwaysModel

UNREACHABLE = 'pathway_unreachable_location'
ARRIVAL_ONLY = 'arrival-only'
DEPARTURE_ONLY = 'departure-only'


def platform_service(zip_path: str, platform_ids: Set[str]) -> Dict[str, str]:
    """
    Which of these platforms trains only arrive at or only depart from, from stop_times.txt: arrival-only
    if every trip that stops there ends there, or no stop time there allows pickup (pickup_type 1);
    departure-only if every trip starts there, or none allows drop-off (drop_off_type 1).
    """
    first_last: Dict[str, list] = {}  # trip_id -> [first sequence, first stop, last sequence, last stop]
    trips_at: Dict[str, Set[str]] = defaultdict(set)
    types_at: Dict[str, Counter] = defaultdict(Counter)
    with zipfile.ZipFile(zip_path) as archive:
        name = next((n for n in archive.namelist() if n.rsplit('/', 1)[-1] == 'stop_times.txt'), None)
        if name is None:
            return {}
        with archive.open(name) as table:
            for row in csv.DictReader(io.TextIOWrapper(table, encoding='utf-8-sig')):
                trip, stop = row.get('trip_id'), (row.get('stop_id') or '').strip()
                try:
                    sequence = int(row.get('stop_sequence') or '')
                except ValueError:
                    continue
                ends = first_last.get(trip)
                if ends is None:
                    first_last[trip] = [sequence, stop, sequence, stop]
                else:
                    if sequence < ends[0]:
                        ends[0], ends[1] = sequence, stop
                    if sequence > ends[2]:
                        ends[2], ends[3] = sequence, stop
                if stop in platform_ids:
                    trips_at[stop].add(trip)
                    types_at[stop][((row.get('pickup_type') or '0').strip(), (row.get('drop_off_type') or '0').strip())] += 1

    service = {}
    for platform, trips in trips_at.items():
        types = types_at[platform]
        if all(first_last[t][3] == platform for t in trips) or all(pickup == '1' for pickup, _ in types):
            service[platform] = ARRIVAL_ONLY
        elif all(first_last[t][1] == platform for t in trips) or all(drop_off == '1' for _, drop_off in types):
            service[platform] = DEPARTURE_ONLY
    return service


def explain_one_way_locations(zip_path: str, notices: List[dict]) -> Dict[int, List[dict]]:
    """
    Re-judges MobilityData's pathway_unreachable_location notices: a location that's one-way by design
    isn't an error. That's one reached only one way (from an entrance, or back to one) that matches its
    platform's service: an arrival-only platform's areas only need a way out, a departure-only one's
    only a way in. A generic node counts if it's on a route from such a platform (when only a way in
    from an entrance is missing), or to one (when only a way back is missing).

    Returns, for each notice (by id) with any such locations, the notices to report instead: one with
    the locations that are still errors, if any (including any MobilityData didn't sample), and one with
    the one-way locations, marked oneWayByService so they don't fail the upload.
    """
    notices = [n for n in notices if n.get('code') == UNREACHABLE]
    if not notices:
        return {}
    model = PathwaysModel(GtfsFeed.from_zip(zip_path))
    platforms = {s['stop_id'] for s in model.stops if model.location_type(s) == STOP_OR_PLATFORM}
    service = platform_service(zip_path, platforms)
    if not service:
        return {}
    arrival = [n for p, kind in service.items() if kind == ARRIVAL_ONLY for n in model.platform_nodes(model.stops_by_id[p])]
    departure = [n for p, kind in service.items() if kind == DEPARTURE_ONLY for n in model.platform_nodes(model.stops_by_id[p])]
    # On routes from arrival-only platforms, or to departure-only ones, inside the station (a route
    # through an entrance leaves it)
    entrances = [e['stop_id'] for e in model.entrances]
    after_arrival = model.reachable(arrival, blocked=entrances)
    before_departure = model.reachable(departure, reverse=True, blocked=entrances)

    def one_way_service(sample: dict) -> Optional[str]:
        stop = model.stops_by_id.get(sample.get('stopId'))
        if stop is None:
            return None
        way_in, way_out = bool(sample.get('hasEntrance')), bool(sample.get('hasExit'))
        kind = model.location_type(stop)
        platform = stop if kind == STOP_OR_PLATFORM else \
            model.stops_by_id.get(stop.get('parent_station')) if kind == BOARDING_AREA else None
        if platform is not None:
            if service.get(platform['stop_id']) == ARRIVAL_ONLY and way_out and not way_in:
                return ARRIVAL_ONLY
            if service.get(platform['stop_id']) == DEPARTURE_ONLY and way_in and not way_out:
                return DEPARTURE_ONLY
            return None
        if way_out and not way_in and stop['stop_id'] in after_arrival:
            return ARRIVAL_ONLY
        if way_in and not way_out and stop['stop_id'] in before_departure:
            return DEPARTURE_ONLY
        return None

    replacements = {}
    for notice in notices:
        samples = notice.get('sampleNotices') or []
        explained = [(sample, one_way_service(sample)) for sample in samples]
        one_way = [{**sample, 'oneWayService': kind} for sample, kind in explained if kind]
        if not one_way:
            continue
        still = [sample for sample, kind in explained if not kind]
        total = notice.get('totalNotices', len(samples))
        unsampled = max(total - len(samples), 0)
        new = []
        if still or unsampled:
            new.append({**notice, 'totalNotices': len(still) + unsampled, 'sampleNotices': still})
        new.append({**notice, 'totalNotices': len(one_way), 'sampleNotices': one_way, 'oneWayByService': True})
        replacements[id(notice)] = new
    return replacements
