"""Tests for v0.3 scraping infrastructure."""
from __future__ import annotations

from datetime import date, datetime
import time
from pathlib import Path

import pytest

from football_betting.config import LEAGUES
from football_betting.scraping.cache import ResponseCache
from football_betting.scraping.rate_limiter import TokenBucketLimiter
from football_betting.scraping.sofascore import (
    SofascoreClient,
    SofascoreMatch,
    _name_matches,
    _normalise_team_name,
)


class TestResponseCache:
    def test_set_and_get(self, tmp_path: Path) -> None:
        cache = ResponseCache(db_path=tmp_path / "test.sqlite")
        cache.set("https://example.com/a", '{"x": 1}')
        result = cache.get("https://example.com/a")
        assert result == '{"x": 1}'

    def test_miss_returns_none(self, tmp_path: Path) -> None:
        cache = ResponseCache(db_path=tmp_path / "test.sqlite")
        assert cache.get("https://nope.com") is None

    def test_params_affect_key(self, tmp_path: Path) -> None:
        cache = ResponseCache(db_path=tmp_path / "test.sqlite")
        cache.set("https://api.com/x", "a", params={"q": 1})
        cache.set("https://api.com/x", "b", params={"q": 2})
        assert cache.get("https://api.com/x", params={"q": 1}) == "a"
        assert cache.get("https://api.com/x", params={"q": 2}) == "b"

    def test_expired_entry_purged(self, tmp_path: Path) -> None:
        cache = ResponseCache(db_path=tmp_path / "test.sqlite")
        cache.set("https://x.com", "stale", ttl_seconds=-1)  # already expired
        assert cache.get("https://x.com") is None

    def test_purge_expired(self, tmp_path: Path) -> None:
        cache = ResponseCache(db_path=tmp_path / "test.sqlite")
        cache.set("https://a.com", "a", ttl_seconds=-1)
        cache.set("https://b.com", "b", ttl_seconds=3600)
        n_purged = cache.purge_expired()
        assert n_purged == 1
        assert cache.get("https://b.com") == "b"

    def test_stats(self, tmp_path: Path) -> None:
        cache = ResponseCache(db_path=tmp_path / "test.sqlite")
        cache.set("https://a.com", "x" * 100)
        stats = cache.stats()
        assert stats["entries"] == 1
        assert stats["total_bytes"] >= 100


class TestTokenBucketLimiter:
    def test_immediate_acquire_when_tokens_available(self) -> None:
        limiter = TokenBucketLimiter(rate_per_second=10, burst_capacity=5)
        wait = limiter.acquire()
        assert wait == 0.0

    def test_blocks_when_exhausted(self) -> None:
        limiter = TokenBucketLimiter(rate_per_second=10, burst_capacity=1)
        limiter.acquire()  # consume first token
        t0 = time.monotonic()
        wait = limiter.acquire()
        elapsed = time.monotonic() - t0
        # Should have waited ~0.1s to refill 1 token at rate=10
        assert elapsed >= 0.05
        assert wait >= 0.0

    def test_from_delay(self) -> None:
        limiter = TokenBucketLimiter.from_delay(delay_seconds=2.0)
        assert limiter.rate_per_second == 0.5
        assert limiter.burst_capacity == 1


