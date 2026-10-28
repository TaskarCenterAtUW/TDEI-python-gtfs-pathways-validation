import math
from collections import defaultdict, deque
from typing import Dict, FrozenSet, Iterable, List, Optional, Set

from .gtfs_feed import GtfsFeed

# location_type values
STOP_OR_PLATFORM = 0
STATION = 1
ENTRANCE = 2
GENERIC_NODE = 3
BOARDING_AREA = 4

# pathway_mode values
WALKWAY = 1
STAIRS = 2
MOVING_SIDEWALK = 3
ESCALATOR = 4
ELEVATOR = 5
FARE_GATE = 6
EXIT_GATE = 7

ALL_MODES: FrozenSet[int] = frozenset(range(1, 8))
# A step-free route uses no stairs, moving sidewalks or escalators
STEP_FREE_MODES: FrozenSet[int] = frozenset({WALKWAY, ELEVATOR, FARE_GATE, EXIT_GATE})


def to_int(value) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def to_float(value) -> Optional[float]:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def distance_m(a: dict, b: dict) -> Optional[float]:
    """Straight-line distance between two stops, in metres, or None if either has no coordinates."""
    lat1, lon1, lat2, lon2 = (to_float(a.get('stop_lat')), to_float(a.get('stop_lon')),
                              to_float(b.get('stop_lat')), to_float(b.get('stop_lon')))
    if None in (lat1, lon1, lat2, lon2):
        return None
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi, d_lambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


class PathwaysModel:
    """
    A feed's stations, levels and pathway graph, as TDEI's checks see them:
    - A stop's type is its location_type (empty means 0).
    - A station's stops are those whose parent_station is the station, or is a platform in it
      (for boarding areas). Stops with no station, or a broken parent_station, belong to none.
    - Pathways go from_stop_id -> to_stop_id, and back too unless is_bidirectional is 0.
      Pathways whose ends aren't in stops.txt are left out (MobilityData reports them).
    - A platform with boarding areas is reached through its boarding areas.
    """

    def __init__(self, feed: GtfsFeed):
        self.feed = feed
        self.stops = feed.stops
        self.stops_by_id = feed.stops_by_id
        self.levels = feed.levels
        self.levels_by_id = feed.levels_by_id
        self.pathways = [p for p in feed.pathways
                         if p.get('from_stop_id') in self.stops_by_id and p.get('to_stop_id') in self.stops_by_id]

        self.touched: Set[str] = set()
        for pathway in self.pathways:
            self.touched.update((pathway['from_stop_id'], pathway['to_stop_id']))

        self.boarding_areas_of: Dict[str, List[str]] = defaultdict(list)
        for stop in self.stops:
            if self.location_type(stop) == BOARDING_AREA and stop.get('parent_station') in self.stops_by_id:
                self.boarding_areas_of[stop['parent_station']].append(stop['stop_id'])

        self.station_of: Dict[str, str] = {}
        self.station_stops: Dict[str, List[dict]] = defaultdict(list)
        for stop in self.stops:
            station = self._find_station(stop)
            if station and stop.get('stop_id'):
                self.station_of[stop['stop_id']] = station
                if stop['stop_id'] != station:
                    self.station_stops[station].append(stop)

        self.stations_with_pathways: Set[str] = {self.station_of[s] for s in self.touched if s in self.station_of}
        self.entrances: List[dict] = [s for s in self.stops if self.location_type(s) == ENTRANCE]
        self._adjacency: Dict[tuple, Dict[str, Set[str]]] = {}
        self._entrance_routes: Dict[tuple, Set[str]] = {}

    @staticmethod
    def location_type(stop: dict) -> Optional[int]:
        value = (stop.get('location_type') or '').strip()
        return STOP_OR_PLATFORM if value == '' else to_int(value)

    def _find_station(self, stop: dict) -> Optional[str]:
        for _ in range(3):
            if self.location_type(stop) == STATION:
                return stop.get('stop_id')
            stop = self.stops_by_id.get(stop.get('parent_station'))
            if stop is None:
                return None
        return None

    def level_index(self, stop: dict) -> Optional[float]:
        level = self.levels_by_id.get(stop.get('level_id'))
        return to_float(level.get('level_index')) if level else None

    def has_boarding_areas(self, stop: dict) -> bool:
        return bool(self.boarding_areas_of.get(stop.get('stop_id')))

    def in_station_with_pathways(self, stop: dict) -> bool:
        return self.station_of.get(stop.get('stop_id')) in self.stations_with_pathways

    @property
    def pathway_entrances(self) -> List[dict]:
        """Entrances in stations with pathways."""
        return [s for s in self.entrances if self.in_station_with_pathways(s)]

    @property
    def platform_targets(self) -> List[dict]:
        """Where riders board, in stations with pathways: platforms without boarding areas, and boarding areas."""
        return [s for s in self.stops if self.in_station_with_pathways(s) and (
            (self.location_type(s) == STOP_OR_PLATFORM and not self.has_boarding_areas(s))
            or self.location_type(s) == BOARDING_AREA)]

    def platform_nodes(self, platform: dict) -> List[str]:
        """The stops a route to this platform ends at: its boarding areas, or the platform itself."""
        return self.boarding_areas_of.get(platform['stop_id']) or [platform['stop_id']]

    def adjacency(self, modes: FrozenSet[int], reverse: bool = False) -> Dict[str, Set[str]]:
        key = (modes, reverse)
        if key not in self._adjacency:
            graph: Dict[str, Set[str]] = defaultdict(set)
            for pathway in self.pathways:
                if to_int(pathway.get('pathway_mode')) not in modes:
                    continue
                a, b = pathway['from_stop_id'], pathway['to_stop_id']
                if reverse:
                    a, b = b, a
                graph[a].add(b)
                if pathway.get('is_bidirectional', '').strip() == '1':
                    graph[b].add(a)
            self._adjacency[key] = graph
        return self._adjacency[key]

    def reachable(self, sources: Iterable[str], modes: FrozenSet[int] = ALL_MODES, reverse: bool = False,
                  blocked: Iterable[str] = ()) -> Set[str]:
        """
        The stops reachable from the sources (sources included), following pathway direction, or
        the stops that can reach them with `reverse`. Routes can't pass through `blocked` stops.
        """
        graph = self.adjacency(modes, reverse)
        blocked = set(blocked)
        seen = set(sources)
        queue = deque(seen)
        while queue:
            for nxt in graph.get(queue.popleft(), ()):
                if nxt not in seen and nxt not in blocked:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    def from_entrances(self, modes: FrozenSet[int] = ALL_MODES) -> Set[str]:
        """The stops some entrance reaches using only these pathway modes."""
        return self._routes(modes, reverse=False)

    def to_entrances(self, modes: FrozenSet[int] = ALL_MODES) -> Set[str]:
        """The stops that can reach some entrance using only these pathway modes."""
        return self._routes(modes, reverse=True)

    def _routes(self, modes: FrozenSet[int], reverse: bool) -> Set[str]:
        key = (frozenset(modes), reverse)
        if key not in self._entrance_routes:
            self._entrance_routes[key] = self.reachable([e['stop_id'] for e in self.entrances], key[0], reverse)
        return self._entrance_routes[key]
