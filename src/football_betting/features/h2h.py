"""
Head-to-Head features.

Tracks last K meetings between any pair of teams and provides features
describing the historical matchup dynamics.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from football_betting.config import H2HConfig

if TYPE_CHECKING:
    from football_betting.data.models import Match


@dataclass(slots=True)
class H2HRecord:
    """A past meeting between two teams."""

    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    date_iso: str


@dataclass(slots=True)
class H2HTracker:
    """Tracks historical meetings between any pair of teams."""

    cfg: H2HConfig = field(default_factory=H2HConfig)
    # Key: sorted (team_a, team_b) tuple → deque of meetings
    _records: dict[tuple[str, str], deque[H2HRecord]] = field(default_factory=dict)

    @staticmethod
    def _pair_key(a: str, b: str) -> tuple[str, str]:
        return tuple(sorted([a, b]))  # type: ignore[return-value]

    def update(self, match: Match) -> None:
        key = self._pair_key(match.home_team, match.away_team)
        if key not in self._records:
            self._records[key] = deque(maxlen=30)

        self._records[key].append(
            H2HRecord(
                home_team=match.home_team,
                away_team=match.away_team,
                home_goals=match.home_goals,
                away_goals=match.away_goals,
                date_iso=match.date.isoformat(),
            )
        )

    def get_history(self, home_team: str, away_team: str) -> list[H2HRecord]:
        key = self._pair_key(home_team, away_team)
        if key not in self._records:
            return []
        return list(self._records[key])[-self.cfg.max_games:]

    def features_for_match(self, home_team: str, away_team: str) -> dict[str, float]:
        recs = self.get_history(home_team, away_team)
        if not recs:
            return {
                "h2h_n_meetings": 0.0,
                "h2h_home_wins": 0.0,
                "h2h_draws": 0.0,
                "h2h_away_wins": 0.0,
                "h2h_avg_goals": 0.0,
                "h2h_home_goal_rate": 0.0,
                "h2h_away_goal_rate": 0.0,
                "h2h_home_team_winrate": 0.0,
            }

        n = len(recs)
        # From *current* home team's perspective (who might have been home or away historically)
        home_team_wins = 0
        draws = 0
        away_team_wins = 0
        home_goals_total = 0.0  # in role of current home team
        away_goals_total = 0.0

        for rec in recs:
            if rec.home_team == home_team:
                # Matches where current home team played at home
                home_in_match = rec.home_goals
                away_in_match = rec.away_goals
            else:
                # Matches where current home team was the away side
                home_in_match = rec.away_goals
                away_in_match = rec.home_goals

            home_goals_total += home_in_match
            away_goals_total += away_in_match

            if home_in_match > away_in_match:
                home_team_wins += 1
            elif home_in_match < away_in_match:
                away_team_wins += 1
            else:
                draws += 1

        avg_goals = (home_goals_total + away_goals_total) / n

        return {
            "h2h_n_meetings": float(n),
            "h2h_home_wins": home_team_wins / n,
            "h2h_draws": draws / n,
            "h2h_away_wins": away_team_wins / n,
            "h2h_avg_goals": avg_goals,
            "h2h_home_goal_rate": home_goals_total / n,
            "h2h_away_goal_rate": away_goals_total / n,
            "h2h_home_team_winrate": home_team_wins / n,
        }
