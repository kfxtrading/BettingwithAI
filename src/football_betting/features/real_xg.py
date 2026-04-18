"""
Real xG tracker — uses Sofascore-sourced xG values when available.

Differs from xg_proxy.py in that the xG values are the actual Opta/Sofascore
xG numbers, not a shot-based approximation. Also adds xG-vs-goals delta as
a "finishing quality / luck" indicator.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from football_betting.config import RealXgConfig


@dataclass(slots=True)
class XgRecord:
    """One team's xG data for a single match."""

    xg_for: float
    xg_against: float
    goals_for: int
    goals_against: int
    was_home: bool
    big_chances_for: int | None = None
    big_chances_against: int | None = None


@dataclass(slots=True)
class RealXgTracker:
    """Rolling real-xG tracker with exponential decay."""

    cfg: RealXgConfig = field(default_factory=RealXgConfig)
    history: dict[str, deque[XgRecord]] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=50))
    )

    # ───────────────────────── Ingestion ─────────────────────────

    def ingest_sofascore_match(self, match_dict: dict) -> None:
        """Add a Sofascore-scraped match to tracker (both teams' records)."""
        home_xg = match_dict.get("home_xg")
        away_xg = match_dict.get("away_xg")
        home_goals = match_dict.get("home_goals")
        away_goals = match_dict.get("away_goals")

        # Skip if xG missing
        if home_xg is None or away_xg is None or home_goals is None or away_goals is None:
            return

        home_team = match_dict["home_team"]
        away_team = match_dict["away_team"]

        self.history[home_team].append(
            XgRecord(
                xg_for=float(home_xg),
                xg_against=float(away_xg),
                goals_for=int(home_goals),
                goals_against=int(away_goals),
                was_home=True,
                big_chances_for=match_dict.get("home_big_chances"),
                big_chances_against=match_dict.get("away_big_chances"),
            )
        )
        self.history[away_team].append(
            XgRecord(
                xg_for=float(away_xg),
                xg_against=float(home_xg),
                goals_for=int(away_goals),
                goals_against=int(home_goals),
                was_home=False,
                big_chances_for=match_dict.get("away_big_chances"),
                big_chances_against=match_dict.get("home_big_chances"),
            )
        )

    def ingest_many(self, match_dicts: list[dict]) -> int:
        """Batch ingest; returns count of successfully ingested matches."""
        before = sum(len(v) for v in self.history.values())
        for m in match_dicts:
            self.ingest_sofascore_match(m)
        after = sum(len(v) for v in self.history.values())
        return (after - before) // 2  # each match adds 2 records

    # ───────────────────────── Weighted aggregation ─────────────────────────

    def _weighted_mean(self, records: list[XgRecord], getter) -> float:
        if not records:
            return 0.0
        weights = [self.cfg.decay_rate**i for i in range(len(records))][::-1]
        total_w = sum(weights)
        return sum(w * getter(r) for w, r in zip(weights, records)) / total_w

    # ───────────────────────── Public queries ─────────────────────────

    def team_has_data(self, team: str) -> bool:
        return team in self.history and len(self.history[team]) > 0

    def features_for_match(self, home_team: str, away_team: str) -> dict[str, float]:
        """Feature vector for a match."""
        h_all = list(self.history.get(home_team, []))[-self.cfg.window_size:]
        a_all = list(self.history.get(away_team, []))[-self.cfg.window_size:]

        h_home_only = [r for r in h_all if r.was_home]
        a_away_only = [r for r in a_all if not r.was_home]

        # Overall rolling xG
        h_xg_for = self._weighted_mean(h_all, lambda r: r.xg_for)
        h_xg_against = self._weighted_mean(h_all, lambda r: r.xg_against)
        a_xg_for = self._weighted_mean(a_all, lambda r: r.xg_for)
        a_xg_against = self._weighted_mean(a_all, lambda r: r.xg_against)

        # Home-specific / away-specific
        h_home_xg_for = self._weighted_mean(h_home_only, lambda r: r.xg_for)
        a_away_xg_for = self._weighted_mean(a_away_only, lambda r: r.xg_for)

        # Finishing quality: actual goals / expected goals
        h_g_total = sum(r.goals_for for r in h_all)
        h_xg_total = sum(r.xg_for for r in h_all)
        h_finishing = h_g_total / h_xg_total if h_xg_total > 0 else 1.0

        a_g_total = sum(r.goals_for for r in a_all)
        a_xg_total = sum(r.xg_for for r in a_all)
        a_finishing = a_g_total / a_xg_total if a_xg_total > 0 else 1.0

        # Big chances if available
        h_bc = self._weighted_mean(
            h_all, lambda r: float(r.big_chances_for or 0)
        )
        a_bc = self._weighted_mean(
            a_all, lambda r: float(r.big_chances_for or 0)
        )

        return {
            "real_xg_home_for": h_xg_for,
            "real_xg_home_against": h_xg_against,
            "real_xg_home_diff": h_xg_for - h_xg_against,
            "real_xg_home_at_home_for": h_home_xg_for,
            "real_xg_home_finishing": h_finishing,
            "real_xg_home_big_chances": h_bc,
            "real_xg_away_for": a_xg_for,
            "real_xg_away_against": a_xg_against,
            "real_xg_away_diff": a_xg_for - a_xg_against,
            "real_xg_away_at_away_for": a_away_xg_for,
            "real_xg_away_finishing": a_finishing,
            "real_xg_away_big_chances": a_bc,
            "real_xg_matchup_diff": (h_xg_for - a_xg_against) - (a_xg_for - h_xg_against),
        }
