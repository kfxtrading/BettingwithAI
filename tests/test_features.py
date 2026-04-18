"""Tests for v0.2 feature engineering modules."""
from __future__ import annotations

from datetime import date

import pytest

from football_betting.data.models import Match
from football_betting.features.builder import FeatureBuilder
from football_betting.features.form import FormTracker
from football_betting.features.h2h import H2HTracker
from football_betting.features.home_advantage import HomeAdvantageTracker
from football_betting.features.rest_days import RestDaysTracker
from football_betting.features.xg_proxy import XgProxyTracker


def _m(
    home: str,
    away: str,
    hg: int,
    ag: int,
    day: int = 1,
    league: str = "PL",
    season: str = "2024-25",
    hs: int | None = None,
    ast: int | None = None,
    hst: int | None = None,
    as_: int | None = None,
) -> Match:
    return Match(
        date=date(2025, 1, day),
        league=league,
        season=season,
        home_team=home,
        away_team=away,
        home_goals=hg,
        away_goals=ag,
        home_shots=hs,
        away_shots=as_,
        home_shots_on_target=hst,
        away_shots_on_target=ast,
    )


# ───────────────────────── FormTracker ─────────────────────────

class TestFormTracker:
    def test_empty_returns_zeros(self) -> None:
        ft = FormTracker()
        feats = ft.features_for_match("A", "B")
        assert feats["form_home_ppg"] == 0.0
        assert feats["form_away_ppg"] == 0.0

    def test_win_increases_ppg(self) -> None:
        ft = FormTracker()
        for i in range(5):
            ft.update(_m("A", "B", 3, 0, day=i + 1))
        feats = ft.features_for_match("A", "C")
        # A won 5 straight → ppg close to 3
        assert feats["form_home_ppg"] > 2.5

    def test_exponential_decay_weights_recent(self) -> None:
        ft = FormTracker()
        # A loses heavily to X, then wins small
        ft.update(_m("A", "X", 0, 5, day=1))
        for i in range(4):
            ft.update(_m("A", "Y", 2, 0, day=i + 2))
        feats = ft.features_for_match("A", "Z")
        # Recent wins should dominate → ppg well above 0
        assert feats["form_home_ppg"] > 1.5

    def test_home_away_split(self) -> None:
        ft = FormTracker()
        # A wins at home, loses away
        for i in range(3):
            ft.update(_m("A", "X", 3, 0, day=i + 1))
            ft.update(_m("Y", "A", 3, 0, day=i + 10))
        feats = ft.features_for_match("A", "B")
        # Overall mixed; home-specific should be strong, away-specific weak
        assert feats["form_home_at_home_ppg"] > feats["form_away_at_away_ppg"]


# ───────────────────────── XgProxyTracker ─────────────────────────

class TestXgProxyTracker:
    def test_empty_returns_zeros(self) -> None:
        xt = XgProxyTracker()
        feats = xt.features_for_match("A", "B")
        assert feats["xg_home_for"] == 0.0

    def test_shots_increase_xg(self) -> None:
        xt = XgProxyTracker()
        for i in range(5):
            xt.update(_m("A", "B", 2, 0, day=i + 1, hs=15, ast=3, hst=7, as_=4))
        feats = xt.features_for_match("A", "C")
        # A has consistent attacking output → xg > 0
        assert feats["xg_home_for"] > 0.5

    def test_missing_shots_skip(self) -> None:
        xt = XgProxyTracker()
        # No shot stats
        xt.update(_m("A", "B", 2, 0, day=1))
        feats = xt.features_for_match("A", "C")
        # Should remain 0 — update was skipped
        assert feats["xg_home_for"] == 0.0


# ───────────────────────── H2HTracker ─────────────────────────

