"""
Zulubet HTTP client for daily 1X2 tip pages.

The site publishes one HTML page per calendar day under
``https://www.zulubet.com/tips-DD-MM-YYYY.html``. From every page we keep
exactly three columns:

* ``date``  — taken from the URL (canonical, timezone-free)
* ``home``  — home team
* ``away``  — away team
* ``tip``   — the site's 1X2 pick: ``1`` / ``X`` / ``2`` / ``1X`` / ``X2`` / ``12``

This is intended as a feature/label source for 1X2 model training, not for
value-bet evaluation, so we deliberately ignore the probability columns,
average odds, FT score and result-indicator cells.

Notes:
* Pages older than 2024-01-01 return HTTP 410 — the server keeps no archive
  beyond that. ``earliest_date`` in :class:`~football_betting.config.ZulubetConfig`
  reflects this.
* The TLS certificate on zulubet.com is currently expired, so requests must
  skip cert verification (``verify=False``).
* Disabled by default — set ``SCRAPING_ENABLED=1`` to activate.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
from curl_cffi import requests
from rich.console import Console

from football_betting.config import ZULUBET_CFG, ZULUBET_DIR, ZulubetConfig
from football_betting.scraping.cache import ResponseCache
from football_betting.scraping.rate_limiter import TokenBucketLimiter

console = Console()
logger = logging.getLogger("football_betting.scraping.zulubet")

DEFAULT_PARQUET_PATH: Path = ZULUBET_DIR / "zulubet_tips.parquet"

_VALID_TIPS: frozenset[str] = frozenset({"1", "X", "2", "1X", "X2", "12"})

# A match row in the daily tips table contains, in order:
#   <td> <noscript>DD-MM, HH:MM</noscript> ... </td>          ← kickoff
#   <td> <img class="flags ..."> Home - Away </td>            ← teams
#   <td class="prediction_min"> ... </td>                      ← 1X2 probs (mobile)
#   <td class="prob prediction_full"> N% </td> × 3             ← 1X2 probs (desktop)
#   <td style="text-align: center;"><span ..><b>TIP</b></span></td>  ← TIPS (or empty)
#   ... (avg odds, FT score, result indicator — ignored)
#
# We extract only the three cells we need with focused regexes.
_RE_NOSCRIPT_TIME = re.compile(r"<noscript>\s*([0-9]{2}-[0-9]{2},\s*[0-9]{2}:[0-9]{2})\s*</noscript>")
# The tip cell is identified by <b>...</b> wrapping a 1X2 token, possibly
# inside a <span style="color:..."> for hit/miss colouring.
_RE_TIP = re.compile(r"<b>\s*(1X|X2|12|1|X|2)\s*</b>", re.IGNORECASE)
_RE_TR = re.compile(r"<tr[^>]*>([\s\S]*?)</tr>", re.IGNORECASE)
_RE_TD = re.compile(r"<td[\s\S]*?</td>", re.IGNORECASE)
_RE_STRIP_TAGS = re.compile(r"<[^>]+>")
# The per-match probability cell embeds an inner <table class="prob_table">
# whose nested <tr>/</tr> would prematurely terminate the outer match-row
# regex. We strip those inner tables (and the <script> blocks injected for
# user-local kickoff times) before iterating top-level rows.
_RE_INNER_PROB_TABLE = re.compile(
    r'<table\s+class="prob_table"[^>]*>[\s\S]*?</table>', re.IGNORECASE
)
_RE_SCRIPT = re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE)


@dataclass(slots=True)
class ZulubetTip:
    """One row of (date, home, away, tip) — flat schema for ML training."""

    date: date
    home: str
    away: str
    tip: str

    def to_dict(self) -> dict[str, str]:
        return {
            "date": self.date.isoformat(),
            "home": self.home,
            "away": self.away,
            "tip": self.tip,
        }


@dataclass(slots=True)
class ZulubetClient:
    """Rate-limited, cached client for zulubet.com daily tip pages."""

    cfg: ZulubetConfig = field(default_factory=lambda: ZULUBET_CFG)
    cache: ResponseCache = field(
        default_factory=lambda: ResponseCache(
            db_path=ZULUBET_DIR / "cache.sqlite",
            default_ttl_seconds=ZULUBET_CFG.cache_ttl_days * 86400,
        )
    )
    _limiter: TokenBucketLimiter = field(init=False)

    def __post_init__(self) -> None:
        self._limiter = TokenBucketLimiter.from_delay(
            self.cfg.request_delay_seconds, burst=1
        )

    # ───────────────────────── HTTP layer ─────────────────────────

    def _build_headers(self) -> dict[str, str]:
        # As with Sofascore: do NOT override User-Agent — curl_cffi's
        # impersonation handles UA + TLS fingerprint together.
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.zulubet.com/",
            "Upgrade-Insecure-Requests": "1",
        }

    def _url_for(self, day: date) -> str:
        return f"{self.cfg.base_url}/tips-{day.strftime('%d-%m-%Y')}.html"

    def _ttl_for(self, day: date) -> int:
        """Long TTL for past dates, short TTL for today (page still updates)."""
        if day >= date.today():
            return self.cfg.cache_ttl_today_seconds
        return self.cfg.cache_ttl_days * 86400

    def fetch_page(
        self,
        day: date,
        *,
        use_cache: bool = True,
        force: bool = False,
    ) -> str | None:
        """Fetch the raw HTML for one day. Returns ``None`` on 410/404/blocked.

        ``force=True`` bypasses the global ``SCRAPING_ENABLED`` gate (matches
        the Sofascore pattern — used by ad-hoc backfills started by the user).
        """
        if not self.cfg.enabled and not force:
            raise RuntimeError(
                "Zulubet scraping disabled. Set env var SCRAPING_ENABLED=1 to enable."
            )

        if day < self.cfg.earliest_date:
            logger.debug(
                "[zulubet] skipping %s — older than earliest_date %s",
                day,
                self.cfg.earliest_date,
            )
            return None

        url = self._url_for(day)

        if use_cache:
            cached = self.cache.get(url)
            if cached is not None:
                return cached

        self._limiter.acquire()

        last_exc: Exception | None = None
        for attempt in range(self.cfg.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=self._build_headers(),
                    timeout=self.cfg.timeout_seconds,
                    impersonate=self.cfg.impersonate,
                    verify=self.cfg.verify_tls,
                )
                if response.status_code == 200:
                    if use_cache:
                        self.cache.set(url, response.text, ttl_seconds=self._ttl_for(day))
                    return response.text
                # 410 = pre-archive cutoff; permanent. Don't retry, don't pollute cache.
                if response.status_code == 410:
                    logger.info("[zulubet] %s → HTTP 410 (out of archive)", url)
                    return None
                if response.status_code == 404:
                    return None
                if response.status_code in (429, 503):
                    wait = self.cfg.retry_backoff_base ** (attempt + 1)
                    console.log(
                        f"[yellow]Zulubet HTTP {response.status_code}, "
                        f"sleeping {wait}s and retrying[/yellow]"
                    )
                    time.sleep(wait)
                    continue
                if response.status_code == 403:
                    console.log(
                        f"[yellow]Zulubet HTTP 403 (bot wall) for {url} — giving up[/yellow]"
                    )
                    return None
                console.log(f"[red]HTTP {response.status_code} for {url}[/red]")
                return None
            except requests.RequestsError as e:
                last_exc = e
                wait = self.cfg.retry_backoff_base ** (attempt + 1)
                console.log(f"[yellow]Request failed ({e}), retrying in {wait}s[/yellow]")
                time.sleep(wait)

        if last_exc is not None:
            console.log(f"[red]All retries exhausted for {url}: {last_exc}[/red]")
        return None

    # ───────────────────────── Parsing ─────────────────────────

    @staticmethod
    def _strip(html: str) -> str:
        return _RE_STRIP_TAGS.sub("", html).strip()

    @classmethod
    def parse_page(cls, html: str, day: date) -> list[ZulubetTip]:
        """Extract (date, home, away, tip) rows from one daily tip page.

        Strategy: iterate ``<tr>`` blocks; a row is a match row iff it contains
        BOTH a ``<noscript>DD-MM, HH:MM</noscript>`` kickoff stamp AND a
        ``<b>TIP</b>`` cell with a valid 1X2 token. Rows missing either (e.g.
        the table caption row, header rows, rows where the tip wasn't yet
        published) are skipped.
        """
        # Flatten nested <table class="prob_table"> + <script> so the outer
        # <tr> regex captures the full match row.
        cleaned = _RE_INNER_PROB_TABLE.sub("", html)
        cleaned = _RE_SCRIPT.sub("", cleaned)
        rows: list[ZulubetTip] = []
        for tr_match in _RE_TR.finditer(cleaned):
            tr_html = tr_match.group(1)
            if _RE_NOSCRIPT_TIME.search(tr_html) is None:
                continue
            tip_match = _RE_TIP.search(tr_html)
            if tip_match is None:
                continue
            tip = tip_match.group(1).upper()
            if tip not in _VALID_TIPS:
                continue

            # Walk the row's <td> cells in order; the first one whose stripped
            # text contains " - " is the team cell. The kickoff cell is always
            # before it (we don't need the time itself for the 3-column output).
            teams_text: str | None = None
            for td in _RE_TD.finditer(tr_html):
                text = cls._strip(td.group(0))
                # Skip the kickoff cell — its stripped form looks like
                # "31-03, 23:00" (no " - " separator with spaces).
                if " - " in text and not _RE_NOSCRIPT_TIME.search(td.group(0)):
                    teams_text = text
                    break
            if teams_text is None:
                continue

            home, sep, away = teams_text.partition(" - ")
            if not sep or not home or not away:
                continue

            rows.append(
                ZulubetTip(
                    date=day,
                    home=home.strip(),
                    away=away.strip(),
                    tip=tip,
                )
            )
        return rows

    def fetch_day(
        self,
        day: date,
        *,
        use_cache: bool = True,
        force: bool = False,
    ) -> list[ZulubetTip]:
        """Convenience: fetch + parse one day. Empty list on 410/404/parse miss."""
        html = self.fetch_page(day, use_cache=use_cache, force=force)
        if html is None:
            return []
        return self.parse_page(html, day)

    # ───────────────────────── Backfill ─────────────────────────

    def iter_dates(
        self,
        start: date,
        end: date | None = None,
    ) -> Iterable[date]:
        """Inclusive date range, clamped to ``cfg.earliest_date``."""
        first = max(start, self.cfg.earliest_date)
        last = end or date.today()
        if last < first:
            return
        cur = first
        while cur <= last:
            yield cur
            cur += timedelta(days=1)

    def backfill(
        self,
        start: date | None = None,
        end: date | None = None,
        *,
        force: bool = False,
        on_progress: callable | None = None,  # type: ignore[type-arg]
    ) -> list[ZulubetTip]:
        """Iterate ``[start, end]`` and collect every parsed tip row.

        Defaults to ``[earliest_date, today]``. ``force=True`` bypasses the
        ``SCRAPING_ENABLED`` gate.
        """
        start = start or self.cfg.earliest_date
        end = end or date.today()
        tips: list[ZulubetTip] = []
        for day in self.iter_dates(start, end):
            day_tips = self.fetch_day(day, force=force)
            tips.extend(day_tips)
            if on_progress is not None:
                on_progress(day, len(day_tips))
        return tips

    # ───────────────────────── Persistence ─────────────────────────

    @staticmethod
    def to_dataframe(tips: Iterable[ZulubetTip]) -> pd.DataFrame:
        df = pd.DataFrame([t.to_dict() for t in tips], columns=["date", "home", "away", "tip"])
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def save_parquet(
        self,
        tips: Iterable[ZulubetTip],
        path: Path = DEFAULT_PARQUET_PATH,
        *,
        merge_existing: bool = True,
    ) -> Path:
        """Persist parsed tips as parquet.

        ``merge_existing=True`` (default) reads the existing file (if any),
        concatenates the new rows, and de-dupes on ``(date, home, away)``
        keeping the **latest** tip — so a re-run replaces same-day rows
        without losing historical ones.
        """
        new_df = self.to_dataframe(tips)
        if merge_existing and path.exists():
            old_df = pd.read_parquet(path)
            # Defensive: the on-disk file from an earlier run might already
            # carry datetime64 dates — normalise both sides.
            for d in (old_df, new_df):
                if not d.empty and not isinstance(d["date"].iloc[0], date):
                    d["date"] = pd.to_datetime(d["date"]).dt.date
            combined = pd.concat([old_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=["date", "home", "away"], keep="last"
            )
        else:
            combined = new_df
        combined = combined.sort_values(["date", "home", "away"]).reset_index(drop=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_parquet(path, index=False)
        return path

    @staticmethod
    def load_parquet(path: Path = DEFAULT_PARQUET_PATH) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame(columns=["date", "home", "away", "tip"])
        return pd.read_parquet(path)


__all__ = [
    "DEFAULT_PARQUET_PATH",
    "ZulubetClient",
    "ZulubetTip",
]
