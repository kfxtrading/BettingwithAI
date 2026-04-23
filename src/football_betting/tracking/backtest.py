"""
Walk-forward backtesting engine.

Trains on historical seasons, predicts the test season match-by-match
in chronological order. After each matchday the feature trackers are
updated with actual results — this mirrors the real-time pipeline
without retraining the CatBoost model between matchdays.

Outputs:
* Match-level predictions + actuals
* Aggregate probabilistic metrics (RPS, Brier, log-loss)
* Financial simulation: if value bets were placed, bankroll curve
* CSV + JSON dumps for further analysis
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress

from football_betting.betting.value import find_value_bets
from football_betting.config import (
    BACKTEST_CFG,
    BACKTEST_DIR,
    BETTING_CFG,
    LEAGUES,
    STACKING_CFG,
    BacktestConfig,
    BettingConfig,
    CalibrationConfig,
    ModelPurpose,
    StackingConfig,
)
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture, Match, Prediction
from football_betting.data.snapshot_service import merge_snapshots_into_matches
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.predict.runtime import (
    LeagueModelProfile,
    betting_config_from_profile,
    make_feature_builder,
    mlp_config_for_purpose,
    normalize_active_members,
    resolve_model_profile,
    sequence_config_for_purpose,
    stage_sofascore_for_seasons,
)
from football_betting.predict.sequence_model import SequencePredictor

# EnsembleModel is lazy-imported inside run() to break circular dep
# (ensemble.py → tracking.metrics → tracking/__init__.py → backtest.py → ensemble)
from football_betting.tracking.metrics import (
    bankroll_curve,
    clv_summary,
    max_drawdown,
    sharpe_ratio,
    summary_stats,
)
from football_betting.tracking.metrics import (
    roi as calc_roi,
)

console = Console()


@dataclass(slots=True)
class ModelBundle:
    """Runtime bundle for one purpose-specific backtest model family."""

    purpose: ModelPurpose
    profile: LeagueModelProfile
    feature_builder: FeatureBuilder | None = None
    catboost: CatBoostPredictor | None = None
    poisson: PoissonModel | None = None
    mlp: MLPPredictor | None = None
    sequence: SequencePredictor | None = None
    stacking: Any = None
    model: Any = None

    def predict(self, fixture: Fixture) -> Prediction:
        if self.stacking is not None:
            cb_probs = self.catboost.predict(fixture).as_tuple() if self.catboost is not None else None
            po_probs = self.poisson.predict(fixture).as_tuple() if self.poisson is not None else None
            mlp_probs = self.mlp.predict(fixture).as_tuple() if self.mlp is not None else None
            seq_probs = self.sequence.predict(fixture).as_tuple() if self.sequence is not None else None
            return self.stacking.predict_one(fixture, cb_probs, po_probs, mlp_probs, seq_probs)
        if self.model is None:
            raise RuntimeError(f"No model available for purpose={self.purpose}")
        return self.model.predict(fixture)

    def update_with_match(self, match: Match) -> None:
        if self.feature_builder is not None:
            self.feature_builder.update_with_match(match)
        if self.mlp is not None and self.mlp.feature_builder is not self.feature_builder:
            self.mlp.feature_builder.update_with_match(match)
        if self.sequence is not None:
            self.sequence.form_tracker.update(match)
            self.sequence.pi_ratings.update(match)


@dataclass(slots=True)
class BacktestResult:
    """Aggregate result from a walk-forward backtest."""

    league: str
    n_predictions: int
    n_bets: int
    metrics: dict[str, float]
    bet_metrics: dict[str, float]
    bankroll_final: float
    max_drawdown: dict[str, float]
    rows: list[dict[str, object]]
    profile_1x2: dict[str, object] | None = None
    profile_value: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def save(self, outdir: Path | None = None) -> Path:
        outdir = outdir or BACKTEST_DIR
        path = outdir / f"backtest_{self.league}.json"
        with path.open("w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        return path

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


@dataclass(slots=True)
class Backtester:
    """Walk-forward backtester.

    ``training_window_matches`` (Phase 4 sliding mode): when set, the
    trailing N matches of the train set are kept — older matches are
    dropped before fitting. ``None`` (default) keeps the full training
    window (expanding behaviour).
    """

    cfg: BacktestConfig = field(default_factory=lambda: BACKTEST_CFG)
    bet_cfg: BettingConfig = field(default_factory=lambda: BETTING_CFG)
    initial_bankroll: float = 1000.0
    use_ensemble: bool = True
    use_stacking: bool = False
    stacking_cfg: StackingConfig = field(default_factory=lambda: STACKING_CFG)
    training_window_matches: int | None = None
    #: Optional override of the CatBoost calibration method
    #: (``"auto"`` | ``"isotonic"`` | ``"sigmoid"``). When ``None`` the
    #: default from :class:`CalibrationConfig` is used.
    calibration_method: str | None = None
    profile_1x2: LeagueModelProfile | None = None
    profile_value: LeagueModelProfile | None = None

    def _resolve_profile(self, league_key: str, purpose: ModelPurpose) -> LeagueModelProfile:
        override = self.profile_value if purpose == "value" else self.profile_1x2
        resolved = override or resolve_model_profile(league_key, purpose)
        effective_stacking = bool((resolved.stacking if resolved is not None else False) or self.use_stacking)
        if resolved is None:
            active = ("catboost", "poisson") if self.use_ensemble else ("catboost",)
            return LeagueModelProfile(
                league_key=league_key,
                purpose=purpose,
                model_kind="ensemble" if len(active) > 1 else "catboost",
                active_members=active,
                stacking=effective_stacking,
            )
        if not self.use_ensemble:
            if resolved.model_kind == "poisson" or resolved.active_members == ("poisson",):
                return replace(resolved, model_kind="poisson", active_members=("poisson",), stacking=False)
            return replace(resolved, model_kind="catboost", active_members=("catboost",), stacking=effective_stacking)
        if resolved.model_kind == "poisson" or resolved.active_members == ("poisson",):
            return replace(resolved, model_kind="poisson", active_members=("poisson",), stacking=False)
        if resolved.active_members == ("catboost",):
            return replace(resolved, model_kind="catboost", active_members=("catboost",), stacking=effective_stacking)
        requested = set(resolved.active_members)
        requested.update({"catboost", "poisson"})
        active = normalize_active_members(
            [name for name in ("catboost", "poisson", "mlp", "sequence") if name in requested]
        )
        return replace(resolved, model_kind="ensemble", active_members=active, stacking=effective_stacking)

    def _fit_stacking(self, bundle: ModelBundle, stack_val_matches: list[Match]) -> None:
        from football_betting.predict.stacking import StackingEnsemble, build_meta_row

        if not stack_val_matches or bundle.catboost is None:
            return

        meta_rows: list[np.ndarray] = []
        meta_labels: list[int] = []
        for match in stack_val_matches:
            fixture = self._fixture_from_match(match)
            cb_probs = bundle.catboost.predict(fixture).as_tuple()
            po_probs = bundle.poisson.predict(fixture).as_tuple() if bundle.poisson is not None else None
            mlp_probs = bundle.mlp.predict(fixture).as_tuple() if bundle.mlp is not None else None
            seq_probs = bundle.sequence.predict(fixture).as_tuple() if bundle.sequence is not None else None
            odds_t = (match.odds.home, match.odds.draw, match.odds.away) if match.odds else None
            meta_rows.append(build_meta_row(cb_probs, po_probs, mlp_probs, seq_probs, odds_t))
            meta_labels.append({"H": 0, "D": 1, "A": 2}[match.result])
            bundle.update_with_match(match)

        if not meta_rows:
            return

        stacking = StackingEnsemble(cfg=self.stacking_cfg)
        stacking.fit(np.vstack(meta_rows), np.asarray(meta_labels, dtype=np.int64))
        bundle.stacking = stacking
        console.log(
            f"[cyan]{bundle.purpose} stacking fitted on {len(meta_labels)} OOF rows "
            f"(learner={self.stacking_cfg.meta_learner})[/cyan]"
        )

    def _train_bundle(self, league_key: str, train_matches: list[Match], purpose: ModelPurpose) -> ModelBundle:
        profile = self._resolve_profile(league_key, purpose)
        seasons = sorted({match.season for match in train_matches})

        if profile.model_kind == "poisson":
            feature_builder = make_feature_builder(purpose)
            stage_sofascore_for_seasons(feature_builder, league_key, seasons)
            feature_builder.fit_on_history(train_matches)
            poisson = PoissonModel(pi_ratings=feature_builder.pi_ratings)
            return ModelBundle(
                purpose=purpose,
                profile=replace(profile, active_members=("poisson",), model_kind="poisson"),
                feature_builder=feature_builder,
                poisson=poisson,
                model=poisson,
            )

        calibration_method = self.calibration_method or profile.calibration_method
        calibration_cfg = (
            CalibrationConfig(method=calibration_method) if calibration_method is not None else None
        )

        feature_builder = make_feature_builder(purpose)
        staged = stage_sofascore_for_seasons(feature_builder, league_key, seasons)
        if staged > 0:
            console.log(f"[green]{purpose} Sofascore staged: {staged} matches[/green]")

        fit_matches = train_matches
        stack_val_matches: list[Match] = []
        if profile.stacking:
            train_sorted = sorted(train_matches, key=lambda match: match.date)
            split = int(len(train_sorted) * self.stacking_cfg.inner_train_fraction)
            fit_matches = train_sorted[:split]
            stack_val_matches = train_sorted[split:]
            if fit_matches and stack_val_matches:
                assert max(match.date for match in fit_matches) <= min(
                    match.date for match in stack_val_matches
                ), "Stacking leakage: inner_train/stack_val overlap"
                console.log(
                    f"{purpose} stacking inner-split: train={len(fit_matches)} "
                    f"stack_val={len(stack_val_matches)}"
                )

        catboost = CatBoostPredictor(
            feature_builder=feature_builder,
            calibration_cfg=calibration_cfg,
            purpose=purpose,
        )
        training_info = catboost.fit(fit_matches, warmup_games=100, val_fraction=0.15, calibrate=True)
        console.log(
            f"{purpose} training complete: {training_info['n_train']} samples, "
            f"{training_info['n_features']} features"
        )
        poisson = PoissonModel(pi_ratings=feature_builder.pi_ratings)

        active_requested = list(profile.active_members)

        mlp = None
        if "mlp" in active_requested:
            try:
                mlp_builder = make_feature_builder(purpose)
                stage_sofascore_for_seasons(mlp_builder, league_key, seasons)
                mlp = MLPPredictor(
                    feature_builder=mlp_builder,
                    cfg=mlp_config_for_purpose(purpose),
                    purpose=purpose,
                )
                mlp.fit(fit_matches, warmup_games=100)
            except Exception as exc:  # pragma: no cover - optional member fallback
                console.log(f"[yellow]{purpose} MLP dropped during backtest: {exc}[/yellow]")
                active_requested.remove("mlp")

        sequence = None
        if "sequence" in active_requested:
            try:
                sequence = SequencePredictor(
                    cfg=sequence_config_for_purpose(purpose),
                    purpose=purpose,
                )
                sequence.fit(fit_matches, warmup_games=100)
            except Exception as exc:  # pragma: no cover - optional member fallback
                console.log(f"[yellow]{purpose} Sequence dropped during backtest: {exc}[/yellow]")
                active_requested.remove("sequence")

        if profile.model_kind == "catboost":
            active_members = ("catboost",)
        else:
            requested = set(active_requested)
            requested.update({"catboost", "poisson"})
            available = {
                "catboost": True,
                "poisson": True,
                "mlp": mlp is not None,
                "sequence": sequence is not None,
            }
            active_members = normalize_active_members(
                [
                    name
                    for name in ("catboost", "poisson", "mlp", "sequence")
                    if name in requested and available[name]
                ]
            )

        effective_profile = replace(
            profile,
            active_members=active_members,
            model_kind="ensemble" if len(active_members) > 1 else "catboost",
            calibration_method=(
                calibration_method
                or (catboost.calibrator.cfg.method if catboost.calibrator is not None else None)
            ),
        )

        bundle = ModelBundle(
            purpose=purpose,
            profile=effective_profile,
            feature_builder=feature_builder,
            catboost=catboost,
            poisson=poisson,
            mlp=mlp,
            sequence=sequence,
        )

        if effective_profile.stacking and stack_val_matches:
            self._fit_stacking(bundle, stack_val_matches)

        if active_members == ("catboost",):
            bundle.model = catboost
            return bundle

        from football_betting.predict.ensemble import EnsembleModel, ensemble_weights_path

        ensemble = EnsembleModel(
            catboost=catboost,
            poisson=poisson,
            mlp=mlp if "mlp" in active_members else None,
            sequence=sequence if "sequence" in active_members else None,
        )
        weights_path = ensemble_weights_path(league_key, purpose)
        if weights_path.exists():
            try:
                ensemble.load_weights(
                    weights_path,
                    expected_purpose=purpose,
                    expected_active_members=active_members,
                    expected_objective=effective_profile.weight_objective,
                    expected_calibration_method=effective_profile.calibration_method,
                )
                console.log(f"[green]Loaded {purpose} weights: {weights_path.name}[/green]")
            except Exception as exc:  # pragma: no cover - defensive
                console.log(f"[yellow]Skipped {purpose} weights {weights_path.name}: {exc}[/yellow]")

        bundle.model = ensemble
        return bundle

    # ───────────────────────── Core loop ─────────────────────────

    def run(self, league_key: str) -> BacktestResult:
        """Run backtest for one league."""
        console.rule(f"[bold cyan]Backtest — {LEAGUES[league_key].name}[/bold cyan]")

        train_matches = load_league(league_key, seasons=list(self.cfg.train_seasons))
        test_matches = load_league(league_key, seasons=[self.cfg.test_season])
        test_matches = merge_snapshots_into_matches(test_matches, league_key)

        if len(train_matches) < self.cfg.min_train_games:
            raise ValueError(
                f"Too few training matches ({len(train_matches)} < {self.cfg.min_train_games})"
            )

        if self.training_window_matches is not None:
            if self.training_window_matches <= 0:
                raise ValueError("training_window_matches must be positive")
            train_matches = sorted(train_matches, key=lambda match: match.date)[
                -self.training_window_matches :
            ]
            console.log(
                f"[yellow]Sliding window: training on last "
                f"{len(train_matches)} matches only[/yellow]"
            )

        console.log(f"Train: {len(train_matches)} matches ({self.cfg.train_seasons})")
        console.log(f"Test:  {len(test_matches)} matches ({self.cfg.test_season})")

        prediction_bundle = self._train_bundle(league_key, train_matches, "1x2")
        value_bundle = self._train_bundle(league_key, train_matches, "value")
        value_bet_cfg = betting_config_from_profile(value_bundle.profile, self.bet_cfg)

        rows: list[dict[str, object]] = []
        bet_records: list[dict[str, object]] = []
        predictions_for_metrics: list[tuple[tuple[float, float, float], str]] = []

        bankroll = self.initial_bankroll
        test_matches_sorted = sorted(test_matches, key=lambda match: match.date)

        with Progress(console=console) as progress:
            task = progress.add_task(f"Backtest {league_key}", total=len(test_matches_sorted))
            for match in test_matches_sorted:
                fixture = self._fixture_from_match(match)
                pred = prediction_bundle.predict(fixture)
                value_pred = value_bundle.predict(fixture)

                probs = pred.as_tuple()
                predictions_for_metrics.append((probs, match.result))

                row = {
                    "date": match.date.isoformat(),
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "prob_home": pred.prob_home,
                    "prob_draw": pred.prob_draw,
                    "prob_away": pred.prob_away,
                    "value_prob_home": value_pred.prob_home,
                    "value_prob_draw": value_pred.prob_draw,
                    "value_prob_away": value_pred.prob_away,
                    "model_name": pred.model_name,
                    "value_model_name": value_pred.model_name,
                    "actual": match.result,
                    "home_goals": match.home_goals,
                    "away_goals": match.away_goals,
                    "odds_home": match.odds.home if match.odds else None,
                    "odds_draw": match.odds.draw if match.odds else None,
                    "odds_away": match.odds.away if match.odds else None,
                }

                value_bets = find_value_bets(value_pred, bankroll, value_bet_cfg)
                if value_bets:
                    best = max(value_bets, key=lambda bet: bet.edge)
                    stake = best.kelly_stake
                    profit = stake * (best.odds - 1) if best.outcome == match.result else -stake
                    bankroll += profit

                    closing_match_odds = match.odds
                    opening_match_odds = getattr(match, "opening_odds", None) or closing_match_odds
                    outcome_idx = {"H": "home", "D": "draw", "A": "away"}[best.outcome]
                    bet_odds_at_placement = (
                        getattr(opening_match_odds, outcome_idx)
                        if opening_match_odds is not None
                        else None
                    )
                    closing_odds = (
                        getattr(closing_match_odds, outcome_idx)
                        if closing_match_odds is not None
                        else None
                    )

                    bet_records.append(
                        {
                            "date": match.date.isoformat(),
                            "match": f"{match.home_team} vs {match.away_team}",
                            "bet": best.bet_label,
                            "odds": best.odds,
                            "stake": stake,
                            "edge": best.edge,
                            "won": best.outcome == match.result,
                            "profit": profit,
                            "bankroll_after": bankroll,
                            "bet_odds_at_placement": bet_odds_at_placement,
                            "closing_odds": closing_odds,
                            "value_model_name": value_pred.model_name,
                        }
                    )
                    row["bet"] = best.bet_label
                    row["bet_odds"] = best.odds
                    row["bet_stake"] = stake
                    row["bet_profit"] = profit
                    row["bankroll"] = bankroll
                    row["bet_odds_at_placement"] = bet_odds_at_placement
                    row["closing_odds"] = closing_odds

                rows.append(row)
                prediction_bundle.update_with_match(match)
                value_bundle.update_with_match(match)
                progress.advance(task)

        prob_metrics = summary_stats(predictions_for_metrics)

        if bet_records:
            stakes = [float(record["stake"]) for record in bet_records]
            profits = [float(record["profit"]) for record in bet_records]
            returns = [
                float(record["stake"]) + float(record["profit"]) if record["won"] else 0.0
                for record in bet_records
            ]
            curve = bankroll_curve(self.initial_bankroll, stakes, profits)
            dd = max_drawdown(curve)
            per_bet_returns = [
                profit / stake if stake > 0 else 0.0
                for profit, stake in zip(profits, stakes, strict=True)
            ]
            bet_odds_at_placement = [record.get("bet_odds_at_placement") for record in bet_records]
            closing_odds_list = [record.get("closing_odds") for record in bet_records]
            clv_stats = clv_summary(bet_odds_at_placement, closing_odds_list)
            bet_metrics = {
                "n_bets": len(bet_records),
                "hits": sum(1 for record in bet_records if record["won"]),
                "total_staked": sum(stakes),
                "total_profit": sum(profits),
                "roi": calc_roi(stakes, returns),
                "sharpe": sharpe_ratio(per_bet_returns, annualization_factor=len(bet_records)),
                "clv_n": clv_stats["n"],
                "clv_mean": clv_stats["mean_clv"],
                "clv_median": clv_stats["median_clv"],
                "clv_pct_positive": clv_stats["pct_positive"],
            }
        else:
            dd = max_drawdown([self.initial_bankroll])
            bet_metrics = {
                "n_bets": 0,
                "clv_n": 0,
                "clv_mean": 0.0,
                "clv_median": 0.0,
                "clv_pct_positive": 0.0,
            }

        return BacktestResult(
            league=league_key,
            n_predictions=len(rows),
            n_bets=len(bet_records),
            metrics=prob_metrics,
            bet_metrics=bet_metrics,
            bankroll_final=bankroll,
            max_drawdown=dd,
            rows=rows,
            profile_1x2=prediction_bundle.profile.to_dict(),
            profile_value=value_bundle.profile.to_dict(),
        )

    @staticmethod
    def _fixture_from_match(m: Match) -> Fixture:
        return Fixture(
            date=m.date,
            league=m.league,
            home_team=m.home_team,
            away_team=m.away_team,
            odds=m.odds,
            kickoff_datetime_utc=m.kickoff_datetime_utc,
        )


# ───────────────────────── Phase 6: Walk-Forward ─────────────────────────


@dataclass(slots=True)
class WalkForwardSummary:
    """Aggregated multi-fold walk-forward result."""

    league: str
    folds: list[BacktestResult]
    aggregate: dict[str, dict[str, float]]  # metric → {mean, std, min, max}

    def to_dict(self) -> dict[str, object]:
        return {
            "league": self.league,
            "n_folds": len(self.folds),
            "folds": [f.to_dict() for f in self.folds],
            "aggregate": self.aggregate,
        }

    def save(self, outdir: Path | None = None) -> Path:
        outdir = outdir or BACKTEST_DIR
        path = outdir / f"walk_forward_{self.league}.json"
        with path.open("w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        return path


#: Default walk-forward schedule per the Phase 6 plan.
#:
#: Each tuple = (train_seasons, test_season). ``max(train_seasons) <
#: test_season`` must always hold to avoid train/test leakage.
DEFAULT_WALK_FORWARD_FOLDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("2019-20", "2020-21", "2021-22"), "2022-23"),
    (("2020-21", "2021-22", "2022-23"), "2023-24"),
    (("2021-22", "2022-23", "2023-24"), "2024-25"),
)


def walk_forward_backtest(
    league_key: str,
    folds: tuple[tuple[tuple[str, ...], str], ...] | None = None,
    *,
    bet_cfg: BettingConfig | None = None,
    bankroll: float = 1000.0,
    use_ensemble: bool = True,
    use_stacking: bool = False,
    mode: str = "expanding",
    window_matches: int = 500,
    profile_1x2: LeagueModelProfile | None = None,
    profile_value: LeagueModelProfile | None = None,
) -> WalkForwardSummary:
    """
    Run a chronological multi-fold walk-forward backtest.

    Each fold re-fits the CatBoost model on its train window, then rolls
    through the corresponding test season with the standard Backtester.
    No train/test leakage is possible because :class:`BacktestConfig` is
    rebuilt per fold and ``min(test_date) > max(train_date)`` is asserted.

    Parameters
    ----------
    mode
        ``"expanding"`` (default) — use the full ``train_seasons`` window.
        ``"sliding"`` — keep only the trailing ``window_matches`` matches
        of each fold's train set. Captures regime shifts (rule changes,
        pandemic effects, VAR introduction) at the cost of less data.
    window_matches
        Trailing window size when ``mode="sliding"``. Ignored otherwise.
    """
    if mode not in ("expanding", "sliding"):
        raise ValueError(f"mode must be 'expanding' or 'sliding', got {mode!r}")
    if mode == "sliding" and window_matches <= 0:
        raise ValueError("window_matches must be positive in sliding mode")

    folds = folds or DEFAULT_WALK_FORWARD_FOLDS
    _validate_folds(folds)

    training_window = window_matches if mode == "sliding" else None

    results: list[BacktestResult] = []
    for train_seasons, test_season in folds:
        fold_cfg = BacktestConfig(
            train_seasons=train_seasons,
            test_season=test_season,
            min_train_games=BACKTEST_CFG.min_train_games,
            update_frequency_days=BACKTEST_CFG.update_frequency_days,
        )
        bt = Backtester(
            cfg=fold_cfg,
            bet_cfg=bet_cfg or BETTING_CFG,
            initial_bankroll=bankroll,
            use_ensemble=use_ensemble,
            use_stacking=use_stacking,
            training_window_matches=training_window,
            profile_1x2=profile_1x2,
            profile_value=profile_value,
        )
        console.rule(
            f"[bold magenta]Fold: train={list(train_seasons)} test={test_season} "
            f"mode={mode}[/bold magenta]"
        )
        result = bt.run(league_key)
        results.append(result)

    aggregate = _aggregate_folds(results)
    return WalkForwardSummary(league=league_key, folds=results, aggregate=aggregate)


def _validate_folds(folds: tuple[tuple[tuple[str, ...], str], ...]) -> None:
    if not folds:
        raise ValueError("At least one fold is required")
    for train_seasons, test_season in folds:
        if not train_seasons:
            raise ValueError("train_seasons must be non-empty")
        if max(train_seasons) >= test_season:
            raise ValueError(
                f"Train/test leakage: max(train)={max(train_seasons)} >= test={test_season}"
            )


def _aggregate_folds(results: list[BacktestResult]) -> dict[str, dict[str, float]]:
    """Mean / std / min / max for every numeric metric across folds."""
    collected: dict[str, list[float]] = {}
    for r in results:
        for src in (r.metrics, r.bet_metrics):
            for k, v in src.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    collected.setdefault(k, []).append(float(v))

    out: dict[str, dict[str, float]] = {}
    for k, values in collected.items():
        arr = np.array(values, dtype=float)
        out[k] = {
            "mean": float(arr.mean()),
            "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
            "min": float(arr.min()),
            "max": float(arr.max()),
            "n": len(arr),
        }
    return out
