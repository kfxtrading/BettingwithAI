"""Tests for the dual-model 1X2 / value split."""

from __future__ import annotations

from datetime import date

from football_betting.config import (
    MODEL_ARTIFACT_SUFFIX,
    VALUE_MODEL_CFG,
    artifact_suffix,
    should_drop_feature,
)
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.ensemble import ensemble_weights_path


def test_artifact_suffix_returns_empty_for_1x2() -> None:
    assert artifact_suffix("1x2") == ""
    assert MODEL_ARTIFACT_SUFFIX["1x2"] == ""


def test_artifact_suffix_returns_value_suffix() -> None:
    assert artifact_suffix("value") == "_value"
    assert MODEL_ARTIFACT_SUFFIX["value"] == "_value"


def test_value_config_blocks_market_and_mm_prefixes() -> None:
    assert "market_" in VALUE_MODEL_CFG.feature_blocklist_prefixes
    assert "mm_" in VALUE_MODEL_CFG.feature_blocklist_prefixes
    assert VALUE_MODEL_CFG.use_kelly_loss is True


def test_should_drop_feature_matches_prefixes_and_exact() -> None:
    assert should_drop_feature("market_p_home") is True
    assert should_drop_feature("mm_opening_closing_drift_h") is True
    assert should_drop_feature("pi_rating_home") is False
    assert should_drop_feature("league_home_adv") is False


def test_feature_builder_applies_blocklist() -> None:
    fb_plain = FeatureBuilder()
    fb_value = FeatureBuilder(
        feature_blocklist_prefixes=VALUE_MODEL_CFG.feature_blocklist_prefixes,
        feature_blocklist_exact=VALUE_MODEL_CFG.feature_blocklist_exact,
    )

    plain_feats = fb_plain.build_features(
        home_team="Bayern Munich",
        away_team="Dortmund",
        league_key="BL",
        match_date=date(2024, 8, 24),
        odds_home=1.5,
        odds_draw=4.0,
        odds_away=6.0,
        season="2024-25",
    )
    value_feats = fb_value.build_features(
        home_team="Bayern Munich",
        away_team="Dortmund",
        league_key="BL",
        match_date=date(2024, 8, 24),
        odds_home=1.5,
        odds_draw=4.0,
        odds_away=6.0,
        season="2024-25",
    )

    # 1X2 builder emits market features; value builder strips them.
    assert any(k.startswith("market_") for k in plain_feats)
    assert not any(k.startswith("market_") for k in value_feats)
    assert not any(k.startswith("mm_") for k in value_feats)
    # Non-blocklisted features must be identical between the two.
    for k, v in value_feats.items():
        assert k in plain_feats
        assert plain_feats[k] == v


def test_ensemble_weights_path_respects_purpose(tmp_path) -> None:  # noqa: ANN001
    p_1x2 = ensemble_weights_path("BL", "1x2")
    p_val = ensemble_weights_path("BL", "value")
    assert p_1x2.name == "ensemble_weights_BL.json"
    assert p_val.name == "ensemble_weights_BL_value.json"
