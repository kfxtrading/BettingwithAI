"""Live match-result settlement via The Odds API or Football-Data CSVs.

Maintains ``data/live_scores.jsonl`` — one row per completed fixture keyed
by ``(league_code, date, home_norm, away_norm)``. This file is merged into
:func:`football_betting.evaluation.grader._load_results_for_league` so
``regrade_all()`` can settle pending bets as soon as the Odds API reports
the final whistle (typically 1–3 min post-game), long before the
football-data.co.uk CSVs are refreshed.

Workflow::

    pending_league_codes()          # which leagues still have pending bets?
    poll_and_store_scores([...])    # hit Odds API /scores, append new rows
    regrade_all()                   # now includes live results

The daily football-data cron still runs and overwrites live rows on
conflict — football-data is the authoritative ground truth.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from datetime import date as date_cls
from pathlib import Path

from football_betting.config import DATA_DIR, LEAGUES
from football_betting.evaluation.grader import GRADED_FILE, _norm, load_graded
from football_betting.scraping.odds_api import (
    OddsApiClient,
    OddsApiError,
    OddsApiQuotaError,
    ScoreResult,
    looks_like_quota_error,
)

logger = logging.getLogger(__name__)

LIVE_SCORES_FILE: Path = DATA_DIR / "live_scores.jsonl"

_CODE_TO_KEY: dict[str, str] = {cfg.code: key for key, cfg in LEAGUES.items()}


@dataclass(slots=True)
class LiveScoreRow:
    league_code: str
    date: str  # YYYY-MM-DD (local league date)
    home_norm: str
    away_norm: str
    ftr: str  # "H" | "D" | "A" (for live matches: current leader, "D" if tied)
    fthg: int
    ftag: int
    source: str  # "odds_api"
    fetched_at: str  # ISO UTC
    status: str = "completed"  # "completed" | "live"
    kickoff_utc: str | None = None  # ISO UTC of kickoff

    def key(self) -> tuple[str, date_cls, str, str]:
        return (
            self.league_code,
            datetime.strptime(self.date, "%Y-%m-%d").date(),
            self.home_norm,
            self.away_norm,
        )


# ───────────────────────── Persistence ─────────────────────────

# path+size+mtime keyed cache for _load_rows(); keeps hot-path enrichment
# fast so raising poll frequency doesn't linearly amplify disk I/O per
# request. Including path and size guards against low-resolution mtimes
# (e.g. Windows) and path re-points during tests.
_ROWS_CACHE: list[LiveScoreRow] | None = None
_ROWS_CACHE_KEY: tuple[str, int, float] | None = None


def _parse_rows() -> list[LiveScoreRow]:
    rows: list[LiveScoreRow] = []
    with LIVE_SCORES_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(LiveScoreRow(**json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue
    return rows


def _cache_key() -> tuple[str, int, float] | None:
    try:
        st = LIVE_SCORES_FILE.stat()
    except OSError:
        return None
    return (str(LIVE_SCORES_FILE), st.st_size, st.st_mtime)


def _load_rows() -> list[LiveScoreRow]:
    """Return cached rows; reparse only when the file's identity changed."""
    global _ROWS_CACHE, _ROWS_CACHE_KEY
    if not LIVE_SCORES_FILE.exists():
        _ROWS_CACHE = []
        _ROWS_CACHE_KEY = None
        return []
    key = _cache_key()
    if key is None:
        return _parse_rows()
    if _ROWS_CACHE is not None and key == _ROWS_CACHE_KEY:
        return _ROWS_CACHE
    rows = _parse_rows()
    _ROWS_CACHE = rows
    _ROWS_CACHE_KEY = key
    return rows


def _write_rows(rows: Iterable[LiveScoreRow]) -> None:
    global _ROWS_CACHE, _ROWS_CACHE_KEY
    LIVE_SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = LIVE_SCORES_FILE.with_suffix(".tmp")
    materialised = list(rows)
    with tmp.open("w", encoding="utf-8") as fh:
        for r in materialised:
            fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    tmp.replace(LIVE_SCORES_FILE)
    # Prime the cache so the next read is a hit without a reparse.
    _ROWS_CACHE = materialised
    _ROWS_CACHE_KEY = _cache_key()


