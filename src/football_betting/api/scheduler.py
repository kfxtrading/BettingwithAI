"""
In-process daily snapshot refresher.

Runs alongside the FastAPI server (same event loop, no extra process),
so deployments on Railway / Docker / localhost all behave the same.

Flow on each refresh:
    Odds API -> fixtures_<today>.json -> today.json snapshot

Configuration (env vars):
    ODDS_API_KEY                     — required; without it the scheduler idles.
    SNAPSHOT_REFRESH_HOUR_UTC        — integer 0-23, default 7 (=08:00 Berlin in winter).
    LIVE_SETTLE_INTERVAL_MIN         — minutes between /scores polls, default 2.
                                       Set to 0 to disable the live-settlement loop.
    PREKICKOFF_SNAPSHOT_INTERVAL_MIN — minutes between pre-kickoff odds polls, default
                                       5. A fresh odds snapshot per league is fetched
                                       and appended to odds_<LEAGUE>.jsonl once per
                                       match, ~30 min before kickoff, so the history
                                       has line-movement info for later training.
                                       Set to 0 to disable.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import UTC, date, datetime, timedelta, timezone

from football_betting.api.services import build_predictions_for_fixtures
from football_betting.api.snapshots import load_today, snapshot_is_stale, write_today
from football_betting.config import DATA_DIR, LEAGUES, ODDS_API_CFG
from football_betting.data.models import MatchOdds
from football_betting.data.odds_snapshots import append_snapshot as append_odds_snapshot
from football_betting.scraping.odds_api import (
    OddsApiClient,
    OddsApiError,
    OddsApiQuotaError,
)

logger = logging.getLogger("football_betting.api")


# ───────────────── Quota backoff ─────────────────
# When The Odds API returns a quota-exhausted error (HTTP 401 with
# "usage"/"quota" body or HTTP 429), we pause all outbound polling
# for a configurable number of hours so we don't spam logs and
# (when the quota resets mid-pause) don't miss the recovery by
# polling too aggressively against a still-flaky key.
_quota_exhausted_until: datetime | None = None


def _quota_backoff_hours() -> int:
    raw = os.environ.get("ODDS_API_QUOTA_BACKOFF_HOURS", "16")
    try:
        return max(1, int(raw))
    except ValueError:
        logger.warning(
            "[scheduler] Invalid ODDS_API_QUOTA_BACKOFF_HOURS=%r, defaulting to 16.", raw,
        )
        return 16


def _note_quota_exhausted(source: str) -> None:
    """Record that the Odds API reported quota exhaustion."""
    global _quota_exhausted_until
    hours = _quota_backoff_hours()
    until = datetime.now(UTC) + timedelta(hours=hours)
    # Extend existing backoff rather than shorten it.
    if _quota_exhausted_until is None or until > _quota_exhausted_until:
        _quota_exhausted_until = until
    logger.error(
        "[%s] Odds API quota exhausted — pausing all Odds-API polling for %d h "
        "(until %s UTC).",
        source, hours, _quota_exhausted_until.isoformat(timespec="minutes"),
    )


def _quota_blocked() -> bool:
    """True while we are inside the active quota-exhausted backoff window."""
    global _quota_exhausted_until
    if _quota_exhausted_until is None:
        return False
    if datetime.now(UTC) >= _quota_exhausted_until:
        logger.info(
            "[scheduler] Quota backoff expired — resuming Odds-API polling.",
        )
        _quota_exhausted_until = None
        return False
    return True


def _refresh_hour_utc() -> int:
    raw = os.environ.get("SNAPSHOT_REFRESH_HOUR_UTC", "7")
    try:
        h = int(raw)
    except ValueError:
        logger.warning("[scheduler] Invalid SNAPSHOT_REFRESH_HOUR_UTC=%r, defaulting to 7.", raw)
        return 7
    return max(0, min(23, h))


def _fetch_fixtures_from_sofascore(
    today: date, tomorrow: date
) -> tuple[list[dict], date | None]:
    """Free fallback: pull fixtures (no odds) from the Sofascore widget.

    Used when the Odds API is missing/exhausted so the landing-page snapshot
    still has predictions. Odds-dependent value bets will be empty.
    """
    try:
        from football_betting.scraping.sofascore import SofascoreClient
    except Exception:  # noqa: BLE001
        logger.exception("[scheduler] Sofascore client unavailable")
        return ([], None)

    sofa = SofascoreClient()
    try:
        fixtures = sofa.fetch_all_leagues_fixtures_for_date(today)
        target = today
        if not fixtures:
            logger.info(
                "[scheduler] Sofascore: no fixtures for %s — trying %s.",
                today.isoformat(), tomorrow.isoformat(),
            )
            fixtures = sofa.fetch_all_leagues_fixtures_for_date(tomorrow)
            target = tomorrow
    except Exception:  # noqa: BLE001
        logger.exception("[scheduler] Sofascore fixture fetch failed")
        return ([], None)
    return (fixtures, target if fixtures else None)


def _refresh_blocking() -> None:
    """Sync refresh — call via asyncio.to_thread so it doesn't block the loop."""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    payload: list[dict] = []
    target_date: date | None = None
    source_tag = "odds-api"

    if not ODDS_API_CFG.api_key:
        logger.info(
            "[scheduler] ODDS_API_KEY not set — using Sofascore widget for fixtures."
        )
    elif _quota_blocked():
        logger.info(
            "[scheduler] Quota backoff active — using Sofascore widget for fixtures."
        )
    else:
        client = OddsApiClient()
        try:
            fixtures = client.fetch_all_leagues_for_date(today)
            target_date = today
            if not fixtures:
                logger.info(
                    "[scheduler] No Odds-API fixtures for %s — trying %s.",
                    today.isoformat(), tomorrow.isoformat(),
                )
                fixtures = client.fetch_all_leagues_for_date(tomorrow)
                target_date = tomorrow
            payload = [f.to_fixture_dict() for f in fixtures]
        except OddsApiQuotaError as exc:
            logger.error("[scheduler] %s", exc)
            _note_quota_exhausted("scheduler")
            payload = []
            target_date = None
        except OddsApiError as exc:
            logger.error("[scheduler] Odds API call failed: %s", exc)
            return

    if not payload:
        payload, target_date = _fetch_fixtures_from_sofascore(today, tomorrow)
        source_tag = "sofascore"

    if not payload or target_date is None:
        logger.warning(
            "[scheduler] No fixtures from any source for %s or %s.",
            today.isoformat(), tomorrow.isoformat(),
        )
        return

    fixtures_path = DATA_DIR / f"fixtures_{target_date.isoformat()}.json"
    fixtures_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(
        "[scheduler] (%s) Wrote %d fixtures -> %s",
        source_tag, len(payload), fixtures_path.name,
    )

    snapshot = build_predictions_for_fixtures(payload)
    write_today(snapshot)
    logger.info(
        "[scheduler] Snapshot refreshed: %d predictions, %d value bets.",
        len(snapshot.predictions), len(snapshot.value_bets),
    )

    # Invalidate Next.js ISR cache so users see the new snapshot immediately
    # instead of waiting up to 10 min for the fetch revalidate window.
    try:
        from football_betting.api.revalidate import revalidate_snapshot_paths

        revalidate_snapshot_paths()
    except Exception:  # noqa: BLE001 — web may be down; refresh still succeeded
        logger.exception("[scheduler] Web revalidation call failed.")

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


