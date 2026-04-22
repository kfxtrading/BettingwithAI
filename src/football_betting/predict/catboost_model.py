"""
CatBoost classifier with FeatureBuilder integration and optional calibration.

v0.2 upgrades:
* Uses FeatureBuilder (28 features vs. v0.1's 14)
* Optional probability calibration via ProbabilityCalibrator
* Backward-compatible — accepts legacy PiRatings-only init
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from rich.console import Console

from football_betting.config import CATBOOST_CFG, LEAGUES, MODELS_DIR, CatBoostConfig
from football_betting.data.models import Fixture, Match, Prediction
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.calibration import ProbabilityCalibrator
from football_betting.predict.weights import season_decay_weights
from football_betting.rating.pi_ratings import PiRatings

console = Console()

OUTCOME_TO_INT = {"H": 0, "D": 1, "A": 2}
INT_TO_OUTCOME = {v: k for k, v in OUTCOME_TO_INT.items()}


@dataclass(slots=True)
class CatBoostPredictor:
    """CatBoost-based outcome classifier — v0.2 with full feature builder."""

    feature_builder: FeatureBuilder = field(default_factory=FeatureBuilder)
    cfg: CatBoostConfig = field(default_factory=lambda: CATBOOST_CFG)
    model: CatBoostClassifier | None = None
    feature_names: list[str] = field(default_factory=list)
    calibrator: ProbabilityCalibrator | None = None

    # ───────────────────────── Back-compat ─────────────────────────

    @property
    def pi_ratings(self) -> PiRatings:
        """Expose pi_ratings for v0.1 compatibility."""
        return self.feature_builder.pi_ratings

    # ───────────────────────── Training ─────────────────────────

    def build_training_data(
        self,
        matches: list[Match],
        warmup_games: int = 100,
    ) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
        """
        Walk matches chronologically; extract features *before* each match,
        then update trackers. First `warmup_games` skipped.

        Returns (features_df, labels, seasons) — ``seasons[i]`` is the season
        string for row ``i`` (used for time-decay weighting).
        """
        self.feature_builder.reset()

        rows: list[dict[str, float]] = []
        labels: list[int] = []
        seasons: list[str] = []
        matches_sorted = sorted(matches, key=lambda m: m.date)

        for idx, match in enumerate(matches_sorted):
            if idx >= warmup_games:
                feats = self.feature_builder.build_features(
                    home_team=match.home_team,
                    away_team=match.away_team,
                    league_key=match.league,
                    match_date=match.date,
                    odds_home=match.odds.home if match.odds else None,
                    odds_draw=match.odds.draw if match.odds else None,
                    odds_away=match.odds.away if match.odds else None,
                    season=match.season,
                    kickoff_datetime_utc=match.kickoff_datetime_utc,
                )
                rows.append(feats)
                labels.append(OUTCOME_TO_INT[match.result])
                seasons.append(match.season)

            # Update after feature extraction (no leakage)
            self.feature_builder.update_with_match(match)

        df = pd.DataFrame(rows)
        self.feature_names = list(df.columns)
        return df, np.array(labels), seasons

    def fit(
        self,
        matches: list[Match],
        warmup_games: int = 100,
        val_fraction: float = 0.15,
        calibrate: bool = True,
    ) -> dict[str, Any]:
        """Train + optionally calibrate."""
        X, y, seasons = self.build_training_data(matches, warmup_games=warmup_games)

        if len(X) < 200:
            raise ValueError(f"Too few samples: {len(X)}. Need >=200.")

        split = int(len(X) * (1 - val_fraction))
        X_train, X_val = X.iloc[:split], X.iloc[split:]
        y_train, y_val = y[:split], y[split:]
        seasons_train = seasons[:split]

        # Time-decay sample weights (newer seasons get higher weight)
        sample_weight = None
        if self.cfg.time_decay is not None and seasons_train:
            ref_season = max(seasons_train, key=lambda s: s.split("-", 1)[0])
            sample_weight = season_decay_weights(
                seasons_train, ref_season=ref_season, decay=self.cfg.time_decay
            )
            console.log(
                f"Time-decay weights: decay={self.cfg.time_decay}, "
                f"ref={ref_season}, min={sample_weight.min():.3f}, "
                f"max={sample_weight.max():.3f}"
            )

        console.log(f"Training: {len(X_train)} samples, validation: {len(X_val)}")
        console.log(f"Features: {len(self.feature_names)}")

        train_pool = Pool(
            X_train, y_train, feature_names=self.feature_names, weight=sample_weight
        )
        val_pool = Pool(X_val, y_val, feature_names=self.feature_names)

        cb_kwargs: dict[str, Any] = dict(
            iterations=self.cfg.iterations,
            learning_rate=self.cfg.learning_rate,
            depth=self.cfg.depth,
            l2_leaf_reg=self.cfg.l2_leaf_reg,
            loss_function=self.cfg.loss_function,
            eval_metric=self.cfg.eval_metric,
            random_seed=self.cfg.random_seed,
            early_stopping_rounds=self.cfg.early_stopping_rounds,
            verbose=self.cfg.verbose,
            classes_count=3,
        )
        if self.cfg.use_gpu:
            from football_betting.predict.gpu_utils import detect_gpu
            if detect_gpu():
                cb_kwargs["task_type"] = "GPU"
                cb_kwargs["devices"] = self.cfg.gpu_devices
                cb_kwargs["bootstrap_type"] = "Bayesian"
                console.log(
                    f"[cyan]CatBoost GPU enabled (devices={self.cfg.gpu_devices})[/cyan]"
                )
            else:
                console.log("[yellow]CatBoost GPU requested but no CUDA — falling back to CPU[/yellow]")
        self.model = CatBoostClassifier(**cb_kwargs)
        self.model.fit(train_pool, eval_set=val_pool)

        val_preds = self.model.predict_proba(X_val)

        # Fit calibrator on validation predictions
        if calibrate:
            self.calibrator = ProbabilityCalibrator()
            self.calibrator.fit(val_preds, y_val)
            console.log("[green]Calibrator fitted on validation set[/green]")

        feature_importance = dict(
            zip(self.feature_names, self.model.get_feature_importance(), strict=True)
        )

        return {
            "n_train": len(X_train),
            "n_val": len(X_val),
            "n_features": len(self.feature_names),
            "best_iteration": self.model.get_best_iteration(),
            "best_score": self.model.get_best_score(),
            "feature_importance": sorted(
                feature_importance.items(), key=lambda kv: kv[1], reverse=True
            ),
            "val_predictions": val_preds,
            "val_labels": y_val,
        }

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, path: Path) -> None:
        if self.model is None:
            raise RuntimeError("No model to save — fit first.")
        self.model.save_model(str(path))
        meta_path = path.with_suffix(".features.txt")
        meta_path.write_text("\n".join(self.feature_names))
        if self.calibrator and self.calibrator.is_fitted:
            cal_path = path.with_suffix(".calibrator.joblib")
            joblib.dump(self.calibrator, cal_path)

    def load(self, path: Path) -> None:
        self.model = CatBoostClassifier()
        self.model.load_model(str(path))

        meta_path = path.with_suffix(".features.txt")
        if meta_path.exists():
            self.feature_names = meta_path.read_text().splitlines()

        cal_path = path.with_suffix(".calibrator.joblib")
        if cal_path.exists():
            self.calibrator = joblib.load(cal_path)
            console.log(f"Loaded calibrator: {cal_path.name}")

    @classmethod
    def for_league(cls, league_key: str, feature_builder: FeatureBuilder) -> CatBoostPredictor:
        inst = cls(feature_builder=feature_builder)
        model_path = MODELS_DIR / f"catboost_{league_key}.cbm"
        if model_path.exists():
            inst.load(model_path)
            console.log(f"Loaded model: {model_path.name}")
        return inst

    # ───────────────────────── Inference ─────────────────────────

    def predict(self, fixture: Fixture) -> Prediction:
        if self.model is None:
            raise RuntimeError("Model not trained / loaded.")

        feats = self.feature_builder.features_for_fixture(fixture)
        X = pd.DataFrame([feats])[self.feature_names]
        raw_probs = self.model.predict_proba(X)[0]

        # Apply calibration if available
        if self.calibrator and self.calibrator.is_fitted:
            probs = self.calibrator.transform(raw_probs.reshape(1, -1))[0]
        else:
            probs = raw_probs

        return Prediction(
            fixture=fixture,
            model_name=f"CatBoost+FB{'+Cal' if self.calibrator else ''}",
            prob_home=float(probs[OUTCOME_TO_INT["H"]]),
            prob_draw=float(probs[OUTCOME_TO_INT["D"]]),
            prob_away=float(probs[OUTCOME_TO_INT["A"]]),
        )
