"""Tests for Kelly staking and metrics."""
from __future__ import annotations

from math import exp

import pytest

from football_betting.betting.kelly import (
    expected_growth_rate,
    expected_value,
    kelly_fraction,
    kelly_stake,
)
from football_betting.betting.margin import remove_margin
from football_betting.tracking.metrics import (
    brier_score,
    log_loss_3way,
    ranked_probability_score,
)


class TestKelly:
    def test_no_edge_zero_fraction(self) -> None:
        # Fair bet: true_prob * odds = 1
        assert kelly_fraction(0.5, 2.0) == pytest.approx(0.0)

    def test_positive_edge_positive_fraction(self) -> None:
        # 60% chance at 2.0 odds → clear +EV
        f = kelly_fraction(0.6, 2.0)
        assert f > 0
        # Classic Kelly formula: f = (bp - q) / b = (1*0.6 - 0.4)/1 = 0.2
        assert f == pytest.approx(0.2)

    def test_negative_edge_zero_fraction(self) -> None:
        assert kelly_fraction(0.3, 2.0) == 0.0

    def test_kelly_stake_respects_max_cap(self) -> None:
        from football_betting.config import BettingConfig

        cfg = BettingConfig(kelly_fraction=1.0, max_stake_pct=0.05)
        # 90% chance at 2.0 → full Kelly = 0.8
        stake = kelly_stake(0.9, 2.0, bankroll=1000, cfg=cfg)
        # Should be capped at 5% = 50
        assert stake == 50

    def test_fractional_kelly(self) -> None:
        from football_betting.config import BettingConfig

        cfg = BettingConfig(kelly_fraction=0.25, max_stake_pct=1.0)  # no cap
        stake = kelly_stake(0.6, 2.0, bankroll=1000, cfg=cfg)
        # f_full = 0.2, quarter = 0.05, stake = 50
        assert stake == 50.0

    def test_ev(self) -> None:
        # Fair bet
        assert expected_value(0.5, 2.0, 100) == 0.0
        # +EV
        assert expected_value(0.6, 2.0, 100) == pytest.approx(20)
        # -EV
        assert expected_value(0.4, 2.0, 100) == pytest.approx(-20)


class TestMargin:
    def test_remove_margin_sums_to_one(self) -> None:
        ph, pd, pa = remove_margin(2.0, 3.5, 4.0)
        assert ph + pd + pa == pytest.approx(1.0)

    def test_remove_margin_no_overround(self) -> None:
        # Perfect 3-way fair odds: 3.0 / 3.0 / 3.0
        ph, pd, pa = remove_margin(3.0, 3.0, 3.0)
        assert ph == pytest.approx(1 / 3)
        assert pd == pytest.approx(1 / 3)
        assert pa == pytest.approx(1 / 3)

    def test_invalid_odds_raises(self) -> None:
        with pytest.raises(ValueError):
            remove_margin(1.0, 3.0, 3.0)

    def test_power_devig_sums_to_one(self) -> None:
        ph, pd, pa = remove_margin(1.30, 5.0, 12.0, method="power")
        assert ph + pd + pa == pytest.approx(1.0, abs=1e-7)

    def test_shin_devig_sums_to_one(self) -> None:
        ph, pd, pa = remove_margin(1.30, 5.0, 12.0, method="shin")
        assert ph + pd + pa == pytest.approx(1.0, abs=1e-7)

    def test_multiplicative_method_explicit(self) -> None:
        ph, pd, pa = remove_margin(2.0, 3.5, 4.0, method="multiplicative")
        assert ph + pd + pa == pytest.approx(1.0)
        # Proportional: home share = 0.5 / (0.5+0.2857+0.25)
        raw = 0.5 / (0.5 + 1 / 3.5 + 0.25)
        assert ph == pytest.approx(raw)

    def test_power_reduces_favorite_longshot_bias(self) -> None:
        # Heavy favorite (1.30) vs longshot (15.0) plus draw
        # Power method should assign LESS probability to the longshot than
        # the multiplicative (proportional) method.
        # Ensure genuine overround (Σ 1/odds > 1): 1/1.30+1/5+1/10 = 1.069
        mult = remove_margin(1.30, 5.0, 10.0, method="multiplicative")
        powr = remove_margin(1.30, 5.0, 10.0, method="power")
        assert powr[2] < mult[2]
        # And MORE to the favorite
        assert powr[0] > mult[0]

    def test_power_converges_for_balanced_book(self) -> None:
        # 3.0/3.0/3.0 has zero overround: k=1, exact 1/3 split
        ph, pd, pa = remove_margin(3.0, 3.0, 3.0, method="power")
        assert ph == pytest.approx(1 / 3)
        assert pd == pytest.approx(1 / 3)
        assert pa == pytest.approx(1 / 3)

    def test_devig_method_switch_via_config(self) -> None:
        from football_betting.config import BettingConfig

        cfg_mult = BettingConfig(devig_method="multiplicative")
        cfg_pow = BettingConfig(devig_method="power")
        assert cfg_mult.devig_method == "multiplicative"
        assert cfg_pow.devig_method == "power"

    def test_unknown_method_raises(self) -> None:
        with pytest.raises(ValueError):
            remove_margin(2.0, 3.5, 4.0, method="bogus")  # type: ignore[arg-type]


class TestMetrics:
    def test_rps_perfect_prediction(self) -> None:
        # Predicted H with 100% confidence, H happened
        assert ranked_probability_score((1.0, 0.0, 0.0), "H") == 0.0

    def test_rps_worst_prediction(self) -> None:
        # Predicted A with 100%, H happened
        # RPS = 0.5 * ((0-1)² + (0-1)²) = 1.0
        assert ranked_probability_score((0.0, 0.0, 1.0), "H") == pytest.approx(1.0)

    def test_rps_uniform(self) -> None:
        # Uniform prediction ≈ 0.222
        rps = ranked_probability_score((1/3, 1/3, 1/3), "H")
        assert 0.2 < rps < 0.3

    def test_brier_perfect(self) -> None:
        assert brier_score((1.0, 0.0, 0.0), "H") == 0.0

    def test_brier_worst(self) -> None:
        assert brier_score((0.0, 0.0, 1.0), "H") == 2.0

    def test_log_loss_perfect_approaches_zero(self) -> None:
        assert log_loss_3way((0.9999, 0.00005, 0.00005), "H") < 0.01

    def test_log_loss_bad_is_large(self) -> None:
        assert log_loss_3way((0.0001, 0.0001, 0.9998), "H") > 5.0
