"""Phase D — evaluate isotonic / temperature / no calibration for Kelly models.

For each (league, architecture) pair with a trained ``*.kelly.pt`` checkpoint:

1. Reproduce the training-time 85/15 val split deterministically.
2. Compute raw (pre-calibration) val probabilities from the loaded model.
3. Halve the val slice into *calib* and *eval* sub-splits (first 50 % / last 50 %).
4. Fit three calibrators on the calib half:
   * ``none``       — identity (raw probs).
   * ``isotonic``   — one-vs-rest :class:`ProbabilityCalibrator`.
   * ``temperature``— single-scalar :class:`TemperatureCalibrator`.
5. Score each on the eval half via:
   * ECE (lower is better)
   * Kelly-growth (per-sample realised log-growth under clamped-Kelly
     on the opening odds; higher is better — matches the training objective)
   * NLL (lower is better)
6. Pick the winner. Default is ``none`` unless another method beats ``none``
   on Kelly-growth by ≥ ``GROWTH_MARGIN`` **and** does not worsen ECE by
   more than ``ECE_MARGIN``. This matches the Phase D plan
   (_plans/gpu_kelly_training_plan.md §Phase D).
7. Persist: winner calibrator → ``models/<arch>_<league>.kelly.calibrator.joblib``
   (or delete that file if winner is ``none`` so ``Predictor.load()`` stays
   uncalibrated). Audit JSON → ``models/_runs/<arch>_<league>.kelly.calibration.json``.

Run:

    python scripts/evaluate_kelly_calibration.py
    # or via CLI wrapper:
    fb evaluate-kelly-calibration
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from typing import Any

import joblib
import numpy as np

from football_betting.config import (
    MLP_CFG,
    MODELS_DIR,
    SEQUENCE_CFG,
    TAB_TRANSFORMER_CFG,
    CalibrationConfig,
)
from football_betting.data.loader import load_league
from football_betting.features.form import FormTracker
from football_betting.predict.calibration import (
    ProbabilityCalibrator,
    TemperatureCalibrator,
    expected_calibration_error,
)
from football_betting.predict.kelly_data import collect_opening_odds_and_mask
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.runtime import make_feature_builder
from football_betting.predict.sequence_features import build_dataset
from football_betting.predict.sequence_model import SequencePredictor
from football_betting.predict.tabular_transformer import TabTransformerPredictor
from football_betting.rating.pi_ratings import PiRatings
from football_betting.scraping.sofascore import SofascoreClient

DEFAULT_LEAGUES: tuple[str, ...] = ("BL", "CH", "LL", "PL", "SA")
DEFAULT_ARCHITECTURES: tuple[str, ...] = ("mlp", "tabtransformer", "sequence")
DEFAULT_SEASONS: tuple[str, ...] = ("2021-22", "2022-23", "2023-24", "2024-25")
WARMUP_GAMES = 100
VAL_FRACTION = 0.15
KELLY_F_CAP = 0.25

# Winner-selection margins (see plan §Phase D).
GROWTH_MARGIN = 0.0005  # must beat "none" on Kelly-growth by at least this
ECE_MARGIN = 0.005  # must not worsen ECE by more than this

RUNS_DIR = MODELS_DIR / "_runs"


# ───────────────────────── Data utilities ─────────────────────────


@dataclass(slots=True)
class ValSlice:
    """Raw-val probabilities plus aligned labels/odds for one model."""

    raw_probs: np.ndarray  # (n_val, 3)
    y_val: np.ndarray  # (n_val,)
    opening_val: np.ndarray  # (n_val, 3)
    mask_val: np.ndarray  # (n_val,) bool


def _stage_sofascore(feature_builder: Any, league: str, seasons: tuple[str, ...]) -> None:
    for season in seasons:
        sf_data = SofascoreClient.load_matches(league, season)
        if sf_data:
            feature_builder.stage_sofascore_batch(sf_data)


def _opening_val(matches: list[Any], split: int, n_rows: int) -> tuple[np.ndarray, np.ndarray]:
    opening_np, mask_np = collect_opening_odds_and_mask(matches, warmup_games=WARMUP_GAMES)
    if opening_np.shape[0] != n_rows:
        raise RuntimeError(
            f"opening rows ({opening_np.shape[0]}) != training rows ({n_rows}); "
            "warmup / sort ordering broke alignment"
        )
    opening_np = np.where(np.isfinite(opening_np), opening_np, 2.0).astype(np.float32)
    return opening_np[split:], mask_np[split:]


def _mlp_val_slice(league: str) -> ValSlice:
    import torch

    seasons = DEFAULT_SEASONS
    matches = load_league(league, seasons=list(seasons))
    feature_builder = make_feature_builder(purpose="1x2")
    _stage_sofascore(feature_builder, league, seasons)

    cfg = dataclasses.replace(MLP_CFG, use_shrinkage_kelly=True)
    predictor = MLPPredictor(feature_builder=feature_builder, cfg=cfg, purpose="1x2")
    predictor.load(MODELS_DIR / f"mlp_{league}.kelly.pt")

    X, y, _odds = predictor.build_training_data(matches, warmup_games=WARMUP_GAMES)  # noqa: N806
    split = int(len(X) * (1 - VAL_FRACTION))

    # Reindex val features to the model's trained column order.
    X_val = X.iloc[split:].reindex(columns=predictor.feature_names, fill_value=0.0).values  # noqa: N806
    assert predictor.scaler is not None
    X_val_s = predictor.scaler.transform(X_val).astype(np.float32)  # noqa: N806

    predictor.model.eval()
    with torch.no_grad():
        logits = predictor.model(torch.tensor(X_val_s, dtype=torch.float32))
        raw_probs = torch.softmax(logits, dim=1).cpu().numpy()

    opening_val, mask_val = _opening_val(matches, split, len(X))
    return ValSlice(raw_probs=raw_probs, y_val=y[split:], opening_val=opening_val, mask_val=mask_val)


def _tab_val_slice(league: str) -> ValSlice:
    seasons = DEFAULT_SEASONS
    matches = load_league(league, seasons=list(seasons))
    feature_builder = make_feature_builder(purpose="1x2")
    _stage_sofascore(feature_builder, league, seasons)

    cfg = dataclasses.replace(TAB_TRANSFORMER_CFG, use_shrinkage_kelly=True)
    predictor = TabTransformerPredictor(feature_builder=feature_builder, cfg=cfg, purpose="1x2")
    predictor.load(MODELS_DIR / f"tabtransformer_{league}.kelly.pt")

    X, y, _odds = predictor.build_training_data(  # type: ignore[misc]  # noqa: N806
        matches, warmup_games=WARMUP_GAMES, return_odds=True
    )
    split = int(len(X) * (1 - VAL_FRACTION))

    X_val = X.iloc[split:].reindex(columns=predictor.feature_names, fill_value=0.0).values  # noqa: N806
    assert predictor.scaler is not None
    X_val_s = predictor.scaler.transform(X_val).astype(np.float32)  # noqa: N806
    raw_probs = predictor._forward_np(X_val_s)

    opening_val, mask_val = _opening_val(matches, split, len(X))
    return ValSlice(raw_probs=raw_probs, y_val=y[split:], opening_val=opening_val, mask_val=mask_val)


def _sequence_val_slice(league: str) -> ValSlice:
    import torch

    seasons = DEFAULT_SEASONS
    matches = load_league(league, seasons=list(seasons))
    # Sequence uses its own FormTracker + PiRatings walk (no FeatureBuilder needed).
    cfg = dataclasses.replace(SEQUENCE_CFG, use_shrinkage_kelly=True)
    predictor = SequencePredictor(cfg=cfg, purpose="1x2")
    predictor.load(MODELS_DIR / f"sequence_{league}.kelly.pt")

    H, HM, A, AM, y, _odds = build_dataset(  # noqa: N806
        matches,
        FormTracker(),
        PiRatings(),
        window_t=cfg.window_t,
        warmup_games=WARMUP_GAMES,
    )
    split = int(len(y) * (1 - VAL_FRACTION))

    predictor.model.eval()
    device = predictor._device or torch.device("cpu")
    with torch.no_grad():
        logits = predictor.model(
            torch.tensor(H[split:], dtype=torch.float32, device=device),
            torch.tensor(HM[split:], dtype=torch.float32, device=device),
            torch.tensor(A[split:], dtype=torch.float32, device=device),
            torch.tensor(AM[split:], dtype=torch.float32, device=device),
        )
        raw_probs = torch.softmax(logits, dim=1).cpu().numpy()

    opening_val, mask_val = _opening_val(matches, split, len(y))
    return ValSlice(raw_probs=raw_probs, y_val=y[split:], opening_val=opening_val, mask_val=mask_val)


VAL_LOADERS: dict[str, Any] = {
    "mlp": _mlp_val_slice,
    "tabtransformer": _tab_val_slice,
    "sequence": _sequence_val_slice,
}


# ───────────────────────── Metrics ─────────────────────────


def _kelly_growth_np(
    probs: np.ndarray,
    opening_odds: np.ndarray,
    y: np.ndarray,
    mask: np.ndarray,
    f_cap: float = KELLY_F_CAP,
    eps: float = 1e-6,
) -> float:
    """NumPy port of :func:`predict.losses.kelly_growth_metric`.

    Returns the mean realised log-bankroll-growth under clamped Kelly on
    the actual (winning) outcome. Rows where ``mask`` is ``False`` are
    excluded. Safe on empty / all-masked input → returns ``0.0``.
    """
    if probs.shape[0] == 0 or not mask.any():
        return 0.0
    y_onehot = np.zeros_like(probs)
    y_onehot[np.arange(probs.shape[0]), y] = 1.0
    p = np.clip(probs, eps, 1.0 - eps)
    b = np.clip(opening_odds - 1.0, eps, None)
    f_star = np.clip((b * p - (1.0 - p)) / b, 0.0, f_cap)
    r = opening_odds * y_onehot - 1.0
    growth = np.clip(1.0 + f_star * r, eps, None)
    per_sample = (y_onehot * np.log(growth)).sum(axis=1)
    mask_f = mask.astype(np.float64)
    denom = max(mask_f.sum(), 1.0)
    return float((per_sample * mask_f).sum() / denom)


def _nll(probs: np.ndarray, y: np.ndarray, eps: float = 1e-12) -> float:
    rows = np.arange(probs.shape[0])
    return float(-np.log(np.clip(probs[rows, y], eps, 1.0)).mean())


# ───────────────────────── Calibration variants ─────────────────────────


def _score(
    probs: np.ndarray,
    y: np.ndarray,
    opening: np.ndarray,
    mask: np.ndarray,
) -> dict[str, float]:
    return {
        "ece": float(expected_calibration_error(probs, y)),
        "kelly_growth": _kelly_growth_np(probs, opening, y, mask),
        "nll": _nll(probs, y),
    }


def _fit_variants(
    calib_probs: np.ndarray,
    calib_y: np.ndarray,
) -> dict[str, Any]:
    """Fit isotonic and temperature calibrators; return {method: calibrator or None}."""
    # Small calib halves (~80-150 samples) would hit the default
    # min_samples_per_class=50 guard and silently fall back to identity for
    # the rarest class (draws). Lower the threshold so isotonic gets a fair
    # chance; this is a per-method fit on the same data as the other variants.
    iso = ProbabilityCalibrator(
        cfg=CalibrationConfig(method="isotonic", min_samples_per_class=10)
    )
    iso.fit(calib_probs, calib_y)
    temp = TemperatureCalibrator().fit(calib_probs, calib_y)
    return {"none": None, "isotonic": iso, "temperature": temp}


def _apply(calibrator: Any, probs: np.ndarray) -> np.ndarray:
    if calibrator is None:
        return probs
    out: np.ndarray = calibrator.transform(probs)
    return out


def _pick_winner(metrics: dict[str, dict[str, float]]) -> tuple[str, str]:
    """Return (winner_method, reason)."""
    base = metrics["none"]
    best_method = "none"
    best_growth = base["kelly_growth"]
    for method in ("isotonic", "temperature"):
        m = metrics[method]
        if m["kelly_growth"] - base["kelly_growth"] < GROWTH_MARGIN:
            continue
        if m["ece"] - base["ece"] > ECE_MARGIN:
            continue
        if m["kelly_growth"] > best_growth:
            best_method = method
            best_growth = m["kelly_growth"]

    if best_method == "none":
        reason = (
            f"kept baseline: no method beats 'none' by +{GROWTH_MARGIN:.4f} growth "
            f"while staying within {ECE_MARGIN:.3f} ECE"
        )
    else:
        delta_g = metrics[best_method]["kelly_growth"] - base["kelly_growth"]
        delta_e = metrics[best_method]["ece"] - base["ece"]
        reason = (
            f"{best_method} beats baseline by +{delta_g:.5f} growth "
            f"(ECE delta {delta_e:+.4f})"
        )
    return best_method, reason


# ───────────────────────── Persistence ─────────────────────────


def _persist(
    league: str,
    architecture: str,
    winner: str,
    calibrators: dict[str, Any],
    audit: dict[str, Any],
) -> None:
    calib_path = MODELS_DIR / f"{architecture}_{league}.kelly.calibrator.joblib"
    if winner == "none":
        if calib_path.exists():
            calib_path.unlink()
    else:
        joblib.dump(calibrators[winner], calib_path)

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    audit_path = RUNS_DIR / f"{architecture}_{league}.kelly.calibration.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True))


# ───────────────────────── Driver ─────────────────────────


def evaluate_one(
    league: str, architecture: str, *, verbose: bool = True
) -> dict[str, Any]:
    ckpt = MODELS_DIR / f"{architecture}_{league}.kelly.pt"
    if not ckpt.exists():
        return {"league": league, "architecture": architecture, "status": "skipped-missing"}

    if verbose:
        print(f"[{architecture}/{league}] loading model + rebuilding val slice...")

    val = VAL_LOADERS[architecture](league)
    n_val = len(val.y_val)
    half = n_val // 2
    calib_slice = slice(0, half)
    eval_slice = slice(half, n_val)

    calib_probs = val.raw_probs[calib_slice]
    calib_y = val.y_val[calib_slice]
    eval_probs = val.raw_probs[eval_slice]
    eval_y = val.y_val[eval_slice]
    eval_opening = val.opening_val[eval_slice]
    eval_mask = val.mask_val[eval_slice]

    variants = _fit_variants(calib_probs, calib_y)
    metrics: dict[str, dict[str, float]] = {}
    for method, cal in variants.items():
        p = _apply(cal, eval_probs)
        metrics[method] = _score(p, eval_y, eval_opening, eval_mask)

    winner, reason = _pick_winner(metrics)

    audit = {
        "league": league,
        "architecture": architecture,
        "n_val_total": int(n_val),
        "n_calib": int(half),
        "n_eval": int(n_val - half),
        "mask_coverage_eval": float(eval_mask.mean()) if len(eval_mask) else 0.0,
        "metrics": metrics,
        "winner": winner,
        "reason": reason,
        "temperature": float(variants["temperature"].temperature),
        "selection": {
            "growth_margin": GROWTH_MARGIN,
            "ece_margin": ECE_MARGIN,
        },
    }
    _persist(league, architecture, winner, variants, audit)

    if verbose:
        row = " | ".join(
            f"{m}: g={metrics[m]['kelly_growth']:+.5f} ece={metrics[m]['ece']:.4f}"
            for m in ("none", "isotonic", "temperature")
        )
        print(f"  {row}")
        print(f"  -> winner: {winner}  ({reason})")

    return audit


def main(
    leagues: tuple[str, ...] = DEFAULT_LEAGUES,
    architectures: tuple[str, ...] = DEFAULT_ARCHITECTURES,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for league in leagues:
        for arch in architectures:
            try:
                results.append(evaluate_one(league, arch))
            except Exception as e:  # pragma: no cover — defensive driver
                print(f"[{arch}/{league}] FAILED: {type(e).__name__}: {e}")
                results.append(
                    {
                        "league": league,
                        "architecture": arch,
                        "status": "error",
                        "error": f"{type(e).__name__}: {e}",
                    }
                )

    summary = {
        "processed": sum(1 for r in results if r.get("winner")),
        "by_winner": {
            k: sum(1 for r in results if r.get("winner") == k)
            for k in ("none", "isotonic", "temperature")
        },
        "skipped": sum(1 for r in results if r.get("status") == "skipped-missing"),
        "errors": sum(1 for r in results if r.get("status") == "error"),
    }
    print("\nSummary:", json.dumps(summary, indent=2))
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / "kelly_calibration_summary.json").write_text(
        json.dumps({"summary": summary, "runs": results}, indent=2)
    )
    return results


if __name__ == "__main__":
    main()
