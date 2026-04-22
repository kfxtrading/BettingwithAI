"""GPU detection + reproducibility helpers.

v0.4: adds ``resolve_device`` that prefers CUDA, then DirectML (AMD/Intel
on Windows via ``torch-directml``), then CPU. CatBoost GPU remains CUDA-
only; only the Torch-based models can use DirectML.
"""

from __future__ import annotations

import os
import random
from typing import Any, Literal

import numpy as np

DevicePreference = Literal["auto", "cuda", "dml", "cpu"]


def detect_gpu() -> bool:
    """Return True iff a usable CUDA device is available via torch."""
    if os.environ.get("FORCE_CPU") == "1":
        return False
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _detect_directml() -> bool:
    """Return True iff ``torch_directml`` is importable and reports a device."""
    if os.environ.get("FORCE_CPU") == "1":
        return False
    try:
        import torch_directml  # type: ignore[import-not-found]

        return torch_directml.device_count() > 0
    except Exception:
        return False


def resolve_device(preference: DevicePreference = "auto") -> tuple[Any, str]:
    """Return ``(torch.device, backend_name)``.

    Precedence when ``preference='auto'``:
        1. CUDA if available
        2. DirectML if ``torch-directml`` is installed and exposes a device
        3. CPU

    ``preference`` can be forced to ``'cuda'``, ``'dml'`` or ``'cpu'``. If the
    requested backend is unavailable the function falls back to the next
    available tier and emits a warning via ``warnings.warn``.
    """
    import warnings

    import torch

    force_cpu = os.environ.get("FORCE_CPU") == "1"
    if force_cpu:
        return torch.device("cpu"), "cpu"

    if preference == "cpu":
        return torch.device("cpu"), "cpu"

    want_cuda = preference in ("auto", "cuda")
    want_dml = preference in ("auto", "dml")

    if want_cuda and detect_gpu():
        return torch.device("cuda"), "cuda"
    if preference == "cuda":
        warnings.warn("CUDA requested but unavailable — falling back to CPU.", stacklevel=2)
        return torch.device("cpu"), "cpu"

    if want_dml and _detect_directml():
        import torch_directml  # type: ignore[import-not-found]

        return torch_directml.device(), "dml"
    if preference == "dml":
        warnings.warn("DirectML requested but unavailable — falling back to CPU.", stacklevel=2)
        return torch.device("cpu"), "cpu"

    return torch.device("cpu"), "cpu"


def seed_everything(seed: int = 42) -> None:
    """Make Python / NumPy / PyTorch reproducible (bitwise-deterministic on CPU)."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except Exception:
        pass


def make_amp_scaler(enabled: bool = True) -> Any:
    """Return a ``torch.cuda.amp.GradScaler`` (disabled if AMP off / no CUDA)."""
    try:
        import torch

        use = enabled and torch.cuda.is_available()
        return torch.cuda.amp.GradScaler(enabled=use)
    except Exception:
        return None
