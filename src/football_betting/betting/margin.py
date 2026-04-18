"""Remove bookmaker overround from decimal odds."""
from __future__ import annotations


def remove_margin(
    odds_home: float, odds_draw: float, odds_away: float
) -> tuple[float, float, float]:
    """
    Convert decimal odds to fair (margin-adjusted) probabilities summing to 1.

    Simple proportional method (Shin method & power methods exist but
    overkill for 3-way markets).
    """
    if min(odds_home, odds_draw, odds_away) <= 1.0:
        raise ValueError("All odds must be > 1.0")

    raw = (1 / odds_home, 1 / odds_draw, 1 / odds_away)
    total = sum(raw)
    return tuple(r / total for r in raw)  # type: ignore[return-value]


def bookmaker_margin(odds_home: float, odds_draw: float, odds_away: float) -> float:
    """Bookmaker overround (e.g. 0.05 = 5% margin)."""
    return (1 / odds_home + 1 / odds_draw + 1 / odds_away) - 1.0
