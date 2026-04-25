"""One-off: fetch today's fixtures from Sofascore (free widget, no odds).

Writes data/fixtures_<YYYY-MM-DD>.json in the same shape that ``fb snapshot``
expects. Use as a zero-cost fallback when Odds-API quota is exhausted.

Usage::

    $env:SCRAPING_ENABLED = "1"
    python scripts/fetch_fixtures_sofascore.py            # today
    python scripts/fetch_fixtures_sofascore.py 2026-04-25 # explicit date
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date

from football_betting.config import DATA_DIR
from football_betting.scraping.sofascore import SofascoreClient


def main() -> int:
    target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()

    if os.environ.get("SCRAPING_ENABLED") != "1":
        print("ERROR: SCRAPING_ENABLED=1 required.", file=sys.stderr)
        return 2

    client = SofascoreClient()
    fixtures = client.fetch_all_leagues_fixtures_for_date(target)

    if not fixtures:
        print(f"No fixtures found for {target}.", file=sys.stderr)
        return 1

    out_path = DATA_DIR / f"fixtures_{target.isoformat()}.json"
    out_path.write_text(json.dumps(fixtures, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(fixtures)} fixtures -> {out_path}")
    for fx in fixtures:
        print(f"  [{fx['league']}] {fx['kickoff_time']} {fx['home_team']} vs {fx['away_team']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
