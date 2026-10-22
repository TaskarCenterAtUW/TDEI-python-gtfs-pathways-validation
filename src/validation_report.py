import datetime
import html
import io
import json
import os
import zipfile
from typing import List, Optional

from .pathways_config import CHANGE_ERROR_TO_WARNING

# What a notice means for the upload
FAILS_UPLOAD = 'fails_upload'
DOWNGRADED = 'downgraded_to_warning'
WARNING = 'warning'
INFO = 'info'

OUTCOME_LABELS = {
    FAILS_UPLOAD: 'Fails upload',
    DOWNGRADED: 'Warning (downgraded error)',
    WARNING: 'Warning',
    INFO: 'Info',
}
OUTCOME_ORDER = [FAILS_UPLOAD, DOWNGRADED, WARNING, INFO]


def notice_outcome(notice: dict) -> str:
    """
    What a notice means for the upload, following the same rules as
    GTFSPathwaysValidation.is_gtfs_pathways_valid: an ERROR fails the upload
    unless pathways_config.py downgrades it to a warning.
    """
    severity = notice.get('severity')
    if severity == 'ERROR':
        return DOWNGRADED if notice.get('code') in CHANGE_ERROR_TO_WARNING else FAILS_UPLOAD
    if severity == 'WARNING':
        return WARNING
    return INFO


class ValidationReport:
    """
    The report of one validation: every notice from MobilityData's validator and from
    TDEI's own checks, each with its outcome for the upload, as `report.json` and
    `report.html`, zipped with MobilityData's own reports.
    """

    def __init__(self, feed_name: str, is_valid: bool, mobility_data_notices: List[dict],
                 custom_notices: List[dict], validator_version: Optional[str] = None,
                 mobility_data_dir: Optional[str] = None):
        self.feed_name = feed_name
        self.is_valid = is_valid
        self.validator_version = validator_version
        self.mobility_data_dir = mobility_data_dir
        self.validated_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')

        notices = [{**notice, 'source': notice.get('source', 'mobilitydata')} for notice in mobility_data_notices]
        notices += [{**notice, 'source': 'tdei'} for notice in custom_notices]
        for notice in notices:
            notice['outcome'] = notice_outcome(notice)
        notices.sort(key=lambda n: (OUTCOME_ORDER.index(n['outcome']), n.get('code', '')))
        self.notices = notices

    @property
    def summary(self) -> dict:
        counts = {outcome: 0 for outcome in OUTCOME_ORDER}
        for notice in self.notices:
            counts[notice['outcome']] += 1
        return {
            'valid': self.is_valid,
            'feed': self.feed_name,
            'validatedAt': self.validated_at,
            'gtfsValidatorVersion': self.validator_version,
            'codesByOutcome': counts,
        }

    def to_json(self) -> dict:
        return {'summary': self.summary, 'notices': self.notices}

    def to_html(self) -> str:
        summary = self.summary
        status = 'Passed' if self.is_valid else 'Failed'
        counts = ''.join(
            f'<li>{OUTCOME_LABELS[outcome]}: {count}</li>' for outcome, count in summary['codesByOutcome'].items())
        sections = ''.join(self._notice_html(notice) for notice in self.notices) \
            or '<p>No problems found.</p>'
        mobility_data_link = '<p>MobilityData\'s full report is in <code>mobilitydata/report.html</code>.</p>' \
            if self.mobility_data_dir else ''
        return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>GTFS Pathways validation: {html.escape(self.feed_name)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #222; }}
  .status {{ font-weight: bold; }}
  .status.failed, .fails_upload h2 {{ color: #b00020; }}
  .status.passed {{ color: #1b7e3c; }}
  section {{ margin-top: 1.5rem; }}
  h2 {{ font-size: 1.1rem; margin-bottom: 0.25rem; }}
  .meta {{ color: #666; margin: 0 0 0.5rem; }}
  table {{ border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ border: 1px solid #ccc; padding: 0.25rem 0.5rem; text-align: left; }}
  th {{ background: #f4f4f4; }}
</style>
</head>
<body>
<h1>GTFS Pathways validation</h1>
<p>{html.escape(self.feed_name)}: <span class="status {status.lower()}">{status}</span></p>
<p class="meta">Validated {html.escape(self.validated_at)} with MobilityData's GTFS validator
{html.escape(self.validator_version or '')} and TDEI's pathways checks.</p>
<ul>{counts}</ul>
{mobility_data_link}
{sections}
</body>
</html>
'''

    @staticmethod
    def _notice_html(notice: dict) -> str:
        samples = notice.get('sampleNotices') or []
        columns = []
        for sample in samples:
            for key in sample:
                if key not in columns:
                    columns.append(key)
        header = ''.join(f'<th>{html.escape(column)}</th>' for column in columns)
        rows = ''.join(
            '<tr>' + ''.join(f'<td>{html.escape(str(sample.get(column, "")))}</td>' for column in columns) + '</tr>'
            for sample in samples)
        table = f'<table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>' if samples else ''
        total = notice.get('totalNotices', len(samples))
        shown = f', showing {len(samples)}' if len(samples) < total else ''
        source = 'TDEI' if notice['source'] == 'tdei' else 'MobilityData'
        return f'''<section class="{notice['outcome']}">
<h2>{html.escape(notice.get('code', ''))}</h2>
<p class="meta">{OUTCOME_LABELS[notice['outcome']]} &middot; {source} &middot; {total} found{shown}</p>
{table}
</section>
'''

    def to_zip(self) -> bytes:
        """`report.json` and `report.html`, plus MobilityData's own reports under `mobilitydata/`."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('report.json', json.dumps(self.to_json(), indent=2, default=str))
            archive.writestr('report.html', self.to_html())
            if self.mobility_data_dir:
                for name in ['report.json', 'report.html', 'system_errors.json']:
                    path = os.path.join(self.mobility_data_dir, name)
                    if os.path.isfile(path):
                        archive.write(path, f'mobilitydata/{name}')
        return buffer.getvalue()
