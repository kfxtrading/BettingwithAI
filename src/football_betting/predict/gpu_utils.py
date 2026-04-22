"""GPU detection + reproducibility helpers."""
from __future__ import annotations

import os
import random
from typing import Any

import numpy as np


def detect_gpu() -> bool:
    """Return True iff a usable CUDA device is available via torch."""
    if os.environ.get("FORCE_CPU") == "1":
        return False
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


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
