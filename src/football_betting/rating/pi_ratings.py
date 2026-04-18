"""
Pi-Ratings based on Constantinou & Fenton (2013):
"Determining the level of ability of football teams by dynamic ratings
 based on the relative discrepancies in scores between adjacent divisions".

Each team has two ratings:
  * R_H: home rating (strength when playing at home)
  * R_A: away rating (strength when playing away)

After each match, ratings are updated iteratively based on the error
between expected and actual goal difference.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from football_betting.config import PI_CFG, PiRatingsConfig

if TYPE_CHECKING:
    from football_betting.data.models import Match


@dataclass(slots=True)
class TeamRating:
    """Pi-rating for one team."""

    home: float = 0.0
    away: float = 0.0

    @property
    def overall(self) -> float:
        """Simple average of home + away rating."""
        return (self.home + self.away) / 2


@dataclass(slots=True)
class PiRatings:
    """Iterative pi-ratings tracker for all teams in a league."""

    cfg: PiRatingsConfig = field(default_factory=lambda: PI_CFG)
    ratings: dict[str, TeamRating] = field(default_factory=lambda: defaultdict(TeamRating))
    history: list[dict[str, float]] = field(default_factory=list)

    # ───────────────────────── Core transforms ─────────────────────────

    def _diff_from_rating(self, rating_diff: float) -> float:
        """
        Convert rating difference to expected goal difference (bounded logistic).

        Formula from the paper:
            ψ(x) = (10^(|x|/c) - 1) / (10^(|x|/c) + 1), sign preserved
        with scale c = 3 → bounded in (-1, 1), then multiplied by 3 for goals.
        """
        sign = 1 if rating_diff >= 0 else -1
        abs_rd = abs(rating_diff)
        logistic = (10 ** (abs_rd / self.cfg.diff_scale) - 1) / (
            10 ** (abs_rd / self.cfg.diff_scale) + 1
        )
        return sign * logistic * 3.0  # scale to roughly ±3 goals max

    def _rating_from_diff(self, goal_diff: float) -> float:
        """Inverse transform: goal difference → rating delta."""
        normalized = max(-0.999, min(0.999, goal_diff / 3.0))
        sign = 1 if normalized >= 0 else -1
        abs_n = abs(normalized)
        return sign * self.cfg.diff_scale * math.log10((1 + abs_n) / (1 - abs_n))

    # ───────────────────────── Prediction ─────────────────────────

    def expected_goal_diff(self, home_team: str, away_team: str) -> float:
        """Predicted goal difference in favor of home team."""
        home_rating = self.ratings[home_team].home
        away_rating = self.ratings[away_team].away
        return self._diff_from_rating(home_rating - away_rating)

    def expected_goals(
        self,
        home_team: str,
        away_team: str,
        league_avg: float,
        home_advantage: float,
    ) -> tuple[float, float]:
        """
        Predicted (home_xG, away_xG) based on pi-ratings.

        Simple translation: expected GD is split around league mean,
        with home advantage already folded into the rating system.
        """
        gd = self.expected_goal_diff(home_team, away_team) + home_advantage
        # Balance around league mean
        home_xg = max(0.2, league_avg + gd / 2)
        away_xg = max(0.2, league_avg - gd / 2)
        return home_xg, away_xg

    # ───────────────────────── Update step ─────────────────────────

    def update(self, match: Match) -> None:
        """Process one match and update all 4 ratings (2 teams × home/away)."""
        home_team = match.home_team
        away_team = match.away_team

        home_rating = self.ratings[home_team]
        away_rating = self.ratings[away_team]

        # Predict and compute error
        expected_diff = self._diff_from_rating(home_rating.home - away_rating.away)
        actual_diff = float(match.goal_diff)
        error = actual_diff - expected_diff

        lam = self.cfg.learning_rate
        gam = self.cfg.cross_venue_weight

        # Home team: larger update on home rating, smaller cross-update on away
        home_rating.home += lam * error
        home_rating.away += lam * gam * error

        # Away team: opposite sign; mirror updates
        away_rating.away -= lam * error
        away_rating.home -= lam * gam * error

    def fit(self, matches: list[Match]) -> None:
        """Process matches in chronological order."""
        matches_sorted = sorted(matches, key=lambda m: m.date)
        for m in matches_sorted:
            self.update(m)
            self.history.append(
                {
                    team: r.overall
                    for team, r in self.ratings.items()
                }
            )

    # ───────────────────────── Access & features ─────────────────────────

    def get(self, team: str) -> TeamRating:
        return self.ratings[team]

    def features_for_match(self, home_team: str, away_team: str) -> dict[str, float]:
        """Feature vector used by the CatBoost downstream model."""
        h = self.ratings[home_team]
        a = self.ratings[away_team]
        return {
            "pi_home_H": h.home,
            "pi_home_A": h.away,
            "pi_home_overall": h.overall,
            "pi_away_H": a.home,
            "pi_away_A": a.away,
            "pi_away_overall": a.overall,
            "pi_diff_H_vs_A": h.home - a.away,
            "pi_diff_overall": h.overall - a.overall,
            "pi_expected_gd": self.expected_goal_diff(home_team, away_team),
        }

    def top_n(self, n: int = 10) -> list[tuple[str, TeamRating]]:
        """Return top-N teams by overall rating."""
        return sorted(
            self.ratings.items(),
            key=lambda kv: kv[1].overall,
            reverse=True,
        )[:n]

    def reset(self) -> None:
        self.ratings.clear()
        self.history.clear()
