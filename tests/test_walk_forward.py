"""Tests for Phase 6: multi-fold walk-forward backtest."""
from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("rich")
pytest.importorskip("catboost")

from football_betting.config import BacktestConfig
from football_betting.data.models import Match, MatchOdds, Prediction
from football_betting.predict.runtime import LeagueModelProfile
from football_betting.tracking.backtest import (
    DEFAULT_WALK_FORWARD_FOLDS,
    Backtester,
    BacktestResult,
    ModelBundle,
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
            metrics={
                "mean_rps": rps,
                "mean_brier": 0.6,
                "mean_log_loss": 1.0,
                "ece": 0.01,
                "hit_rate": 0.45,
                "n": 10,
            },
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


class _StaticPredictor:
    def __init__(self, probs: tuple[float, float, float], name: str) -> None:
        self.probs = probs
        self.name = name

    def predict(self, fixture) -> Prediction:  # noqa: ANN001
        return Prediction(
            fixture=fixture,
            model_name=self.name,
            prob_home=self.probs[0],
            prob_draw=self.probs[1],
            prob_away=self.probs[2],
        )


def test_backtester_uses_dedicated_value_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    train_matches = [
        Match(
            date=date(2024, 1, 1),
            league="BL",
            season="2023-24",
            home_team="A",
            away_team="B",
            home_goals=1,
            away_goals=0,
            odds=MatchOdds(home=2.10, draw=3.40, away=3.60),
        ),
        Match(
            date=date(2024, 1, 8),
            league="BL",
            season="2023-24",
            home_team="C",
            away_team="D",
            home_goals=0,
            away_goals=0,
            odds=MatchOdds(home=2.40, draw=3.20, away=3.10),
        ),
    ]
    test_matches = [
        Match(
            date=date(2024, 5, 1),
            league="BL",
            season="2024-25",
            home_team="Home",
            away_team="Away",
            home_goals=1,
            away_goals=0,
            odds=MatchOdds(home=2.60, draw=3.40, away=3.60),
            opening_odds=MatchOdds(home=2.50, draw=3.50, away=3.70),
        )
    ]

    def fake_load_league(_league: str, seasons: list[str] | None = None):  # noqa: ANN001
        if seasons == ["2024-25"]:
            return test_matches
        return train_matches

    monkeypatch.setattr("football_betting.tracking.backtest.load_league", fake_load_league)
    monkeypatch.setattr(
        "football_betting.tracking.backtest.merge_snapshots_into_matches",
        lambda matches, _league: matches,
    )

    def fake_train_bundle(self, league_key: str, train_matches_arg, purpose: str) -> ModelBundle:  # noqa: ANN001
        profile = LeagueModelProfile(
            league_key=league_key,
            purpose=purpose,  # type: ignore[arg-type]
            model_kind="catboost",
            active_members=("catboost",),
        )
        if purpose == "1x2":
            predictor = _StaticPredictor((0.34, 0.33, 0.33), "pred-1x2")
        else:
            predictor = _StaticPredictor((0.55, 0.25, 0.20), "pred-value")
        return ModelBundle(purpose=purpose, profile=profile, model=predictor)

    monkeypatch.setattr(Backtester, "_train_bundle", fake_train_bundle)

    backtester = Backtester(
        cfg=BacktestConfig(train_seasons=("2023-24",), test_season="2024-25", min_train_games=1),
        use_ensemble=False,
    )
    result = backtester.run("BL")

    assert result.n_bets == 1
    assert result.rows[0]["model_name"] == "pred-1x2"
    assert result.rows[0]["value_model_name"] == "pred-value"
    assert result.rows[0]["value_prob_home"] == pytest.approx(0.55)
    assert result.rows[0]["opening_odds_home"] == pytest.approx(2.50)
    assert result.rows[0]["opening_odds_draw"] == pytest.approx(3.50)
    assert result.rows[0]["opening_odds_away"] == pytest.approx(3.70)
    assert result.bet_metrics["roi"] > 0.0
