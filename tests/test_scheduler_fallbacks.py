from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from football_betting.api import scheduler
from football_betting.evaluation import live_results, pipeline
from football_betting.scraping.odds_api import OddsApiQuotaError


class FixedDate(date):
    @classmethod
    def today(cls) -> FixedDate:
        return cls(2026, 4, 25)


def _install_refresh_stubs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, list[dict[str, Any]]]:
    recorded: dict[str, list[dict[str, Any]]] = {}

    monkeypatch.setattr(scheduler, "date", FixedDate)
    monkeypatch.setattr(scheduler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(scheduler, "snapshot_fixture_source", lambda: "odds_api")
    monkeypatch.setenv("ODDS_API_KEY", "dummy")

    def _build(fixtures: list[dict[str, Any]], *args: Any, **kwargs: Any) -> Any:
        recorded["fixtures"] = fixtures
        return SimpleNamespace(predictions=[object()], value_bets=[])

    monkeypatch.setattr(scheduler, "build_predictions_for_fixtures", _build)
    monkeypatch.setattr(scheduler, "write_today", lambda snapshot: None)

    from football_betting.api import revalidate

    monkeypatch.setattr(revalidate, "revalidate_snapshot_paths", lambda *a, **kw: None)
    monkeypatch.setattr(pipeline, "capture_today_snapshot", lambda: "dated.json")
    monkeypatch.setattr(pipeline, "regrade_all", lambda: [])
    return recorded


def test_refresh_uses_sofascore_when_odds_quota_exhausted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded = _install_refresh_stubs(tmp_path, monkeypatch)
    fixture = {
        "date": "2026-04-25",
        "league": "PL",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "kickoff_time": "15:00",
    }

    class QuotaClient:
        def fetch_all_leagues_for_date(self, target_date: date) -> list[Any]:
            raise OddsApiQuotaError("quota exhausted")

    monkeypatch.setattr(scheduler, "OddsApiClient", QuotaClient)
    monkeypatch.setattr(
        scheduler,
        "_sofascore_fixture_payload",
        lambda day, leagues=None: [fixture] if day == FixedDate.today() else [],
    )
    monkeypatch.setattr(scheduler, "_football_data_fixture_payload", lambda day, leagues=None: [])

    scheduler._refresh_blocking()

    out = tmp_path / "fixtures_2026-04-25.json"
    assert json.loads(out.read_text(encoding="utf-8")) == [fixture]
    assert recorded["fixtures"] == [fixture]


def test_refresh_uses_football_data_when_sofascore_fallback_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded = _install_refresh_stubs(tmp_path, monkeypatch)
    fixture = {
        "date": "2026-04-25",
        "league": "PL",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "source": "football_data",
    }

    class QuotaClient:
        def fetch_all_leagues_for_date(self, target_date: date) -> list[Any]:
            raise OddsApiQuotaError("quota exhausted")

    monkeypatch.setattr(scheduler, "OddsApiClient", QuotaClient)
    monkeypatch.setattr(scheduler, "_sofascore_fixture_payload", lambda day, leagues=None: [])
    monkeypatch.setattr(
        scheduler,
        "_football_data_fixture_payload",
        lambda day, leagues=None: [fixture] if day == FixedDate.today() else [],
    )

    scheduler._refresh_blocking()

    assert json.loads((tmp_path / "fixtures_2026-04-25.json").read_text("utf-8")) == [
        fixture
    ]
    assert recorded["fixtures"] == [fixture]


def test_prekickoff_capture_skips_non_odds_fixture_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(scheduler, "odds_api_disabled", lambda: False)
    monkeypatch.setattr(scheduler, "snapshot_fixture_source", lambda: "sofascore")

    class NeverClient:
        def __init__(self) -> None:
            raise AssertionError("OddsApiClient must not be created")

    monkeypatch.setattr(scheduler, "OddsApiClient", NeverClient)

    scheduler._capture_prekickoff_blocking()


def test_settle_live_falls_back_to_football_data_on_odds_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ODDS_API_DISABLED", "0")
    monkeypatch.setenv("LIVE_SCORE_SOURCE", "odds_api")
    monkeypatch.setattr(live_results, "pending_league_codes", lambda: set())

    calls: dict[str, Any] = {}

    def _odds_poll(codes: set[str], **kwargs: Any) -> int:
        calls["odds_codes"] = set(codes)
        raise OddsApiQuotaError("quota exhausted")

    def _football_data_poll(codes: set[str], **kwargs: Any) -> int:
        calls["football_data_codes"] = set(codes)
        return 2

    monkeypatch.setattr(live_results, "poll_and_store_scores", _odds_poll)
    monkeypatch.setattr(
        live_results,
        "poll_and_store_scores_football_data",
        _football_data_poll,
    )

    added, settled = pipeline.settle_live(force_leagues={"E0"})

    assert calls == {
        "odds_codes": {"E0"},
        "football_data_codes": {"E0"},
    }
    assert (added, settled) == (2, 0)
