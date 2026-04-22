"""Unit tests for the reproducibility helper (support/reproducibility.py)."""
from __future__ import annotations

import os
import random

import pytest

from football_betting.support.reproducibility import seed_all


def test_seed_all_returns_summary() -> None:
    info = seed_all(42)
    assert info["seed"] == 42
    assert info["python_hash_seed"] == "42"
    assert os.environ["PYTHONHASHSEED"] == "42"
    assert info["torch_available"] in (True, False)
    assert info["cuda_available"] in (True, False)


def test_seed_all_repro_python_rng() -> None:
    seed_all(123)
    a = [random.random() for _ in range(4)]
    seed_all(123)
    b = [random.random() for _ in range(4)]
    assert a == b


def test_seed_all_repro_numpy_rng() -> None:
    np = pytest.importorskip("numpy")
    seed_all(7)
    a = np.random.rand(4)
    seed_all(7)
    b = np.random.rand(4)
    assert (a == b).all()


def test_seed_all_rejects_negative() -> None:
    with pytest.raises(ValueError):
        seed_all(-1)
