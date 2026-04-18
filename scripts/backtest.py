"""
Walk-forward backtest across all 5 top leagues.

Loads the trained CatBoost models, runs the Backtester on each league's
test season, and prints a comparative summary.

Usage:
    python scripts/backtest.py
    python scripts/backtest.py --league BL
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from football_betting.config import LEAGUES, MODELS_DIR
from football_betting.tracking.backtest import Backtester

console = Console()


@click.command()
@click.option(
    "--league",
    "-l",
    type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False),
    default="all",
)
@click.option("--bankroll", default=1000.0)
@click.option("--no-ensemble", is_flag=True, help="CatBoost-only (no Poisson blend)")
def main(league: str, bankroll: float, no_ensemble: bool) -> None:
    keys = list(LEAGUES.keys()) if league.lower() == "all" else [league.upper()]
    bt = Backtester(initial_bankroll=bankroll, use_ensemble=not no_ensemble)

    results = []
    for key in keys:
        model_path = MODELS_DIR / f"catboost_{key}.cbm"
        if not model_path.exists():
            console.log(f"[yellow]Skip {key} — no trained model at {model_path}[/yellow]")
            continue
        try:
            result = bt.run(key)
            result.save()
            results.append(result)
        except (FileNotFoundError, ValueError) as e:
            console.log(f"[red]Failed {key}: {e}[/red]")

    # Comparative summary
    if results:
        console.rule("[bold green]COMPARATIVE BACKTEST SUMMARY[/bold green]")
        table = Table()
        table.add_column("League")
        table.add_column("#Pred", justify="right")
        table.add_column("#Bets", justify="right")
        table.add_column("RPS", justify="right")
        table.add_column("Hit rate", justify="right")
        table.add_column("Final BR", justify="right")
        table.add_column("ROI", justify="right")
        table.add_column("Max DD", justify="right")

        for r in results:
            roi_val = r.bet_metrics.get("roi", 0.0) if r.n_bets > 0 else 0.0
            table.add_row(
                r.league,
                str(r.n_predictions),
                str(r.n_bets),
                f"{r.metrics.get('mean_rps', 0):.4f}",
                f"{r.metrics.get('hit_rate', 0):.3f}",
                f"{r.bankroll_final:.0f}",
                f"{roi_val * 100:+.1f}%",
                f"{r.max_drawdown['max_drawdown_pct'] * 100:.1f}%",
            )
        console.print(table)


if __name__ == "__main__":
    main()
