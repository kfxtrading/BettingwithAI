"""
Update the public + private performance-index artefacts.

Reads the ResultsTracker log and writes:

    data/predictions/performance.json        (anonymised)
    data/predictions/performance_full.json   (full detail)

Run daily (e.g. 02:00 UTC) via cron / systemd timer / GitHub Actions.

Usage:
    python scripts/update_performance_index.py
    python scripts/update_performance_index.py --tracking-start 2026-01-01
"""
from __future__ import annotations

import click
from rich.console import Console

from football_betting.tracking.performance_index import (
    TRACKING_START_DEFAULT,
    write_performance_files,
)

console = Console()


@click.command()
@click.option(
    "--tracking-start",
    default=TRACKING_START_DEFAULT,
    help="ISO date when tracking began (YYYY-MM-DD).",
)
def main(tracking_start: str) -> None:
    public_path, private_path = write_performance_files(
        tracking_start=tracking_start
    )
    console.log(f"[green]Wrote {public_path}[/green]")
    console.log(f"[green]Wrote {private_path}[/green]")


if __name__ == "__main__":
    main()
