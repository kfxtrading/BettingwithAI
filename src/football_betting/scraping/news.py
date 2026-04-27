"""
Lightweight football news fetcher using Google News RSS.

No API key required. Results are cached in-memory with a 2-hour TTL so
repeated calls within a prediction/snapshot cycle do not hit the network.
"""
from __future__ import annotations

import logging
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from threading import Lock
from typing import NamedTuple
from urllib.parse import quote_plus

import requests

logger = logging.getLogger("football_betting.api")

_TTL_SECONDS = 7200  # 2 hours
_FETCH_TIMEOUT = 8   # seconds
_MAX_ITEMS = 5


class NewsItem(NamedTuple):
    title: str
    url: str
    source: str


@dataclass
class _CacheEntry:
    items: list[NewsItem]
    expires_at: float


_cache: dict[str, _CacheEntry] = {}
_lock = Lock()


def _normalise(text: str) -> str:
    """Lowercase + strip accents for cache-key dedup."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _rss_url(team: str) -> str:
    query = quote_plus(f"{team} football")
    return (
        f"https://news.google.com/rss/search"
        f"?q={query}&hl=en&gl=GB&ceid=GB:en"
    )


def _fetch_rss(team: str) -> list[NewsItem]:
    url = _rss_url(team)
    try:
        resp = requests.get(
            url,
            timeout=_FETCH_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BettingwithAI/1.0)"},
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.debug("[news] RSS fetch failed for %r: %s", team, exc)
        return []

    items: list[NewsItem] = []
    try:
        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []
        for item_el in channel.findall("item")[:_MAX_ITEMS]:
            title_el = item_el.find("title")
            link_el = item_el.find("link")
            source_el = item_el.find("source")
            if title_el is None or link_el is None:
                continue
            title = (title_el.text or "").strip()
            link = (link_el.text or "").strip()
            source = (
                (source_el.text or "").strip() if source_el is not None else "News"
            ) or "News"
            if title and link:
                items.append(NewsItem(title=title, url=link, source=source))
    except ET.ParseError as exc:
        logger.debug("[news] RSS parse error for %r: %s", team, exc)
    return items


def fetch_team_news(team: str, max_items: int = 3) -> list[NewsItem]:
    """Return recent news headlines for *team* (cached 2 h in-memory).

    Returns an empty list on any network or parse failure so callers never
    need to handle exceptions from this function.
    """
    key = _normalise(team)
    now = time.monotonic()

    with _lock:
        entry = _cache.get(key)
        if entry is not None and entry.expires_at > now:
            return entry.items[:max_items]

    items = _fetch_rss(team)
    logger.debug("[news] fetched %d items for %r", len(items), team)

    with _lock:
        _cache[key] = _CacheEntry(items=items, expires_at=now + _TTL_SECONDS)

    return items[:max_items]


def fetch_match_news(home_team: str, away_team: str, max_per_team: int = 2) -> list[NewsItem]:
    """Fetch and merge news for both teams in a fixture.

    Returns up to ``max_per_team`` items per team, interleaved so the result
    alternates home/away headlines.
    """
    home_news = fetch_team_news(home_team, max_items=max_per_team)
    away_news = fetch_team_news(away_team, max_items=max_per_team)
    merged: list[NewsItem] = []
    for h, a in zip(home_news, away_news):
        merged.append(h)
        merged.append(a)
    # Append any remaining items from the longer list
    for item in home_news[len(away_news):]:
        merged.append(item)
    for item in away_news[len(home_news):]:
        merged.append(item)
    return merged
