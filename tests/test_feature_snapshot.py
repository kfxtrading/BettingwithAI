"""Tests for the Parquet feature-snapshot store (Phase 4)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from football_betting.tracking.feature_snapshot import FeatureSnapshotStore


@pytest.fixture
def store(tmp_path: Path) -> FeatureSnapshotStore:
    return FeatureSnapshotStore(base_dir=tmp_path)


def _feats(n: int = 5) -> dict[str, float]:
    return {f"f{i}": float(i * 1.1) for i in range(n)}


def test_save_and_load_latest(store: FeatureSnapshotStore) -> None:
    store.save(
        league="BL",
        match_date=date(2024, 5, 18),
        home_team="Bayern",
        away_team="Dortmund",
        features=_feats(),
    )
    got = store.load_asof("BL", date(2024, 5, 18), "Bayern", "Dortmund")
    assert got is not None
    assert got == _feats()


def test_empty_features_raises(store: FeatureSnapshotStore) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        store.save(
            league="BL",
            match_date=date(2024, 5, 18),
            home_team="H",
            away_team="A",
            features={},
        )


def test_load_missing_returns_none(store: FeatureSnapshotStore) -> None:
    assert store.load_asof("BL", date(2024, 5, 18), "Nope", "None") is None


def test_asof_selects_most_recent_at_or_before_cutoff(store: FeatureSnapshotStore) -> None:
    d = date(2024, 5, 18)
    t_early = datetime(2024, 5, 15, 12, 0, tzinfo=UTC)
    t_mid = datetime(2024, 5, 17, 12, 0, tzinfo=UTC)
    t_late = datetime(2024, 5, 18, 12, 0, tzinfo=UTC)

    store.save("BL", d, "H", "A", {"x": 1.0, "y": 2.0}, as_of=t_early)
    store.save("BL", d, "H", "A", {"x": 10.0, "y": 20.0}, as_of=t_mid)
    store.save("BL", d, "H", "A", {"x": 100.0, "y": 200.0}, as_of=t_late)

    # Latest overall
    latest = store.load_asof("BL", d, "H", "A")
    assert latest is not None and latest["x"] == pytest.approx(100.0)

    # As-of the mid timestamp → must return mid (not late)
    mid = store.load_asof("BL", d, "H", "A", as_of=t_mid)
    assert mid is not None and mid["x"] == pytest.approx(10.0)

    # As-of before any snapshot → None
    before = store.load_asof(
        "BL",
        d,
        "H",
        "A",
        as_of=t_early - timedelta(days=1),
    )
    assert before is None


def test_partition_created_per_month(store: FeatureSnapshotStore) -> None:
    store.save("BL", date(2024, 5, 18), "H1", "A1", {"f": 1.0})
    store.save("BL", date(2024, 6, 1), "H2", "A2", {"f": 2.0})

    # Two partitions exist
    may = store.load_partition("BL", date(2024, 5, 18))
    jun = store.load_partition("BL", date(2024, 6, 1))
    assert not may.empty and len(may) == 1
    assert not jun.empty and len(jun) == 1
    # Files on disk
    root = store.root / "BL"
    files = {p.name for p in root.glob("*.parquet")}
    assert files == {"2024-05.parquet", "2024-06.parquet"}


def test_list_snapshots_sorted(store: FeatureSnapshotStore) -> None:
    d = date(2024, 5, 18)
    t1 = datetime(2024, 5, 18, 10, tzinfo=UTC)
    t2 = datetime(2024, 5, 18, 12, tzinfo=UTC)
    t3 = datetime(2024, 5, 18, 15, tzinfo=UTC)
    # Insert out of order
    store.save("BL", d, "H", "A", {"f": 1.0}, as_of=t2)
    store.save("BL", d, "H", "A", {"f": 2.0}, as_of=t1)
    store.save("BL", d, "H", "A", {"f": 3.0}, as_of=t3)
    out = store.list_snapshots("BL", d, "H", "A")
    assert out == [t1, t2, t3]


def test_multi_fixture_isolation(store: FeatureSnapshotStore) -> None:
    d = date(2024, 5, 18)
    store.save("BL", d, "H1", "A1", {"f": 1.0})
    store.save("BL", d, "H2", "A2", {"f": 99.0})

    a = store.load_asof("BL", d, "H1", "A1")
    b = store.load_asof("BL", d, "H2", "A2")
    assert a == {"f": 1.0}
    assert b == {"f": 99.0}


def test_save_many_returns_touched_partitions(store: FeatureSnapshotStore) -> None:
    records = [
        {
            "match_date": date(2024, 5, 1),
            "home_team": "H",
            "away_team": "A",
            "features": {"f": 1.0},
        },
        {
            "match_date": date(2024, 5, 2),
            "home_team": "H",
            "away_team": "A",
            "features": {"f": 2.0},
        },
        {
            "match_date": date(2024, 6, 3),
            "home_team": "H",
            "away_team": "A",
            "features": {"f": 3.0},
        },
    ]
    paths = store.save_many("BL", records)
    assert len(paths) == 2  # two unique monthly partitions
