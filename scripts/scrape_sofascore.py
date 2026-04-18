"""
Sofascore scraping batch script.

Convenience wrapper around `fb scrape` that runs for all leagues × seasons.

Usage:
    export SCRAPING_ENABLED=1
    python scripts/scrape_sofascore.py --leagues BL --seasons 2024-25 2025-26
"""
from __future__ import annotations

import click
from rich.console import Console

from football_betting.config import LEAGUES
from football_betting.scraping.sofascore import SofascoreClient

console = Console()


@click.command()
@click.option("--leagues", "-l", multiple=True, default=("all",))
@click.option("--seasons", "-s", multiple=True, default=("2024-25", "2025-26"))
@click.option("--with-stats/--no-stats", default=True)
@click.option("--max-matches", default=None, type=int)
def main(
    leagues: tuple[str, ...],
    seasons: tuple[str, ...],
    with_stats: bool,
    max_matches: int | None,
) -> None:
    client = SofascoreClient()
    if not client.cfg.enabled:
        console.print("[red]Set SCRAPING_ENABLED=1 env var to enable.[/red]")
        raise SystemExit(1)

    keys = list(LEAGUES.keys()) if "all" in leagues else list(leagues)

    for league_key in keys:
        for season in seasons:
            console.rule(f"[bold cyan]{LEAGUES[league_key].name} — {season}[/bold cyan]")
            events = client.get_season_events(league_key, season)
            console.log(f"Events: {len(events)}")

            if max_matches:
                events = events[:max_matches]

            matches = []
            for idx, event in enumerate(events):
                match = client.parse_match(event)
                if match is None:
                    continue
                if with_stats and match.status == "finished":
                    match = client.enrich_match_with_stats(match)
                matches.append(match)
                if (idx + 1) % 20 == 0:
                    console.log(f"  {idx + 1}/{len(events)} done")

            path = client.save_matches(matches, league_key, season)
            console.log(f"[green]Saved: {path}[/green]")


if __name__ == "__main__":
    main()
