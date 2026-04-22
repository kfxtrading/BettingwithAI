"""
Dixon-Coles modified Poisson model.

Reference: Dixon & Coles (1997), "Modelling Association Football Scores
and Inefficiencies in the Football Betting Market".

Given expected goals (λ_H, λ_A), computes P(H), P(D), P(A) via 8x8 score matrix
with optional low-score correlation correction τ.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from math import exp, factorial

from football_betting.config import LEAGUES, LeagueConfig
from football_betting.data.models import Fixture, Prediction
from football_betting.features.home_advantage import (
    GHOST_PERIODS,
    dynamic_home_advantage,
)
from football_betting.rating.pi_ratings import PiRatings


@dataclass(slots=True)
class PoissonModel:
    """Poisson scorelines + Dixon-Coles τ correction."""

    pi_ratings: PiRatings
    rho: float = -0.08  # Dixon-Coles correlation parameter (typical range -0.1..0)
    max_goals: int = 8
    # COVID ghost-games correction applied to ``league.home_advantage`` when a
    # fixture date falls inside one of the configured ghost periods.
    ghost_factor: float = 0.35
    ghost_periods: Sequence[tuple[date, date]] = GHOST_PERIODS

    @staticmethod
    def _pmf(lam: float, k: int) -> float:
        """Poisson probability mass function."""
        return (lam**k) * exp(-lam) / factorial(k)

    def _tau(self, h_goals: int, a_goals: int, lam_h: float, lam_a: float) -> float:
        """
        Dixon-Coles low-score correction τ.
        Adjusts probabilities of 0-0, 0-1, 1-0, 1-1 scores.
        """
        rho = self.rho
        if h_goals == 0 and a_goals == 0:
            return 1.0 - lam_h * lam_a * rho
        if h_goals == 0 and a_goals == 1:
            return 1.0 + lam_h * rho
        if h_goals == 1 and a_goals == 0:
            return 1.0 + lam_a * rho
        if h_goals == 1 and a_goals == 1:
            return 1.0 - rho
        return 1.0

    def score_matrix(self, lam_h: float, lam_a: float) -> list[list[float]]:
        """8x8 matrix of P(score = i:j)."""
        matrix = [
            [
                self._pmf(lam_h, i) * self._pmf(lam_a, j) * self._tau(i, j, lam_h, lam_a)
                for j in range(self.max_goals)
            ]
            for i in range(self.max_goals)
        ]
        # Renormalize (τ correction can break sum-to-1)
        total = sum(sum(row) for row in matrix)
        if total > 0:
            matrix = [[p / total for p in row] for row in matrix]
        return matrix

    def probabilities(
        self,
        home_team: str,
        away_team: str,
        league: LeagueConfig,
        match_date: date | None = None,
    ) -> tuple[float, float, float, float, float]:
        """Return (P_H, P_D, P_A, λ_H, λ_A)."""
        home_adv = league.home_advantage
        if match_date is not None:
            home_adv = dynamic_home_advantage(
                match_date,
                home_adv,
                ghost_factor=self.ghost_factor,
                periods=self.ghost_periods,
            )
        lam_h, lam_a = self.pi_ratings.expected_goals(
            home_team, away_team, league.avg_goals_per_team, home_adv
        )
        lam_h = min(lam_h, 4.0)  # cap for numerical stability
        lam_a = min(lam_a, 3.5)

        matrix = self.score_matrix(lam_h, lam_a)
        p_h = sum(matrix[i][j] for i in range(self.max_goals) for j in range(i))
        p_d = sum(matrix[i][i] for i in range(self.max_goals))
        p_a = sum(matrix[i][j] for i in range(self.max_goals) for j in range(i + 1, self.max_goals))
        return p_h, p_d, p_a, lam_h, lam_a

    def predict(self, fixture: Fixture) -> Prediction:
        """Generate a single Prediction."""
        league_cfg = LEAGUES[fixture.league]
        p_h, p_d, p_a, lam_h, lam_a = self.probabilities(
            fixture.home_team, fixture.away_team, league_cfg, match_date=fixture.date
        )
        return Prediction(
            fixture=fixture,
            model_name="Poisson+PiRatings",
            prob_home=p_h,
            prob_draw=p_d,
            prob_away=p_a,
            expected_home_goals=lam_h,
            expected_away_goals=lam_a,
        )
