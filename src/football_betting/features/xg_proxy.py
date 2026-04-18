"""
Shot-based Expected Goals (xG) proxy.

Since true xG requires event data (Opta, StatsBomb, Understat) that's not
in the football-data.co.uk CSVs, we build a proxy from shots and shots on target.

Methodology:
    xG_per_match ≈ w_sot * sot_conv * SOT + w_off * off_conv * (shots - SOT)

where `sot_conv` is league-specific conversion rate. Rolling average over
last N matches gives a stable attacking-quality estimate.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from football_betting.config import LEAGUES, XgProxyConfig

if TYPE_CHECKING:
    from football_betting.data.models import Match


@dataclass(slots=True)
class ShotRecord:
    """Shot record from team's perspective."""

    league: str
    shots: int
    shots_on_target: int
    shots_against: int
    shots_against_on_target: int
    goals: int
    goals_against: int


@dataclass(slots=True)
class XgProxyTracker:
    """Tracks shot-based xG proxy per team."""

    cfg: XgProxyConfig = field(default_factory=XgProxyConfig)
    history: dict[str, deque[ShotRecord]] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=50))
    )

    # ───────────────────────── Update ─────────────────────────

    def update(self, match: Match) -> None:
        """Add shot records for both teams."""
        # Skip if shot stats missing
        if None in (
            match.home_shots,
            match.away_shots,
            match.home_shots_on_target,
            match.away_shots_on_target,
        ):
            return

        # Home team record
        self.history[match.home_team].append(
            ShotRecord(
                league=match.league,
                shots=match.home_shots or 0,  # type: ignore[arg-type]
                shots_on_target=match.home_shots_on_target or 0,  # type: ignore[arg-type]
                shots_against=match.away_shots or 0,  # type: ignore[arg-type]
                shots_against_on_target=match.away_shots_on_target or 0,  # type: ignore[arg-type]
                goals=match.home_goals,
                goals_against=match.away_goals,
            )
        )
        # Away team record (swapped)
        self.history[match.away_team].append(
            ShotRecord(
                league=match.league,
                shots=match.away_shots or 0,  # type: ignore[arg-type]
                shots_on_target=match.away_shots_on_target or 0,  # type: ignore[arg-type]
                shots_against=match.home_shots or 0,  # type: ignore[arg-type]
                shots_against_on_target=match.home_shots_on_target or 0,  # type: ignore[arg-type]
                goals=match.away_goals,
                goals_against=match.home_goals,
            )
        )

    # ───────────────────────── xG computation ─────────────────────────

    def _xg_from_shots(self, shots: int, sot: int, league_key: str) -> float:
        """Convert shots + SOT → xG using league-specific rates."""
        lg = LEAGUES[league_key]
        off_target = max(0, shots - sot)
        # Simpler / empirically better: SOT contributes most of xG
        xg_sot = sot * lg.sot_conv_rate
        xg_off = off_target * lg.shot_conv_rate * 0.3  # off-target much less valuable
        return xg_sot + xg_off

    def _weighted_xg(self, records: list[ShotRecord], is_for: bool = True) -> float:
        """Exponentially-weighted xG (or xGA)."""
        if not records:
            return 0.0

        weights = [self.cfg.decay_rate**i for i in range(len(records))][::-1]
        total_w = sum(weights)

        xg_values = []
        for rec in records:
            if is_for:
                xg = self._xg_from_shots(rec.shots, rec.shots_on_target, rec.league)
            else:
                xg = self._xg_from_shots(
                    rec.shots_against, rec.shots_against_on_target, rec.league
                )
            xg_values.append(xg)

        return sum(w * x for w, x in zip(weights, xg_values)) / total_w

    # ───────────────────────── Public queries ─────────────────────────

    def features_for_match(self, home_team: str, away_team: str) -> dict[str, float]:
        h_recs = list(self.history.get(home_team, []))[-self.cfg.window_size:]
        a_recs = list(self.history.get(away_team, []))[-self.cfg.window_size:]

        h_xg_for = self._weighted_xg(h_recs, is_for=True)
        h_xg_against = self._weighted_xg(h_recs, is_for=False)
        a_xg_for = self._weighted_xg(a_recs, is_for=True)
        a_xg_against = self._weighted_xg(a_recs, is_for=False)

        # Conversion ratios (finishing quality)
        h_conv = self._conversion_rate(h_recs, goals_over_xg=True)
        a_conv = self._conversion_rate(a_recs, goals_over_xg=True)

        return {
            "xg_home_for": h_xg_for,
            "xg_home_against": h_xg_against,
            "xg_home_diff": h_xg_for - h_xg_against,
            "xg_home_conv": h_conv,
            "xg_away_for": a_xg_for,
            "xg_away_against": a_xg_against,
            "xg_away_diff": a_xg_for - a_xg_against,
            "xg_away_conv": a_conv,
            "xg_matchup_diff": (h_xg_for - a_xg_against) - (a_xg_for - h_xg_against),
        }

    def _conversion_rate(
        self, records: list[ShotRecord], goals_over_xg: bool = True
    ) -> float:
        """Actual goals / expected goals — finishing quality."""
        if not records:
            return 1.0  # neutral
        total_goals = sum(r.goals for r in records)
        total_xg = sum(
            self._xg_from_shots(r.shots, r.shots_on_target, r.league) for r in records
        )
        if total_xg == 0:
            return 1.0
        return total_goals / total_xg if goals_over_xg else total_xg / max(total_goals, 1)
