"""
FeatureBuilder v0.3 — orchestrates all feature extractors including
real xG, squad quality, and market movement.

Central entry point for feature engineering. Walks matches chronologically,
building feature rows using only *past* data (no leakage), then updating
all internal trackers with each match's outcome.

v0.3 additions:
* RealXgTracker (fed from Sofascore data if available)
* SquadQualityTracker (fed from Sofascore lineup data)
* MarketMovementTracker (fed from odds snapshots over time)
* Auto-fallback: uses xg_proxy when no Sofascore data available
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

from football_betting.config import FEATURE_CFG, LEAGUES, POINT_DEDUCTIONS, FeatureConfig
from football_betting.features.form import FormTracker
from football_betting.features.h2h import H2HTracker
from football_betting.features.home_advantage import (
    HomeAdvantageTracker,
    dynamic_home_advantage,
)
from football_betting.features.market_movement import MarketMovementTracker
from football_betting.features.real_xg import RealXgTracker
from football_betting.features.rest_days import RestDaysTracker
from football_betting.features.squad_quality import SquadQualityTracker
from football_betting.features.weather import WeatherTracker
from football_betting.features.xg_proxy import XgProxyTracker
from football_betting.rating.pi_ratings import PiRatings

if TYPE_CHECKING:
    from football_betting.data.models import Fixture, Match


@dataclass(slots=True)
class FeatureBuilder:
    """Orchestrates all feature extractors."""

    cfg: FeatureConfig = field(default_factory=lambda: FEATURE_CFG)
    pi_ratings: PiRatings = field(default_factory=PiRatings)
    form_tracker: FormTracker = field(default_factory=FormTracker)
    xg_tracker: XgProxyTracker = field(default_factory=XgProxyTracker)
    real_xg_tracker: RealXgTracker = field(default_factory=RealXgTracker)
    h2h_tracker: H2HTracker = field(default_factory=H2HTracker)
    rest_days_tracker: RestDaysTracker = field(default_factory=RestDaysTracker)
    home_adv_tracker: HomeAdvantageTracker = field(default_factory=HomeAdvantageTracker)
    squad_tracker: SquadQualityTracker = field(default_factory=SquadQualityTracker)
    market_tracker: MarketMovementTracker = field(default_factory=MarketMovementTracker)
    weather_tracker: WeatherTracker | None = None  # v0.4: optional, opt-in
    _sofascore_staged: dict[str, dict] = field(default_factory=dict)

    @staticmethod
    def _sofascore_key(home: str, away: str, date_iso: str) -> str:
        return f"{date_iso}|{home}|{away}"

    # ───────────────────────── Feature extraction ─────────────────────────

    def build_features(
        self,
        home_team: str,
        away_team: str,
        league_key: str,
        match_date: date,
        odds_home: float | None = None,
        odds_draw: float | None = None,
        odds_away: float | None = None,
        season: str | None = None,
        kickoff_datetime_utc: datetime | None = None,
    ) -> dict[str, float]:
        """Full feature vector for a single fixture."""
        feats: dict[str, float] = {}
        league = LEAGUES[league_key]

        # Core pi-ratings
        if self.cfg.use_pi_ratings:
            feats.update(self.pi_ratings.features_for_match(home_team, away_team))

        # Form
        if self.cfg.use_form:
            feats.update(self.form_tracker.features_for_match(home_team, away_team))

        # xG — prefer real xG, fall back to proxy
        has_real_xg = (
            self.real_xg_tracker.team_has_data(home_team)
            and self.real_xg_tracker.team_has_data(away_team)
        )
        if self.cfg.use_real_xg and has_real_xg:
            feats.update(self.real_xg_tracker.features_for_match(home_team, away_team))
            feats["has_real_xg"] = 1.0
        elif self.cfg.use_xg_proxy:
            feats.update(self.xg_tracker.features_for_match(home_team, away_team))
            feats["has_real_xg"] = 0.0

        # Squad quality (v0.3)
        if self.cfg.use_squad_quality:
            feats.update(self.squad_tracker.features_for_match(home_team, away_team))

        # Market movement (v0.3)
        if self.cfg.use_market_movement:
            feats.update(
                self.market_tracker.features_for_fixture(
                    home_team, away_team, match_date.isoformat()
                )
            )

        # H2H
        if self.cfg.use_h2h:
            feats.update(self.h2h_tracker.features_for_match(home_team, away_team))

        # Rest days
        if self.cfg.use_rest_days:
            feats.update(
                self.rest_days_tracker.features_for_match(home_team, away_team, match_date)
            )

        # Dynamic HA
        if self.cfg.use_home_advantage:
            feats.update(
                self.home_adv_tracker.features_for_match(home_team, away_team, match_date)
            )

        # League meta
        feats["league_avg_goals"] = league.avg_goals_per_team
        feats["league_home_adv"] = dynamic_home_advantage(
            match_date,
            league.home_advantage,
            ghost_factor=self.home_adv_tracker.cfg.ghost_factor,
            periods=self.home_adv_tracker.cfg.ghost_periods,
        )

        # Market features
        if self.cfg.use_market_odds:
            if odds_home and odds_draw and odds_away:
                total = 1 / odds_home + 1 / odds_draw + 1 / odds_away
                feats["market_p_home"] = (1 / odds_home) / total
                feats["market_p_draw"] = (1 / odds_draw) / total
                feats["market_p_away"] = (1 / odds_away) / total
                feats["market_margin"] = total - 1.0
                feats["market_fav_ratio"] = max(feats["market_p_home"], feats["market_p_away"]) / max(
                    min(feats["market_p_home"], feats["market_p_away"]), 0.01
                )
            else:
                for k in ("market_p_home", "market_p_draw", "market_p_away",
                          "market_margin", "market_fav_ratio"):
                    feats[k] = -1.0

        # Point deduction adjustment
        if season:
            feats["home_point_ded"] = float(POINT_DEDUCTIONS.get((home_team, season), 0))
            feats["away_point_ded"] = float(POINT_DEDUCTIONS.get((away_team, season), 0))
        else:
            feats["home_point_ded"] = 0.0
            feats["away_point_ded"] = 0.0

        # Weather (v0.4 — Familie A)
        if self.cfg.use_weather and self.weather_tracker is not None:
            feats.update(
                self.weather_tracker.features_for_match(
                    home_team, away_team, match_date, kickoff_datetime_utc,
                )
            )

        return feats

    def features_for_fixture(self, fixture: Fixture) -> dict[str, float]:
        odds = fixture.odds
        return self.build_features(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            league_key=fixture.league,
            match_date=fixture.date,
            odds_home=odds.home if odds else None,
            odds_draw=odds.draw if odds else None,
            odds_away=odds.away if odds else None,
            season=fixture.effective_season(),
            kickoff_datetime_utc=fixture.resolve_kickoff(),
        )

    # ───────────────────────── State update ─────────────────────────

    def update_with_match(self, match: Match) -> None:
        """Process a completed match and update ALL trackers.

        If a Sofascore record for this match was staged upfront via
        `stage_sofascore_batch`, it is ingested *now* — preserving
        chronological order so the real-xG / squad trackers never see
        future matches while features for earlier matches are built.
        """
        sf = self._sofascore_staged.pop(
            self._sofascore_key(match.home_team, match.away_team, match.date.isoformat()),
            None,
        )
        if sf is not None:
            if self.cfg.use_real_xg:
                self.real_xg_tracker.ingest_sofascore_match(sf)
            if self.cfg.use_squad_quality:
                self.squad_tracker.ingest_sofascore_match(sf)

        if self.cfg.use_pi_ratings:
            self.pi_ratings.update(match)
        if self.cfg.use_form:
            self.form_tracker.update(match)
        if self.cfg.use_xg_proxy:
            self.xg_tracker.update(match)
        if self.cfg.use_h2h:
            self.h2h_tracker.update(match)
        if self.cfg.use_rest_days:
            self.rest_days_tracker.update(match)
        if self.cfg.use_home_advantage:
            self.home_adv_tracker.update(match)

    def fit_on_history(self, matches: list[Match]) -> None:
        """Warmup: populate trackers from historical matches chronologically."""
        matches_sorted = sorted(matches, key=lambda m: m.date)
        for m in matches_sorted:
            self.update_with_match(m)

    def stage_sofascore_batch(self, match_dicts: list[dict]) -> int:
        """Stage Sofascore records for *chronological* ingestion.

        Records land in `_sofascore_staged` keyed by (date, home, away).
        `update_with_match` pops the matching record when the corresponding
        football-data match is processed, so real-xG / squad trackers
        never see future matches during walk-forward feature building.

        Returns the number of records that were actually staged.
        """
        staged = 0
        for m in match_dicts:
            home = m.get("home_team")
            away = m.get("away_team")
            date_iso = m.get("date")
            if not (home and away and date_iso):
                continue
            self._sofascore_staged[self._sofascore_key(home, away, date_iso)] = m
            staged += 1
        return staged

    def ingest_sofascore_batch(self, match_dicts: list[dict]) -> dict[str, int]:
        """Immediate batch ingest — use only when no future leakage risk.

        Prefer `stage_sofascore_batch` for any flow that walks matches
        chronologically (training, walk-forward backtest). This direct
        path is kept for the *prediction* flow where all staged matches
        are strictly historical relative to the upcoming fixture.
        """
        n_xg = self.real_xg_tracker.ingest_many(match_dicts)
        self.squad_tracker.ingest_many(match_dicts)
        return {"xg_ingested": n_xg, "squad_ingested": len(match_dicts)}

    # ───────────────────────── Utilities ─────────────────────────

    def feature_names(self, sample: dict[str, float] | None = None) -> list[str]:
        if sample is not None:
            return list(sample.keys())
        from datetime import date as _date
        dummy = self.build_features(
            "_TEAM_A_", "_TEAM_B_", "PL", _date(2025, 1, 1)
        )
        return list(dummy.keys())

    def reset(self, keep_staged_sofascore: bool = True) -> None:
        """Reset all trackers. Staged Sofascore records are preserved by
        default so that a subsequent walk-forward run can consume them
        chronologically via `update_with_match`."""
        staged = self._sofascore_staged if keep_staged_sofascore else {}
        self.pi_ratings.reset()
        self.form_tracker = FormTracker(self.form_tracker.cfg)
        self.xg_tracker = XgProxyTracker(self.xg_tracker.cfg)
        self.real_xg_tracker = RealXgTracker(self.real_xg_tracker.cfg)
        self.h2h_tracker = H2HTracker(self.h2h_tracker.cfg)
        self.rest_days_tracker = RestDaysTracker(self.rest_days_tracker.cfg)
        self.home_adv_tracker = HomeAdvantageTracker(self.home_adv_tracker.cfg)
        self.squad_tracker = SquadQualityTracker(self.squad_tracker.cfg)
        self.market_tracker = MarketMovementTracker(self.market_tracker.cfg)
        self._sofascore_staged = dict(staged)