class TestH2HTracker:
    def test_no_history_default_zeros(self) -> None:
        h2h = H2HTracker()
        feats = h2h.features_for_match("A", "B")
        assert feats["h2h_n_meetings"] == 0

    def test_perfect_record(self) -> None:
        h2h = H2HTracker()
        for i in range(3):
            h2h.update(_m("A", "B", 2, 0, day=i + 1))
        feats = h2h.features_for_match("A", "B")
        assert feats["h2h_n_meetings"] == 3
        assert feats["h2h_home_team_winrate"] == 1.0

    def test_perspective_swap(self) -> None:
        """H2H records count home-team perspective correctly regardless of past venue."""
        h2h = H2HTracker()
        # A wins home, B wins home (A was away)
        h2h.update(_m("A", "B", 2, 0, day=1))
        h2h.update(_m("B", "A", 3, 1, day=2))  # A loses away
        # From A's perspective: 1 win + 1 loss
        feats = h2h.features_for_match("A", "B")
        assert feats["h2h_home_team_winrate"] == 0.5
        assert feats["h2h_away_wins"] == 0.5


# ───────────────────────── RestDaysTracker ─────────────────────────

class TestRestDaysTracker:
    def test_no_prior_returns_sentinel(self) -> None:
        rd = RestDaysTracker()
        feats = rd.features_for_match("A", "B", date(2025, 1, 10))
        assert feats["rest_home_days"] == -1.0

    def test_rest_days_computed(self) -> None:
        rd = RestDaysTracker()
        rd.update(_m("A", "X", 1, 1, day=1))
        feats = rd.features_for_match("A", "B", date(2025, 1, 8))
        assert feats["rest_home_days"] == 7.0
        # 7 days is in optimal range → positive fatigue score
        assert feats["rest_home_fatigue"] == pytest.approx(0.1, abs=0.01)

    def test_fatigue_for_short_rest(self) -> None:
        rd = RestDaysTracker()
        rd.update(_m("A", "X", 1, 1, day=1))
        feats = rd.features_for_match("A", "B", date(2025, 1, 3))
        # 2 days → fatigued
        assert feats["rest_home_fatigue"] < 0


# ───────────────────────── HomeAdvantageTracker ─────────────────────────

class TestHomeAdvantageTracker:
    def test_fallback_to_league_default(self) -> None:
        ha = HomeAdvantageTracker()
        # No data AND no known league → hardcoded fallback 0.35
        assert ha.team_home_advantage("A") == pytest.approx(0.35, abs=0.01)

    def test_adjusted_with_data(self) -> None:
        ha = HomeAdvantageTracker()
        # A is much stronger at home
        for i in range(10):
            ha.update(_m("A", "X", 4, 0, day=i + 1))
            ha.update(_m("Y", "A", 1, 1, day=i + 20))
        team_ha = ha.team_home_advantage("A")
        # Should be positive (strong home team)
        assert team_ha > 0.35


# ───────────────────────── FeatureBuilder integration ─────────────────────────

class TestFeatureBuilder:
    def test_build_features_returns_flat_dict(self) -> None:
        fb = FeatureBuilder()
        for i in range(5):
            fb.update_with_match(_m("A", "B", 2, 1, day=i + 1))

        feats = fb.build_features(
            home_team="A", away_team="B", league_key="PL", match_date=date(2025, 3, 1)
        )
        # Should contain all feature groups
        assert "pi_home_H" in feats
        assert "form_home_ppg" in feats
        assert "h2h_n_meetings" in feats
        assert "rest_home_days" in feats
        assert "home_team_ha" in feats
        assert "league_avg_goals" in feats

    def test_reset_clears_state(self) -> None:
        fb = FeatureBuilder()
        fb.update_with_match(_m("A", "B", 2, 0))
        fb.reset()
        feats = fb.build_features("A", "B", "PL", date(2025, 1, 1))
        assert feats["form_home_ppg"] == 0.0

    def test_fit_on_history_chronological(self) -> None:
        fb = FeatureBuilder()
        matches = [_m("A", "B", 2, 0, day=i + 1) for i in range(20)]
        fb.fit_on_history(matches)
        # pi_ratings has processed all matches
        assert fb.pi_ratings.get("A").home > 0
        # 20 h2h meetings logged
        assert fb.h2h_tracker.features_for_match("A", "B")["h2h_n_meetings"] == 6  # max_games cap
