"""
Rest days between matches.

Fatigue (fewer rest days) and long breaks (international pause) both affect
match performance in measurable ways.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from football_betting.config import RestDaysConfig

if TYPE_CHECKING:
    from football_betting.data.models import Match


@dataclass(slots=True)
class RestDaysTracker:
    """Tracks last match date per team."""

    cfg: RestDaysConfig = field(default_factory=RestDaysConfig)
    last_match_date: dict[str, date] = field(default_factory=dict)

    def update(self, match: Match) -> None:
        self.last_match_date[match.home_team] = match.date
        self.last_match_date[match.away_team] = match.date

    def rest_days(self, team: str, current_date: date) -> int | None:
        """Days since team's last match. None if no prior match."""
        last = self.last_match_date.get(team)
        if last is None:
            return None
        return (current_date - last).days

    def _fatigue_score(self, days: int | None) -> float:
        """
        Map rest days to a signed fatigue score.

        * days < 4: negative (fatigued)
        * 3-7: ~0 (optimal)
        * 7-14: slightly positive (well-rested)
        * >14: negative (rusty, international break effect)
        """
        if days is None:
            return 0.0  # neutral if no prior match
        if days < self.cfg.fatigue_threshold_days:
            return -0.4 * (self.cfg.fatigue_threshold_days - days)
        if self.cfg.optimal_min_days <= days <= self.cfg.optimal_max_days:
            return 0.1  # fresh but match-sharp
        if days > self.cfg.long_break_threshold:
            return -0.2 * min(4, (days - self.cfg.long_break_threshold) / 7)
        return 0.0

    def features_for_match(
        self,
        home_team: str,
        away_team: str,
        current_date: date,
    ) -> dict[str, float]:
        h_days = self.rest_days(home_team, current_date)
        a_days = self.rest_days(away_team, current_date)

        return {
            "rest_home_days": float(h_days) if h_days is not None else -1.0,
            "rest_away_days": float(a_days) if a_days is not None else -1.0,
            "rest_home_fatigue": self._fatigue_score(h_days),
            "rest_away_fatigue": self._fatigue_score(a_days),
            "rest_diff": (
                (h_days or 0) - (a_days or 0)
                if h_days is not None and a_days is not None
                else 0.0
            ),
        }