class TestSofascoreClient:
    def test_parse_match_basic(self) -> None:
        client = SofascoreClient()
        event_json = {
            "id": 12345,
            "tournament": {"id": 17},
            "homeTeam": {"name": "Arsenal"},
            "awayTeam": {"name": "Chelsea"},
            "homeScore": {"current": 2},
            "awayScore": {"current": 1},
            "startTimestamp": 1712770200,
            "status": {"type": "finished"},
        }
        match = client.parse_match(event_json)
        assert match is not None
        assert match.event_id == 12345
        assert match.home_team == "Arsenal"
        assert match.away_team == "Chelsea"
        assert match.home_goals == 2
        assert match.away_goals == 1
        assert match.status == "finished"

    def test_parse_match_missing_fields(self) -> None:
        client = SofascoreClient()
        # Upcoming match (no score)
        event_json = {
            "id": 99999,
            "tournament": {"id": 17},
            "homeTeam": {"name": "Liverpool"},
            "awayTeam": {"name": "Everton"},
            "homeScore": {},
            "awayScore": {},
            "startTimestamp": 1712770200,
            "status": {"type": "scheduled"},
        }
        match = client.parse_match(event_json)
        assert match is not None
        assert match.home_goals is None
        assert match.away_goals is None

    def test_parse_match_broken(self) -> None:
        client = SofascoreClient()
        # Missing required field
        assert client.parse_match({}) is None

    def test_scraping_disabled_by_default(self) -> None:
        client = SofascoreClient()
        # Env var not set
        assert not client.cfg.enabled
        with pytest.raises(RuntimeError, match="disabled"):
            client._fetch_json("/test")

    def test_find_event_id_accepts_string_date_and_deduplicates_hits(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        client = SofascoreClient()
        tournament_id = LEAGUES["SA"].sofascore_tournament_id or 0
        event = {
            "id": 13980099,
            "tournament": {"uniqueTournament": {"id": tournament_id}},
            "homeTeam": {"name": "US Lecce"},
            "awayTeam": {"name": "ACF Fiorentina"},
        }

        monkeypatch.setattr(
            SofascoreClient,
            "get_scheduled_events_for_date",
            lambda self, *_args, **_kwargs: [event],
        )

        event_id = client.find_event_id(
            "SA",
            "Lecce",
            "Fiorentina",
            "2026-04-20",
        )

        assert event_id == 13980099

    def test_find_event_id_returns_none_for_ambiguous_hits(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        client = SofascoreClient()
        tournament_id = LEAGUES["SA"].sofascore_tournament_id or 0
        events = [
            {
                "id": 1,
                "tournament": {"uniqueTournament": {"id": tournament_id}},
                "homeTeam": {"name": "US Lecce"},
                "awayTeam": {"name": "ACF Fiorentina"},
            },
            {
                "id": 2,
                "tournament": {"uniqueTournament": {"id": tournament_id}},
                "homeTeam": {"name": "Lecce"},
                "awayTeam": {"name": "Fiorentina"},
            },
        ]

        monkeypatch.setattr(
            SofascoreClient,
            "get_scheduled_events_for_date",
            lambda self, *_args, **_kwargs: events,
        )

        event_id = client.find_event_id(
            "SA",
            "Lecce",
            "Fiorentina",
            datetime(2026, 4, 20, 20, 45),
        )

        assert event_id is None

    def test_normalise_team_name_handles_common_aliases(self) -> None:
        assert _normalise_team_name("US Lecce") == "lecce"
        assert _normalise_team_name("ACF Fiorentina") == "fiorentina"
        assert _normalise_team_name("1. FC Köln") == "koln"

    def test_name_matches_handles_prefixes_and_misses(self) -> None:
        assert _name_matches("lecce", "us lecce")
        assert _name_matches("fiorentina", "acf fiorentina")
        assert not _name_matches("lecce", "lazio")


class TestSofascoreMatch:
    def test_to_dict(self) -> None:
        match = SofascoreMatch(
            event_id=1, tournament_id=17,
            home_team="A", away_team="B",
            home_goals=2, away_goals=1,
            start_timestamp=1712770200,
            status="finished",
            home_xg=1.8, away_xg=0.9,
        )
        d = match.to_dict()
        assert d["event_id"] == 1
        assert d["home_xg"] == 1.8
        assert "date" in d

    def test_date_property(self) -> None:
        match = SofascoreMatch(
            event_id=1, tournament_id=17,
            home_team="A", away_team="B",
            home_goals=None, away_goals=None,
            start_timestamp=1712770200,
            status="scheduled",
        )
        # 1712770200 → 2024-04-10
        assert match.date.year == 2024


class TestSofascoreOverrides:
    def test_roundtrip(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from football_betting.scraping import sofascore_overrides

        path = tmp_path / "overrides.json"
        monkeypatch.setattr(sofascore_overrides, "OVERRIDES_PATH", path)

        assert sofascore_overrides.get_override("foo-vs-bar-2026-01-01") is None
        sofascore_overrides.set_override("foo-vs-bar-2026-01-01", 42)
        assert sofascore_overrides.get_override("foo-vs-bar-2026-01-01") == 42
        sofascore_overrides.set_override("baz-vs-qux-2026-01-02", 7)
        assert sofascore_overrides.load_all() == {
            "foo-vs-bar-2026-01-01": 42,
            "baz-vs-qux-2026-01-02": 7,
        }

    def test_missing_file_returns_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from football_betting.scraping import sofascore_overrides

        monkeypatch.setattr(sofascore_overrides, "OVERRIDES_PATH", tmp_path / "nope.json")
        assert sofascore_overrides.load_all() == {}
        assert sofascore_overrides.get_override("any-slug") is None

    def test_corrupt_file_returns_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from football_betting.scraping import sofascore_overrides

        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        monkeypatch.setattr(sofascore_overrides, "OVERRIDES_PATH", path)
        assert sofascore_overrides.load_all() == {}

