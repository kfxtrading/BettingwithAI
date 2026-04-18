"""
SQLite-backed response cache for scraped API data.

TTL-aware: entries expire after N days. Atomic writes via transactions.
Keyed on (url, params_hash) to handle different query parameters.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from football_betting.config import SOFASCORE_DIR


@dataclass(slots=True)
class ResponseCache:
    """SQLite-backed HTTP response cache."""

    db_path: Path = SOFASCORE_DIR / "cache.sqlite"
    default_ttl_seconds: int = 7 * 86400  # 7 days

    def __post_init__(self) -> None:
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS response_cache (
                    key TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    body BLOB NOT NULL,
                    status INTEGER NOT NULL,
                    cached_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires ON response_cache(expires_at)"
            )

    @staticmethod
    def _cache_key(url: str, params: dict | None = None) -> str:
        """Deterministic cache key from URL + sorted params."""
        payload = {"url": url, "params": params or {}}
        serialized = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(serialized).hexdigest()

    def get(self, url: str, params: dict | None = None) -> str | None:
        """Return cached response body as str, or None if missing/expired."""
        key = self._cache_key(url, params)
        now = int(time.time())
        with self._conn() as conn:
            row = conn.execute(
                "SELECT body, expires_at FROM response_cache WHERE key=?", (key,)
            ).fetchone()
        if row is None:
            return None
        if row["expires_at"] < now:
            self.delete(url, params)
            return None
        body = row["body"]
        return body.decode() if isinstance(body, bytes) else str(body)

    def set(
        self,
        url: str,
        body: str,
        status: int = 200,
        params: dict | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store response body with TTL."""
        key = self._cache_key(url, params)
        now = int(time.time())
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO response_cache
                   (key, url, body, status, cached_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (key, url, body.encode(), status, now, now + ttl),
            )

    def delete(self, url: str, params: dict | None = None) -> None:
        key = self._cache_key(url, params)
        with self._conn() as conn:
            conn.execute("DELETE FROM response_cache WHERE key=?", (key,))

    def purge_expired(self) -> int:
        """Remove all expired entries; return count deleted."""
        now = int(time.time())
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM response_cache WHERE expires_at < ?", (now,)
            )
            return cursor.rowcount

    def clear_all(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM response_cache")

    def stats(self) -> dict[str, int]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as n, SUM(LENGTH(body)) as bytes FROM response_cache"
            ).fetchone()
        return {"entries": row["n"] or 0, "total_bytes": row["bytes"] or 0}
