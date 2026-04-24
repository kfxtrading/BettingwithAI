"""Opening-odds + Kelly-mask extraction for CLV-aware deep-model training.

Phase A of [_plans/gpu_kelly_training_plan.md](../../../_plans/gpu_kelly_training_plan.md).

Companion to :func:`MLPPredictor.build_training_data`,
:func:`build_dataset` (sequence model) and
:func:`TabTransformerPredictor.build_training_data`. Produces the extra
arrays that the CLV-aligned Kelly training objective needs without
breaking the existing 3/6-tuple return contracts of those functions.

The walk order and ``warmup_games`` skip **must** match the companion
builders exactly so the returned arrays align row-for-row with the
training tensors (``sorted(matches, key=lambda m: m.date)`` + skip first
``warmup_games`` entries). If either builder ever changes ordering, this
module must change in lock-step — covered by regression tests.
"""

from __future__ import annotations

import numpy as np

from football_betting.data.models import Match


def collect_opening_odds_and_mask(
    matches: list[Match],
    warmup_games: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """Walk matches chronologically and collect opening-odds + Kelly-mask.

    Args:
        matches: Training matches. Re-sorted locally by ``date``.
        warmup_games: First N matches feed the trackers but yield no
            training row, same convention as the companion builders.

    Returns:
        opening: ``(N, 3)`` float32 array of ``(home, draw, away)`` opening
            odds. Rows without opening odds are filled with ``np.nan``.
        kelly_mask: ``(N,)`` bool array. ``True`` iff the row has all three
            opening odds present and strictly greater than 1.0 (needed for
            a well-defined Kelly fraction ``b = odds − 1 > 0``).

    Notes:
        ``N`` here equals ``max(0, len(matches) − warmup_games)``.
        Callers that need the matching closing odds or labels must obtain
        them from the companion builder so the warmup skip is done in one
        place per model.
    """
    matches_sorted = sorted(matches, key=lambda m: m.date)
    opening_rows: list[tuple[float, float, float]] = []
    mask_rows: list[bool] = []

    for idx, m in enumerate(matches_sorted):
        if idx < warmup_games:
            continue
        op = getattr(m, "opening_odds", None)
        if op is None:
            opening_rows.append((float("nan"), float("nan"), float("nan")))
            mask_rows.append(False)
            continue
        h, d, a = float(op.home), float(op.draw), float(op.away)
        valid = (
            np.isfinite(h) and h > 1.0 and np.isfinite(d) and d > 1.0 and np.isfinite(a) and a > 1.0
        )
        opening_rows.append((h, d, a))
        mask_rows.append(bool(valid))

    opening = (
        np.asarray(opening_rows, dtype=np.float32)
        if opening_rows
        else np.empty((0, 3), dtype=np.float32)
    )
    mask = np.asarray(mask_rows, dtype=bool)
    return opening, mask


def coverage(mask: np.ndarray) -> float:
    """Fraction of rows with a usable opening-odds triple.

    Safe on empty input (returns 0.0). Used by training loops to log
    per-league Kelly-mask coverage before scheduling a run — low coverage
    means the run is effectively a pure CE fit with a tiny Kelly-gradient
    sidecar, which is a signal to prioritise the opening-odds snapshot
    workflow (Phase 4 of the main optimisation roadmap) instead.
    """
    if mask.size == 0:
        return 0.0
    return float(mask.mean())
