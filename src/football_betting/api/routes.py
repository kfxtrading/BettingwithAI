"""Public REST endpoints for the Betting with AI homepage."""

from __future__ import annotations

import os

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse

from football_betting.api import consent as consent_store
from football_betting.api import services, support_service
from football_betting.api.schemas import (
    BankrollPoint,
    CalibrationBucketOut,
    ConsentIn,
    ConsentOut,
    FormRow,
    HealthOut,
    HistoryPayload,
    LeagueFixturesOut,
    LeagueOut,
    LeagueRatingSummary,
    MatchSlugsOut,
    MatchWrapperOut,
    PerformanceIndexOut,
    PerformanceSummary,
    RatingRow,
    SeoSlugsOut,
    SupportAskIn,
    SupportAskOut,
    SupportPredictionOut,
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


@router.get(
    "/seo/matches/upcoming",
    response_model=MatchSlugsOut,
    tags=["seo"],
)
def seo_matches_upcoming(
    response: Response,
    league: str | None = Query(None),
) -> MatchSlugsOut:
    """Upcoming-match slugs from today's snapshot for sitemap / SEO."""
    if league is not None:
        league = _validate_league(league)
    response.headers["Cache-Control"] = "public, max-age=600"
    return services.get_upcoming_match_slugs(league=league)


@router.get(
    "/seo/matches/{slug}",
    response_model=MatchWrapperOut,
    tags=["seo"],
)
def seo_match_wrapper(slug: str, response: Response) -> MatchWrapperOut:
    """SEO wrapper (probabilities + 150–300 word prose) for a match slug.

    Returns 404 when the slug is not in the current snapshot — the
    frontend uses that signal to ``noindex`` the page (see Battle Plan §4).
    """
    wrapper = services.get_match_wrapper(slug)
    if wrapper is None:
        raise HTTPException(status_code=404, detail=f"Unknown match slug '{slug}'")
    response.headers["Cache-Control"] = "public, max-age=600"
    return wrapper


@router.get(
    "/leagues/{league_key}/fixtures",
    response_model=LeagueFixturesOut,
    tags=["leagues"],
)
def league_fixtures(
    league_key: str,
    limit: int = Query(5, ge=1, le=20),
) -> LeagueFixturesOut:
    """Next-N upcoming + last-N past fixtures for the league hub widgets."""
    key = _validate_league(league_key)
    return services.get_league_fixtures(key, limit=limit)


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


@router.post("/admin/refresh-snapshot", tags=["admin"])
async def admin_refresh_snapshot(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    """Force the daily scheduler refresh to run immediately.

    Calls the same blocking pipeline as the daily timer (Odds-API fetch ->
    today.json -> regrade). Protected by ``ADMIN_REFRESH_TOKEN`` env var.
    """
    expected = os.environ.get("ADMIN_REFRESH_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="ADMIN_REFRESH_TOKEN not configured on server.",
        )
    if x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token.")

    from football_betting.api.scheduler import refresh_snapshot_once
    from football_betting.api.snapshots import load_today

    await refresh_snapshot_once()
    payload = load_today()
    return {
        "ok": True,
        "predictions": len(payload.predictions) if payload else 0,
        "value_bets": len(payload.value_bets) if payload else 0,
        "generated_at": payload.generated_at.isoformat() if payload else None,
    }


@router.post("/support/ask", response_model=SupportAskOut, tags=["support"])
def support_ask(payload: SupportAskIn) -> SupportAskOut:
    """Classify a support-chatbot question with the multilingual two-head transformer.

    Returns an empty ``predictions`` list (with ``fallback=True``) when the
    query is out-of-distribution or below the confidence gate — the frontend
    is expected to fall back to its Fuse.js FAQ search in that case.

    When the model directory is missing or torch/transformers are unavailable
    the endpoint also reports ``fallback=True`` rather than HTTP 500, so the
    chatbot UI keeps working during partial deploys.
    """
    try:
        predictions = support_service.classify(
            question=payload.question, lang=payload.lang, top_k=payload.top_k
        )
    except support_service.SupportModelUnavailable:
        return SupportAskOut(
            lang=payload.lang, question=payload.question, predictions=[], fallback=True
        )
    return SupportAskOut(
        lang=payload.lang,
        question=payload.question,
        predictions=[
            SupportPredictionOut(
                intent_id=p.intent_id,
                chapter=p.chapter,
                score=p.score,
                chapter_score=p.chapter_score,
            )
            for p in predictions
        ],
        fallback=not predictions,
    )
