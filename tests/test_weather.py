"""Tests for v0.4 weather features (Open-Meteo client + WeatherTracker)."""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from football_betting.config import WeatherConfig
from football_betting.features.weather import (
    FAMILIE_A_KEYS,
    WeatherTracker,
    _average_observations,
    _empty_familie_a,
)
from football_betting.scraping.cache import ResponseCache
from football_betting.scraping.weather import (
    GeocodeResult,
    OpenMeteoClient,
    WeatherObservation,
    _safe_float,
)


# ───────────────────────── Fixtures ─────────────────────────


def _make_observation(
    ts: datetime,
    temp_c: float = 18.0,
    precip_mm: float = 0.0,
    wind_kmh: float = 5.0,
) -> WeatherObservation:
    return WeatherObservation(
        timestamp=ts,
        latitude=48.0,
        longitude=11.0,
        temp_c=temp_c,
        precip_mm=precip_mm,
        wind_kmh=wind_kmh,
        wind_gust_kmh=wind_kmh + 5,
        humidity_pct=60.0,
        pressure_hpa=1013.0,
        cloud_cover_pct=30.0,
    )


@pytest.fixture()
def stub_client(tmp_path: Path) -> OpenMeteoClient:
    cache = ResponseCache(db_path=tmp_path / "wx.sqlite", default_ttl_seconds=3600)
    cfg = WeatherConfig(request_delay_seconds=0.001)
    return OpenMeteoClient(cfg=cfg, cache=cache)


# ───────────────────────── WeatherObservation ─────────────────────────


class TestWeatherObservation:
    def test_wbgt_in_realistic_range(self) -> None:
        obs = _make_observation(datetime(2024, 7, 1, 15), temp_c=30.0)
        # WBGT for hot+humid should be in (15, 35) — sanity bounds
        assert 15.0 < obs.wbgt < 35.0

    def test_is_extreme_high_temp(self) -> None:
        assert _make_observation(datetime(2024, 7, 1), temp_c=32.0).is_extreme

    def test_is_extreme_freeze(self) -> None:
        assert _make_observation(datetime(2024, 1, 1), temp_c=-2.0).is_extreme

    def test_is_extreme_storm(self) -> None:
        assert _make_observation(datetime(2024, 4, 1), wind_kmh=45.0).is_extreme

    def test_is_extreme_rain(self) -> None:
        assert _make_observation(datetime(2024, 4, 1), precip_mm=10.0).is_extreme

    def test_not_extreme_baseline(self) -> None:
        assert not _make_observation(datetime(2024, 4, 1)).is_extreme


# ───────────────────────── OpenMeteoClient ─────────────────────────


