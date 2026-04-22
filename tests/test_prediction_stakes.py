"""Tests for the 1X2 prediction staking allocator."""
from __future__ import annotations

import numpy as np
import pytest

from football_betting.api.schemas import OddsOut, PredictionOut
from football_betting.betting.prediction_stakes import (
    allocate_prediction_stakes,
    conf_stakes,
    diagnostics,
    entropy_stakes,
    flat_stakes,
    hybrid_stakes,
    power_stakes,
)
from football_betting.config import PredictionStakingConfig

# ───────────────────────── Core strategies ─────────────────────────


def test_flat_stakes_equal_split() -> None:
    s = flat_stakes(1000.0, 4)
    assert s.shape == (4,)
    assert np.allclose(s, 250.0)
    assert s.sum() == pytest.approx(1000.0)


def test_flat_stakes_empty() -> None:
    s = flat_stakes(1000.0, 0)
    assert s.shape == (0,)


def test_conf_stakes_proportional() -> None:
    p = np.array([0.5, 0.3, 0.2])
    s = conf_stakes(1000.0, p)
    assert s.sum() == pytest.approx(1000.0)
    assert s[0] == pytest.approx(500.0)
    assert s[1] == pytest.approx(300.0)
    assert s[2] == pytest.approx(200.0)


def test_conf_stakes_zero_sum() -> None:
    s = conf_stakes(1000.0, np.zeros(3))
    assert np.allclose(s, 0.0)


def test_power_stakes_more_concentrated_than_conf() -> None:
    p = np.array([0.65, 0.50, 0.40])
    s_conf = conf_stakes(1000.0, p)
    s_pow = power_stakes(1000.0, p, k=2.0)
    hhi_conf = diagnostics(s_conf)["HHI"]
    hhi_pow = diagnostics(s_pow)["HHI"]
    assert hhi_pow > hhi_conf


def test_hybrid_stakes_dampens_favorites() -> None:
    # Two picks, same p — but one has low odds (1.4, heavy favorite).
    p = np.array([0.60, 0.60])
    o = np.array([1.40, 2.50])
    s = hybrid_stakes(1000.0, p, o, k=2.0, odds_floor=2.0, min_p=0.40)
    # Favorite must get less than the mid-odds pick due to odds damping.
    assert s[0] < s[1]
    assert s.sum() == pytest.approx(1000.0)


def test_hybrid_stakes_min_p_threshold() -> None:
    p = np.array([0.60, 0.35, 0.50])
    o = np.array([2.00, 2.80, 2.20])
    s = hybrid_stakes(1000.0, p, o, k=2.0, odds_floor=2.0, min_p=0.40)
    # Pick below min_p gets stake 0.
    assert s[1] == 0.0
    # Others share the full bankroll.
    assert s.sum() == pytest.approx(1000.0)


def test_hybrid_stakes_all_below_min_p() -> None:
    p = np.array([0.30, 0.35])
    o = np.array([3.0, 2.8])
    s = hybrid_stakes(1000.0, p, o, min_p=0.40)
    assert np.allclose(s, 0.0)


def test_entropy_stakes_sum_equals_x() -> None:
    p_full = np.array([
        [0.60, 0.25, 0.15],  # low entropy → high weight
        [0.40, 0.35, 0.25],  # mid entropy
        [0.36, 0.33, 0.31],  # high entropy → low weight
    ])
    s = entropy_stakes(1000.0, p_full)
    assert s.sum() == pytest.approx(1000.0)
    assert s[0] > s[1] > s[2]


def test_entropy_stakes_bad_shape() -> None:
    with pytest.raises(ValueError):
        entropy_stakes(1000.0, np.array([[0.5, 0.5]]))


# ───────────────────────── Diagnostics ─────────────────────────


def test_diagnostics_flat() -> None:
    d = diagnostics(np.full(10, 100.0))
    assert d["HHI"] == pytest.approx(0.1)
    assert d["N_eff"] == pytest.approx(10.0)
    assert d["max_weight"] == pytest.approx(0.1)
    assert d["sum"] == pytest.approx(1000.0)


def test_diagnostics_all_zero() -> None:
    d = diagnostics(np.zeros(5))
    assert d["HHI"] == 0.0
    assert d["N_eff"] == 0.0


# ───────────────────────── High-level allocator ─────────────────────────


