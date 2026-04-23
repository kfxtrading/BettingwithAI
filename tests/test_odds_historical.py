"""Tests for the Phase 8 historical-odds backfill pipeline."""
from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from football_betting.config import OddsApiHistoricalConfig
from football_betting.features.market_microstructure import (
    MM_FEATURE_KEYS,
    MarketMicrostructureTracker,
)
from football_betting.scraping.odds_api_historical import (
    SNAPSHOT_COLUMNS,
    BudgetTracker,
    OddsApiHistoricalClient,
    OddsApiHistoricalError,
    append_rows,
    parse_snapshot_payload,
    plan_snapshot_timestamps,
    season_window,
)


def _mk_cfg(tmp_path: Path, **overrides) -> OddsApiHistoricalConfig:
    # Config is frozen; tests rely on ODDS_SNAPSHOT_DIR path manipulation via monkeypatch.
    base = OddsApiHistoricalConfig()
    from dataclasses import replace
    return replace(base, **overrides)


# ───────────────────────── Credits pricing ─────────────────────────


def test_credits_per_call_h2h_eu():
    cfg = OddsApiHistoricalConfig(regions="eu", markets="h2h")
    assert cfg.credits_per_call() == 10


def test_credits_per_call_multi_markets():
    cfg = OddsApiHistoricalConfig(regions="eu,uk", markets="h2h,totals,spreads")
    assert cfg.credits_per_call() == 60


# ───────────────────────── Season window ─────────────────────────


def test_season_window():
    assert season_window("2024-25") == (date(2024, 8, 1), date(2025, 5, 31))


def test_season_window_invalid():
    with pytest.raises(OddsApiHistoricalError):
        season_window("nonsense")


def test_plan_snapshot_timestamps_orders_and_dedups():
    start = date(2024, 8, 1)
    end = date(2024, 8, 21)
    ts = plan_snapshot_timestamps(start, end, hours_before_anchor=(168, 24, 2))
    # 3 Fridays × 3 offsets — may share timestamps across weeks, just assert sorted + unique.
    assert ts == sorted(ts)
    assert len(ts) == len(set(ts))
    assert all(t.tzinfo is not None for t in ts)


# ───────────────────────── Budget tracker ─────────────────────────


def test_budget_tracker_roundtrip(tmp_path):
    path = tmp_path / "_credits.json"
    bt = BudgetTracker(path=path)
    at = datetime(2026, 4, 23, 12, tzinfo=UTC)

    assert bt.consumed_this_month(at) == 0
    bt.add(10, at)
    bt.add(20, at)
    assert bt.consumed_this_month(at) == 30
    assert bt.would_exceed(5, monthly_budget=34, at=at) is True
    assert bt.would_exceed(5, monthly_budget=100, at=at) is False


# ───────────────────────── Payload parser ─────────────────────────


def _fake_payload(snapshot_ts: str, commence: str) -> dict:
    return {
        "timestamp": snapshot_ts,
        "data": [
            {
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "commence_time": commence,
                "bookmakers": [
                    {
                        "key": "pinnacle",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Arsenal", "price": 1.90},
                                    {"name": "Draw", "price": 3.60},
                                    {"name": "Chelsea", "price": 4.20},
                                ],
                            }
                        ],
                    },
                    {
                        "key": "bet365",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Arsenal", "price": 1.95},
                                    {"name": "Draw", "price": 3.50},
                                    {"name": "Chelsea", "price": 4.00},
                                ],
                            }
                        ],
                    },
                ],
            }
        ],
    }


def test_parse_snapshot_payload_h2h_consensus():
    payload = _fake_payload(
        snapshot_ts="2024-08-23T12:00:00Z",
        commence="2024-08-24T14:00:00Z",
    )
    rows = list(
        parse_snapshot_payload(payload, league_key="PL", season="2024-25", markets="h2h")
    )
    assert len(rows) == 1
    r = rows[0]
    assert r["market"] == "h2h"
    assert r["bookmaker"] == "consensus"
    assert r["n_bookmakers"] == 2
    assert abs(r["price_home"] - 1.925) < 1e-6  # median of 1.90, 1.95
    assert abs(r["price_away"] - 4.10) < 1e-6
    assert r["match_date"] == "2024-08-24"
    assert r["hours_before_kickoff"] == pytest.approx(26.0, abs=1e-3)
    assert set(SNAPSHOT_COLUMNS).issubset(r.keys())


def test_parse_snapshot_payload_leakage_guard():
    """Snapshot AT-OR-AFTER kickoff must be dropped."""
    payload = _fake_payload(
        snapshot_ts="2024-08-24T14:00:00Z",  # == kickoff
        commence="2024-08-24T14:00:00Z",
    )
    assert list(parse_snapshot_payload(payload, league_key="PL", season="2024-25", markets="h2h")) == []


# ───────────────────────── Parquet roundtrip ─────────────────────────


def test_append_rows_is_idempotent(tmp_path):
    path = tmp_path / "PL_2024-25_h2h.parquet"
    row = dict.fromkeys(SNAPSHOT_COLUMNS)
    row.update(
        league="PL",
        season="2024-25",
        match_date="2024-08-24",
        home_team="Arsenal",
        away_team="Chelsea",
        raw_home="Arsenal",
        raw_away="Chelsea",
        snapshot_ts="2024-08-23T12:00:00Z",
        kickoff_utc="2024-08-24T14:00:00Z",
        hours_before_kickoff=26.0,
        market="h2h",
        line=None,
        bookmaker="consensus",
        n_bookmakers=5,
        price_home=1.9,
        price_draw=3.5,
        price_away=4.0,
    )
    append_rows(path, [row])
    append_rows(path, [row])  # same row twice
    df = pd.read_parquet(path)
    assert len(df) == 1


