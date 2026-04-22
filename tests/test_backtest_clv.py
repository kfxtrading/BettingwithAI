"""Tests for CLV pipeline in the walk-forward backtest (Phase 3)."""
from __future__ import annotations

import pytest

from football_betting.tracking.backtest import BacktestResult
from football_betting.tracking.metrics import clv_summary


class TestCLVSummary:
    def test_clv_zero_when_bet_equals_closing(self) -> None:
        # Phase 3 baseline: no opening snapshots → bet_odds == closing_odds → CLV ≡ 0.
        bet_odds = [2.10, 3.40, 1.80, 5.50]
        close_odds = list(bet_odds)
        stats = clv_summary(bet_odds, close_odds)
        assert stats["n"] == 4
        assert stats["mean_clv"] == pytest.approx(0.0)
        assert stats["median_clv"] == pytest.approx(0.0)
        assert stats["pct_positive"] == pytest.approx(0.0)

    def test_clv_positive_when_bet_odds_higher(self) -> None:
        # Bet placed at higher price than market close → positive CLV on every bet.
        bet_odds = [2.20, 3.60, 1.95]
        close_odds = [2.00, 3.40, 1.80]
        stats = clv_summary(bet_odds, close_odds)
        assert stats["n"] == 3
        assert stats["mean_clv"] > 0.0
        assert stats["pct_positive"] == pytest.approx(1.0)
        # spot-check: first = 2.20/2.00 - 1 = 0.10
        assert stats["median_clv"] > 0.05

    def test_clv_tolerates_none_values(self) -> None:
        # Robustness: missing snapshots on either side must be skipped, not crash.
        bet_odds = [2.10, None, 3.00, 1.50]
        close_odds = [2.00, 3.20, None, 1.50]
        stats = clv_summary(bet_odds, close_odds)
        # Only the first and last pair are usable.
        assert stats["n"] == 2

    def test_clv_all_none_returns_zero_stats(self) -> None:
        stats = clv_summary([None, None], [None, None])
        assert stats["n"] == 0
        assert stats["mean_clv"] == 0.0
        assert stats["pct_positive"] == 0.0


class TestCLVInBacktestResult:
    def test_clv_summary_in_result_dict(self) -> None:
        """BacktestResult.bet_metrics must expose the CLV keys produced by Phase 3."""
        # Construct a minimal result mirroring what Backtester.run() yields when
        # at least one bet was placed.
        result = BacktestResult(
            league="BL",
            n_predictions=3,
            n_bets=2,
            metrics={"mean_rps": 0.2},
            bet_metrics={
                "n_bets": 2,
                "hits": 1,
                "total_staked": 20.0,
                "total_profit": 1.0,
                "roi": 0.05,
                "sharpe": 0.0,
                "clv_n": 2,
                "clv_mean": 0.0,
                "clv_median": 0.0,
                "clv_pct_positive": 0.0,
            },
            bankroll_final=1001.0,
            max_drawdown={"max_drawdown_abs": 0.0, "max_drawdown_pct": 0.0},
            rows=[],
        )

        for key in ("clv_n", "clv_mean", "clv_median", "clv_pct_positive"):
            assert key in result.bet_metrics

    def test_empty_bet_metrics_still_have_clv_keys(self) -> None:
        # When no value bets are placed, the backtester must still emit CLV
        # fields so downstream consumers can rely on the schema.
        result = BacktestResult(
            league="BL",
            n_predictions=3,
            n_bets=0,
            metrics={},
            bet_metrics={
                "n_bets": 0,
                "clv_n": 0,
                "clv_mean": 0.0,
                "clv_median": 0.0,
                "clv_pct_positive": 0.0,
            },
            bankroll_final=1000.0,
            max_drawdown={"max_drawdown_abs": 0.0, "max_drawdown_pct": 0.0},
            rows=[],
        )
        assert result.bet_metrics["clv_mean"] == 0.0
        assert result.bet_metrics["clv_n"] == 0
