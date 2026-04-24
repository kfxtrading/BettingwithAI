"""Phase C of ``_plans/gpu_kelly_training_plan.md``.

Smoke + regression tests for the CLV-aware shrinkage-Kelly training path
wired into :class:`MLPPredictor`, :class:`SequencePredictor`, and
:class:`TabTransformerPredictor`.

We keep these tests light — the goal is to catch structural wiring bugs
(DataLoader tuple arity, opening-odds alignment, coverage logging, early-
stop switch) rather than predictive quality, which is covered by the
league-level backtest suite.
"""

from __future__ import annotations

import dataclasses
from datetime import date, timedelta

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from football_betting.config import (  # noqa: E402
    MLPConfig,
    SequenceConfig,
    TabTransformerConfig,
)
from football_betting.data.models import Match, MatchOdds  # noqa: E402
from football_betting.predict.losses import kelly_growth_metric  # noqa: E402

# ───────────────────────── helpers ─────────────────────────


def _mk_match(
    day_offset: int,
    home: str,
    away: str,
    hg: int,
    ag: int,
    *,
    with_opening: bool = True,
) -> Match:
    odds = MatchOdds(home=2.0, draw=3.4, away=3.8)
    opening = MatchOdds(home=2.1, draw=3.3, away=3.6) if with_opening else None
    return Match(
        date=date(2023, 1, 1) + timedelta(days=day_offset),
        league="BL",
        season="2022-23",
        home_team=home,
        away_team=away,
        home_goals=hg,
        away_goals=ag,
        odds=odds,
        opening_odds=opening,
    )


def _synthetic_matches(n: int = 300, opening_fraction: float = 0.7) -> list[Match]:
    """Create a chronologically-ordered league with round-robin teams.

    Half of the matches are missing opening odds so the Kelly-mask is
    non-trivially split (exercises the masking code path).
    """
    teams = [f"T{i:02d}" for i in range(12)]
    rng = np.random.default_rng(0)
    matches: list[Match] = []
    for i in range(n):
        h = teams[i % len(teams)]
        a = teams[(i * 3 + 1) % len(teams)]
        if h == a:
            a = teams[(i + 1) % len(teams)]
        hg = int(rng.integers(0, 4))
        ag = int(rng.integers(0, 4))
        with_open = rng.random() < opening_fraction
        matches.append(_mk_match(i, h, a, hg, ag, with_opening=with_open))
    return matches


# ───────────────────────── kelly_growth_metric ─────────────────────────


def test_kelly_growth_metric_zero_on_empty_mask() -> None:
    probs = torch.tensor([[0.4, 0.3, 0.3], [0.3, 0.4, 0.3]])
    odds = torch.tensor([[2.0, 3.5, 4.0], [2.5, 3.2, 3.0]])
    y = torch.tensor([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    mask = torch.tensor([False, False])
    assert kelly_growth_metric(probs, odds, y, mask=mask) == 0.0


def test_kelly_growth_metric_is_positive_for_value_bet() -> None:
    # 60% prob on an outcome at odds 2.0 → strong +EV; Kelly f* > 0, win realises gain.
    probs = torch.tensor([[0.6, 0.2, 0.2]])
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    y = torch.tensor([[1.0, 0.0, 0.0]])
    g = kelly_growth_metric(probs, odds, y)
    assert g > 0.0


def test_kelly_growth_metric_nonpositive_for_neutral_bet() -> None:
    # Market-aligned probs on odds equal to 1/prob → zero edge, f*=0, growth=0.
    probs = torch.tensor([[1 / 2.0, 1 / 3.5, 1 / 4.0]])
    probs = probs / probs.sum(dim=1, keepdim=True)
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    y = torch.tensor([[1.0, 0.0, 0.0]])
    g = kelly_growth_metric(probs, odds, y)
    assert g == pytest.approx(0.0, abs=1e-6)


# ───────────────────────── config flags ─────────────────────────


def test_all_three_configs_have_phase_c_fields() -> None:
    for cfg in (MLPConfig(), SequenceConfig(), TabTransformerConfig()):
        assert hasattr(cfg, "use_shrinkage_kelly")
        assert cfg.use_shrinkage_kelly is False
        assert hasattr(cfg, "kelly_beta")
        assert hasattr(cfg, "kelly_warmup_epochs")
        assert hasattr(cfg, "kelly_lam_max")


def test_dataclass_replace_enables_shrinkage() -> None:
    cfg = dataclasses.replace(MLPConfig(), use_shrinkage_kelly=True, epochs=3)
    assert cfg.use_shrinkage_kelly is True
    assert cfg.epochs == 3


# ───────────────────────── TabTransformer.build_training_data ─────────────────────────


def test_tab_transformer_build_training_data_returns_odds_when_requested() -> None:
    from football_betting.predict.runtime import make_feature_builder
    from football_betting.predict.tabular_transformer import TabTransformerPredictor

    fb = make_feature_builder(purpose="1x2")
    tab = TabTransformerPredictor(feature_builder=fb, purpose="1x2")

    matches = _synthetic_matches(n=250, opening_fraction=0.6)

    # Back-compat: 2-tuple
    out2 = tab.build_training_data(matches, warmup_games=50)
    assert len(out2) == 2

    # New: 3-tuple with closing-odds
    out3 = tab.build_training_data(matches, warmup_games=50, return_odds=True)
    assert len(out3) == 3
    df, y, odds = out3
    assert odds.shape == (len(df), 3)
    assert odds.dtype == np.float32
    assert np.all(odds > 1.0)


# ───────────────────────── MLP fit smoke ─────────────────────────


def test_mlp_fit_shrinkage_path_runs_end_to_end() -> None:
    from football_betting.predict.mlp_model import MLPPredictor
    from football_betting.predict.runtime import make_feature_builder

    cfg = dataclasses.replace(
        MLPConfig(),
        use_shrinkage_kelly=True,
        epochs=2,
        early_stopping_patience=5,
        batch_size=32,
        hidden_dims=(16, 8),
        kelly_warmup_epochs=1,
    )
    fb = make_feature_builder(purpose="1x2")
    mlp = MLPPredictor(feature_builder=fb, cfg=cfg, purpose="1x2")

    matches = _synthetic_matches(n=260, opening_fraction=0.6)
    result = mlp.fit(matches, warmup_games=30, calibrate=False)

    assert result["best_val_growth"] is not None
    assert result["kelly_mask_coverage"] is not None
    assert 0.0 < result["kelly_mask_coverage"] <= 1.0
    # Coverage from synthetic matches should be close to opening_fraction (± 15 pp).
    assert abs(result["kelly_mask_coverage"] - 0.6) < 0.2


def test_mlp_fit_default_path_unchanged() -> None:
    """Back-compat: default cfg still falls through to plain-CE early-stop."""
    from football_betting.predict.mlp_model import MLPPredictor
    from football_betting.predict.runtime import make_feature_builder

    cfg = dataclasses.replace(
        MLPConfig(),
        epochs=2,
        early_stopping_patience=5,
        batch_size=32,
        hidden_dims=(16, 8),
    )
    fb = make_feature_builder(purpose="1x2")
    mlp = MLPPredictor(feature_builder=fb, cfg=cfg, purpose="1x2")

    matches = _synthetic_matches(n=260, opening_fraction=0.6)
    result = mlp.fit(matches, warmup_games=30, calibrate=False)

    assert result["best_val_growth"] is None
    assert result["kelly_mask_coverage"] is None
