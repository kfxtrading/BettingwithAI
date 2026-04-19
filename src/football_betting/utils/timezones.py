"""League timezone handling with DST (summer/winter time) awareness.

All kickoff times are internally carried as UTC-aware datetimes. Conversion
to/from league-local time uses ``zoneinfo.ZoneInfo`` which resolves DST
transitions (CET ↔ CEST, GMT ↔ BST, …) automatically from the IANA tz db.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# IANA timezone per league key. Keep in sync with football_betting.config.LEAGUES.
LEAGUE_TIMEZONES: dict[str, str] = {
    "PL": "Europe/London",
    "CH": "Europe/London",
    "BL": "Europe/Berlin",
    "SA": "Europe/Rome",
    "LL": "Europe/Madrid",
}

DEFAULT_TZ = "UTC"


def league_tz_name(league_key: str) -> str:
    """Return IANA timezone string for a league (falls back to UTC)."""
    return LEAGUE_TIMEZONES.get(league_key, DEFAULT_TZ)


def league_tz(league_key: str) -> ZoneInfo:
    """Return ``ZoneInfo`` for the league's local timezone."""
    return ZoneInfo(league_tz_name(league_key))


def local_to_utc(local_dt: datetime, league_key: str) -> datetime:
    """Attach the league tz to a naive local datetime and convert to UTC.

    Ambiguous wall-clock times during the DST end transition are resolved
    deterministically via ``fold=0`` (earlier occurrence).
    """
    if local_dt.tzinfo is not None:
        return local_dt.astimezone(timezone.utc)
    tz = league_tz(league_key)
    aware = local_dt.replace(tzinfo=tz, fold=0)
    return aware.astimezone(timezone.utc)


def utc_to_local(utc_dt: datetime, league_key: str) -> datetime:
    """Convert UTC-aware datetime to the league's local timezone (DST-aware)."""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(league_tz(league_key))


def isoformat_utc(dt: datetime) -> str:
    """Serialize a UTC-aware datetime with a trailing ``Z``."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
