"""GPU utilities — CPU fallback + seed reproducibility."""
from __future__ import annotations

import os

import numpy as np


def test_detect_gpu_force_cpu(monkeypatch):
    from football_betting.predict.gpu_utils import detect_gpu

    monkeypatch.setenv("FORCE_CPU", "1")
    assert detect_gpu() is False


def test_seed_everything_reproducible():
    from football_betting.predict.gpu_utils import seed_everything

    seed_everything(123)
    a = np.random.rand(5)
    seed_everything(123)
    b = np.random.rand(5)
    assert np.allclose(a, b)


def test_make_amp_scaler_returns_object_or_none():
    from football_betting.predict.gpu_utils import make_amp_scaler

    scaler = make_amp_scaler(enabled=False)
    # Either None (no torch) or a disabled scaler
    assert scaler is None or hasattr(scaler, "scale")


def test_detect_gpu_returns_bool():
    os.environ.pop("FORCE_CPU", None)
    from football_betting.predict.gpu_utils import detect_gpu

    assert isinstance(detect_gpu(), bool)
