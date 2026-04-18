"""
Results tracker — persists predictions and actual outcomes as JSON.

Enables:
* Backtesting over historical predictions
* CLV tracking over time
* ROI / yield calculation
* RPS improvement over time
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

from football_betting.config import PREDICTIONS_DIR
from football_betting.data.models import Outcome


@dataclass(slots=True)
class PredictionRecord:
    """A single prediction persisted on disk."""

    date: str
    league: str
    home_team: str
    away_team: str
    model_name: str
    prob_home: float
    prob_draw: float
    prob_away: float
    odds_home: float | None = None
    odds_draw: float | None = None
    odds_away: float | None = None
    bet_outcome: Outcome | None = None
    bet_odds: float | None = None
    bet_stake: float | None = None
    bet_edge: float | None = None
    actual_outcome: Outcome | None = None
    actual_home_goals: int | None = None
    actual_away_goals: int | None = None
    bet_status: Literal["pending", "won", "lost", "void"] | None = None


@dataclass(slots=True)
class ResultsTracker:
    """Manages persistence of prediction records."""

    filename: str = "predictions_log.json"
    records: list[PredictionRecord] = field(default_factory=list)

    @property
    def path(self) -> Path:
        return PREDICTIONS_DIR / self.filename

    def load(self) -> None:
        if not self.path.exists():
            self.records = []
            return
        with self.path.open() as f:
            data = json.load(f)
        self.records = [PredictionRecord(**r) for r in data]

    def save(self) -> None:
        with self.path.open("w") as f:
            json.dump([asdict(r) for r in self.records], f, indent=2, default=str)

    def add(self, record: PredictionRecord) -> None:
        self.records.append(record)

    def for_date(self, target_date: date | str) -> list[PredictionRecord]:
        target = target_date.isoformat() if isinstance(target_date, date) else target_date
        return [r for r in self.records if r.date == target]

    def update_result(
        self,
        home_team: str,
        away_team: str,
        match_date: str,
        home_goals: int,
        away_goals: int,
    ) -> bool:
        """Update the actual result for a given fixture. Returns True if found."""
        if home_goals > away_goals:
            outcome: Outcome = "H"
        elif home_goals < away_goals:
            outcome = "A"
        else:
            outcome = "D"

        for rec in self.records:
            if (
                rec.home_team == home_team
                and rec.away_team == away_team
                and rec.date == match_date
            ):
                rec.actual_outcome = outcome
                rec.actual_home_goals = home_goals
                rec.actual_away_goals = away_goals
                if rec.bet_outcome is not None:
                    rec.bet_status = "won" if rec.bet_outcome == outcome else "lost"
                return True
        return False

    def completed_bets(self) -> list[PredictionRecord]:
        """Records that have both a bet AND a result."""
        return [
            r
            for r in self.records
            if r.bet_outcome is not None and r.actual_outcome is not None
        ]

    def roi_stats(self) -> dict[str, float]:
        """Aggregate staking performance."""
        completed = self.completed_bets()
        if not completed:
            return {"n_bets": 0, "roi": 0.0, "total_stake": 0.0, "total_profit": 0.0}

        total_stake = sum(r.bet_stake or 0 for r in completed)
        total_profit = 0.0
        wins = 0
        for r in completed:
            stake = r.bet_stake or 0
            if r.bet_status == "won" and r.bet_odds:
                total_profit += stake * (r.bet_odds - 1)
                wins += 1
            elif r.bet_status == "lost":
                total_profit -= stake

        return {
            "n_bets": len(completed),
            "wins": wins,
            "losses": len(completed) - wins,
            "hit_rate": wins / len(completed),
            "total_stake": total_stake,
            "total_profit": total_profit,
            "roi": total_profit / total_stake if total_stake > 0 else 0.0,
        }
