"""Tests for ``resolve_device`` (DirectML / CUDA / CPU fallback)."""

from __future__ import annotations

import sys
import types

import pytest

torch = pytest.importorskip("torch")

from football_betting.predict import gpu_utils
from football_betting.predict.gpu_utils import resolve_device


def test_resolve_device_force_cpu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORCE_CPU", "1")
    dev, backend = resolve_device("auto")
    assert backend == "cpu"
    assert dev.type == "cpu"


def test_resolve_device_explicit_cpu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORCE_CPU", raising=False)
    dev, backend = resolve_device("cpu")
    assert backend == "cpu"
    assert dev.type == "cpu"


def test_resolve_device_cuda_requested_but_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FORCE_CPU", raising=False)
    monkeypatch.setattr(gpu_utils, "detect_gpu", lambda: False)
    with pytest.warns(UserWarning, match="CUDA"):
        dev, backend = resolve_device("cuda")
    assert backend == "cpu"


def test_resolve_device_dml_requested_but_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FORCE_CPU", raising=False)
    monkeypatch.setattr(gpu_utils, "_detect_directml", lambda: False)
    with pytest.warns(UserWarning, match="DirectML"):
        dev, backend = resolve_device("dml")
    assert backend == "cpu"


def test_resolve_device_auto_prefers_cuda_over_dml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FORCE_CPU", raising=False)
    monkeypatch.setattr(gpu_utils, "detect_gpu", lambda: True)
    monkeypatch.setattr(gpu_utils, "_detect_directml", lambda: True)
    _dev, backend = resolve_device("auto")
    assert backend == "cuda"


def test_resolve_device_auto_uses_dml_when_cuda_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When CUDA is missing but ``torch_directml`` is mocked in, auto → dml."""
    monkeypatch.delenv("FORCE_CPU", raising=False)
    monkeypatch.setattr(gpu_utils, "detect_gpu", lambda: False)

    # Inject a fake torch_directml module
    fake = types.ModuleType("torch_directml")
    sentinel = torch.device("cpu")  # any torch.device works for the assertion
    fake.device_count = lambda: 1  # type: ignore[attr-defined]
    fake.device = lambda: sentinel  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch_directml", fake)
    monkeypatch.setattr(gpu_utils, "_detect_directml", lambda: True)

    dev, backend = resolve_device("auto")
    assert backend == "dml"
    assert dev is sentinel
