"""The Odds API — Historical endpoint client (Phase 8).

Fetches ``/v4/historical/sports/{sport}/odds?date=<ISO>`` snapshots and
persists them into a league/season-scoped Parquet cache under
``data/odds_snapshots/``.

**Quota**: one historical call costs ``10 × regions × markets`` credits and
returns *all upcoming events* for that sport at the requested timestamp.
A persistent monthly counter in ``data/odds_snapshots/_credits.json``
guards against runaway consumption.

Opt-in via ``THEODDS_HISTORICAL_ENABLED=1`` + ``THEODDS_HISTORICAL_API_KEY``
(or fallback to ``ODDS_API_KEY``).

Docs: https://the-odds-api.com/liveapi/guides/v4/#get-historical-odds
"""
from __future__ import annotations

import json
import statistics
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from football_betting.config import (
    LEAGUES,
    ODDS_API_HISTORICAL_CFG,
    ODDS_SNAPSHOT_DIR,
    OddsApiHistoricalConfig,
)
from football_betting.scraping.team_names import normalize


class OddsApiHistoricalError(RuntimeError):
    """Raised on missing key, HTTP failure, or quota abort."""


# ───────────────────────── Season helpers ─────────────────────────


# European football seasons: Aug 1 → May 31 next calendar year.
# "2024-25" → (2024-08-01, 2025-05-31).
def season_window(season: str) -> tuple[date, date]:
    try:
        start_year_s, end_year_s = season.split("-")
        start_year = int(start_year_s)
        # "2024-25" → end_year_full = 2025
        end_year = int(start_year_s[:2] + end_year_s) if len(end_year_s) == 2 else int(end_year_s)
    except (ValueError, IndexError) as exc:
        raise OddsApiHistoricalError(f"Bad season string {season!r}") from exc
    return date(start_year, 8, 1), date(end_year, 5, 31)


# ───────────────────────── Budget tracking ─────────────────────────


