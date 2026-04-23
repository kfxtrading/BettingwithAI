"""
k-way ensemble: CatBoost + Poisson (+ MLP/TabTransformer + Sequence).

v0.3 introduced the optional MLP member; v0.5 adds an optional
``SequencePredictor`` (1D-CNN + Transformer over match histories),
turning the blender into a 4-way simplex.

Weight-tuning uses Dirichlet sampling on an active-members-only simplex
so 2-/3-/4-way configurations all share the same code path.

Phase 6: ``tune_dirichlet`` extends the objective from probabilistic-only
(RPS) to CLV-aware and blended scoring using per-match bet/closing odds.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

import numpy as np

from football_betting.betting.margin import remove_margin
from football_betting.config import (
    BETTING_CFG,
    ENSEMBLE_TUNE_CFG,
    MODELS_DIR,
    BettingConfig,
    EnsembleTuneConfig,
    ModelPurpose,
    artifact_suffix,
)
from football_betting.data.models import Fixture, Outcome, Prediction
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.predict.sequence_model import SequencePredictor
from football_betting.tracking.metrics import (
    brier_score,
    clv_summary,
    log_loss_3way,
    mean_rps,
)

Objective = Literal["rps", "log_loss", "brier", "clv", "blended", "brier_logloss_blended"]


def _normalize_active_members(raw: Iterable[object]) -> list[str]:
    canonical = ["catboost", "poisson", "mlp", "sequence"]
    requested = {str(name).lower() for name in raw}
    unknown = sorted(requested.difference(canonical))
    if unknown:
        raise ValueError(f"Unknown ensemble members in weight metadata: {unknown}")
    active = [name for name in canonical if name in requested]
    if not active:
        raise ValueError("Weight metadata active_members must not be empty")
    return active


def ensemble_weights_path(league_key: str, purpose: ModelPurpose = "1x2") -> Path:
    """Return the canonical ``models/ensemble_weights_<LG><suffix>.json`` path."""
    return MODELS_DIR / f"ensemble_weights_{league_key}{artifact_suffix(purpose)}.json"


@dataclass(slots=True)
class EnsembleModel:
    """Weighted blend of up to 4 models (CatBoost, Poisson, MLP, Sequence).

    Any optional member can be ``None``; its weight is redistributed to the
    remaining active members proportionally. The simplex is always
    normalized to sum to 1.
    """

    catboost: CatBoostPredictor
    poisson: PoissonModel
    mlp: MLPPredictor | None = None
    sequence: SequencePredictor | None = None
    w_catboost: float = 0.5
    w_poisson: float = 0.2
    w_mlp: float = 0.15
    w_sequence: float = 0.15

    def __post_init__(self) -> None:
        # Zero-out weights for missing members
        if self.mlp is None:
            self.w_mlp = 0.0
        if self.sequence is None:
            self.w_sequence = 0.0

        total = self.w_catboost + self.w_poisson + self.w_mlp + self.w_sequence
        if total <= 0:
            raise ValueError("EnsembleModel: at least one weight must be positive.")
        self.w_catboost /= total
        self.w_poisson /= total
        self.w_mlp /= total
        self.w_sequence /= total

    # ───────────────────────── Helpers ─────────────────────────

    def _active_members(self) -> list[str]:
        active = ["catboost", "poisson"]
        if self.mlp is not None:
            active.append("mlp")
        if self.sequence is not None:
            active.append("sequence")
        return active

    def _weights_array(self) -> np.ndarray:
        return np.asarray(
            [self.w_catboost, self.w_poisson, self.w_mlp, self.w_sequence],
            dtype=float,
        )

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

        if self.sequence is not None and self.w_sequence > 0:
            sq_pred = self.sequence.predict(fixture)
            p_h += self.w_sequence * sq_pred.prob_home
            p_d += self.w_sequence * sq_pred.prob_draw
            p_a += self.w_sequence * sq_pred.prob_away

        s = p_h + p_d + p_a
        parts = [f"CB={self.w_catboost:.2f}", f"Po={self.w_poisson:.2f}"]
        if self.mlp is not None:
            parts.append(f"MLP={self.w_mlp:.2f}")
        if self.sequence is not None:
            parts.append(f"Seq={self.w_sequence:.2f}")

        return Prediction(
            fixture=fixture,
            model_name=f"Ensemble({','.join(parts)})",
            prob_home=p_h / s,
            prob_draw=p_d / s,
            prob_away=p_a / s,
            expected_home_goals=po_pred.expected_home_goals,
            expected_away_goals=po_pred.expected_away_goals,
        )

    # ───────────────────────── Weight tuning ─────────────────────────

    def _precompute_member_probs(
        self,
        fixtures: list[Fixture],
    ) -> dict[str, np.ndarray]:
        """Evaluate each active member once; return {name: (N, 3) float array}."""
        out: dict[str, np.ndarray] = {
            "catboost": np.asarray(
                [self.catboost.predict(fx).as_tuple() for fx in fixtures],
                dtype=float,
            ),
            "poisson": np.asarray(
                [self.poisson.predict(fx).as_tuple() for fx in fixtures],
                dtype=float,
            ),
        }
        if self.mlp is not None:
            out["mlp"] = np.asarray(
                [self.mlp.predict(fx).as_tuple() for fx in fixtures],
                dtype=float,
            )
        if self.sequence is not None:
            out["sequence"] = np.asarray(
                [self.sequence.predict(fx).as_tuple() for fx in fixtures],
                dtype=float,
            )
        return out

    # ───────────────────────── Weight persistence ─────────────────────────

    def save_weights(self, path: Path, *, metadata: dict[str, object] | None = None) -> None:
        """Persist current simplex weights to JSON (e.g. models/ensemble_weights_BL.json)."""
        payload: dict[str, object] = {
            "w_catboost": float(self.w_catboost),
            "w_poisson": float(self.w_poisson),
            "w_mlp": float(self.w_mlp),
            "w_sequence": float(self.w_sequence),
        }
        metadata_payload = dict(metadata or {})
        metadata_payload.setdefault("active_members", self._active_members())
        payload["metadata"] = metadata_payload
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_weights(
        self,
        path: Path,
        *,
        expected_purpose: ModelPurpose | None = None,
        expected_active_members: Iterable[str] | None = None,
        expected_objective: str | None = None,
        expected_calibration_method: str | None = None,
    ) -> None:
        """Load simplex weights from JSON and optionally validate saved metadata."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        metadata_raw = data.get("metadata")
        metadata = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}

        runtime_active = self._active_members()
        expected_active = (
            _normalize_active_members(expected_active_members)
            if expected_active_members is not None
            else runtime_active
        )

        metadata_active_raw = metadata.get("active_members")
        if metadata_active_raw is not None:
            if not isinstance(metadata_active_raw, list):
                raise ValueError(
                    f"EnsembleModel.load_weights: metadata.active_members must be a list in {path}"
                )
            metadata_active = _normalize_active_members(metadata_active_raw)
            if metadata_active != runtime_active:
                raise ValueError(
                    "EnsembleModel.load_weights: saved active_members "
                    f"{metadata_active} do not match runtime members {runtime_active} in {path}"
                )
        elif expected_active_members is not None:
            raise ValueError(
                f"EnsembleModel.load_weights: missing metadata.active_members in {path}"
            )

        if runtime_active != expected_active:
            raise ValueError(
                "EnsembleModel.load_weights: runtime members "
                f"{runtime_active} do not match expected members {expected_active}"
            )

        if expected_purpose is not None:
            metadata_purpose = metadata.get("purpose")
            if metadata_purpose is None:
                raise ValueError(f"EnsembleModel.load_weights: missing metadata.purpose in {path}")
            if str(metadata_purpose).lower() != expected_purpose:
                raise ValueError(
                    "EnsembleModel.load_weights: saved purpose "
                    f"{metadata_purpose!r} does not match expected {expected_purpose!r}"
                )

        if expected_objective is not None:
            metadata_objective = metadata.get("objective")
            if metadata_objective is None:
                raise ValueError(f"EnsembleModel.load_weights: missing metadata.objective in {path}")
            if str(metadata_objective) != expected_objective:
                raise ValueError(
                    "EnsembleModel.load_weights: saved objective "
                    f"{metadata_objective!r} does not match expected {expected_objective!r}"
                )

        if expected_calibration_method is not None:
            metadata_calibration = metadata.get("calibration_method")
            if metadata_calibration is None:
                raise ValueError(
                    f"EnsembleModel.load_weights: missing metadata.calibration_method in {path}"
                )
            if str(metadata_calibration) != expected_calibration_method:
                raise ValueError(
                    "EnsembleModel.load_weights: saved calibration_method "
                    f"{metadata_calibration!r} does not match expected "
                    f"{expected_calibration_method!r}"
                )

        self.w_catboost = float(data.get("w_catboost", 0.0))
        self.w_poisson = float(data.get("w_poisson", 0.0))
        self.w_mlp = float(data.get("w_mlp", 0.0)) if self.mlp is not None else 0.0
        self.w_sequence = float(data.get("w_sequence", 0.0)) if self.sequence is not None else 0.0
        total = self.w_catboost + self.w_poisson + self.w_mlp + self.w_sequence
        if total <= 0:
            raise ValueError(f"EnsembleModel.load_weights: degenerate weights in {path}")
        self.w_catboost /= total
        self.w_poisson /= total
        self.w_mlp /= total
        self.w_sequence /= total

    def _assign_weights(self, active: list[str], weights: np.ndarray) -> None:
        mapping = dict(zip(active, weights.tolist(), strict=True))
        self.w_catboost = float(mapping.get("catboost", 0.0))
        self.w_poisson = float(mapping.get("poisson", 0.0))
        self.w_mlp = float(mapping.get("mlp", 0.0))
        self.w_sequence = float(mapping.get("sequence", 0.0))

    def tune_weights(
        self,
        fixtures: list[Fixture],
        actuals: list[Outcome],
        cfg: EnsembleTuneConfig | None = None,
    ) -> dict[str, object]:
        """Dirichlet-sampling weight tuning on validation pairs (k-way)."""
        cfg = cfg or ENSEMBLE_TUNE_CFG
        if len(fixtures) != len(actuals):
            raise ValueError("fixtures and actuals must be same length")

        member_probs = self._precompute_member_probs(fixtures)
        active = self._active_members()

        rng = np.random.default_rng(42)
        alpha = np.asarray(cfg.dirichlet_alpha[: len(active)], dtype=float)
        if alpha.shape[0] != len(active):
            raise ValueError(
                f"dirichlet_alpha has {len(cfg.dirichlet_alpha)} entries but "
                f"{len(active)} ensemble members are active."
            )
        samples = rng.dirichlet(alpha, size=cfg.dirichlet_samples)

        stacked = np.stack([member_probs[name] for name in active], axis=0)  # (K, N, 3)

        best_metric = float("inf")
        best_weights: np.ndarray | None = None

        for weights in samples:
            blended = np.tensordot(weights, stacked, axes=1)  # (N, 3)
            row_sum = blended.sum(axis=1, keepdims=True)
            blended = blended / np.where(row_sum > 0, row_sum, 1.0)
            pairs = [
                ((float(p[0]), float(p[1]), float(p[2])), a)
                for p, a in zip(blended, actuals, strict=True)
            ]

            if cfg.metric == "rps":
                metric = mean_rps(pairs)
            elif cfg.metric == "log_loss":
                metric = float(np.mean([log_loss_3way(p, a) for p, a in pairs]))
            elif cfg.metric == "brier":
                metric = float(np.mean([brier_score(p, a) for p, a in pairs]))
            else:
                raise ValueError(f"Unknown metric: {cfg.metric}")

            if metric < best_metric:
                best_metric = metric
                best_weights = weights

        if best_weights is None:
            raise RuntimeError("No valid weight sample found.")

        self._assign_weights(active, best_weights)

        return {
            "best_w_catboost": self.w_catboost,
            "best_w_poisson": self.w_poisson,
            "best_w_mlp": self.w_mlp,
            "best_w_sequence": self.w_sequence,
            f"best_{cfg.metric}": best_metric,
            "n_samples_tried": cfg.dirichlet_samples,
            "active_members": active,
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
        """CLV-aware Dirichlet sampling (Phase 6, k-way generalized).

        Supports objectives: ``rps``, ``log_loss``, ``brier``, ``clv``,
        ``blended`` (z-score mix of -RPS and CLV).
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

        member_probs = self._precompute_member_probs(fixtures)
        active = self._active_members()
        stacked = np.stack([member_probs[name] for name in active], axis=0)  # (K, N, 3)

        opening_market: list[tuple[float, float, float] | None] | None = None
        if objective in ("clv", "blended"):
            assert bet_odds is not None
            opening_market = _precompute_market_probs(bet_odds, bet_cfg)

        rng = np.random.default_rng(42)
        alpha = np.asarray(cfg.dirichlet_alpha[: len(active)], dtype=float)
        if alpha.shape[0] != len(active):
            raise ValueError(
                f"dirichlet_alpha has {len(cfg.dirichlet_alpha)} entries but "
                f"{len(active)} ensemble members are active."
            )
        samples = rng.dirichlet(alpha, size=cfg.dirichlet_samples)

        rps_scores: list[float] = []
        clv_scores: list[float] = []
        clv_n: list[int] = []
        brier_scores: list[float] = []
        logloss_scores: list[float] = []

        for weights in samples:
            blended_probs = np.tensordot(weights, stacked, axes=1)  # (N, 3)
            row_sum = blended_probs.sum(axis=1, keepdims=True)
            blended_probs = blended_probs / np.where(row_sum > 0, row_sum, 1.0)

            pairs = [
                ((float(p[0]), float(p[1]), float(p[2])), a)
                for p, a in zip(blended_probs, actuals, strict=True)
            ]

            if objective == "rps":
                rps_scores.append(mean_rps(pairs))
            elif objective == "log_loss":
                rps_scores.append(float(np.mean([log_loss_3way(p, a) for p, a in pairs])))
            elif objective == "brier":
                rps_scores.append(float(np.mean([brier_score(p, a) for p, a in pairs])))
            elif objective == "brier_logloss_blended":
                brier_scores.append(float(np.mean([brier_score(p, a) for p, a in pairs])))
                logloss_scores.append(float(np.mean([log_loss_3way(p, a) for p, a in pairs])))

            if objective in ("clv", "blended"):
                assert opening_market is not None
                assert bet_odds is not None and closing_odds is not None
                bet_open, bet_close = _simulate_bets_for_clv(
                    blended_probs,
                    opening_market,
                    bet_odds,
                    closing_odds,
                    bet_cfg,
                )
                stats = clv_summary(bet_open, bet_close)
                clv_scores.append(float(stats["mean_clv"]))
                clv_n.append(int(stats["n"]))
                if objective == "blended":
                    rps_scores.append(mean_rps(pairs))

        if objective in ("rps", "log_loss", "brier"):
            best_idx = int(np.argmin(rps_scores))
            best_metric_val = float(rps_scores[best_idx])
            metric_key = f"best_{objective}"
        elif objective == "clv":
            best_idx = int(np.argmax(clv_scores))
            best_metric_val = float(clv_scores[best_idx])
            metric_key = "best_clv_mean"
        elif objective == "brier_logloss_blended":
            # Minimise an equally-weighted z-score blend of both proper
            # scoring rules. Both are "lower-is-better".
            b_arr = np.asarray(brier_scores, dtype=float)
            l_arr = np.asarray(logloss_scores, dtype=float)
            score = 0.5 * _zscore(b_arr) + 0.5 * _zscore(l_arr)
            best_idx = int(np.argmin(score))
            best_metric_val = float(score[best_idx])
            metric_key = "best_brier_logloss_blended"
        else:  # blended (rps × CLV)
            rps_arr = np.asarray(rps_scores, dtype=float)
            clv_arr = np.asarray(clv_scores, dtype=float)
            rps_z = _zscore(-rps_arr)
            clv_z = _zscore(clv_arr)
            score = blend * rps_z + (1.0 - blend) * clv_z
            best_idx = int(np.argmax(score))
            best_metric_val = float(score[best_idx])
            metric_key = "best_blended"

        best_weights = samples[best_idx]
        self._assign_weights(active, best_weights)

        result: dict[str, object] = {
            "objective": objective,
            "best_w_catboost": self.w_catboost,
            "best_w_poisson": self.w_poisson,
            "best_w_mlp": self.w_mlp,
            "best_w_sequence": self.w_sequence,
            metric_key: best_metric_val,
            "n_samples_tried": cfg.dirichlet_samples,
            "active_members": active,
        }
        if clv_scores:
            result["clv_mean_at_best"] = float(clv_scores[best_idx])
            result["clv_n_at_best"] = int(clv_n[best_idx])
        if rps_scores and objective == "blended":
            result["rps_at_best"] = float(rps_scores[best_idx])
        if objective == "brier_logloss_blended":
            result["brier_at_best"] = float(brier_scores[best_idx])
            result["log_loss_at_best"] = float(logloss_scores[best_idx])
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
    for i, (mp_row, bo_row, co_row) in enumerate(
        zip(market_probs, bet_odds, closing_odds, strict=True)
    ):
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
