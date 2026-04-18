"""
Kelly Criterion for optimal stake sizing.

Reference: Kelly (1956), "A New Interpretation of Information Rate".

For a bet with decimal odds `o` and true win probability `p`:
    f* = (p * o - 1) / (o - 1)

Fractional Kelly (e.g. 1/4 Kelly) reduces variance at cost of growth rate,
and is strongly recommended in practice where `p` is estimated with error.
"""
from __future__ import annotations

from football_betting.config import BETTING_CFG, BettingConfig


def kelly_fraction(prob: float, odds: float) -> float:
    """
    Full Kelly fraction of bankroll to bet.

    Returns 0 if the bet has no positive edge.
    """
    if not (0.0 < prob < 1.0):
        raise ValueError(f"Probability must be in (0,1), got {prob}")
    if odds <= 1.0:
        raise ValueError(f"Odds must be > 1.0, got {odds}")

    edge = prob * odds - 1.0
    if edge <= 0.0:
        return 0.0

    b = odds - 1.0
    f_star = edge / b
    return max(0.0, f_star)


def kelly_stake(
    prob: float,
    odds: float,
    bankroll: float,
    cfg: BettingConfig | None = None,
) -> float:
    """
    Fractional Kelly stake in monetary units.

    Applies:
    * fractional multiplier (default 0.25)
    * hard cap via max_stake_pct (default 5% of bankroll)
    """
    cfg = cfg or BETTING_CFG
    f_full = kelly_fraction(prob, odds)
    f_adjusted = f_full * cfg.kelly_fraction
    f_capped = min(f_adjusted, cfg.max_stake_pct)
    return round(bankroll * f_capped, 2)


def expected_value(prob: float, odds: float, stake: float) -> float:
    """Expected monetary value of a bet (can be negative)."""
    return stake * (prob * odds - 1.0)


def expected_growth_rate(prob: float, odds: float, fraction: float) -> float:
    """
    Expected logarithmic growth rate for a given staking fraction.
    Maximum at Kelly fraction.
    """
    if fraction <= 0 or fraction >= 1:
        return 0.0
    from math import log

    return prob * log(1 + fraction * (odds - 1)) + (1 - prob) * log(1 - fraction)
