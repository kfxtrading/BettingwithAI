"""
Sofascore HTTP client for match statistics (xG, lineups, player ratings).

IMPORTANT: This scraper is for personal research only. Sofascore has no public API
license. The client:
* Waits 25 seconds between requests (configurable via SofascoreConfig)
* Rotates user agents
* Caches all responses in SQLite (default TTL 7 days)
* Is disabled by default (set SCRAPING_ENABLED=1 to activate)

For production/commercial use, switch to a paid API like API-Football or Sportmonks.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from curl_cffi import requests
from rich.console import Console

from football_betting.config import (
    LEAGUES,
    SOFASCORE_CFG,
    SOFASCORE_DIR,
    SofascoreConfig,
)
from football_betting.scraping.cache import ResponseCache
from football_betting.scraping.rate_limiter import TokenBucketLimiter

console = Console()


@dataclass(slots=True)
class SofascoreMatch:
    """Structured match data from Sofascore."""

    event_id: int
    tournament_id: int
    home_team: str
    away_team: str
    home_goals: int | None
    away_goals: int | None
    start_timestamp: int
    status: str  # "finished" | "scheduled" | "inprogress"

    # Extended stats (fetched via separate endpoint)
    home_xg: float | None = None
    away_xg: float | None = None
    home_shots: int | None = None
    away_shots: int | None = None
    home_shots_on_target: int | None = None
    away_shots_on_target: int | None = None
    home_big_chances: int | None = None
    away_big_chances: int | None = None

    # Lineup data
    home_avg_rating: float | None = None
    away_avg_rating: float | None = None
    home_starting_xi: list[int] = field(default_factory=list)  # player IDs
    away_starting_xi: list[int] = field(default_factory=list)

    @property
    def date(self) -> date:
        return datetime.fromtimestamp(self.start_timestamp).date()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "tournament_id": self.tournament_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_goals": self.home_goals,
            "away_goals": self.away_goals,
            "date": self.date.isoformat(),
            "status": self.status,
            "home_xg": self.home_xg,
            "away_xg": self.away_xg,
            "home_shots": self.home_shots,
            "away_shots": self.away_shots,
            "home_shots_on_target": self.home_shots_on_target,
            "away_shots_on_target": self.away_shots_on_target,
            "home_big_chances": self.home_big_chances,
            "away_big_chances": self.away_big_chances,
            "home_avg_rating": self.home_avg_rating,
            "away_avg_rating": self.away_avg_rating,
            "home_starting_xi": list(self.home_starting_xi),
            "away_starting_xi": list(self.away_starting_xi),
        }


@dataclass(slots=True)
class SofascoreClient:
    """Rate-limited, cached Sofascore client."""

    cfg: SofascoreConfig = field(default_factory=lambda: SOFASCORE_CFG)
    cache: ResponseCache = field(default_factory=ResponseCache)
    _limiter: TokenBucketLimiter = field(init=False)

    def __post_init__(self) -> None:
        self._limiter = TokenBucketLimiter.from_delay(
            self.cfg.request_delay_seconds, burst=1
        )

    # ───────────────────────── HTTP layer ─────────────────────────

    def _build_headers(self) -> dict[str, str]:
        ua = random.choice(self.cfg.user_agents)
        return {
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

    def _fetch_json(
        self,
        path: str,
        params: dict | None = None,
        cache_ttl: int | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any] | None:
        """Fetch with cache + rate limit + retries. Returns parsed JSON or None."""
        if not self.cfg.enabled:
            raise RuntimeError(
                "Sofascore scraping disabled. Set env var SCRAPING_ENABLED=1 to enable."
            )

        url = f"{self.cfg.base_url}{path}"

        # Try cache first
        if use_cache:
            cached = self.cache.get(url, params)
            if cached is not None:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    self.cache.delete(url, params)

        # Rate limit
        self._limiter.acquire()

        # Retry loop
        last_exc: Exception | None = None
        for attempt in range(self.cfg.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self._build_headers(),
                    timeout=self.cfg.timeout_seconds,
                    impersonate="chrome120",
                )
                if response.status_code == 200:
                    if use_cache:
                        self.cache.set(url, response.text, params=params, ttl_seconds=cache_ttl)
                    return response.json()
                if response.status_code in (429, 503):
                    wait = self.cfg.retry_backoff_base ** (attempt + 1)
                    console.log(f"[yellow]Rate limited ({response.status_code}), sleeping {wait}s[/yellow]")
                    import time
                    time.sleep(wait)
                    continue
                if response.status_code == 404:
                    return None
                console.log(f"[red]HTTP {response.status_code} for {url}[/red]")
                return None
            except requests.RequestsError as e:
                last_exc = e
                wait = self.cfg.retry_backoff_base ** (attempt + 1)
                console.log(f"[yellow]Request failed ({e}), retrying in {wait}s[/yellow]")
                import time
                time.sleep(wait)

        if last_exc is not None:
            console.log(f"[red]All retries exhausted: {last_exc}[/red]")
        return None

    # ───────────────────────── High-level API ─────────────────────────

    def get_season_id(self, league_key: str, season: str) -> int | None:
        """Resolve Sofascore season ID for a league + human season ('2024-25')."""
        league = LEAGUES[league_key]
        if season in league.sofascore_season_ids:
            return league.sofascore_season_ids[season]
        tid = league.sofascore_tournament_id
        if tid is None:
            return None

        data = self._fetch_json(f"/unique-tournament/{tid}/seasons")
        if not data:
            return None

        # Sofascore uses short form "24/25" in both `year` and `name`.
        # Convert "2024-25" → "24/25" and match on `year` (exact); fall back to `name` substring.
        short = f"{season[2:4]}/{season[5:7]}"
        for s in data.get("seasons", []):
            if str(s.get("year", "")) == short:
                return int(s["id"])
        for s in data.get("seasons", []):
            if short in str(s.get("name", "")):
                return int(s["id"])
        return None

    def get_round_events(self, league_key: str, season: str, round_num: int) -> list[dict]:
        """Fetch all events in one matchday."""
        tid = LEAGUES[league_key].sofascore_tournament_id
        season_id = self.get_season_id(league_key, season)
        if tid is None or season_id is None:
            return []

        data = self._fetch_json(
            f"/unique-tournament/{tid}/season/{season_id}/events/round/{round_num}"
        )
        return data.get("events", []) if data else []

    def get_season_events(self, league_key: str, season: str) -> list[dict]:
        """Iterate rounds 1-38 (most top leagues) and collect all events."""
        all_events = []
        for round_num in range(1, 39):
            events = self.get_round_events(league_key, season, round_num)
            if not events:
                # Try a few more in case of missing rounds, then stop
                if round_num > 40:
                    break
                continue
            all_events.extend(events)
        return all_events

    def get_event_statistics(self, event_id: int) -> dict[str, Any] | None:
        """xG, shots, possession, big chances for one event."""
        return self._fetch_json(f"/event/{event_id}/statistics")

    def get_event_lineups(self, event_id: int) -> dict[str, Any] | None:
        """Starting XI + bench + ratings."""
        return self._fetch_json(f"/event/{event_id}/lineups")

    # ───────────────────────── Parsing ─────────────────────────

    @staticmethod
    def _extract_stat(stats_json: dict, period: str, group: str, name: str) -> float | None:
        """Pull a single stat value from Sofascore's nested statistics response."""
        for p in stats_json.get("statistics", []):
            if p.get("period") != period:
                continue
            for g in p.get("groups", []):
                if g.get("groupName") != group:
                    continue
                for s in g.get("statisticsItems", []):
                    if s.get("name") == name:
                        # Sofascore returns "home"/"away" as string; parse
                        return float(s.get("home", 0)), float(s.get("away", 0))  # type: ignore[return-value]
        return None  # type: ignore[return-value]

    def parse_match(self, event_json: dict) -> SofascoreMatch | None:
        """Parse minimal SofascoreMatch from an event JSON (no stats)."""
        try:
            home = event_json.get("homeTeam", {})
            away = event_json.get("awayTeam", {})
            score_home = event_json.get("homeScore", {}).get("current")
            score_away = event_json.get("awayScore", {}).get("current")
            status_info = event_json.get("status", {})

            return SofascoreMatch(
                event_id=int(event_json["id"]),
                tournament_id=int(event_json.get("tournament", {}).get("id", 0)),
                home_team=str(home.get("name", "")),
                away_team=str(away.get("name", "")),
                home_goals=int(score_home) if score_home is not None else None,
                away_goals=int(score_away) if score_away is not None else None,
                start_timestamp=int(event_json.get("startTimestamp", 0)),
                status=str(status_info.get("type", "unknown")),
            )
        except (KeyError, ValueError, TypeError) as e:
            console.log(f"[red]Parse error: {e}[/red]")
            return None

    def enrich_match_with_stats(self, match: SofascoreMatch) -> SofascoreMatch:
        """Fetch + attach statistics and lineups."""
        stats = self.get_event_statistics(match.event_id)
        if stats:
            for period in stats.get("statistics", []):
                if period.get("period") != "ALL":
                    continue
                for group in period.get("groups", []):
                    for item in group.get("statisticsItems", []):
                        name = item.get("name", "")
                        h, a = item.get("home"), item.get("away")
                        try:
                            hf = float(str(h).strip("%")) if h else None
                            af = float(str(a).strip("%")) if a else None
                        except (ValueError, TypeError):
                            continue
                        if name == "Expected goals":
                            match.home_xg = hf
                            match.away_xg = af
                        elif name == "Total shots":
                            match.home_shots = int(hf) if hf else None
                            match.away_shots = int(af) if af else None
                        elif name == "Shots on target":
                            match.home_shots_on_target = int(hf) if hf else None
                            match.away_shots_on_target = int(af) if af else None
                        elif name == "Big chances":
                            match.home_big_chances = int(hf) if hf else None
                            match.away_big_chances = int(af) if af else None

        lineups = self.get_event_lineups(match.event_id)
        if lineups:
            for side in ("home", "away"):
                side_data = lineups.get(side, {})
                players = side_data.get("players", [])
                # Average rating of starting 11
                starting = [p for p in players if not p.get("substitute", False)]
                ratings = [
                    float(p.get("statistics", {}).get("rating", 0))
                    for p in starting
                    if p.get("statistics", {}).get("rating")
                ]
                avg_rating = sum(ratings) / len(ratings) if ratings else None
                xi = [int(p.get("player", {}).get("id", 0)) for p in starting]
                if side == "home":
                    match.home_avg_rating = avg_rating
                    match.home_starting_xi = xi
                else:
                    match.away_avg_rating = avg_rating
                    match.away_starting_xi = xi

        return match

    # ───────────────────────── Persistence ─────────────────────────

    def save_matches(self, matches: list[SofascoreMatch], league_key: str, season: str) -> Path:
        """Persist scraped matches as JSON."""
        path = SOFASCORE_DIR / f"{league_key}_{season}.json"
        data = [m.to_dict() for m in matches]
        path.write_text(json.dumps(data, indent=2))
        return path

    @staticmethod
    def load_matches(league_key: str, season: str) -> list[dict]:
        """Load previously scraped match data."""
        path = SOFASCORE_DIR / f"{league_key}_{season}.json"
        if not path.exists():
            return []
        return json.loads(path.read_text())
