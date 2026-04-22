"""Reproducibility helpers for the support intent stack (M3).

Python / NumPy / torch RNG seeding. `cudnn.deterministic` is only enabled
when running on CUDA — torch-directml and CPU do not honour those flags
and (for DML) are not bit-deterministic anyway. That limitation is
surfaced via the return dict for inclusion in the metrics report.
"""
from __future__ import annotations

import os
import random
from typing import Any


def seed_all(seed: int) -> dict[str, Any]:
    """Seed Python/NumPy/torch RNGs and return a small summary.

    Parameters
    ----------
    seed:
        Integer seed (non-negative). Use e.g. 42 for reproducible training.

    Returns
    -------
    dict with keys ``{"seed", "python_hash_seed", "cudnn_deterministic",
    "torch_available", "cuda_available"}``. The last three describe the
    level of determinism actually achieved on this host.
    """
    if seed < 0:
        raise ValueError(f"seed must be non-negative, got {seed}")

    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    info: dict[str, Any] = {
        "seed": int(seed),
        "python_hash_seed": str(seed),
        "cudnn_deterministic": False,
        "torch_available": False,
        "cuda_available": False,
    }

    try:
        import numpy as np

        np.random.seed(seed)
    except Exception:  # noqa: BLE001 — NumPy absence is tolerated
        pass

    try:
        import torch  # type: ignore[import-not-found]

        info["torch_available"] = True
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            info["cuda_available"] = True
            torch.cuda.manual_seed_all(seed)
            try:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
                info["cudnn_deterministic"] = True
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001 — torch is optional for some entry points
        pass

    return info


__all__ = ["seed_all"]
