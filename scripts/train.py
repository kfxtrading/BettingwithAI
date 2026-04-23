"""
Full training pipeline for v0.2.

Trains CatBoost + calibrator for all 5 top leagues, evaluates RPS/ECE
on held-out validation data, saves models + calibrators to `models/`.

Usage:
    python scripts/train.py
"""
from __future__ import annotations

import numpy as np
from rich.console import Console
from rich.table import Table

from football_betting.config import (
    LEAGUES,
    MODELS_DIR,
    VALUE_MODEL_CFG,
    WEATHER_CFG,
    artifact_suffix,
)
from football_betting.data.loader import load_league
from football_betting.data.models import Outcome
from football_betting.features.builder import FeatureBuilder
from football_betting.features.weather import WeatherTracker
from football_betting.predict.calibration import expected_calibration_error
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.scraping.sofascore import SofascoreClient
from football_betting.tracking.metrics import summary_stats

console = Console()

TRAIN_SEASONS = ("2021-22", "2022-23", "2023-24", "2024-25")
INT_TO_OUTCOME = {0: "H", 1: "D", 2: "A"}


def train_league(league_key: str, purpose: str = "1x2") -> dict[str, float | int | str]:
    console.rule(f"[bold cyan]{LEAGUES[league_key].name} — {purpose}[/bold cyan]")

    matches = load_league(league_key, seasons=list(TRAIN_SEASONS))
    console.log(f"Loaded {len(matches)} training matches")

    # v0.4: opt-in weather features (Familie A — Match-Day Weather)
    weather_tracker = WeatherTracker() if WEATHER_CFG.enabled else None
    if weather_tracker is not None and not weather_tracker.stadiums:
        console.log(
            "[yellow]Weather enabled but no stadiums.json found — "
            "run `fb weather-stadiums` first to populate it.[/yellow]"
        )
    fb_kwargs: dict = {"weather_tracker": weather_tracker}
    if purpose == "value":
        fb_kwargs["feature_blocklist_prefixes"] = VALUE_MODEL_CFG.feature_blocklist_prefixes
        fb_kwargs["feature_blocklist_exact"] = VALUE_MODEL_CFG.feature_blocklist_exact
    fb = FeatureBuilder(**fb_kwargs)

    # Stage Sofascore data so chronological replay consumes it (real xG / squad)
    staged = 0
    for season in TRAIN_SEASONS:
        sf_data = SofascoreClient.load_matches(league_key, season)
        if sf_data:
            staged += fb.stage_sofascore_batch(sf_data)
    if staged:
        console.log(f"[green]Staged Sofascore data: {staged} matches[/green]")

    predictor = CatBoostPredictor(feature_builder=fb, purpose=purpose)  # type: ignore[arg-type]
    result = predictor.fit(matches, warmup_games=100, val_fraction=0.15, calibrate=True)

    # Evaluate RPS on raw + calibrated validation predictions
    val_probs_raw = result["val_predictions"]
    val_labels = result["val_labels"]
    val_pairs: list[tuple[tuple[float, float, float], Outcome]] = []
    for probs, label in zip(val_probs_raw, val_labels, strict=True):
        outcome: Outcome = INT_TO_OUTCOME[int(label)]  # type: ignore[assignment]
        val_pairs.append((tuple(probs), outcome))
    stats_raw = summary_stats(val_pairs)

    # Calibrated version
    if predictor.calibrator and predictor.calibrator.is_fitted:
        val_probs_cal = predictor.calibrator.transform(val_probs_raw)
        val_pairs_cal = []
        for probs, label in zip(val_probs_cal, val_labels, strict=True):
            outcome = INT_TO_OUTCOME[int(label)]  # type: ignore[assignment]
            val_pairs_cal.append((tuple(probs), outcome))
        stats_cal = summary_stats(val_pairs_cal)

        ece_raw = expected_calibration_error(np.array(val_probs_raw), np.array(val_labels))
        ece_cal = expected_calibration_error(np.array(val_probs_cal), np.array(val_labels))
    else:
        stats_cal = stats_raw
        ece_raw = ece_cal = 0.0

    # Save
    suffix = artifact_suffix(purpose)  # type: ignore[arg-type]
    model_path = MODELS_DIR / f"catboost_{league_key}{suffix}.cbm"
    predictor.save(model_path)
    console.log(f"[green]Saved: {model_path.name}[/green]")

    # Show top features
    top_feats = result["feature_importance"][:15]
    table = Table(title="Top 15 features")
    table.add_column("Feature")
    table.add_column("Imp.", justify="right")
    for feat, imp in top_feats:
        table.add_row(feat, f"{imp:.2f}")
    console.print(table)

    console.print(
        f"[bold]RPS raw: {stats_raw['mean_rps']:.4f} → calibrated: {stats_cal['mean_rps']:.4f}[/bold]"
    )
    console.print(f"[bold]ECE raw: {ece_raw:.4f} → calibrated: {ece_cal:.4f}[/bold]")

    return {
        "league": league_key,
        "purpose": purpose,
        "n_train": result["n_train"],
        "n_val": result["n_val"],
        "n_features": result["n_features"],
        "rps_raw": stats_raw["mean_rps"],
        "rps_cal": stats_cal["mean_rps"],
        "ece_raw": ece_raw,
        "ece_cal": ece_cal,
        "hit_rate": stats_cal["hit_rate"],
    }


def main() -> None:
    import sys

    # Allow: python scripts/train.py [1x2|value|both]
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    if mode not in ("1x2", "value", "both"):
        raise SystemExit(f"Unknown mode {mode!r}; expected 1x2, value, or both")
    purposes = (mode,) if mode != "both" else ("1x2", "value")

    all_stats = []
    for purpose in purposes:
        for key in LEAGUES.keys():
            try:
                stats = train_league(key, purpose=purpose)
                all_stats.append(stats)
            except FileNotFoundError as e:
                console.log(f"[red]Skip {key} ({purpose}): {e}[/red]")

    console.rule("[bold green]FINAL SUMMARY[/bold green]")
    table = Table()
    table.add_column("League")
    table.add_column("Purpose")
    table.add_column("#Feat", justify="right")
    table.add_column("RPS (raw)", justify="right")
    table.add_column("RPS (cal)", justify="right")
    table.add_column("ECE (raw)", justify="right")
    table.add_column("ECE (cal)", justify="right")
    table.add_column("Hit", justify="right")
    for s in all_stats:
        table.add_row(
            str(s["league"]),
            str(s.get("purpose", "1x2")),
            str(s["n_features"]),
            f"{s['rps_raw']:.4f}", f"{s['rps_cal']:.4f}",
            f"{s['ece_raw']:.4f}", f"{s['ece_cal']:.4f}",
            f"{s['hit_rate']:.3f}",
        )
    console.print(table)


if __name__ == "__main__":
    main()
