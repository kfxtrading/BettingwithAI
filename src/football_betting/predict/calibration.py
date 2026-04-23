"""
Probability calibration via Isotonic regression or Platt scaling.

Raw CatBoost probabilities are often poorly calibrated at the extremes
(too confident about heavy favorites, under-confident on upsets). Post-hoc
calibration on held-out validation data fixes this without retraining.

Reference:
    Platt (1999), "Probabilistic Outputs for SVMs and Comparisons to
    Regularized Likelihood Methods"
    Zadrozny & Elkan (2002), "Transforming Classifier Scores into
    Accurate Multiclass Probability Estimates"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from football_betting.config import CALIBRATION_CFG, CalibrationConfig


@dataclass(slots=True)
class ProbabilityCalibrator:
    """
    One-vs-rest calibrator for multi-class probabilities.

    Fits K separate calibrators (one per class) on (raw_prob, is_class) pairs,
    then at prediction time applies each and renormalizes.
    """

    cfg: CalibrationConfig = field(default_factory=lambda: CALIBRATION_CFG)
    n_classes: int = 3
    calibrators: list[IsotonicRegression | LogisticRegression] = field(default_factory=list)
    is_fitted: bool = False

    def fit(self, raw_probs: np.ndarray, y_true: np.ndarray) -> ProbabilityCalibrator:
        """
        Fit one-vs-rest calibrators.

        raw_probs: (n_samples, n_classes) — raw classifier probs
        y_true: (n_samples,) — true class indices 0..K-1
        """
        if raw_probs.ndim != 2:
            raise ValueError(f"Expected 2-D probs, got shape {raw_probs.shape}")
        n_samples, n_classes = raw_probs.shape
        self.n_classes = n_classes

        self.calibrators = []
        for class_idx in range(n_classes):
            # Binary: is_class[i] == 1 if y_true[i] == class_idx
            is_class = (y_true == class_idx).astype(int)
            raw_p = raw_probs[:, class_idx]

            # Enough positive samples?
            if is_class.sum() < self.cfg.min_samples_per_class:
                # Fall back to identity mapping
                self.calibrators.append(_IdentityCalibrator())
                continue

            if self.cfg.method == "isotonic":
                cal = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                cal.fit(raw_p, is_class)
            elif self.cfg.method == "sigmoid":
                cal = LogisticRegression(C=1e10)  # essentially no regularization
                cal.fit(raw_p.reshape(-1, 1), is_class)
            elif self.cfg.method == "auto":
                cal = _fit_auto_calibrator(raw_p, is_class)
            else:
                raise ValueError(f"Unknown calibration method: {self.cfg.method}")

            self.calibrators.append(cal)

        self.is_fitted = True
        return self

    def transform(self, raw_probs: np.ndarray) -> np.ndarray:
        """Apply calibration + renormalization."""
        if not self.is_fitted:
            raise RuntimeError("Calibrator not fitted.")

        calibrated = np.zeros_like(raw_probs)
        for idx, cal in enumerate(self.calibrators):
            if isinstance(cal, _IdentityCalibrator):
                calibrated[:, idx] = raw_probs[:, idx]
            elif isinstance(cal, IsotonicRegression):
                calibrated[:, idx] = cal.predict(raw_probs[:, idx])
            elif isinstance(cal, LogisticRegression):
                calibrated[:, idx] = cal.predict_proba(raw_probs[:, idx].reshape(-1, 1))[:, 1]

        # Renormalize rows
        row_sums = calibrated.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return calibrated / row_sums

    def transform_single(self, raw_probs: tuple[float, float, float]) -> tuple[float, float, float]:
        arr = np.array([raw_probs])
        out = self.transform(arr)[0]
        return float(out[0]), float(out[1]), float(out[2])


class _IdentityCalibrator:
    """Placeholder when not enough data to calibrate a class."""

    def predict(self, x: np.ndarray) -> np.ndarray:
        return x


def _fit_auto_calibrator(
    raw_p: np.ndarray, is_class: np.ndarray
) -> IsotonicRegression | LogisticRegression:
    """Pick lowest held-out ECE across {isotonic, sigmoid, regularized-sigmoid}.

    Rationale: isotonic is non-parametric and overfits on small samples
    (<200 per class); unregularized sigmoid (Platt) helps; regularized
    sigmoid acts like temperature scaling (1 effective dof) and wins
    under temporal distribution shift. Auto lets the data pick.
    """
    from sklearn.model_selection import KFold

    n = len(raw_p)
    kf = KFold(n_splits=min(5, n), shuffle=True, random_state=42)

    def _fold_ece(method: str) -> float:
        total = 0.0
        for tr, te in kf.split(raw_p):
            p_tr, p_te = raw_p[tr], raw_p[te]
            y_tr, y_te = is_class[tr], is_class[te]
            if y_tr.sum() == 0 or y_tr.sum() == len(y_tr):
                return float("inf")  # degenerate fold
            if method == "isotonic":
                m = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                m.fit(p_tr, y_tr)
                pred = m.predict(p_te)
            elif method == "sigmoid":
                m = LogisticRegression(C=1e10)
                m.fit(p_tr.reshape(-1, 1), y_tr)
                pred = m.predict_proba(p_te.reshape(-1, 1))[:, 1]
            else:  # regularized sigmoid (≈ temperature scaling)
                m = LogisticRegression(C=0.1)
                m.fit(p_tr.reshape(-1, 1), y_tr)
                pred = m.predict_proba(p_te.reshape(-1, 1))[:, 1]
            # Binary ECE with 10 bins
            bins = np.linspace(0, 1, 11)
            for i in range(10):
                mask = (pred > bins[i]) & (pred <= bins[i + 1])
                if mask.sum() == 0:
                    continue
                total += (mask.sum() / n) * abs(pred[mask].mean() - y_te[mask].mean())
        return total

    candidates: dict[str, float] = {
        "isotonic": _fold_ece("isotonic"),
        "sigmoid": _fold_ece("sigmoid"),
        "regularized": _fold_ece("regularized"),
    }
    best = min(candidates, key=lambda k: candidates[k])

    if best == "isotonic":
        cal: IsotonicRegression | LogisticRegression = IsotonicRegression(
            out_of_bounds="clip", y_min=0.0, y_max=1.0
        )
        cal.fit(raw_p, is_class)
    elif best == "sigmoid":
        cal = LogisticRegression(C=1e10)
        cal.fit(raw_p.reshape(-1, 1), is_class)
    else:
        cal = LogisticRegression(C=0.1)
        cal.fit(raw_p.reshape(-1, 1), is_class)
    return cal


# ───────────────────────── Reliability diagrams ─────────────────────────

def expected_calibration_error(
    probs: np.ndarray,
    y_true: np.ndarray,
    n_bins: int = 10,
) -> float:
    """
    Expected Calibration Error (ECE) — multi-class version.

    Groups predictions by confidence bin; computes |accuracy - confidence| per bin
    weighted by bin size.

    Perfect calibration → ECE = 0. Values <0.02 are very good.
    """
    if probs.ndim != 2:
        raise ValueError(f"Expected 2-D probs, got shape {probs.shape}")

    predicted_class = probs.argmax(axis=1)
    max_conf = probs.max(axis=1)
    correct = (predicted_class == y_true).astype(float)

    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (max_conf > bins[i]) & (max_conf <= bins[i + 1])
        if mask.sum() == 0:
            continue
        bin_conf = max_conf[mask].mean()
        bin_acc = correct[mask].mean()
        weight = mask.sum() / len(max_conf)
        ece += weight * abs(bin_conf - bin_acc)

    return float(ece)


def reliability_diagram_data(
    probs: np.ndarray,
    y_true: np.ndarray,
    n_bins: int = 10,
) -> dict[str, np.ndarray]:
    """Bin centers + accuracy per bin, ready for matplotlib plotting."""
    predicted_class = probs.argmax(axis=1)
    max_conf = probs.max(axis=1)
    correct = (predicted_class == y_true).astype(float)

    bins = np.linspace(0, 1, n_bins + 1)
    centers = []
    confidences = []
    accuracies = []
    counts = []

    for i in range(n_bins):
        mask = (max_conf > bins[i]) & (max_conf <= bins[i + 1])
        if mask.sum() == 0:
            continue
        centers.append((bins[i] + bins[i + 1]) / 2)
        confidences.append(max_conf[mask].mean())
        accuracies.append(correct[mask].mean())
        counts.append(int(mask.sum()))

    return {
        "bin_center": np.array(centers),
        "bin_confidence": np.array(confidences),
        "bin_accuracy": np.array(accuracies),
        "bin_count": np.array(counts),
    }
