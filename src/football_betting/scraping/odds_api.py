"""
The Odds API client — fetches scheduled fixtures together with
consensus bookmaker odds. One endpoint = one call per league.

Docs: https://the-odds-api.com/liveapi/guides/v4/
Auth: API key via env var ODDS_API_KEY.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests

from football_betting.config import LEAGUES, ODDS_API_CFG, OddsApiConfig
from football_betting.scraping.team_names import normalize
from football_betting.utils.timezones import (
    LEAGUE_TIMEZONES as _LEAGUE_TIMEZONES,
)
from football_betting.utils.timezones import (
    isoformat_utc,
    league_tz_name,
)


class OddsApiError(RuntimeError):
    """Raised on missing key, HTTP failure, or unexpected payload shape."""


class OddsApiQuotaError(OddsApiError):
    """Raised when the API key is valid but the monthly request quota is exhausted.

    The Odds API signals this via HTTP 401 (with ``"quota"``/``"usage"``
    in the body) or HTTP 429. Consumers can catch this separately to
    trigger backoff / pause-polling logic.
    """


@dataclass(slots=True)
class ScoreResult:
    """Completed / in-progress match result from The Odds API /scores."""

    league: str
    date: date
    kickoff_utc: datetime
    home_team: str  # normalised
    away_team: str  # normalised
    home_goals: int | None
    away_goals: int | None
    completed: bool
    last_update: str | None

    @property
    def ftr(self) -> str | None:
        if self.home_goals is None or self.away_goals is None:
            return None
        if self.home_goals > self.away_goals:
            return "H"
        if self.home_goals < self.away_goals:
            return "A"
        return "D"


@dataclass(slots=True)
class FixtureOdds:
    """Normalised fixture + consensus odds, ready for the pipeline."""

    league: str
    date: date
    kickoff_local: str  # "HH:MM" in league-local timezone (DST-aware via ZoneInfo)
    home_team: str
    away_team: str
    odds_home: float
    odds_draw: float
    odds_away: float
    n_bookmakers: int
    kickoff_utc: datetime | None = None  # UTC-aware kickoff for client-side TZ conversion

    def to_fixture_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "date": self.date.isoformat(),
            "league": self.league,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "kickoff_time": self.kickoff_local,
            "league_timezone": league_tz_name(self.league),
            "odds": {
                "home": round(self.odds_home, 3),
                "draw": round(self.odds_draw, 3),
                "away": round(self.odds_away, 3),
            },
        }
        if self.kickoff_utc is not None:
            payload["kickoff_utc"] = isoformat_utc(self.kickoff_utc)
        return payload


# Process-lifetime set of API keys that have already returned a quota
# error. We skip them on subsequent requests instead of burning a round
# trip just to learn they are still exhausted. Cleared on process restart.
_EXHAUSTED_KEYS: set[str] = set()


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}…{key[-4:]}"


@dataclass(slots=True)
class OddsApiClient:
    cfg: OddsApiConfig = ODDS_API_CFG

    def _candidate_keys(self) -> list[str]:
        keys = [k for k in self.cfg.api_keys if k not in _EXHAUSTED_KEYS]
        if not keys:
            raise OddsApiQuotaError(
                "No usable Odds-API key available. Set ODDS_API_KEY, "
                "ODDS_API_FALLBACK_KEYS, and/or THEODDS_HISTORICAL_API_KEY — "
                "every known key is currently marked quota-exhausted for this "
                "process."
            )
        return keys

    def _try_request(
        self, url: str, params: dict[str, Any], api_key: str
    ) -> Any:
        merged = {"apiKey": api_key, **params}
        try:
            r = requests.get(url, params=merged, timeout=self.cfg.timeout_seconds)
        except requests.RequestException as e:
            raise OddsApiError(f"HTTP error for {url}: {e}") from e
        if r.status_code == 401:
            body = (r.text or "").strip()[:240]
            lower = body.lower()
            if "quota" in lower or "usage" in lower or "exceeded" in lower:
                raise OddsApiQuotaError(
                    f"Odds API HTTP 401 (quota exhausted) — body: {body or 'no body'}"
                )
            raise OddsApiError(
                f"Odds API HTTP 401 (invalid key) — body: {body or 'no body'}"
            )
        if r.status_code == 429:
            body = (r.text or "").strip()[:240]
            raise OddsApiQuotaError(
                f"Odds API HTTP 429 (quota / rate limit) — body: {body or 'no body'}"
            )
        if r.status_code != 200:
            raise OddsApiError(f"Odds API HTTP {r.status_code}: {r.text[:240]}")
        return r.json()

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        """Execute the request, transparently rotating to a fallback key on
        quota exhaustion. Only re-raises ``OddsApiQuotaError`` once *every*
        configured key has been exhausted.
        """
        url = f"{self.cfg.base_url}{path}"
        keys = self._candidate_keys()
        last_quota_exc: OddsApiQuotaError | None = None
        for idx, key in enumerate(keys):
            try:
                return self._try_request(url, params, key)
            except OddsApiQuotaError as exc:
                _EXHAUSTED_KEYS.add(key)
                last_quota_exc = exc
                remaining = len(keys) - idx - 1
                if remaining > 0:
                    next_key = keys[idx + 1]
                    import logging as _logging
                    _logging.getLogger(__name__).warning(
                        "[odds-api] key %s quota-exhausted — rotating to "
                        "fallback %s (%d candidate(s) remaining).",
                        _mask_key(key), _mask_key(next_key), remaining,
                    )
                    continue
                # All keys exhausted — propagate.
                raise
        # Defensive — loop always either returns or raises.
        if last_quota_exc is not None:
            raise last_quota_exc
        raise OddsApiError("Odds API request failed: no candidate keys executed")

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
        now_utc = datetime.now(UTC)

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

    # ───────────────────────── Scores ─────────────────────────

    def fetch_scores(
        self,
        league_key: str,
        days_from: int = 1,
    ) -> list[ScoreResult]:
        """Live + completed matches up to `days_from` days old (max 3)."""
        league_key = league_key.upper()
        sport = self.cfg.sport_keys.get(league_key)
        if sport is None:
            raise OddsApiError(f"No Odds-API sport_key configured for league {league_key}")
        days_from = max(1, min(days_from, 3))

        payload = self._get(
            f"/sports/{sport}/scores",
            {"daysFrom": days_from, "dateFormat": self.cfg.date_format},
        )
        if not isinstance(payload, list):
            raise OddsApiError(f"Unexpected scores payload for {league_key}: {payload!r:200}")

        tz_name = _LEAGUE_TIMEZONES.get(league_key, "UTC")
        local_tz = ZoneInfo(tz_name)

        out: list[ScoreResult] = []
        for event in payload:
            res = self._parse_score(event, league_key, local_tz)
            if res is not None:
                out.append(res)
        return out

    @staticmethod
    def _parse_score(
        event: dict[str, Any],
        league_key: str,
        local_tz: ZoneInfo,
    ) -> ScoreResult | None:
        try:
            raw_home = event["home_team"]
            raw_away = event["away_team"]
            commence = event["commence_time"]
        except KeyError:
            return None

        kickoff_utc = datetime.fromisoformat(commence.replace("Z", "+00:00"))
        if kickoff_utc.tzinfo is None:
            kickoff_utc = kickoff_utc.replace(tzinfo=UTC)
        match_date = kickoff_utc.astimezone(local_tz).date()

        home = normalize(league_key, raw_home)
        away = normalize(league_key, raw_away)

        hg: int | None = None
        ag: int | None = None
        for s in event.get("scores") or []:
            try:
                val = int(s.get("score"))
            except (TypeError, ValueError):
                continue
            name = s.get("name")
            if name == raw_home:
                hg = val
            elif name == raw_away:
                ag = val

        return ScoreResult(
            league=league_key,
            date=match_date,
            kickoff_utc=kickoff_utc,
            home_team=home,
            away_team=away,
            home_goals=hg,
            away_goals=ag,
            completed=bool(event.get("completed", False)),
            last_update=event.get("last_update"),
        )

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
            kickoff_utc = kickoff_utc.replace(tzinfo=UTC)

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
            kickoff_utc=kickoff_utc,
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
