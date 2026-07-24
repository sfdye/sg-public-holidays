# Singapore Public Holidays 🇸🇬📅

Singapore's public holidays as a single machine-readable JSON file, sourced from
**[data.gov.sg](https://data.gov.sg/collections/691/view)** — the Ministry of
Manpower's authoritative dataset — and refreshed automatically.

## Get the data

Stable URL (always the latest published years):

```
https://github.com/sfdye/sg-public-holidays/releases/download/data/holidays.json
```

Or read [`holidays.json`](./holidays.json) directly in this repo.

## Shape

```json
{
  "2025": ["2025-01-01", "2025-01-29", "..."],
  "2026": ["2026-01-01", "..."]
}
```

Each key is a year; each value is that year's public-holiday dates
(`YYYY-MM-DD`), sorted. Currently covers 2020 onward — new years are added
automatically once MOM gazettes them (usually ~1 year ahead).

## How it stays current

- **Source of truth:** the MOM "Singapore Public Holidays (consolidated)" dataset
  on data.gov.sg. `build.py` reads it via the CKAN `datastore_search` API and
  emits the dates verbatim — **gov data is authoritative**.
- **Cross-check:** every year is compared against the
  [`holidays`](https://pypi.org/project/holidays/) Python library. The library
  only *estimates* movable holidays (Hari Raya, Deepavali, Vesak…), so
  discrepancies are expected; they're **reported for review, never applied** —
  data.gov.sg always wins.
- **Automation:** a monthly GitHub Action rebuilds the file and, if it changed,
  opens a PR (with any discrepancies in the description). Merging it refreshes the
  rolling `data` release asset above.

## Develop

```bash
uv sync
uv run python build.py          # rebuild holidays.json, print discrepancies
uv run python build.py --check  # assert holidays.json is up to date (CI)
uv run ruff check --fix . && uv run ruff format .
```

## License

The holiday dates are public factual data from data.gov.sg (© Government of
Singapore, [Singapore Open Data Licence](https://data.gov.sg/open-data-licence)).
The code in this repo is released under the Unlicense (public domain).
