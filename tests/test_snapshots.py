"""Phase 4 — Opening-line snapshot capture + merge tests."""
from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from football_betting.data import odds_snapshots, snapshot_service
from football_betting.data.models import Fixture, Match, MatchOdds
from football_betting.data.snapshot_service import (
    _within_tminus_window,
    capture_odds_snapshot,
    load_opening_odds,
    merge_snapshots_into_matches,
)
from football_betting.tracking.metrics import clv_summary


@pytest.fixture
def tmp_snapshot_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect persisted odds snapshots to an isolated temp directory."""
    monkeypatch.setattr(odds_snapshots, "SNAPSHOT_DIR", tmp_path)
    return tmp_path


def _make_fixture(
    *, home: str, away: str, match_date: date, kickoff: datetime | None, odds: MatchOdds | None
) -> Fixture:
    return Fixture(
        date=match_date,
        league="BL",
        home_team=home,
        away_team=away,
        kickoff_datetime_utc=kickoff,
        odds=odds,
    )


def _make_match(*, home: str, away: str, match_date: date, closing: MatchOdds) -> Match:
    return Match(
        date=match_date,
        league="BL",
        season="2024-25",
        home_team=home,
        away_team=away,
        home_goals=1,
        away_goals=0,
        odds=closing,
    )


class TestTMinusWindow:
    def test_within_window(self) -> None:
        now = datetime(2026, 4, 20, 10, 0, tzinfo=UTC)
        kickoff = now + timedelta(hours=24)
        assert _within_tminus_window(kickoff, now, t_minus_hours=48) is True

    def test_outside_window(self) -> None:
        now = datetime(2026, 4, 20, 10, 0, tzinfo=UTC)
        kickoff = now + timedelta(hours=72)
        assert _within_tminus_window(kickoff, now, t_minus_hours=48) is False

    def test_past_kickoff_rejected(self) -> None:
        now = datetime(2026, 4, 20, 10, 0, tzinfo=UTC)
        kickoff = now - timedelta(hours=1)
        assert _within_tminus_window(kickoff, now, t_minus_hours=48) is False

    def test_none_kickoff_rejected(self) -> None:
        now = datetime(2026, 4, 20, 10, 0, tzinfo=UTC)
        assert _within_tminus_window(None, now, t_minus_hours=48) is False


class TestCaptureOddsSnapshot:
    def test_persists_only_fixtures_in_window(self, tmp_snapshot_dir: Path) -> None:
        now = datetime(2026, 4, 20, 10, 0, tzinfo=UTC)
        odds = MatchOdds(home=2.1, draw=3.4, away=3.5, bookmaker="odds_api")

        in_window = _make_fixture(
            home="Bayern", away="Dortmund",
            match_date=date(2026, 4, 22),
            kickoff=now + timedelta(hours=24),
            odds=odds,
        )
        out_of_window = _make_fixture(
            home="Leipzig", away="Leverkusen",
            match_date=date(2026, 5, 1),
            kickoff=now + timedelta(hours=200),
            odds=odds,
        )
        no_odds = _make_fixture(
            home="Mainz", away="Bremen",
            match_date=date(2026, 4, 22),
            kickoff=now + timedelta(hours=24),
            odds=None,
        )

        captured = capture_odds_snapshot(
            "BL",
            [in_window, out_of_window, no_odds],
            t_minus_hours=48,
            now=now,
        )

        assert len(captured) == 1
        assert captured[0].home_team == "Bayern"

        path = tmp_snapshot_dir / "odds_BL.jsonl"
        assert path.exists()
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 1
        assert rows[0]["home"] == "Bayern"
        assert rows[0]["home_odds"] == pytest.approx(2.1)

    def test_snapshot_schema_roundtrip(self, tmp_snapshot_dir: Path) -> None:
        """Written rows must be round-trippable through load_opening_odds."""
        now = datetime(2026, 4, 20, 10, 0, tzinfo=UTC)
        odds = MatchOdds(home=2.0, draw=3.3, away=3.8, bookmaker="odds_api")
        fx = _make_fixture(
            home="Bayern", away="Dortmund",
            match_date=date(2026, 4, 22),
            kickoff=now + timedelta(hours=10),
            odds=odds,
        )
        capture_odds_snapshot("BL", [fx], t_minus_hours=48, now=now)

        opening_map = load_opening_odds("BL")
        key = ("2026-04-22", "Bayern", "Dortmund")
        assert key in opening_map
        assert opening_map[key].home == pytest.approx(2.0)
        assert opening_map[key].away == pytest.approx(3.8)


class TestLoadOpeningOdds:
    def test_picks_earliest_timestamp(self, tmp_snapshot_dir: Path) -> None:
        early = datetime(2026, 4, 20, 8, 0, tzinfo=UTC)
        late = datetime(2026, 4, 21, 16, 0, tzinfo=UTC)

        odds_snapshots.append_snapshot(
            "BL", "Bayern", "Dortmund", "2026-04-22",
            MatchOdds(home=2.20, draw=3.40, away=3.50, bookmaker="odds_api"),
            timestamp=late,
        )
        odds_snapshots.append_snapshot(
            "BL", "Bayern", "Dortmund", "2026-04-22",
            MatchOdds(home=1.90, draw=3.60, away=4.20, bookmaker="odds_api"),
            timestamp=early,
        )
        opening_map = load_opening_odds("BL")
        opener = opening_map[("2026-04-22", "Bayern", "Dortmund")]
        assert opener.home == pytest.approx(1.90)

    def test_missing_file_returns_empty(self, tmp_snapshot_dir: Path) -> None:
        assert load_opening_odds("BL") == {}


class TestMergeSnapshotsIntoMatches:
    def test_merge_attaches_opening_to_matching_match(self, tmp_snapshot_dir: Path) -> None:
        ts = datetime(2026, 4, 20, 8, 0, tzinfo=UTC)
        odds_snapshots.append_snapshot(
            "BL", "Bayern", "Dortmund", "2026-04-22",
            MatchOdds(home=1.90, draw=3.60, away=4.20, bookmaker="odds_api"),
            timestamp=ts,
        )
        closing = MatchOdds(home=1.80, draw=3.70, away=4.50, bookmaker="Pinnacle")
        match = _make_match(
            home="Bayern", away="Dortmund",
            match_date=date(2026, 4, 22), closing=closing,
        )

        merged = merge_snapshots_into_matches([match], "BL")
        assert merged[0].opening_odds is not None
        assert merged[0].opening_odds.home == pytest.approx(1.90)
        # Closing untouched.
        assert merged[0].odds is not None
        assert merged[0].odds.home == pytest.approx(1.80)

    def test_merge_falls_back_to_closing_when_opening_missing(
        self, tmp_snapshot_dir: Path
    ) -> None:
        closing = MatchOdds(home=1.80, draw=3.70, away=4.50, bookmaker="Pinnacle")
        match = _make_match(
            home="Bayern", away="Dortmund",
            match_date=date(2026, 4, 22), closing=closing,
        )
        merged = merge_snapshots_into_matches([match], "BL")
        # No snapshots persisted → opening_odds stays None (graceful-None).
        assert merged[0].opening_odds is None
        assert merged[0].odds is not None


class TestCLVNonDegenerateWithSnapshots:
    def test_clv_nondegenerate_with_real_snapshots(self, tmp_snapshot_dir: Path) -> None:
        """When opening > closing across the board, CLV must be positive."""
        # Two matches, opening odds higher than closing on the home side.
        for home, away, match_date, open_home, _close_home in [
            ("Bayern", "Dortmund", "2026-04-22", 2.20, 2.00),
            ("Leipzig", "Leverkusen", "2026-04-23", 3.80, 3.40),
        ]:
            odds_snapshots.append_snapshot(
                "BL", home, away, match_date,
                MatchOdds(home=open_home, draw=3.50, away=3.50, bookmaker="odds_api"),
                timestamp=datetime(2026, 4, 20, 8, 0, tzinfo=UTC),
            )
        matches = [
            _make_match(
                home="Bayern", away="Dortmund", match_date=date(2026, 4, 22),
                closing=MatchOdds(home=2.00, draw=3.40, away=3.80, bookmaker="Pinnacle"),
            ),
            _make_match(
                home="Leipzig", away="Leverkusen", match_date=date(2026, 4, 23),
                closing=MatchOdds(home=3.40, draw=3.40, away=2.10, bookmaker="Pinnacle"),
            ),
        ]
        merged = merge_snapshots_into_matches(matches, "BL")
        bet_odds = [m.opening_odds.home for m in merged if m.opening_odds]
        close_odds = [m.odds.home for m in merged if m.odds]
        stats = clv_summary(bet_odds, close_odds)
        assert stats["n"] == 2
        assert stats["mean_clv"] > 0.0
        assert stats["pct_positive"] == pytest.approx(1.0)


class TestMatchModelOpeningField:
    def test_opening_odds_defaults_to_none(self) -> None:
        m = _make_match(
            home="A", away="B", match_date=date(2026, 4, 22),
            closing=MatchOdds(home=2.0, draw=3.4, away=3.5, bookmaker="avg"),
        )
        assert m.opening_odds is None

    def test_opening_odds_round_trips(self) -> None:
        opening = MatchOdds(home=2.3, draw=3.5, away=3.0, bookmaker="odds_api_opening")
        m = Match(
            date=date(2026, 4, 22), league="BL", season="2024-25",
            home_team="A", away_team="B", home_goals=0, away_goals=0,
            odds=MatchOdds(home=2.0, draw=3.4, away=3.5, bookmaker="Pinnacle"),
            opening_odds=opening,
        )
        assert m.opening_odds is not None
        assert m.opening_odds.home == pytest.approx(2.3)


# Silence unused-import warning for snapshot_service module (exercised above).
_ = snapshot_service
