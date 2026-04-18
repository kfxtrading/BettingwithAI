"""Tests for v0.3 new feature trackers."""
from __future__ import annotations

from datetime import date, datetime

import pytest

from football_betting.data.models import Fixture, Match, MatchOdds
from football_betting.features.builder import FeatureBuilder
from football_betting.features.market_movement import MarketMovementTracker, OddsSnapshot
from football_betting.features.real_xg import RealXgTracker
from football_betting.features.squad_quality import SquadQualityTracker


def _sf_match(
    home: str, away: str,
    hg: int, ag: int,
    h_xg: float | None, a_xg: float | None,
    h_rating: float | None = None, a_rating: float | None = None,
    h_xi: list[int] | None = None, a_xi: list[int] | None = None,
) -> dict:
    return {
        "home_team": home,
        "away_team": away,
        "home_goals": hg,
        "away_goals": ag,
        "home_xg": h_xg,
        "away_xg": a_xg,
        "home_avg_rating": h_rating,
        "away_avg_rating": a_rating,
        "home_starting_xi": h_xi or [],
        "away_starting_xi": a_xi or [],
        "home_big_chances": None,
        "away_big_chances": None,
    }


# ───────────────────────── RealXgTracker ─────────────────────────

class TestRealXgTracker:
    def test_empty_returns_zeros(self) -> None:
        t = RealXgTracker()
        feats = t.features_for_match("A", "B")
        assert feats["real_xg_home_for"] == 0.0

    def test_ingest_basic(self) -> None:
        t = RealXgTracker()
        t.ingest_sofascore_match(_sf_match("A", "B", 2, 1, 1.8, 0.9))
        assert t.team_has_data("A")
        assert t.team_has_data("B")

    def test_skip_when_missing_xg(self) -> None:
        t = RealXgTracker()
        t.ingest_sofascore_match(_sf_match("A", "B", 2, 1, None, None))
        assert not t.team_has_data("A")

    def test_weighted_xg_recent_heavier(self) -> None:
        t = RealXgTracker()
        # 5 old matches with low xG
        for _ in range(5):
            t.ingest_sofascore_match(_sf_match("A", "X", 0, 0, 0.5, 0.5))
        # 3 recent with high xG
        for _ in range(3):
            t.ingest_sofascore_match(_sf_match("A", "Y", 3, 0, 3.0, 0.5))

        feats = t.features_for_match("A", "Z")
        # Weighted xG should be closer to recent (3.0) than mean (1.4)
        assert feats["real_xg_home_for"] > 1.5

    def test_finishing_quality_ratio(self) -> None:
        t = RealXgTracker()
        # Scored more than xG suggests (lucky / clinical)
        for _ in range(5):
            t.ingest_sofascore_match(_sf_match("A", "B", 3, 0, 1.5, 0.5))
        feats = t.features_for_match("A", "C")
        # 3 goals vs 1.5 xG → finishing ~2.0
        assert feats["real_xg_home_finishing"] > 1.5

    def test_ingest_many_returns_count(self) -> None:
        t = RealXgTracker()
        matches = [
            _sf_match("A", "B", 2, 1, 1.8, 0.9),
            _sf_match("C", "D", 1, 1, 1.1, 1.1),
            _sf_match("A", "D", 3, 0, 2.2, 0.5),
        ]
        n = t.ingest_many(matches)
        assert n == 3


# ───────────────────────── SquadQualityTracker ─────────────────────────

class TestSquadQualityTracker:
    def test_empty_returns_zeros(self) -> None:
        t = SquadQualityTracker()
        feats = t.features_for_match("A", "B")
        assert feats["squad_home_rating"] == 0.0

    def test_ingest_and_rating(self) -> None:
        t = SquadQualityTracker()
        for _ in range(5):
            t.ingest_sofascore_match(
                _sf_match("A", "B", 1, 1, 1.0, 1.0,
                          h_rating=7.5, a_rating=6.8,
                          h_xi=list(range(11)), a_xi=list(range(100, 111)))
            )
        feats = t.features_for_match("A", "B")
        assert feats["squad_home_rating"] == pytest.approx(7.5, abs=0.01)
        assert feats["squad_away_rating"] == pytest.approx(6.8, abs=0.01)
        assert feats["squad_rating_diff"] == pytest.approx(0.7, abs=0.01)

    def test_rotation_score(self) -> None:
        t = SquadQualityTracker()
        # First match: XI = [0..10]
        t.ingest_sofascore_match(
            _sf_match("A", "B", 1, 0, 1.0, 0.5,
                      h_rating=7.0, a_rating=7.0,
                      h_xi=list(range(11)), a_xi=list(range(100, 111)))
        )
        # Second match: XI = [0..9, 99] — 1 change
        t.ingest_sofascore_match(
            _sf_match("A", "B", 1, 0, 1.0, 0.5,
                      h_rating=7.0, a_rating=7.0,
                      h_xi=[*range(10), 99], a_xi=list(range(100, 111)))
        )
        feats = t.features_for_match("A", "B")
        # 1 change out of 11 slots
        assert 0 < feats["squad_home_rotation"] < 0.2

    def test_key_player_absence(self) -> None:
        t = SquadQualityTracker()
        # Simulate 12 matches: player 0 plays in 11, player 99 plays in 1
        for _ in range(11):
            t.ingest_sofascore_match(
                _sf_match("A", "B", 1, 0, 1.0, 0.5,
                          h_rating=7.0, a_rating=7.0,
                          h_xi=list(range(11)), a_xi=list(range(100, 111)))
            )
        # Last match: player 0 missing (replaced by 99)
        t.ingest_sofascore_match(
            _sf_match("A", "B", 1, 0, 1.0, 0.5,
                      h_rating=6.5, a_rating=7.0,
                      h_xi=[*range(1, 11), 99], a_xi=list(range(100, 111)))
        )
        feats = t.features_for_match("A", "B")
        # Player 0 is "season XI" → absent → at least 1 key absence
        assert feats["squad_home_key_absences"] >= 1


