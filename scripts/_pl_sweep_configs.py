"""PL config sweep registry — one entry per training variant we want to
evaluate against the 2026-03-02 → 2026-04-22 PL test window.

A "config" is a partial override of three things:
  * ``feature_overrides``: kwargs passed to ``replace(FEATURE_CFG, ...)``
    to toggle feature families on/off.
  * ``catboost_overrides``: kwargs passed to ``replace(CATBOOST_CFG, ...)``
    to tune hyperparameters.
  * ``calibrate``: bool — whether to fit a calibrator on the val slice.
  * ``calibration_method``: 'auto' | 'sigmoid' | 'isotonic' (only used when
    ``calibrate`` is True).

The retrain driver imports ``CONFIGS`` and ``apply()`` which returns a
``(FeatureConfig, CatBoostConfig, calibrate, calibration_cfg)`` tuple.

Phase A (PL date-cutoff feature impact) findings drove the choice of
``pl_drop_lowimpact``: squad_quality, xg_proxy, rest_days, h2h all
contributed 0–1 high-impact features in PL on the cutoff window.
``use_weather`` is intentionally left ON because ``weather_wind_kmh``
ranked top-10 across all three supervised estimators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SweepConfig:
    name: str
    description: str
    feature_overrides: dict[str, Any] = field(default_factory=dict)
    catboost_overrides: dict[str, Any] = field(default_factory=dict)
    calibrate: bool = False
    calibration_method: str | None = None  # used only when calibrate=True


CONFIGS: dict[str, SweepConfig] = {
    "pl_baseline": SweepConfig(
        name="pl_baseline",
        description="Production defaults — current state, calibrate=False. "
                    "Reproduces the −48.8 % top-pick ROI starting point.",
    ),
    "pl_drop_lowimpact": SweepConfig(
        name="pl_drop_lowimpact",
        description="Drop families that contributed 0–1 high-impact features "
                    "in Phase A: squad_quality, xg_proxy, rest_days, h2h. "
                    "Keep weather (weather_wind_kmh ranked top-10).",
        feature_overrides={
            "use_squad_quality": False,
            "use_xg_proxy": False,
            "use_rest_days": False,
            "use_h2h": False,
        },
    ),
    "pl_sigmoid_cal": SweepConfig(
        name="pl_sigmoid_cal",
        description="Baseline features + Platt-scaling calibration "
                    "(4 params/class, much harder to overfit than isotonic/auto).",
        calibrate=True,
        calibration_method="sigmoid",
    ),
    "pl_higher_decay": SweepConfig(
        name="pl_higher_decay",
        description="time_decay=0.92 (less aggressive — 2021-22 weight ≈ 0.72 "
                    "vs current 0.52). Tests whether older PL data carries "
                    "more transferable signal.",
        catboost_overrides={"time_decay": 0.92},
    ),
    "pl_smaller_depth": SweepConfig(
        name="pl_smaller_depth",
        description="Tighter CatBoost: depth=4, l2_leaf_reg=5.0. "
                    "More regularisation for the most efficient market.",
        catboost_overrides={"depth": 4, "l2_leaf_reg": 5.0},
    ),
    "pl_lower_lr": SweepConfig(
        name="pl_lower_lr",
        description="Smoother fit: learning_rate=0.01, iterations=3000, "
                    "early_stopping_rounds=200. Reduces iteration noise.",
        catboost_overrides={
            "learning_rate": 0.01,
            "iterations": 3000,
            "early_stopping_rounds": 200,
        },
    ),
}


def list_config_names() -> list[str]:
    return list(CONFIGS.keys())


def get_config(name: str) -> SweepConfig:
    if name not in CONFIGS:
        raise KeyError(
            f"Unknown PL sweep config '{name}'. "
            f"Available: {', '.join(CONFIGS.keys())}"
        )
    return CONFIGS[name]
