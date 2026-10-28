"""
Validates GTFS pathways feeds on disk as the service does (MobilityData's validator, then TDEI's checks),
without Azure, e.g.:

    python scripts/validate_feed.py feed.zip other.zip --out reports [--strict]

Writes each feed's report.json and report.html, with MobilityData's own reports, to <out>/<feed>/, and
prints whether each passes and what failed it. Exits 1 if any feed fails.
"""
import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pathways_feed_validation import PathwaysFeedValidation  # noqa: E402
from src.validation_report import FAILS_UPLOAD  # noqa: E402


def validate(path: str, out: str, strict: bool) -> bool:
    name = os.path.splitext(os.path.basename(path))[0]
    folder = os.path.join(out, name)
    os.makedirs(folder, exist_ok=True)
    is_valid, _, report = PathwaysFeedValidation.check_feed(path, os.path.basename(path),
                                                            os.path.join(folder, 'mobilitydata'), strict=strict)
    with open(os.path.join(folder, 'report.json'), 'w', encoding='utf-8') as f:
        json.dump(report.to_json(), f, indent=2)
    with open(os.path.join(folder, 'report.html'), 'w', encoding='utf-8') as f:
        f.write(report.to_html())

    counts = ', '.join(f'{outcome} {count}' for outcome, count in report.summary['codesByOutcome'].items())
    print(f"{'PASS' if is_valid else 'FAIL'}  {name}  ({counts})  {folder}/report.html")
    for notice in report.notices:
        if notice['outcome'] == FAILS_UPLOAD:
            print(f"      {notice['source']:12} {notice['code']}: {notice.get('totalNotices', 1)}")
    return is_valid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('feeds', nargs='+', help='GTFS zip files')
    parser.add_argument('--out', default='reports', help='where to write the reports (default: reports)')
    parser.add_argument('--strict', action='store_true',
                        help='fail on errors in pathways data too (by default they\'re reported as warnings)')
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)  # the reports say it all
    results = [validate(path, args.out, args.strict) for path in args.feeds]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