# Delay between a refresh and the automatic follow-up verification that
# today.json actually contains predictions for the current date. If the
# first attempt produced an empty snapshot (e.g. Odds-API hiccup, no
# fixtures returned), the verifier re-triggers the refresh. Configurable
# via env var SNAPSHOT_VERIFY_DELAY_MIN (default 30).
def _verify_delay_min() -> int:
    raw = os.environ.get("SNAPSHOT_VERIFY_DELAY_MIN", "30")
    try:
        return max(0, int(raw))
    except ValueError:
        logger.warning(
            "[scheduler] Invalid SNAPSHOT_VERIFY_DELAY_MIN=%r, defaulting to 30.", raw,
        )
        return 30


def _has_predictions_for_today() -> bool:
    """True iff today.json is present, dated today (UTC) and has predictions."""
    payload = load_today()
    if payload is None or not payload.predictions:
        return False
    generated = payload.generated_at
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    return generated.date() >= datetime.now(timezone.utc).date()


async def _verify_and_retry_after_delay() -> None:
    delay_min = _verify_delay_min()
    if delay_min <= 0:
        return
    await asyncio.sleep(delay_min * 60)
    if _has_predictions_for_today():
        logger.info(
            "[scheduler] Post-refresh verify (+%d min): today.json OK.", delay_min,
        )
        return
    logger.warning(
        "[scheduler] Post-refresh verify (+%d min): no predictions for today "
        "— re-triggering refresh.",
        delay_min,
    )
    try:
        await refresh_snapshot_once()
    except Exception:  # noqa: BLE001 — verifier must stay quiet
        logger.exception("[scheduler] Retry refresh failed.")


