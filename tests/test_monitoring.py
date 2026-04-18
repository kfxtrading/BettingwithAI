"""Tests for drift detection and monitoring."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from football_betting.tracking.monitoring import (
    DriftDetector,
    PredictionMonitor,
)


class TestDriftDetector:
    def test_no_drift_identical_distributions(self) -> None:
        rng = np.random.default_rng(42)
        # Larger samples → KS statistic converges toward true value (0) on identical dists
        data = rng.normal(0, 1, 2000)
        train_df = pd.DataFrame({"feat_a": data[:1000]})
        prod_df = pd.DataFrame({"feat_a": data[1000:]})

        detector = DriftDetector()
        report = detector.analyze(train_df, prod_df, "PL")
        # Same distribution → no drift (may be 0 or 1 due to random chance, but KS stat low)
        assert report.n_drifted_features <= 1
        assert report.per_feature[0].ks_statistic < 0.15

    def test_detects_shifted_distribution(self) -> None:
        rng = np.random.default_rng(42)
        train_df = pd.DataFrame({"feat_a": rng.normal(0, 1, 500)})
        # Production data shifted by 3σ
        prod_df = pd.DataFrame({"feat_a": rng.normal(3, 1, 100)})

        detector = DriftDetector()
        report = detector.analyze(train_df, prod_df, "PL")
        assert report.n_drifted_features == 1
        assert len(report.alerts) >= 1
        assert report.per_feature[0].ks_statistic > 0.1

    def test_report_save(self, tmp_path) -> None:
        rng = np.random.default_rng(42)
        train_df = pd.DataFrame({"f": rng.normal(0, 1, 100)})
        prod_df = pd.DataFrame({"f": rng.normal(0, 1, 50)})

        detector = DriftDetector()
        report = detector.analyze(train_df, prod_df, "PL")
        path = report.save(outdir=tmp_path)
        assert path.exists()


class TestPredictionMonitor:
    def test_confidence_report(self) -> None:
        monitor = PredictionMonitor()
        preds = [(0.6, 0.2, 0.2), (0.5, 0.3, 0.2), (0.8, 0.1, 0.1)]
        report = monitor.confidence_report(preds)
        assert report["n_predictions"] == 3
        assert report["production_mean_confidence"] == pytest.approx(0.633, abs=0.01)

    def test_drift_alert_when_distant(self) -> None:
        monitor = PredictionMonitor()
        # Production much more confident than training
        preds = [(0.95, 0.03, 0.02)] * 10
        report = monitor.confidence_report(
            preds,
            training_mean_confidence=0.5,
            training_std_confidence=0.1,
        )
        assert report["confidence_z_score"] > 4.0
        assert report["confidence_drift_alert"] is True

    def test_histogram(self) -> None:
        monitor = PredictionMonitor()
        preds = [(0.5 + i * 0.01, 0.3, 0.2) for i in range(50)]
        hist = monitor.histogram(preds)
        assert "bin_edges" in hist
        assert "counts" in hist
        assert sum(hist["counts"]) == 50
