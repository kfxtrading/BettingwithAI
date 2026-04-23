"""Tests for SeasonStandingsTracker."""
from __future__ import annotations

from datetime import date

from football_betting.data.models import Match
from football_betting.features.standings import SeasonStandingsTracker


def _m(
    home: str,
    away: str,
    hg: int,
    ag: int,
    day: int = 1,
    league: str = "PL",
    season: str = "2024-25",
) -> Match:
    return Match(
        date=date(2025, 1, day),
        league=league,
        season=season,
        home_team=home,
        away_team=away,
        home_goals=hg,
        away_goals=ag,
    )


class TestStandingsTracker:
    def test_empty_returns_zeros(self) -> None:
        t = SeasonStandingsTracker()
        feats = t.features_for_match("A", "B", "PL", "2024-25")
        assert feats["standings_home_pts"] == 0.0
        assert feats["standings_away_pts"] == 0.0
        assert feats["standings_matchday_pct"] == 0.0

    def test_no_season_returns_empty(self) -> None:
        t = SeasonStandingsTracker()
        feats = t.features_for_match("A", "B", "PL", None)
        assert feats["standings_home_pts"] == 0.0

    def test_home_win_awards_three_points(self) -> None:
        t = SeasonStandingsTracker()
        t.update(_m("A", "B", 3, 0))
        feats = t.features_for_match("A", "C", "PL", "2024-25")
        assert feats["standings_home_pts"] == 3.0
        assert feats["standings_home_gd"] == 3.0
        assert feats["standings_home_ppg"] == 3.0
        assert feats["standings_home_home_ppg"] == 3.0

    def test_draw_awards_one_each(self) -> None:
        t = SeasonStandingsTracker()
        t.update(_m("A", "B", 1, 1))
        fa = t.features_for_match("A", "X", "PL", "2024-25")
        fb = t.features_for_match("B", "Y", "PL", "2024-25")
        assert fa["standings_home_pts"] == 1.0
        assert fb["standings_home_pts"] == 1.0

    def test_season_isolation(self) -> None:
        t = SeasonStandingsTracker()
        t.update(_m("A", "B", 3, 0, season="2023-24"))
        feats = t.features_for_match("A", "C", "PL", "2024-25")
        assert feats["standings_home_pts"] == 0.0

    def test_league_isolation(self) -> None:
        t = SeasonStandingsTracker()
        t.update(_m("A", "B", 3, 0, league="PL"))
        feats = t.features_for_match("A", "C", "BL", "2024-25")
        assert feats["standings_home_pts"] == 0.0

    def test_rank_assigned(self) -> None:
        t = SeasonStandingsTracker()
        t.update(_m("A", "B", 3, 0, day=1))
        t.update(_m("C", "D", 1, 1, day=2))
        feats = t.features_for_match("A", "C", "PL", "2024-25")
        # A has 3 pts → rank 1; C has 1 pt → rank 2 or 3
        assert feats["standings_home_rank"] == 1.0
        assert feats["standings_away_rank"] >= 2.0

    def test_pts_and_gd_diff(self) -> None:
        t = SeasonStandingsTracker()
        t.update(_m("A", "Z", 3, 0, day=1))  # A: 3 pts, GD +3
        t.update(_m("B", "Z", 0, 1, day=2))  # B: 0 pts, GD -1
        feats = t.features_for_match("A", "B", "PL", "2024-25")
        assert feats["standings_pts_diff"] == 3.0
        assert feats["standings_gd_diff"] == 4.0

    def test_matchday_pct_progresses(self) -> None:
        t = SeasonStandingsTracker()
        # Simulate 19 matchdays (50% of 38)
        for i in range(19):
            t.update(_m("A", f"T{i}", 1, 0, day=i + 1))
        feats = t.features_for_match("A", "B", "PL", "2024-25")
        assert 0.45 < feats["standings_matchday_pct"] < 0.55
        assert feats["standings_is_late_season"] == 0.0

    def test_late_season_flag(self) -> None:
        t = SeasonStandingsTracker()
        for i in range(30):
            t.update(_m("A", f"T{i}", 1, 0, day=i + 1))
        feats = t.features_for_match("A", "B", "PL", "2024-25")
        assert feats["standings_is_late_season"] == 1.0

    def test_home_vs_away_ppg_split(self) -> None:
        t = SeasonStandingsTracker()
        t.update(_m("A", "B", 3, 0, day=1))  # A home win
        t.update(_m("C", "A", 2, 0, day=2))  # A lost away
        feats = t.features_for_match("A", "X", "PL", "2024-25")
        assert feats["standings_home_home_ppg"] == 3.0
        # A played away once (lost) → away_ppg = 0
        feats2 = t.features_for_match("X", "A", "PL", "2024-25")
        assert feats2["standings_away_away_ppg"] == 0.0

    def test_reset_clears_all(self) -> None:
        t = SeasonStandingsTracker()
        t.update(_m("A", "B", 3, 0))
        t.reset()
        feats = t.features_for_match("A", "C", "PL", "2024-25")
        assert feats["standings_home_pts"] == 0.0
