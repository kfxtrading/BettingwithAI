"""LL config sweep registry — mirrors ``_pl_sweep_configs.py`` but the
``ll_drop_lowimpact`` config reflects LL-specific Phase A findings:

LL Phase 0 (date cutoff 2026-03-01, val 2026-03-02 → 2026-04-25, 1678 train,
62 val) high-impact-feature counts per family:

    form          2/14    h2h           2/8    weather    2/9
    market_odds   1/5     pi_ratings    1/9    real_xg    1/14    xg_proxy 1/9
    squad_quality 0/8     rest_days     0/5    home_adv   0/3   (always low)

Differences vs PL: h2h actually matters for LL (h2h_avg_goals + h2h_draws
are top-3 across the supervised estimators) and xg_proxy contributes
(xg_matchup_diff). For PL we dropped both — must NOT drop them here.

The five non-drop configs (baseline, sigmoid_cal, higher_decay, smaller_depth,
lower_lr) are league-agnostic and identical to PL's, just renamed.
"""

from __future__ import annotations

import sys
from pathlib import Path

# When this module is imported by scripts/retrain_date_cutoff.py that
# already adds scripts/ to sys.path, this is a no-op; when loaded
# stand-alone (e.g. for testing), make sure the sibling module is
# discoverable.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from _pl_sweep_configs import SweepConfig  # noqa: E402

CONFIGS: dict[str, SweepConfig] = {
    "ll_baseline": SweepConfig(
        name="ll_baseline",
        description="Production defaults — current state, calibrate=False. "
                    "Reproduces the date-cutoff retrain starting point.",
    ),
    "ll_drop_lowimpact": SweepConfig(
        name="ll_drop_lowimpact",
        description="Drop families that contributed 0 high-impact features "
                    "in LL Phase A: squad_quality, rest_days. "
                    "Keep h2h (2/8 high-impact) and xg_proxy (1/9, "
                    "xg_matchup_diff top-1 by catboost-loss-change) — both "
                    "matter for LL even though they were dropped for PL.",
        feature_overrides={
            "use_squad_quality": False,
            "use_rest_days": False,
        },
    ),
    "ll_sigmoid_cal": SweepConfig(
        name="ll_sigmoid_cal",
        description="Baseline features + Platt-scaling calibration "
                    "(4 params/class, much harder to overfit than isotonic/auto).",
        calibrate=True,
        calibration_method="sigmoid",
    ),
    "ll_higher_decay": SweepConfig(
        name="ll_higher_decay",
        description="time_decay=0.92 (less aggressive — 2021-22 weight ≈ 0.72 "
                    "vs current 0.52). Tests whether older LL data carries "
                    "more transferable signal.",
        catboost_overrides={"time_decay": 0.92},
    ),
    "ll_smaller_depth": SweepConfig(
        name="ll_smaller_depth",
        description="Tighter CatBoost: depth=4, l2_leaf_reg=5.0. "
                    "More regularisation against PL-style over-fit risk.",
        catboost_overrides={"depth": 4, "l2_leaf_reg": 5.0},
    ),
    "ll_lower_lr": SweepConfig(
        name="ll_lower_lr",
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
            f"Unknown LL sweep config '{name}'. "
            f"Available: {', '.join(CONFIGS.keys())}"
        )
    return CONFIGS[name]
