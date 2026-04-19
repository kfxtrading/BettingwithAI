"""Cookie-consent persistence.

Stores per-IP consent records in a single JSON file under ``data/consents.json``.
Designed for low-traffic deployments — a SQLite/Postgres backend can replace this
later without changing the public API surface.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Request

from football_betting.config import DATA_DIR

CONSENTS_FILE: Path = DATA_DIR / "consents.json"
_LOCK = threading.Lock()
_logger = logging.getLogger("football_betting.api")


def _client_ip(request: Request) -> str:
    """Extract the originating client IP, honouring common proxy headers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _hash_ip(ip: str) -> str:
    """One-way hash so we never persist raw IPs at rest."""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def _load_all() -> dict[str, dict[str, Any]]:
    if not CONSENTS_FILE.exists():
        return {}
    try:
        with CONSENTS_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        _logger.warning("[consent] failed to read %s: %s", CONSENTS_FILE, exc)
        return {}


def _write_all(data: dict[str, dict[str, Any]]) -> None:
    CONSENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONSENTS_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
    tmp.replace(CONSENTS_FILE)


def save_consent(
    request: Request,
    *,
    accepted: bool,
    categories: list[str],
    user_agent: str | None = None,
    version: str = "1.0",
) -> dict[str, Any]:
    ip = _client_ip(request)
    ip_hash = _hash_ip(ip)
    record = {
        "ip_hash": ip_hash,
        "accepted": bool(accepted),
        "categories": sorted({c.strip() for c in categories if c.strip()}),
        "user_agent": (user_agent or request.headers.get("user-agent", ""))[:512],
        "version": version,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with _LOCK:
        data = _load_all()
        existing = data.get(ip_hash)
        if existing and "first_seen_at" in existing:
            record["first_seen_at"] = existing["first_seen_at"]
        else:
            record["first_seen_at"] = record["updated_at"]
        data[ip_hash] = record
        _write_all(data)
    return record


def get_consent(request: Request) -> dict[str, Any] | None:
    ip_hash = _hash_ip(_client_ip(request))
    with _LOCK:
        return _load_all().get(ip_hash)
