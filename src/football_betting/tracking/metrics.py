"""
Performance metrics for betting model evaluation.

v0.2 additions:
* bankroll_curve — equity over time
* max_drawdown — peak-to-trough loss
* sharpe_ratio — risk-adjusted return
* clv_summary — aggregate CLV statistics
"""
from __future__ import annotations

from math import log, sqrt

import numpy as np

from football_betting.data.models import Outcome
from football_betting.predict.calibration import expected_calibration_error

OUTCOME_IDX: dict[Outcome, int] = {"H": 0, "D": 1, "A": 2}


# ───────────────────────── Core probabilistic metrics ─────────────────────────

def ranked_probability_score(
    probs: tuple[float, float, float], actual: Outcome
) -> float:
    """Ranked Probability Score for ordinal (H/D/A) outcomes. Lower is better."""
    actual_vec = np.zeros(3)
    actual_vec[OUTCOME_IDX[actual]] = 1.0
    p_cum = np.cumsum(probs)
    a_cum = np.cumsum(actual_vec)
    return 0.5 * float(np.sum((p_cum[:-1] - a_cum[:-1]) ** 2))


def mean_rps(predictions: list[tuple[tuple[float, float, float], Outcome]]) -> float:
    if not predictions:
        return float("nan")
    return float(np.mean([ranked_probability_score(p, a) for p, a in predictions]))


def brier_score(probs: tuple[float, float, float], actual: Outcome) -> float:
    actual_vec = np.zeros(3)
    actual_vec[OUTCOME_IDX[actual]] = 1.0
    return float(np.sum((np.array(probs) - actual_vec) ** 2))


def log_loss_3way(
    probs: tuple[float, float, float], actual: Outcome, eps: float = 1e-15
) -> float:
    p_actual = max(eps, min(1 - eps, probs[OUTCOME_IDX[actual]]))
    return -log(p_actual)


def hit_rate(predictions: list[Outcome], actuals: list[Outcome]) -> float:
    if not predictions:
        return 0.0
    correct = sum(p == a for p, a in zip(predictions, actuals, strict=True))
    return correct / len(predictions)


# ───────────────────────── F1-Score (per-class + macro/weighted) ─────────────────────────

def f1_scores_3way(
    predictions: list[Outcome],
    actuals: list[Outcome],
) -> dict[str, float]:
    """
    Precision / Recall / F1 for 3-way 1x2 classification.

    Returns per-class metrics plus ``macro_f1`` (unweighted mean) and
    ``weighted_f1`` (support-weighted). Useful for rare-event evaluation
    such as draws, where overall accuracy obscures class imbalance.
    """
    if len(predictions) != len(actuals):
        raise ValueError("predictions and actuals must be same length")

    classes: tuple[Outcome, ...] = ("H", "D", "A")
    result: dict[str, float] = {}

    if not predictions:
        for cls in classes:
            result[f"precision_{cls}"] = 0.0
            result[f"recall_{cls}"] = 0.0
            result[f"f1_{cls}"] = 0.0
            result[f"support_{cls}"] = 0.0
        result["macro_f1"] = 0.0
        result["weighted_f1"] = 0.0
        return result

    f1_per_class: list[float] = []
    support_per_class: list[int] = []

    for cls in classes:
        tp = sum(1 for p, a in zip(predictions, actuals, strict=True) if p == cls and a == cls)
        fp = sum(1 for p, a in zip(predictions, actuals, strict=True) if p == cls and a != cls)
        fn = sum(1 for p, a in zip(predictions, actuals, strict=True) if p != cls and a == cls)
        support = tp + fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        result[f"precision_{cls}"] = precision
        result[f"recall_{cls}"] = recall
        result[f"f1_{cls}"] = f1
        result[f"support_{cls}"] = float(support)

        f1_per_class.append(f1)
        support_per_class.append(support)

    total_support = sum(support_per_class)
    result["macro_f1"] = float(np.mean(f1_per_class))
    result["weighted_f1"] = (
        float(np.sum(np.array(f1_per_class) * np.array(support_per_class)) / total_support)
        if total_support > 0
        else 0.0
    )
    return result


# ───────────────────────── Financial metrics ─────────────────────────

def clv(bet_odds: float, closing_odds: float) -> float:
    """Closing Line Value (fractional). Positive → beat the market."""
    if closing_odds <= 1.0 or bet_odds <= 1.0:
        raise ValueError("Odds must be > 1.0")
    return (bet_odds / closing_odds) - 1.0


