"""
Tune ensemble weights across all leagues.

For each league with a trained model, grid-searches the optimal
CatBoost/Poisson blend on the validation season's fixtures.

Usage:
    python scripts/tune_ensemble.py
    python scripts/tune_ensemble.py --val-season 2024-25
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from football_betting.config import LEAGUES, MODELS_DIR
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.ensemble import EnsembleModel
from football_betting.predict.poisson import PoissonModel

console = Console()


@click.command()
@click.option("--val-season", default="2024-25", help="Validation season")
def main(val_season: str) -> None:
    rows = []
    for league_key in LEAGUES.keys():
        model_path = MODELS_DIR / f"catboost_{league_key}.cbm"
        if not model_path.exists():
            continue

        try:
            matches = load_league(league_key)
        except FileNotFoundError:
            continue

        train = [m for m in matches if m.season < val_season]
        val = [m for m in matches if m.season == val_season]
        if not val:
            console.log(f"[yellow]Skip {league_key}: no {val_season} data[/yellow]")
            continue

        console.rule(f"[bold cyan]{LEAGUES[league_key].name}[/bold cyan]")
        console.log(f"Train: {len(train)} | Val: {len(val)}")

        fb = FeatureBuilder()
        fb.fit_on_history(train)

        cb = CatBoostPredictor.for_league(league_key, fb)
        poisson = PoissonModel(pi_ratings=fb.pi_ratings)
        ensemble = EnsembleModel(catboost=cb, poisson=poisson)

        fixtures: list[Fixture] = []
        actuals = []
        for m in sorted(val, key=lambda m: m.date):
            fixtures.append(Fixture(
                date=m.date, league=m.league,
                home_team=m.home_team, away_team=m.away_team, odds=m.odds,
            ))
            actuals.append(m.result)

        result = ensemble.tune_weights(fixtures, actuals)
        rows.append({
            "league": league_key,
            "best_w_cb": result["best_w_catboost"],
            "best_w_po": result["best_w_poisson"],
            "best_rps": result.get("best_rps") or result.get("best_log_loss") or result.get("best_brier"),
        })

    console.rule("[bold green]TUNED ENSEMBLE WEIGHTS[/bold green]")
    table = Table()
    table.add_column("League")
    table.add_column("W_CatBoost", justify="right")
    table.add_column("W_Poisson", justify="right")
    table.add_column("Best RPS", justify="right")
    for r in rows:
        table.add_row(
            r["league"],
            f"{r['best_w_cb']:.2f}",
            f"{r['best_w_po']:.2f}",
            f"{r['best_rps']:.4f}" if r["best_rps"] else "n/a",
        )
    console.print(table)


if __name__ == "__main__":
    main()
