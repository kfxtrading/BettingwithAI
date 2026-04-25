"""Manual injection of 2026-04-24 results into live_scores.jsonl.

Football-Data.co.uk CSVs hadn't published 2026-04-24 results yet, so we
record them as authoritative ``completed`` rows in the live cache. The
nightly football-data sync will overwrite these on conflict (CSV wins).
"""

from __future__ import annotations

from datetime import UTC, datetime

from football_betting.evaluation.live_results import (
    LiveScoreRow,
    _load_rows,
    _write_rows,
)
from football_betting.evaluation.pipeline import regrade_all

MATCH_DATE = "2026-04-24"
FETCHED_AT = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
SOURCE = "manual_football_data"

# (league_code, home, away, fthg, ftag, kickoff_utc)
RESULTS = [
    ("E0", "Sunderland", "Nott'm Forest", 0, 5, "2026-04-24T19:00:00Z"),
    ("E1", "Leicester City", "Millwall", 1, 1, "2026-04-24T19:00:00Z"),
    ("D1", "RB Leipzig", "Union Berlin", 3, 1, "2026-04-24T18:30:00Z"),
    ("I1", "Napoli", "Cremonese", 4, 0, "2026-04-24T18:45:00Z"),
    ("SP1", "Betis", "Real Madrid", 1, 1, "2026-04-24T19:00:00Z"),
]


def _ftr(fthg: int, ftag: int) -> str:
    if fthg > ftag:
        return "H"
    if fthg < ftag:
        return "A"
    return "D"


def main() -> None:
    rows = _load_rows()
    by_key = {r.key(): r for r in rows}
    added = 0
    updated = 0
    for code, home, away, fthg, ftag, ko in RESULTS:
        new = LiveScoreRow(
            league_code=code,
            date=MATCH_DATE,
            home_norm=home.lower().strip(),
            away_norm=away.lower().strip(),
            ftr=_ftr(fthg, ftag),
            fthg=fthg,
            ftag=ftag,
            source=SOURCE,
            fetched_at=FETCHED_AT,
            status="completed",
            kickoff_utc=ko,
        )
        if new.key() in by_key:
            by_key[new.key()] = new
            updated += 1
        else:
            by_key[new.key()] = new
            added += 1
    _write_rows(by_key.values())
    print(f"live_scores.jsonl: added={added}, updated={updated}, total={len(by_key)}")

    graded = regrade_all()
    settled_today = [g for g in graded if g.date == MATCH_DATE and g.status != "pending"]
    pending_today = [g for g in graded if g.date == MATCH_DATE and g.status == "pending"]
    print(
        f"regrade_all: settled_on_{MATCH_DATE}={len(settled_today)} "
        f"still_pending_on_{MATCH_DATE}={len(pending_today)}"
    )
    for g in settled_today:
        print(
            f"  [{g.status:>4}] {g.league} {g.home_team} vs {g.away_team} "
            f"({g.ft_score}) — {g.bet_label} @ {g.odds} → pnl={g.pnl}"
        )
    if pending_today:
        print("Still pending (likely team-name mismatch):")
        for g in pending_today:
            print(f"  {g.league} {g.home_team} vs {g.away_team}")


if __name__ == "__main__":
    main()
