"""Trigger Next.js on-demand revalidation after a snapshot refresh.

The web service exposes ``POST /api/revalidate`` which calls
``revalidatePath(path, 'page')`` for each path in the payload. Without this
hook, league pages keep serving stale ISR cache for up to the fetch
revalidate window (10 min), which means users see yesterday's fixtures for
several minutes after the daily snapshot refresh.

Config (env vars):
    WEB_REVALIDATE_URL — full URL of the web route, e.g.
                         ``https://bettingwithai.app/api/revalidate``.
    REVALIDATE_TOKEN   — shared secret, matched against ``x-revalidate-token``.
"""
from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger("football_betting.api")


# All dynamic routes whose cache depends on today's snapshot. Next.js accepts
# the literal route template (with ``[param]`` placeholders) and revalidates
# every concrete URL that matches.
_SNAPSHOT_PATHS: list[str] = [
    "/[locale]",
    "/[locale]/leagues",
    "/[locale]/leagues/[league]",
    "/[locale]/leagues/[league]/[match]",
]


def revalidate_snapshot_paths(paths: list[str] | None = None) -> None:
    """POST revalidation request; swallow network/auth errors."""
    url = os.environ.get("WEB_REVALIDATE_URL")
    token = os.environ.get("REVALIDATE_TOKEN")
    if not url or not token:
        logger.info(
            "[revalidate] WEB_REVALIDATE_URL/REVALIDATE_TOKEN not set — skipping."
        )
        return

    to_send = paths if paths is not None else _SNAPSHOT_PATHS
    try:
        resp = requests.post(
            url,
            json={"paths": to_send},
            headers={"x-revalidate-token": token},
            timeout=10,
        )
    except requests.RequestException as exc:
        logger.warning("[revalidate] HTTP error calling %s: %s", url, exc)
        return

    if resp.status_code == 200:
        try:
            body = resp.json()
        except ValueError:
            body = resp.text[:200]
        logger.info("[revalidate] ok -> %s", body)
    else:
        logger.warning(
            "[revalidate] %s returned HTTP %d: %s",
            url, resp.status_code, resp.text[:200],
        )