@dataclass(slots=True)
class BudgetTracker:
    """Persistent monthly credits counter under ODDS_SNAPSHOT_DIR/_credits.json.

    File format: ``{"YYYY-MM": consumed_credits, ...}``.
    """

    path: Path = field(default_factory=lambda: ODDS_SNAPSHOT_DIR / "_credits.json")

    def _load(self) -> dict[str, int]:
        if not self.path.is_file():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return {str(k): int(v) for k, v in data.items()}
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return {}

    def _save(self, data: dict[str, int]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _month_key(at: datetime | None = None) -> str:
        now = at or datetime.now(UTC)
        return f"{now.year:04d}-{now.month:02d}"

    def consumed_this_month(self, at: datetime | None = None) -> int:
        return self._load().get(self._month_key(at), 0)

    def add(self, credits: int, at: datetime | None = None) -> int:
        data = self._load()
        key = self._month_key(at)
        data[key] = data.get(key, 0) + int(credits)
        self._save(data)
        return data[key]

    def would_exceed(
        self,
        add_credits: int,
        monthly_budget: int,
        at: datetime | None = None,
    ) -> bool:
        return self.consumed_this_month(at) + add_credits > monthly_budget


# ───────────────────────── Parquet cache ─────────────────────────


SNAPSHOT_COLUMNS = (
    "league",
    "season",
    "match_date",     # ISO date (local league date)
    "home_team",      # normalised
    "away_team",      # normalised
    "raw_home",
    "raw_away",
    "snapshot_ts",    # UTC ISO
    "kickoff_utc",    # UTC ISO
    "hours_before_kickoff",
    "market",         # "h2h" | "totals" | "spreads"
    "line",           # totals/spread line (None for h2h)
    "bookmaker",      # "consensus" for median, else book key
    "n_bookmakers",
    "price_home",
    "price_draw",
    "price_away",
)


def cache_path(league_key: str, season: str, markets: str) -> Path:
    safe_markets = markets.replace(",", "_")
    return ODDS_SNAPSHOT_DIR / f"{league_key.upper()}_{season}_{safe_markets}.parquet"


def load_cached(
    league_key: str,
    season: str,
    markets: str,
) -> pd.DataFrame:
    path = cache_path(league_key, season, markets)
    if not path.exists():
        return pd.DataFrame(columns=list(SNAPSHOT_COLUMNS))
    return pd.read_parquet(path)


def append_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    df_new = pd.DataFrame(rows, columns=list(SNAPSHOT_COLUMNS))
    if path.exists():
        df_old = pd.read_parquet(path)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    # Idempotent: drop duplicate (match, snapshot_ts, market, line, bookmaker).
    df = df.drop_duplicates(
        subset=[
            "match_date",
            "home_team",
            "away_team",
            "snapshot_ts",
            "market",
            "line",
            "bookmaker",
        ],
        keep="last",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


# ───────────────────────── Timestamp planning ─────────────────────────


def plan_snapshot_timestamps(
    season_start: date,
    season_end: date,
    *,
    weekday_anchors: tuple[int, ...] = (4,),  # Fri noon = typical matchday start
    hours_before_anchor: tuple[int, ...] = (168, 24, 2),
    anchor_hour_utc: int = 12,
) -> list[datetime]:
    """Generate a list of UTC datetimes to poll.

    One snapshot per (matchweek anchor × hours_before). For leagues
    playing Sat/Sun, a Friday-noon anchor reliably catches the weekend
    fixtures as *upcoming* events.
    """
    # Find the first Friday on/after season_start.
    days_ahead = (weekday_anchors[0] - season_start.weekday()) % 7
    cursor = season_start + timedelta(days=days_ahead)
    anchors: list[date] = []
    while cursor <= season_end:
        anchors.append(cursor)
        cursor += timedelta(days=7)

    out: list[datetime] = []
    for d in anchors:
        for h in hours_before_anchor:
            base = datetime(d.year, d.month, d.day, anchor_hour_utc, tzinfo=UTC)
            out.append(base - timedelta(hours=h))
    return sorted(set(out))


# ───────────────────────── Client ─────────────────────────


@dataclass(slots=True)
class OddsApiHistoricalClient:
    cfg: OddsApiHistoricalConfig = ODDS_API_HISTORICAL_CFG
    budget: BudgetTracker = field(default_factory=BudgetTracker)
    _session: requests.Session = field(default_factory=requests.Session)

    def _require_key(self) -> str:
        key = self.cfg.api_key
        if not key:
            raise OddsApiHistoricalError(
                "No API key. Set THEODDS_HISTORICAL_API_KEY or ODDS_API_KEY in .env."
            )
        return key

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.cfg.base_url}{path}"
        merged = {"apiKey": self._require_key(), **params}
        try:
            r = self._session.get(url, params=merged, timeout=self.cfg.timeout_seconds)
        except requests.RequestException as exc:
            raise OddsApiHistoricalError(f"HTTP error for {url}: {exc}") from exc
        if r.status_code == 401:
            raise OddsApiHistoricalError("Odds API rejected the key (HTTP 401).")
        if r.status_code == 429:
            raise OddsApiHistoricalError("Odds API quota exhausted (HTTP 429).")
        if r.status_code != 200:
            raise OddsApiHistoricalError(f"Odds API HTTP {r.status_code}: {r.text[:300]}")
        return r.json()

    def fetch_snapshot(
        self,
        league_key: str,
        ts_utc: datetime,
    ) -> dict[str, Any]:
        """Single ``/v4/historical/sports/{sport}/odds`` call.

        Returns the raw JSON payload. Caller must track credit consumption.
        """
        league_key = league_key.upper()
        sport = self.cfg.sport_keys.get(league_key)
        if sport is None:
            raise OddsApiHistoricalError(f"No sport_key for league {league_key}")
        iso = ts_utc.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = self._get(
            f"/historical/sports/{sport}/odds",
            {
                "regions": self.cfg.regions,
                "markets": self.cfg.markets,
                "oddsFormat": self.cfg.odds_format,
                "dateFormat": self.cfg.date_format,
                "date": iso,
            },
        )
        if not isinstance(payload, dict):
            raise OddsApiHistoricalError(f"Unexpected payload shape: {payload!r:200}")
        return payload

    # ───────────────────────── Backfill orchestration ─────────────────────────

    def backfill_season(
        self,
        league_key: str,
        season: str,
        *,
        timestamps: list[datetime] | None = None,
        max_credits: int | None = None,
        dry_run: bool = False,
        progress_cb=None,
    ) -> dict[str, int]:
        """Pull all planned snapshots for (league, season) into Parquet cache.

        Returns counters: ``{calls, credits, rows, skipped_cached, aborted}``.
        """
        league_key = league_key.upper()
        if league_key not in LEAGUES:
            raise OddsApiHistoricalError(f"Unknown league: {league_key}")
        if league_key not in self.cfg.sport_keys:
            raise OddsApiHistoricalError(f"No sport_key for league {league_key}")

        start, end = season_window(season)
        if timestamps is None:
            timestamps = plan_snapshot_timestamps(
                start, end,
                hours_before_anchor=self.cfg.snapshot_hours_before,
            )

        path = cache_path(league_key, season, self.cfg.markets)
        already = load_cached(league_key, season, self.cfg.markets)
        seen_ts = set(already["snapshot_ts"].astype(str).tolist()) if not already.empty else set()

        cpc = self.cfg.credits_per_call()
        counters = {"calls": 0, "credits": 0, "rows": 0, "skipped_cached": 0, "aborted": 0}

        effective_cap = max_credits if max_credits is not None else self.cfg.max_credits_per_run

        for ts in timestamps:
            iso = ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            if iso in seen_ts:
                counters["skipped_cached"] += 1
                continue

            # Budget guards.
            if counters["credits"] + cpc > effective_cap:
                counters["aborted"] = 1
                break
            if self.budget.would_exceed(cpc, self.cfg.monthly_budget_credits):
                counters["aborted"] = 1
                break

            if dry_run:
                counters["calls"] += 1
                counters["credits"] += cpc
                continue

            payload = self.fetch_snapshot(league_key, ts)
            self.budget.add(cpc)
            counters["calls"] += 1
            counters["credits"] += cpc

            rows = list(
                parse_snapshot_payload(
                    payload,
                    league_key=league_key,
                    season=season,
                    markets=self.cfg.markets,
                )
            )
            if rows:
                append_rows(path, rows)
                counters["rows"] += len(rows)
                # Update the in-memory "seen_ts" to keep the same run idempotent.
                seen_ts.add(iso)

            if progress_cb is not None:
                progress_cb(iso=iso, counters=dict(counters))

            time.sleep(self.cfg.request_delay_seconds)

        return counters


# ───────────────────────── Payload parser ─────────────────────────


def parse_snapshot_payload(
    payload: dict[str, Any],
    *,
    league_key: str,
    season: str,
    markets: str,
) -> Iterable[dict[str, Any]]:
    """Flatten one historical snapshot JSON into flat Parquet rows.

    The Odds API historical envelope is:
    ``{"timestamp": ISO, "previous_timestamp": ISO|None,
       "next_timestamp": ISO|None, "data": [<event>, ...]}``.
    Each ``<event>`` has the same shape as the live ``/v4/odds`` response.
    """
    snapshot_ts = payload.get("timestamp")
    events = payload.get("data") or []
    if snapshot_ts is None or not isinstance(events, list):
        return

    snap_ts_dt = datetime.fromisoformat(str(snapshot_ts).replace("Z", "+00:00"))
    if snap_ts_dt.tzinfo is None:
        snap_ts_dt = snap_ts_dt.replace(tzinfo=UTC)

    requested_markets = {m.strip() for m in markets.split(",") if m.strip()}

    for ev in events:
        raw_home = ev.get("home_team")
        raw_away = ev.get("away_team")
        commence = ev.get("commence_time")
        bookmakers = ev.get("bookmakers") or []
        if not raw_home or not raw_away or not commence:
            continue

        kickoff_utc = datetime.fromisoformat(str(commence).replace("Z", "+00:00"))
        if kickoff_utc.tzinfo is None:
            kickoff_utc = kickoff_utc.replace(tzinfo=UTC)
        # Leakage guard: snapshot must be strictly pre-kickoff.
        if snap_ts_dt >= kickoff_utc:
            continue

        hours_before = (kickoff_utc - snap_ts_dt).total_seconds() / 3600.0
        match_date = kickoff_utc.date().isoformat()
        home_norm = normalize(league_key, raw_home)
        away_norm = normalize(league_key, raw_away)

        # ── Consensus (median) rows per market ───────────────────────────
        per_market: dict[tuple[str, float | None], dict[str, list[float]]] = {}
        for book in bookmakers:
            for market in book.get("markets", []):
                mkey = market.get("key")
                if mkey not in requested_markets:
                    continue
                if mkey == "h2h":
                    line: float | None = None
                    outcomes = {o.get("name"): o.get("price") for o in market.get("outcomes", [])}
                    h = outcomes.get(raw_home)
                    a = outcomes.get(raw_away)
                    d = outcomes.get("Draw")
                    if h is None or d is None or a is None:
                        continue
                    bucket = per_market.setdefault(
                        ("h2h", line),
                        {"home": [], "draw": [], "away": []},
                    )
                    try:
                        bucket["home"].append(float(h))
                        bucket["draw"].append(float(d))
                        bucket["away"].append(float(a))
                    except (TypeError, ValueError):
                        continue
                elif mkey in ("totals", "spreads"):
                    # Group outcomes by point/line.
                    by_line: dict[float, dict[str, float]] = {}
                    for o in market.get("outcomes", []):
                        try:
                            pt = float(o.get("point"))
                            price = float(o.get("price"))
                        except (TypeError, ValueError):
                            continue
                        by_line.setdefault(pt, {})[str(o.get("name"))] = price
                    for pt, prices in by_line.items():
                        # For totals: keys Over / Under (map Over→home, Under→away)
                        # For spreads: keys raw_home / raw_away
                        if mkey == "totals":
                            over = prices.get("Over")
                            under = prices.get("Under")
                            if over is None or under is None:
                                continue
                            bucket = per_market.setdefault(
                                (mkey, pt),
                                {"home": [], "draw": [], "away": []},
                            )
                            bucket["home"].append(over)
                            bucket["away"].append(under)
                        else:  # spreads
                            h = prices.get(raw_home)
                            a = prices.get(raw_away)
                            if h is None or a is None:
                                continue
                            bucket = per_market.setdefault(
                                (mkey, pt),
                                {"home": [], "draw": [], "away": []},
                            )
                            bucket["home"].append(h)
                            bucket["away"].append(a)

        for (mkey, line), prices in per_market.items():
            home_prices = prices["home"]
            draw_prices = prices["draw"]
            away_prices = prices["away"]
            if not home_prices or not away_prices:
                continue
            row = {
                "league": league_key,
                "season": season,
                "match_date": match_date,
                "home_team": home_norm,
                "away_team": away_norm,
                "raw_home": raw_home,
                "raw_away": raw_away,
                "snapshot_ts": snap_ts_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "kickoff_utc": kickoff_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "hours_before_kickoff": round(hours_before, 3),
                "market": mkey,
                "line": line,
                "bookmaker": "consensus",
                "n_bookmakers": len(home_prices),
                "price_home": float(statistics.median(home_prices)),
                "price_draw": float(statistics.median(draw_prices)) if draw_prices else None,
                "price_away": float(statistics.median(away_prices)),
            }
            yield row
