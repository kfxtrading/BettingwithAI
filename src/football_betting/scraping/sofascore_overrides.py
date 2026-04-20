"""Static ``sofascore_event_id`` overrides keyed by match slug.

Production hosts (Railway, most cloud IPs) are routinely blocked by
Sofascore's Cloudflare layer even with ``curl_cffi``'s browser-TLS
fingerprint. This module provides a deterministic fallback:

* Operators resolve event IDs from a trusted network (local machine or
  GitHub Actions runner) using ``fb resolve-sofascore-ids``.
* Resolved IDs are persisted to ``data/sofascore_id_overrides.json``
  (committed to the repo and baked into the Railway Docker image).
* Runtime lookups (``get_match_wrapper``, snapshot build) consult this
  file first and only fall back to live Sofascore calls when the slug is
  missing.

The file is kept tiny (one int per slug) and is considered authoritative
— once a slug is mapped, we do not re-query Sofascore for it.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Ship the overrides as package data so they are baked into the Docker
# image and cannot be shadowed by stale files on the runtime volume.
OVERRIDES_PATH: Path = (
    Path(__file__).resolve().parent.parent / "_bundled" / "sofascore_id_overrides.json"
)


def _read_raw() -> dict[str, int]:
    """Load the overrides mapping, tolerating missing/corrupt files."""
    if not OVERRIDES_PATH.exists():
        return {}
    try:
        raw = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("sofascore overrides unreadable (%s): %s", OVERRIDES_PATH, exc)
        return {}
    if not isinstance(raw, dict):
        logger.warning("sofascore overrides not a dict: %s", OVERRIDES_PATH)
        return {}
    out: dict[str, int] = {}
    for slug, event_id in raw.items():
        if not isinstance(slug, str):
            continue
        try:
            out[slug] = int(event_id)
        except (TypeError, ValueError):
            continue
    return out


def get_override(slug: str) -> int | None:
    """Return the pinned event_id for ``slug`` or ``None`` if absent."""
    if not slug:
        return None
    return _read_raw().get(slug)


def set_override(slug: str, event_id: int) -> None:
    """Write a single slug → event_id mapping, preserving existing entries."""
    if not slug:
        raise ValueError("slug must be non-empty")
    data = _read_raw()
    data[slug] = int(event_id)
    OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDES_PATH.write_text(
        json.dumps(dict(sorted(data.items())), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_all() -> dict[str, int]:
    """Return a copy of all overrides (for diagnostics / bulk reads)."""
    return dict(_read_raw())
