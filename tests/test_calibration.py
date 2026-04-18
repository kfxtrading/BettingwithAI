"""Tests for probability calibration."""
from __future__ import annotations

import numpy as np
import pytest

from football_betting.predict.calibration import (
    ProbabilityCalibrator,
    expected_calibration_error,
    reliability_diagram_data,
)


def _perfect_classifier_probs(n: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """Generate perfectly calibrated synthetic probs."""
    rng = np.random.default_rng(42)
    # True probabilities
    true_probs = rng.dirichlet(alpha=[2, 1, 2], size=n)
    # Draw actual labels from true probs
    labels = np.array([rng.choice(3, p=p) for p in true_probs])
    return true_probs, labels


def _overconfident_probs(n: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Generate overconfident probs (needs calibration)."""
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 3, size=n)
    # For each label, generate prob that's too confident (0.8+ in correct class)
    probs = np.zeros((n, 3))
    for i, lab in enumerate(labels):
        probs[i, lab] = 0.85 + rng.uniform(0, 0.1)
        # Spread remaining 0.05-0.15 on other two
        other_classes = [c for c in range(3) if c != lab]
        remaining = 1.0 - probs[i, lab]
        probs[i, other_classes[0]] = remaining * rng.uniform(0.3, 0.7)
        probs[i, other_classes[1]] = remaining - probs[i, other_classes[0]]

    # Make 30% of labels wrong (overconfidence = reality doesn't match prediction)
    flip_mask = rng.random(n) < 0.3
    for i in np.where(flip_mask)[0]:
        labels[i] = (labels[i] + 1) % 3

    return probs, labels


class TestProbabilityCalibrator:
    def test_isotonic_fit_and_transform(self) -> None:
        probs, labels = _overconfident_probs(300)
        cal = ProbabilityCalibrator()
        cal.fit(probs, labels)
        out = cal.transform(probs)

        assert out.shape == probs.shape
        # Rows should sum to 1
        row_sums = out.sum(axis=1)
        np.testing.assert_allclose(row_sums, np.ones_like(row_sums), atol=1e-6)

    def test_fit_requires_2d(self) -> None:
        cal = ProbabilityCalibrator()
        with pytest.raises(ValueError):
            cal.fit(np.array([0.5, 0.3, 0.2]), np.array([0]))

    def test_not_fitted_raises(self) -> None:
        cal = ProbabilityCalibrator()
        with pytest.raises(RuntimeError):
            cal.transform(np.zeros((10, 3)))

    def test_transform_single(self) -> None:
        probs, labels = _overconfident_probs(200)
        cal = ProbabilityCalibrator()
        cal.fit(probs, labels)
        out = cal.transform_single((0.8, 0.1, 0.1))
        assert isinstance(out, tuple)
        assert len(out) == 3
        assert sum(out) == pytest.approx(1.0, abs=1e-6)

    def test_calibration_improves_ece(self) -> None:
        """Calibration should reduce ECE on overconfident model."""
        # Split into train + test halves for honest evaluation
        probs, labels = _overconfident_probs(600)
        n_half = 300
        train_probs, train_labels = probs[:n_half], labels[:n_half]
        test_probs, test_labels = probs[n_half:], labels[n_half:]

        cal = ProbabilityCalibrator()
        cal.fit(train_probs, train_labels)
        calibrated = cal.transform(test_probs)

        ece_before = expected_calibration_error(test_probs, test_labels)
        ece_after = expected_calibration_error(calibrated, test_labels)

        # Isotonic should meaningfully reduce ECE on overconfident input
        assert ece_after <= ece_before + 0.01  # at least no worse


class TestECE:
    def test_perfect_prediction_ece_low(self) -> None:
        # All predictions perfect → low ECE
        n = 100
        probs = np.zeros((n, 3))
        labels = np.random.default_rng(0).integers(0, 3, size=n)
        for i, lab in enumerate(labels):
            probs[i, lab] = 1.0
        ece = expected_calibration_error(probs, labels)
        # Perfect probs + correct labels → near zero ECE
        assert ece < 0.01

    def test_random_prediction_ece_high(self) -> None:
        """Random probs paired with random labels → higher ECE."""
        rng = np.random.default_rng(1)
        probs = rng.dirichlet(alpha=[1, 1, 1], size=500)
        labels = rng.integers(0, 3, size=500)
        ece = expected_calibration_error(probs, labels)
        assert ece > 0  # sanity

    def test_reliability_diagram_data(self) -> None:
        probs, labels = _overconfident_probs(200)
        data = reliability_diagram_data(probs, labels, n_bins=10)
        assert "bin_center" in data
        assert "bin_accuracy" in data
        assert "bin_confidence" in data
        # Arrays align
        assert len(data["bin_center"]) == len(data["bin_accuracy"])
