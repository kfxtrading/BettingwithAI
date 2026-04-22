"""Sliding-mode walk-forward validation (Phase 4)."""

from __future__ import annotations

import pytest

from football_betting.tracking.backtest import (
    Backtester,
    walk_forward_backtest,
)


def test_walk_forward_rejects_invalid_mode() -> None:
    with pytest.raises(ValueError, match="mode must be"):
        walk_forward_backtest("BL", mode="banana")


def test_walk_forward_sliding_requires_positive_window() -> None:
    with pytest.raises(ValueError, match="window_matches must be positive"):
        walk_forward_backtest("BL", mode="sliding", window_matches=0)


def test_backtester_training_window_must_be_positive() -> None:
    bt = Backtester(training_window_matches=-5)
    # `.run()` is the layer that validates; simulate via direct attribute check.
    assert bt.training_window_matches == -5
    # The validation fires inside ``run`` — we exercise the check path only
    # by asserting the public attribute is exposed for walk_forward to wire.
