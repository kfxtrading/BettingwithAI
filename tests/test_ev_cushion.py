"""Tests for the positive-EV cushion guard added to find_value_bets."""
from __future__ import annotations

from datetime import date

from football_betting.betting.value import find_value_bets
from football_betting.config import BettingConfig
from football_betting.data.models import Fixture, MatchOdds, Prediction


def _make_prediction(
    prob_home: float, prob_draw: float, prob_away: float,
    odds_home: float, odds_draw: float, odds_away: float,
) -> Prediction:
    fx = Fixture(
        home_team="A",
        away_team="B",
        league="BL",
        date=date(2025, 1, 1),
        odds=MatchOdds(home=odds_home, draw=odds_draw, away=odds_away),
    )
    return Prediction(
        fixture=fx,
        model_name="test",
        prob_home=prob_home,
        prob_draw=prob_draw,
        prob_away=prob_away,
        expected_home_goals=1.5,
        expected_away_goals=1.2,
    )


def test_min_ev_pct_filters_thin_value_bets() -> None:
    # Model prob 40 %, odds 2.60 → raw EV = 0.40*2.60 - 1 = 0.04 (4 %).
    # Edge vs margin-free market (~0.385) ≈ 0.015 — below default min_edge,
    # so we lower min_edge to let the bet through, then assert the EV
    # cushion kicks in.
    pred = _make_prediction(
        prob_home=0.40, prob_draw=0.30, prob_away=0.30,
        odds_home=2.60, odds_draw=3.40, odds_away=3.40,
    )
    permissive = BettingConfig(min_edge=0.0, min_ev_pct=0.0)
    tight = BettingConfig(min_edge=0.0, min_ev_pct=0.05)  # demand ≥5 % EV

    bets_permissive = find_value_bets(pred, bankroll=1000.0, cfg=permissive)
    bets_tight = find_value_bets(pred, bankroll=1000.0, cfg=tight)

    assert any(b.outcome == "H" for b in bets_permissive)
    # Home bet has only 4 % EV → must be filtered under the 5 % cushion.
    assert not any(b.outcome == "H" for b in bets_tight)


def test_min_ev_pct_keeps_strong_positive_ev() -> None:
    # Model prob 50 %, odds 2.60 → raw EV = 0.30 (30 %). Must survive even a
    # strict 10 % cushion.
    pred = _make_prediction(
        prob_home=0.50, prob_draw=0.25, prob_away=0.25,
        odds_home=2.60, odds_draw=4.0, odds_away=4.0,
    )
    tight = BettingConfig(min_edge=0.0, min_ev_pct=0.10)
    bets = find_value_bets(pred, bankroll=1000.0, cfg=tight)
    assert any(b.outcome == "H" for b in bets)


def test_default_config_unchanged() -> None:
    # Guarantee the default BettingConfig has a 0 cushion so legacy call
    # sites retain their previous selection universe.
    cfg = BettingConfig()
    assert cfg.min_ev_pct == 0.0
