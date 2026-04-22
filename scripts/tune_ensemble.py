"""
Tune ensemble weights across all leagues.

For each league with a trained model, Dirichlet-samples the optimal
CatBoost/Poisson/MLP blend on the validation season's fixtures.

Phase 6 additions:
    --objective clv|blended enables CLV-aware tuning when opening-line
    snapshots have been captured via ``fb snapshot-odds``.

Usage:
    python scripts/tune_ensemble.py
    python scripts/tune_ensemble.py --val-season 2024-25 --objective blended
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from football_betting.config import LEAGUES, MODELS_DIR
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture
from football_betting.data.snapshot_service import merge_snapshots_into_matches
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.ensemble import EnsembleModel
from football_betting.predict.poisson import PoissonModel

console = Console()


@click.command()
@click.option("--val-season", default="2024-25", help="Validation season")
@click.option(
    "--objective",
    type=click.Choice(["rps", "log_loss", "brier", "clv", "blended"], case_sensitive=False),
    default="rps",
    help="Tuning objective (Phase 6).",
)
@click.option("--blend", default=0.5, show_default=True)
def main(val_season: str, objective: str, blend: float) -> None:
    rows = []
    for league_key in LEAGUES:
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

        val = merge_snapshots_into_matches(val, league_key)

        console.rule(f"[bold cyan]{LEAGUES[league_key].name}[/bold cyan]")
        console.log(f"Train: {len(train)} | Val: {len(val)} | objective: {objective}")

        fb = FeatureBuilder()
        fb.fit_on_history(train)

        cb = CatBoostPredictor.for_league(league_key, fb)
        poisson = PoissonModel(pi_ratings=fb.pi_ratings)
        ensemble = EnsembleModel(catboost=cb, poisson=poisson)

        fixtures: list[Fixture] = []
        actuals = []
        bet_odds: list[tuple[float, float, float] | None] = []
        close_odds: list[tuple[float, float, float] | None] = []
        for m in sorted(val, key=lambda m: m.date):
            fixtures.append(Fixture(
                date=m.date, league=m.league,
                home_team=m.home_team, away_team=m.away_team, odds=m.odds,
            ))
            actuals.append(m.result)
            closing = m.odds
            opening = getattr(m, "opening_odds", None) or closing
            bet_odds.append((opening.home, opening.draw, opening.away) if opening else None)
            close_odds.append((closing.home, closing.draw, closing.away) if closing else None)

        obj = objective.lower()
        if obj in ("clv", "blended"):
            result = ensemble.tune_dirichlet(
                fixtures, actuals,
                bet_odds=bet_odds, closing_odds=close_odds,
                objective=obj,  # type: ignore[arg-type]
                blend=blend,
            )
        elif obj in ("log_loss", "brier"):
            result = ensemble.tune_dirichlet(
                fixtures, actuals, objective=obj,  # type: ignore[arg-type]
            )
        else:
            result = ensemble.tune_weights(fixtures, actuals)

        best_metric = (
            result.get(f"best_{obj}")
            or result.get("best_blended")
            or result.get("best_clv_mean")
            or result.get("best_rps")
            or result.get("best_log_loss")
            or result.get("best_brier")
        )
        rows.append({
            "league": league_key,
            "best_w_cb": result["best_w_catboost"],
            "best_w_po": result["best_w_poisson"],
            "best_rps": best_metric,
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
