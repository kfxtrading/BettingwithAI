"""
Backfill missing 2021-22 xG into Sofascore JSON files using the Understat
shot-level dump from the (archived) JaseZiv/worldfootballR_data GitHub mirror.

Sofascore's `/event/{id}/statistics` endpoint does NOT expose Expected Goals
for the 2021-22 season — it was added in 2022-23. To unblock training pipelines
that need xG features for 2021-22, this script:

1. Downloads `bundesliga|epl|la_liga|serie_a_shot_data.rds` (≈1-2 MB each)
2. Filters to season 2021 (= 2021-22)
3. Aggregates shot-level xG to match-level (sum per team per match)
4. Maps Understat team names → Sofascore team names
5. Joins on (home, away, date ±1 day) and writes home_xg / away_xg back into
   data/sofascore/{BL,PL,LL,SA}_2021-22.json

EFL Championship (CH) is intentionally NOT covered: neither Understat nor FBref
provides xG for Championship 2021-22.

Usage:
    python scripts/backfill_xg_understat.py
    python scripts/backfill_xg_understat.py --leagues BL PL
    python scripts/backfill_xg_understat.py --dry-run
"""
from __future__ import annotations

import json
import urllib.request
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path

import click
import pandas as pd
from rich.console import Console

warnings.filterwarnings("ignore")
import rdata  # noqa: E402

console = Console()

REPO_BASE = (
    "https://raw.githubusercontent.com/JaseZiv/worldfootballR_data/"
    "master/data/understat_shots/"
)

RDS_FILES: dict[str, str] = {
    "BL": "bundesliga_shot_data.rds",
    "PL": "epl_shot_data.rds",
    "LL": "la_liga_shot_data.rds",
    "SA": "serie_a_shot_data.rds",
}

# Understat name → Sofascore name (per league)
TEAM_MAP: dict[str, dict[str, str]] = {
    "BL": {
        "Arminia Bielefeld": "Arminia Bielefeld",
        "Augsburg": "FC Augsburg",
        "Bayer Leverkusen": "Bayer 04 Leverkusen",
        "Bayern Munich": "FC Bayern München",
        "Bochum": "VfL Bochum 1848",
        "Borussia Dortmund": "Borussia Dortmund",
        "Borussia M.Gladbach": "Borussia M'gladbach",
        "Eintracht Frankfurt": "Eintracht Frankfurt",
        "FC Cologne": "1. FC Köln",
        "Freiburg": "SC Freiburg",
        "Greuther Fuerth": "SpVgg Greuther Fürth",
        "Hertha Berlin": "Hertha BSC",
        "Hoffenheim": "TSG Hoffenheim",
        "Mainz 05": "1. FSV Mainz 05",
        "RasenBallsport Leipzig": "RB Leipzig",
        "Union Berlin": "1. FC Union Berlin",
        "VfB Stuttgart": "VfB Stuttgart",
        "Wolfsburg": "VfL Wolfsburg",
    },
    "PL": {
        "Arsenal": "Arsenal",
        "Aston Villa": "Aston Villa",
        "Brentford": "Brentford",
        "Brighton": "Brighton & Hove Albion",
        "Burnley": "Burnley",
        "Chelsea": "Chelsea",
        "Crystal Palace": "Crystal Palace",
        "Everton": "Everton",
        "Leeds": "Leeds United",
        "Leicester": "Leicester City",
        "Liverpool": "Liverpool",
        "Manchester City": "Manchester City",
        "Manchester United": "Manchester United",
        "Newcastle United": "Newcastle United",
        "Norwich": "Norwich City",
        "Southampton": "Southampton",
        "Tottenham": "Tottenham Hotspur",
        "Watford": "Watford",
        "West Ham": "West Ham United",
        "Wolverhampton Wanderers": "Wolverhampton",
    },
    "LL": {
        "Alaves": "Deportivo Alavés",
        "Athletic Club": "Athletic Club",
        "Atletico Madrid": "Atlético Madrid",
        "Barcelona": "FC Barcelona",
        "Cadiz": "Cádiz",
        "Celta Vigo": "Celta Vigo",
        "Elche": "Elche",
        "Espanyol": "Espanyol",
        "Getafe": "Getafe",
        "Granada": "Granada",
        "Levante": "Levante UD",
        "Mallorca": "Mallorca",
        "Osasuna": "Osasuna",
        "Rayo Vallecano": "Rayo Vallecano",
        "Real Betis": "Real Betis",
        "Real Madrid": "Real Madrid",
        "Real Sociedad": "Real Sociedad",
        "Sevilla": "Sevilla",
        "Valencia": "Valencia",
        "Villarreal": "Villarreal",
    },
    "SA": {
        "AC Milan": "Milan",
        "Atalanta": "Atalanta",
        "Bologna": "Bologna",
        "Cagliari": "Cagliari",
        "Empoli": "Empoli",
        "Fiorentina": "Fiorentina",
        "Genoa": "Genoa",
        "Inter": "Inter",
        "Juventus": "Juventus",
        "Lazio": "Lazio",
        "Napoli": "Napoli",
        "Roma": "Roma",
        "Salernitana": "Salernitana",
        "Sampdoria": "Sampdoria",
        "Sassuolo": "Sassuolo",
        "Spezia": "Spezia",
        "Torino": "Torino",
        "Udinese": "Udinese",
        "Venezia": "Venezia",
        "Verona": "Hellas Verona",
    },
}

CACHE_DIR = Path("data/sofascore/_understat_cache")
SOFASCORE_DIR = Path("data/sofascore")
SEASON = "2021-22"
UNDERSTAT_SEASON_KEY = 2021.0  # Understat encodes "season" as start year


