"""
Exponentially-weighted rolling form features.

For each team, tracks recent match outcomes and goal statistics with
exponential decay (most recent matches weighted highest). Separate
home/away form allows teams with strong home records but weak away form
to be properly modeled.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from football_betting.config import FormConfig

if TYPE_CHECKING:
    from football_betting.data.models import Match


@dataclass(slots=True)
class MatchRecord:
    """Single match record from team's perspective."""

    goals_scored: int
    goals_conceded: int
    was_home: bool
    result: str  # "W" | "D" | "L"
    shots: int | None = None
    shots_on_target: int | None = None


@dataclass(slots=True)
class FormTracker:
    """Tracks per-team recent form with exponential decay."""

    cfg: FormConfig = field(default_factory=FormConfig)
    history: dict[str, deque[MatchRecord]] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=50))
    )

    # ───────────────────────── Update ─────────────────────────

    def update(self, match: Match) -> None:
        """Add match to both teams' history."""
        h_goals = match.home_goals
        a_goals = match.away_goals

        # Home team's perspective
        self.history[match.home_team].append(
            MatchRecord(
                goals_scored=h_goals,
                goals_conceded=a_goals,
                was_home=True,
                result=self._result_for(h_goals, a_goals),
                shots=match.home_shots,
                shots_on_target=match.home_shots_on_target,
            )
        )
        # Away team's perspective
        self.history[match.away_team].append(
            MatchRecord(
                goals_scored=a_goals,
                goals_conceded=h_goals,
                was_home=False,
                result=self._result_for(a_goals, h_goals),
                shots=match.away_shots,
                shots_on_target=match.away_shots_on_target,
            )
        )

    @staticmethod
    def _result_for(scored: int, conceded: int) -> str:
        if scored > conceded:
            return "W"
        if scored < conceded:
            return "L"
        return "D"

    # ───────────────────────── Weighted aggregates ─────────────────────────

    def _weighted_stats(
        self,
        records: list[MatchRecord],
    ) -> dict[str, float]:
        """Compute exponentially-weighted averages of key metrics."""
        if not records:
            return self._empty_stats()

        # Newest match has weight 1.0, older matches decayed
        weights = [self.cfg.decay_rate**i for i in range(len(records))][::-1]
        total_w = sum(weights)

        def wavg(getter) -> float:
            return sum(w * getter(r) for w, r in zip(weights, records)) / total_w

        wins = wavg(lambda r: 1.0 if r.result == "W" else 0.0)
        draws = wavg(lambda r: 1.0 if r.result == "D" else 0.0)
        losses = wavg(lambda r: 1.0 if r.result == "L" else 0.0)
        goals_for = wavg(lambda r: float(r.goals_scored))
        goals_against = wavg(lambda r: float(r.goals_conceded))

        # Points per game (weighted)
        ppg = 3.0 * wins + 1.0 * draws

        # Form score: rolling "trend" — positive if recent > older
        if len(records) >= 4:
            recent = records[-3:]
            older = records[:-3]
            recent_ppg = sum(3 if r.result == "W" else 1 if r.result == "D" else 0 for r in recent) / len(recent)
            older_ppg = (
                sum(3 if r.result == "W" else 1 if r.result == "D" else 0 for r in older) / len(older)
            )
            form_trend = recent_ppg - older_ppg
        else:
            form_trend = 0.0

        return {
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_diff": goals_for - goals_against,
            "ppg": ppg,
            "form_trend": form_trend,
        }

    @staticmethod
    def _empty_stats() -> dict[str, float]:
        return {
            "wins": 0.0,
            "draws": 0.0,
            "losses": 0.0,
            "goals_for": 0.0,
            "goals_against": 0.0,
            "goal_diff": 0.0,
            "ppg": 0.0,
            "form_trend": 0.0,
        }

    # ───────────────────────── Public queries ─────────────────────────

    def overall_form(self, team: str) -> dict[str, float]:
        """All recent matches combined."""
        recs = list(self.history.get(team, []))[-self.cfg.window_size:]
        return self._weighted_stats(recs)

    def home_form(self, team: str) -> dict[str, float]:
        """Recent home matches only."""
        recs = [r for r in self.history.get(team, []) if r.was_home][-self.cfg.window_size:]
        return self._weighted_stats(recs)

    def away_form(self, team: str) -> dict[str, float]:
        """Recent away matches only."""
        recs = [r for r in self.history.get(team, []) if not r.was_home][-self.cfg.window_size:]
        return self._weighted_stats(recs)

    def features_for_match(self, home_team: str, away_team: str) -> dict[str, float]:
        """Flat feature dict for match between home and away."""
        h_overall = self.overall_form(home_team)
        h_home = self.home_form(home_team)
        a_overall = self.overall_form(away_team)
        a_away = self.away_form(away_team)

        return {
            # Home team's overall form
            "form_home_ppg": h_overall["ppg"],
            "form_home_gf": h_overall["goals_for"],
            "form_home_ga": h_overall["goals_against"],
            "form_home_trend": h_overall["form_trend"],
            # Home team's home-specific form
            "form_home_at_home_ppg": h_home["ppg"],
            "form_home_at_home_gf": h_home["goals_for"],
            # Away team's overall form
            "form_away_ppg": a_overall["ppg"],
            "form_away_gf": a_overall["goals_for"],
            "form_away_ga": a_overall["goals_against"],
            "form_away_trend": a_overall["form_trend"],
            # Away team's away-specific form
            "form_away_at_away_ppg": a_away["ppg"],
            "form_away_at_away_gf": a_away["goals_for"],
            # Derived differentials
            "form_ppg_diff": h_overall["ppg"] - a_overall["ppg"],
            "form_gd_diff": h_overall["goal_diff"] - a_overall["goal_diff"],
        }

    def games_played(self, team: str) -> int:
        return len(self.history.get(team, []))

    def get_recent(self, team: str, n: int = 10) -> list[MatchRecord]:
        """Return up to ``n`` most recent match records for ``team``.

        v0.4 — consumed by ``MatchSequenceModel``. Leakage-safe because the
        tracker is only updated AFTER each match's features are extracted.
        """
        records = list(self.history.get(team, []))
        return records[-n:] if n > 0 else records
