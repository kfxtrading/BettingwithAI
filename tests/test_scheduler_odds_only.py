from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from football_betting.api import scheduler
from football_betting.evaluation import live_results, pipeline
from football_betting.scraping.odds_api import OddsApiQuotaError


class FixedDate(date):
    @classmethod
    def today(cls) -> FixedDate:
        return cls(2026, 4, 25)


def test_refresh_stops_on_odds_quota_without_fixture_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(scheduler, "date", FixedDate)
    monkeypatch.setattr(scheduler, "DATA_DIR", tmp_path)
    monkeypatch.setattr(scheduler, "snapshot_fixture_source", lambda: "odds_api")
    monkeypatch.setenv("ODDS_API_KEY", "dummy")

    class QuotaClient:
        def fetch_all_leagues_for_date(self, target_date: date) -> list[Any]:
            raise OddsApiQuotaError("quota exhausted")

    def _never_build(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("snapshot build must not run after Odds quota failure")

    monkeypatch.setattr(scheduler, "OddsApiClient", QuotaClient)
    monkeypatch.setattr(scheduler, "build_predictions_for_fixtures", _never_build)

    scheduler._refresh_blocking()

    assert not list(tmp_path.glob("fixtures_*.json"))


def test_settle_live_propagates_odds_quota_without_football_data_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(live_results, "pending_league_codes", lambda: set())

    def _odds_poll(codes: set[str], **kwargs: Any) -> int:
        raise OddsApiQuotaError("quota exhausted")

    monkeypatch.setattr(live_results, "poll_and_store_scores", _odds_poll)

    with pytest.raises(OddsApiQuotaError):
        pipeline.settle_live(force_leagues={"E0"})
