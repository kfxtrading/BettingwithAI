"""Tests for Bayesian fractional Kelly staking."""

from __future__ import annotations

import numpy as np
import pytest

from football_betting.betting.bayesian_kelly import (
    BayesianKellyResult,
    bayesian_kelly_stake,
)
from football_betting.config import BettingConfig

CFG = BettingConfig(kelly_fraction=0.25, max_stake_pct=0.05)


def _samples_around(mean: float, scale: float, n: int = 200, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = rng.normal(mean, scale, n)
    return np.clip(x, 1e-4, 1.0 - 1e-4)


def test_returns_bayesian_kelly_result_with_positive_stake() -> None:
    samples = _samples_around(0.55, 0.02)
    r = bayesian_kelly_stake(samples, odds=2.10, bankroll=1000.0, cfg=CFG)
    assert isinstance(r, BayesianKellyResult)
    assert r.stake > 0.0
    assert 0.0 < r.shrink <= 1.0
    assert 0.54 < r.p_mean < 0.56


def test_higher_variance_reduces_stake() -> None:
    low_var = _samples_around(0.60, 0.01, seed=1)
    high_var = _samples_around(0.60, 0.10, seed=2)
    r_low = bayesian_kelly_stake(low_var, odds=2.0, bankroll=1000.0, cfg=CFG)
    r_high = bayesian_kelly_stake(high_var, odds=2.0, bankroll=1000.0, cfg=CFG)
    assert r_high.stake < r_low.stake
    assert r_high.shrink < r_low.shrink


def test_negative_edge_yields_zero_stake() -> None:
    # p=0.40 with odds 2.0 => edge = 0.40*2 - 1 = -0.20  <=> skip
    samples = _samples_around(0.40, 0.02)
    r = bayesian_kelly_stake(samples, odds=2.0, bankroll=1000.0, cfg=CFG)
    assert r.stake == 0.0
    assert r.fraction_full == 0.0


def test_stake_capped_at_max_stake_pct() -> None:
    # Extreme edge: p=0.95, odds=3.0  => raw Kelly ≈ 0.925
    samples = np.full(100, 0.95)
    r = bayesian_kelly_stake(samples, odds=3.0, bankroll=1000.0, cfg=CFG)
    # cap is 5% of 1000 = 50
    assert r.stake <= 50.0 + 1e-6


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError):
        bayesian_kelly_stake([], 2.0, 1000.0)
    with pytest.raises(ValueError):
        bayesian_kelly_stake([1.5], 2.0, 1000.0)
    with pytest.raises(ValueError):
        bayesian_kelly_stake([0.5], 1.0, 1000.0)
    with pytest.raises(ValueError):
        bayesian_kelly_stake([0.5], 2.0, -1.0)
    with pytest.raises(ValueError):
        bayesian_kelly_stake([0.5], 2.0, 1000.0, lam=-1.0)


def test_lam_zero_equals_plain_fractional_kelly() -> None:
    samples = np.full(50, 0.60)
    r = bayesian_kelly_stake(samples, odds=2.0, bankroll=1000.0, lam=0.0, cfg=CFG)
    # full Kelly = (0.6*2 - 1) / 1 = 0.20; fractional = 0.05; stake = 50
    assert r.stake == pytest.approx(50.0, abs=1e-6)
    assert r.shrink == 1.0
