"""
Open-Meteo weather API client (v0.4 — weather features).

Open-Meteo (https://open-meteo.com/) is free, requires no API key, and
provides ERA5 historical reanalysis back to 1940 plus 14-day forecasts
at ~9 km resolution. License: CC BY 4.0.

Unlike Sofascore (Cloudflare-blocked, needs curl_cffi), Open-Meteo
accepts plain HTTP requests — no impersonation needed.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from rich.console import Console

from football_betting.config import WEATHER_CFG, WEATHER_DIR, WeatherConfig
from football_betting.scraping.cache import ResponseCache
from football_betting.scraping.rate_limiter import TokenBucketLimiter

console = Console()


@dataclass(slots=True)
class WeatherObservation:
    """Hourly weather snapshot at a single location."""

    timestamp: datetime
    latitude: float
    longitude: float
    temp_c: float
    precip_mm: float
    wind_kmh: float
    wind_gust_kmh: float
    humidity_pct: float
    pressure_hpa: float
    cloud_cover_pct: float

    @property
    def wbgt(self) -> float:
        """Wet Bulb Globe Temperature (Stull 2011 approximation, °C)."""
        t = self.temp_c
        rh = max(0.0, min(100.0, self.humidity_pct))
        # Stull's wet-bulb-from-T-and-RH approximation
        tw = (
            t * math.atan(0.151977 * (rh + 8.313659) ** 0.5)
            + math.atan(t + rh)
            - math.atan(rh - 1.676331)
            + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
            - 4.686035
        )
        return 0.7 * tw + 0.3 * t

    @property
    def is_extreme(self) -> bool:
        return (
            self.precip_mm > 5.0
            or self.wind_kmh > 30.0
            or self.temp_c < 0.0
            or self.temp_c > 28.0
        )


@dataclass(slots=True)
class GeocodeResult:
    """Result from Open-Meteo geocoding-API search."""

    lat: float
    lon: float
    name: str
    country: str | None = None
    admin1: str | None = None  # state/region


@dataclass(slots=True)
class OpenMeteoClient:
    """Rate-limited, SQLite-cached client for Open-Meteo APIs."""

    cfg: WeatherConfig = field(default_factory=lambda: WEATHER_CFG)
    cache: ResponseCache = field(
        default_factory=lambda: ResponseCache(
            db_path=WEATHER_DIR / "cache.sqlite",
            default_ttl_seconds=WEATHER_CFG.cache_ttl_days * 86400,
        )
    )
    _limiter: TokenBucketLimiter = field(init=False)

    def __post_init__(self) -> None:
        self._limiter = TokenBucketLimiter.from_delay(
            self.cfg.request_delay_seconds, burst=1
        )

    # ───────────────────────── HTTP layer ─────────────────────────

    def _fetch(self, url: str, params: dict, ttl_seconds: int | None = None) -> dict | None:
        cached = self.cache.get(url, params)
        if cached is not None:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                self.cache.delete(url, params)

        self._limiter.acquire()
        for attempt in range(self.cfg.max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=self.cfg.timeout_seconds)
                if response.status_code == 200:
                    self.cache.set(url, response.text, params=params, ttl_seconds=ttl_seconds)
                    return response.json()
                if response.status_code in (429, 503):
                    wait = self.cfg.retry_backoff_base ** (attempt + 1)
                    console.log(f"[yellow]Open-Meteo {response.status_code}, sleeping {wait}s[/yellow]")
                    time.sleep(wait)
                    continue
                console.log(f"[red]Open-Meteo HTTP {response.status_code} for {url}[/red]")
                return None
            except requests.RequestException as e:
                wait = self.cfg.retry_backoff_base ** (attempt + 1)
                console.log(f"[yellow]Open-Meteo request failed ({e}), retrying in {wait}s[/yellow]")
                time.sleep(wait)
        return None

    # ───────────────────────── High-level API ─────────────────────────

    _HOURLY_VARS = (
        "temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,"
        "relative_humidity_2m,surface_pressure,cloud_cover"
    )

    def fetch_historical(
        self,
        lat: float,
        lon: float,
        start: date,
        end: date,
    ) -> list[WeatherObservation]:
        """ERA5 archive lookup — for matches older than ~5 days."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": self._HOURLY_VARS,
            "timezone": "UTC",
            "wind_speed_unit": "kmh",
        }
        data = self._fetch(
            self.cfg.historical_api,
            params,
            ttl_seconds=self.cfg.cache_ttl_days * 86400,
        )
        return self._parse_hourly(data, lat, lon) if data else []

    def fetch_forecast(
        self,
        lat: float,
        lon: float,
        days: int | None = None,
    ) -> list[WeatherObservation]:
        """Forecast API — for upcoming matches within forecast_horizon_days."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": self._HOURLY_VARS,
            "forecast_days": days or self.cfg.forecast_horizon_days,
            "timezone": "UTC",
            "wind_speed_unit": "kmh",
        }
        # Forecast data changes — short TTL (1 hour)
        data = self._fetch(self.cfg.forecast_api, params, ttl_seconds=3600)
        return self._parse_hourly(data, lat, lon) if data else []

    def geocode(self, query: str, count: int = 1) -> GeocodeResult | None:
        """Look up coordinates by free-text name (city, stadium, etc.)."""
        if not query:
            return None
        params = {"name": query, "count": max(1, count), "language": "en", "format": "json"}
        data = self._fetch(
            self.cfg.geocoding_api,
            params,
            ttl_seconds=365 * 86400,  # geocoding is effectively immutable
        )
        if not data:
            return None
        results = data.get("results") or []
        if not results:
            return None
        top = results[0]
        try:
            return GeocodeResult(
                lat=float(top["latitude"]),
                lon=float(top["longitude"]),
                name=str(top.get("name", query)),
                country=top.get("country"),
                admin1=top.get("admin1"),
            )
        except (KeyError, TypeError, ValueError):
            return None

    # ───────────────────────── Parsing ─────────────────────────

    def _parse_hourly(self, data: dict, lat: float, lon: float) -> list[WeatherObservation]:
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        if not times:
            return []
        observations: list[WeatherObservation] = []
        for i, t in enumerate(times):
            try:
                ts = datetime.fromisoformat(t)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                observations.append(
                    WeatherObservation(
                        timestamp=ts,
                        latitude=lat,
                        longitude=lon,
                        temp_c=_safe_float(hourly.get("temperature_2m"), i, default=0.0),
                        precip_mm=_safe_float(hourly.get("precipitation"), i, default=0.0),
                        wind_kmh=_safe_float(hourly.get("wind_speed_10m"), i, default=0.0),
                        wind_gust_kmh=_safe_float(hourly.get("wind_gusts_10m"), i, default=0.0),
                        humidity_pct=_safe_float(hourly.get("relative_humidity_2m"), i, default=0.0),
                        pressure_hpa=_safe_float(hourly.get("surface_pressure"), i, default=1013.25),
                        cloud_cover_pct=_safe_float(hourly.get("cloud_cover"), i, default=0.0),
                    )
                )
            except (KeyError, IndexError, TypeError, ValueError):
                continue
        return observations


def _safe_float(values: list | None, i: int, default: float = 0.0) -> float:
    """Return values[i] as float, or default if missing/None."""
    if not values or i >= len(values):
        return default
    v = values[i]
    if v is None:
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default
