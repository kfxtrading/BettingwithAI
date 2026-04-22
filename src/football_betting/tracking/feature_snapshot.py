"""Parquet-backed as-of feature-snapshot store (Phase 4).

Purpose
-------
Persist the exact ``(features, odds, metadata)`` snapshot that was used to
produce a prediction at a given wall-clock time. This decouples feature
re-engineering from backtest reproducibility: once a snapshot is saved,
future pipeline changes cannot silently alter historical predictions.

Storage layout
--------------
``data/processed/feature_snapshots/{league}/{yyyy-mm}.parquet``

Each row represents one ``(match, as_of_timestamp)`` feature vector:

    league            str
    match_date        date
    home_team         str
    away_team         str
    as_of             timestamp[ns, tz=UTC]
    feature_name      str (the flat feature key)
    feature_value     float64

Long-format (one row per feature) keeps the schema stable across feature
set revisions — no ALTER/migrate headaches when the feature count grows.

Queries
-------
* ``save_snapshot(...)`` — append one match's features at one as-of time.
* ``load_asof(league, match_date, home, away, as_of=None)`` — retrieve
  the most recent snapshot at or before ``as_of`` (``None`` → latest).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from football_betting.config import DATA_DIR

_SNAPSHOT_DIR = DATA_DIR / "processed" / "feature_snapshots"

_SCHEMA_COLS: tuple[str, ...] = (
    "league",
    "match_date",
    "home_team",
    "away_team",
    "as_of",
    "feature_name",
    "feature_value",
)


def _month_partition(match_date: date) -> str:
    return f"{match_date.year:04d}-{match_date.month:02d}"


def _partition_path(league: str, match_date: date, base: Path | None = None) -> Path:
    root = base or _SNAPSHOT_DIR
    return root / league / f"{_month_partition(match_date)}.parquet"


@dataclass(slots=True)
class FeatureSnapshotStore:
    """Parquet-backed feature snapshot store with monthly partitions.

    Pass ``base_dir`` explicitly in tests to isolate writes from the main
    ``data/processed/feature_snapshots/`` tree.
    """

    base_dir: Path | None = None

    @property
    def root(self) -> Path:
        return self.base_dir or _SNAPSHOT_DIR

    # ───────────────────────── Write ─────────────────────────

    def save(
        self,
        league: str,
        match_date: date,
        home_team: str,
        away_team: str,
        features: dict[str, float],
        as_of: datetime | None = None,
    ) -> Path:
        """Append one feature snapshot. Creates the monthly Parquet file if absent."""
        if not features:
            raise ValueError("features must be non-empty")
        ts = as_of or datetime.now(UTC)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)

        rows = [
            {
                "league": league,
                "match_date": pd.Timestamp(match_date),
                "home_team": home_team,
                "away_team": away_team,
                "as_of": pd.Timestamp(ts),
                "feature_name": str(k),
                "feature_value": float(v),
            }
            for k, v in features.items()
        ]
        new_df = pd.DataFrame(rows, columns=list(_SCHEMA_COLS))

        path = _partition_path(league, match_date, self.base_dir)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            existing = pd.read_parquet(path)
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df

        combined.to_parquet(path, engine="pyarrow", index=False)
        return path

    def save_many(
        self,
        league: str,
        records: list[dict[str, Any]],
    ) -> list[Path]:
        """Batch-save multiple snapshots. Each record must have the keys
        ``match_date``, ``home_team``, ``away_team``, ``features`` and
        optionally ``as_of``. Returns the set of touched partition paths.
        """
        touched: set[Path] = set()
        for rec in records:
            p = self.save(
                league=league,
                match_date=rec["match_date"],
                home_team=rec["home_team"],
                away_team=rec["away_team"],
                features=rec["features"],
                as_of=rec.get("as_of"),
            )
            touched.add(p)
        return sorted(touched)

    # ───────────────────────── Read ─────────────────────────

    def load_partition(self, league: str, match_date: date) -> pd.DataFrame:
        path = _partition_path(league, match_date, self.base_dir)
        if not path.exists():
            return pd.DataFrame(columns=list(_SCHEMA_COLS))
        return pd.read_parquet(path)

    def load_asof(
        self,
        league: str,
        match_date: date,
        home_team: str,
        away_team: str,
        as_of: datetime | None = None,
    ) -> dict[str, float] | None:
        """Return the feature dict captured at or before ``as_of`` (latest if None)."""
        df = self.load_partition(league, match_date)
        if df.empty:
            return None
        mask = (
            (df["league"] == league)
            & (df["match_date"] == pd.Timestamp(match_date))
            & (df["home_team"] == home_team)
            & (df["away_team"] == away_team)
        )
        if as_of is not None:
            ts = as_of if as_of.tzinfo else as_of.replace(tzinfo=UTC)
            mask &= df["as_of"] <= pd.Timestamp(ts)
        sub = df[mask]
        if sub.empty:
            return None
        latest_ts = sub["as_of"].max()
        row = sub[sub["as_of"] == latest_ts]
        return dict(zip(row["feature_name"].tolist(), row["feature_value"].tolist()))

    def list_snapshots(
        self,
        league: str,
        match_date: date,
        home_team: str,
        away_team: str,
    ) -> list[datetime]:
        """Return the list of ``as_of`` timestamps for a single fixture (sorted asc)."""
        df = self.load_partition(league, match_date)
        if df.empty:
            return []
        sub = df[
            (df["league"] == league)
            & (df["match_date"] == pd.Timestamp(match_date))
            & (df["home_team"] == home_team)
            & (df["away_team"] == away_team)
        ]
        return sorted(pd.to_datetime(sub["as_of"]).dt.to_pydatetime().tolist())


__all__ = [
    "FeatureSnapshotStore",
]
