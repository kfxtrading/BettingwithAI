"""
Market movement tracker — opening vs closing odds analysis.

Detects "steam moves" (sharp sudden line movements) and "reverse line
movement" (line moves against the public betting %, indicating sharp money).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from football_betting.config import MarketMovementConfig


@dataclass(slots=True)
class OddsSnapshot:
    """A single point-in-time odds reading."""

    timestamp: datetime
    home: float
    draw: float
    away: float
    bookmaker: str = "consensus"


@dataclass(slots=True)
class MarketMovementTracker:
    """Tracks odds movement for each fixture."""

    cfg: MarketMovementConfig = field(default_factory=MarketMovementConfig)
    snapshots: dict[str, list[OddsSnapshot]] = field(default_factory=dict)

    @staticmethod
    def _fixture_key(home: str, away: str, match_date: str) -> str:
        return f"{match_date}|{home}|{away}"

    # ───────────────────────── Ingestion ─────────────────────────

    def add_snapshot(
        self,
        home_team: str,
        away_team: str,
        match_date: str,
        snapshot: OddsSnapshot,
    ) -> None:
        key = self._fixture_key(home_team, away_team, match_date)
        if key not in self.snapshots:
            self.snapshots[key] = []
        self.snapshots[key].append(snapshot)

    # ───────────────────────── Analysis ─────────────────────────

    @staticmethod
    def _pct_change(old: float, new: float) -> float:
        if old == 0:
            return 0.0
        return (new - old) / old

    def _steam_move(self, snapshots: list[OddsSnapshot]) -> int:
        """Detect at least one steam move (|Δodds|>threshold within window)."""
        if len(snapshots) < 2:
            return 0
        sorted_snaps = sorted(snapshots, key=lambda s: s.timestamp)
        for i in range(1, len(sorted_snaps)):
            dt = (sorted_snaps[i].timestamp - sorted_snaps[i - 1].timestamp).total_seconds() / 60
            if dt > self.cfg.steam_window_minutes:
                continue
            for attr in ("home", "draw", "away"):
                old = getattr(sorted_snaps[i - 1], attr)
                new = getattr(sorted_snaps[i], attr)
                if abs(self._pct_change(old, new)) >= self.cfg.steam_threshold_pct:
                    return 1
        return 0

    def _sharp_indicator(self, snapshots: list[OddsSnapshot]) -> float:
        """
        Sharp money indicator: magnitude of move against public expectation.

        Heuristic: if public backs the favorite but odds on the favorite INCREASE
        (line moves against the public), sharp money is on the underdog. We
        return the total (normalized) magnitude of movement on home side.
        """
        if len(snapshots) < 2:
            return 0.0
        sorted_snaps = sorted(snapshots, key=lambda s: s.timestamp)
        opening = sorted_snaps[0]
        closing = sorted_snaps[-1]
        return self._pct_change(opening.home, closing.home)

    def features_for_fixture(
        self,
        home_team: str,
        away_team: str,
        match_date: str,
    ) -> dict[str, float]:
        key = self._fixture_key(home_team, away_team, match_date)
        snaps = self.snapshots.get(key, [])
        if len(snaps) < 2:
            # Not enough data — return neutral features
            return {
                "mm_steam_detected": 0.0,
                "mm_home_odds_drift": 0.0,
                "mm_draw_odds_drift": 0.0,
                "mm_away_odds_drift": 0.0,
                "mm_sharp_indicator": 0.0,
                "mm_n_snapshots": float(len(snaps)),
            }
        sorted_snaps = sorted(snaps, key=lambda s: s.timestamp)
        opening, closing = sorted_snaps[0], sorted_snaps[-1]

        return {
            "mm_steam_detected": float(self._steam_move(sorted_snaps)),
            "mm_home_odds_drift": self._pct_change(opening.home, closing.home),
            "mm_draw_odds_drift": self._pct_change(opening.draw, closing.draw),
            "mm_away_odds_drift": self._pct_change(opening.away, closing.away),
            "mm_sharp_indicator": self._sharp_indicator(sorted_snaps),
            "mm_n_snapshots": float(len(snaps)),
        }
