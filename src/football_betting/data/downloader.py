"""Download historical match data from football-data.co.uk."""
from __future__ import annotations

from pathlib import Path

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from football_betting.config import LEAGUES, RAW_DIR, LeagueConfig

console = Console()


def season_code(season: str) -> str:
    """Convert '2025-26' → '2526' format used by football-data.co.uk."""
    parts = season.split("-")
    if len(parts) != 2:
        raise ValueError(f"Expected 'YYYY-YY' format, got: {season}")
    start_short = parts[0][-2:]
    end_short = parts[1][-2:] if len(parts[1]) >= 2 else parts[1]
    return f"{start_short}{end_short}"


def download_season(league: LeagueConfig, season: str, force: bool = False) -> Path:
    """Download one season CSV for one league. Returns cached path if present."""
    code = season_code(season)
    out_path = RAW_DIR / f"{league.code}_{code}.csv"

    if out_path.exists() and not force:
        console.log(f"  cached: {out_path.name}")
        return out_path

    url = league.url(code)
    console.log(f"  downloading {league.name} {season} from {url}")

    response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    out_path.write_bytes(response.content)
    console.log(f"  saved: {out_path.name} ({len(response.content)} bytes)")
    return out_path


def download_all(
    league_keys: list[str] | None = None,
    seasons: list[str] | None = None,
    force: bool = False,
) -> list[Path]:
    """Download multiple leagues × seasons."""
    league_keys = league_keys or list(LEAGUES.keys())
    seasons = seasons or ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]

    paths: list[Path] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Downloading…", total=len(league_keys) * len(seasons)
        )
        for key in league_keys:
            league = LEAGUES[key]
            for season in seasons:
                try:
                    paths.append(download_season(league, season, force=force))
                except requests.HTTPError as e:
                    console.log(f"  failed {league.name} {season}: {e}")
                progress.advance(task)

    console.log(f"[green]Done.[/green] {len(paths)} files.")
    return paths