# ───────────────────────── MarketMovementTracker ─────────────────────────

class TestMarketMovementTracker:
    def test_empty_returns_neutral(self) -> None:
        t = MarketMovementTracker()
        feats = t.features_for_fixture("A", "B", "2026-04-17")
        assert feats["mm_steam_detected"] == 0.0
        assert feats["mm_n_snapshots"] == 0.0

    def test_add_snapshots(self) -> None:
        t = MarketMovementTracker()
        t.add_snapshot("A", "B", "2026-04-17",
                       OddsSnapshot(timestamp=datetime(2026, 4, 17, 10, 0),
                                    home=2.50, draw=3.20, away=2.80))
        t.add_snapshot("A", "B", "2026-04-17",
                       OddsSnapshot(timestamp=datetime(2026, 4, 17, 16, 0),
                                    home=2.30, draw=3.20, away=3.00))
        feats = t.features_for_fixture("A", "B", "2026-04-17")
        assert feats["mm_n_snapshots"] == 2.0
        # Home odds drifted down (favorite got shorter)
        assert feats["mm_home_odds_drift"] < 0

    def test_steam_move_detected(self) -> None:
        t = MarketMovementTracker()
        t.add_snapshot("A", "B", "2026-04-17",
                       OddsSnapshot(timestamp=datetime(2026, 4, 17, 15, 0),
                                    home=2.00, draw=3.50, away=3.50))
        # 10 minutes later: big move
        t.add_snapshot("A", "B", "2026-04-17",
                       OddsSnapshot(timestamp=datetime(2026, 4, 17, 15, 10),
                                    home=1.80, draw=3.50, away=4.00))
        feats = t.features_for_fixture("A", "B", "2026-04-17")
        # 10% move on home odds within 10 min → steam
        assert feats["mm_steam_detected"] == 1.0

    def test_no_steam_when_slow(self) -> None:
        t = MarketMovementTracker()
        t.add_snapshot("A", "B", "2026-04-17",
                       OddsSnapshot(timestamp=datetime(2026, 4, 17, 8, 0),
                                    home=2.00, draw=3.50, away=3.50))
        # 2 hours later: same movement but slow
        t.add_snapshot("A", "B", "2026-04-17",
                       OddsSnapshot(timestamp=datetime(2026, 4, 17, 10, 0),
                                    home=1.80, draw=3.50, away=4.00))
        feats = t.features_for_fixture("A", "B", "2026-04-17")
        # Outside 30-min window → not a steam move
        assert feats["mm_steam_detected"] == 0.0


# ───────────────────────── Squad Quality without XI ─────────────────────────


class TestSquadQualityWithoutXI:
    def test_rating_alone_populates_feature(self) -> None:
        """Rating without XI should still drive squad_home_rating — XI is optional."""
        t = SquadQualityTracker()
        for _ in range(5):
            t.ingest_sofascore_match(
                _sf_match("A", "B", 1, 1, 1.0, 1.0,
                          h_rating=7.2, a_rating=6.5,
                          h_xi=[], a_xi=[])  # no XI present
            )
        feats = t.features_for_match("A", "B")
        assert feats["squad_home_rating"] == pytest.approx(7.2, abs=0.01)
        assert feats["squad_away_rating"] == pytest.approx(6.5, abs=0.01)
        # Rotation/absences stay 0 gracefully
        assert feats["squad_home_rotation"] == 0.0
        assert feats["squad_home_key_absences"] == 0.0


# ───────────────────────── Fixture season inference ─────────────────────────


class TestFixtureSeason:
    def test_effective_season_from_date_autumn(self) -> None:
        fx = Fixture(date="2025-09-15", league="PL",
                     home_team="A", away_team="B")
        assert fx.effective_season() == "2025-26"

    def test_effective_season_from_date_spring(self) -> None:
        fx = Fixture(date="2026-04-18", league="PL",
                     home_team="A", away_team="B")
        assert fx.effective_season() == "2025-26"

    def test_explicit_season_wins(self) -> None:
        fx = Fixture(date="2026-04-18", league="PL",
                     home_team="A", away_team="B", season="2023-24")
        assert fx.effective_season() == "2023-24"


