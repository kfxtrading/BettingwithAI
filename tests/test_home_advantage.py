"""Tests for COVID ghost-games home-advantage correction (Phase 5)."""
from __future__ import annotations

from datetime import date

import pytest

from football_betting.config import HomeAdvantageConfig
from football_betting.features.home_advantage import (
    GHOST_PERIODS,
    HomeAdvantageTracker,
    dynamic_home_advantage,
)


class TestDynamicHomeAdvantage:
    def test_ghost_period_reduces_home_advantage(self) -> None:
        base = 0.40
        corrected = dynamic_home_advantage(date(2020, 5, 1), base, ghost_factor=0.35)
        assert corrected == pytest.approx(base * 0.35)
        assert corrected < base

    def test_non_ghost_date_unchanged(self) -> None:
        base = 0.40
        assert dynamic_home_advantage(date(2019, 9, 15), base) == pytest.approx(base)
        assert dynamic_home_advantage(date(2023, 11, 1), base) == pytest.approx(base)

    def test_ghost_boundary_inclusive_inclusive(self) -> None:
        # Boundaries are inclusive on both sides per GHOST_PERIODS definition.
        base = 1.0
        start, end = GHOST_PERIODS[0]
        assert dynamic_home_advantage(start, base, ghost_factor=0.5) == pytest.approx(0.5)
        assert dynamic_home_advantage(end, base, ghost_factor=0.5) == pytest.approx(0.5)
        # One day outside on either side
        from datetime import timedelta

        assert dynamic_home_advantage(start - timedelta(days=1), base) == pytest.approx(base)
        assert dynamic_home_advantage(end + timedelta(days=1), base) == pytest.approx(base)

    def test_second_ghost_period_applied(self) -> None:
        base = 0.40
        corrected = dynamic_home_advantage(date(2021, 10, 15), base, ghost_factor=0.35)
        assert corrected == pytest.approx(base * 0.35)

    def test_custom_periods_override_defaults(self) -> None:
        base = 0.40
        custom = ((date(2024, 1, 1), date(2024, 1, 31)),)
        assert dynamic_home_advantage(
            date(2024, 1, 15), base, ghost_factor=0.5, periods=custom
        ) == pytest.approx(base * 0.5)
        # Inside default ghost period but not in custom → unchanged
        assert dynamic_home_advantage(
            date(2020, 5, 1), base, ghost_factor=0.5, periods=custom
        ) == pytest.approx(base)


class TestTrackerGhostIntegration:
    def _make_tracker(self) -> HomeAdvantageTracker:
        return HomeAdvantageTracker(cfg=HomeAdvantageConfig())

    def test_tracker_fallback_applies_ghost_factor(self) -> None:
        # No data → league-default fallback path should still be ghost-adjusted.
        tracker = self._make_tracker()
        tracker.league_of_team["TeamX"] = "PL"
        ha_normal = tracker.team_home_advantage("TeamX", match_date=date(2023, 9, 1))
        ha_ghost = tracker.team_home_advantage("TeamX", match_date=date(2020, 5, 1))
        assert ha_ghost == pytest.approx(ha_normal * tracker.cfg.ghost_factor)
        assert ha_ghost < ha_normal

    def test_tracker_no_date_unchanged(self) -> None:
        tracker = self._make_tracker()
        tracker.league_of_team["TeamX"] = "PL"
        assert tracker.team_home_advantage("TeamX") == tracker.team_home_advantage(
            "TeamX", match_date=date(2023, 9, 1)
        )

    def test_features_for_match_reduced_during_ghost(self) -> None:
        tracker = self._make_tracker()
        tracker.league_of_team["H"] = "PL"
        tracker.league_of_team["A"] = "PL"
        feats_normal = tracker.features_for_match("H", "A", match_date=date(2023, 9, 1))
        feats_ghost = tracker.features_for_match("H", "A", match_date=date(2020, 5, 1))
        assert feats_ghost["home_team_ha"] < feats_normal["home_team_ha"]


class TestPoissonGhostIntegration:
    def test_poisson_home_edge_smaller_during_ghost(self) -> None:
        from football_betting.config import LEAGUES
        from football_betting.predict.poisson import PoissonModel
        from football_betting.rating.pi_ratings import PiRatings

        model = PoissonModel(pi_ratings=PiRatings())
        p_h_normal, _, p_a_normal, _, _ = model.probabilities(
            "A", "B", LEAGUES["PL"], match_date=date(2023, 9, 1)
        )
        p_h_ghost, _, p_a_ghost, _, _ = model.probabilities(
            "A", "B", LEAGUES["PL"], match_date=date(2020, 5, 1)
        )
        # Equal ratings → home edge purely from HA. Ghost factor must shrink it.
        assert (p_h_normal - p_a_normal) > (p_h_ghost - p_a_ghost)
