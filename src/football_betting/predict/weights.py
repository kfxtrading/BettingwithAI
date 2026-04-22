"""Time-decay sample weighting for training data.

Older seasons receive exponentially smaller weights so the model prioritises
recent regime behaviour (rule changes, tactical trends, post-COVID normal).

Usage::

    from football_betting.predict.weights import season_decay_weights
    w = season_decay_weights(seasons, ref_season="2024-25", decay=0.85)
    model.fit(X, y, sample_weight=w)
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def _season_to_int(season: str) -> int:
    """Return the starting year of a ``YYYY-YY`` or ``YYYY`` season string."""
    if not season:
        raise ValueError("Empty season string")
    head = season.split("-", 1)[0]
    return int(head)


def season_decay_weights(
    seasons: Sequence[str],
    ref_season: str,
    decay: float = 0.85,
    min_weight: float = 0.1,
    max_weight: float = 1.0,
) -> np.ndarray:
    """Inverse-distance exponential decay over seasons.

    ``w_s = decay ** (ref_idx - s_idx)``, then clipped to ``[min_weight, max_weight]``.

    Parameters
    ----------
    seasons:
        Iterable of season labels, one per training sample (e.g. ``"2023-24"``).
    ref_season:
        Target season (newest). Its samples receive weight 1.0.
    decay:
        Per-season decay factor in ``(0, 1]``. ``1.0`` disables decay.
    min_weight, max_weight:
        Clipping bounds applied *after* decay computation.
    """
    if not 0.0 < decay <= 1.0:
        raise ValueError("decay must be in (0, 1]")
    if min_weight < 0 or max_weight <= 0 or min_weight > max_weight:
        raise ValueError("invalid weight bounds")

    ref_idx = _season_to_int(ref_season)
    weights = np.empty(len(seasons), dtype=np.float64)
    for i, s in enumerate(seasons):
        delta = ref_idx - _season_to_int(s)
        if delta < 0:
            # Future seasons (shouldn't happen) get full weight
            delta = 0
        weights[i] = decay**delta
    return np.clip(weights, min_weight, max_weight)
