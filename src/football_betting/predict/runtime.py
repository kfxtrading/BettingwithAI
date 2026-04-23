"""Shared runtime helpers for league model composition and profile persistence.

This module deliberately keeps top-level imports lightweight so profile and
path logic can be tested without the full ML stack installed.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from football_betting.config import (
    BETTING_CFG,
    MLP_CFG,
    MODELS_DIR,
    SEQUENCE_CFG,
    VALUE_MODEL_CFG,
    BettingConfig,
    MLPConfig,
    ModelPurpose,
    SequenceConfig,
    artifact_suffix,
)

if TYPE_CHECKING:
    from football_betting.data.models import Match
    from football_betting.features.builder import FeatureBuilder

logger = logging.getLogger(__name__)

ActiveMember = Literal["catboost", "poisson", "mlp", "sequence"]
ModelKind = Literal["poisson", "catboost", "ensemble"]

ACTIVE_MEMBER_ORDER: tuple[ActiveMember, ...] = ("catboost", "poisson", "mlp", "sequence")


@dataclass(frozen=True, slots=True)
class LeagueModelProfile:
    """Persisted per-league runtime profile for one model purpose."""

    league_key: str
    purpose: ModelPurpose
    model_kind: ModelKind = "ensemble"
    active_members: tuple[ActiveMember, ...] = ("catboost", "poisson")
    calibration_method: str | None = None
    weight_objective: str | None = None
    weight_blend: float | None = None
    stacking: bool = False
    betting: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "league_key": self.league_key,
            "purpose": self.purpose,
            "model_kind": self.model_kind,
            "active_members": list(self.active_members),
            "calibration_method": self.calibration_method,
            "weight_objective": self.weight_objective,
            "weight_blend": self.weight_blend,
            "stacking": self.stacking,
        }
        if self.betting:
            payload["betting"] = dict(self.betting)
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> LeagueModelProfile:
        purpose = cast(ModelPurpose, str(raw.get("purpose", "1x2")).lower())
        model_kind = cast(ModelKind, str(raw.get("model_kind", "ensemble")).lower())
        active_members = normalize_active_members(raw.get("active_members"))
        calibration_method = raw.get("calibration_method")
        weight_objective = raw.get("weight_objective")
        weight_blend = raw.get("weight_blend")
        betting = raw.get("betting")
        return cls(
            league_key=str(raw.get("league_key", "")).upper(),
            purpose=purpose,
            model_kind=model_kind,
            active_members=active_members,
            calibration_method=str(calibration_method) if calibration_method is not None else None,
            weight_objective=str(weight_objective) if weight_objective is not None else None,
            weight_blend=float(weight_blend) if isinstance(weight_blend, (int, float)) else None,
            stacking=bool(raw.get("stacking", False)),
            betting=dict(betting) if isinstance(betting, dict) else None,
        )


def normalize_active_members(raw: object) -> tuple[ActiveMember, ...]:
    """Return unique active-member names in canonical ensemble order."""
    if raw is None:
        return ("catboost", "poisson")
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"active_members must be a list/tuple, got {type(raw)!r}")
    requested = {str(v).lower() for v in raw}
    unknown = sorted(requested.difference(ACTIVE_MEMBER_ORDER))
    if unknown:
        raise ValueError(f"Unknown ensemble members: {unknown}")
    active = tuple(name for name in ACTIVE_MEMBER_ORDER if name in requested)
    if not active:
        raise ValueError("active_members must not be empty")
    return cast(tuple[ActiveMember, ...], active)


def model_profile_path(league_key: str, purpose: ModelPurpose = "1x2") -> Path:
    """Canonical path for a persisted league profile."""
    return MODELS_DIR / f"model_profile_{league_key.upper()}{artifact_suffix(purpose)}.json"


def ensemble_weights_json_path(league_key: str, purpose: ModelPurpose = "1x2") -> Path:
    """Canonical path for ensemble weights without importing the heavy ensemble module."""
    return MODELS_DIR / f"ensemble_weights_{league_key.upper()}{artifact_suffix(purpose)}.json"


def load_model_profile(
    league_key: str,
    purpose: ModelPurpose = "1x2",
    *,
    path: Path | None = None,
) -> LeagueModelProfile | None:
    """Load a saved profile if present."""
    profile_path = path or model_profile_path(league_key, purpose)
    if not profile_path.exists():
        return None
    raw = json.loads(profile_path.read_text(encoding="utf-8"))
    profile = LeagueModelProfile.from_dict(raw)
    return replace(profile, league_key=league_key.upper(), purpose=purpose)


def save_model_profile(profile: LeagueModelProfile, *, path: Path | None = None) -> Path:
    """Persist a league profile to disk."""
    out_path = path or model_profile_path(profile.league_key, profile.purpose)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
    return out_path


def infer_model_profile(league_key: str, purpose: ModelPurpose = "1x2") -> LeagueModelProfile | None:
    """Best-effort profile inference from locally available artefacts."""
    league_key = league_key.upper()
    suffix = artifact_suffix(purpose)
    catboost_path = MODELS_DIR / f"catboost_{league_key}{suffix}.cbm"
    mlp_path = MODELS_DIR / f"mlp_{league_key}{suffix}.pt"
    sequence_path = MODELS_DIR / f"sequence_{league_key}{suffix}.pt"
    weights_path = ensemble_weights_json_path(league_key, purpose)

    if not catboost_path.exists():
        if purpose == "value":
            return None
        return LeagueModelProfile(
            league_key=league_key,
            purpose=purpose,
            model_kind="poisson",
            active_members=("poisson",),
        )

    active: tuple[ActiveMember, ...] = ("catboost", "poisson")
    if mlp_path.exists():
        active = cast(tuple[ActiveMember, ...], active + ("mlp",))
    if sequence_path.exists():
        active = cast(tuple[ActiveMember, ...], active + ("sequence",))

    calibration_method: str | None = None
    weight_objective: str | None = None
    weight_blend: float | None = None
    if weights_path.exists():
        try:
            raw = json.loads(weights_path.read_text(encoding="utf-8"))
            metadata = raw.get("metadata")
            if isinstance(metadata, dict):
                md_purpose = str(metadata.get("purpose", purpose)).lower()
                if md_purpose == purpose:
                    md_active = metadata.get("active_members")
                    if md_active is not None:
                        inferred = normalize_active_members(md_active)
                        available = {
                            "catboost": catboost_path.exists(),
                            "poisson": True,
                            "mlp": mlp_path.exists(),
                            "sequence": sequence_path.exists(),
                        }
                        filtered = tuple(name for name in inferred if available.get(name, False))
                        if filtered:
                            active = cast(tuple[ActiveMember, ...], filtered)
                    md_cal = metadata.get("calibration_method")
                    if md_cal is not None:
                        calibration_method = str(md_cal)
                    md_obj = metadata.get("objective")
                    if md_obj is not None:
                        weight_objective = str(md_obj)
                    md_blend = metadata.get("blend")
                    if isinstance(md_blend, (int, float)):
                        weight_blend = float(md_blend)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to infer profile from %s: %s", weights_path, exc)

    model_kind: ModelKind = "ensemble" if len(active) > 1 else "catboost"
    if active == ("poisson",):
        model_kind = "poisson"
    return LeagueModelProfile(
        league_key=league_key,
        purpose=purpose,
        model_kind=model_kind,
        active_members=active,
        calibration_method=calibration_method,
        weight_objective=weight_objective,
        weight_blend=weight_blend,
    )


def resolve_model_profile(league_key: str, purpose: ModelPurpose = "1x2") -> LeagueModelProfile | None:
    """Load a saved profile, falling back to artefact inference."""
    return load_model_profile(league_key, purpose) or infer_model_profile(league_key, purpose)


def mlp_config_for_purpose(purpose: ModelPurpose) -> MLPConfig:
    """Return the appropriate MLP config for 1x2 or value training."""
    if purpose == "value":
        return replace(
            MLP_CFG,
            use_kelly_loss=VALUE_MODEL_CFG.use_kelly_loss,
            kelly_lambda=VALUE_MODEL_CFG.kelly_lambda,
            kelly_f_cap=VALUE_MODEL_CFG.kelly_f_cap,
        )
    return MLP_CFG


def sequence_config_for_purpose(purpose: ModelPurpose) -> SequenceConfig:
    """Return the appropriate Sequence config for 1x2 or value training."""
    if purpose == "value":
        return replace(
            SEQUENCE_CFG,
            use_kelly_loss=VALUE_MODEL_CFG.use_kelly_loss,
            kelly_lambda=VALUE_MODEL_CFG.kelly_lambda,
        )
    return SEQUENCE_CFG


def betting_config_from_profile(
    profile: LeagueModelProfile | None,
    fallback: BettingConfig = BETTING_CFG,
) -> BettingConfig:
    """Apply any saved value-bet overrides from ``profile`` to ``fallback``."""
    if profile is None or not profile.betting:
        return fallback
    valid = {field.name for field in fields(BettingConfig)}
    overrides = {k: v for k, v in profile.betting.items() if k in valid}
    if not overrides:
        return fallback
    return replace(fallback, **overrides)


def make_feature_builder(purpose: ModelPurpose = "1x2") -> FeatureBuilder:
    """Construct a feature builder aligned with the requested model purpose."""
    from football_betting.features.builder import FeatureBuilder
    from football_betting.features.weather import WeatherTracker

    kwargs: dict[str, object] = {"weather_tracker": WeatherTracker()}
    if purpose == "value":
        kwargs.update(
            {
                "feature_blocklist_prefixes": VALUE_MODEL_CFG.feature_blocklist_prefixes,
                "feature_blocklist_exact": VALUE_MODEL_CFG.feature_blocklist_exact,
            }
        )
    return FeatureBuilder(**kwargs)


def stage_sofascore_for_seasons(
    feature_builder: FeatureBuilder,
    league_key: str,
    seasons: list[str] | tuple[str, ...] | set[str],
) -> int:
    """Stage locally cached Sofascore matches for the provided seasons."""
    from football_betting.scraping.sofascore import SofascoreClient

    staged = 0
    for season in sorted({str(season) for season in seasons}):
        sf_data = SofascoreClient.load_matches(league_key.upper(), season)
        if sf_data:
            staged += feature_builder.stage_sofascore_batch(sf_data)
    return staged


def warm_feature_builder(
    league_key: str,
    matches: list[Match],
    *,
    purpose: ModelPurpose = "1x2",
) -> tuple[FeatureBuilder, int]:
    """Create, stage and replay a feature builder over historical matches."""
    feature_builder = make_feature_builder(purpose)
    staged = stage_sofascore_for_seasons(
        feature_builder,
        league_key,
        {match.season for match in matches},
    )
    feature_builder.fit_on_history(matches)
    return feature_builder, staged


def warm_sequence_predictor(sequence: object, history_matches: list[Match] | None) -> None:
    """Replay historical matches into a loaded sequence predictor."""
    if not history_matches:
        return
    from football_betting.predict.sequence_features import build_dataset as build_sequence_dataset

    build_sequence_dataset(
        sorted(history_matches, key=lambda match: match.date),
        sequence.form_tracker,  # type: ignore[attr-defined]
        sequence.pi_ratings,  # type: ignore[attr-defined]
        window_t=sequence.cfg.window_t,  # type: ignore[attr-defined]
        warmup_games=0,
    )


def build_league_model(
    league_key: str,
    feature_builder: FeatureBuilder,
    *,
    purpose: ModelPurpose = "1x2",
    profile: LeagueModelProfile | None = None,
    history_matches: list[Match] | None = None,
    strict_profile: bool = False,
) -> tuple[object | None, LeagueModelProfile | None]:
    """Load the strongest configured model for ``league_key`` and ``purpose``."""
    from football_betting.predict.catboost_model import CatBoostPredictor
    from football_betting.predict.ensemble import EnsembleModel
    from football_betting.predict.mlp_model import MLPPredictor
    from football_betting.predict.poisson import PoissonModel
    from football_betting.predict.sequence_model import SequencePredictor

    league_key = league_key.upper()
    resolved = profile or resolve_model_profile(league_key, purpose)
    if resolved is None:
        if purpose == "value":
            return None, None
        resolved = LeagueModelProfile(
            league_key=league_key,
            purpose=purpose,
            model_kind="poisson",
            active_members=("poisson",),
        )

    suffix = artifact_suffix(purpose)
    catboost_path = MODELS_DIR / f"catboost_{league_key}{suffix}.cbm"
    if not catboost_path.exists():
        if purpose == "value":
            if strict_profile:
                raise FileNotFoundError(f"Missing CatBoost artifact for {league_key}/{purpose}")
            return None, resolved
        return PoissonModel(pi_ratings=feature_builder.pi_ratings), replace(
            resolved,
            model_kind="poisson",
            active_members=("poisson",),
        )

    active = list(resolved.active_members)
    if resolved.model_kind == "poisson":
        return PoissonModel(pi_ratings=feature_builder.pi_ratings), replace(
            resolved,
            active_members=("poisson",),
        )

    cb = CatBoostPredictor.for_league(league_key, feature_builder, purpose=purpose)
    poisson = PoissonModel(pi_ratings=feature_builder.pi_ratings)

    if resolved.model_kind == "catboost":
        return cb, replace(resolved, active_members=("catboost",))

    mlp = None
    if "mlp" in active:
        mlp = MLPPredictor.for_league(league_key, feature_builder, purpose=purpose)
        if mlp is None:
            if strict_profile:
                raise FileNotFoundError(f"Missing MLP artifact for {league_key}/{purpose}")
            logger.warning("MLP artifact missing for %s/%s; dropping member", league_key, purpose)
            active.remove("mlp")

    sequence = None
    if "sequence" in active:
        sequence = SequencePredictor.for_league(league_key, purpose=purpose)
        if sequence is None:
            if strict_profile:
                raise FileNotFoundError(f"Missing Sequence artifact for {league_key}/{purpose}")
            logger.warning("Sequence artifact missing for %s/%s; dropping member", league_key, purpose)
            active.remove("sequence")
        else:
            warm_sequence_predictor(sequence, history_matches)

    effective_active = normalize_active_members(active)
    effective_profile = replace(
        resolved,
        active_members=effective_active,
        model_kind="ensemble" if len(effective_active) > 1 else "catboost",
    )
    if effective_active == ("catboost",):
        return cb, effective_profile

    ensemble = EnsembleModel(
        catboost=cb,
        poisson=poisson,
        mlp=mlp if "mlp" in effective_active else None,
        sequence=sequence if "sequence" in effective_active else None,
    )
    weights_path = ensemble_weights_json_path(league_key, purpose)
    if weights_path.exists():
        try:
            ensemble.load_weights(
                weights_path,
                expected_purpose=purpose,
                expected_active_members=effective_active,
                expected_objective=effective_profile.weight_objective,
                expected_calibration_method=effective_profile.calibration_method,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load %s: %s — using default weights", weights_path, exc)
    return ensemble, effective_profile


__all__ = [
    "ACTIVE_MEMBER_ORDER",
    "ActiveMember",
    "LeagueModelProfile",
    "ModelKind",
    "betting_config_from_profile",
    "build_league_model",
    "ensemble_weights_json_path",
    "infer_model_profile",
    "load_model_profile",
    "make_feature_builder",
    "mlp_config_for_purpose",
    "model_profile_path",
    "normalize_active_members",
    "resolve_model_profile",
    "save_model_profile",
    "sequence_config_for_purpose",
    "stage_sofascore_for_seasons",
    "warm_feature_builder",
    "warm_sequence_predictor",
]
