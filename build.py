"""Build holidays.json from data.gov.sg (authoritative MOM data).

Source of truth is the Ministry of Manpower "Singapore Public Holidays
(consolidated)" dataset on data.gov.sg. We read it via the CKAN
datastore_search API, emit every published year as
{"YYYY": ["YYYY-MM-DD", ...]}, and cross-check each year against the
`holidays` Python library — reporting (never silently applying) any
discrepancy so a human can review it in the PR.

    python build.py            # write holidays.json, print any discrepancies
    python build.py --check    # exit non-zero if holidays.json is stale
"""

import argparse
import json
import sys
from pathlib import Path

import holidays
import requests

# The consolidated dataset (all years MOM has gazetted, currently 2020-2027).
# New years appear here automatically, so one resource covers everything.
RESOURCE_ID = "d_8ef23381f9417e4d4254ee8b4dcdb176"
SEARCH_URL = "https://data.gov.sg/api/action/datastore_search"

OUTPUT = Path(__file__).resolve().parent / "holidays.json"


def fetch_gov_records() -> list[dict]:
    """Return every record from the consolidated holidays dataset.

    The dataset is ~100 rows (a decade of ~11 holidays/year), so a single
    request with a generous limit fetches everything — no paging needed.
    """
    resp = requests.get(
        SEARCH_URL,
        params={"resource_id": RESOURCE_ID, "limit": 10000},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"datastore_search failed: {payload}")
    return payload["result"].get("records", [])


def group_by_year(records: list[dict]) -> dict[str, list[str]]:
    """Group the `date` column (YYYY-MM-DD) into {year: sorted unique dates}."""
    result: dict[str, list[str]] = {}
    for row in records:
        date = str(row.get("date", "")).strip()
        if not date:
            continue
        result.setdefault(date[:4], []).append(date)
    return {year: sorted(set(dates)) for year, dates in sorted(result.items())}


def cross_check(dates_by_year: dict[str, list[str]]) -> list[str]:
    """Compare each gov year against the `holidays` lib; return discrepancy lines.

    Gov is authoritative — this only flags for human review, never mutates output.
    """
    lines: list[str] = []
    for year, gov_dates in dates_by_year.items():
        lib_dates = {d.isoformat() for d in holidays.Singapore(years=int(year))}
        gov_set = set(gov_dates)
        only_gov = sorted(gov_set - lib_dates)
        only_lib = sorted(lib_dates - gov_set)
        if only_gov or only_lib:
            lines.append(f"{year}: gov-only={only_gov} lib-only={only_lib}")
    return lines


def build() -> tuple[str, dict[str, list[str]], list[str]]:
    dates_by_year = group_by_year(fetch_gov_records())
    if not dates_by_year:
        raise RuntimeError("no holidays parsed from data.gov.sg")
    text = json.dumps(dates_by_year, indent=2) + "\n"
    return text, dates_by_year, cross_check(dates_by_year)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if holidays.json differs from the freshly built output",
    )
    args = ap.parse_args()

    text, dates_by_year, discrepancies = build()

    if args.check:
        current = OUTPUT.read_text() if OUTPUT.exists() else ""
        if current != text:
            print("holidays.json is stale; run `python build.py`", file=sys.stderr)
            sys.exit(1)
        print("holidays.json is up to date")
    else:
        OUTPUT.write_text(text)
        years = list(dates_by_year)
        print(f"Wrote {OUTPUT.name} covering {years[0]}-{years[-1]} ({len(years)} years)")

    if discrepancies:
        print(
            "\n⚠️  data.gov.sg vs `holidays` library discrepancies (gov is authoritative; review):",
            file=sys.stderr,
        )
        for line in discrepancies:
            print(f"  {line}", file=sys.stderr)


if __name__ == "__main__":
    main()
