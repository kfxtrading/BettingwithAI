"""Tests for Poisson prediction model."""
from __future__ import annotations

import pytest

from football_betting.predict.poisson import PoissonModel
from football_betting.rating.pi_ratings import PiRatings


class TestPoissonModel:
    def test_pmf_known_values(self) -> None:
        assert PoissonModel._pmf(1.0, 0) == pytest.approx(0.3679, abs=1e-3)
        assert PoissonModel._pmf(2.0, 2) == pytest.approx(0.2707, abs=1e-3)

    def test_score_matrix_sums_to_one(self) -> None:
        model = PoissonModel(pi_ratings=PiRatings())
        matrix = model.score_matrix(1.5, 1.2)
        total = sum(sum(row) for row in matrix)
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_probabilities_sum_to_one(self) -> None:
        from football_betting.config import LEAGUES

        pi = PiRatings()
        model = PoissonModel(pi_ratings=pi)
        p_h, p_d, p_a, _, _ = model.probabilities("A", "B", LEAGUES["PL"])
        assert p_h + p_d + p_a == pytest.approx(1.0, abs=1e-6)
        assert all(p >= 0 for p in (p_h, p_d, p_a))

    def test_home_advantage_gives_home_edge(self) -> None:
        from football_betting.config import LEAGUES

        pi = PiRatings()  # equal ratings
        model = PoissonModel(pi_ratings=pi)
        p_h, p_d, p_a, _, _ = model.probabilities("A", "B", LEAGUES["PL"])
        # With equal ratings, home advantage alone should give home > away
        assert p_h > p_a

    def test_dc_correction_affects_low_scores(self) -> None:
        m_with = PoissonModel(pi_ratings=PiRatings(), rho=-0.08)
        m_without = PoissonModel(pi_ratings=PiRatings(), rho=0.0)

        # τ should affect 0-0, 1-0, 0-1, 1-1 boxes
        m_with_pmf = m_with.score_matrix(1.2, 1.0)
        m_without_pmf = m_without.score_matrix(1.2, 1.0)

        # 1-1 boxes should differ
        assert m_with_pmf[1][1] != m_without_pmf[1][1]
        # High-score boxes should be essentially identical
        assert m_with_pmf[4][4] == pytest.approx(m_without_pmf[4][4], abs=1e-6)
