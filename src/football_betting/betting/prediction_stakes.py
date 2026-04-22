"""1X2 prediction staking: distribute a fixed daily bankroll across all
argmax-picks of a day, weighted by model probability.

Reference: ``Erweiterungen/Staking-Algorithmen.md``. Default strategy is
``hybrid`` (power-k=2 with odds damping) following the report's recommendation.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from football_betting.api.schemas import PredictionOut
    from football_betting.config import PredictionStakingConfig


# ───────────────────────── Core strategies ─────────────────────────


def flat_stakes(bankroll: float, n: int) -> np.ndarray:
    """Equal-weighted baseline: ``s_i = X / n``."""
    if n <= 0:
        return np.zeros(0, dtype=np.float64)
    return np.full(n, bankroll / n, dtype=np.float64)


def conf_stakes(bankroll: float, p: np.ndarray) -> np.ndarray:
    """Proportional (Hubáček conf): ``s_i = X · p_i / Σp_j``."""
    p = np.asarray(p, dtype=np.float64)
    total = p.sum()
    if total <= 0:
        return np.zeros_like(p)
    return np.asarray(bankroll * p / total, dtype=np.float64)


def power_stakes(bankroll: float, p: np.ndarray, k: float = 2.0) -> np.ndarray:
    """Power-law: ``s_i = X · p_i^k / Σp_j^k``. Softmax-equivalent on log-p."""
    p = np.asarray(p, dtype=np.float64)
    w = np.power(np.clip(p, 0.0, 1.0), k)
    total = w.sum()
    if total <= 0:
        return np.zeros_like(p)
    return np.asarray(bankroll * w / total, dtype=np.float64)


def hybrid_stakes(
    bankroll: float,
    p: np.ndarray,
    o: np.ndarray,
    k: float = 2.0,
    odds_floor: float = 2.0,
    min_p: float = 0.40,
) -> np.ndarray:
    """Hybrid (production default).

    Power-law confidence (``p_i^k``) combined with odds damping
    (``min(o_i / odds_floor, 1.0)``) and a ``min_p`` threshold. Picks below
    ``min_p`` are assigned stake 0 (but kept in the output for index stability).
    """
    p = np.asarray(p, dtype=np.float64)
    o = np.asarray(o, dtype=np.float64)
    mask = p >= min_p
    conf_w = np.where(mask, np.power(np.clip(p, 0.0, 1.0), k), 0.0)
    odds_factor = np.minimum(o / odds_floor, 1.0)
    w = conf_w * odds_factor
    total = w.sum()
    if total <= 0:
        return np.zeros_like(p)
    return np.asarray(bankroll * w / total, dtype=np.float64)


def entropy_stakes(
    bankroll: float, p_full: np.ndarray, eps: float = 1e-12
) -> np.ndarray:
    """Shannon-entropy weighted: uses full 3-outcome distribution.

    ``p_full`` shape ``(N, 3)`` with rows ``(p_H, p_X, p_A)``.
    ``s_i = X · (1 - H_i/ln 3) / Σ(1 - H_j/ln 3)``.
    """
    p_full = np.asarray(p_full, dtype=np.float64)
    if p_full.ndim != 2 or p_full.shape[1] != 3:
        raise ValueError(f"p_full must be (N,3), got shape {p_full.shape}")
    h = -np.sum(p_full * np.log(p_full + eps), axis=1)
    conf = 1.0 - h / np.log(3)
    conf = np.clip(conf, 0.0, 1.0)
    total = conf.sum()
    if total <= 0:
        return np.zeros(p_full.shape[0], dtype=np.float64)
    return np.asarray(bankroll * conf / total, dtype=np.float64)


# ───────────────────────── Diagnostics ─────────────────────────


def diagnostics(stakes: np.ndarray) -> dict[str, float]:
    """Concentration diagnostics: HHI, effective count, max weight, sum."""
    s = np.asarray(stakes, dtype=float)
    total = s.sum()
    if total <= 0:
        return {"HHI": 0.0, "N_eff": 0.0, "max_weight": 0.0, "sum": 0.0}
    w = s / total
    hhi = float((w**2).sum())
    return {
        "HHI": hhi,
        "N_eff": float(1.0 / hhi) if hhi > 0 else 0.0,
        "max_weight": float(w.max()),
        "sum": float(total),
    }


# ───────────────────────── High-level allocator ─────────────────────────


def _extract_pick(
    pred: PredictionOut,
) -> tuple[float, float, tuple[float, float, float]] | None:
    """Return (p_max, odds_of_pick, (p_H, p_X, p_A)) or None if not stakable."""
    if pred.odds is None:
        return None
    if pred.most_likely == "H":
        p_max, o = pred.prob_home, pred.odds.home
    elif pred.most_likely == "A":
        p_max, o = pred.prob_away, pred.odds.away
    else:
        p_max, o = pred.prob_draw, pred.odds.draw
    if o is None or o <= 1.0:
        return None
    return float(p_max), float(o), (
        float(pred.prob_home),
        float(pred.prob_draw),
        float(pred.prob_away),
    )


def allocate_prediction_stakes(
    predictions: list[PredictionOut],
    cfg: PredictionStakingConfig,
) -> list[float]:
    """Allocate the daily bankroll across 1X2 predictions.

    Returns monetary stakes (rounded to 2 decimals) in the same order as
    ``predictions``. Picks without odds or with odds ≤ 1 get stake 0. The
    total is guaranteed to be ≤ ``cfg.daily_bankroll`` (rounding is
    floor-safe; cumulative rounding error is absorbed on the largest pick).
    """
    n = len(predictions)
    if n == 0:
        return []

    extracted = [_extract_pick(p) for p in predictions]
    valid_idx = [i for i, e in enumerate(extracted) if e is not None]
    if not valid_idx:
        return [0.0] * n

    p_max = np.array([extracted[i][0] for i in valid_idx], dtype=np.float64)  # type: ignore[index]
    odds = np.array([extracted[i][1] for i in valid_idx], dtype=np.float64)  # type: ignore[index]
    p_full = np.array([extracted[i][2] for i in valid_idx], dtype=np.float64)  # type: ignore[index]
    bankroll = float(cfg.daily_bankroll)

    if cfg.strategy == "flat":
        raw = flat_stakes(bankroll, len(valid_idx))
    elif cfg.strategy == "conf":
        raw = conf_stakes(bankroll, p_max)
    elif cfg.strategy == "power":
        raw = power_stakes(bankroll, p_max, k=cfg.power_k)
    elif cfg.strategy == "hybrid":
        raw = hybrid_stakes(
            bankroll, p_max, odds,
            k=cfg.power_k,
            odds_floor=cfg.odds_floor,
            min_p=cfg.min_p,
        )
    elif cfg.strategy == "entropy":
        raw = entropy_stakes(bankroll, p_full)
    else:
        raise ValueError(f"Unknown staking strategy: {cfg.strategy!r}")

    rounded = np.round(raw, 2)
    total = float(rounded.sum())
    if total > bankroll:
        max_i = int(np.argmax(rounded))
        rounded[max_i] = max(0.0, rounded[max_i] - (total - bankroll))
        rounded = np.round(rounded, 2)

    out = [0.0] * n
    for pos, src_i in enumerate(valid_idx):
        out[src_i] = float(rounded[pos])
    return out
