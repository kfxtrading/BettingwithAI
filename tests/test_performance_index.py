"""Tests for the public performance-index feature."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from football_betting.tracking import performance_index as pi
from football_betting.tracking.tracker import PredictionRecord, ResultsTracker


def _rec(
    day: str,
    status: str | None,
    outcome: str | None = "H",
    odds: float | None = 2.0,
    stake: float = 10.0,
) -> PredictionRecord:
    return PredictionRecord(
        date=day,
        league="BL",
        home_team="A",
        away_team="B",
        model_name="test",
        prob_home=0.5,
        prob_draw=0.25,
        prob_away=0.25,
        bet_outcome=outcome,
        bet_odds=odds,
        bet_stake=stake,
        bet_edge=0.1,
        actual_outcome="H" if status == "won" else ("A" if status == "lost" else None),
        bet_status=status,
    )


def test_compute_rule_hash_stable() -> None:
    h1 = pi.compute_rule_hash()
    h2 = pi.compute_rule_hash()
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_build_daily_equity_curve_empty_log() -> None:
    curve = pi.build_daily_equity_curve(
        completed=[],
        tracking_start="2026-01-01",
        today=date(2026, 1, 3),
    )
    assert len(curve) == 3
    assert all(p.balance_eur == pi.INITIAL_BALANCE for p in curve)
    assert all(p.n_bets_cumulative == 0 for p in curve)


def test_build_daily_equity_curve_pnl_applied_on_correct_day() -> None:
    completed = [
        _rec("2026-01-02", "won", odds=2.0, stake=100.0),  # +100
        _rec("2026-01-04", "lost", odds=3.0, stake=50.0),  # -50
    ]
    curve = pi.build_daily_equity_curve(
        completed,
        tracking_start="2026-01-01",
        today=date(2026, 1, 5),
    )
    balances = [p.balance_eur for p in curve]
    assert balances[0] == 1000.0
    assert balances[1] == 1100.0
    assert balances[2] == 1100.0  # carry-forward
    assert balances[3] == 1050.0
    assert balances[4] == 1050.0
    assert curve[-1].n_bets_cumulative == 2


def test_public_payload_has_no_euro_fields() -> None:
    completed = [_rec("2026-01-02", "won", odds=2.0, stake=100.0)]
    tracker = ResultsTracker()
    tracker.records = completed
    public, _ = pi.compute_payloads(
        tracker=tracker,
        tracking_start="2026-01-01",
        today=date(2026, 1, 3),
    )
    serialized = json.dumps(public).lower()
    assert "eur" not in serialized
    assert "balance" not in serialized
    assert public["current_index"] == pytest.approx(110.0)
    assert public["all_time_high_index"] == pytest.approx(110.0)
    assert public["n_bets"] == 1
    assert public["hit_rate"] == pytest.approx(1.0)


def test_private_payload_contains_euro_and_recent_bets() -> None:
    completed = [_rec("2026-01-02", "won", odds=2.0, stake=100.0)]
    tracker = ResultsTracker()
    tracker.records = completed
    _, private = pi.compute_payloads(
        tracker=tracker,
        tracking_start="2026-01-01",
        today=date(2026, 1, 3),
    )
    assert private["initial_balance_eur"] == 1000.0
    assert private["current_balance_eur"] == pytest.approx(1100.0)
    assert private["wins"] == 1
    assert private["losses"] == 0
    assert len(private["recent_bets"]) == 1
    assert private["recent_bets"][0]["profit_eur"] == pytest.approx(100.0)


def test_drawdown_detected() -> None:
    completed = [
        _rec("2026-01-02", "won", odds=2.0, stake=100.0),   # +100 → 1100
        _rec("2026-01-03", "lost", odds=2.0, stake=200.0),  # -200 → 900
    ]
    tracker = ResultsTracker()
    tracker.records = completed
    public, _ = pi.compute_payloads(
        tracker=tracker,
        tracking_start="2026-01-01",
        today=date(2026, 1, 3),
    )
    assert public["max_drawdown_pct"] > 0.1
    assert public["current_drawdown_pct"] > 0.1
    assert public["current_index"] == pytest.approx(90.0)


def test_void_bet_does_not_change_balance() -> None:
    completed = [_rec("2026-01-02", "void", odds=2.0, stake=100.0)]
    tracker = ResultsTracker()
    tracker.records = completed
    public, _ = pi.compute_payloads(
        tracker=tracker,
        tracking_start="2026-01-01",
        today=date(2026, 1, 2),
    )
    assert public["current_index"] == pytest.approx(100.0)


def test_write_performance_files(tmp_path: Path) -> None:
    out_public, out_private = pi.write_performance_files(
        tracking_start="2026-01-01",
        today=date(2026, 1, 2),
        output_dir=tmp_path,
    )
    assert out_public.exists()
    assert out_private.exists()
    pub = json.loads(out_public.read_text(encoding="utf-8"))
    priv = json.loads(out_private.read_text(encoding="utf-8"))
    assert pub["rule_hash"] == priv["rule_hash"]
    assert "current_index" in pub
    assert "current_balance_eur" in priv


def test_api_performance_index_endpoint() -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from football_betting.api.app import create_app
    from football_betting.api.cache import cache

    cache.clear()
    client = TestClient(create_app())
    res = client.get("/performance/index")
    assert res.status_code == 200
    body = res.json()
    for field in (
        "updated_at",
        "tracking_started_at",
        "n_bets",
        "current_index",
        "all_time_high_index",
        "max_drawdown_pct",
        "current_drawdown_pct",
        "equity_curve",
        "rule_hash",
        "model_version",
    ):
        assert field in body
    assert isinstance(body["equity_curve"], list)
