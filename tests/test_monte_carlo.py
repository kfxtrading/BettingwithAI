"""Tests for bankroll Monte-Carlo stress-testing."""

from __future__ import annotations

import numpy as np
import pytest

from football_betting.tracking.monte_carlo import (
    MonteCarloResult,
    simulate_bankroll_paths,
)


def _edge_case_dataset(n: int = 100) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    stakes = np.full(n, 10.0)
    odds = np.full(n, 2.0)
    probs = np.full(n, 0.55)  # positive edge
    return stakes, odds, probs


def test_returns_monte_carlo_result_shape() -> None:
    stakes, odds, probs = _edge_case_dataset(50)
    res = simulate_bankroll_paths(
        stakes,
        odds,
        probs,
        initial_bankroll=1000.0,
        n_paths=500,
        seed=0,
    )
    assert isinstance(res, MonteCarloResult)
    assert res.n_paths == 500
    assert res.n_bets == 50
    assert res.initial_bankroll == 1000.0
    d = res.to_dict()
    assert set(d) >= {"final_bankroll_p05", "max_drawdown_p95", "risk_of_ruin", "cagr_mean"}


def test_positive_edge_grows_bankroll_in_expectation() -> None:
    stakes, odds, probs = _edge_case_dataset(200)
    res = simulate_bankroll_paths(stakes, odds, probs, n_paths=2000, seed=1)
    assert res.final_bankroll_mean > 1000.0


def test_negative_edge_erodes_bankroll() -> None:
    stakes = np.full(200, 10.0)
    odds = np.full(200, 2.0)
    probs = np.full(200, 0.40)  # clearly losing
    # Ruin threshold 70% of initial ⇒ many paths will breach this in 200 bets
    res = simulate_bankroll_paths(
        stakes,
        odds,
        probs,
        n_paths=1000,
        seed=2,
        ruin_threshold_fraction=0.7,
    )
    assert res.final_bankroll_mean < 1000.0
    assert res.risk_of_ruin > 0.0


def test_seed_reproducibility() -> None:
    stakes, odds, probs = _edge_case_dataset(50)
    a = simulate_bankroll_paths(stakes, odds, probs, n_paths=500, seed=7)
    b = simulate_bankroll_paths(stakes, odds, probs, n_paths=500, seed=7)
    assert a.to_dict() == b.to_dict()


def test_drawdown_in_unit_interval() -> None:
    stakes, odds, probs = _edge_case_dataset(100)
    res = simulate_bankroll_paths(stakes, odds, probs, n_paths=500, seed=3)
    assert 0.0 <= res.max_drawdown_mean <= 1.0
    assert 0.0 <= res.max_drawdown_p95 <= 1.0
    assert res.max_drawdown_p95 >= res.max_drawdown_mean - 1e-9


def test_invalid_inputs_raise() -> None:
    s = np.array([10.0, 10.0])
    o = np.array([2.0, 2.0])
    p = np.array([0.5, 0.5])
    with pytest.raises(ValueError, match="same shape"):
        simulate_bankroll_paths(s, o, np.array([0.5]))
    with pytest.raises(ValueError, match="odds must be"):
        simulate_bankroll_paths(s, np.array([1.0, 2.0]), p)
    with pytest.raises(ValueError, match="probs"):
        simulate_bankroll_paths(s, o, np.array([1.2, 0.5]))
    with pytest.raises(ValueError, match="n_paths"):
        simulate_bankroll_paths(s, o, p, n_paths=0)
    with pytest.raises(ValueError, match="at least one bet"):
        simulate_bankroll_paths(np.array([]), np.array([]), np.array([]))