class TestOpenMeteoClient:
    @patch("football_betting.scraping.weather.requests.get")
    def test_fetch_historical_parses_hourly(
        self, mock_get: MagicMock, stub_client: OpenMeteoClient
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "hourly": {
                    "time": ["2024-04-15T18:00", "2024-04-15T19:00"],
                    "temperature_2m": [16.5, 17.2],
                    "precipitation": [0.0, 0.1],
                    "wind_speed_10m": [10.0, 12.5],
                    "wind_gusts_10m": [15.0, 18.0],
                    "relative_humidity_2m": [55.0, 58.0],
                    "surface_pressure": [1015.0, 1014.5],
                    "cloud_cover": [40.0, 45.0],
                }
            }
        )
        mock_response.json.return_value = json.loads(mock_response.text)
        mock_get.return_value = mock_response

        obs = stub_client.fetch_historical(48.0, 11.0, date(2024, 4, 15), date(2024, 4, 15))
        assert len(obs) == 2
        assert obs[0].temp_c == 16.5
        assert obs[1].wind_kmh == 12.5
        assert obs[0].timestamp.tzinfo is not None  # UTC-aware

    @patch("football_betting.scraping.weather.requests.get")
    def test_fetch_uses_cache_on_repeat(
        self, mock_get: MagicMock, stub_client: OpenMeteoClient
    ) -> None:
        body = {
            "hourly": {
                "time": ["2024-04-15T18:00"],
                "temperature_2m": [10.0],
                "precipitation": [0.0],
                "wind_speed_10m": [5.0],
                "wind_gusts_10m": [7.0],
                "relative_humidity_2m": [70.0],
                "surface_pressure": [1010.0],
                "cloud_cover": [80.0],
            }
        }
        mock_response = MagicMock(status_code=200, text=json.dumps(body))
        mock_response.json.return_value = body
        mock_get.return_value = mock_response

        stub_client.fetch_historical(48.0, 11.0, date(2024, 4, 15), date(2024, 4, 15))
        stub_client.fetch_historical(48.0, 11.0, date(2024, 4, 15), date(2024, 4, 15))
        assert mock_get.call_count == 1  # second call hit cache

    @patch("football_betting.scraping.weather.requests.get")
    def test_geocode_returns_first_result(
        self, mock_get: MagicMock, stub_client: OpenMeteoClient
    ) -> None:
        body = {
            "results": [
                {"latitude": 48.137, "longitude": 11.575, "name": "Munich",
                 "country": "Germany", "admin1": "Bavaria"}
            ]
        }
        mock_response = MagicMock(status_code=200, text=json.dumps(body))
        mock_response.json.return_value = body
        mock_get.return_value = mock_response

        result = stub_client.geocode("Bayern Munich")
        assert isinstance(result, GeocodeResult)
        assert result.lat == pytest.approx(48.137)
        assert result.country == "Germany"

    @patch("football_betting.scraping.weather.requests.get")
    def test_geocode_returns_none_on_empty(
        self, mock_get: MagicMock, stub_client: OpenMeteoClient
    ) -> None:
        body = {"results": []}
        mock_response = MagicMock(status_code=200, text=json.dumps(body))
        mock_response.json.return_value = body
        mock_get.return_value = mock_response

        assert stub_client.geocode("ImaginaryFC") is None

    def test_safe_float_handles_missing(self) -> None:
        assert _safe_float(None, 0) == 0.0
        assert _safe_float([1.0, None, 3.0], 1, default=99.0) == 99.0
        assert _safe_float([1.0, 2.0], 5, default=7.0) == 7.0


# ───────────────────────── WeatherTracker ─────────────────────────


