"""
Dynamic per-team home advantage.

Some teams have unusually strong (e.g. Atlético Madrid at Metropolitano)
or weak (e.g. teams playing in temporary stadiums) home advantage. This
tracker computes a rolling per-team HA factor from recent home vs. away
goal differentials, falling back to the league average when sample size
is insufficient.
"""
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from football_betting.config import LEAGUES, HomeAdvantageConfig

if TYPE_CHECKING:
    from football_betting.data.models import Match


GHOST_PERIODS: tuple[tuple[date, date], ...] = (
    (date(2020, 3, 1), date(2021, 6, 30)),
    (date(2021, 8, 1), date(2021, 12, 31)),
)


def _in_ghost_period(
    match_date: date,
    periods: Sequence[tuple[date, date]] = GHOST_PERIODS,
) -> bool:
    return any(start <= match_date <= end for start, end in periods)


def dynamic_home_advantage(
    match_date: date,
    base: float,
    ghost_factor: float = 0.35,
    periods: Sequence[tuple[date, date]] = GHOST_PERIODS,
) -> float:
    """Apply COVID ghost-games correction to a base home-advantage value.

    During empty-stadium periods (no crowd support), home advantage was
    empirically ~0.3x-0.4x of normal. Outside these periods returns ``base``.
    """
    if _in_ghost_period(match_date, periods):
        return base * ghost_factor
    return base


@dataclass(slots=True)
class HomeAdvantageTracker:
    """Per-team dynamic home-advantage estimation."""

    cfg: HomeAdvantageConfig = field(default_factory=HomeAdvantageConfig)
    home_gd: dict[str, deque[float]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    away_gd: dict[str, deque[float]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    league_of_team: dict[str, str] = field(default_factory=dict)

    def update(self, match: Match) -> None:
        h, a = match.home_team, match.away_team
        gd_home_perspective = float(match.home_goals - match.away_goals)
        gd_away_perspective = float(match.away_goals - match.home_goals)

        # Track league for fallback lookup
        self.league_of_team[h] = match.league
        self.league_of_team[a] = match.league

        # Maintain rolling window
        w = self.cfg.window_games
        for team, dq, gd in [
            (h, self.home_gd[h], gd_home_perspective),
            (a, self.away_gd[a], gd_away_perspective),
        ]:
            dq.append(gd)
            while len(dq) > w:
                dq.popleft()

    def team_home_advantage(self, team: str, match_date: date | None = None) -> float:
        """Estimate team's specific home advantage (goals) vs. league avg.

        When ``match_date`` falls inside a configured COVID ghost-games period
        the resulting HA is multiplied by ``cfg.ghost_factor`` to account for
        the loss of crowd support in empty stadiums.
        """
        home_games = list(self.home_gd.get(team, []))
        away_games = list(self.away_gd.get(team, []))
        league_key = self.league_of_team.get(team)

        # Default to league-avg if insufficient data
        if len(home_games) < self.cfg.min_home_games or league_key is None:
            base = LEAGUES[league_key].home_advantage if league_key else 0.35
            return self._apply_ghost(base, match_date)

        home_avg_gd = sum(home_games) / len(home_games)

        if not away_games:
            return self._apply_ghost(max(0.0, home_avg_gd), match_date)  # fallback

        away_avg_gd = sum(away_games) / len(away_games)

        # Team's HA is how much better they do at home than away
        team_ha = (home_avg_gd - away_avg_gd) / 2  # divide by 2 to convert to one-sided

        # Blend with league default (shrinkage toward prior)
        n = min(len(home_games), self.cfg.window_games)
        blend_weight = n / self.cfg.window_games
        league_default = LEAGUES[league_key].home_advantage

        ha = blend_weight * team_ha + (1 - blend_weight) * league_default
        return self._apply_ghost(ha, match_date)

    def _apply_ghost(self, base: float, match_date: date | None) -> float:
        if match_date is None:
            return base
        return dynamic_home_advantage(
            match_date,
            base,
            ghost_factor=self.cfg.ghost_factor,
            periods=self.cfg.ghost_periods,
        )

    def features_for_match(
        self,
        home_team: str,
        away_team: str,
        match_date: date | None = None,
    ) -> dict[str, float]:
        h_ha = self.team_home_advantage(home_team, match_date=match_date)
        league_default = LEAGUES.get(
            self.league_of_team.get(home_team, "PL"),
            LEAGUES["PL"],
        ).home_advantage
        if match_date is not None:
            league_default = dynamic_home_advantage(
                match_date,
                league_default,
                ghost_factor=self.cfg.ghost_factor,
                periods=self.cfg.ghost_periods,
            )
        return {
            "home_team_ha": h_ha,
            "home_team_ha_vs_default": h_ha - league_default,
        }
