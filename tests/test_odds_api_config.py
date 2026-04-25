from __future__ import annotations

import pytest

from football_betting.config import OddsApiConfig, live_score_source, snapshot_fixture_source


@pytest.fixture(autouse=True)
def _clear_odds_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    monkeypatch.delenv("ODDS_API_FALLBACK_KEYS", raising=False)
    monkeypatch.delenv("THEODDS_HISTORICAL_API_KEY", raising=False)
    monkeypatch.delenv("ODDS_API_DISABLED", raising=False)
    monkeypatch.delenv("SNAPSHOT_FIXTURE_SOURCE", raising=False)
    monkeypatch.delenv("FIXTURE_SOURCE", raising=False)
    monkeypatch.delenv("LIVE_SCORE_SOURCE", raising=False)
    monkeypatch.delenv("SCORE_SOURCE", raising=False)


def test_api_keys_use_historical_key_as_implicit_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ODDS_API_KEY", "primary")
    monkeypatch.setenv("THEODDS_HISTORICAL_API_KEY", "historical")

    keys = OddsApiConfig().api_keys

    assert keys[:2] == ["primary", "historical"]
    assert keys.count("historical") == 1


def test_api_keys_keep_explicit_fallback_order_and_dedupe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ODDS_API_KEY", "primary")
    monkeypatch.setenv("ODDS_API_FALLBACK_KEYS", "fallback-a,historical,fallback-b")
    monkeypatch.setenv("THEODDS_HISTORICAL_API_KEY", "historical")

    assert OddsApiConfig().api_keys == [
        "primary",
        "fallback-a",
        "historical",
        "fallback-b",
    ]


def test_odds_api_disabled_routes_automatic_sources_to_football_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ODDS_API_DISABLED", "1")

    assert snapshot_fixture_source() == "football_data"
    assert live_score_source() == "football_data"


def test_explicit_source_overrides_odds_api_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ODDS_API_DISABLED", "1")
    monkeypatch.setenv("SNAPSHOT_FIXTURE_SOURCE", "odds_api")
    monkeypatch.setenv("LIVE_SCORE_SOURCE", "odds_api")

    assert snapshot_fixture_source() == "odds_api"
    assert live_score_source() == "odds_api"


def test_sofascore_can_be_selected_for_fixture_snapshots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SNAPSHOT_FIXTURE_SOURCE", "sofascore")

    assert snapshot_fixture_source() == "sofascore"