class TestWeatherTracker:
    def test_returns_empty_when_disabled(self, tmp_path: Path) -> None:
        cfg = WeatherConfig(enabled=False)
        client = MagicMock(spec=OpenMeteoClient)
        tracker = WeatherTracker(cfg=cfg, client=client, stadiums={})
        feats = tracker.features_for_match("Home", "Away", date(2024, 4, 15))
        assert feats == {}

    def test_returns_nan_keys_when_no_stadium(self) -> None:
        cfg = WeatherConfig()
        client = MagicMock(spec=OpenMeteoClient)
        tracker = WeatherTracker(cfg=cfg, client=client, stadiums={})

        feats = tracker.features_for_match("UnknownTeam", "Away", date(2024, 4, 15))
        assert set(feats.keys()) == set(FAMILIE_A_KEYS)
        assert all(math.isnan(v) for v in feats.values())

    def test_emits_familie_a_for_known_stadium(self) -> None:
        cfg = WeatherConfig()
        client = MagicMock(spec=OpenMeteoClient)
        kickoff = datetime(2024, 4, 15, 19, 0, tzinfo=timezone.utc)
        client.fetch_forecast.return_value = [
            _make_observation(kickoff - timedelta(hours=1), temp_c=20.0),
            _make_observation(kickoff, temp_c=21.0),
            _make_observation(kickoff + timedelta(hours=1), temp_c=19.0),
        ]
        client.fetch_historical.return_value = client.fetch_forecast.return_value

        tracker = WeatherTracker(
            cfg=cfg,
            client=client,
            stadiums={"Bayern Munich": {"lat": 48.137, "lon": 11.575}},
        )
        feats = tracker.features_for_match(
            "Bayern Munich", "Dortmund", date(2024, 4, 15), kickoff,
        )
        assert set(feats.keys()) == set(FAMILIE_A_KEYS)
        assert feats["weather_temp_c"] == pytest.approx(20.0, abs=0.01)
        assert feats["weather_is_extreme"] == 0.0

    def test_naive_kickoff_treated_as_utc(self) -> None:
        cfg = WeatherConfig()
        client = MagicMock(spec=OpenMeteoClient)
        kickoff_aware = datetime(2024, 4, 15, 19, 0, tzinfo=timezone.utc)
        client.fetch_forecast.return_value = [_make_observation(kickoff_aware, temp_c=15.0)]
        client.fetch_historical.return_value = client.fetch_forecast.return_value

        tracker = WeatherTracker(
            cfg=cfg, client=client,
            stadiums={"Home": {"lat": 0.0, "lon": 0.0}},
        )
        feats = tracker.features_for_match(
            "Home", "Away", date(2024, 4, 15),
            kickoff_dt=datetime(2024, 4, 15, 19, 0),  # naive
        )
        assert feats["weather_temp_c"] == pytest.approx(15.0)

    def test_loads_stadiums_json_from_disk(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from football_betting.features import weather as wx_module

        path = tmp_path / "stadiums.json"
        path.write_text(json.dumps({"FC X": {"lat": 1.0, "lon": 2.0}}))
        monkeypatch.setattr(wx_module, "STADIUMS_PATH", path)

        tracker = WeatherTracker()
        assert tracker.stadiums.get("FC X") == {"lat": 1.0, "lon": 2.0}


# ───────────────────────── helpers ─────────────────────────


class TestHelpers:
    def test_empty_familie_a_has_all_keys(self) -> None:
        feats = _empty_familie_a()
        assert set(feats.keys()) == set(FAMILIE_A_KEYS)
        assert all(math.isnan(v) for v in feats.values())

    def test_average_observations_aggregates_correctly(self) -> None:
        ts = datetime(2024, 4, 15, 19, 0, tzinfo=timezone.utc)
        obs = [
            _make_observation(ts - timedelta(hours=1), temp_c=10.0, precip_mm=1.0, wind_kmh=10.0),
            _make_observation(ts, temp_c=12.0, precip_mm=2.0, wind_kmh=15.0),
            _make_observation(ts + timedelta(hours=1), temp_c=14.0, precip_mm=0.5, wind_kmh=20.0),
        ]
        avg = _average_observations(obs)
        assert avg.temp_c == pytest.approx(12.0)
        assert avg.precip_mm == pytest.approx(3.5)  # sum, not mean
        assert avg.wind_gust_kmh == pytest.approx(25.0)  # peak (max + 5 from helper)


# ───────────────────────── Integration with FeatureBuilder ─────────────────────────


class TestFeatureBuilderIntegration:
    def test_build_features_passes_kickoff_to_tracker(self) -> None:
        from football_betting.features.builder import FeatureBuilder

        kickoff = datetime(2024, 4, 15, 19, 0, tzinfo=timezone.utc)
        cfg = WeatherConfig()
        client = MagicMock(spec=OpenMeteoClient)
        client.fetch_forecast.return_value = [_make_observation(kickoff, temp_c=22.5)]
        client.fetch_historical.return_value = client.fetch_forecast.return_value

        wx = WeatherTracker(
            cfg=cfg, client=client,
            stadiums={"Bayern Munich": {"lat": 48.137, "lon": 11.575}},
        )
        fb = FeatureBuilder(weather_tracker=wx)
        feats = fb.build_features(
            home_team="Bayern Munich",
            away_team="Dortmund",
            league_key="BL",
            match_date=date(2024, 4, 15),
            kickoff_datetime_utc=kickoff,
        )
        assert "weather_temp_c" in feats
        assert feats["weather_temp_c"] == pytest.approx(22.5)

    def test_build_features_no_tracker_no_weather_keys(self) -> None:
        from football_betting.features.builder import FeatureBuilder

        fb = FeatureBuilder()  # no weather_tracker
        feats = fb.build_features(
            home_team="Bayern Munich",
            away_team="Dortmund",
            league_key="BL",
            match_date=date(2024, 4, 15),
        )
        assert not any(k.startswith("weather_") for k in feats)
