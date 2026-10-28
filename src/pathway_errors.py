from typing import Dict, List, Set

from .gtfs_feed import GtfsFeed
from .pathways_config import MOBILITY_DATA_PATHWAY_CODES, PATHWAY_FILES, PATHWAY_LOCATION_TYPES


def pathway_stop_ids(zip_path: str) -> Set[str]:
    """The feed's entrances, generic nodes and boarding areas: stops that are pathways data."""
    feed = GtfsFeed.from_zip(zip_path)
    return {s['stop_id'] for s in feed.stops if (s.get('location_type') or '').strip() in PATHWAY_LOCATION_TYPES}


def is_pathway_sample(sample: dict, pathway_stops: Set[str]) -> bool:
    """Whether one of a MobilityData notice's samples is about pathways data: in a pathways file, or about a pathway stop."""
    files = {sample.get(key) for key in ('filename', 'childFilename', 'parentFilename')}
    return bool(files & set(PATHWAY_FILES)) or sample.get('stopId') in pathway_stops


def lenient_replacements(errors: List[dict], pathway_stops: Set[str]) -> Dict[int, List[dict]]:
    """
    For lenient mode: the notices to report instead of each MobilityData error (by id) that's in pathways data,
    marked pathwayData so they don't fail the upload. A notice with samples both in and outside pathways data is
    split; samples MobilityData didn't list stay errors. An unreadable feed is never pathways data.
    """
    replacements = {}
    for error in errors:
        if error.get('severity') != 'ERROR' or error.get('feedUnreadable'):
            continue
        if error.get('code') in MOBILITY_DATA_PATHWAY_CODES:
            replacements[id(error)] = [{**error, 'pathwayData': True}]
            continue
        samples = error.get('sampleNotices') or []
        local = [s for s in samples if is_pathway_sample(s, pathway_stops)]
        if not local:
            continue
        rest = [s for s in samples if not is_pathway_sample(s, pathway_stops)]
        unsampled = max(error.get('totalNotices', len(samples)) - len(samples), 0)
        new = []
        if rest or unsampled:
            new.append({**error, 'totalNotices': len(rest) + unsampled, 'sampleNotices': rest})
        new.append({**error, 'totalNotices': len(local), 'sampleNotices': local, 'pathwayData': True})
        replacements[id(error)] = new
    return replacements
