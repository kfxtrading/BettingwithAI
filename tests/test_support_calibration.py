"""Unit tests for Temperature Scaling + ECE (support/calibration.py)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from football_betting.support.calibration import (
    TemperatureCalibrator,
    expected_calibration_error,
)


def _synthetic_logits(
    n: int, n_classes: int, *, signal: float = 1.2, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Build (logits, labels) with controllable accuracy (~50-70%).

    ``signal`` is added to the label-row; noise is unit-variance Gaussian.
    Small signal → imperfect top-1 → meaningful ECE behaviour when scaled.
    """
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, n_classes, size=n)
    logits = rng.normal(0.0, 1.0, size=(n, n_classes))
    logits[np.arange(n), labels] += signal
    return logits.astype(np.float64), labels


def test_ece_perfect_calibration_is_low() -> None:
    # Sharp, correct logits → very confident + (almost) always right → low ECE.
    logits, labels = _synthetic_logits(2000, 10, signal=7.0, seed=1)
    probs = _softmax(logits)
    ece = expected_calibration_error(probs, labels)
    assert 0.0 <= ece < 0.1


def test_ece_overconfident_is_high() -> None:
    # With weak signal (~60% acc) and big scaling factor, probs saturate at 1.0
    # while accuracy stays ~60% → ECE climbs well above baseline.
    base_logits, labels = _synthetic_logits(2000, 10, signal=1.2, seed=2)
    ece_base = expected_calibration_error(_softmax(base_logits), labels)
    ece_scaled = expected_calibration_error(_softmax(base_logits * 5.0), labels)
    assert ece_scaled > ece_base + 0.05


def test_temperature_scaling_reduces_ece(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    logits, labels = _synthetic_logits(1500, 10, signal=1.2, seed=3)
    # Make model over-confident (scale up → T>1 should be the remedy).
    over = logits * 5.0
    ece_before = expected_calibration_error(_softmax(over), labels)

    calibrator = TemperatureCalibrator()
    info = calibrator.fit(over, labels, max_iter=50)

    # T > 1 (softening) is the expected fix for over-confidence.
    assert info["temperature"] > 1.0
    assert calibrator.ece_after is not None
    assert calibrator.ece_after < ece_before
    # Argmax ranking must not change — Temperature Scaling is monotone.
    argmax_before = _softmax(over).argmax(axis=1)
    argmax_after = calibrator.apply_probs(over).argmax(axis=1)
    np.testing.assert_array_equal(argmax_before, argmax_after)


def test_calibrator_save_load_roundtrip(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    logits, labels = _synthetic_logits(200, 5, signal=1.2, seed=4)
    calibrator = TemperatureCalibrator()
    calibrator.fit(logits * 3.0, labels, max_iter=20)
    path = tmp_path / "temperature.json"
    calibrator.save(path)
    loaded = TemperatureCalibrator.load(path)
    assert loaded.temperature == pytest.approx(calibrator.temperature)
    assert loaded.ece_before == pytest.approx(calibrator.ece_before)
    assert loaded.ece_after == pytest.approx(calibrator.ece_after)

    # On-disk payload stays small (1-parameter + ECE).
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) >= {"temperature", "ece_before", "ece_after"}


def test_calibrator_handles_tiny_input() -> None:
    pytest.importorskip("torch")
    logits = np.array([[1.0, 2.0]], dtype=np.float32)
    labels = np.array([1], dtype=np.int64)
    info = TemperatureCalibrator().fit(logits, labels)
    assert info["n_fit"] == 1
    assert info["converged"] is False


def _softmax(x: np.ndarray) -> np.ndarray:
    z = x - x.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)