async def _refresh_with_verify() -> None:
    """Run a refresh and schedule a one-shot verification retry."""
    try:
        await refresh_snapshot_once()
    except Exception:  # noqa: BLE001
        logger.exception("[scheduler] Refresh iteration failed.")
    asyncio.create_task(_verify_and_retry_after_delay())


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
        await _refresh_with_verify()


def _live_settle_interval_min() -> int:
    raw = os.environ.get("LIVE_SETTLE_INTERVAL_MIN", "2")
    try:
        return max(0, int(raw))
    except ValueError:
        logger.warning("[scheduler] Invalid LIVE_SETTLE_INTERVAL_MIN=%r, defaulting to 2.", raw)
        return 2


def _live_settle_interval_active_sec() -> int:
    """Short poll cadence used while at least one match is in the live window."""
    raw = os.environ.get("LIVE_SETTLE_INTERVAL_ACTIVE_SEC", "30")
    try:
        return max(10, int(raw))
    except ValueError:
        logger.warning(
            "[scheduler] Invalid LIVE_SETTLE_INTERVAL_ACTIVE_SEC=%r, defaulting to 30.", raw,
        )
        return 30


# A match is considered in its "live display window" from shortly before
# kickoff (to surface the 0-0 initial state on the UI) until ~150 min after
# kickoff (regulation + injury + half-time). Matches outside this window
# never drive the fast poll cadence and are not force-polled.
_LIVE_WINDOW_BEFORE_MIN = 5
_LIVE_WINDOW_AFTER_MIN = 150


def _parse_iso_utc(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _live_display_league_codes() -> set[str]:
    """League *codes* of matches currently within the live display window.

    Read from today.json (already on disk — no Odds-API call). Returned as
    Odds-API sport_keys so they can be merged with ``pending_league_codes``.
    """
    payload = load_today()
    if payload is None or not payload.predictions:
        return set()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=_LIVE_WINDOW_AFTER_MIN)
    window_end = now + timedelta(minutes=_LIVE_WINDOW_BEFORE_MIN)
    codes: set[str] = set()
    for p in payload.predictions:
        ko = _parse_iso_utc(p.kickoff_utc)
        if ko is None:
            continue
        if window_start <= ko <= window_end:
            cfg = LEAGUES.get(p.league.upper())
            if cfg is not None:
                codes.add(cfg.code)
    return codes


def _settle_live_blocking() -> None:
    """Hit Odds-API /scores for leagues with pending bets or live matches and re-grade.

    While the Odds-API key is in quota backoff we transparently fall back to
    Sofascore's public scheduled-events widget so live scores keep flowing
    into the UI and pending bets still get settled on full-time.
    """
    quota_blocked = _quota_blocked()
    if not ODDS_API_CFG.api_key and not quota_blocked:
        return  # quiet — daily loop already warned at startup
    try:
        from football_betting.evaluation.pipeline import settle_live

        force = _live_display_league_codes()
        if quota_blocked:
            try:
                added, settled = settle_live(
                    force_leagues=force, use_sofascore=True,
                )
            except Exception:  # noqa: BLE001
                logger.exception("[live-settle] Sofascore fallback failed")
                return
            source_tag = "sofascore"
        else:
            try:
                added, settled = settle_live(force_leagues=force)
                source_tag = "odds-api"
            except OddsApiQuotaError as exc:
                logger.error("[live-settle] %s", exc)
                _note_quota_exhausted("live-settle")
                # Immediately retry via Sofascore so the current iteration
                # still surfaces fresh live scores to the UI.
                try:
                    added, settled = settle_live(
                        force_leagues=force, use_sofascore=True,
                    )
                    source_tag = "sofascore"
                except Exception:  # noqa: BLE001
                    logger.exception("[live-settle] Sofascore fallback failed")
                    return
        if added or settled:
            logger.info(
                "[live-settle] (%s) +%d live results, %d bet(s) newly settled.",
                source_tag, added, settled,
            )
            try:
                from football_betting.api.services import (
                    invalidate_performance_cache,
                )
                invalidate_performance_cache()
            except Exception:
                logger.exception("[live-settle] cache clear failed")
            # Kick Next.js ISR so cached SSR pages reflect the new score
            # immediately instead of waiting for the next revalidate window.
            try:
                from football_betting.api.revalidate import revalidate_snapshot_paths

                revalidate_snapshot_paths(["/[locale]"])
            except Exception:
                logger.exception("[live-settle] web revalidation failed")
    except Exception:  # noqa: BLE001
        logger.exception("[live-settle] iteration failed")


async def settle_live_once() -> None:
    await asyncio.to_thread(_settle_live_blocking)


