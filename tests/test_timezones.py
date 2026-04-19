"""Tests for DST-aware kickoff handling."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from football_betting.data.loader import _extract_kickoff
from football_betting.utils.timezones import (
    LEAGUE_TIMEZONES,
    isoformat_utc,
    league_tz_name,
    local_to_utc,
    utc_to_local,
)


def _row(date_str: str, time_str: str) -> pd.Series:
    return pd.Series({"Date": date_str, "Time": time_str})


class TestLeagueTimezoneMap:
    def test_known_leagues(self) -> None:
        assert LEAGUE_TIMEZONES["BL"] == "Europe/Berlin"
        assert LEAGUE_TIMEZONES["PL"] == "Europe/London"
        assert LEAGUE_TIMEZONES["SA"] == "Europe/Rome"
        assert LEAGUE_TIMEZONES["LL"] == "Europe/Madrid"

    def test_unknown_league_defaults_to_utc(self) -> None:
        assert league_tz_name("XX") == "UTC"


class TestLocalToUtc:
    def test_winter_time_berlin_is_utc_plus_one(self) -> None:
        # 2025-02-15 15:30 local Berlin → CET = UTC+1 → 14:30 UTC
        dt = local_to_utc(datetime(2025, 2, 15, 15, 30), "BL")
        assert dt == datetime(2025, 2, 15, 14, 30, tzinfo=timezone.utc)

    def test_summer_time_berlin_is_utc_plus_two(self) -> None:
        # 2025-06-15 15:30 local Berlin → CEST = UTC+2 → 13:30 UTC
        dt = local_to_utc(datetime(2025, 6, 15, 15, 30), "BL")
        assert dt == datetime(2025, 6, 15, 13, 30, tzinfo=timezone.utc)

    def test_winter_time_london_equals_utc(self) -> None:
        dt = local_to_utc(datetime(2025, 1, 15, 15, 0), "PL")
        assert dt == datetime(2025, 1, 15, 15, 0, tzinfo=timezone.utc)

    def test_summer_time_london_is_utc_plus_one(self) -> None:
        dt = local_to_utc(datetime(2025, 7, 15, 15, 0), "PL")
        assert dt == datetime(2025, 7, 15, 14, 0, tzinfo=timezone.utc)

    def test_dst_end_ambiguous_hour_uses_fold_zero(self) -> None:
        # On 2025-10-26 Europe/Berlin falls back 03:00 → 02:00. 02:30 exists
        # twice. fold=0 resolves to the earlier (CEST, UTC+2) occurrence.
        dt = local_to_utc(datetime(2025, 10, 26, 2, 30), "BL")
        assert dt == datetime(2025, 10, 26, 0, 30, tzinfo=timezone.utc)

    def test_aware_input_passes_through(self) -> None:
        aware = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        assert local_to_utc(aware, "BL") == aware


class TestUtcToLocal:
    def test_roundtrip(self) -> None:
        original = datetime(2025, 6, 15, 15, 30)
        utc_dt = local_to_utc(original, "BL")
        back = utc_to_local(utc_dt, "BL").replace(tzinfo=None)
        assert back == original


class TestIsoformatUtc:
    def test_z_suffix(self) -> None:
        dt = datetime(2025, 6, 15, 13, 30, tzinfo=timezone.utc)
        assert isoformat_utc(dt) == "2025-06-15T13:30:00Z"

    def test_naive_assumed_utc(self) -> None:
        dt = datetime(2025, 6, 15, 13, 30)
        assert isoformat_utc(dt).endswith("Z")


class TestExtractKickoff:
    def test_bundesliga_summer(self) -> None:
        result = _extract_kickoff(_row("15/06/2025", "15:30"), "BL")
        assert result == datetime(2025, 6, 15, 13, 30, tzinfo=timezone.utc)

    def test_bundesliga_winter(self) -> None:
        result = _extract_kickoff(_row("15/02/2025", "15:30"), "BL")
        assert result == datetime(2025, 2, 15, 14, 30, tzinfo=timezone.utc)

    def test_premier_league_summer(self) -> None:
        result = _extract_kickoff(_row("15/08/2025", "15:00"), "PL")
        assert result == datetime(2025, 8, 15, 14, 0, tzinfo=timezone.utc)

    def test_missing_time_returns_none(self) -> None:
        row = pd.Series({"Date": "15/06/2025", "Time": pd.NA})
        assert _extract_kickoff(row, "BL") is None

    def test_bad_time_returns_none(self) -> None:
        assert _extract_kickoff(_row("15/06/2025", "not-a-time"), "BL") is None

    @pytest.mark.parametrize(
        "date_fmt",
        ["15/06/2025", "15/06/25", "2025-06-15"],
    )
    def test_various_date_formats(self, date_fmt: str) -> None:
        result = _extract_kickoff(_row(date_fmt, "15:30"), "BL")
        assert result == datetime(2025, 6, 15, 13, 30, tzinfo=timezone.utc)
