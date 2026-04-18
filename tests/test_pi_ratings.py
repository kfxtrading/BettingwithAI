"""Tests for pi-ratings module."""
from __future__ import annotations

from datetime import date

import pytest

from football_betting.data.models import Match
from football_betting.rating.pi_ratings import PiRatings, TeamRating


def _match(home: str, away: str, hg: int, ag: int, day: int = 1) -> Match:
    return Match(
        date=date(2025, 1, day),
        league="PL",
        season="2024-25",
        home_team=home,
        away_team=away,
        home_goals=hg,
        away_goals=ag,
    )


class TestPiRatings:
    def test_initial_rating_is_zero(self) -> None:
        r = PiRatings()
        assert r.get("any_team").home == 0.0
        assert r.get("any_team").away == 0.0

    def test_diff_symmetric_around_zero(self) -> None:
        r = PiRatings()
        assert r._diff_from_rating(0.0) == pytest.approx(0.0)
        pos = r._diff_from_rating(1.0)
        neg = r._diff_from_rating(-1.0)
        assert pos > 0
        assert neg < 0
        assert pos == pytest.approx(-neg)

    def test_inverse_transform_roundtrip(self) -> None:
        r = PiRatings()
        for gd in (0.5, 1.0, 1.5, 2.0, -1.0, -2.5):
            rating = r._rating_from_diff(gd)
            back = r._diff_from_rating(rating)
            assert back == pytest.approx(gd, abs=0.05)

    def test_home_win_boosts_home_rating(self) -> None:
        r = PiRatings()
        r.update(_match("A", "B", 3, 0))
        assert r.get("A").home > 0
        assert r.get("B").away < 0

    def test_cross_venue_update_smaller(self) -> None:
        """Cross-venue update should be smaller than primary update."""
        r = PiRatings()
        r.update(_match("A", "B", 3, 0))
        a = r.get("A")
        # Home update should be > away update for home team
        assert abs(a.home) > abs(a.away)
        # Ratio should equal cross_venue_weight
        assert a.away / a.home == pytest.approx(r.cfg.cross_venue_weight)

    def test_draw_leaves_ratings_near_expected(self) -> None:
        """After many draws, equal teams should have similar ratings."""
        r = PiRatings()
        for i in range(20):
            r.update(_match("A", "B", 1, 1, day=i + 1))
        # Ratings should have stabilized
        a = r.get("A")
        b = r.get("B")
        # Home advantage means home team of repeated match gets slight edge
        # but both should be in small range
        assert abs(a.overall) < 1.0
        assert abs(b.overall) < 1.0

    def test_expected_goals_sensible(self) -> None:
        r = PiRatings()
        # Make team A dominant
        for i in range(10):
            r.update(_match("A", "B", 3, 0, day=i + 1))

        h_xg, a_xg = r.expected_goals("A", "B", league_avg=1.4, home_advantage=0.35)
        assert h_xg > a_xg
        assert h_xg > 1.4  # above league avg
        assert a_xg > 0.2  # floored

    def test_features_for_match_keys(self) -> None:
        r = PiRatings()
        r.update(_match("A", "B", 2, 1))
        feats = r.features_for_match("A", "B")

        required = {
            "pi_home_H", "pi_home_A", "pi_home_overall",
            "pi_away_H", "pi_away_A", "pi_away_overall",
            "pi_diff_H_vs_A", "pi_diff_overall", "pi_expected_gd",
        }
        assert required.issubset(feats.keys())

    def test_fit_many_matches(self) -> None:
        r = PiRatings()
        matches = [
            _match("A", "B", 2, 0, day=1),
            _match("B", "C", 1, 1, day=2),
            _match("C", "A", 0, 2, day=3),
            _match("A", "C", 3, 0, day=4),
            _match("B", "A", 0, 2, day=5),
        ]
        r.fit(matches)
        # A wins all 4 of its matches, should be top
        top = r.top_n(3)
        assert top[0][0] == "A"
        assert len(r.history) == 5

    def test_reset(self) -> None:
        r = PiRatings()
        r.update(_match("A", "B", 3, 0))
        assert r.get("A").home != 0
        r.reset()
        assert len(r.ratings) == 0
