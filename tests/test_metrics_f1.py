"""Tests for f1_scores_3way and summary_stats F1 integration."""
from __future__ import annotations

import pytest

from football_betting.tracking.metrics import f1_scores_3way, summary_stats


def test_f1_perfect_predictions() -> None:
    preds = ["H", "D", "A", "H", "D", "A"]
    actuals = ["H", "D", "A", "H", "D", "A"]
    r = f1_scores_3way(preds, actuals)  # type: ignore[arg-type]
    assert r["macro_f1"] == pytest.approx(1.0)
    assert r["weighted_f1"] == pytest.approx(1.0)
    assert r["f1_H"] == pytest.approx(1.0)
    assert r["f1_D"] == pytest.approx(1.0)
    assert r["f1_A"] == pytest.approx(1.0)


def test_f1_all_wrong() -> None:
    preds = ["H", "H", "H"]
    actuals = ["D", "A", "D"]
    r = f1_scores_3way(preds, actuals)  # type: ignore[arg-type]
    assert r["macro_f1"] == pytest.approx(0.0)
    assert r["f1_H"] == pytest.approx(0.0)


def test_f1_known_values() -> None:
    # H: tp=2, fp=1, fn=0 -> p=2/3, r=1,   f1 = 2*(2/3)/(5/3) = 4/5 = 0.8
    # D: tp=1, fp=1, fn=1 -> p=0.5, r=0.5, f1 = 0.5
    # A: tp=1, fp=0, fn=1 -> p=1,   r=0.5, f1 = 2/3
    preds = ["H", "H", "H", "D", "D", "A"]
    actuals = ["H", "H", "D", "D", "A", "A"]
    r = f1_scores_3way(preds, actuals)  # type: ignore[arg-type]
    assert r["precision_H"] == pytest.approx(2 / 3)
    assert r["recall_H"] == pytest.approx(1.0)
    assert r["f1_H"] == pytest.approx(0.8)
    assert r["f1_D"] == pytest.approx(0.5)
    assert r["f1_A"] == pytest.approx(2 / 3)
    assert r["support_H"] == pytest.approx(2.0)
    assert r["support_D"] == pytest.approx(2.0)
    assert r["support_A"] == pytest.approx(2.0)
    assert r["macro_f1"] == pytest.approx((0.8 + 0.5 + 2 / 3) / 3)
    # equal support -> weighted == macro
    assert r["weighted_f1"] == pytest.approx(r["macro_f1"])


def test_f1_empty() -> None:
    r = f1_scores_3way([], [])
    assert r["macro_f1"] == 0.0
    assert r["weighted_f1"] == 0.0


def test_f1_length_mismatch() -> None:
    with pytest.raises(ValueError):
        f1_scores_3way(["H"], ["H", "D"])  # type: ignore[arg-type]


def test_summary_stats_includes_f1() -> None:
    preds = [
        ((0.7, 0.2, 0.1), "H"),
        ((0.2, 0.6, 0.2), "D"),
        ((0.1, 0.3, 0.6), "A"),
        ((0.5, 0.3, 0.2), "D"),
    ]
    s = summary_stats(preds)  # type: ignore[arg-type]
    assert "macro_f1" in s
    assert "weighted_f1" in s
    assert "f1_draw" in s
    assert "precision_draw" in s
    assert "recall_draw" in s
    assert 0.0 <= s["macro_f1"] <= 1.0
