"""Tests for v0.3 scraping infrastructure."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from football_betting.scraping.cache import ResponseCache
from football_betting.scraping.rate_limiter import TokenBucketLimiter
from football_betting.scraping.sofascore import SofascoreClient, SofascoreMatch


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
