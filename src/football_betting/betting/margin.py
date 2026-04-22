"""Devigging methods to convert bookmaker decimal odds to fair probabilities.

Three methods supported:

* ``multiplicative`` — proportional normalisation (legacy default, ignores
  Favorite-Longshot Bias).
* ``power``          — exponential method ``Σ π_i^(1/k) = 1`` solved via
  Newton-Raphson. SOTA for asymmetric 3-way markets.
* ``shin``           — Hyun Song Shin (1993) insider-trading model; iterative
  bisection on parameter ``z``. Strong on 3+ way markets.
"""
from __future__ import annotations

from typing import Literal

DevigMethod = Literal["multiplicative", "power", "shin"]


def remove_margin(
    odds_home: float,
    odds_draw: float,
    odds_away: float,
    method: DevigMethod = "power",
) -> tuple[float, float, float]:
    """Convert decimal odds to fair (margin-adjusted) probabilities summing to 1."""
    if min(odds_home, odds_draw, odds_away) <= 1.0:
        raise ValueError("All odds must be > 1.0")

    raw = (1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away)

    if method == "multiplicative":
        total = sum(raw)
        return raw[0] / total, raw[1] / total, raw[2] / total
    if method == "power":
        return _power_devig(raw)
    if method == "shin":
        return _shin_devig(raw)
    raise ValueError(f"Unknown devig method: {method}")


def _power_devig(
    probs: tuple[float, float, float],
    tol: float = 1e-9,
    max_iter: int = 50,
) -> tuple[float, float, float]:
    """Newton-Raphson on ``f(k) = Σ π_i^(1/k) − 1``.

    Starts at ``k = 1.0`` (no correction). For an overround book ``k > 1``
    contracts longshots more than favorites, mirroring the Favorite-Longshot
    Bias asymmetry.
    """
    k = 1.0
    for _ in range(max_iter):
        # f(k) = Σ p^(1/k) − 1
        # f'(k) = -Σ p^(1/k) * ln(p) / k²
        powers = [p ** (1.0 / k) for p in probs]
        f = sum(powers) - 1.0
        if abs(f) < tol:
            break
        # Derivative
        from math import log

        fp = -sum(pw * log(p) for pw, p in zip(powers, probs, strict=True)) / (k * k)
        if fp == 0.0:
            break
        k -= f / fp
        # Guard against negative/zero k
        if k <= 0:
            k = 1e-6
    out = tuple(p ** (1.0 / k) for p in probs)
    s = sum(out)
    return out[0] / s, out[1] / s, out[2] / s  # type: ignore[return-value]


def _shin_devig(
    probs: tuple[float, float, float],
    tol: float = 1e-9,
    max_iter: int = 100,
) -> tuple[float, float, float]:
    """Shin (1993) insider-trading model. Bisection on ``z ∈ [0, 0.4]``.

    Fair probability ``p_i = (sqrt(z² + 4(1-z)*π_i²/Σπ) − z) / (2(1-z))``.
    """
    from math import sqrt

    booksum = sum(probs)
    lo, hi = 0.0, 0.4

    def fair(z: float) -> tuple[float, float, float]:
        out = tuple(
            (sqrt(z * z + 4.0 * (1.0 - z) * (pi * pi) / booksum) - z) / (2.0 * (1.0 - z))
            for pi in probs
        )
        return out  # type: ignore[return-value]

    for _ in range(max_iter):
        z = 0.5 * (lo + hi)
        s = sum(fair(z))
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            lo = z
        else:
            hi = z
    out = fair(z)
    s = sum(out)
    return out[0] / s, out[1] / s, out[2] / s  # type: ignore[return-value]


def bookmaker_margin(odds_home: float, odds_draw: float, odds_away: float) -> float:
    """Bookmaker overround (e.g. 0.05 = 5% margin)."""
    return (1 / odds_home + 1 / odds_draw + 1 / odds_away) - 1.0
