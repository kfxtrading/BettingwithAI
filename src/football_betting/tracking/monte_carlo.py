"""Monte-Carlo bankroll stress-testing (Phase 5).

Given a history of independent bets (stake, odds, win-probability), simulate
``n_paths`` alternative outcome sequences to estimate:

    * P95 max drawdown          — tail downside
    * Risk of ruin (P(bankroll ≤ ruin_threshold))
    * CAGR across the simulated paths (annualised geometric growth)
    * Full bankroll quantiles

The bets are treated as independent Bernoulli trials with success
probability :math:`p_i` and payoff ``stake_i * (odds_i - 1)`` on win,
``-stake_i`` on loss. This matches the walk-forward backtester's
per-bet accounting, and is the standard stress-test harness for Kelly
staking systems (Thorp 1997; Ziemba 2008).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    """Aggregate diagnostics across simulated bankroll paths."""

    n_paths: int
    n_bets: int
    initial_bankroll: float
    final_bankroll_mean: float
    final_bankroll_median: float
    final_bankroll_p05: float
    final_bankroll_p95: float
    max_drawdown_mean: float
    max_drawdown_p95: float  # P95 worst drawdown (fraction, 0–1)
    risk_of_ruin: float  # fraction of paths that hit ruin_threshold
    cagr_mean: float  # annualised compound growth rate
    cagr_p05: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "n_paths": int(self.n_paths),
            "n_bets": int(self.n_bets),
            "initial_bankroll": float(self.initial_bankroll),
            "final_bankroll_mean": float(self.final_bankroll_mean),
            "final_bankroll_median": float(self.final_bankroll_median),
            "final_bankroll_p05": float(self.final_bankroll_p05),
            "final_bankroll_p95": float(self.final_bankroll_p95),
            "max_drawdown_mean": float(self.max_drawdown_mean),
            "max_drawdown_p95": float(self.max_drawdown_p95),
            "risk_of_ruin": float(self.risk_of_ruin),
            "cagr_mean": float(self.cagr_mean),
            "cagr_p05": float(self.cagr_p05),
        }


def simulate_bankroll_paths(
    stakes: np.ndarray | list[float],
    odds: np.ndarray | list[float],
    probs: np.ndarray | list[float],
    initial_bankroll: float = 1000.0,
    n_paths: int = 10_000,
    ruin_threshold_fraction: float = 0.1,
    bets_per_year: float = 380.0,
    seed: int | None = 42,
) -> MonteCarloResult:
    """Simulate ``n_paths`` independent Bernoulli bet sequences.

    Parameters
    ----------
    stakes, odds, probs
        Aligned 1-D arrays of length ``n_bets``.
    initial_bankroll
        Starting capital. Bankroll is *not* rebalanced across paths.
    n_paths
        Number of Monte-Carlo rollouts (10k = ~0.5% SE on P95 drawdown).
    ruin_threshold_fraction
        Path is "ruined" if bankroll drops below this fraction of the
        starting capital at any point. Default 10%.
    bets_per_year
        Used to annualise CAGR (≈ 380 bets for a full football season).
    seed
        RNG seed for reproducibility.
    """
    stakes_arr = np.asarray(stakes, dtype=float)
    odds_arr = np.asarray(odds, dtype=float)
    probs_arr = np.asarray(probs, dtype=float)

    if not (stakes_arr.shape == odds_arr.shape == probs_arr.shape):
        raise ValueError("stakes, odds, probs must have the same shape")
    if stakes_arr.ndim != 1:
        raise ValueError("inputs must be 1-D arrays")
    if stakes_arr.size == 0:
        raise ValueError("at least one bet is required")
    if np.any(stakes_arr < 0):
        raise ValueError("stakes must be non-negative")
    if np.any(odds_arr <= 1.0):
        raise ValueError("odds must be > 1.0")
    if np.any((probs_arr < 0.0) | (probs_arr > 1.0)):
        raise ValueError("probs must lie in [0, 1]")
    if n_paths < 1:
        raise ValueError("n_paths must be >= 1")
    if not 0.0 <= ruin_threshold_fraction <= 1.0:
        raise ValueError("ruin_threshold_fraction must be in [0, 1]")

    rng = np.random.default_rng(seed)
    n_bets = stakes_arr.size

    # Draw all Bernoulli outcomes at once: (n_paths, n_bets)
    uniforms = rng.random(size=(n_paths, n_bets))
    wins = uniforms < probs_arr[None, :]

    # Per-bet profit matrix
    win_payoff = stakes_arr * (odds_arr - 1.0)
    loss_payoff = -stakes_arr
    profits = np.where(wins, win_payoff[None, :], loss_payoff[None, :])

    # Running bankroll trajectories
    bankrolls = initial_bankroll + np.cumsum(profits, axis=1)
    trajectory = np.concatenate(
        [np.full((n_paths, 1), float(initial_bankroll)), bankrolls],
        axis=1,
    )  # (n_paths, n_bets + 1)

    # Max drawdown per path (fractional)
    running_peak = np.maximum.accumulate(trajectory, axis=1)
    drawdowns = (running_peak - trajectory) / np.maximum(running_peak, 1e-12)
    max_dd_per_path = drawdowns.max(axis=1)

    # Ruin: path hit threshold at any point
    ruin_level = ruin_threshold_fraction * initial_bankroll
    ruined = (trajectory <= ruin_level).any(axis=1)
    risk_of_ruin = float(ruined.mean())

    final = trajectory[:, -1]
    years = max(n_bets / bets_per_year, 1e-6)
    # CAGR: non-positive finals → treat as -100%.
    safe_final = np.where(final > 0, final, 1e-9)
    cagr = np.where(
        final > 0,
        (safe_final / initial_bankroll) ** (1.0 / years) - 1.0,
        -1.0,
    )

    return MonteCarloResult(
        n_paths=n_paths,
        n_bets=n_bets,
        initial_bankroll=float(initial_bankroll),
        final_bankroll_mean=float(final.mean()),
        final_bankroll_median=float(np.median(final)),
        final_bankroll_p05=float(np.quantile(final, 0.05)),
        final_bankroll_p95=float(np.quantile(final, 0.95)),
        max_drawdown_mean=float(max_dd_per_path.mean()),
        max_drawdown_p95=float(np.quantile(max_dd_per_path, 0.95)),
        risk_of_ruin=risk_of_ruin,
        cagr_mean=float(cagr.mean()),
        cagr_p05=float(np.quantile(cagr, 0.05)),
    )


__all__ = [
    "MonteCarloResult",
    "simulate_bankroll_paths",
]
