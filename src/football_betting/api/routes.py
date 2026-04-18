"""Public REST endpoints for the Betting with AI homepage."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from football_betting.api import services
from football_betting.api.schemas import (
    BankrollPoint,
    FormRow,
    HealthOut,
    LeagueOut,
    LeagueRatingSummary,
    PerformanceIndexOut,
    PerformanceSummary,
    RatingRow,
    TeamDetail,
    TodayPayload,
    ValueBetOut,
)
from football_betting.config import LEAGUES


API_VERSION = "0.3.0"

router = APIRouter()


def _validate_league(league_key: str) -> str:
    key = league_key.upper()
    if key not in LEAGUES:
        raise HTTPException(status_code=404, detail=f"Unknown league '{league_key}'")
    return key


@router.get("/health", response_model=HealthOut, tags=["meta"])
def health() -> HealthOut:
    return services.get_health(version=API_VERSION)


@router.get("/leagues", response_model=list[LeagueOut], tags=["leagues"])
def leagues() -> list[LeagueOut]:
    return services.list_leagues()


@router.get(
    "/leagues/summaries",
    response_model=list[LeagueRatingSummary],
    tags=["leagues"],
)
def league_summaries() -> list[LeagueRatingSummary]:
    return services.get_league_summaries()


@router.get(
    "/leagues/{league_key}/ratings",
    response_model=list[RatingRow],
    tags=["leagues"],
)
def league_ratings(
    league_key: str,
    top: int = Query(20, ge=1, le=100),
) -> list[RatingRow]:
    key = _validate_league(league_key)
    try:
        return services.get_league_ratings(key, top=top)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/leagues/{league_key}/form",
    response_model=list[FormRow],
    tags=["leagues"],
)
def league_form(
    league_key: str,
    top: int = Query(20, ge=1, le=100),
) -> list[FormRow]:
    key = _validate_league(league_key)
    try:
        return services.get_league_form(key, top=top)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/predictions/today", response_model=TodayPayload, tags=["predictions"])
def predictions_today(
    league: str | None = Query(None, description="Optional league filter (PL, BL, …)"),
) -> TodayPayload:
    if league is not None:
        league = _validate_league(league)
    return services.get_today_payload(league=league)


@router.get(
    "/value-bets/today",
    response_model=list[ValueBetOut],
    tags=["predictions"],
)
def value_bets_today(
    league: str | None = Query(None),
) -> list[ValueBetOut]:
    if league is not None:
        league = _validate_league(league)
    payload = services.get_today_payload(league=league)
    return payload.value_bets


@router.get(
    "/performance/summary",
    response_model=PerformanceSummary,
    tags=["performance"],
)
def performance_summary() -> PerformanceSummary:
    return services.get_performance_summary()


@router.get(
    "/performance/bankroll",
    response_model=list[BankrollPoint],
    tags=["performance"],
)
def performance_bankroll() -> list[BankrollPoint]:
    return services.get_bankroll_curve()


@router.get(
    "/performance/index",
    response_model=PerformanceIndexOut,
    tags=["performance"],
)
def performance_index() -> PerformanceIndexOut:
    """Anonymised public performance tracker (no EUR amounts)."""
    return services.get_performance_index()


@router.get(
    "/teams/{league_key}/{team}",
    response_model=TeamDetail,
    tags=["teams"],
)
def team_detail(league_key: str, team: str) -> TeamDetail:
    key = _validate_league(league_key)
    detail = services.get_team_detail(key, team)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Team '{team}' not found")
    return detail
