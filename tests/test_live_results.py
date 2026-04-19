"""Tests for The Odds API /scores integration."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from football_betting.evaluation import live_results
from football_betting.evaluation.grader import GradedBet
from football_betting.scraping.odds_api import OddsApiClient, ScoreResult


# ───────────────────────── Client parsing ─────────────────────────


SAMPLE_SCORES_JSON: list[dict] = [
    {
        "id": "abc123",
        "sport_key": "soccer_epl",
        "commence_time": "2026-04-18T14:00:00Z",
        "completed": True,
        "home_team": "Tottenham Hotspur",
        "away_team": "Brighton and Hove Albion",
        "scores": [
            {"name": "Tottenham Hotspur", "score": "1"},
            {"name": "Brighton and Hove Albion", "score": "2"},
        ],
        "last_update": "2026-04-18T15:55:00Z",
    },
    {
        "id": "def456",
        "sport_key": "soccer_epl",
        "commence_time": "2026-04-19T14:00:00Z",
        "completed": False,
        "home_team": "Chelsea",
        "away_team": "Manchester United",
        "scores": None,
        "last_update": None,
    },
]


def test_fetch_scores_parses_odds_api_payload() -> None:
    client = OddsApiClient()
    with patch.object(OddsApiClient, "_get", return_value=SAMPLE_SCORES_JSON):
        results = client.fetch_scores("PL", days_from=1)

    assert len(results) == 2
    finished = next(r for r in results if r.completed)
    assert finished.home_team == "Tottenham"  # normalised against CSV convention
    assert finished.away_team == "Brighton"
    assert finished.home_goals == 1
    assert finished.away_goals == 2
    assert finished.ftr == "A"
    assert finished.date == date(2026, 4, 18)

    pending = next(r for r in results if not r.completed)
    assert pending.home_goals is None
    assert pending.ftr is None


# ───────────────────────── Poll & persist ─────────────────────────


def test_poll_and_store_skips_non_completed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(live_results, "LIVE_SCORES_FILE", tmp_path / "live_scores.jsonl")

    class FakeClient:
        def fetch_scores(self, league_key: str, days_from: int = 3):  # noqa: ARG002
            return [
                ScoreResult(
                    league="PL",
                    date=date(2026, 4, 18),
                    kickoff_utc=None,  # type: ignore[arg-type]
                    home_team="Tottenham",
                    away_team="Brighton",
                    home_goals=1,
                    away_goals=2,
                    completed=True,
                    last_update=None,
                ),
                ScoreResult(
                    league="PL",
                    date=date(2026, 4, 19),
                    kickoff_utc=None,  # type: ignore[arg-type]
                    home_team="Chelsea",
                    away_team="Man United",
                    home_goals=None,
                    away_goals=None,
                    completed=False,
                    last_update=None,
                ),
            ]

    added = live_results.poll_and_store_scores(["E0"], client=FakeClient())
    assert added == 1

    # Idempotent: re-running adds nothing
    again = live_results.poll_and_store_scores(["E0"], client=FakeClient())
    assert again == 0

    rows = [
        json.loads(line)
        for line in (tmp_path / "live_scores.jsonl").read_text().splitlines()
    ]
    assert len(rows) == 1
    assert rows[0]["league_code"] == "E0"
    assert rows[0]["ftr"] == "A"
    assert rows[0]["fthg"] == 1
    assert rows[0]["ftag"] == 2


def test_load_live_results_for_code_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file = tmp_path / "live_scores.jsonl"
    file.write_text(
        json.dumps(
            {
                "league_code": "D1",
                "date": "2026-04-18",
                "home_norm": "ein frankfurt",
                "away_norm": "rb leipzig",
                "ftr": "H",
                "fthg": 3,
                "ftag": 1,
                "source": "odds_api",
                "fetched_at": "2026-04-18T16:00:00Z",
            }
        )
        + "\n"
    )
    monkeypatch.setattr(live_results, "LIVE_SCORES_FILE", file)

    out = live_results.load_live_results_for_code("D1")
    key = (date(2026, 4, 18), "ein frankfurt", "rb leipzig")
    assert out[key] == ("H", 3, 1)
    assert live_results.load_live_results_for_code("E0") == {}


# ───────────────────────── Pending discovery ─────────────────────────


def test_pending_league_codes_reads_graded_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graded_file = tmp_path / "graded_bets.jsonl"
    rows = [
        GradedBet(
            date="2026-04-18",
            league="PL",
            league_name="Premier League",
            home_team="Tottenham",
            away_team="Brighton",
            outcome="A",
            bet_label="Brighton",
            odds=2.19,
            stake=33.26,
            ft_result=None,
            ft_score=None,
            status="pending",
            pnl=0.0,
        ),
        GradedBet(
            date="2026-04-12",
            league="BL",
            league_name="Bundesliga",
            home_team="Bayern",
            away_team="Dortmund",
            outcome="H",
            bet_label="Bayern",
            odds=1.80,
            stake=20.0,
            ft_result="H",
            ft_score="2-1",
            status="won",
            pnl=16.0,
        ),
    ]
    with graded_file.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r.__dict__) + "\n")

    monkeypatch.setattr("football_betting.evaluation.grader.GRADED_FILE", graded_file)
    monkeypatch.setattr(live_results, "GRADED_FILE", graded_file)

    codes = live_results.pending_league_codes()
    # PL's CSV code is E0 — see LEAGUES config
    assert codes == {"E0"}


# ───────────────────────── Grader merge ─────────────────────────


def test_grader_merges_live_scores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from football_betting.evaluation import grader

    file = tmp_path / "live_scores.jsonl"
    file.write_text(
        json.dumps(
            {
                "league_code": "E0",
                "date": "2026-04-18",
                "home_norm": "tottenham",
                "away_norm": "brighton",
                "ftr": "A",
                "fthg": 1,
                "ftag": 2,
                "source": "odds_api",
                "fetched_at": "2026-04-18T16:00:00Z",
            }
        )
        + "\n"
    )
    monkeypatch.setattr(live_results, "LIVE_SCORES_FILE", file)
    # Ensure CSVs don't mask the live row
    monkeypatch.setattr(grader, "RAW_DIR", tmp_path / "empty_raw")
    (tmp_path / "empty_raw").mkdir()

    results = grader._load_results_for_league("E0")
    assert results[(date(2026, 4, 18), "tottenham", "brighton")] == ("A", 1, 2)