async def _live_settle_loop() -> None:
    interval_min = _live_settle_interval_min()
    if interval_min <= 0:
        logger.info("[live-settle] disabled (LIVE_SETTLE_INTERVAL_MIN=0)")
        return
    active_s = _live_settle_interval_active_sec()
    idle_s = interval_min * 60
    logger.info(
        "[live-settle] polling /scores every %ds while matches are live, "
        "every %ds otherwise",
        active_s, idle_s,
    )
    while True:
        has_live = bool(_live_display_league_codes())
        sleep_s = active_s if has_live else idle_s
        await asyncio.sleep(sleep_s)
        try:
            await settle_live_once()
        except Exception:  # noqa: BLE001
            logger.exception("[live-settle] loop iteration failed")


# ──────────────────────── Pre-kickoff odds capture ────────────────────────

_PREKICKOFF_WINDOW_START_MIN = 25  # begin capturing this many min before kickoff
_PREKICKOFF_WINDOW_END_MIN = 35    # stop once kickoff is farther than this
_captured_prekickoff: set[tuple[str, str, str, str]] = set()


def _prekickoff_interval_min() -> int:
    raw = os.environ.get("PREKICKOFF_SNAPSHOT_INTERVAL_MIN", "5")
    try:
        return max(0, int(raw))
    except ValueError:
        logger.warning(
            "[prekickoff] Invalid PREKICKOFF_SNAPSHOT_INTERVAL_MIN=%r, defaulting to 5.",
            raw,
        )
        return 5


def _parse_kickoff_utc(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _capture_prekickoff_blocking() -> None:
    """Append a fresh odds snapshot per league with a match ~30 min from kickoff."""
    if not ODDS_API_CFG.api_key:
        return
    if _quota_blocked():
        return
    payload = load_today()
    if payload is None or not payload.predictions:
        return

    now = datetime.now(timezone.utc)
    window_start = now + timedelta(minutes=_PREKICKOFF_WINDOW_START_MIN)
    window_end = now + timedelta(minutes=_PREKICKOFF_WINDOW_END_MIN)

    due_leagues: set[str] = set()
    for p in payload.predictions:
        key = (p.league.upper(), p.date, p.home_team, p.away_team)
        if key in _captured_prekickoff:
            continue
        ko = _parse_kickoff_utc(p.kickoff_utc)
        if ko is None:
            continue
        if window_start <= ko <= window_end:
            due_leagues.add(p.league.upper())

    if not due_leagues:
        return

    client = OddsApiClient()
    today = date.today()

    for league_key in sorted(due_leagues):
        try:
            fixtures = client.fetch_for_date(league_key, today)
        except OddsApiQuotaError as exc:
            logger.error("[prekickoff] %s", exc)
            _note_quota_exhausted("prekickoff")
            return
        except OddsApiError as exc:
            logger.warning("[prekickoff] Odds API fetch failed for %s: %s", league_key, exc)
            continue

        appended = 0
        for fx in fixtures:
            odds = MatchOdds(
                home=fx.odds_home,
                draw=fx.odds_draw,
                away=fx.odds_away,
                bookmaker="avg",
            )
            append_odds_snapshot(
                league_key,
                fx.home_team,
                fx.away_team,
                fx.date.isoformat(),
                odds,
            )
            _captured_prekickoff.add(
                (league_key, fx.date.isoformat(), fx.home_team, fx.away_team)
            )
            appended += 1
        logger.info(
            "[prekickoff] %s: %d odds snapshot(s) appended.",
            league_key, appended,
        )


async def capture_prekickoff_once() -> None:
    await asyncio.to_thread(_capture_prekickoff_blocking)


async def _prekickoff_loop() -> None:
    interval_min = _prekickoff_interval_min()
    if interval_min <= 0:
        logger.info("[prekickoff] disabled (PREKICKOFF_SNAPSHOT_INTERVAL_MIN=0)")
        return
    logger.info("[prekickoff] polling fixtures every %d min", interval_min)
    interval_s = interval_min * 60
    while True:
        await asyncio.sleep(interval_s)
        try:
            await capture_prekickoff_once()
        except Exception:  # noqa: BLE001
            logger.exception("[prekickoff] loop iteration failed")


async def start(run_initial_if_stale: bool = True) -> None:
    """Install as a FastAPI startup hook."""
    if run_initial_if_stale and snapshot_is_stale(_refresh_hour_utc()):
        logger.info(
            "[scheduler] Snapshot missing or stale — refreshing now (background)."
        )
        asyncio.create_task(_refresh_with_verify())
    asyncio.create_task(_daily_loop())
    asyncio.create_task(_live_settle_loop())
    asyncio.create_task(_prekickoff_loop())
