"""StackingEnsemble — meta-feature shape, LR fit, uniform fallback."""
from __future__ import annotations

import math

import numpy as np
import pytest

from football_betting.config import StackingConfig
from football_betting.predict.stacking import (
    N_META_FEATURES,
    StackingEnsemble,
    build_meta_row,
)


def test_meta_row_has_19_features():
    row = build_meta_row(
        (0.5, 0.3, 0.2), (0.4, 0.3, 0.3), (0.6, 0.2, 0.2), (0.5, 0.25, 0.25),
        (2.0, 3.5, 4.0),
    )
    assert row.shape == (N_META_FEATURES,)
    assert N_META_FEATURES == 19


def test_meta_row_uniform_fallback_for_missing_members():
    row = build_meta_row(
        (0.5, 0.3, 0.2), (0.4, 0.3, 0.3), None, None, (2.0, 3.5, 4.0),
    )
    assert row.shape == (19,)
    # missing MLP member → probs at indices 6..8 are uniform 1/3
    assert math.isclose(row[6], 1.0 / 3.0, rel_tol=1e-5)
    assert math.isclose(row[7], 1.0 / 3.0, rel_tol=1e-5)
    assert math.isclose(row[8], 1.0 / 3.0, rel_tol=1e-5)


def test_meta_row_missing_odds_uses_uniform_market():
    row = build_meta_row((0.5, 0.3, 0.2), None, None, None, None)
    # last 3 entries are market probs → uniform
    assert math.isclose(row[-1], 1.0 / 3.0, rel_tol=1e-5)
    assert math.isclose(row[-2], 1.0 / 3.0, rel_tol=1e-5)
    assert math.isclose(row[-3], 1.0 / 3.0, rel_tol=1e-5)


def test_stacking_fit_lr():
    rng = np.random.default_rng(0)
    x_meta = rng.random((80, N_META_FEATURES), dtype=np.float32)
    y = rng.integers(0, 3, size=80)
    ens = StackingEnsemble(cfg=StackingConfig(meta_learner="lr"))
    ens.fit(x_meta, y)
    probs = ens.predict_proba(x_meta[:5])
    assert probs.shape == (5, 3)
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-4)


def test_stacking_rejects_wrong_feature_count():
    ens = StackingEnsemble()
    x_bad = np.zeros((10, 5), dtype=np.float32)
    y = np.zeros(10, dtype=np.int64)
    with pytest.raises(ValueError):
        ens.fit(x_bad, y)