def clv_summary(
    bet_odds_list: list[float | None],
    close_odds_list: list[float | None],
) -> dict[str, float]:
    """Aggregate CLV statistics. Pairs with a ``None`` on either side are skipped."""
    if len(bet_odds_list) != len(close_odds_list):
        raise ValueError("Lists must be same length")

    clvs: list[float] = []
    for b, c in zip(bet_odds_list, close_odds_list, strict=True):
        if b is None or c is None:
            continue
        if b <= 1.0 or c <= 1.0:
            continue
        clvs.append(clv(b, c))

    if not clvs:
        return {"n": 0, "mean_clv": 0.0, "median_clv": 0.0, "pct_positive": 0.0}

    return {
        "n": len(clvs),
        "mean_clv": float(np.mean(clvs)),
        "median_clv": float(np.median(clvs)),
        "pct_positive": float(np.mean([1 if x > 0 else 0 for x in clvs])),
    }


def roi(stakes: list[float], returns: list[float]) -> float:
    if len(stakes) != len(returns):
        raise ValueError("stakes and returns must be same length")
    total_stake = sum(stakes)
    if total_stake <= 0:
        return 0.0
    return (sum(returns) - total_stake) / total_stake


def yield_pct(stakes: list[float], profits: list[float]) -> float:
    if sum(stakes) <= 0:
        return 0.0
    return sum(profits) / sum(stakes)


# ───────────────────────── v0.2: Bankroll curve & drawdown ─────────────────────────

def bankroll_curve(
    initial_bankroll: float,
    stakes: list[float],
    profits: list[float],
) -> list[float]:
    """Equity curve after each bet (initial value + running PnL)."""
    if len(stakes) != len(profits):
        raise ValueError("stakes and profits must be same length")
    curve = [initial_bankroll]
    for profit in profits:
        curve.append(curve[-1] + profit)
    return curve


def max_drawdown(bankroll: list[float]) -> dict[str, float]:
    """Peak-to-trough maximum drawdown, as absolute and percentage."""
    if not bankroll:
        return {"max_drawdown_abs": 0.0, "max_drawdown_pct": 0.0, "peak_idx": 0, "trough_idx": 0}

    peak = bankroll[0]
    peak_idx = 0
    max_dd_abs = 0.0
    max_dd_pct = 0.0
    trough_idx = 0

    for i, value in enumerate(bankroll):
        if value > peak:
            peak = value
            peak_idx = i
        dd = peak - value
        dd_pct = dd / peak if peak > 0 else 0.0
        if dd > max_dd_abs:
            max_dd_abs = dd
            max_dd_pct = dd_pct
            trough_idx = i

    return {
        "max_drawdown_abs": max_dd_abs,
        "max_drawdown_pct": max_dd_pct,
        "peak_idx": peak_idx,
        "trough_idx": trough_idx,
    }


def sharpe_ratio(returns: list[float], annualization_factor: float = 52.0) -> float:
    """
    Sharpe ratio of per-bet returns.

    `annualization_factor` ≈ 52 if averaging weekly; 250 if daily.
    For betting: use number of bets per year.
    """
    if not returns or len(returns) < 2:
        return 0.0
    arr = np.array(returns)
    mean_r = float(arr.mean())
    std_r = float(arr.std(ddof=1))
    if std_r == 0:
        return 0.0
    return mean_r / std_r * sqrt(annualization_factor)


# ───────────────────────── Summary ─────────────────────────

def summary_stats(
    predictions: list[tuple[tuple[float, float, float], Outcome]],
) -> dict[str, float]:
    """Summary of all probabilistic metrics."""
    if not predictions:
        return {}

    pred_outcomes: list[Outcome] = []
    for probs, _ in predictions:
        idx = int(np.argmax(probs))
        pred_outcomes.append(["H", "D", "A"][idx])  # type: ignore[arg-type]

    actuals = [a for _, a in predictions]
    probs = np.asarray([p for p, _ in predictions], dtype=float)
    y_true = np.asarray([OUTCOME_IDX[a] for a in actuals], dtype=int)

    f1_stats = f1_scores_3way(pred_outcomes, actuals)

    return {
        "n": len(predictions),
        "mean_rps": mean_rps(predictions),
        "mean_brier": float(np.mean([brier_score(p, a) for p, a in predictions])),
        "mean_log_loss": float(np.mean([log_loss_3way(p, a) for p, a in predictions])),
        "ece": expected_calibration_error(probs, y_true),
        "hit_rate": hit_rate(pred_outcomes, actuals),
        "macro_f1": f1_stats["macro_f1"],
        "weighted_f1": f1_stats["weighted_f1"],
        "f1_draw": f1_stats["f1_D"],
        "precision_draw": f1_stats["precision_D"],
        "recall_draw": f1_stats["recall_D"],
    }
