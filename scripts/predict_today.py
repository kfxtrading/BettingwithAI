"""
Predict today's fixtures.

Expects a JSON file at `data/fixtures_YYYY-MM-DD.json` with the format
documented in `cli.py predict`. Runs the ensemble model and saves
predictions + value bets to the predictions log.

Usage:
    python scripts/predict_today.py --date 2026-04-17 --bankroll 1000
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import click
from rich.console import Console

from football_betting.config import DATA_DIR
from football_betting.cli import main as cli_main

console = Console()


@click.command()
@click.option("--date", "match_date", default=None, help="YYYY-MM-DD (default: today)")
@click.option("--bankroll", default=1000.0)
def main(match_date: str | None, bankroll: float) -> None:
    if match_date is None:
        match_date = date.today().isoformat()

    fixtures_path = DATA_DIR / f"fixtures_{match_date}.json"
    if not fixtures_path.exists():
        console.print(f"[red]File not found: {fixtures_path}[/red]")
        console.print(
            f"[yellow]Create it with today's fixtures in this format:[/yellow]\n"
            f"""[
  {{
    "date": "{match_date}",
    "league": "BL",
    "home_team": "St. Pauli",
    "away_team": "Köln",
    "odds": {{"home": 2.90, "draw": 3.15, "away": 2.45}}
  }}
]"""
        )
        raise SystemExit(1)

    # Delegate to CLI command
    import subprocess
    import sys

    cmd = [
        sys.executable, "-m", "football_betting.cli", "predict",
        "--fixtures", str(fixtures_path),
        "--bankroll", str(bankroll),
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
