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

import json
import logging
from datetime import date

from football_betting.api.services import get_today_payload
from football_betting.config import SNAPSHOT_DIR
from football_betting.evaluation.grader import (
    GradedBet,
    grade_bets,
    iter_historical_snapshots,
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


def regrade_all() -> list[GradedBet]:
    graded: list[GradedBet] = []
    for snap_date, payload in iter_historical_snapshots():
        if not payload.value_bets:
            continue
        graded.extend(grade_bets(payload.value_bets))
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
        from football_betting.api.cache import cache

        cache.clear()
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
