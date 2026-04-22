"""Bayesian fractional Kelly staking (Phase 5).

Accepts a posterior-sample distribution over the win probability rather
than a single point estimate, and shrinks the resulting stake by the
posterior variance. Intuition: when the model is uncertain about `p`, bet
less. When it is confident, bet closer to the fractional-Kelly allocation.

Formula
-------
Given probability samples :math:`\\{p_i\\}_{i=1}^{M}` (e.g. from MC-Dropout):

    p_mean = mean(p_samples)
    p_var  = var(p_samples)
    f_full = max(0, (p_mean * o - 1) / (o - 1))
    shrink = 1 / (1 + lam * p_var)          # variance-aware shrinkage
    f_eff  = f_full * kelly_fraction * shrink

    stake  = bankroll * min(f_eff, max_stake_pct)

``lam`` (lambda) controls how aggressively variance shrinks the stake.
Default 10 follows Smith/Shaver (2012): a credible interval half-width of
~0.1 halves the stake.

Also provides :func:`mc_dropout_probabilities` — a Torch helper that runs
an MLP predictor in train mode N times to collect posterior draws.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from football_betting.betting.kelly import kelly_fraction
from football_betting.config import BETTING_CFG, BettingConfig


@dataclass(frozen=True, slots=True)
class BayesianKellyResult:
    """Per-bet Bayesian Kelly diagnostics."""

    stake: float
    p_mean: float
    p_var: float
    shrink: float
    fraction_full: float
    fraction_effective: float
    ev: float  # expected monetary value at stake


def bayesian_kelly_stake(
    prob_samples: np.ndarray | list[float],
    odds: float,
    bankroll: float,
    lam: float = 10.0,
    cfg: BettingConfig | None = None,
) -> BayesianKellyResult:
    """Variance-shrunk fractional Kelly stake.

    Parameters
    ----------
    prob_samples
        1-D array of posterior win-probability samples.
    odds
        Decimal odds of the bet (> 1.0).
    bankroll
        Current bankroll in monetary units.
    lam
        Shrinkage coefficient; larger ⇒ more conservative.
    cfg
        :class:`BettingConfig` controlling ``kelly_fraction`` and
        ``max_stake_pct`` caps. Defaults to :data:`BETTING_CFG`.
    """
    cfg = cfg or BETTING_CFG
    arr = np.asarray(prob_samples, dtype=float)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError("prob_samples must be a non-empty 1-D array")
    if np.any(arr < 0.0) or np.any(arr > 1.0):
        raise ValueError("prob_samples must lie in [0, 1]")
    if odds <= 1.0:
        raise ValueError(f"odds must be > 1.0, got {odds}")
    if bankroll < 0.0:
        raise ValueError("bankroll must be non-negative")
    if lam < 0.0:
        raise ValueError("lam must be non-negative")

    p_mean = float(arr.mean())
    p_var = float(arr.var(ddof=1)) if arr.size > 1 else 0.0

    # Guard point-kelly call against boundary probabilities (0 or 1)
    p_clipped = min(max(p_mean, 1e-6), 1.0 - 1e-6)
    f_full = kelly_fraction(p_clipped, odds)

    shrink = 1.0 / (1.0 + lam * p_var)
    f_effective = f_full * cfg.kelly_fraction * shrink
    f_capped = min(f_effective, cfg.max_stake_pct)
    stake = round(max(0.0, bankroll * f_capped), 2)
    ev = stake * (p_mean * odds - 1.0)

    return BayesianKellyResult(
        stake=stake,
        p_mean=p_mean,
        p_var=p_var,
        shrink=shrink,
        fraction_full=f_full,
        fraction_effective=f_effective,
        ev=ev,
    )


def mc_dropout_probabilities(
    model: Any,
    predict_fn: Any,
    n_passes: int = 50,
    seed: int | None = None,
) -> np.ndarray:
    """Run ``predict_fn(model)`` ``n_passes`` times with dropout enabled.

    ``predict_fn(model)`` must return a 1-D array of shape ``(3,)``
    containing the (home, draw, away) posterior draw for one fixture.

    Parameters
    ----------
    model
        A PyTorch ``nn.Module`` whose Dropout layers produce stochasticity.
    predict_fn
        Closure that runs one forward pass and returns the outcome probs.
    n_passes
        Number of posterior draws; 50 is the Gal & Ghahramani (2016)
        default for tabular nets. More passes reduce Monte-Carlo noise at
        linear cost.
    seed
        Optional base seed for reproducibility.
    """
    import torch

    if n_passes < 1:
        raise ValueError("n_passes must be >= 1")

    model.train()  # enable dropout
    rng = torch.Generator()
    if seed is not None:
        rng.manual_seed(int(seed))

    draws: list[np.ndarray] = []
    with torch.no_grad():
        for i in range(n_passes):
            if seed is not None:
                torch.manual_seed(int(seed) + i)
            probs = np.asarray(predict_fn(model), dtype=float).reshape(-1)
            if probs.shape[0] != 3:
                raise ValueError(f"predict_fn must return shape (3,), got {probs.shape}")
            draws.append(probs)
    model.eval()
    return np.asarray(draws, dtype=float)  # (n_passes, 3)


__all__ = [
    "BayesianKellyResult",
    "bayesian_kelly_stake",
    "mc_dropout_probabilities",
]
