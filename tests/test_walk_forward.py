"""Tests for Phase 6: multi-fold walk-forward backtest."""
from __future__ import annotations

import pytest

from football_betting.tracking.backtest import (
    DEFAULT_WALK_FORWARD_FOLDS,
    BacktestResult,
    WalkForwardSummary,
    _aggregate_folds,
    _validate_folds,
)


class TestFoldValidation:
    def test_default_folds_have_no_leakage(self) -> None:
        _validate_folds(DEFAULT_WALK_FORWARD_FOLDS)

    def test_walk_forward_yields_n_folds(self) -> None:
        # 3 folds are defined in the plan.
        assert len(DEFAULT_WALK_FORWARD_FOLDS) == 3

    def test_walk_forward_no_train_test_leakage(self) -> None:
        for train_seasons, test_season in DEFAULT_WALK_FORWARD_FOLDS:
            assert max(train_seasons) < test_season, (
                f"Leakage: train max {max(train_seasons)} >= test {test_season}"
            )

    def test_validator_rejects_leakage(self) -> None:
        bad = ((("2023-24", "2024-25"), "2024-25"),)
        with pytest.raises(ValueError, match="leakage"):
            _validate_folds(bad)

    def test_validator_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="At least one fold"):
            _validate_folds(())

    def test_validator_rejects_empty_train(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            _validate_folds((((), "2024-25"),))


class TestAggregateFolds:
    def _mk_result(self, rps: float, roi: float, clv: float) -> BacktestResult:
        return BacktestResult(
            league="BL",
            n_predictions=10,
            n_bets=5,
            metrics={"mean_rps": rps, "mean_brier": 0.6, "mean_log_loss": 1.0, "hit_rate": 0.45, "n": 10},
            bet_metrics={
                "n_bets": 5, "hits": 2, "total_staked": 100.0, "total_profit": 5.0,
                "roi": roi, "sharpe": 0.1,
                "clv_n": 5, "clv_mean": clv, "clv_median": clv, "clv_pct_positive": 0.6,
            },
            bankroll_final=1005.0,
            max_drawdown={"max_drawdown_abs": 10.0, "max_drawdown_pct": 0.01},
            rows=[],
        )

    def test_aggregate_mean_std_min_max(self) -> None:
        folds = [
            self._mk_result(0.20, 0.05, 0.01),
            self._mk_result(0.22, 0.04, 0.02),
            self._mk_result(0.18, 0.06, 0.03),
        ]
        agg = _aggregate_folds(folds)
        assert "mean_rps" in agg and "roi" in agg and "clv_mean" in agg
        rps = agg["mean_rps"]
        assert rps["mean"] == pytest.approx(0.20, abs=1e-9)
        assert rps["min"] == pytest.approx(0.18)
        assert rps["max"] == pytest.approx(0.22)
        assert rps["n"] == 3
        assert rps["std"] > 0.0

    def test_aggregate_handles_single_fold_without_std_crash(self) -> None:
        agg = _aggregate_folds([self._mk_result(0.2, 0.05, 0.01)])
        assert agg["mean_rps"]["std"] == 0.0

    def test_summary_to_dict_roundtrips(self) -> None:
        folds = [self._mk_result(0.2, 0.05, 0.01)]
        agg = _aggregate_folds(folds)
        summary = WalkForwardSummary(league="BL", folds=folds, aggregate=agg)
        d = summary.to_dict()
        assert d["league"] == "BL"
        assert d["n_folds"] == 1
        assert "aggregate" in d and "folds" in d
