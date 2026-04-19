"""Public REST endpoints for the Betting with AI homepage."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse

from football_betting.api import consent as consent_store
from football_betting.api import services
from football_betting.api.schemas import (
    BankrollPoint,
    CalibrationBucketOut,
    ConsentIn,
    ConsentOut,
    FormRow,
    HealthOut,
    HistoryPayload,
    LeagueOut,
    LeagueRatingSummary,
    PerformanceIndexOut,
    PerformanceSummary,
    RatingRow,
    SeoSlugsOut,
    TeamDetail,
    TodayPayload,
    TrackRecordCalibrationOut,
    ValueBetOut,
)
from football_betting.config import LEAGUES
from football_betting.seo.track_record import (
    build_calibration,
    build_csv,
    load_records,
)


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
    "/history",
    response_model=HistoryPayload,
    tags=["performance"],
)
def history(
    days: int = Query(14, ge=1, le=180, description="Number of most-recent days to include"),
) -> HistoryPayload:
    """Graded value bets grouped by day, newest first."""
    return services.get_history(days=days)


@router.get(
    "/seo/track-record.csv",
    tags=["seo"],
    response_class=PlainTextResponse,
    responses={200: {"content": {"text/csv": {}}}},
)
def seo_track_record_csv(response: Response) -> PlainTextResponse:
    """Downloadable predictions-vs-results CSV for SEO Dataset asset."""
    records = load_records()
    body = build_csv(records)
    headers = {
        "Cache-Control": "public, max-age=3600",
        "Content-Disposition": 'attachment; filename="track-record.csv"',
    }
    return PlainTextResponse(content=body, media_type="text/csv", headers=headers)


@router.get(
    "/seo/track-record/calibration",
    response_model=TrackRecordCalibrationOut,
    tags=["seo"],
)
def seo_track_record_calibration(
    response: Response,
    league: str | None = Query(None),
    bins: int = Query(10, ge=2, le=50),
) -> TrackRecordCalibrationOut:
    """Reliability-diagram buckets for SEO calibration plot."""
    if league is not None:
        league = _validate_league(league)
    records = load_records()
    n_settled = sum(1 for r in records if r.actual_outcome is not None)
    buckets = build_calibration(records, n_bins=bins, league=league)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return TrackRecordCalibrationOut(
        league=league,
        n_records=len(records),
        n_settled=n_settled,
        buckets=[CalibrationBucketOut(**b.__dict__) for b in buckets],
    )


@router.get(
    "/seo/slugs",
    response_model=SeoSlugsOut,
    tags=["seo"],
)
def seo_slugs(response: Response) -> SeoSlugsOut:
    """League + team slugs for sitemap / SEO tooling. Cached for 1 hour."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    return services.get_seo_slugs()


@router.post("/consent", response_model=ConsentOut, tags=["consent"])
def submit_consent(payload: ConsentIn, request: Request) -> ConsentOut:
    """Persist cookie-consent decision keyed by hashed client IP."""
    record = consent_store.save_consent(
        request,
        accepted=payload.accepted,
        categories=payload.categories,
        version=payload.version,
    )
    return ConsentOut(
        accepted=record["accepted"],
        categories=record["categories"],
        version=record["version"],
        updated_at=record["updated_at"],
        first_seen_at=record["first_seen_at"],
    )


@router.get("/consent", response_model=ConsentOut | None, tags=["consent"])
def fetch_consent(request: Request) -> ConsentOut | None:
    """Return the previously stored consent for the calling IP, if any."""
    record = consent_store.get_consent(request)
    if record is None:
        return None
    return ConsentOut(
        accepted=record["accepted"],
        categories=record.get("categories", []),
        version=record.get("version", "1.0"),
        updated_at=record["updated_at"],
        first_seen_at=record.get("first_seen_at", record["updated_at"]),
    )


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
