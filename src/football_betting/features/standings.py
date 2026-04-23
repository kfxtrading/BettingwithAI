"""Season-aware league-standings features.

Captures the *motivational* and *season-progress* signals the feature set
previously lacked. The calibration audit (Phase 4) showed that for leagues
where most matches cluster in the 0.45 confidence bin (e.g. Championship),
the model cannot discriminate motivated from safe teams. This tracker
provides season-to-date points, goal-difference, home/away split PPG,
approximate table rank and season-progress fraction — all leakage-safe
because trackers are only updated AFTER a match's features are built.

Feature keys emitted per fixture (prefix ``standings_``):

* ``home_pts`` / ``away_pts``       — season points so far
* ``home_gd``  / ``away_gd``        — season goal difference so far
* ``home_gp``  / ``away_gp``        — season games played
* ``home_ppg`` / ``away_ppg``       — points per game this season
* ``home_home_ppg`` / ``away_away_ppg`` — split PPG (home at home, away at away)
* ``home_rank`` / ``away_rank``     — ordinal rank within league season
* ``pts_diff`` / ``gd_diff``        — home − away asymmetry
* ``matchday_pct``                  — season progress (0..1, relative to max gp)
* ``is_late_season``                — 1 if matchday_pct ≥ 0.75 else 0
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from football_betting.data.models import Match


@dataclass(slots=True)
class _TeamSeasonRecord:
    points: int = 0
    gd: int = 0
    games_played: int = 0
    home_points: int = 0
    home_games: int = 0
    away_points: int = 0
    away_games: int = 0

    def ppg(self) -> float:
        return self.points / self.games_played if self.games_played else 0.0

    def home_ppg(self) -> float:
        return self.home_points / self.home_games if self.home_games else 0.0

    def away_ppg(self) -> float:
        return self.away_points / self.away_games if self.away_games else 0.0


@dataclass(slots=True)
class SeasonStandingsTracker:
    """Per-(league, season) league-table tracker."""

    # Keyed by (league, season) → team → record
    _tables: dict[tuple[str, str], dict[str, _TeamSeasonRecord]] = field(
        default_factory=lambda: defaultdict(dict)
    )

    # ───────────────────────── Update ─────────────────────────

    def update(self, match: Match) -> None:
        """Register a completed match to both teams' season rows."""
        key = (match.league, match.season)
        table = self._tables[key]
        home_rec = table.setdefault(match.home_team, _TeamSeasonRecord())
        away_rec = table.setdefault(match.away_team, _TeamSeasonRecord())

        hg, ag = match.home_goals, match.away_goals
        if hg > ag:
            hp, ap = 3, 0
        elif hg < ag:
            hp, ap = 0, 3
        else:
            hp = ap = 1

        home_rec.points += hp
        home_rec.home_points += hp
        home_rec.gd += hg - ag
        home_rec.games_played += 1
        home_rec.home_games += 1

        away_rec.points += ap
        away_rec.away_points += ap
        away_rec.gd += ag - hg
        away_rec.games_played += 1
        away_rec.away_games += 1

    # ───────────────────────── Queries ─────────────────────────

    def features_for_match(
        self,
        home_team: str,
        away_team: str,
        league_key: str,
        season: str | None,
    ) -> dict[str, float]:
        """Build the ``standings_*`` feature block for one fixture.

        When the team has not yet played this season (e.g. matchday 1) or
        no ``season`` is supplied, zero/neutral fill is returned so the
        feature schema stays stable.
        """
        if not season:
            return self._empty()

        table = self._tables.get((league_key, season), {})
        home_rec = table.get(home_team, _TeamSeasonRecord())
        away_rec = table.get(away_team, _TeamSeasonRecord())

        # Ordinal ranks (1 = best). Ties broken by GD then alphabetical.
        ranking = sorted(
            table.items(),
            key=lambda kv: (-kv[1].points, -kv[1].gd, kv[0]),
        )
        pos_map = {team: i + 1 for i, (team, _) in enumerate(ranking)}
        home_rank = float(pos_map.get(home_team, 0) or 0)
        away_rank = float(pos_map.get(away_team, 0) or 0)

        max_gp = max((r.games_played for r in table.values()), default=0)
        matchday_pct = max_gp / 38.0 if max_gp else 0.0  # 38 ≈ typical season length
        matchday_pct = min(matchday_pct, 1.0)

        return {
            "standings_home_pts": float(home_rec.points),
            "standings_away_pts": float(away_rec.points),
            "standings_pts_diff": float(home_rec.points - away_rec.points),
            "standings_home_gd": float(home_rec.gd),
            "standings_away_gd": float(away_rec.gd),
            "standings_gd_diff": float(home_rec.gd - away_rec.gd),
            "standings_home_gp": float(home_rec.games_played),
            "standings_away_gp": float(away_rec.games_played),
            "standings_home_ppg": home_rec.ppg(),
            "standings_away_ppg": away_rec.ppg(),
            "standings_home_home_ppg": home_rec.home_ppg(),
            "standings_away_away_ppg": away_rec.away_ppg(),
            "standings_home_rank": home_rank,
            "standings_away_rank": away_rank,
            "standings_rank_diff": away_rank - home_rank,  # + means home better placed
            "standings_matchday_pct": matchday_pct,
            "standings_is_late_season": 1.0 if matchday_pct >= 0.75 else 0.0,
        }

    @staticmethod
    def _empty() -> dict[str, float]:
        return {
            "standings_home_pts": 0.0,
            "standings_away_pts": 0.0,
            "standings_pts_diff": 0.0,
            "standings_home_gd": 0.0,
            "standings_away_gd": 0.0,
            "standings_gd_diff": 0.0,
            "standings_home_gp": 0.0,
            "standings_away_gp": 0.0,
            "standings_home_ppg": 0.0,
            "standings_away_ppg": 0.0,
            "standings_home_home_ppg": 0.0,
            "standings_away_away_ppg": 0.0,
            "standings_home_rank": 0.0,
            "standings_away_rank": 0.0,
            "standings_rank_diff": 0.0,
            "standings_matchday_pct": 0.0,
            "standings_is_late_season": 0.0,
        }

    # ───────────────────────── Maintenance ─────────────────────────

    def reset(self) -> None:
        self._tables.clear()
