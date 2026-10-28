import csv
import io
import zipfile
from typing import Dict, List

# The files TDEI's own checks read (see custom_checks.py)
FEED_FILES = ['stops.txt', 'pathways.txt', 'levels.txt']


class GtfsFeed:
    """
    The pathways-related tables of a GTFS feed, read for TDEI's own checks.
    Each row is a dict of the file's columns (values as text, stripped), plus `csvRowNumber`:
    the row's line in the file, counting the header as 1, as MobilityData's notices do.
    """

    def __init__(self, tables: Dict[str, List[dict]]):
        self.tables = tables
        self.stops = tables.get('stops.txt', [])
        self.pathways = tables.get('pathways.txt', [])
        self.levels = tables.get('levels.txt', [])
        self.stops_by_id = {stop['stop_id']: stop for stop in self.stops if stop.get('stop_id')}
        self.levels_by_id = {level['level_id']: level for level in self.levels if level.get('level_id')}

    @classmethod
    def from_zip(cls, zip_path: str) -> 'GtfsFeed':
        tables = {}
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                filename = info.filename.rsplit('/', 1)[-1]
                if filename in FEED_FILES and filename not in tables:
                    with archive.open(info) as table:
                        tables[filename] = cls.read_csv(table.read())
        return cls(tables)

    @classmethod
    def from_rows(cls, **tables: List[dict]) -> 'GtfsFeed':
        """For tests: e.g. `GtfsFeed.from_rows(stops=[{...}], pathways=[{...}])`; rows are numbered from 2."""
        return cls({
            f'{name}.txt': [{**{k: str(v) for k, v in row.items()}, 'csvRowNumber': i + 2} for i, row in enumerate(rows)]
            for name, rows in tables.items()
        })

    @staticmethod
    def read_csv(content: bytes) -> List[dict]:
        text = content.decode('utf-8-sig', errors='replace')
        rows = []
        for i, row in enumerate(csv.DictReader(io.StringIO(text))):
            cleaned = {(key or '').strip(): (value or '').strip() for key, value in row.items() if key is not None}
            cleaned['csvRowNumber'] = i + 2
            rows.append(cleaned)
        return rows