def _download(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / name
    if not p.exists():
        url = REPO_BASE + name
        console.log(f"[cyan]downloading {name} ...[/cyan]")
        urllib.request.urlretrieve(url, p)
    return p


def _load_match_xg(rds_path: Path) -> pd.DataFrame:
    df = rdata.read_rds(str(rds_path), default_encoding="utf-8")
    s = df[df["season"] == UNDERSTAT_SEASON_KEY].copy()
    if s.empty:
        return s
    agg = (
        s.groupby(["match_id", "h_a"])["xG"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    agg.columns.name = None
    agg = agg.rename(columns={"h": "home_xg", "a": "away_xg"})
    meta = s.drop_duplicates("match_id")[
        ["match_id", "date", "home_team", "away_team"]
    ]
    agg = agg.merge(meta, on="match_id", how="left")
    agg["date"] = pd.to_datetime(agg["date"]).dt.date
    return agg


def _build_index(
    xg_df: pd.DataFrame, mapping: dict[str, str]
) -> dict[tuple[str, str], list[tuple[date, float, float]]]:
    """(home_sofa, away_sofa) → [(date, home_xg, away_xg), …]"""
    idx: dict[tuple[str, str], list[tuple[date, float, float]]] = {}
    missing: set[str] = set()
    for r in xg_df.itertuples(index=False):
        ht_sofa = mapping.get(r.home_team)
        at_sofa = mapping.get(r.away_team)
        if ht_sofa is None:
            missing.add(r.home_team)
        if at_sofa is None:
            missing.add(r.away_team)
        if ht_sofa is None or at_sofa is None:
            continue
        idx.setdefault((ht_sofa, at_sofa), []).append(
            (r.date, float(r.home_xg), float(r.away_xg))
        )
    if missing:
        console.log(
            f"[yellow]Unmapped Understat teams skipped: {sorted(missing)}[/yellow]"
        )
    return idx


def _find_match(
    idx: dict[tuple[str, str], list[tuple[date, float, float]]],
    home: str,
    away: str,
    target_date: date,
) -> tuple[float, float] | None:
    candidates = idx.get((home, away))
    if not candidates:
        return None
    # Pick closest date within ±2 days; in practice always the same day.
    best: tuple[int, tuple[float, float]] | None = None
    for d, hxg, axg in candidates:
        delta = abs((d - target_date).days)
        if delta > 2:
            continue
        if best is None or delta < best[0]:
            best = (delta, (hxg, axg))
    return best[1] if best else None


def backfill_league(league_key: str, dry_run: bool) -> dict[str, int]:
    name = RDS_FILES[league_key]
    rds_path = _download(name)
    console.log(f"[cyan]parsing {league_key} ...[/cyan]")
    xg_df = _load_match_xg(rds_path)
    console.log(
        f"  Understat matches in {SEASON}: {len(xg_df)} "
        f"(shots aggregated by match_id × side)"
    )

    sofa_path = SOFASCORE_DIR / f"{league_key}_{SEASON}.json"
    matches = json.loads(sofa_path.read_text(encoding="utf-8"))

    mapping = TEAM_MAP[league_key]
    idx = _build_index(xg_df, mapping)

    stats = {"updated": 0, "already_set": 0, "no_match": 0, "skipped_status": 0}
    unmatched: list[str] = []

    for m in matches:
        if m.get("status") != "finished":
            stats["skipped_status"] += 1
            continue
        if m.get("home_xg") is not None and m.get("away_xg") is not None:
            stats["already_set"] += 1
            continue
        try:
            target = datetime.strptime(m["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            stats["no_match"] += 1
            continue
        result = _find_match(idx, m["home_team"], m["away_team"], target)
        if result is None:
            stats["no_match"] += 1
            unmatched.append(
                f"{m['date']}  {m['home_team']} vs {m['away_team']}"
            )
            continue
        m["home_xg"] = round(result[0], 4)
        m["away_xg"] = round(result[1], 4)
        stats["updated"] += 1

    if unmatched:
        console.log(f"[yellow]{league_key}: {len(unmatched)} unmatched fixtures[/yellow]")
        for line in unmatched[:10]:
            console.log(f"  • {line}")

    if not dry_run and stats["updated"] > 0:
        sofa_path.write_text(
            json.dumps(matches, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        console.log(f"[green]wrote {sofa_path}[/green]")
    elif dry_run:
        console.log("[yellow]dry-run: no file written[/yellow]")

    return stats


@click.command()
@click.option(
    "--leagues",
    "-l",
    multiple=True,
    default=("BL", "PL", "LL", "SA"),
    help="Subset of leagues to backfill.",
)
@click.option("--dry-run", is_flag=True, help="Probe + match, but do not write.")
def main(leagues: tuple[str, ...], dry_run: bool) -> None:
    summary: dict[str, dict[str, int]] = {}
    for lg in leagues:
        if lg not in RDS_FILES:
            console.log(f"[red]Unsupported league {lg} (BL/PL/LL/SA only)[/red]")
            continue
        console.rule(f"[bold cyan]{lg} {SEASON}[/bold cyan]")
        summary[lg] = backfill_league(lg, dry_run=dry_run)

    console.rule("[bold]Summary[/bold]")
    for lg, st in summary.items():
        console.log(
            f"{lg}: updated={st['updated']}  already_set={st['already_set']}  "
            f"no_match={st['no_match']}  skipped_status={st['skipped_status']}"
        )


if __name__ == "__main__":
    main()