# ───────────────────────── Backfill with mocked HTTP ─────────────────────────


def test_backfill_season_consumes_budget_and_caches(monkeypatch, tmp_path):
    # Redirect storage to tmp_path.
    import football_betting.scraping.odds_api_historical as mod

    snap_dir = tmp_path / "odds_snapshots"
    snap_dir.mkdir()
    monkeypatch.setattr(mod, "ODDS_SNAPSHOT_DIR", snap_dir)
    monkeypatch.setattr(
        mod, "cache_path",
        lambda league, season, markets: snap_dir / f"{league}_{season}_{markets.replace(',', '_')}.parquet",
    )

    # Dedicated budget file in tmp.
    budget = BudgetTracker(path=snap_dir / "_credits.json")

    cfg = OddsApiHistoricalConfig(
        snapshot_hours_before=(168, 24, 2),
        max_credits_per_run=30,  # allow exactly 3 calls at 10cr/call.
        request_delay_seconds=0.0,
    )
    client = OddsApiHistoricalClient(cfg=cfg, budget=budget)

    payload = _fake_payload(
        snapshot_ts="2024-08-23T12:00:00Z",
        commence="2024-08-24T14:00:00Z",
    )

    calls = {"n": 0}

    def _fake_fetch(self, league_key, ts_utc):
        calls["n"] += 1
        # Shift the snapshot_ts per call so idempotency doesn't collapse rows.
        p = {**payload, "timestamp": f"2024-08-{23 - calls['n'] % 5:02d}T12:00:00Z"}
        return p

    monkeypatch.setattr(OddsApiHistoricalClient, "fetch_snapshot", _fake_fetch)
    # Pre-set API key env just in case (no real HTTP happens).
    monkeypatch.setenv("THEODDS_HISTORICAL_API_KEY", "test-key")

    counters = client.backfill_season("PL", "2024-25", max_credits=30)
    assert counters["calls"] == 3  # capped by max_credits
    assert counters["credits"] == 30
    assert counters["aborted"] == 1
    assert counters["rows"] >= 1

    # Parquet file was written.
    out = snap_dir / "PL_2024-25_h2h.parquet"
    assert out.exists()
    df = pd.read_parquet(out)
    assert set(df.columns) == set(SNAPSHOT_COLUMNS)

    # Budget counter persisted.
    assert budget.consumed_this_month() == 30


def test_backfill_requires_api_key_when_not_dry(monkeypatch, tmp_path):
    cfg = OddsApiHistoricalConfig()
    client = OddsApiHistoricalClient(cfg=cfg)
    monkeypatch.delenv("THEODDS_HISTORICAL_API_KEY", raising=False)
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    with pytest.raises(OddsApiHistoricalError):
        client.fetch_snapshot("PL", datetime(2024, 8, 23, 12, tzinfo=UTC))


# ───────────────────────── Feature tracker ─────────────────────────


def _mk_row(home_price: float, draw_price: float, away_price: float, snap_ts: str, hours_before: float):
    return {
        "league": "PL",
        "season": "2024-25",
        "match_date": "2024-08-24",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "raw_home": "Arsenal",
        "raw_away": "Chelsea",
        "snapshot_ts": snap_ts,
        "kickoff_utc": "2024-08-24T14:00:00Z",
        "hours_before_kickoff": hours_before,
        "market": "h2h",
        "line": None,
        "bookmaker": "consensus",
        "n_bookmakers": 5,
        "price_home": home_price,
        "price_draw": draw_price,
        "price_away": away_price,
    }


def test_microstructure_tracker_features(tmp_path):
    df = pd.DataFrame(
        [
            _mk_row(2.10, 3.40, 3.30, "2024-08-17T14:00:00Z", 168.0),
            _mk_row(2.05, 3.45, 3.35, "2024-08-23T14:00:00Z", 24.0),
            _mk_row(1.80, 3.60, 3.80, "2024-08-24T12:00:00Z", 2.0),
        ]
    )
    tracker = MarketMicrostructureTracker()
    loaded = tracker.ingest_dataframe(df)
    assert loaded == 3

    feats = tracker.features_for_match("Arsenal", "Chelsea", "2024-08-24")
    assert set(feats.keys()) == set(MM_FEATURE_KEYS)
    # Opening 2.10 → closing 1.80 → home drift ≈ -14.3% → sharp down
    assert feats["mm_opening_closing_drift_h"] < -0.1
    assert feats["mm_sharp_money_direction"] == -1.0
    assert feats["mm_n_snapshots"] == 3.0
    assert feats["mm_time_to_kickoff_last_h"] == pytest.approx(2.0)
    assert feats["mm_volatility_48h"] > 0


def test_microstructure_tracker_neutral_when_empty():
    tracker = MarketMicrostructureTracker()
    feats = tracker.features_for_match("X", "Y", "2024-08-24")
    assert feats == {**dict.fromkeys(MM_FEATURE_KEYS, 0.0)}
