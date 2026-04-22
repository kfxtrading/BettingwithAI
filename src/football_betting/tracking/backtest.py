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
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress

from football_betting.betting.value import find_value_bets
from football_betting.config import (
    BACKTEST_CFG,
    BETTING_CFG,
    BACKTEST_DIR,
    BacktestConfig,
    BettingConfig,
    LEAGUES,
)
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture, Match
from football_betting.data.snapshot_service import merge_snapshots_into_matches
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.poisson import PoissonModel

# EnsembleModel is lazy-imported inside run() to break circular dep
# (ensemble.py → tracking.metrics → tracking/__init__.py → backtest.py → ensemble)
from football_betting.tracking.metrics import (
    bankroll_curve,
    clv_summary,
    max_drawdown,
    mean_rps,
    roi as calc_roi,
    sharpe_ratio,
    summary_stats,
)

console = Console()


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
    """Walk-forward backtester."""

    cfg: BacktestConfig = field(default_factory=lambda: BACKTEST_CFG)
    bet_cfg: BettingConfig = field(default_factory=lambda: BETTING_CFG)
    initial_bankroll: float = 1000.0
    use_ensemble: bool = True

    # ───────────────────────── Core loop ─────────────────────────

    def run(self, league_key: str) -> BacktestResult:
        """Run backtest for one league."""
        console.rule(f"[bold cyan]Backtest — {LEAGUES[league_key].name}[/bold cyan]")

        # Load matches, split by season
        train_matches = load_league(league_key, seasons=list(self.cfg.train_seasons))
        test_matches = load_league(league_key, seasons=[self.cfg.test_season])

        # Phase 4: overlay persisted T-minus opening-line snapshots so CLV
        # becomes non-degenerate. Silent no-op when no snapshots exist.
        test_matches = merge_snapshots_into_matches(test_matches, league_key)

        if len(train_matches) < self.cfg.min_train_games:
            raise ValueError(
                f"Too few training matches ({len(train_matches)} < "
                f"{self.cfg.min_train_games})"
            )

        console.log(f"Train: {len(train_matches)} matches ({self.cfg.train_seasons})")
        console.log(f"Test:  {len(test_matches)} matches ({self.cfg.test_season})")

        # Train feature builder + CatBoost on training seasons
        feature_builder = FeatureBuilder()
        cb = CatBoostPredictor(feature_builder=feature_builder)
        training_info = cb.fit(train_matches, warmup_games=100, val_fraction=0.15, calibrate=True)
        console.log(
            f"Training complete: {training_info['n_train']} samples, "
            f"{training_info['n_features']} features"
        )

        # Now `feature_builder` has seen all training matches. For each test
        # match: predict BEFORE outcome, then update builder with result.
        poisson = PoissonModel(pi_ratings=feature_builder.pi_ratings)
        # Lazy import to break circular dep
        from football_betting.predict.ensemble import EnsembleModel
        model = (
            EnsembleModel(catboost=cb, poisson=poisson) if self.use_ensemble else cb
        )

        rows: list[dict[str, object]] = []
        bet_records: list[dict[str, object]] = []
        predictions_for_metrics: list[tuple[tuple[float, float, float], str]] = []

        bankroll = self.initial_bankroll
        test_matches_sorted = sorted(test_matches, key=lambda m: m.date)

        with Progress(console=console) as progress:
            task = progress.add_task(f"Backtest {league_key}", total=len(test_matches_sorted))
            for m in test_matches_sorted:
                fixture = self._fixture_from_match(m)
                pred = model.predict(fixture)

                probs = pred.as_tuple()
                predictions_for_metrics.append((probs, m.result))

                row = {
                    "date": m.date.isoformat(),
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "prob_home": pred.prob_home,
                    "prob_draw": pred.prob_draw,
                    "prob_away": pred.prob_away,
                    "actual": m.result,
                    "home_goals": m.home_goals,
                    "away_goals": m.away_goals,
                    "odds_home": m.odds.home if m.odds else None,
                    "odds_draw": m.odds.draw if m.odds else None,
                    "odds_away": m.odds.away if m.odds else None,
                }

                # Value-betting simulation
                value_bets = find_value_bets(pred, bankroll, self.bet_cfg)
                if value_bets:
                    # Pick highest-edge bet only (avoid betting both sides)
                    best = max(value_bets, key=lambda b: b.edge)
                    stake = best.kelly_stake
                    profit = (
                        stake * (best.odds - 1) if best.outcome == m.result else -stake
                    )
                    bankroll += profit

                    # CLV pipeline: bet_odds_at_placement vs closing_odds.
                    # Phase 3: no opening-snapshots available → both equal m.odds
                    # (CLV ≡ 0). Phase 4 will fill `opening_odds` with real T-48h
                    # snapshots so CLV becomes non-degenerate.
                    closing_match_odds = m.odds
                    opening_match_odds = getattr(m, "opening_odds", None) or closing_match_odds
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
                            "date": m.date.isoformat(),
                            "match": f"{m.home_team} vs {m.away_team}",
                            "bet": best.bet_label,
                            "odds": best.odds,
                            "stake": stake,
                            "edge": best.edge,
                            "won": best.outcome == m.result,
                            "profit": profit,
                            "bankroll_after": bankroll,
                            "bet_odds_at_placement": bet_odds_at_placement,
                            "closing_odds": closing_odds,
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

                # Update feature builder with this match's result
                feature_builder.update_with_match(m)
                progress.advance(task)

        # Aggregate metrics
        prob_metrics = summary_stats(predictions_for_metrics)

        if bet_records:
            stakes = [float(r["stake"]) for r in bet_records]
            profits = [float(r["profit"]) for r in bet_records]
            returns = [
                float(r["stake"]) + float(r["profit"]) if r["won"] else 0.0
                for r in bet_records
            ]
            curve = bankroll_curve(self.initial_bankroll, stakes, profits)
            dd = max_drawdown(curve)
            per_bet_returns = [p / s if s > 0 else 0.0 for p, s in zip(profits, stakes, strict=True)]
            bet_odds_at_placement = [
                r.get("bet_odds_at_placement") for r in bet_records  # type: ignore[misc]
            ]
            closing_odds_list = [
                r.get("closing_odds") for r in bet_records  # type: ignore[misc]
            ]
            clv_stats = clv_summary(bet_odds_at_placement, closing_odds_list)
            bet_metrics = {
                "n_bets": len(bet_records),
                "hits": sum(1 for r in bet_records if r["won"]),
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
            curve = [self.initial_bankroll]
            dd = max_drawdown(curve)
            bet_metrics = {
                "n_bets": 0,
                "clv_n": 0,
                "clv_mean": 0.0,
                "clv_median": 0.0,
                "clv_pct_positive": 0.0,
            }

        result = BacktestResult(
            league=league_key,
            n_predictions=len(rows),
            n_bets=len(bet_records),
            metrics=prob_metrics,
            bet_metrics=bet_metrics,
            bankroll_final=bankroll,
            max_drawdown=dd,
            rows=rows,
        )
        return result

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
