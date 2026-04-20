"""Persistence helpers for prediction snapshots."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from football_betting.api.schemas import TodayPayload
from football_betting.config import SNAPSHOT_DIR


TODAY_FILE = "today.json"


def today_path() -> str:
    return str(SNAPSHOT_DIR / TODAY_FILE)


def load_today() -> TodayPayload | None:
    path = SNAPSHOT_DIR / TODAY_FILE
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return TodayPayload(**raw)


def write_today(payload: TodayPayload) -> str:
    path = SNAPSHOT_DIR / TODAY_FILE
    path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return str(path)


def write_league(league_key: str, payload: TodayPayload) -> str:
    path = SNAPSHOT_DIR / f"{league_key.upper()}.json"
    path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return str(path)


def snapshot_exists() -> bool:
    return (SNAPSHOT_DIR / TODAY_FILE).exists()


def snapshot_is_stale(refresh_hour_utc: int, now: datetime | None = None) -> bool:
    """True if today.json is missing or older than the last expected refresh.

    The scheduler runs daily at `refresh_hour_utc`. After a restart we want
    to catch up on any missed refresh (crash, port conflict, deploy) instead
    of idling until the next scheduled run.
    """
    payload = load_today()
    if payload is None:
        return True
    generated = payload.generated_at
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    expected = current.replace(
        hour=refresh_hour_utc, minute=0, second=0, microsecond=0
    )
    if expected > current:
        expected -= timedelta(days=1)
    return generated < expected
