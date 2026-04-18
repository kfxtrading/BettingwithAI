"""Persistence helpers for prediction snapshots."""
from __future__ import annotations

import json

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
