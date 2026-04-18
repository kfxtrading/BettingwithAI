"""Public REST endpoints for the Betting with AI homepage."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from football_betting.api import services
from football_betting.api.schemas import (
    BankrollPoint,
    FormRow,
    HealthOut,
    HistoryPayload,
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


@router.get("/debug/download", tags=["meta"], include_in_schema=False)
def debug_download() -> dict:
    """Trigger CSV download synchronously; return before/after file counts."""
    from football_betting.config import DATA_DIR
    from football_betting.data.downloader import download_all

    raw_dir = DATA_DIR / "raw"
    before = sorted(p.name for p in raw_dir.glob("*.csv")) if raw_dir.exists() else []
    try:
        paths = download_all()
        error: str | None = None
    except Exception as exc:  # pragma: no cover
        paths = []
        error = f"{type(exc).__name__}: {exc}"
    after = sorted(p.name for p in raw_dir.glob("*.csv")) if raw_dir.exists() else []
    return {
        "before_count": len(before),
        "after_count": len(after),
        "downloaded": [str(p.name) for p in paths],
        "added": sorted(set(after) - set(before)),
        "error": error,
    }


@router.get("/debug/paths", tags=["meta"], include_in_schema=False)
def debug_paths() -> dict:
    from pathlib import Path
    from football_betting.api import services as svc
    from football_betting.config import DATA_DIR, MODELS_DIR

    def _listdir(p: Path) -> list[str]:
        try:
            return sorted(x.name for x in p.iterdir())
        except (OSError, FileNotFoundError):
            return []

    latest = svc._latest_fixtures_file()
    raw_dir = DATA_DIR / "raw"
    return {
        "cwd": str(Path.cwd()),
        "DATA_DIR": str(DATA_DIR),
        "DATA_DIR_exists": DATA_DIR.exists(),
        "DATA_DIR_files": _listdir(DATA_DIR)[:30],
        "DATA_DIR_glob_fixtures": [p.name for p in DATA_DIR.glob("fixtures_*.json")],
        "RAW_DIR": str(raw_dir),
        "RAW_DIR_exists": raw_dir.exists(),
        "RAW_DIR_files": _listdir(raw_dir)[:40],
        "MODELS_DIR": str(MODELS_DIR),
        "MODELS_DIR_files": _listdir(MODELS_DIR)[:20],
        "BUNDLED_DIR": str(svc._BUNDLED_FIXTURES_DIR),
        "BUNDLED_DIR_exists": svc._BUNDLED_FIXTURES_DIR.exists(),
        "BUNDLED_DIR_files": _listdir(svc._BUNDLED_FIXTURES_DIR),
        "_latest_fixtures_file": str(latest) if latest else None,
        "services_file": str(Path(svc.__file__).resolve()),
    }


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
