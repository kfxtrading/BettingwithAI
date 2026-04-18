"""Persist per-fixture odds snapshots to disk so the MarketMovementTracker
can reconstruct drift / steam-move features across prediction runs.

One JSONL file per league at `data/snapshots/odds_<LEAGUE>.jsonl`:

    {"date": "2026-04-18", "home": "Arsenal", "away": "Man City",
     "timestamp": "2026-04-18T09:30:00", "home_odds": 2.35,
     "draw_odds": 3.40, "away_odds": 2.95, "bookmaker": "avg"}

Every `fb predict` / `fb snapshot` / API prediction call appends a fresh
row; successive runs over time build a time series per fixture that the
tracker replays into `mm_*` features.
"""
from __future__ import annotations

import json
from datetime import date as _date, datetime
from pathlib import Path
from typing import Iterable

from football_betting.config import SNAPSHOT_DIR
from football_betting.data.models import MatchOdds
from football_betting.features.market_movement import (
    MarketMovementTracker,
    OddsSnapshot,
)


def _snapshot_path(league_key: str) -> Path:
    return SNAPSHOT_DIR / f"odds_{league_key.upper()}.jsonl"


def append_snapshot(
    league_key: str,
    home_team: str,
    away_team: str,
    match_date: str,
    odds: MatchOdds,
    *,
    timestamp: datetime | None = None,
) -> None:
    """Append one odds snapshot row for a fixture."""
    ts = (timestamp or datetime.utcnow()).isoformat(timespec="seconds")
    record = {
        "league": league_key.upper(),
        "date": match_date,
        "home": home_team,
        "away": away_team,
        "timestamp": ts,
        "home_odds": float(odds.home),
        "draw_odds": float(odds.draw),
        "away_odds": float(odds.away),
        "bookmaker": odds.bookmaker,
    }
    path = _snapshot_path(league_key)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def _iter_records(league_key: str) -> Iterable[dict]:
    path = _snapshot_path(league_key)
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def load_into_tracker(
    league_key: str,
    tracker: MarketMovementTracker,
    *,
    only_future: bool = False,
) -> int:
    """Replay persisted snapshots into `tracker`. Returns rows loaded.

    With `only_future=True`, snapshots whose match-date is already in
    the past (relative to today) are skipped — useful for prediction
    paths where we only care about fixtures still to come.
    """
    today = _date.today()
    loaded = 0
    for rec in _iter_records(league_key):
        try:
            match_date_iso = rec["date"]
            if only_future:
                if _date.fromisoformat(match_date_iso) < today:
                    continue
            snap = OddsSnapshot(
                timestamp=datetime.fromisoformat(rec["timestamp"]),
                home=float(rec["home_odds"]),
                draw=float(rec["draw_odds"]),
                away=float(rec["away_odds"]),
                bookmaker=rec.get("bookmaker", "avg"),
            )
        except (KeyError, ValueError):
            continue
        tracker.add_snapshot(
            home_team=rec["home"],
            away_team=rec["away"],
            match_date=match_date_iso,
            snapshot=snap,
        )
        loaded += 1
    return loaded