def _make_pred(
    outcome: str = "H",
    prob_home: float = 0.55,
    prob_draw: float = 0.25,
    prob_away: float = 0.20,
    odds_home: float = 1.80,
    odds_draw: float = 3.50,
    odds_away: float = 4.50,
    with_odds: bool = True,
) -> PredictionOut:
    return PredictionOut(
        date="2026-04-22",
        league="BL",
        league_name="Bundesliga",
        home_team="A",
        away_team="B",
        prob_home=prob_home,
        prob_draw=prob_draw,
        prob_away=prob_away,
        odds=OddsOut(home=odds_home, draw=odds_draw, away=odds_away)
        if with_odds
        else None,
        model_name="test",
        most_likely=outcome,  # type: ignore[arg-type]
    )


def test_allocate_empty_list() -> None:
    cfg = PredictionStakingConfig(daily_bankroll=1000.0)
    assert allocate_prediction_stakes([], cfg) == []


def test_allocate_skips_picks_without_odds() -> None:
    preds = [
        _make_pred(outcome="H", prob_home=0.55, odds_home=2.0),
        _make_pred(with_odds=False, outcome="H", prob_home=0.55),
    ]
    cfg = PredictionStakingConfig(daily_bankroll=1000.0, strategy="hybrid")
    stakes = allocate_prediction_stakes(preds, cfg)
    assert len(stakes) == 2
    assert stakes[1] == 0.0
    assert stakes[0] > 0.0


def test_allocate_hybrid_sum_within_bankroll() -> None:
    preds = [
        _make_pred(outcome="H", prob_home=0.65, odds_home=1.55),
        _make_pred(outcome="H", prob_home=0.50, odds_home=2.00),
        _make_pred(outcome="A", prob_away=0.40, odds_away=2.70),
    ]
    cfg = PredictionStakingConfig(daily_bankroll=1000.0, strategy="hybrid")
    stakes = allocate_prediction_stakes(preds, cfg)
    assert len(stakes) == 3
    assert sum(stakes) <= 1000.0 + 1e-6
    assert sum(stakes) == pytest.approx(1000.0, abs=0.5)


def test_allocate_flat_equal_stakes() -> None:
    preds = [
        _make_pred(outcome="H", prob_home=0.65),
        _make_pred(outcome="H", prob_home=0.50),
        _make_pred(outcome="A", prob_away=0.45),
    ]
    cfg = PredictionStakingConfig(daily_bankroll=900.0, strategy="flat")
    stakes = allocate_prediction_stakes(preds, cfg)
    assert all(s == pytest.approx(300.0) for s in stakes)


def test_allocate_respects_min_p_and_keeps_pick() -> None:
    """Picks under min_p get stake=0 but stay in the output (index stable)."""
    preds = [
        _make_pred(outcome="H", prob_home=0.60, odds_home=2.00),
        _make_pred(outcome="H", prob_home=0.35, odds_home=2.80),  # below min_p
        _make_pred(outcome="A", prob_away=0.50, odds_away=2.20),
    ]
    cfg = PredictionStakingConfig(
        daily_bankroll=1000.0, strategy="hybrid", min_p=0.40
    )
    stakes = allocate_prediction_stakes(preds, cfg)
    assert len(stakes) == 3
    assert stakes[1] == 0.0
    assert stakes[0] > 0.0
    assert stakes[2] > 0.0


def test_allocate_unknown_strategy_raises() -> None:
    preds = [_make_pred()]
    cfg = PredictionStakingConfig(daily_bankroll=1000.0)
    # bypass dataclass validation via a hand-crafted config-like object.
    cfg = PredictionStakingConfig.__new__(PredictionStakingConfig)  # type: ignore[misc]
    object.__setattr__(cfg, "strategy", "nope")
    object.__setattr__(cfg, "daily_bankroll", 1000.0)
    object.__setattr__(cfg, "power_k", 2.0)
    object.__setattr__(cfg, "odds_floor", 2.0)
    object.__setattr__(cfg, "min_p", 0.40)
    with pytest.raises(ValueError, match="Unknown staking strategy"):
        allocate_prediction_stakes(preds, cfg)


def test_allocate_draw_pick_uses_draw_odds() -> None:
    preds = [
        _make_pred(
            outcome="D",
            prob_home=0.30, prob_draw=0.45, prob_away=0.25,
            odds_home=3.5, odds_draw=2.10, odds_away=3.8,
        ),
    ]
    cfg = PredictionStakingConfig(daily_bankroll=500.0, strategy="hybrid")
    stakes = allocate_prediction_stakes(preds, cfg)
    # Single pick (p=0.45 > min_p, draw-odds 2.10 > odds_floor 2.0) → full bankroll.
    assert stakes[0] == pytest.approx(500.0)
