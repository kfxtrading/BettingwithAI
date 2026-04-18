"""
In-process daily snapshot refresher.

Runs alongside the FastAPI server (same event loop, no extra process),
so deployments on Railway / Docker / localhost all behave the same.

Flow on each refresh:
    Odds API -> fixtures_<today>.json -> today.json snapshot

Configuration (env vars):
    ODDS_API_KEY              — required; without it the scheduler logs and idles.
    SNAPSHOT_REFRESH_HOUR_UTC — integer 0-23, default 7 (=08:00 Berlin in winter).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone

from football_betting.api.services import build_predictions_for_fixtures
from football_betting.api.snapshots import snapshot_exists, write_today
from football_betting.config import DATA_DIR, ODDS_API_CFG
from football_betting.scraping.odds_api import OddsApiClient, OddsApiError

logger = logging.getLogger("football_betting.api")


def _refresh_hour_utc() -> int:
    raw = os.environ.get("SNAPSHOT_REFRESH_HOUR_UTC", "7")
    try:
        h = int(raw)
    except ValueError:
        logger.warning("[scheduler] Invalid SNAPSHOT_REFRESH_HOUR_UTC=%r, defaulting to 7.", raw)
        return 7
    return max(0, min(23, h))


def _refresh_blocking() -> None:
    """Sync refresh — call via asyncio.to_thread so it doesn't block the loop."""
    if not ODDS_API_CFG.api_key:
        logger.warning("[scheduler] ODDS_API_KEY not set — snapshot refresh skipped.")
        return

    client = OddsApiClient()
    try:
        fixtures = client.fetch_all_leagues_for_date(date.today())
    except OddsApiError as exc:
        logger.error("[scheduler] Odds API call failed: %s", exc)
        return

    if not fixtures:
        logger.warning("[scheduler] Odds API returned no pre-match fixtures for today.")
        return

    payload = [f.to_fixture_dict() for f in fixtures]
    fixtures_path = DATA_DIR / f"fixtures_{date.today().isoformat()}.json"
    fixtures_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("[scheduler] Wrote %d fixtures -> %s", len(fixtures), fixtures_path.name)

    snapshot = build_predictions_for_fixtures(payload)
    write_today(snapshot)
    logger.info(
        "[scheduler] Snapshot refreshed: %d predictions, %d value bets.",
        len(snapshot.predictions), len(snapshot.value_bets),
    )

    # Persist a dated copy for historical grading and regrade everything.
    try:
        from football_betting.evaluation.pipeline import (
            capture_today_snapshot,
            regrade_all,
        )

        dated_path = capture_today_snapshot()
        graded = regrade_all()
        settled = sum(1 for g in graded if g.status != "pending")
        logger.info(
            "[scheduler] Graded %d bets (%d settled) | dated snapshot -> %s",
            len(graded), settled, dated_path,
        )
    except Exception:  # noqa: BLE001 — grading failure shouldn't kill the loop
        logger.exception("[scheduler] Post-refresh grading failed.")


async def refresh_snapshot_once() -> None:
    await asyncio.to_thread(_refresh_blocking)


async def _daily_loop() -> None:
    hour = _refresh_hour_utc()
    while True:
        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        wait_s = (next_run - now).total_seconds()
        logger.info(
            "[scheduler] Next snapshot refresh at %s UTC (%.1f h)",
            next_run.isoformat(timespec="minutes"), wait_s / 3600,
        )
        await asyncio.sleep(wait_s)
        try:
            await refresh_snapshot_once()
        except Exception:  # noqa: BLE001 — loop must stay alive
            logger.exception("[scheduler] Refresh iteration failed.")


async def start(run_initial_if_missing: bool = True) -> None:
    """Install as a FastAPI startup hook."""
    if run_initial_if_missing and not snapshot_exists():
        logger.info("[scheduler] No snapshot on disk — refreshing now (background).")
        asyncio.create_task(refresh_snapshot_once())
    asyncio.create_task(_daily_loop())
