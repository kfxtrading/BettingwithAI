"""Tests for the live-latency reduction (Stufe 1+2).

Covers:
* mtime-cache in live_results._load_rows()
* settle_live(force_leagues=...) polling without any pending bet
* scheduler._live_display_league_codes() windowing
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from football_betting.evaluation import live_results

# ───────────────────────── mtime-cache ─────────────────────────


def _reset_live_cache() -> None:
    live_results._ROWS_CACHE = None
    live_results._ROWS_CACHE_KEY = None


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    _reset_live_cache()
    yield
    _reset_live_cache()


def test_load_rows_caches_on_mtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file = tmp_path / "live_scores.jsonl"
    file.write_text(
        json.dumps(
            {
                "league_code": "E0",
                "date": "2026-04-18",
                "home_norm": "tottenham",
                "away_norm": "brighton",
                "ftr": "H",
                "fthg": 1,
                "ftag": 0,
                "source": "odds_api",
                "fetched_at": "2026-04-18T16:00:00Z",
                "status": "live",
                "kickoff_utc": "2026-04-18T14:00:00Z",
            }
        )
        + "\n"
    )
    monkeypatch.setattr(live_results, "LIVE_SCORES_FILE", file)

    # First read: parses file.
    with patch.object(live_results, "_parse_rows", wraps=live_results._parse_rows) as spy:
        rows1 = live_results._load_rows()
        assert len(rows1) == 1
        assert spy.call_count == 1

        # Second read without file change: served from cache, no reparse.
        rows2 = live_results._load_rows()
        assert rows2 is rows1
        assert spy.call_count == 1


def test_load_rows_reparses_after_mtime_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    file = tmp_path / "live_scores.jsonl"
    file.write_text(
        json.dumps(
            {
                "league_code": "E0",
                "date": "2026-04-18",
                "home_norm": "a",
                "away_norm": "b",
                "ftr": "H",
                "fthg": 0,
                "ftag": 0,
                "source": "odds_api",
                "fetched_at": "2026-04-18T16:00:00Z",
                "status": "live",
                "kickoff_utc": "2026-04-18T14:00:00Z",
            }
        )
        + "\n"
    )
    monkeypatch.setattr(live_results, "LIVE_SCORES_FILE", file)

    rows1 = live_results._load_rows()
    assert len(rows1) == 1

    # Force a different mtime and append a row.
    future = file.stat().st_mtime + 10
    file.write_text(file.read_text() + file.read_text())  # two lines now
    import os

    os.utime(file, (future, future))

    rows2 = live_results._load_rows()
    assert len(rows2) == 2
    assert rows2 is not rows1


# ───────────────────────── settle_live force ─────────────────────────


def test_settle_live_polls_forced_leagues_without_pending_bets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without pending bets but with force_leagues, /scores must still be polled
    and new rows persisted — but regrade_all() must NOT run."""
    from football_betting.evaluation import pipeline

    monkeypatch.setattr(live_results, "LIVE_SCORES_FILE", tmp_path / "live_scores.jsonl")
    # No graded file → pending_league_codes() returns set()
    monkeypatch.setattr(
        "football_betting.evaluation.grader.GRADED_FILE", tmp_path / "no_graded.jsonl",
    )
    monkeypatch.setattr(live_results, "GRADED_FILE", tmp_path / "no_graded.jsonl")

    regrade_calls = {"n": 0}

    def _fake_regrade() -> list:
        regrade_calls["n"] += 1
        return []

    monkeypatch.setattr(pipeline, "regrade_all", _fake_regrade)

    call_tracker: dict[str, int] = {"calls": 0}

    def _fake_poll(codes, **kwargs):  # noqa: ANN001, ANN003
        call_tracker["calls"] += 1
        call_tracker["codes"] = set(codes)
        return 0  # no new rows — but call happened

    monkeypatch.setattr(live_results, "poll_and_store_scores", _fake_poll)

    added, settled = pipeline.settle_live(force_leagues={"soccer_epl"})

    assert call_tracker["calls"] == 1
    assert call_tracker["codes"] == {"soccer_epl"}
    assert regrade_calls["n"] == 0  # no pending bets → no regrade
    assert added == 0
    assert settled == 0


def test_settle_live_skips_when_no_pending_and_no_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from football_betting.evaluation import pipeline

    monkeypatch.setattr(live_results, "LIVE_SCORES_FILE", tmp_path / "live_scores.jsonl")
    monkeypatch.setattr(
        "football_betting.evaluation.grader.GRADED_FILE", tmp_path / "no_graded.jsonl",
    )
    monkeypatch.setattr(live_results, "GRADED_FILE", tmp_path / "no_graded.jsonl")

    def _never_called(*a, **kw):  # noqa: ANN002, ANN003, ARG001
        raise AssertionError("poll_and_store_scores must not be called")

    monkeypatch.setattr(live_results, "poll_and_store_scores", _never_called)

    added, settled = pipeline.settle_live()
    assert (added, settled) == (0, 0)


# ───────────────────────── scheduler window ─────────────────────────


def test_live_display_league_codes_window() -> None:
    from football_betting.api import scheduler
    from football_betting.api.schemas import PredictionOut, TodayPayload

    now = datetime.now(UTC)

    in_window = PredictionOut(
        date=now.date().isoformat(),
        league="PL",
        league_name="Premier League",
        home_team="Tottenham",
        away_team="Brighton",
        kickoff_utc=(now - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        prob_home=0.4,
        prob_draw=0.3,
        prob_away=0.3,
        model_name="ensemble",
        most_likely="H",
    )
    too_old = PredictionOut(
        date=now.date().isoformat(),
        league="BL",
        league_name="Bundesliga",
        home_team="Bayern",
        away_team="Dortmund",
        kickoff_utc=(now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        prob_home=0.5,
        prob_draw=0.3,
        prob_away=0.2,
        model_name="ensemble",
        most_likely="H",
    )
    too_future = PredictionOut(
        date=now.date().isoformat(),
        league="SA",
        league_name="Serie A",
        home_team="Juventus",
        away_team="Napoli",
        kickoff_utc=(now + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        prob_home=0.4,
        prob_draw=0.3,
        prob_away=0.3,
        model_name="ensemble",
        most_likely="H",
    )

    payload = TodayPayload(
        generated_at=now,
        predictions=[in_window, too_old, too_future],
        value_bets=[],
        data_sources=[],
    )

    with patch.object(scheduler, "load_today", return_value=payload):
        codes = scheduler._live_display_league_codes()

    # PL -> "soccer_epl" (per LEAGUES config). Only the in-window match counts.
    from football_betting.config import LEAGUES

    assert codes == {LEAGUES["PL"].code}


def test_live_display_league_codes_empty_when_no_snapshot() -> None:
    from football_betting.api import scheduler

    with patch.object(scheduler, "load_today", return_value=None):
        assert scheduler._live_display_league_codes() == set()
