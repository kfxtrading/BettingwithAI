"""Football-Data.co.uk fixture/result source for TheOdds-free operation."""

from __future__ import annotations

import logging
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from football_betting.config import LEAGUES, RAW_DIR
from football_betting.data.downloader import download_season, season_code
from football_betting.data.loader import _extract_kickoff, _extract_odds
from football_betting.utils.timezones import isoformat_utc, league_tz_name

logger = logging.getLogger(__name__)

_REFRESHED_AT: dict[tuple[str, str], datetime] = {}


def season_for_date(day: date) -> str:
    """Infer European football season label for a match date."""
    if day.month >= 8:
        return f"{day.year}-{str(day.year + 1)[-2:]}"
    return f"{day.year - 1}-{str(day.year)[-2:]}"


def _refresh_interval() -> timedelta:
    raw = os.getenv("FOOTBALL_DATA_REFRESH_INTERVAL_MIN", "30")
    try:
        minutes = max(0, int(raw))
    except ValueError:
        logger.warning(
            "Invalid FOOTBALL_DATA_REFRESH_INTERVAL_MIN=%r, defaulting to 30.",
            raw,
        )
        minutes = 30
    return timedelta(minutes=minutes)


def _parse_date_value(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if pd.isna(value):
        return None
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _season_csv_path(league_key: str, season: str) -> Path:
    return RAW_DIR / f"{LEAGUES[league_key].code}_{season_code(season)}.csv"


def ensure_season_csv(
    league_key: str,
    season: str,
    *,
    refresh: bool,
) -> Path:
    """Return local CSV path, refreshing Football-Data at a modest cadence."""
    path = _season_csv_path(league_key, season)
    if not refresh:
        return path

    now = datetime.now(UTC)
    cache_key = (league_key, season)
    last = _REFRESHED_AT.get(cache_key)
    if last is not None and now - last < _refresh_interval() and path.exists():
        return path

    try:
        path = download_season(LEAGUES[league_key], season, force=True)
        _REFRESHED_AT[cache_key] = now
    except Exception as exc:  # noqa: BLE001 - stale CSV is better than no source
        logger.warning(
            "[football-data] refresh failed for %s %s: %s; using local CSV if present",
            league_key,
            season,
            exc,
        )
    return path


def _read_season_csv(
    league_key: str,
    season: str,
    *,
    refresh: bool,
) -> pd.DataFrame:
    path = ensure_season_csv(league_key, season, refresh=refresh)
    if not path.exists():
        raise FileNotFoundError(
            f"No Football-Data CSV for {league_key} {season}: {path}"
        )
    return pd.read_csv(path, encoding_errors="replace")


def load_fixtures_for_date(
    target_date: date,
    *,
    leagues: list[str] | None = None,
    refresh: bool = True,
) -> list[dict[str, Any]]:
    """Load fixtures for one date from Football-Data current-season CSVs.

    Rows with and without final scores are returned. This lets the landing page
    keep showing the day's card after kickoff while the enrichment layer marks
    completed results once the CSV is refreshed.
    """
    keys = leagues or list(LEAGUES.keys())
    out: list[dict[str, Any]] = []
    season = season_for_date(target_date)

    for raw_key in keys:
        league_key = raw_key.upper()
        if league_key not in LEAGUES:
            continue
        try:
            df = _read_season_csv(league_key, season, refresh=refresh)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[football-data] fixture load failed for %s: %s", league_key, exc)
            continue

        tz_name = league_tz_name(league_key)
        for _, row in df.iterrows():
            match_date = _parse_date_value(row.get("Date"))
            if match_date != target_date:
                continue
            home = str(row.get("HomeTeam") or "").strip()
            away = str(row.get("AwayTeam") or "").strip()
            if not home or not away or home.lower() == "nan" or away.lower() == "nan":
                continue

            payload: dict[str, Any] = {
                "date": target_date.isoformat(),
                "league": league_key,
                "home_team": home,
                "away_team": away,
                "league_timezone": tz_name,
                "source": "football_data",
            }

            raw_time = row.get("Time")
            if raw_time is not None and not pd.isna(raw_time):
                payload["kickoff_time"] = str(raw_time).strip()

            kickoff_utc = _extract_kickoff(row, league_key)
            if kickoff_utc is not None:
                payload["kickoff_utc"] = isoformat_utc(kickoff_utc)

            odds = _extract_odds(row)
            if odds is not None:
                payload["odds"] = {
                    "home": odds.home,
                    "draw": odds.draw,
                    "away": odds.away,
                    "bookmaker": odds.bookmaker,
                }

            out.append(payload)

    return sorted(
        out,
        key=lambda x: (
            str(x.get("league") or ""),
            str(x.get("kickoff_utc") or x.get("kickoff_time") or ""),
            str(x.get("home_team") or ""),
        ),
    )


def load_completed_results(
    *,
    league_codes: list[str] | None = None,
    days_from: int = 3,
    refresh: bool = True,
) -> list[dict[str, Any]]:
    """Load recently completed match results from Football-Data CSVs."""
    today = date.today()
    start = today - timedelta(days=max(1, days_from) - 1)
    wanted_codes = set(league_codes) if league_codes is not None else {
        cfg.code for cfg in LEAGUES.values()
    }
    out: list[dict[str, Any]] = []

    for league_key, cfg in LEAGUES.items():
        if cfg.code not in wanted_codes:
            continue
        seasons = {season_for_date(start), season_for_date(today)}
        for season in sorted(seasons):
            try:
                df = _read_season_csv(league_key, season, refresh=refresh)
            except Exception as exc:  # noqa: BLE001
                logger.warning("[football-data] result load failed for %s: %s", league_key, exc)
                continue

            for _, row in df.iterrows():
                match_date = _parse_date_value(row.get("Date"))
                if match_date is None or match_date < start or match_date > today:
                    continue
                ftr = str(row.get("FTR") or "").strip().upper()
                if ftr not in {"H", "D", "A"}:
                    continue
                try:
                    fthg = int(row["FTHG"])
                    ftag = int(row["FTAG"])
                except (KeyError, ValueError, TypeError):
                    continue
                home = str(row.get("HomeTeam") or "").strip()
                away = str(row.get("AwayTeam") or "").strip()
                if not home or not away:
                    continue
                kickoff_utc = _extract_kickoff(row, league_key)
                out.append(
                    {
                        "league_code": cfg.code,
                        "date": match_date.isoformat(),
                        "home_team": home,
                        "away_team": away,
                        "ftr": ftr,
                        "fthg": fthg,
                        "ftag": ftag,
                        "kickoff_utc": isoformat_utc(kickoff_utc)
                        if kickoff_utc is not None
                        else None,
                    }
                )

    return out
