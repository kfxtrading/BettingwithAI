"""
Zulubet daily-tips backfill.

Iterates ``[--start, --end]`` (default: 2024-01-01 → today), fetches each
day's tips page, extracts the (date, home, away, tip) rows and writes them
to ``data/zulubet/zulubet_tips.parquet``. Pages are cached in SQLite under
``data/zulubet/cache.sqlite`` so re-runs are essentially free.

Usage:
    export SCRAPING_ENABLED=1
    python scripts/scrape_zulubet.py                       # full backfill
    python scripts/scrape_zulubet.py --start 2025-01-01    # partial range
    python scripts/scrape_zulubet.py --force               # bypass enable gate
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from football_betting.scraping.zulubet import (
    DEFAULT_PARQUET_PATH,
    ZulubetClient,
    ZulubetTip,
)

console = Console()


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@click.command()
@click.option(
    "--start",
    type=str,
    default=None,
    help="Inclusive start date YYYY-MM-DD. Defaults to ZulubetConfig.earliest_date (2024-01-01).",
)
@click.option(
    "--end",
    type=str,
    default=None,
    help="Inclusive end date YYYY-MM-DD. Defaults to today.",
)
@click.option(
    "--out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_PARQUET_PATH,
    show_default=True,
    help="Output parquet path.",
)
@click.option(
    "--force/--no-force",
    default=False,
    help="Bypass the SCRAPING_ENABLED env gate.",
)
@click.option(
    "--no-merge",
    "no_merge",
    is_flag=True,
    default=False,
    help="Overwrite the parquet instead of merging with existing rows.",
)
def main(
    start: str | None,
    end: str | None,
    out: Path,
    force: bool,
    no_merge: bool,
) -> None:
    client = ZulubetClient()
    if not client.cfg.enabled and not force:
        console.print("[red]Set SCRAPING_ENABLED=1 (or pass --force) to enable.[/red]")
        raise SystemExit(1)

    start_d = _parse_date(start) or client.cfg.earliest_date
    end_d = _parse_date(end) or date.today()
    if end_d < start_d:
        console.print(f"[red]end ({end_d}) must be >= start ({start_d})[/red]")
        raise SystemExit(2)

    days = list(client.iter_dates(start_d, end_d))
    console.print(
        f"[cyan]Backfilling Zulubet tips:[/cyan] "
        f"{start_d} -> {end_d} ({len(days)} days), out={out}"
    )

    tips: list[ZulubetTip] = []
    misses = 0
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("· tips={task.fields[tips]}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("scraping", total=len(days), tips=0)
        for day in days:
            day_tips = client.fetch_day(day, force=force)
            if not day_tips:
                misses += 1
            tips.extend(day_tips)
            progress.update(task, advance=1, tips=len(tips))

    if not tips:
        console.print("[yellow]No tip rows parsed — nothing written.[/yellow]")
        raise SystemExit(0 if misses == len(days) else 3)

    path = client.save_parquet(tips, path=out, merge_existing=not no_merge)
    df = client.load_parquet(path)
    console.print(
        f"[green]Wrote {path}[/green] · "
        f"new_rows={len(tips)} · total_rows={len(df)} · "
        f"days_with_no_data={misses}"
    )


if __name__ == "__main__":
    main()
