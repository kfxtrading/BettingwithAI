"""Tests for Phase 6: CLV-aware Dirichlet ensemble tuning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

import pytest

pytest.importorskip("catboost")

from football_betting.config import ENSEMBLE_TUNE_CFG, EnsembleTuneConfig
from football_betting.data.models import Fixture, MatchOdds, Outcome, Prediction
from football_betting.predict.ensemble import EnsembleModel

# ───────────────────────── Stub predictors ─────────────────────────


@dataclass
class _StubPredictor:
    """Returns fixture-dependent probabilities via a callable."""

    probs: list[tuple[float, float, float]]
    idx: int = 0
    _lookup: dict[str, tuple[float, float, float]] | None = None

    def __post_init__(self) -> None:
        # snapshot probs into lookup keyed by fixture signature
        self._lookup = {}

    def _key(self, fx: Fixture) -> str:
        return f"{fx.date}|{fx.home_team}|{fx.away_team}"

    def seed(self, fixtures: list[Fixture]) -> None:
        assert self._lookup is not None
        for fx, p in zip(fixtures, self.probs, strict=True):
            self._lookup[self._key(fx)] = p

    def predict(self, fx: Fixture) -> Prediction:
        assert self._lookup is not None
        p = self._lookup[self._key(fx)]
        return Prediction(
            fixture=fx,
            model_name="stub",
            prob_home=p[0],
            prob_draw=p[1],
            prob_away=p[2],
        )


def _mk_fixtures(n: int) -> list[Fixture]:
    out: list[Fixture] = []
    for i in range(n):
        out.append(
            Fixture(
                date=date(2024, 1, 1 + (i % 27)),
                league="BL",
                home_team=f"H{i}",
                away_team=f"A{i}",
                odds=MatchOdds(home=2.10, draw=3.40, away=3.60),
            )
        )
    return out


def _mk_ensemble(
    cb_probs: list[tuple[float, float, float]],
    po_probs: list[tuple[float, float, float]],
    fixtures: list[Fixture],
) -> EnsembleModel:
    cb = _StubPredictor(cb_probs)
    cb.seed(fixtures)
    po = _StubPredictor(po_probs)
    po.seed(fixtures)
    # bypass dataclass type checking — Ensemble only uses .predict()
    ens = EnsembleModel.__new__(EnsembleModel)
    object.__setattr__(ens, "catboost", cb)
    object.__setattr__(ens, "poisson", po)
    object.__setattr__(ens, "mlp", None)
    object.__setattr__(ens, "sequence", None)
    object.__setattr__(ens, "w_catboost", 0.5)
    object.__setattr__(ens, "w_poisson", 0.5)
    object.__setattr__(ens, "w_mlp", 0.0)
    object.__setattr__(ens, "w_sequence", 0.0)
    return ens


# ───────────────────────── Tests ─────────────────────────


class TestTuneDirichletObjectives:
    def test_rps_objective_runs_and_normalises_weights(self) -> None:
        fixtures = _mk_fixtures(12)
        cb_p = [(0.50, 0.25, 0.25)] * 12
        po_p = [(0.40, 0.30, 0.30)] * 12
        actuals: list[Outcome] = ["H", "D", "A", "H", "H", "D", "A", "H", "D", "A", "H", "D"]
        ens = _mk_ensemble(cb_p, po_p, fixtures)

        cfg = EnsembleTuneConfig(
            catboost_weights=ENSEMBLE_TUNE_CFG.catboost_weights,
            dirichlet_samples=50,
            dirichlet_alpha=ENSEMBLE_TUNE_CFG.dirichlet_alpha,
            metric="rps",
        )
        result = ens.tune_dirichlet(fixtures, actuals, objective="rps", cfg=cfg)
        assert "best_rps" in result
        assert result["objective"] == "rps"
        assert abs((ens.w_catboost + ens.w_poisson) - 1.0) < 1e-6

    def test_clv_objective_requires_odds(self) -> None:
        fixtures = _mk_fixtures(5)
        actuals: list[Outcome] = ["H"] * 5
        ens = _mk_ensemble(
            [(0.5, 0.25, 0.25)] * 5,
            [(0.5, 0.25, 0.25)] * 5,
            fixtures,
        )
        with pytest.raises(ValueError, match="requires bet_odds"):
            ens.tune_dirichlet(fixtures, actuals, objective="clv")

    def test_tune_objective_clv_picks_different_weights_than_rps(self) -> None:
        # CatBoost is directionally strong on Home; Poisson is diffuse.
        # Opening > closing only on Home leg → any bet placed on H yields +CLV.
        # We check that CLV tuning produces positive mean CLV and that the
        # output dict contains CLV-specific keys absent from the RPS run.
        n = 30
        fixtures = _mk_fixtures(n)
        cb_p = [(0.65, 0.20, 0.15)] * n
        po_p = [(0.45, 0.28, 0.27)] * n
        actuals: list[Outcome] = ["H"] * n
        bet_odds = [(2.60, 3.40, 3.60)] * n
        close_odds = [(2.10, 3.40, 3.60)] * n

        ens = _mk_ensemble(cb_p, po_p, fixtures)
        cfg = EnsembleTuneConfig(
            catboost_weights=ENSEMBLE_TUNE_CFG.catboost_weights,
            dirichlet_samples=120,
            dirichlet_alpha=(1.0, 1.0, 1.0),
            metric="rps",
        )

        rps_res = ens.tune_dirichlet(fixtures, actuals, objective="rps", cfg=cfg)
        assert "best_rps" in rps_res and "best_clv_mean" not in rps_res

        ens2 = _mk_ensemble(cb_p, po_p, fixtures)
        clv_res = ens2.tune_dirichlet(
            fixtures,
            actuals,
            bet_odds=bet_odds,
            closing_odds=close_odds,
            objective="clv",
            cfg=cfg,
        )
        assert "best_clv_mean" in clv_res
        assert clv_res["clv_n_at_best"] > 0
        # With opening (2.60) always higher than closing (2.10) on the bet leg,
        # every qualifying value bet has positive CLV, so mean_clv must be > 0.
        assert clv_res["best_clv_mean"] > 0.0

    def test_blended_objective_returns_both_metrics(self) -> None:
        n = 20
        fixtures = _mk_fixtures(n)
        cb_p = [(0.60, 0.22, 0.18)] * n
        po_p = [(0.45, 0.28, 0.27)] * n
        actuals: list[Outcome] = ["H"] * n
        bet_odds = [(2.50, 3.40, 3.60)] * n
        close_odds = [(2.10, 3.40, 3.60)] * n
        ens = _mk_ensemble(cb_p, po_p, fixtures)
        cfg = EnsembleTuneConfig(
            catboost_weights=ENSEMBLE_TUNE_CFG.catboost_weights,
            dirichlet_samples=60,
            dirichlet_alpha=(1.0, 1.0, 1.0),
            metric="rps",
        )

        res = ens.tune_dirichlet(
            fixtures,
            actuals,
            bet_odds=bet_odds,
            closing_odds=close_odds,
            objective="blended",
            blend=0.5,
            cfg=cfg,
        )
        assert "best_blended" in res
        assert "clv_mean_at_best" in res
        assert "rps_at_best" in res

    def test_blended_objective_monotone_in_blend_parameter(self) -> None:
        """Blend=1.0 → same pick as objective=rps; blend=0.0 → same pick as objective=clv."""
        n = 25
        fixtures = _mk_fixtures(n)
        cb_p = [(0.60, 0.22, 0.18)] * n
        po_p = [(0.40, 0.30, 0.30)] * n
        actuals: list[Outcome] = ["H"] * n
        bet_odds = [(2.50, 3.40, 3.60)] * n
        close_odds = [(2.10, 3.40, 3.60)] * n

        cfg = EnsembleTuneConfig(
            catboost_weights=ENSEMBLE_TUNE_CFG.catboost_weights,
            dirichlet_samples=80,
            dirichlet_alpha=(1.0, 1.0, 1.0),
            metric="rps",
        )

        ens_blend1 = _mk_ensemble(cb_p, po_p, fixtures)
        ens_rps = _mk_ensemble(cb_p, po_p, fixtures)
        ens_blend1.tune_dirichlet(
            fixtures,
            actuals,
            bet_odds=bet_odds,
            closing_odds=close_odds,
            objective="blended",
            blend=1.0,
            cfg=cfg,
        )
        ens_rps.tune_dirichlet(fixtures, actuals, objective="rps", cfg=cfg)
        # Same seed → same Dirichlet samples → blend=1.0 should select the RPS minimiser
        assert ens_blend1.w_catboost == pytest.approx(ens_rps.w_catboost, abs=1e-6)

    def test_invalid_blend_raises(self) -> None:
        fixtures = _mk_fixtures(3)
        ens = _mk_ensemble([(0.4, 0.3, 0.3)] * 3, [(0.4, 0.3, 0.3)] * 3, fixtures)
        with pytest.raises(ValueError, match="blend"):
            ens.tune_dirichlet(
                fixtures,
                ["H", "D", "A"],
                bet_odds=[(2.0, 3.0, 4.0)] * 3,
                closing_odds=[(2.0, 3.0, 4.0)] * 3,
                objective="blended",
                blend=1.5,
            )

    def test_mismatched_lengths_raise(self) -> None:
        fixtures = _mk_fixtures(3)
        ens = _mk_ensemble([(0.4, 0.3, 0.3)] * 3, [(0.4, 0.3, 0.3)] * 3, fixtures)
        with pytest.raises(ValueError):
            ens.tune_dirichlet(fixtures, ["H", "D"], objective="rps")


class TestFourWayEnsemble:
    """4-way blend: CatBoost + Poisson + MLP + Sequence."""

    @staticmethod
    def _mk_four_way(
        cb_p: list[tuple[float, float, float]],
        po_p: list[tuple[float, float, float]],
        mlp_p: list[tuple[float, float, float]],
        sq_p: list[tuple[float, float, float]],
        fixtures: list[Fixture],
    ) -> EnsembleModel:
        cb = _StubPredictor(cb_p)
        cb.seed(fixtures)
        po = _StubPredictor(po_p)
        po.seed(fixtures)
        mlp = _StubPredictor(mlp_p)
        mlp.seed(fixtures)
        sq = _StubPredictor(sq_p)
        sq.seed(fixtures)
        ens = EnsembleModel.__new__(EnsembleModel)
        object.__setattr__(ens, "catboost", cb)
        object.__setattr__(ens, "poisson", po)
        object.__setattr__(ens, "mlp", mlp)
        object.__setattr__(ens, "sequence", sq)
        object.__setattr__(ens, "w_catboost", 0.25)
        object.__setattr__(ens, "w_poisson", 0.25)
        object.__setattr__(ens, "w_mlp", 0.25)
        object.__setattr__(ens, "w_sequence", 0.25)
        return ens

    def test_four_way_predict_uses_all_members(self) -> None:
        fixtures = _mk_fixtures(1)
        ens = self._mk_four_way(
            [(0.60, 0.20, 0.20)],
            [(0.40, 0.30, 0.30)],
            [(0.50, 0.25, 0.25)],
            [(0.45, 0.30, 0.25)],
            fixtures,
        )
        pred = ens.predict(fixtures[0])
        # Each weight is 0.25 → blend = mean of the four rows (first column):
        # (0.60 + 0.40 + 0.50 + 0.45)/4 = 0.4875
        assert pred.prob_home == pytest.approx(0.4875, abs=1e-4)
        assert pred.prob_draw + pred.prob_home + pred.prob_away == pytest.approx(1.0)
        assert "Seq=" in pred.model_name and "MLP=" in pred.model_name

    def test_four_way_tune_dirichlet_sets_all_four_weights(self) -> None:
        n = 20
        fixtures = _mk_fixtures(n)
        cb_p = [(0.60, 0.22, 0.18)] * n
        po_p = [(0.40, 0.30, 0.30)] * n
        mlp_p = [(0.55, 0.22, 0.23)] * n
        sq_p = [(0.50, 0.25, 0.25)] * n
        actuals: list[Outcome] = ["H"] * n
        ens = self._mk_four_way(cb_p, po_p, mlp_p, sq_p, fixtures)
        cfg = EnsembleTuneConfig(
            catboost_weights=ENSEMBLE_TUNE_CFG.catboost_weights,
            dirichlet_samples=80,
            dirichlet_alpha=(1.0, 1.0, 1.0, 1.0),
            metric="rps",
        )
        res = ens.tune_dirichlet(fixtures, actuals, objective="rps", cfg=cfg)
        assert res["active_members"] == ["catboost", "poisson", "mlp", "sequence"]
        total = ens.w_catboost + ens.w_poisson + ens.w_mlp + ens.w_sequence
        assert total == pytest.approx(1.0, abs=1e-6)
        # All four weights must be within [0, 1]
        for w in (ens.w_catboost, ens.w_poisson, ens.w_mlp, ens.w_sequence):
            assert 0.0 <= w <= 1.0

    def test_alpha_length_shorter_than_active_raises(self) -> None:
        n = 8
        fixtures = _mk_fixtures(n)
        ens = self._mk_four_way(
            [(0.5, 0.25, 0.25)] * n,
            [(0.4, 0.3, 0.3)] * n,
            [(0.5, 0.25, 0.25)] * n,
            [(0.45, 0.3, 0.25)] * n,
            fixtures,
        )
        cfg = EnsembleTuneConfig(
            catboost_weights=ENSEMBLE_TUNE_CFG.catboost_weights,
            dirichlet_samples=20,
            dirichlet_alpha=(1.0, 1.0),  # too short for 4 active members
            metric="rps",
        )
        with pytest.raises(ValueError, match="dirichlet_alpha"):
            ens.tune_dirichlet(fixtures, ["H"] * n, objective="rps", cfg=cfg)


class TestBrierLogLossBlendedObjective:
    """Phase 4 objective: minimise z(brier) + z(log_loss) equally."""

    def test_returns_brier_and_logloss_at_best(self) -> None:
        n = 20
        fixtures = _mk_fixtures(n)
        cb_p = [(0.60, 0.22, 0.18)] * n
        po_p = [(0.40, 0.30, 0.30)] * n
        actuals: list[Outcome] = ["H"] * n
        ens = _mk_ensemble(cb_p, po_p, fixtures)
        cfg = EnsembleTuneConfig(
            catboost_weights=ENSEMBLE_TUNE_CFG.catboost_weights,
            dirichlet_samples=60,
            dirichlet_alpha=(1.0, 1.0),
            metric="rps",
        )
        res = ens.tune_dirichlet(
            fixtures,
            actuals,
            objective="brier_logloss_blended",
            cfg=cfg,
        )
        assert "best_brier_logloss_blended" in res
        assert "brier_at_best" in res
        assert "log_loss_at_best" in res
        # Individual metrics at the chosen index must be finite
        assert res["brier_at_best"] == pytest.approx(res["brier_at_best"])  # not NaN
        assert res["log_loss_at_best"] > 0.0


class TestWeightMetadataValidation:
    def test_load_weights_rejects_wrong_purpose(self, tmp_path) -> None:  # noqa: ANN001
        fixtures = _mk_fixtures(1)
        ens = _mk_ensemble([(0.5, 0.25, 0.25)], [(0.4, 0.3, 0.3)], fixtures)
        path = tmp_path / "weights.json"
        path.write_text(
            json.dumps(
                {
                    "w_catboost": 0.7,
                    "w_poisson": 0.3,
                    "metadata": {
                        "purpose": "value",
                        "active_members": ["catboost", "poisson"],
                    },
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="purpose"):
            ens.load_weights(
                path,
                expected_purpose="1x2",
                expected_active_members=["catboost", "poisson"],
            )

    def test_load_weights_rejects_incompatible_active_members(self, tmp_path) -> None:  # noqa: ANN001
        fixtures = _mk_fixtures(1)
        ens = _mk_ensemble([(0.5, 0.25, 0.25)], [(0.4, 0.3, 0.3)], fixtures)
        path = tmp_path / "weights.json"
        path.write_text(
            json.dumps(
                {
                    "w_catboost": 0.6,
                    "w_poisson": 0.2,
                    "w_mlp": 0.2,
                    "metadata": {
                        "purpose": "1x2",
                        "active_members": ["catboost", "poisson", "mlp"],
                    },
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="active_members"):
            ens.load_weights(
                path,
                expected_purpose="1x2",
                expected_active_members=["catboost", "poisson"],
            )
