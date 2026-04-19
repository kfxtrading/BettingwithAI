"""Submit URLs to the IndexNow protocol (Bing, Yandex, Naver, Seznam, Yep).

Set the following environment variables to enable submission:

* ``INDEXNOW_KEY``  - 32-char hex string. Must also be served by the web app
  at the URL given in ``INDEXNOW_KEY_LOCATION`` (or at ``/{key}.txt`` of the
  site root if you prefer the default path).
* ``INDEXNOW_KEY_LOCATION`` - absolute URL where the key file is reachable,
  e.g. ``https://bettingwithai.app/indexnow/<key>``. Optional - defaults to
  ``{site}/indexnow/{key}``.
* ``SITE_URL`` (or ``NEXT_PUBLIC_SITE_URL``) - public origin of the site.
"""

from __future__ import annotations

import logging
import os
from typing import Iterable

LOGGER = logging.getLogger(__name__)

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def _site_url() -> str | None:
    return os.environ.get("SITE_URL") or os.environ.get("NEXT_PUBLIC_SITE_URL")


def _key_location(site: str, key: str) -> str:
    explicit = os.environ.get("INDEXNOW_KEY_LOCATION")
    if explicit:
        return explicit
    return f"{site.rstrip('/')}/indexnow/{key}"


def ping_indexnow(urls: Iterable[str], *, timeout: float = 10.0) -> bool:
    """POST a batch of URLs to the IndexNow endpoint.

    Returns ``True`` on a 2xx response, ``False`` on any failure or when
    configuration is missing. Designed to be safe to call after every
    snapshot — never raises.
    """
    key = os.environ.get("INDEXNOW_KEY")
    site = _site_url()
    url_list = [u for u in urls if u]
    if not key or not site or not url_list:
        LOGGER.debug(
            "IndexNow skipped (key=%s, site=%s, urls=%d)",
            bool(key),
            bool(site),
            len(url_list),
        )
        return False

    host = site.replace("https://", "").replace("http://", "").rstrip("/")
    payload = {
        "host": host,
        "key": key,
        "keyLocation": _key_location(site, key),
        "urlList": url_list,
    }
    import httpx  # lazy: keep import cost off the `seo` package init path

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(INDEXNOW_ENDPOINT, json=payload)
    except httpx.HTTPError as exc:  # pragma: no cover - network failure
        LOGGER.warning("IndexNow request failed: %s", exc)
        return False

    if 200 <= response.status_code < 300:
        LOGGER.info("IndexNow accepted %d URLs (status=%s)", len(url_list), response.status_code)
        return True
    LOGGER.warning(
        "IndexNow rejected: status=%s body=%s", response.status_code, response.text[:200]
    )
    return False


def build_snapshot_urls(*, leagues: Iterable[str] = ()) -> list[str]:
    """Compose the list of URLs to ping after a fresh snapshot."""
    site = _site_url()
    if not site:
        return []
    base = site.rstrip("/")
    locales = ("en", "de", "fr", "it", "es")
    paths = ["/", "/leagues", "/performance"]
    for league in leagues:
        paths.append(f"/leagues/{league}")
    return [f"{base}/{loc}{p if p != '/' else ''}" for loc in locales for p in paths]
