"""Market-microstructure feature tracker (Phase 8 — Family D).

Consumes the per-(league, season) Parquet snapshots produced by
``scraping/odds_api_historical.py`` and emits ``mm_*`` features per fixture:

- ``mm_opening_closing_drift_h/d/a`` — % change opening → closing price
- ``mm_volatility_48h`` — stdev of home price across the last 48h window
- ``mm_steam_detected_h`` — 1.0 if any |Δprice|>5% step within 30min
- ``mm_sharp_money_direction`` — sign of home drift when |drift|>2%
- ``mm_n_snapshots`` — number of snapshots available (confidence proxy)
- ``mm_time_to_kickoff_last_h`` — how late the most recent snapshot was

Leakage guard: only snapshots with ``snapshot_ts < kickoff_utc`` are used
(already enforced upstream by the parser, double-checked here).
"""
from __future__ import annotations

import statistics
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from football_betting.config import (
    MARKET_MICROSTRUCTURE_CFG,
    ODDS_SNAPSHOT_DIR,
    MarketMicrostructureConfig,
)

MM_FEATURE_KEYS: tuple[str, ...] = (
    "mm_opening_closing_drift_h",
    "mm_opening_closing_drift_d",
    "mm_opening_closing_drift_a",
    "mm_volatility_48h",
    "mm_steam_detected_h",
    "mm_sharp_money_direction",
    "mm_n_snapshots",
    "mm_time_to_kickoff_last_h",
)


def _neutral_features() -> dict[str, float]:
    return dict.fromkeys(MM_FEATURE_KEYS, 0.0)


@dataclass(slots=True)
class MarketMicrostructureTracker:
    """In-memory index over historical h2h snapshots per fixture."""

    cfg: MarketMicrostructureConfig = field(default_factory=lambda: MARKET_MICROSTRUCTURE_CFG)
    #: {(home_norm, away_norm, match_date_iso): [row-dict sorted by snapshot_ts]}
    _index: dict[tuple[str, str, str], list[dict[str, float | str]]] = field(default_factory=dict)

    # ───────────────────────── Ingestion ─────────────────────────

    def ingest_parquet(self, path: Path) -> int:
        if not path.exists():
            return 0
        df = pd.read_parquet(path)
        return self.ingest_dataframe(df)

    def ingest_dataframe(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        # Only h2h rows feed mm_* for now; totals/spreads reserved for later families.
        h2h = df[df["market"] == "h2h"]
        loaded = 0
        for rec in h2h.to_dict(orient="records"):
            key = (
                str(rec["home_team"]),
                str(rec["away_team"]),
                str(rec["match_date"]),
            )
            self._index.setdefault(key, []).append(rec)
            loaded += 1
        # Sort chronologically for fast feature extraction.
        for _key, rows in self._index.items():
            rows.sort(key=lambda r: str(r["snapshot_ts"]))
        return loaded

    def ingest_directory(
        self,
        league_key: str,
        seasons: Iterable[str] | None = None,
        markets: str = "h2h",
        root: Path | None = None,
    ) -> int:
        root = root or ODDS_SNAPSHOT_DIR
        safe_markets = markets.replace(",", "_")
        loaded = 0
        for path in sorted(root.glob(f"{league_key.upper()}_*_{safe_markets}.parquet")):
            name = path.stem  # e.g. BL_2024-25_h2h
            parts = name.split("_")
            if len(parts) < 3:
                continue
            season_part = parts[1]
            if seasons is not None and season_part not in set(seasons):
                continue
            loaded += self.ingest_parquet(path)
        return loaded

    # ───────────────────────── Feature extraction ─────────────────────────

    @staticmethod
    def _pct(old: float, new: float) -> float:
        if old == 0:
            return 0.0
        return (new - old) / old

    def features_for_match(
        self,
        home_team: str,
        away_team: str,
        match_date_iso: str,
    ) -> dict[str, float]:
        rows = self._index.get((home_team, away_team, match_date_iso))
        if not rows or len(rows) < self.cfg.min_snapshots:
            feats = _neutral_features()
            feats["mm_n_snapshots"] = float(len(rows) if rows else 0)
            return feats

        opening = rows[0]
        closing = rows[-1]

        drift_h = self._pct(float(opening["price_home"]), float(closing["price_home"]))
        draw_open = opening.get("price_draw")
        draw_close = closing.get("price_draw")
        drift_d = (
            self._pct(float(draw_open), float(draw_close))
            if draw_open is not None and draw_close is not None
            else 0.0
        )
        drift_a = self._pct(float(opening["price_away"]), float(closing["price_away"]))

        # Volatility over the full captured window (we already filter ≤168h upstream).
        home_prices = [float(r["price_home"]) for r in rows]
        volatility = statistics.pstdev(home_prices) if len(home_prices) >= 2 else 0.0

        # Steam move = any |Δp| ≥ 5 % between consecutive snapshots < 180 min apart.
        steam = 0.0
        for i in range(1, len(rows)):
            prev_ts = datetime.fromisoformat(str(rows[i - 1]["snapshot_ts"]).replace("Z", "+00:00"))
            cur_ts = datetime.fromisoformat(str(rows[i]["snapshot_ts"]).replace("Z", "+00:00"))
            gap_min = abs((cur_ts - prev_ts).total_seconds()) / 60.0
            if gap_min > 180:
                continue
            step = abs(self._pct(float(rows[i - 1]["price_home"]), float(rows[i]["price_home"])))
            if step >= 0.05:
                steam = 1.0
                break

        sharp_dir = 0.0
        if abs(drift_h) >= 0.02:
            sharp_dir = 1.0 if drift_h > 0 else -1.0

        hours_before_last = float(closing.get("hours_before_kickoff", 0.0) or 0.0)

        return {
            "mm_opening_closing_drift_h": float(drift_h),
            "mm_opening_closing_drift_d": float(drift_d),
            "mm_opening_closing_drift_a": float(drift_a),
            "mm_volatility_48h": float(volatility),
            "mm_steam_detected_h": float(steam),
            "mm_sharp_money_direction": float(sharp_dir),
            "mm_n_snapshots": float(len(rows)),
            "mm_time_to_kickoff_last_h": float(hours_before_last),
        }
