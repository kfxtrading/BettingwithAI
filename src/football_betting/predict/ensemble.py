"""
3-way ensemble: CatBoost + Poisson + MLP (optional).

v0.3: extends v0.2 2-way blend to include an optional MLP member. If MLP
is None, falls back to 2-way behavior identical to v0.2.

Weight-tuning uses Dirichlet sampling rather than grid search — more
efficient exploration of the simplex and supports arbitrary number of
components.

Phase 6: `tune_dirichlet` extends objective from probabilistic-only (RPS)
to CLV-aware and blended scoring using per-match bet/closing odds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from football_betting.betting.margin import remove_margin
from football_betting.config import (
    BETTING_CFG,
    ENSEMBLE_TUNE_CFG,
    BettingConfig,
    EnsembleTuneConfig,
)
from football_betting.data.models import Fixture, Outcome, Prediction
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.tracking.metrics import (
    brier_score,
    clv_summary,
    log_loss_3way,
    mean_rps,
)

Objective = Literal["rps", "log_loss", "brier", "clv", "blended"]


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

    # ───────────────────────── CLV-aware Dirichlet tuning (Phase 6) ─────────

    def tune_dirichlet(
        self,
        fixtures: list[Fixture],
        actuals: list[Outcome],
        bet_odds: list[tuple[float, float, float] | None] | None = None,
        closing_odds: list[tuple[float, float, float] | None] | None = None,
        objective: Objective = "blended",
        blend: float = 0.5,
        cfg: EnsembleTuneConfig | None = None,
        bet_cfg: BettingConfig | None = None,
    ) -> dict[str, object]:
        """
        CLV-aware Dirichlet sampling (Phase 6).

        objective:
            - ``rps``       : minimize mean RPS (probabilistic only)
            - ``log_loss``  : minimize mean log-loss
            - ``brier``     : minimize mean Brier score
            - ``clv``       : maximize mean CLV of simulated value bets
            - ``blended``   : ``blend * z(-rps) + (1-blend) * z(clv_mean)`` (maximize)

        For ``clv`` / ``blended`` objectives, ``bet_odds`` (opening line) and
        ``closing_odds`` must be provided as per-match (home, draw, away)
        tuples; ``None`` entries are skipped.
        """
        cfg = cfg or ENSEMBLE_TUNE_CFG
        bet_cfg = bet_cfg or BETTING_CFG

        if len(fixtures) != len(actuals):
            raise ValueError("fixtures and actuals must be same length")
        if objective in ("clv", "blended"):
            if bet_odds is None or closing_odds is None:
                raise ValueError(f"objective={objective!r} requires bet_odds and closing_odds")
            if len(bet_odds) != len(fixtures) or len(closing_odds) != len(fixtures):
                raise ValueError("bet_odds and closing_odds must align with fixtures")
        if not 0.0 <= blend <= 1.0:
            raise ValueError("blend must be in [0, 1]")

        # Pre-compute base model probabilities once
        cb_probs = np.asarray(
            [self.catboost.predict(fx).as_tuple() for fx in fixtures], dtype=float
        )
        po_probs = np.asarray(
            [self.poisson.predict(fx).as_tuple() for fx in fixtures], dtype=float
        )
        mlp_probs = (
            np.asarray([self.mlp.predict(fx).as_tuple() for fx in fixtures], dtype=float)
            if self.mlp is not None else None
        )

        # Pre-devig opening market probs (stable across all weight samples) for
        # CLV objective: a bet is placed on the opening line when edge > min_edge.
        opening_market: list[tuple[float, float, float] | None] | None = None
        if objective in ("clv", "blended"):
            assert bet_odds is not None  # narrowed by the validation above
            opening_market = _precompute_market_probs(bet_odds, bet_cfg)

        rng = np.random.default_rng(42)
        if mlp_probs is None:
            alpha = np.array(cfg.dirichlet_alpha[:2], dtype=float)
        else:
            alpha = np.array(cfg.dirichlet_alpha[:3], dtype=float)
        samples = rng.dirichlet(alpha, size=cfg.dirichlet_samples)

        rps_scores: list[float] = []
        clv_scores: list[float] = []
        clv_n: list[int] = []

        for weights in samples:
            blended_probs = weights[0] * cb_probs + weights[1] * po_probs
            if mlp_probs is not None and len(weights) > 2:
                blended_probs = blended_probs + weights[2] * mlp_probs
            # renormalize (weights are a simplex, but rounding can produce drift)
            row_sum = blended_probs.sum(axis=1, keepdims=True)
            blended_probs = blended_probs / np.where(row_sum > 0, row_sum, 1.0)

            pairs = [
                ((float(p[0]), float(p[1]), float(p[2])), a)
                for p, a in zip(blended_probs, actuals, strict=True)
            ]

            if objective == "rps":
                rps_scores.append(mean_rps(pairs))
            elif objective == "log_loss":
                rps_scores.append(
                    float(np.mean([log_loss_3way(p, a) for p, a in pairs]))
                )
            elif objective == "brier":
                rps_scores.append(
                    float(np.mean([brier_score(p, a) for p, a in pairs]))
                )

            if objective in ("clv", "blended"):
                assert opening_market is not None
                assert bet_odds is not None and closing_odds is not None
                bet_open, bet_close = _simulate_bets_for_clv(
                    blended_probs, opening_market, bet_odds, closing_odds, bet_cfg,
                )
                stats = clv_summary(bet_open, bet_close)
                clv_scores.append(float(stats["mean_clv"]))
                clv_n.append(int(stats["n"]))
                if objective == "blended":
                    rps_scores.append(mean_rps(pairs))

        # Pick best sample
        if objective in ("rps", "log_loss", "brier"):
            best_idx = int(np.argmin(rps_scores))
            best_metric_val = float(rps_scores[best_idx])
            metric_key = f"best_{objective}"
        elif objective == "clv":
            best_idx = int(np.argmax(clv_scores))
            best_metric_val = float(clv_scores[best_idx])
            metric_key = "best_clv_mean"
        else:  # blended
            rps_arr = np.asarray(rps_scores, dtype=float)
            clv_arr = np.asarray(clv_scores, dtype=float)
            rps_z = _zscore(-rps_arr)          # lower RPS is better → negate
            clv_z = _zscore(clv_arr)           # higher CLV is better
            score = blend * rps_z + (1.0 - blend) * clv_z
            best_idx = int(np.argmax(score))
            best_metric_val = float(score[best_idx])
            metric_key = "best_blended"

        best_weights = samples[best_idx]
        self.w_catboost = float(best_weights[0])
        self.w_poisson = float(best_weights[1])
        if len(best_weights) > 2:
            self.w_mlp = float(best_weights[2])

        result: dict[str, object] = {
            "objective": objective,
            "best_w_catboost": self.w_catboost,
            "best_w_poisson": self.w_poisson,
            "best_w_mlp": self.w_mlp if mlp_probs is not None else 0.0,
            metric_key: best_metric_val,
            "n_samples_tried": cfg.dirichlet_samples,
        }
        if clv_scores:
            result["clv_mean_at_best"] = float(clv_scores[best_idx])
            result["clv_n_at_best"] = int(clv_n[best_idx])
        if rps_scores and objective == "blended":
            # with blended we pushed RPS per sample, so index aligns
            result["rps_at_best"] = float(rps_scores[best_idx])
        return result


# ───────────────────────── Module-level helpers ─────────────────────────

def _zscore(x: np.ndarray) -> np.ndarray:
    std = float(x.std())
    if std < 1e-12:
        return np.zeros_like(x)
    return (x - float(x.mean())) / std


def _precompute_market_probs(
    odds_list: list[tuple[float, float, float] | None],
    bet_cfg: BettingConfig,
) -> list[tuple[float, float, float] | None]:
    out: list[tuple[float, float, float] | None] = []
    for row in odds_list:
        if row is None:
            out.append(None)
            continue
        oh, od, oa = row
        mh, md, ma = remove_margin(oh, od, oa, method=bet_cfg.devig_method)
        out.append((mh, md, ma))
    return out


def _simulate_bets_for_clv(
    model_probs: np.ndarray,
    market_probs: list[tuple[float, float, float] | None],
    bet_odds: list[tuple[float, float, float] | None],
    closing_odds: list[tuple[float, float, float] | None],
    bet_cfg: BettingConfig,
) -> tuple[list[float | None], list[float | None]]:
    """Emit (opening, closing) odds pairs for each match where a value bet is placed."""
    bet_open: list[float | None] = []
    bet_close: list[float | None] = []
    for i, (mp_row, bo_row, co_row) in enumerate(zip(market_probs, bet_odds, closing_odds, strict=True)):
        if mp_row is None or bo_row is None:
            continue
        candidates: list[tuple[int, float, float, float]] = []
        for idx in (0, 1, 2):
            model_p = float(model_probs[i, idx])
            market_p = mp_row[idx]
            odds = bo_row[idx]
            edge = model_p - market_p
            if edge < bet_cfg.min_edge:
                continue
            if not (bet_cfg.min_odds <= odds <= bet_cfg.max_odds):
                continue
            candidates.append((idx, model_p, edge, odds))
        if not candidates:
            continue
        # Pick highest-edge leg (mirrors backtester behaviour)
        idx, _, _, open_odd = max(candidates, key=lambda c: c[2])
        close_odd = co_row[idx] if co_row is not None else None
        bet_open.append(open_odd)
        bet_close.append(close_odd)
    return bet_open, bet_close