def load_live_results_for_code(
    code: str,
) -> dict[tuple[date_cls, str, str], tuple[str, int, int]]:
    """Return {(date, home_norm, away_norm): (ftr, fthg, ftag)} for a league code.

    Shape matches :func:`grader._load_results_for_league` so it can be merged.
    Only *completed* rows are returned — live-in-progress matches must never
    leak into the grading pipeline (would prematurely settle bets).
    """
    out: dict[tuple[date_cls, str, str], tuple[str, int, int]] = {}
    for r in _load_rows():
        if r.league_code != code:
            continue
        if r.status != "completed":
            continue
        try:
            d = datetime.strptime(r.date, "%Y-%m-%d").date()
        except ValueError:
            continue
        out[(d, r.home_norm, r.away_norm)] = (r.ftr, r.fthg, r.ftag)
    return out


def load_live_matches_for_code(
    code: str,
) -> dict[tuple[date_cls, str, str], tuple[str, str, int, int]]:
    """Return {(date, home_norm, away_norm): (status, ftr, fthg, ftag)} for a league.

    Includes BOTH live and completed rows. Used by the API anrichment layer
    to surface Live / Tipp-richtig badges on the homepage.
    """
    out: dict[tuple[date_cls, str, str], tuple[str, str, int, int]] = {}
    for r in _load_rows():
        if r.league_code != code:
            continue
        try:
            d = datetime.strptime(r.date, "%Y-%m-%d").date()
        except ValueError:
            continue
        out[(d, r.home_norm, r.away_norm)] = (r.status, r.ftr, r.fthg, r.ftag)
    return out


# ───────────────────────── Pending-bet discovery ─────────────────────────


def pending_league_codes() -> set[str]:
    """League codes that still have `status == "pending"` bets in graded log."""
    if not GRADED_FILE.exists():
        return set()
    codes: set[str] = set()
    for g in load_graded():
        if g.status != "pending":
            continue
        cfg = LEAGUES.get(g.league)
        if cfg is not None:
            codes.add(cfg.code)
    return codes


# ───────────────────────── Polling ─────────────────────────


def _now_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _score_to_row(s: ScoreResult, code: str) -> LiveScoreRow | None:
    """Convert an Odds-API score result to a persistable row.

    Returns a row with ``status="completed"`` for full-time results or
    ``status="live"`` for matches whose kickoff has passed but that are
    not yet completed (includes half-time / in-play). Future-scheduled
    matches (kickoff still in the future) yield ``None``.
    """
    now = datetime.now(UTC)
    kickoff_iso: str | None = None
    if s.kickoff_utc is not None:
        kickoff_iso = (
            s.kickoff_utc.astimezone(UTC)
            .isoformat()
            .replace("+00:00", "Z")
        )

    if s.completed:
        if s.home_goals is None or s.away_goals is None:
            return None
        ftr = s.ftr
        if ftr is None:
            return None
        return LiveScoreRow(
            league_code=code,
            date=s.date.isoformat(),
            home_norm=_norm(s.home_team),
            away_norm=_norm(s.away_team),
            ftr=ftr,
            fthg=int(s.home_goals),
            ftag=int(s.away_goals),
            source="odds_api",
            fetched_at=_now_utc_iso(),
            status="completed",
            kickoff_utc=kickoff_iso,
        )

    # Not completed — only persist if already kicked off (live/in-play).
    if s.kickoff_utc is None or s.kickoff_utc > now:
        return None

    hg = int(s.home_goals) if s.home_goals is not None else 0
    ag = int(s.away_goals) if s.away_goals is not None else 0
    if hg > ag:
        ftr = "H"
    elif hg < ag:
        ftr = "A"
    else:
        ftr = "D"
    return LiveScoreRow(
        league_code=code,
        date=s.date.isoformat(),
        home_norm=_norm(s.home_team),
        away_norm=_norm(s.away_team),
        ftr=ftr,
        fthg=hg,
        ftag=ag,
        source="odds_api",
        fetched_at=_now_utc_iso(),
        status="live",
        kickoff_utc=kickoff_iso,
    )


