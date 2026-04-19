"""SEO-facing track-record helpers.

Builds two derived artefacts from the persisted ResultsTracker records:

* a downloadable CSV of historical predictions vs results, and
* probability-bin calibration buckets (predicted vs actual frequency).

Both are designed to be safe on missing data — empty input yields empty
output rather than raising.
"""
from __future__ import annotations

import csv
import io
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from football_betting.tracking.tracker import PredictionRecord, ResultsTracker


CSV_HEADER = [
    "date",
    "league",
    "home_team",
    "away_team",
    "model_name",
    "prob_home",
    "prob_draw",
    "prob_away",
    "predicted_outcome",
    "actual_outcome",
    "actual_home_goals",
    "actual_away_goals",
    "bet_outcome",
    "bet_odds",
    "bet_stake",
    "bet_status",
    "correct",
]


def _predicted_outcome(rec: PredictionRecord) -> str:
    """The argmax of the model probabilities."""
    probs = (rec.prob_home, rec.prob_draw, rec.prob_away)
    idx = max(range(3), key=lambda i: probs[i])
    return ("H", "D", "A")[idx]


def _correct_flag(rec: PredictionRecord) -> str:
    if rec.actual_outcome is None:
        return ""
    return "1" if _predicted_outcome(rec) == rec.actual_outcome else "0"


def build_csv(records: Iterable[PredictionRecord]) -> str:
    """Render predictions vs results as a UTF-8 CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CSV_HEADER)
    for rec in records:
        writer.writerow([
            rec.date,
            rec.league,
            rec.home_team,
            rec.away_team,
            rec.model_name,
            f"{rec.prob_home:.4f}",
            f"{rec.prob_draw:.4f}",
            f"{rec.prob_away:.4f}",
            _predicted_outcome(rec),
            rec.actual_outcome or "",
            "" if rec.actual_home_goals is None else rec.actual_home_goals,
            "" if rec.actual_away_goals is None else rec.actual_away_goals,
            rec.bet_outcome or "",
            "" if rec.bet_odds is None else f"{rec.bet_odds:.3f}",
            "" if rec.bet_stake is None else f"{rec.bet_stake:.4f}",
            rec.bet_status or "",
            _correct_flag(rec),
        ])
    return buf.getvalue()


@dataclass(slots=True)
class CalibrationBucket:
    bin_lower: float
    bin_upper: float
    n: int
    predicted_mean: float
    actual_rate: float


def build_calibration(
    records: Iterable[PredictionRecord],
    n_bins: int = 10,
    league: str | None = None,
) -> list[CalibrationBucket]:
    """Bin (predicted_prob, hit) pairs across all 3 outcomes per match.

    For every settled match we emit three samples (one per outcome) where the
    target is 1 if that outcome happened. This is the standard reliability
    diagram input.
    """
    if n_bins <= 0:
        raise ValueError("n_bins must be > 0")

    width = 1.0 / n_bins
    sums: dict[int, list[float]] = defaultdict(list)
    hits: dict[int, list[int]] = defaultdict(list)

    for rec in records:
        if rec.actual_outcome is None:
            continue
        if league and rec.league.upper() != league.upper():
            continue
        outcomes = (
            ("H", rec.prob_home),
            ("D", rec.prob_draw),
            ("A", rec.prob_away),
        )
        for outcome, prob in outcomes:
            if prob < 0 or prob > 1:
                continue
            bucket = min(int(prob / width), n_bins - 1)
            sums[bucket].append(prob)
            hits[bucket].append(1 if outcome == rec.actual_outcome else 0)

    buckets: list[CalibrationBucket] = []
    for i in range(n_bins):
        ps = sums.get(i, [])
        hs = hits.get(i, [])
        if not ps:
            continue
        buckets.append(
            CalibrationBucket(
                bin_lower=round(i * width, 4),
                bin_upper=round((i + 1) * width, 4),
                n=len(ps),
                predicted_mean=round(sum(ps) / len(ps), 4),
                actual_rate=round(sum(hs) / len(hs), 4),
            )
        )
    return buckets


def load_records() -> list[PredictionRecord]:
    """Best-effort load of the default predictions log."""
    tracker = ResultsTracker()
    try:
        tracker.load()
    except Exception:  # noqa: BLE001 - SEO endpoints must never 500
        return []
    return list(tracker.records)