class TestFeatureBuilderSeasonPassthrough:
    def test_point_deduction_applied_at_inference(self, monkeypatch) -> None:
        """features_for_fixture must pass `season` so POINT_DEDUCTIONS fire."""
        from football_betting import config

        monkeypatch.setitem(config.POINT_DEDUCTIONS, ("TeamX", "2025-26"), 9)

        fb = FeatureBuilder()
        fx = Fixture(date="2025-10-01", league="PL",
                     home_team="TeamX", away_team="Other")
        feats = fb.features_for_fixture(fx)
        assert feats["home_point_ded"] == 9.0
        assert feats["away_point_ded"] == 0.0


# ───────────────────────── Sofascore staging (Fix 3) ─────────────────────────


def _match(
    home: str, away: str, hg: int, ag: int, day: int,
    season: str = "2024-25",
) -> Match:
    return Match(
        date=date(2025, 1, day),
        league="PL",
        season=season,
        home_team=home,
        away_team=away,
        home_goals=hg,
        away_goals=ag,
    )


class TestSofascoreStaging:
    def test_staged_record_ingested_on_update(self) -> None:
        fb = FeatureBuilder()
        sf = _sf_match("A", "B", 2, 1, 1.9, 0.8)
        sf["date"] = date(2025, 1, 2).isoformat()
        fb.stage_sofascore_batch([sf])
        # Before update → real_xg tracker still empty
        assert not fb.real_xg_tracker.team_has_data("A")
        fb.update_with_match(_match("A", "B", 2, 1, day=2))
        # Now ingested
        assert fb.real_xg_tracker.team_has_data("A")
        assert fb.real_xg_tracker.team_has_data("B")

    def test_reset_preserves_staged(self) -> None:
        fb = FeatureBuilder()
        sf = _sf_match("A", "B", 2, 1, 1.9, 0.8)
        sf["date"] = date(2025, 1, 2).isoformat()
        fb.stage_sofascore_batch([sf])
        fb.reset()
        # Staged still there → consumed by subsequent walk
        fb.update_with_match(_match("A", "B", 2, 1, day=2))
        assert fb.real_xg_tracker.team_has_data("A")

    def test_future_match_stays_staged(self) -> None:
        """Features for match i don't see Sofascore data from match i+1."""
        fb = FeatureBuilder()
        future = _sf_match("A", "B", 3, 0, 2.5, 0.3)
        future["date"] = date(2025, 1, 10).isoformat()
        fb.stage_sofascore_batch([future])
        # Process an earlier match; future Sofascore remains staged
        fb.update_with_match(_match("A", "B", 1, 0, day=5))
        assert not fb.real_xg_tracker.team_has_data("A")


# ───────────────────────── Odds snapshots persistence (Fix 4) ─────────────────────────


class TestOddsSnapshotsPersistence:
    def test_append_and_load_roundtrip(self, tmp_path, monkeypatch) -> None:
        from football_betting import config
        from football_betting.data import odds_snapshots

        monkeypatch.setattr(config, "SNAPSHOT_DIR", tmp_path)
        monkeypatch.setattr(odds_snapshots, "SNAPSHOT_DIR", tmp_path)

        odds = MatchOdds(home=2.50, draw=3.20, away=2.80)
        # Two snapshots, hours apart → drift signal
        odds_snapshots.append_snapshot(
            "PL", "A", "B", "2099-04-18", odds,
            timestamp=datetime(2099, 4, 18, 10, 0),
        )
        odds_snapshots.append_snapshot(
            "PL", "A", "B", "2099-04-18",
            MatchOdds(home=2.30, draw=3.20, away=3.00),
            timestamp=datetime(2099, 4, 18, 16, 0),
        )

        tracker = MarketMovementTracker()
        n = odds_snapshots.load_into_tracker("PL", tracker)
        assert n == 2
        feats = tracker.features_for_fixture("A", "B", "2099-04-18")
        assert feats["mm_n_snapshots"] == 2.0
        # Home odds shortened → negative drift
        assert feats["mm_home_odds_drift"] < 0

    def test_only_future_skips_past(self, tmp_path, monkeypatch) -> None:
        from football_betting import config
        from football_betting.data import odds_snapshots

        monkeypatch.setattr(config, "SNAPSHOT_DIR", tmp_path)
        monkeypatch.setattr(odds_snapshots, "SNAPSHOT_DIR", tmp_path)

        odds_snapshots.append_snapshot(
            "PL", "A", "B", "1999-01-01",
            MatchOdds(home=2.0, draw=3.0, away=4.0),
            timestamp=datetime(1999, 1, 1, 12, 0),
        )
        tracker = MarketMovementTracker()
        n = odds_snapshots.load_into_tracker("PL", tracker, only_future=True)
        assert n == 0
