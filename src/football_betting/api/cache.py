"""Tiny in-memory TTL cache shared across routers."""
from __future__ import annotations

import threading
import time
from typing import Any


class TTLCache:
    """Thread-safe key/value store with per-key expiry."""

    def __init__(self, default_ttl_seconds: float = 60.0) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl_seconds

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < time.monotonic():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            self._store[key] = (time.monotonic() + ttl, value)

    def delete(self, key: str) -> None:
        """Evict a single key (no-op if missing)."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


cache = TTLCache(default_ttl_seconds=60.0)
