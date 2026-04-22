"""Tests for predict.weights (time-decay sample weighting)."""
from __future__ import annotations

import numpy as np
import pytest

from football_betting.predict.weights import season_decay_weights


class TestSeasonDecayWeights:
    def test_ref_season_weight_is_one(self) -> None:
        w = season_decay_weights(
            ["2024-25", "2023-24", "2022-23"], ref_season="2024-25", decay=0.85
        )
        assert w[0] == pytest.approx(1.0)

    def test_monotonic_in_recency(self) -> None:
        w = season_decay_weights(
            ["2021-22", "2022-23", "2023-24", "2024-25"],
            ref_season="2024-25",
            decay=0.85,
        )
        # Older seasons must have smaller weight
        assert w[0] < w[1] < w[2] < w[3]

    def test_decay_formula(self) -> None:
        w = season_decay_weights(
            ["2024-25", "2023-24", "2022-23", "2021-22"],
            ref_season="2024-25",
            decay=0.85,
        )
        assert w[0] == pytest.approx(1.0)
        assert w[1] == pytest.approx(0.85)
        assert w[2] == pytest.approx(0.85**2)
        assert w[3] == pytest.approx(0.85**3)

    def test_decay_one_gives_uniform_weights(self) -> None:
        w = season_decay_weights(
            ["2019-20", "2020-21", "2024-25"], ref_season="2024-25", decay=1.0
        )
        assert np.allclose(w, 1.0)

    def test_min_weight_clip(self) -> None:
        # 0.5**20 ≈ 1e-6 — should be clipped to 0.1
        w = season_decay_weights(
            ["2004-05"], ref_season="2024-25", decay=0.5, min_weight=0.1
        )
        assert w[0] == pytest.approx(0.1)

    def test_future_season_treated_as_ref(self) -> None:
        # ref_season older than sample → clamped to Δ=0 → weight = 1.0
        w = season_decay_weights(["2025-26"], ref_season="2024-25", decay=0.85)
        assert w[0] == pytest.approx(1.0)

    def test_invalid_decay_raises(self) -> None:
        with pytest.raises(ValueError):
            season_decay_weights(["2024-25"], ref_season="2024-25", decay=0.0)
        with pytest.raises(ValueError):
            season_decay_weights(["2024-25"], ref_season="2024-25", decay=1.5)

    def test_empty_seasons(self) -> None:
        w = season_decay_weights([], ref_season="2024-25", decay=0.85)
        assert w.shape == (0,)

    def test_single_year_season_label(self) -> None:
        # Also supports "2024" style labels (non-hyphenated)
        w = season_decay_weights(
            ["2023", "2024"], ref_season="2024", decay=0.9
        )
        assert w[0] == pytest.approx(0.9)
        assert w[1] == pytest.approx(1.0)
