"""Tests for the strategy-split bankroll curve and performance summary."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

import football_betting.api.services as services
import football_betting.evaluation.grader as grader_mod


@dataclass
class _FakeGraded:
    date: str
    league: str = "BL"
    league_name: str = "Bundesliga"
    home_team: str = "A"
    away_team: str = "B"
    outcome: str = "H"
    bet_label: str = "A win"
    odds: float = 2.0
    stake: float = 100.0
    ft_result: str | None = "H"
    ft_score: str | None = "1-0"
    status: str = "won"
    pnl: float = 100.0
    kind: str = "value"


@pytest.fixture
def patch_graded(monkeypatch: pytest.MonkeyPatch):
    def _install(rows: list[_FakeGraded]) -> None:
        monkeypatch.setattr(grader_mod, "load_graded", lambda: list(rows))

    # Ensure `_load_tracker()` does not pick up on-disk predictions_log.json
    # during tests — keep it empty so graded rows are the only source.
    from football_betting.tracking.tracker import ResultsTracker

    def _empty_tracker(*_args, **_kwargs):
        t = ResultsTracker()
        t.records = []
        return t

    monkeypatch.setattr(services, "_load_tracker", _empty_tracker)

    # Neutralise the optimised-value-bet baseline + cutoff so the legacy
    # test assertions (which predate the dual-model snapshot) keep working.
    from datetime import date as _date

    monkeypatch.setattr(services, "VALUE_SNAPSHOT_CUTOFF", _date(1970, 1, 1))
    monkeypatch.setattr(
        services,
        "VALUE_SNAPSHOT_BASELINE",
        {
            "n_bets": 0,
            "wins": 0,
            "total_stake": 0.0,
            "total_profit": 0.0,
            "max_drawdown_pct": 0.0,
        },
    )
    return _install


def test_bankroll_curve_empty(patch_graded) -> None:
    patch_graded([])
    curve = services.get_bankroll_curve(initial_bankroll=1000.0)
    assert len(curve) == 1
    p = curve[0]
    assert p.value == 1000.0
    assert p.value_bets == 1000.0
    assert p.predictions == 1000.0


def test_bankroll_curve_splits_by_kind(patch_graded) -> None:
    patch_graded(
        [
            _FakeGraded(
                date="2026-01-02", kind="value", status="won",
                odds=2.0, stake=100.0, pnl=100.0,
            ),
            _FakeGraded(
                date="2026-01-02", kind="prediction", status="lost",
                odds=3.0, stake=50.0, pnl=-50.0, outcome="H", ft_result="A",
            ),
            _FakeGraded(
                date="2026-01-03", kind="value", status="lost",
                odds=2.0, stake=40.0, pnl=-40.0, outcome="H", ft_result="A",
            ),
        ]
    )

    curve = services.get_bankroll_curve(initial_bankroll=1000.0)
    # Anchor + 2 dated points.
    assert len(curve) == 3
    anchor, p1, p2 = curve

    assert anchor.value == 1000.0
    assert anchor.value_bets == 1000.0
    assert anchor.predictions == 1000.0

    # 2026-01-02: value +100, prediction -50, combined +50.
    assert p1.date == "2026-01-02"
    assert p1.value_bets == 1100.0
    assert p1.predictions == 950.0
    assert p1.value == 1050.0

    # 2026-01-03: value -40 → 1060, prediction unchanged 950, combined 1010.
    assert p2.date == "2026-01-03"
    assert p2.value_bets == 1060.0
    assert p2.predictions == 950.0
    assert p2.value == 1010.0

    # Consistency: per-kind deltas sum to combined delta.
    initial = 1000.0
    assert (
        (p2.value_bets - initial) + (p2.predictions - initial)
        == pytest.approx(p2.value - initial)
    )


def test_bankroll_curve_ignores_pending(patch_graded) -> None:
    patch_graded(
        [
            _FakeGraded(
                date="2026-01-02", kind="value", status="pending",
                ft_result=None, ft_score=None, pnl=0.0,
            ),
        ]
    )
    curve = services.get_bankroll_curve(initial_bankroll=1000.0)
    assert len(curve) == 1  # only the synthetic today anchor
    assert curve[0].value == 1000.0


def test_performance_summary_per_strategy(patch_graded) -> None:
    patch_graded(
        [
            _FakeGraded(
                date="2026-01-02", kind="value", status="won",
                odds=2.0, stake=100.0, pnl=100.0,
            ),
            _FakeGraded(
                date="2026-01-03", kind="value", status="lost",
                odds=2.0, stake=100.0, pnl=-100.0, outcome="H", ft_result="A",
            ),
            _FakeGraded(
                date="2026-01-02", kind="prediction", status="won",
                odds=3.0, stake=50.0, pnl=100.0,
            ),
        ]
    )
    summary = services.get_performance_summary()

    assert summary.value_bets is not None
    assert summary.predictions is not None

    vb = summary.value_bets
    assert vb.n_bets == 2
    assert vb.total_stake == 200.0
    assert vb.total_profit == 0.0
    assert vb.hit_rate == 0.5
    assert vb.roi == 0.0

    pr = summary.predictions
    assert pr.n_bets == 1
    assert pr.total_stake == 50.0
    assert pr.total_profit == 100.0
    assert pr.hit_rate == 1.0
    assert pr.roi == 2.0


def test_performance_summary_no_predictions(patch_graded) -> None:
    patch_graded(
        [
            _FakeGraded(
                date="2026-01-02", kind="value", status="won",
                odds=2.0, stake=100.0, pnl=100.0,
            ),
        ]
    )
    summary = services.get_performance_summary()
    assert summary.value_bets is not None
    assert summary.value_bets.n_bets == 1
    assert summary.predictions is None


def test_legacy_rows_without_kind_default_to_value(patch_graded) -> None:
    patch_graded(
        [
            _FakeGraded(
                date="2026-01-02", kind="", status="won",  # empty → value
                odds=2.0, stake=100.0, pnl=100.0,
            ),
        ]
    )
    summary = services.get_performance_summary()
    assert summary.value_bets is not None and summary.value_bets.n_bets == 1
    assert summary.predictions is None
