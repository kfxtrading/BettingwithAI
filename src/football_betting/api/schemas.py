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
    kickoff_utc: str | None = None  # ISO-8601 with trailing Z (DST-aware)
    league_timezone: str | None = None  # IANA tz name for client-side local rendering
    prob_home: float = Field(ge=0.0, le=1.0)
    prob_draw: float = Field(ge=0.0, le=1.0)
    prob_away: float = Field(ge=0.0, le=1.0)
    odds: OddsOut | None = None
    model_name: str
    most_likely: Outcome
    is_live: bool = False
    pick_correct: bool | None = None
    ft_score: str | None = None
    sofascore_event_id: int | None = None
    stake: float | None = None  # monetary units (EUR), filled by staking allocator
    stake_pct: float | None = None  # % share of daily bankroll


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
    is_live: bool = False
    pick_correct: bool | None = None
    ft_score: str | None = None


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


class StrategyStats(BaseModel):
    """Aggregate performance metrics scoped to a single betting strategy."""

    n_bets: int
    hit_rate: float
    roi: float
    total_profit: float
    total_stake: float
    max_drawdown_pct: float


class PerformanceSummary(BaseModel):
    n_predictions: int
    n_bets: int
    hit_rate: float
    roi: float
    total_profit: float
    total_stake: float
    brier_mean: float | None = None
    rps_mean: float | None = None
    log_loss_mean: float | None = None
    macro_f1: float | None = None
    weighted_f1: float | None = None
    f1_draw: float | None = None
    max_drawdown_pct: float
    per_league: list[PerformancePerLeague] = Field(default_factory=list)
    value_bets: StrategyStats | None = None
    predictions: StrategyStats | None = None


class BankrollPoint(BaseModel):
    date: str
    value: float
    value_bets: float | None = None
    predictions: float | None = None


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
    kind: Literal["value", "prediction"] = "value"


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


class CalibrationBucketOut(BaseModel):
    """One reliability-diagram bucket: predicted vs actual frequency."""

    bin_lower: float
    bin_upper: float
    n: int
    predicted_mean: float
    actual_rate: float


class TrackRecordCalibrationOut(BaseModel):
    """Calibration buckets for SEO /track-record page."""

    league: str | None = None
    n_records: int
    n_settled: int
    buckets: list[CalibrationBucketOut] = Field(default_factory=list)


class MatchSlugOut(BaseModel):
    """One upcoming-match slug for SEO routing / sitemap."""

    slug: str
    league: str
    league_name: str
    home_team: str
    away_team: str
    date: str
    kickoff_time: str | None = None
    kickoff_utc: str | None = None
    league_timezone: str | None = None


class MatchSlugsOut(BaseModel):
    """Lightweight payload listing every upcoming match slug."""

    league: str | None = None
    n_matches: int
    matches: list[MatchSlugOut] = Field(default_factory=list)


class MatchWrapperOut(BaseModel):
    """SEO wrapper prose + probabilities for ``/leagues/{league}/{match}``."""

    slug: str
    league: str
    league_name: str
    home_team: str
    away_team: str
    kickoff: str
    prob_home: float = Field(ge=0.0, le=1.0)
    prob_draw: float = Field(ge=0.0, le=1.0)
    prob_away: float = Field(ge=0.0, le=1.0)
    pick: Outcome
    prose: str
    is_archived: bool = False
    actual_result: Outcome | None = None
    actual_score: str | None = None
    pick_correct: bool | None = None
    sofascore_event_id: int | None = None


class LeagueFixtureOut(BaseModel):
    """One fixture / past match for the league hub widgets."""

    date: str
    home_team: str
    away_team: str
    kickoff_time: str | None = None
    kickoff_utc: str | None = None
    league_timezone: str | None = None
    # Upcoming-only model probabilities.
    prob_home: float | None = None
    prob_draw: float | None = None
    prob_away: float | None = None
    most_likely: Outcome | None = None
    # Past-only result fields.
    home_goals: int | None = None
    away_goals: int | None = None
    result: Outcome | None = None
    # If model picked this match in the past, was the pick correct?
    pick_correct: bool | None = None
    slug: str | None = None


class LeagueFixturesOut(BaseModel):
    """Last-5 + next-5 fixtures for the league hub SEO upgrade."""

    league: str
    league_name: str
    next_5: list[LeagueFixtureOut] = Field(default_factory=list)
    last_5: list[LeagueFixtureOut] = Field(default_factory=list)


class ConsentIn(BaseModel):
    """Cookie-consent submission from the frontend banner."""

    accepted: bool
    categories: list[str] = Field(default_factory=list)
    version: str = "1.0"


class ConsentOut(BaseModel):
    """Persisted cookie-consent record (IP is stored as a salted hash only)."""

    accepted: bool
    categories: list[str] = Field(default_factory=list)
    version: str
    updated_at: str
    first_seen_at: str


class SupportAskIn(BaseModel):
    """Support-chatbot query payload."""

    question: str = Field(min_length=1, max_length=500)
    lang: str = Field(default="en", min_length=2, max_length=5)
    top_k: int = Field(default=3, ge=1, le=10)


class SupportPredictionOut(BaseModel):
    intent_id: str
    chapter: str
    score: float = Field(ge=0.0, le=1.0)
    chapter_score: float = Field(ge=0.0, le=1.0)


class MatchNewsItem(BaseModel):
    """A single news headline for a team or fixture."""

    title: str
    url: str
    source: str


class MatchContext(BaseModel):
    """Pre-computed match overview returned when a chat query mentions a team."""

    home_team: str
    away_team: str
    league: str
    league_name: str
    kickoff_time: str | None = None
    prob_home: float = Field(ge=0.0, le=1.0)
    prob_draw: float = Field(ge=0.0, le=1.0)
    prob_away: float = Field(ge=0.0, le=1.0)
    most_likely: Outcome
    odds: OddsOut | None = None
    form_home: str | None = None
    form_away: str | None = None
    value_bet: bool = False
    news: list[MatchNewsItem] = Field(default_factory=list)


class SupportAskOut(BaseModel):
    """Response for `POST /support/ask`. Empty `predictions` signals OOD — clients should fall back to FAQ search."""

    lang: str
    question: str
    predictions: list[SupportPredictionOut] = Field(default_factory=list)
    fallback: bool = False
    match_context: MatchContext | None = None
    match_article: str | None = None

