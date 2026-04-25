"""Daily grading pipeline.

Run ``python -m football_betting.evaluation.pipeline`` to:

1. Capture today's TodayPayload into ``data/snapshots/YYYY-MM-DD.json`` so
   historical grading can find the bets later.
2. Walk every dated snapshot in ``data/snapshots/`` and re-grade every value
   bet against the current football-data CSV archive.
3. Rewrite ``data/graded_bets.jsonl`` with the full history (append-only from
   the consumer's perspective; atomic on disk).
"""
from __future__ import annotations

import logging
from datetime import date

from football_betting.api.schemas import ValueBetOut
from football_betting.api.services import get_today_payload
from football_betting.config import SNAPSHOT_DIR
from football_betting.evaluation.grader import (
    GradedBet,
    grade_bets,
    iter_historical_snapshots,
    prediction_to_tracked_bet,
    write_graded,
)

logger = logging.getLogger(__name__)


def capture_today_snapshot() -> str:
    """Write today's payload to ``SNAPSHOT_DIR/YYYY-MM-DD.json`` (dated, keep)."""
    payload = get_today_payload()
    today = date.today().isoformat()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"{today}.json"
    path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return str(path)


def settle_live(
    days_from: int = 3,
    *,
    force_leagues: set[str] | frozenset[str] | None = None,
) -> tuple[int, int]:
    """Poll the configured result source for leagues with pending bets, re-grade.

    Returns (n_new_live_rows, n_bets_settled_delta).

    Polls the union of:
      * ``pending_league_codes()`` — leagues with still-pending bets that need
        authoritative final-score grading, and
      * ``force_leagues`` — extra league *codes* whose matches must surface
        fresh live scores in the UI even when no bet is pending yet.

    ``regrade_all()`` only runs when there is at least one pending bet; pure
    display-driven polls skip the (expensive) regrade pass.
    """
    from football_betting.config import live_score_source
    from football_betting.evaluation.live_results import (
        pending_league_codes,
        poll_and_store_scores,
        poll_and_store_scores_football_data,
    )

    pending = pending_league_codes()
    forced = set(force_leagues) if force_leagues else set()
    codes = pending | forced
    if not codes:
        logger.debug("[live] No pending bets and no forced leagues — skipping live poll")
        return (0, 0)

    before_pending = (
        len([g for g in _load_current_graded() if g.status == "pending"]) if pending else 0
    )
    source = live_score_source()
    if source == "football_data":
        added = poll_and_store_scores_football_data(codes, days_from=days_from)
    else:
        added = poll_and_store_scores(codes, days_from=days_from)
    if pending:
        regrade_all()
        after_pending = len([g for g in _load_current_graded() if g.status == "pending"])
        settled = max(0, before_pending - after_pending)
    else:
        settled = 0
    if settled or added:
        logger.info("[live] Settled %d bets (added %d live rows)", settled, added)
    return (added, settled)


def _load_current_graded() -> list[GradedBet]:
    from football_betting.evaluation.grader import load_graded

    return load_graded()


def regrade_all() -> list[GradedBet]:
    # A match can appear in multiple daily snapshots until kickoff; dedupe
    # by (match_date, league, home, away, outcome) so each bet is graded
    # exactly once. Iteration is sorted by snapshot date ascending, so later
    # (more recent) snapshots overwrite earlier ones — giving us the freshest
    # odds/stake for each unique bet.
    #
    # Two maps: value bets and most-likely predictions are tracked
    # independently. When both strategies agree on the same outcome for a
    # match we still keep both rows so each strategy is represented in the
    # "Letzte Wetten" history.
    value_map: dict[tuple[str, str, str, str, str], ValueBetOut] = {}
    pred_map: dict[tuple[str, str, str, str, str], ValueBetOut] = {}
    for _snap_date, payload in iter_historical_snapshots():
        for bet in payload.value_bets or []:
            key = (
                bet.date,
                bet.league,
                bet.home_team.lower().strip(),
                bet.away_team.lower().strip(),
                bet.outcome,
            )
            value_map[key] = bet
        for pred in payload.predictions or []:
            tracked = prediction_to_tracked_bet(pred)
            if tracked is None:
                continue
            key = (
                tracked.date,
                tracked.league,
                tracked.home_team.lower().strip(),
                tracked.away_team.lower().strip(),
                tracked.outcome,
            )
            pred_map[key] = tracked
    graded = grade_bets(value_map.values(), kind="value") + grade_bets(
        pred_map.values(), kind="prediction"
    )
    write_graded(graded)
    _refresh_performance_artifacts()
    return graded


def _refresh_performance_artifacts() -> None:
    """Regenerate ``performance.json`` / ``performance_full.json`` and bust
    the in-memory cache so ``/performance/*`` endpoints reflect the freshly
    graded bets immediately."""
    try:
        from football_betting.tracking.performance_index import write_performance_files

        write_performance_files()
    except Exception:
        logger.exception("[pipeline] Failed to refresh performance artefacts")
        return
    try:
        from football_betting.api.services import invalidate_performance_cache

        invalidate_performance_cache()
    except Exception:
        logger.exception("[pipeline] Failed to clear performance cache")


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-5s | %(message)s")
    path = capture_today_snapshot()
    logger.info("Captured today snapshot: %s", path)
    graded = regrade_all()
    won = sum(1 for g in graded if g.status == "won")
    lost = sum(1 for g in graded if g.status == "lost")
    pending = sum(1 for g in graded if g.status == "pending")
    pnl = round(sum(g.pnl for g in graded), 2)
    logger.info("Graded %d bets: %d won, %d lost, %d pending (P&L %+.2f)",
                len(graded), won, lost, pending, pnl)


if __name__ == "__main__":
    run()