def poll_and_store_scores(
    league_codes: Iterable[str] | None = None,
    *,
    client: OddsApiClient | None = None,
    days_from: int = 3,
) -> int:
    """Hit The Odds API `/scores` for each league, append newly completed matches.

    Returns the number of *new* rows written (dedup by key). Existing rows
    are preserved; re-polling the same match is a no-op.
    """
    client = client or OddsApiClient()
    codes = list(league_codes) if league_codes is not None else [
        cfg.code for cfg in LEAGUES.values()
    ]
    if not codes:
        return 0

    existing = {r.key(): r for r in _load_rows()}
    added = 0
    updated = 0
    for code in codes:
        league_key = _CODE_TO_KEY.get(code)
        if league_key is None:
            continue
        try:
            scores = client.fetch_scores(league_key, days_from=days_from)
        except OddsApiQuotaError:
            # Let the scheduler / caller see quota exhaustion so it can
            # pause polling. No point iterating the remaining leagues —
            # the same key would fail for all of them.
            raise
        except OddsApiError as e:
            if looks_like_quota_error(e):
                raise OddsApiQuotaError(str(e)) from e
            logger.warning("[live] Odds API scores failed for %s: %s", league_key, e)
            continue
        for s in scores:
            row = _score_to_row(s, code)
            if row is None:
                continue
            prev = existing.get(row.key())
            if prev is None:
                existing[row.key()] = row
                added += 1
                continue
            # Never downgrade a completed row back to live.
            if prev.status == "completed" and row.status == "live":
                continue
            state_changed = prev.status != row.status
            score_changed = (prev.ftr, prev.fthg, prev.ftag) != (
                row.ftr, row.fthg, row.ftag,
            )
            if state_changed or score_changed:
                logger.info(
                    "[live] Update %s %s %s-%s: %d-%d (%s/%s) -> %d-%d (%s/%s)",
                    row.date, code, row.home_norm, row.away_norm,
                    prev.fthg, prev.ftag, prev.ftr, prev.status,
                    row.fthg, row.ftag, row.ftr, row.status,
                )
                existing[row.key()] = row
                updated += 1

    if added or updated:
        _write_rows(existing.values())
        logger.info(
            "[live] Added %d new + %d corrected completed results", added, updated,
        )
    return added + updated


def poll_and_store_scores_football_data(
    league_codes: Iterable[str] | None = None,
    *,
    days_from: int = 3,
    refresh: bool = True,
) -> int:
    """Refresh Football-Data CSVs and persist recently completed results.

    Football-Data is not a live in-play source, so this writes only
    ``status="completed"`` rows. It is intended for TheOdds-free operation
    where the evening CSV refresh is enough to settle bets and update the UI.
    """
    from football_betting.data.football_data import load_completed_results

    codes = list(league_codes) if league_codes is not None else [
        cfg.code for cfg in LEAGUES.values()
    ]
    if not codes:
        return 0

    existing = {r.key(): r for r in _load_rows()}
    added = 0
    updated = 0
    rows = load_completed_results(
        league_codes=codes,
        days_from=days_from,
        refresh=refresh,
    )
    for item in rows:
        row = LiveScoreRow(
            league_code=str(item["league_code"]),
            date=str(item["date"]),
            home_norm=_norm(str(item["home_team"])),
            away_norm=_norm(str(item["away_team"])),
            ftr=str(item["ftr"]),
            fthg=int(item["fthg"]),
            ftag=int(item["ftag"]),
            source="football_data",
            fetched_at=_now_utc_iso(),
            status="completed",
            kickoff_utc=item.get("kickoff_utc"),
        )
        prev = existing.get(row.key())
        if prev is None:
            existing[row.key()] = row
            added += 1
            continue
        score_changed = (prev.ftr, prev.fthg, prev.ftag, prev.status) != (
            row.ftr,
            row.fthg,
            row.ftag,
            row.status,
        )
        if score_changed:
            existing[row.key()] = row
            updated += 1

    if added or updated:
        _write_rows(existing.values())
        logger.info(
            "[live] Football-Data added %d new + %d corrected completed results",
            added,
            updated,
        )
    return added + updated


__all__ = [
    "LIVE_SCORES_FILE",
    "LiveScoreRow",
    "load_live_matches_for_code",
    "load_live_results_for_code",
    "pending_league_codes",
    "poll_and_store_scores",
    "poll_and_store_scores_football_data",
]
