"""Load & parse football-data.co.uk CSVs into typed Match objects."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console

from football_betting.config import LEAGUES, RAW_DIR
from football_betting.data.models import Match, MatchOdds

console = Console()


# football-data.co.uk column mapping
COL_DATE = "Date"
COL_TIME = "Time"  # HH:MM, local kickoff (v0.4 weather features)
COL_HOME = "HomeTeam"
COL_AWAY = "AwayTeam"
COL_HG = "FTHG"  # full-time home goals
COL_AG = "FTAG"  # full-time away goals
COL_HS = "HS"  # home shots
COL_AS = "AS"  # away shots
COL_HST = "HST"  # home shots on target
COL_AST = "AST"  # away shots on target

# Preferred odds columns (Pinnacle > Bet365 > Average)
ODDS_PRIORITY = [
    ("PSH", "PSD", "PSA", "Pinnacle"),
    ("B365H", "B365D", "B365A", "Bet365"),
    ("AvgH", "AvgD", "AvgA", "avg"),
    ("BbAvH", "BbAvD", "BbAvA", "avg_legacy"),
]


def _extract_kickoff(row: pd.Series) -> datetime | None:
    """Combine Date + Time → naive datetime (local kickoff)."""
    if COL_TIME not in row or pd.isna(row[COL_TIME]):
        return None
    raw_date = row[COL_DATE]
    raw_time = str(row[COL_TIME]).strip()
    parsed_date = None
    if isinstance(raw_date, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
            try:
                parsed_date = datetime.strptime(raw_date, fmt).date()
                break
            except ValueError:
                continue
    elif hasattr(raw_date, "date"):
        parsed_date = raw_date.date() if isinstance(raw_date, datetime) else raw_date
    if parsed_date is None:
        return None
    try:
        hh, mm = raw_time.split(":")[:2]
        return datetime(parsed_date.year, parsed_date.month, parsed_date.day, int(hh), int(mm))
    except (ValueError, IndexError):
        return None


def _extract_odds(row: pd.Series) -> MatchOdds | None:
    """Try odds columns in priority order."""
    for h_col, d_col, a_col, bookmaker in ODDS_PRIORITY:
        if h_col in row and pd.notna(row[h_col]) and row[h_col] > 1.0:
            try:
                return MatchOdds(
                    home=float(row[h_col]),
                    draw=float(row[d_col]),
                    away=float(row[a_col]),
                    bookmaker=bookmaker,
                )
            except (ValueError, KeyError):
                continue
    return None


def _infer_season(filename: str) -> str:
    """Extract '2025-26' from 'E0_2526.csv'."""
    stem = Path(filename).stem
    code = stem.split("_")[-1] if "_" in stem else stem[-4:]
    if len(code) != 4:
        return "unknown"
    return f"20{code[:2]}-{code[2:]}"


def load_csv(path: Path, league_key: str) -> list[Match]:
    """Load and parse one CSV file into Match objects."""
    df = pd.read_csv(path, encoding_errors="replace")

    # Clean: drop rows without result
    df = df.dropna(subset=[COL_HG, COL_AG, COL_HOME, COL_AWAY])

    season = _infer_season(path.name)
    matches: list[Match] = []

    for _, row in df.iterrows():
        try:
            match = Match(
                date=row[COL_DATE],
                league=league_key,
                season=season,
                home_team=str(row[COL_HOME]).strip(),
                away_team=str(row[COL_AWAY]).strip(),
                home_goals=int(row[COL_HG]),
                away_goals=int(row[COL_AG]),
                home_shots=int(row[COL_HS]) if COL_HS in row and pd.notna(row[COL_HS]) else None,
                away_shots=int(row[COL_AS]) if COL_AS in row and pd.notna(row[COL_AS]) else None,
                home_shots_on_target=(
                    int(row[COL_HST]) if COL_HST in row and pd.notna(row[COL_HST]) else None
                ),
                away_shots_on_target=(
                    int(row[COL_AST]) if COL_AST in row and pd.notna(row[COL_AST]) else None
                ),
                odds=_extract_odds(row),
                kickoff_datetime_utc=_extract_kickoff(row),
            )
            matches.append(match)
        except Exception as e:
            console.log(f"  skip row in {path.name}: {e}")

    return matches


def load_league(league_key: str, seasons: list[str] | None = None) -> list[Match]:
    """Load all available seasons for one league."""
    league = LEAGUES[league_key]
    csv_files = sorted(RAW_DIR.glob(f"{league.code}_*.csv"))

    if seasons is not None:
        from football_betting.data.downloader import season_code

        wanted = {season_code(s) for s in seasons}
        csv_files = [p for p in csv_files if p.stem.split("_")[-1] in wanted]

    if not csv_files:
        raise FileNotFoundError(
            f"No CSVs for {league.name} in {RAW_DIR}. Run `fb download` first."
        )

    matches: list[Match] = []
    for path in csv_files:
        matches.extend(load_csv(path, league_key))

    # Sort by date
    matches.sort(key=lambda m: m.date)
    console.log(f"[green]Loaded {len(matches)} {league.name} matches[/green]")
    return matches


def matches_to_dataframe(matches: list[Match]) -> pd.DataFrame:
    """Convert list of Matches to DataFrame for ML pipelines."""
    rows = []
    for m in matches:
        row = {
            "date": m.date,
            "league": m.league,
            "season": m.season,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "home_goals": m.home_goals,
            "away_goals": m.away_goals,
            "result": m.result,
            "home_shots": m.home_shots,
            "away_shots": m.away_shots,
            "home_shots_on_target": m.home_shots_on_target,
            "away_shots_on_target": m.away_shots_on_target,
        }
        if m.odds:
            row["odds_home"] = m.odds.home
            row["odds_draw"] = m.odds.draw
            row["odds_away"] = m.odds.away
            row["odds_margin"] = m.odds.margin
        rows.append(row)

    return pd.DataFrame(rows)
