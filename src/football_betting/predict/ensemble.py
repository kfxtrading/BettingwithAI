"""
3-way ensemble: CatBoost + Poisson + MLP (optional).

v0.3: extends v0.2 2-way blend to include an optional MLP member. If MLP
is None, falls back to 2-way behavior identical to v0.2.

Weight-tuning uses Dirichlet sampling rather than grid search — more
efficient exploration of the simplex and supports arbitrary number of
components.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from football_betting.config import ENSEMBLE_TUNE_CFG, EnsembleTuneConfig
from football_betting.data.models import Fixture, Outcome, Prediction
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.tracking.metrics import (
    brier_score,
    log_loss_3way,
    mean_rps,
)


@dataclass(slots=True)
class EnsembleModel:
    """Weighted blend of up to 3 models."""

    catboost: CatBoostPredictor
    poisson: PoissonModel
    mlp: MLPPredictor | None = None
    w_catboost: float = 0.6
    w_poisson: float = 0.2
    w_mlp: float = 0.2

    def __post_init__(self) -> None:
        if self.mlp is None:
            # 2-way fallback — redistribute MLP weight
            self.w_catboost += self.w_mlp * (self.w_catboost / (self.w_catboost + self.w_poisson))
            self.w_poisson += self.w_mlp * (self.w_poisson / (self.w_catboost + self.w_poisson - self.w_mlp))
            self.w_mlp = 0.0

        # Normalize
        total = self.w_catboost + self.w_poisson + self.w_mlp
        if total > 0:
            self.w_catboost /= total
            self.w_poisson /= total
            self.w_mlp /= total

    # ───────────────────────── Prediction ─────────────────────────

    def predict(self, fixture: Fixture) -> Prediction:
        cb_pred = self.catboost.predict(fixture)
        po_pred = self.poisson.predict(fixture)

        p_h = self.w_catboost * cb_pred.prob_home + self.w_poisson * po_pred.prob_home
        p_d = self.w_catboost * cb_pred.prob_draw + self.w_poisson * po_pred.prob_draw
        p_a = self.w_catboost * cb_pred.prob_away + self.w_poisson * po_pred.prob_away

        if self.mlp is not None and self.w_mlp > 0:
            mlp_pred = self.mlp.predict(fixture)
            p_h += self.w_mlp * mlp_pred.prob_home
            p_d += self.w_mlp * mlp_pred.prob_draw
            p_a += self.w_mlp * mlp_pred.prob_away

        s = p_h + p_d + p_a
        weights_str = f"CB={self.w_catboost:.2f},Po={self.w_poisson:.2f}"
        if self.mlp is not None:
            weights_str += f",MLP={self.w_mlp:.2f}"

        return Prediction(
            fixture=fixture,
            model_name=f"Ensemble({weights_str})",
            prob_home=p_h / s,
            prob_draw=p_d / s,
            prob_away=p_a / s,
            expected_home_goals=po_pred.expected_home_goals,
            expected_away_goals=po_pred.expected_away_goals,
        )

    # ───────────────────────── Weight tuning ─────────────────────────

    def tune_weights(
        self,
        fixtures: list[Fixture],
        actuals: list[Outcome],
        cfg: EnsembleTuneConfig | None = None,
    ) -> dict[str, object]:
        """
        Dirichlet-sampling weight tuning on validation pairs.

        Samples N weight triplets from Dirichlet(α), evaluates each,
        picks the best. Handles both 2-way (MLP=None) and 3-way ensemble.
        """
        cfg = cfg or ENSEMBLE_TUNE_CFG
        if len(fixtures) != len(actuals):
            raise ValueError("fixtures and actuals must be same length")

        # Pre-compute each model's predictions once
        cb_probs = [self.catboost.predict(fx).as_tuple() for fx in fixtures]
        po_probs = [self.poisson.predict(fx).as_tuple() for fx in fixtures]
        mlp_probs = (
            [self.mlp.predict(fx).as_tuple() for fx in fixtures]
            if self.mlp is not None else None
        )

        rng = np.random.default_rng(42)
        if mlp_probs is None:
            # 2-way: sample only (w_cb, w_poisson)
            alpha = np.array(cfg.dirichlet_alpha[:2])
            samples = rng.dirichlet(alpha, size=cfg.dirichlet_samples)
        else:
            alpha = np.array(cfg.dirichlet_alpha[:3])
            samples = rng.dirichlet(alpha, size=cfg.dirichlet_samples)

        best_metric = float("inf")
        best_weights = None

        for weights in samples:
            blended = []
            for i, actual in enumerate(actuals):
                p_h = weights[0] * cb_probs[i][0] + weights[1] * po_probs[i][0]
                p_d = weights[0] * cb_probs[i][1] + weights[1] * po_probs[i][1]
                p_a = weights[0] * cb_probs[i][2] + weights[1] * po_probs[i][2]
                if mlp_probs is not None:
                    p_h += weights[2] * mlp_probs[i][0]
                    p_d += weights[2] * mlp_probs[i][1]
                    p_a += weights[2] * mlp_probs[i][2]
                s = p_h + p_d + p_a
                blended.append(((p_h / s, p_d / s, p_a / s), actual))

            if cfg.metric == "rps":
                metric = mean_rps(blended)
            elif cfg.metric == "log_loss":
                metric = float(np.mean([log_loss_3way(p, a) for p, a in blended]))
            elif cfg.metric == "brier":
                metric = float(np.mean([brier_score(p, a) for p, a in blended]))
            else:
                raise ValueError(f"Unknown metric: {cfg.metric}")

            if metric < best_metric:
                best_metric = metric
                best_weights = weights

        if best_weights is None:
            raise RuntimeError("No valid weight sample found.")

        # Apply best weights
        self.w_catboost = float(best_weights[0])
        self.w_poisson = float(best_weights[1])
        if len(best_weights) > 2:
            self.w_mlp = float(best_weights[2])

        return {
            "best_w_catboost": self.w_catboost,
            "best_w_poisson": self.w_poisson,
            "best_w_mlp": self.w_mlp if mlp_probs is not None else 0.0,
            f"best_{cfg.metric}": best_metric,
            "n_samples_tried": cfg.dirichlet_samples,
        }
