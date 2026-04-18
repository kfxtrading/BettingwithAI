"""
Data quality & model drift monitoring.

v0.3 module for detecting:
* Feature distribution drift (KS-test per feature vs training distribution)
* Missing value rates above threshold
* Prediction confidence anomalies (mean confidence drifting from training)

Writes JSON reports to MONITORING_DIR. Integrated with CLI via `fb monitor`.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from football_betting.config import MONITORING_CFG, MONITORING_DIR, MonitoringConfig


@dataclass(slots=True)
class FeatureDriftReport:
    """Per-feature drift diagnostic."""

    feature_name: str
    training_mean: float
    training_std: float
    production_mean: float
    production_std: float
    ks_statistic: float
    ks_p_value: float
    is_drifted: bool
    missing_rate: float


@dataclass(slots=True)
class DriftReport:
    """Aggregate monitoring report."""

    timestamp: str
    league: str
    n_production_samples: int
    n_drifted_features: int
    per_feature: list[FeatureDriftReport] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "league": self.league,
            "n_production_samples": self.n_production_samples,
            "n_drifted_features": self.n_drifted_features,
            "per_feature": [asdict(f) for f in self.per_feature],
            "alerts": self.alerts,
        }

    def save(self, outdir: Path | None = None) -> Path:
        outdir = outdir or MONITORING_DIR
        outdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = outdir / f"drift_{self.league}_{ts}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))
        return path


@dataclass(slots=True)
class DriftDetector:
    """Compares production feature distributions to training baseline."""

    cfg: MonitoringConfig = field(default_factory=lambda: MONITORING_CFG)

    def analyze(
        self,
        training_features: pd.DataFrame,
        production_features: pd.DataFrame,
        league: str,
    ) -> DriftReport:
        """Run KS-test per feature; collect drift diagnostics."""
        common_cols = set(training_features.columns) & set(production_features.columns)
        n_drifted = 0
        per_feature_reports: list[FeatureDriftReport] = []
        alerts: list[str] = []

        for col in sorted(common_cols):
            train_values = training_features[col].dropna().values
            prod_values = production_features[col].dropna().values

            if len(train_values) < 20 or len(prod_values) < 5:
                continue  # not enough data

            # KS test
            ks_stat, ks_p = stats.ks_2samp(train_values, prod_values)

            # Missing rate in production
            missing_rate = (
                1.0 - len(prod_values) / len(production_features[col])
                if len(production_features[col]) > 0 else 0.0
            )

            is_drifted = float(ks_stat) > self.cfg.ks_test_threshold
            if is_drifted:
                n_drifted += 1
                alerts.append(
                    f"Drift in {col}: KS={ks_stat:.3f} (threshold {self.cfg.ks_test_threshold})"
                )

            if missing_rate > self.cfg.missing_rate_threshold:
                alerts.append(
                    f"High missing rate in {col}: {missing_rate * 100:.1f}% "
                    f"(threshold {self.cfg.missing_rate_threshold * 100:.1f}%)"
                )

            per_feature_reports.append(
                FeatureDriftReport(
                    feature_name=col,
                    training_mean=float(train_values.mean()),
                    training_std=float(train_values.std()),
                    production_mean=float(prod_values.mean()),
                    production_std=float(prod_values.std()),
                    ks_statistic=float(ks_stat),
                    ks_p_value=float(ks_p),
                    is_drifted=bool(is_drifted),
                    missing_rate=float(missing_rate),
                )
            )

        return DriftReport(
            timestamp=datetime.now().isoformat(),
            league=league,
            n_production_samples=len(production_features),
            n_drifted_features=n_drifted,
            per_feature=per_feature_reports,
            alerts=alerts,
        )


@dataclass(slots=True)
class PredictionMonitor:
    """Tracks model prediction confidence over time."""

    cfg: MonitoringConfig = field(default_factory=lambda: MONITORING_CFG)

    def confidence_report(
        self,
        predictions: list[tuple[float, float, float]],
        training_mean_confidence: float | None = None,
        training_std_confidence: float | None = None,
    ) -> dict[str, float]:
        """Compute confidence statistics + drift check."""
        if not predictions:
            return {}

        max_confidences = [max(p) for p in predictions]
        prod_mean = float(np.mean(max_confidences))
        prod_std = float(np.std(max_confidences))

        report = {
            "n_predictions": len(predictions),
            "production_mean_confidence": prod_mean,
            "production_std_confidence": prod_std,
            "min_confidence": float(min(max_confidences)),
            "max_confidence": float(max(max_confidences)),
        }

        if training_mean_confidence is not None and training_std_confidence is not None:
            z = abs(prod_mean - training_mean_confidence) / max(training_std_confidence, 1e-6)
            report["confidence_z_score"] = float(z)
            report["confidence_drift_alert"] = bool(z > self.cfg.confidence_drift_sigma)

        return report

    def histogram(self, predictions: list[tuple[float, float, float]]) -> dict[str, list[float]]:
        """Bin predictions into histogram for visualization."""
        if not predictions:
            return {"bin_edges": [], "counts": []}
        max_confs = [max(p) for p in predictions]
        counts, bin_edges = np.histogram(max_confs, bins=self.cfg.n_bins_histogram)
        return {
            "bin_edges": bin_edges.tolist(),
            "counts": counts.tolist(),
        }
