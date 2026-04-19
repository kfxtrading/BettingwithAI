"""
Wire-format Pydantic models for the public REST API.

Kept distinct from internal models in `football_betting.data.models` so the
external contract can evolve independently of the ML pipeline.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Outcome = Literal["H", "D", "A"]
Confidence = Literal["low", "medium", "high"]


class OddsOut(BaseModel):
    home: float
    draw: float
    away: float
    bookmaker: str = "avg"


class PredictionOut(BaseModel):
    date: str
    league: str
    league_name: str
    home_team: str
    away_team: str
    kickoff_time: str | None = None
    prob_home: float = Field(ge=0.0, le=1.0)
    prob_draw: float = Field(ge=0.0, le=1.0)
    prob_away: float = Field(ge=0.0, le=1.0)
    odds: OddsOut | None = None
    model_name: str
    most_likely: Outcome


class ValueBetOut(BaseModel):
    date: str
    league: str
    league_name: str
    home_team: str
    away_team: str
    outcome: Outcome
    bet_label: str
    odds: float
    model_prob: float
    market_prob: float
    edge: float
    edge_pct: float
    kelly_stake: float
    expected_value_pct: float
    confidence: Confidence


class LeagueOut(BaseModel):
    key: str
    name: str
    code: str
    avg_goals_per_team: float
    home_advantage: float


class RatingRow(BaseModel):
    rank: int
    team: str
    pi_home: float
    pi_away: float
    pi_overall: float


class FormRow(BaseModel):
    team: str
    last5: str
    points: int
    goals_for: int
    goals_against: int


class TeamDetail(BaseModel):
    team: str
    league: str
    pi_home: float
    pi_away: float
    pi_overall: float
    last10: str
    goals_for_avg: float
    goals_against_avg: float


class LeagueRatingSummary(BaseModel):
    league: str
    league_name: str
    leader: str | None = None
    leader_rating: float | None = None
    n_teams: int


class PerformancePerLeague(BaseModel):
    league: str
    league_name: str
    n_bets: int
    hit_rate: float
    roi: float


class PerformanceSummary(BaseModel):
    n_predictions: int
    n_bets: int
    hit_rate: float
    roi: float
    total_profit: float
    total_stake: float
    brier_mean: float | None = None
    rps_mean: float | None = None
    max_drawdown_pct: float
    per_league: list[PerformancePerLeague] = Field(default_factory=list)


class BankrollPoint(BaseModel):
    date: str
    value: float


class EquityIndexPoint(BaseModel):
    date: str
    index: float
    n_bets_cumulative: int


class PerformanceIndexOut(BaseModel):
    """Anonymised public performance tracker (no EUR amounts)."""

    updated_at: str
    tracking_started_at: str
    n_days_tracked: int
    n_bets: int
    hit_rate: float | None = None
    current_index: float
    all_time_high_index: float
    max_drawdown_pct: float
    current_drawdown_pct: float
    equity_curve: list[EquityIndexPoint] = Field(default_factory=list)
    rule_hash: str
    model_version: str


class DataSourceInfo(BaseModel):
    """Provenance info: which historical data / model fed the predictions per league."""
    league: str
    league_name: str
    n_matches: int
    seasons: list[str] = Field(default_factory=list)
    date_range: str | None = None
    model: str
    n_predictions: int
    sofascore_matches_ingested: int = 0


class TodayPayload(BaseModel):
    generated_at: datetime
    predictions: list[PredictionOut] = Field(default_factory=list)
    value_bets: list[ValueBetOut] = Field(default_factory=list)
    data_sources: list[DataSourceInfo] = Field(default_factory=list)


class GradedBetOut(BaseModel):
    """A single value bet after the match has been settled."""

    date: str
    league: str
    league_name: str
    home_team: str
    away_team: str
    outcome: Outcome
    bet_label: str
    odds: float
    stake: float
    ft_result: Outcome | None = None
    ft_score: str | None = None
    status: Literal["won", "lost", "pending"]
    pnl: float


class HistoryDayOut(BaseModel):
    date: str
    n_bets: int
    n_won: int
    n_lost: int
    n_pending: int
    pnl: float
    bets: list[GradedBetOut] = Field(default_factory=list)


class HistoryPayload(BaseModel):
    generated_at: datetime
    n_days: int
    total_bets: int
    total_won: int
    total_lost: int
    total_pending: int
    total_pnl: float
    hit_rate: float | None = None  # won / (won + lost); None if no settled bets yet
    days: list[HistoryDayOut] = Field(default_factory=list)


class ModelAvailability(BaseModel):
    catboost: bool
    mlp: bool


class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    models_available: dict[str, ModelAvailability] = Field(default_factory=dict)
    snapshot_present: bool = False


class SeoLeagueSlug(BaseModel):
    key: str
    slug: str
    name: str


class SeoTeamSlug(BaseModel):
    league: str
    slug: str
    name: str


class SeoSlugsOut(BaseModel):
    """Lightweight payload for sitemap generation / SEO tooling."""

    leagues: list[SeoLeagueSlug] = Field(default_factory=list)
    teams: list[SeoTeamSlug] = Field(default_factory=list)
