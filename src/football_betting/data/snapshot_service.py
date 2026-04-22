"""Opening-line snapshot capture and merge utilities (Phase 4).

This module glues together three pieces so the CLV pipeline sees a real
opening-vs-closing spread:

1. **Capture** — poll a pre-match odds source (The Odds API; optionally
   Sofascore if ``SCRAPING_ENABLED=1``) for fixtures whose kickoff is
   within a configurable T-minus window and persist the response via
   :func:`football_betting.data.odds_snapshots.append_snapshot`.
2. **Merge** — replay the persisted JSONL snapshots into an in-memory
   ``dict[(date, home, away) -> MatchOdds]``.
3. **Attach** — copy the merged opening lines onto ``Match.opening_odds``
   for every historical/training match whose closing odds we already have.

Design notes:
    * The capture step is **opt-in** and respects ``SCRAPING_ENABLED``.
    * Merging is purely filesystem-local and side-effect-free.
    * Missing snapshots are *not* an error — Phase 4 degrades gracefully
      to Phase 3 behaviour (CLV ≡ 0) until real data is available.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from football_betting.data.models import Fixture, Match, MatchOdds
from football_betting.data.odds_snapshots import (
    _iter_records,
    append_snapshot,
)

OpeningKey = tuple[str, str, str]  # (match_date ISO, home, away)


@dataclass(slots=True)
class CapturedSnapshot:
    """One pre-match odds row persisted during :func:`capture_odds_snapshot`."""

    league: str
    match_date: str
    home_team: str
    away_team: str
    captured_at: datetime
    odds: MatchOdds


def _within_tminus_window(
    kickoff: datetime | None,
    now: datetime,
    t_minus_hours: int,
) -> bool:
    """True when ``kickoff`` falls inside the ``[now, now + T-h]`` pre-match window."""
    if kickoff is None:
        return False
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    delta = kickoff - now
    return timedelta(0) <= delta <= timedelta(hours=t_minus_hours)


def capture_odds_snapshot(
    league_key: str,
    fixtures: Iterable[Fixture],
    *,
    t_minus_hours: int = 48,
    source: str = "odds_api",
    now: datetime | None = None,
) -> list[CapturedSnapshot]:
    """Persist pre-match odds for fixtures within the T-minus window.

    Returns the list of snapshots actually written. The function only
    persists fixtures that carry an ``odds`` payload (so callers are
    expected to enrich ``fixtures`` from The Odds API or Sofascore before
    invoking this helper).

    The ``source`` argument is stored in :class:`CapturedSnapshot` so the
    caller can log provenance; it is *not* round-tripped through the
    JSONL store (that one already carries the bookmaker label on the
    :class:`MatchOdds` itself).
    """
    now = now or datetime.now(UTC)
    captured: list[CapturedSnapshot] = []
    for fx in fixtures:
        if fx.odds is None:
            continue
        kickoff = fx.resolve_kickoff()
        if not _within_tminus_window(kickoff, now, t_minus_hours):
            continue
        append_snapshot(
            league_key,
            fx.home_team,
            fx.away_team,
            fx.date.isoformat(),
            fx.odds,
            timestamp=now,
        )
        captured.append(
            CapturedSnapshot(
                league=league_key.upper(),
                match_date=fx.date.isoformat(),
                home_team=fx.home_team,
                away_team=fx.away_team,
                captured_at=now,
                odds=fx.odds,
            )
        )
    _ = source  # kept for caller-side logging; intentional no-op here
    return captured


def _select_opening_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the earliest-timestamp snapshot as the opening line."""
    if not records:
        return None
    parsed: list[tuple[datetime, dict[str, Any]]] = []
    for rec in records:
        ts_raw = rec.get("timestamp")
        if not isinstance(ts_raw, str):
            continue
        try:
            ts = datetime.fromisoformat(ts_raw)
        except ValueError:
            continue
        parsed.append((ts, rec))
    if not parsed:
        return None
    parsed.sort(key=lambda p: p[0])
    return parsed[0][1]


def _grouped_snapshots(
    league_key: str,
) -> Iterator[tuple[OpeningKey, list[dict[str, Any]]]]:
    """Group persisted snapshots by ``(date, home, away)``."""
    groups: dict[OpeningKey, list[dict[str, Any]]] = {}
    for rec in _iter_records(league_key):
        try:
            key: OpeningKey = (rec["date"], rec["home"], rec["away"])
        except KeyError:
            continue
        groups.setdefault(key, []).append(rec)
    yield from groups.items()


def load_opening_odds(league_key: str) -> dict[OpeningKey, MatchOdds]:
    """Return ``{(date, home, away): opening_MatchOdds}`` from persisted snapshots."""
    out: dict[OpeningKey, MatchOdds] = {}
    for key, records in _grouped_snapshots(league_key):
        opener = _select_opening_record(records)
        if opener is None:
            continue
        try:
            odds = MatchOdds(
                home=float(opener["home_odds"]),
                draw=float(opener["draw_odds"]),
                away=float(opener["away_odds"]),
                bookmaker=str(opener.get("bookmaker", "avg")) + "_opening",
            )
        except (KeyError, ValueError, TypeError):
            continue
        out[key] = odds
    return out


def merge_snapshots_into_matches(
    matches: list[Match],
    league_key: str,
    *,
    opening_window: str = "T-48h",
) -> list[Match]:
    """Attach opening odds (from persisted snapshots) to existing matches.

    Matches without a persisted snapshot fall back to whatever
    ``opening_odds`` already carried (typically the Bet365 proxy populated
    by the football-data loader) and ultimately to ``None`` — at which
    point the backtester will treat ``bet_odds == closing_odds`` and CLV
    degenerates to zero for that bet (graceful-None policy).

    The ``opening_window`` string is retained in the signature for future
    multi-window support (e.g. ``T-24h`` vs ``T-1h``); currently only the
    earliest persisted snapshot is used.
    """
    opening_map = load_opening_odds(league_key)
    if not opening_map:
        return matches
    enriched: list[Match] = []
    for m in matches:
        key: OpeningKey = (m.date.isoformat(), m.home_team, m.away_team)
        opening = opening_map.get(key)
        if opening is None:
            enriched.append(m)
            continue
        enriched.append(m.model_copy(update={"opening_odds": opening}))
    _ = opening_window
    return enriched
