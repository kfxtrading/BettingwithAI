"""
Weather feature extraction (v0.4 — Phase 1+2: Familie A only).

Familie A — Match-Day Weather: temperature, WBGT, precipitation, wind,
humidity, pressure, cloud cover, extreme-conditions flag at the home
stadium around kickoff.

Familie B (Weather Shock vs. team climate baseline) and Familie C
(Simons-Signal Paris morning weather) are deliberately unimplemented in
this phase — config flags exist but `_features_*` methods are stubs.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from rich.console import Console

from football_betting.config import DATA_DIR, WEATHER_CFG, WeatherConfig
from football_betting.scraping.weather import (
    OpenMeteoClient,
    WeatherObservation,
)

console = Console()

STADIUMS_PATH = DATA_DIR / "stadiums.json"

FAMILIE_A_KEYS: tuple[str, ...] = (
    "weather_temp_c",
    "weather_wbgt",
    "weather_precip_mm",
    "weather_wind_kmh",
    "weather_wind_gust_kmh",
    "weather_humidity_pct",
    "weather_pressure_hpa",
    "weather_cloud_cover_pct",
    "weather_is_extreme",
)


def _empty_familie_a() -> dict[str, float]:
    """All Familie-A keys with NaN — keeps feature schema stable across matches."""
    return {k: math.nan for k in FAMILIE_A_KEYS}


@dataclass(slots=True)
class WeatherTracker:
    """Looks up stadium weather around kickoff and emits feature dict."""

    cfg: WeatherConfig = field(default_factory=lambda: WEATHER_CFG)
    client: OpenMeteoClient = field(default_factory=OpenMeteoClient)
    stadiums: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.stadiums and STADIUMS_PATH.exists():
            try:
                self.stadiums = json.loads(STADIUMS_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                console.log(f"[yellow]WeatherTracker: failed to load stadiums.json ({e})[/yellow]")
                self.stadiums = {}

    # ───────────────────────── Public API ─────────────────────────

    def features_for_match(
        self,
        home_team: str,
        away_team: str,
        match_date: date,
        kickoff_dt: datetime | None = None,
    ) -> dict[str, float]:
        """Return weather feature dict.

        Always emits all Familie-A keys (NaN when stadium / observation
        unavailable) so the downstream feature schema stays stable.
        """
        if not self.cfg.enabled or not self.cfg.use_match_day_weather:
            return {}

        coords = self._stadium_coords(home_team)
        if coords is None:
            return _empty_familie_a()

        kickoff = self._resolve_kickoff(match_date, kickoff_dt)
        observation = self._observation_at_kickoff(coords[0], coords[1], match_date, kickoff)
        if observation is None:
            return _empty_familie_a()

        # Familie B/C: deliberately unimplemented in Phase 1+2.
        # See Erweiterungen/weather-feature-konzept.md sections 3.B/3.C.
        return _familie_a_features(observation)

    # ───────────────────────── Internals ─────────────────────────

    def _stadium_coords(self, team: str) -> tuple[float, float] | None:
        entry = self.stadiums.get(team)
        if not entry:
            return None
        try:
            return float(entry["lat"]), float(entry["lon"])
        except (KeyError, TypeError, ValueError):
            return None

    def _resolve_kickoff(self, match_date: date, kickoff_dt: datetime | None) -> datetime:
        if kickoff_dt is not None:
            if kickoff_dt.tzinfo is None:
                return kickoff_dt.replace(tzinfo=timezone.utc)
            return kickoff_dt.astimezone(timezone.utc)
        return datetime(
            match_date.year, match_date.month, match_date.day,
            self.cfg.default_kickoff_hour_utc, 0, tzinfo=timezone.utc,
        )

    def _observation_at_kickoff(
        self,
        lat: float,
        lon: float,
        match_date: date,
        kickoff: datetime,
    ) -> WeatherObservation | None:
        """Fetch hourly data for the kickoff day, average ±window/2 hours."""
        today_utc = datetime.now(tz=timezone.utc).date()
        horizon = today_utc + timedelta(days=self.cfg.forecast_horizon_days)

        if match_date > horizon:
            return None  # too far in the future for any source

        if match_date >= today_utc - timedelta(days=5):
            # Forecast covers recent past + future
            obs_list = self.client.fetch_forecast(lat, lon)
        else:
            # Archive — query a 1-day window for safety
            obs_list = self.client.fetch_historical(
                lat, lon, match_date, match_date + timedelta(days=1)
            )

        if not obs_list:
            return None

        half_window = timedelta(hours=self.cfg.kickoff_window_hours / 2)
        window_obs = [
            o for o in obs_list
            if kickoff - half_window <= _ensure_utc(o.timestamp) <= kickoff + half_window
        ]
        if not window_obs:
            # Fall back to nearest hour
            nearest = min(obs_list, key=lambda o: abs((_ensure_utc(o.timestamp) - kickoff).total_seconds()))
            return nearest

        return _average_observations(window_obs)


def _ensure_utc(ts: datetime) -> datetime:
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def _average_observations(obs_list: list[WeatherObservation]) -> WeatherObservation:
    n = len(obs_list)
    base = obs_list[len(obs_list) // 2]  # use middle obs for timestamp/coords anchor
    return WeatherObservation(
        timestamp=base.timestamp,
        latitude=base.latitude,
        longitude=base.longitude,
        temp_c=sum(o.temp_c for o in obs_list) / n,
        precip_mm=sum(o.precip_mm for o in obs_list),  # sum, not mean (window total)
        wind_kmh=sum(o.wind_kmh for o in obs_list) / n,
        wind_gust_kmh=max(o.wind_gust_kmh for o in obs_list),  # peak gust
        humidity_pct=sum(o.humidity_pct for o in obs_list) / n,
        pressure_hpa=sum(o.pressure_hpa for o in obs_list) / n,
        cloud_cover_pct=sum(o.cloud_cover_pct for o in obs_list) / n,
    )


def _familie_a_features(obs: WeatherObservation) -> dict[str, float]:
    return {
        "weather_temp_c": obs.temp_c,
        "weather_wbgt": obs.wbgt,
        "weather_precip_mm": obs.precip_mm,
        "weather_wind_kmh": obs.wind_kmh,
        "weather_wind_gust_kmh": obs.wind_gust_kmh,
        "weather_humidity_pct": obs.humidity_pct,
        "weather_pressure_hpa": obs.pressure_hpa,
        "weather_cloud_cover_pct": obs.cloud_cover_pct,
        "weather_is_extreme": float(obs.is_extreme),
    }
