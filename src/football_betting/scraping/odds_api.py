"""
The Odds API client — fetches scheduled fixtures together with
consensus bookmaker odds. One endpoint = one call per league.

Docs: https://the-odds-api.com/liveapi/guides/v4/
Auth: API key via env var ODDS_API_KEY.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import requests

from football_betting.config import LEAGUES, ODDS_API_CFG, OddsApiConfig
from football_betting.scraping.team_names import normalize


class OddsApiError(RuntimeError):
    """Raised on missing key, HTTP failure, or unexpected payload shape."""


_LEAGUE_TIMEZONES: dict[str, str] = {
    "PL": "Europe/London",
    "CH": "Europe/London",
    "BL": "Europe/Berlin",
    "SA": "Europe/Rome",
    "LL": "Europe/Madrid",
}


@dataclass(slots=True)
class FixtureOdds:
    """Normalised fixture + consensus odds, ready for the pipeline."""

    league: str
    date: date
    kickoff_local: str  # "HH:MM" in league-local timezone
    home_team: str
    away_team: str
    odds_home: float
    odds_draw: float
    odds_away: float
    n_bookmakers: int

    def to_fixture_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "league": self.league,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "kickoff_time": self.kickoff_local,
            "odds": {
                "home": round(self.odds_home, 3),
                "draw": round(self.odds_draw, 3),
                "away": round(self.odds_away, 3),
            },
        }


@dataclass(slots=True)
class OddsApiClient:
    cfg: OddsApiConfig = ODDS_API_CFG

    def _require_key(self) -> str:
        key = self.cfg.api_key
        if not key:
            raise OddsApiError(
                "ODDS_API_KEY env var is not set. Get a free key at "
                "https://the-odds-api.com/ and export ODDS_API_KEY=<key>."
            )
        return key

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.cfg.base_url}{path}"
        merged = {"apiKey": self._require_key(), **params}
        try:
            r = requests.get(url, params=merged, timeout=self.cfg.timeout_seconds)
        except requests.RequestException as e:
            raise OddsApiError(f"HTTP error for {url}: {e}") from e
        if r.status_code == 401:
            raise OddsApiError("Odds API rejected the key (HTTP 401).")
        if r.status_code == 429:
            raise OddsApiError("Odds API quota exhausted (HTTP 429).")
        if r.status_code != 200:
            raise OddsApiError(f"Odds API HTTP {r.status_code}: {r.text[:200]}")
        return r.json()

    # ───────────────────────── High-level API ─────────────────────────

    def fetch_league(self, league_key: str) -> list[FixtureOdds]:
        """Upcoming fixtures + consensus h2h odds for one league."""
        league_key = league_key.upper()
        sport = self.cfg.sport_keys.get(league_key)
        if sport is None:
            raise OddsApiError(f"No Odds-API sport_key configured for league {league_key}")

        payload = self._get(
            f"/sports/{sport}/odds",
            {
                "regions": self.cfg.regions,
                "markets": self.cfg.markets,
                "oddsFormat": self.cfg.odds_format,
                "dateFormat": self.cfg.date_format,
            },
        )
        if not isinstance(payload, list):
            raise OddsApiError(f"Unexpected Odds API payload for {league_key}: {payload!r:200}")

        tz_name = _LEAGUE_TIMEZONES.get(league_key, "UTC")
        local_tz = ZoneInfo(tz_name)
        now_utc = datetime.now(timezone.utc)

        out: list[FixtureOdds] = []
        for event in payload:
            fx = self._parse_event(event, league_key, local_tz, now_utc=now_utc)
            if fx is not None:
                out.append(fx)
        return out

    def fetch_for_date(
        self,
        league_key: str,
        target_date: date,
    ) -> list[FixtureOdds]:
        """Only fixtures whose *local* kickoff date matches target_date."""
        return [f for f in self.fetch_league(league_key) if f.date == target_date]

    def fetch_all_leagues_for_date(
        self,
        target_date: date,
        leagues: list[str] | None = None,
    ) -> list[FixtureOdds]:
        keys = leagues or list(self.cfg.sport_keys)
        out: list[FixtureOdds] = []
        for key in keys:
            if key not in LEAGUES:
                continue
            out.extend(self.fetch_for_date(key, target_date))
        return out

    # ───────────────────────── Parsing ─────────────────────────

    @staticmethod
    def _parse_event(
        event: dict[str, Any],
        league_key: str,
        local_tz: ZoneInfo,
        now_utc: datetime | None = None,
    ) -> FixtureOdds | None:
        try:
            raw_home = event["home_team"]
            raw_away = event["away_team"]
            commence = event["commence_time"]
            bookmakers = event.get("bookmakers") or []
        except KeyError:
            return None

        home = normalize(league_key, raw_home)
        away = normalize(league_key, raw_away)

        # Odds API ISO comes with trailing Z; fromisoformat needs +00:00
        kickoff_utc = datetime.fromisoformat(commence.replace("Z", "+00:00"))
        if kickoff_utc.tzinfo is None:
            kickoff_utc = kickoff_utc.replace(tzinfo=timezone.utc)

        # Drop already-commenced matches — their odds are live-in-play and
        # will contain impossible values (home at 1.00 after a 5-0 lead, etc.).
        if now_utc is not None and kickoff_utc <= now_utc:
            return None

        kickoff_local = kickoff_utc.astimezone(local_tz)

        odds = _consensus_h2h(bookmakers, raw_home, raw_away)
        if odds is None:
            return None
        oh, od, oa, n_books = odds

        # Sanity: pre-match h2h never has any price at 1.0x.
        if min(oh, od, oa) < 1.05:
            return None

        return FixtureOdds(
            league=league_key,
            date=kickoff_local.date(),
            kickoff_local=kickoff_local.strftime("%H:%M"),
            home_team=home,
            away_team=away,
            odds_home=oh,
            odds_draw=od,
            odds_away=oa,
            n_bookmakers=n_books,
        )


def _consensus_h2h(
    bookmakers: list[dict[str, Any]],
    raw_home: str,
    raw_away: str,
) -> tuple[float, float, float, int] | None:
    """Median h2h odds across all bookmakers (robust to outliers)."""
    home_prices: list[float] = []
    draw_prices: list[float] = []
    away_prices: list[float] = []

    for book in bookmakers:
        for market in book.get("markets", []):
            if market.get("key") != "h2h":
                continue
            outcomes = {o.get("name"): o.get("price") for o in market.get("outcomes", [])}
            h = outcomes.get(raw_home)
            a = outcomes.get(raw_away)
            d = outcomes.get("Draw")
            if h is None or a is None or d is None:
                continue
            try:
                home_prices.append(float(h))
                draw_prices.append(float(d))
                away_prices.append(float(a))
            except (TypeError, ValueError):
                continue

    if not home_prices:
        return None
    return (
        statistics.median(home_prices),
        statistics.median(draw_prices),
        statistics.median(away_prices),
        len(home_prices),
    )
