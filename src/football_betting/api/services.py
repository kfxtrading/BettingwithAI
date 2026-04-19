"""
API service layer — bridges FastAPI routers and the existing ML package.

All functions return wire-format Pydantic models from `api.schemas`.
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from football_betting.api.cache import cache
from football_betting.api.schemas import (
    BankrollPoint,
    DataSourceInfo,
    EquityIndexPoint,
    FormRow,
    GradedBetOut,
    HealthOut,
    HistoryDayOut,
    HistoryPayload,
    LeagueFixtureOut,
    LeagueFixturesOut,
    LeagueOut,
    LeagueRatingSummary,
    MatchSlugOut,
    MatchSlugsOut,
    MatchWrapperOut,
    ModelAvailability,
    OddsOut,
    PerformanceIndexOut,
    PerformancePerLeague,
    PerformanceSummary,
    PredictionOut,
    RatingRow,
    SeoLeagueSlug,
    SeoSlugsOut,
    SeoTeamSlug,
    TeamDetail,
    TodayPayload,
    ValueBetOut,
)

logger = logging.getLogger("football_betting.api")
from football_betting.api.snapshots import load_today
from football_betting.betting.value import find_value_bets, rank_value_bets
from football_betting.config import DATA_DIR, LEAGUES, MODELS_DIR
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture, MatchOdds, Outcome, Prediction
from football_betting.data.odds_snapshots import (
    append_snapshot as append_odds_snapshot,
    load_into_tracker as load_odds_snapshots,
)
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.ensemble import EnsembleModel
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.rating.pi_ratings import PiRatings
from football_betting.scraping.sofascore import SofascoreClient
from football_betting.tracking.tracker import ResultsTracker


__all__ = [
    "build_predictions_for_fixtures",
    "get_health",
    "get_today_payload",
    "get_league_ratings",
    "get_league_form",
    "get_league_summaries",
    "get_league_fixtures",
    "get_match_wrapper",
    "get_performance_summary",
    "get_performance_index",
    "get_upcoming_match_slugs",
    "invalidate_performance_cache",
    "get_bankroll_curve",
    "get_seo_slugs",
    "get_team_detail",
    "list_leagues",
]


# ─────────────────────────────────────────────────────────────────
# SEO helpers
# ─────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    """Make a URL-friendly slug from an arbitrary team/league name."""
    slug = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE).strip().lower()
    slug = re.sub(r"[\s_]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")


def get_seo_slugs() -> SeoSlugsOut:
    """Return league + team slugs for sitemap generation.

    Teams are pulled from current Pi-Ratings; missing data is silently
    skipped so the endpoint remains robust during fresh deployments.
    """
    cache_key = "seo:slugs"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    leagues: list[SeoLeagueSlug] = []
    teams: list[SeoTeamSlug] = []
    for key, cfg in LEAGUES.items():
        leagues.append(
            SeoLeagueSlug(key=key, slug=_slugify(cfg.name), name=cfg.name)
        )
        try:
            ratings = _ratings_for_league(key)
        except FileNotFoundError:
            continue
        except Exception:  # noqa: BLE001 — SEO endpoint must never 500
            logger.warning("get_seo_slugs: failed to load ratings for %s", key)
            continue
        for team, _ in ratings.top_n(500):
            teams.append(
                SeoTeamSlug(league=key, slug=_slugify(team), name=team)
            )

    payload = SeoSlugsOut(leagues=leagues, teams=teams)
    cache.set(cache_key, payload, ttl=3600.0)
    return payload


# ─────────────────────────────────────────────────────────────────
# Health / metadata
# ─────────────────────────────────────────────────────────────────

def get_health(version: str) -> HealthOut:
    models: dict[str, ModelAvailability] = {}
    for key in LEAGUES:
        models[key] = ModelAvailability(
            catboost=(MODELS_DIR / f"catboost_{key}.cbm").exists(),
            mlp=(MODELS_DIR / f"mlp_{key}.pt").exists(),
        )
    from football_betting.api.snapshots import snapshot_exists

    return HealthOut(
        version=version,
        models_available=models,
        snapshot_present=snapshot_exists(),
    )


def list_leagues() -> list[LeagueOut]:
    return [
        LeagueOut(
            key=key,
            name=cfg.name,
            code=cfg.code,
            avg_goals_per_team=cfg.avg_goals_per_team,
            home_advantage=cfg.home_advantage,
        )
        for key, cfg in LEAGUES.items()
    ]


# ─────────────────────────────────────────────────────────────────
# Predictions / value bets
# ─────────────────────────────────────────────────────────────────

_FIXTURE_PATTERN = re.compile(r"fixtures_(\d{4})-(\d{2})-(\d{2})\.json$")
_BUNDLED_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "_bundled"


def _latest_fixtures_file() -> Path | None:
    candidates = list(DATA_DIR.glob("fixtures_*.json"))
    if _BUNDLED_FIXTURES_DIR.is_dir():
        candidates.extend(_BUNDLED_FIXTURES_DIR.glob("fixtures_*.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.name)


def _to_prediction_out(pred: Prediction, league_name: str) -> PredictionOut:
    fx = pred.fixture
    odds = (
        OddsOut(
            home=fx.odds.home,
            draw=fx.odds.draw,
            away=fx.odds.away,
            bookmaker=fx.odds.bookmaker,
        )
        if fx.odds is not None
        else None
    )
    return PredictionOut(
        date=fx.date.isoformat(),
        league=fx.league,
        league_name=league_name,
        home_team=fx.home_team,
        away_team=fx.away_team,
        kickoff_time=fx.kickoff_time,
        prob_home=pred.prob_home,
        prob_draw=pred.prob_draw,
        prob_away=pred.prob_away,
        odds=odds,
        model_name=pred.model_name,
        most_likely=pred.most_likely_outcome,
    )


def _to_value_bet_out(vb, league_name: str) -> ValueBetOut:
    return ValueBetOut(
        date=vb.date,
        league=vb.league,
        league_name=league_name,
        home_team=vb.home_team,
        away_team=vb.away_team,
        outcome=vb.outcome,
        bet_label=vb.bet_label,
        odds=vb.odds,
        model_prob=vb.model_prob,
        market_prob=vb.market_prob,
        edge=vb.edge,
        edge_pct=vb.edge_pct,
        kelly_stake=vb.kelly_stake,
        expected_value_pct=vb.expected_value_pct,
        confidence=vb.confidence,
    )


def build_predictions_for_fixtures(
    fixtures_data: list[dict],
    bankroll: float = 1000.0,
) -> TodayPayload:
    """
    Run the full prediction pipeline over a list of fixture dicts.

    `fixtures_data` mirrors the JSON shape consumed by `fb predict`:
        [{"league": "PL", "date": "...", "home_team": "...",
          "away_team": "...", "odds": {"home", "draw", "away"}}]
    """
    by_league: dict[str, list[dict]] = defaultdict(list)
    for fd in fixtures_data:
        by_league[fd["league"].upper()].append(fd)

    logger.info(
        "[predict] Building predictions for %d fixture(s) across %d league(s): %s",
        len(fixtures_data),
        len(by_league),
        ", ".join(sorted(by_league)),
    )

    predictions: list[PredictionOut] = []
    value_bets = []
    data_sources: list[DataSourceInfo] = []

    for league_key, league_fixtures in by_league.items():
        if league_key not in LEAGUES:
            logger.warning("[predict] Skipping unknown league %s", league_key)
            continue
        league_name = LEAGUES[league_key].name

        try:
            matches = load_league(league_key)
        except FileNotFoundError:
            logger.warning(
                "[predict] No historical CSV for %s — run `fb download --league %s`.",
                league_key, league_key,
            )
            continue

        seasons = sorted({m.season for m in matches})
        date_min = min(m.date for m in matches).isoformat() if matches else None
        date_max = max(m.date for m in matches).isoformat() if matches else None
        date_range = f"{date_min} → {date_max}" if date_min else None

        fb = FeatureBuilder()

        # Stage Sofascore BEFORE replay → consumed chronologically by fit_on_history
        sofascore_count = 0
        for season in seasons:
            sf_data = SofascoreClient.load_matches(league_key, season)
            if sf_data:
                sofascore_count += fb.stage_sofascore_batch(sf_data)

        fb.fit_on_history(matches)

        # Persist current odds → reload full history into market tracker so
        # mm_* features reflect real drift across prediction runs.
        for fd in league_fixtures:
            if fd.get("odds"):
                try:
                    append_odds_snapshot(
                        league_key,
                        fd["home_team"],
                        fd["away_team"],
                        str(fd["date"]),
                        MatchOdds(**fd["odds"]),
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning(
                        "[predict] Failed to persist odds snapshot for %s vs %s: %s",
                        fd["home_team"], fd["away_team"], exc,
                    )
        odds_snaps_loaded = load_odds_snapshots(
            league_key, fb.market_tracker, only_future=True
        )

        model = _build_model(league_key, fb)
        model_name = type(model).__name__

        logger.info(
            "[predict] %s (%s): %d historical matches | seasons=%s | range=%s | "
            "sofascore=%d | odds_snaps=%d | model=%s | fixtures=%d",
            league_name, league_key, len(matches),
            ",".join(seasons), date_range, sofascore_count,
            odds_snaps_loaded, model_name, len(league_fixtures),
        )

        n_pred_before = len(predictions)
        for fd in league_fixtures:
            odds = MatchOdds(**fd["odds"]) if fd.get("odds") else None
            fixture = Fixture(
                date=fd["date"],
                league=league_key,
                home_team=fd["home_team"],
                away_team=fd["away_team"],
                kickoff_time=fd.get("kickoff_time"),
                odds=odds,
                season=fd.get("season"),
            )
            try:
                pred = model.predict(fixture)
            except Exception as exc:
                logger.warning(
                    "[predict] Failed %s vs %s (%s): %s",
                    fd["home_team"], fd["away_team"], league_key, exc,
                )
                continue
            predictions.append(_to_prediction_out(pred, league_name))

            if odds is not None:
                bets = find_value_bets(pred, bankroll)
                for b in rank_value_bets(bets):
                    value_bets.append(_to_value_bet_out(b, league_name))

        data_sources.append(
            DataSourceInfo(
                league=league_key,
                league_name=league_name,
                n_matches=len(matches),
                seasons=seasons,
                date_range=date_range,
                model=model_name,
                n_predictions=len(predictions) - n_pred_before,
                sofascore_matches_ingested=sofascore_count,
            )
        )

    logger.info(
        "[predict] DONE — %d predictions, %d value bets across %d league(s).",
        len(predictions), len(value_bets), len(data_sources),
    )

    return TodayPayload(
        generated_at=datetime.utcnow(),
        predictions=predictions,
        value_bets=value_bets,
        data_sources=data_sources,
    )


def _build_model(league_key: str, fb: FeatureBuilder):
    """Instantiate the strongest model available for this league."""
    catboost_path = MODELS_DIR / f"catboost_{league_key}.cbm"
    if not catboost_path.exists():
        return PoissonModel(pi_ratings=fb.pi_ratings)

    cb = CatBoostPredictor.for_league(league_key, fb)
    poisson = PoissonModel(pi_ratings=fb.pi_ratings)
    mlp = MLPPredictor.for_league(league_key, fb)
    return EnsembleModel(catboost=cb, poisson=poisson, mlp=mlp)


def _enrich_predictions_with_live_and_graded(payload: TodayPayload) -> TodayPayload:
    """Annotate each prediction with live-status and pick-correctness.

    Joins ``graded_bets.jsonl`` (authoritative full-time results) and
    ``live_scores.jsonl`` (Odds-API in-progress scores) onto the snapshot
    predictions. ``pick_correct`` is set only for settled matches; ``is_live``
    flags matches that have kicked off but not yet finished.
    """
    if not payload.predictions:
        return payload

    try:
        from football_betting.evaluation.grader import _norm, load_graded
        from football_betting.evaluation.live_results import (
            load_live_matches_for_code,
        )
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("[api] enrichment imports failed: %s", exc)
        return payload

    # Build graded index: (league_key, date, home_norm, away_norm) -> GradedBet.
    graded_idx: dict[tuple[str, str, str, str], object] = {}
    try:
        for g in load_graded():
            if g.kind != "prediction":
                continue
            graded_idx[
                (g.league, g.date, _norm(g.home_team), _norm(g.away_team))
            ] = g
    except Exception as exc:  # pragma: no cover
        logger.warning("[api] load_graded failed: %s", exc)

    # Build live index per-league: (date, home_norm, away_norm) -> (status, ftr, hg, ag)
    live_by_league: dict[str, dict] = {}
    pred_leagues = {p.league for p in payload.predictions}
    for lk in pred_leagues:
        cfg = LEAGUES.get(lk)
        if cfg is None:
            continue
        try:
            live_by_league[lk] = load_live_matches_for_code(cfg.code)
        except Exception as exc:  # pragma: no cover
            logger.warning("[api] load_live_matches_for_code(%s) failed: %s", lk, exc)
            live_by_league[lk] = {}

    enriched: list[PredictionOut] = []
    for p in payload.predictions:
        home_n = _norm(p.home_team)
        away_n = _norm(p.away_team)
        try:
            match_date = datetime.strptime(p.date, "%Y-%m-%d").date()
        except ValueError:
            enriched.append(p)
            continue

        is_live = False
        pick_correct: bool | None = None
        ft_score: str | None = None

        live_map = live_by_league.get(p.league, {})
        live_hit = live_map.get((match_date, home_n, away_n))
        if live_hit is not None:
            status, ftr, hg, ag = live_hit
            ft_score = f"{hg}-{ag}"
            if status == "live":
                is_live = True
            elif status == "completed":
                pick_correct = ftr == p.most_likely

        # Graded (CSV / authoritative) overrides live-completed.
        g = graded_idx.get((p.league, p.date, home_n, away_n))
        if g is not None:
            g_status = getattr(g, "status", "pending")
            if g_status == "won":
                pick_correct = True
                ft_score = getattr(g, "ft_score", ft_score) or ft_score
                is_live = False
            elif g_status == "lost":
                pick_correct = False
                ft_score = getattr(g, "ft_score", ft_score) or ft_score
                is_live = False

        enriched.append(
            p.model_copy(
                update={
                    "is_live": is_live,
                    "pick_correct": pick_correct,
                    "ft_score": ft_score,
                }
            )
        )

    return TodayPayload(
        generated_at=payload.generated_at,
        predictions=enriched,
        value_bets=payload.value_bets,
        data_sources=payload.data_sources,
    )


def get_today_payload(league: str | None = None) -> TodayPayload:
    """Prefer cached snapshot; fall back to on-demand prediction."""
    snapshot = load_today()
    source = "snapshot"
    if snapshot is None:
        source = "on-demand"
        fixtures_file = _latest_fixtures_file()
        if fixtures_file is None:
            logger.info("[api] /predictions/today — no snapshot, no fixtures file; returning empty.")
            return TodayPayload(generated_at=datetime.utcnow())
        try:
            data = json.loads(fixtures_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("[api] /predictions/today — malformed fixtures file %s", fixtures_file)
            return TodayPayload(generated_at=datetime.utcnow())
        logger.info("[api] /predictions/today — no snapshot; computing on-demand from %s", fixtures_file.name)
        snapshot = build_predictions_for_fixtures(data)

    snapshot = _enrich_predictions_with_live_and_graded(snapshot)

    _log_snapshot_served(snapshot, source, league)

    if league is not None:
        league = league.upper()
        snapshot = TodayPayload(
            generated_at=snapshot.generated_at,
            predictions=[p for p in snapshot.predictions if p.league == league],
            value_bets=[v for v in snapshot.value_bets if v.league == league],
            data_sources=[d for d in snapshot.data_sources if d.league == league],
        )
    return snapshot


def get_history(days: int | None = 14) -> HistoryPayload:
    """Aggregate graded bets by date (newest first), capped at ``days``.

    Self-heals: captures today's snapshot (idempotent) and re-grades all
    persisted snapshots against the latest CSV archive before reading.
    """
    from football_betting.evaluation.grader import load_graded
    from football_betting.evaluation.pipeline import (
        capture_today_snapshot,
        regrade_all,
    )

    try:
        capture_today_snapshot()
        regrade_all()
    except Exception as exc:  # pragma: no cover — never block the endpoint
        logger.warning("[api] /history refresh failed: %s", exc)

    graded = load_graded()
    by_date: dict[str, list[GradedBetOut]] = defaultdict(list)
    for g in graded:
        by_date[g.date].append(
            GradedBetOut(
                date=g.date,
                league=g.league,
                league_name=g.league_name,
                home_team=g.home_team,
                away_team=g.away_team,
                outcome=g.outcome,
                bet_label=g.bet_label,
                odds=g.odds,
                stake=g.stake,
                ft_result=g.ft_result,
                ft_score=g.ft_score,
                status=g.status,
                pnl=g.pnl,
                kind=g.kind,
            )
        )

    day_rows: list[HistoryDayOut] = []
    for d in sorted(by_date.keys(), reverse=True):
        bets = by_date[d]
        won = sum(1 for b in bets if b.status == "won")
        lost = sum(1 for b in bets if b.status == "lost")
        pending = sum(1 for b in bets if b.status == "pending")
        pnl = round(sum(b.pnl for b in bets), 2)
        day_rows.append(HistoryDayOut(
            date=d, n_bets=len(bets), n_won=won, n_lost=lost,
            n_pending=pending, pnl=pnl, bets=bets,
        ))

    if days is not None and days > 0:
        day_rows = day_rows[:days]

    total_bets = sum(r.n_bets for r in day_rows)
    total_won = sum(r.n_won for r in day_rows)
    total_lost = sum(r.n_lost for r in day_rows)
    total_pending = sum(r.n_pending for r in day_rows)
    total_pnl = round(sum(r.pnl for r in day_rows), 2)
    settled = total_won + total_lost
    hit_rate = round(total_won / settled, 4) if settled > 0 else None

    return HistoryPayload(
        generated_at=datetime.utcnow(),
        n_days=len(day_rows),
        total_bets=total_bets,
        total_won=total_won,
        total_lost=total_lost,
        total_pending=total_pending,
        total_pnl=total_pnl,
        hit_rate=hit_rate,
        days=day_rows,
    )


def _log_snapshot_served(payload: TodayPayload, source: str, league: str | None) -> None:
    """Emit a human-readable trace of the data backing this response."""
    filter_txt = f" filter={league.upper()}" if league else ""
    logger.info(
        "[api] /predictions/today served from %s (generated_at=%s, %d preds, %d value bets)%s",
        source, payload.generated_at.isoformat(timespec="seconds"),
        len(payload.predictions), len(payload.value_bets), filter_txt,
    )
    if not payload.data_sources:
        logger.info("[api]   ↳ no data-source metadata (legacy snapshot — regenerate with `fb snapshot`).")
        return
    for ds in payload.data_sources:
        logger.info(
            "[api]   ↳ %s (%s): model=%s | %d hist. matches | seasons=%s | range=%s | "
            "sofascore=%d | %d predictions",
            ds.league_name, ds.league, ds.model, ds.n_matches,
            ",".join(ds.seasons), ds.date_range or "n/a",
            ds.sofascore_matches_ingested, ds.n_predictions,
        )


# ─────────────────────────────────────────────────────────────────
# Pi-Ratings & form
# ─────────────────────────────────────────────────────────────────

def _ratings_for_league(league_key: str) -> PiRatings:
    cache_key = f"pi_ratings:{league_key}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    matches = load_league(league_key)
    ratings = PiRatings()
    ratings.fit(matches)
    cache.set(cache_key, ratings, ttl=300.0)
    return ratings


def get_league_ratings(league_key: str, top: int = 20) -> list[RatingRow]:
    ratings = _ratings_for_league(league_key.upper())
    rows = []
    for rank, (team, r) in enumerate(ratings.top_n(top), 1):
        rows.append(
            RatingRow(
                rank=rank,
                team=team,
                pi_home=round(r.home, 3),
                pi_away=round(r.away, 3),
                pi_overall=round(r.overall, 3),
            )
        )
    return rows


def get_league_form(league_key: str, top: int = 20, last_n: int = 5) -> list[FormRow]:
    league_key = league_key.upper()
    cache_key = f"league_form:{league_key}:{top}:{last_n}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    matches = load_league(league_key)
    matches.sort(key=lambda m: m.date)

    per_team: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    for m in matches:
        per_team[m.home_team].append(("H", m.home_goals, m.away_goals))
        per_team[m.away_team].append(("A", m.away_goals, m.home_goals))

    rows: list[FormRow] = []
    for team, history in per_team.items():
        recent = history[-last_n:]
        if not recent:
            continue
        last5 = ""
        points = 0
        gf = 0
        ga = 0
        for _, scored, conceded in recent:
            gf += scored
            ga += conceded
            if scored > conceded:
                last5 += "W"
                points += 3
            elif scored == conceded:
                last5 += "D"
                points += 1
            else:
                last5 += "L"
        rows.append(
            FormRow(team=team, last5=last5, points=points, goals_for=gf, goals_against=ga)
        )

    rows.sort(key=lambda r: (-r.points, -(r.goals_for - r.goals_against)))
    rows = rows[:top]
    cache.set(cache_key, rows, ttl=300.0)
    return rows


def get_league_summaries() -> list[LeagueRatingSummary]:
    """Lightweight per-league snapshot for the /leagues index page."""
    summaries: list[LeagueRatingSummary] = []
    for key, cfg in LEAGUES.items():
        try:
            ratings = _ratings_for_league(key)
        except FileNotFoundError:
            summaries.append(
                LeagueRatingSummary(
                    league=key, league_name=cfg.name, n_teams=0,
                )
            )
            continue
        top = ratings.top_n(1)
        leader, rating = (top[0][0], round(top[0][1].overall, 3)) if top else (None, None)
        summaries.append(
            LeagueRatingSummary(
                league=key,
                league_name=cfg.name,
                leader=leader,
                leader_rating=rating,
                n_teams=len(ratings.ratings),
            )
        )
    return summaries


def get_team_detail(league_key: str, team: str) -> TeamDetail | None:
    league_key = league_key.upper()
    matches = load_league(league_key)
    matches.sort(key=lambda m: m.date)

    team_matches = [m for m in matches if m.home_team == team or m.away_team == team]
    if not team_matches:
        return None

    ratings = _ratings_for_league(league_key)
    r = ratings.get(team)

    last10 = ""
    gf_total = 0
    ga_total = 0
    recent = team_matches[-10:]
    for m in recent:
        if m.home_team == team:
            scored, conceded = m.home_goals, m.away_goals
        else:
            scored, conceded = m.away_goals, m.home_goals
        gf_total += scored
        ga_total += conceded
        if scored > conceded:
            last10 += "W"
        elif scored == conceded:
            last10 += "D"
        else:
            last10 += "L"

    n = max(len(recent), 1)
    return TeamDetail(
        team=team,
        league=league_key,
        pi_home=round(r.home, 3),
        pi_away=round(r.away, 3),
        pi_overall=round(r.overall, 3),
        last10=last10,
        goals_for_avg=round(gf_total / n, 2),
        goals_against_avg=round(ga_total / n, 2),
    )


# ─────────────────────────────────────────────────────────────────
# Performance dashboard
# ─────────────────────────────────────────────────────────────────

def _load_tracker() -> ResultsTracker:
    """Load the canonical tracker and *always* merge in graded-bet history.

    ``predictions_log.json`` typically carries many ``pending`` entries
    while the daily/live pipeline writes settled outcomes to
    ``graded_bets.jsonl``. The previous "if-empty fallback" silently
    skipped graded history whenever the tracker file existed (which is
    nearly always), so ``/performance/summary`` and
    ``/performance/bankroll`` would report 0 bets even though graded
    results were on disk. We now merge both sources, dedup on
    ``(date, league, home, away, outcome)``, with graded rows winning on
    conflict so the latest CSV/Odds-API result is reflected.
    """
    from football_betting.evaluation.grader import graded_as_prediction_records
    from football_betting.tracking.tracker import PredictionRecord

    tracker = ResultsTracker()
    tracker.load()

    def _key(r: PredictionRecord) -> tuple:
        return (r.date, r.league, r.home_team, r.away_team, r.bet_outcome)

    merged: dict[tuple, PredictionRecord] = {}
    for rec in tracker.records:
        merged[_key(rec)] = rec
    for rec in graded_as_prediction_records():  # graded wins on conflict
        merged[_key(rec)] = rec
    tracker.records = list(merged.values())
    return tracker


def _max_drawdown_pct(curve: list[BankrollPoint]) -> float:
    if not curve:
        return 0.0
    peak = curve[0].value
    max_dd = 0.0
    for p in curve:
        if p.value > peak:
            peak = p.value
        if peak > 0:
            dd = (peak - p.value) / peak
            if dd > max_dd:
                max_dd = dd
    return round(max_dd * 100, 2)


def get_bankroll_curve(initial_bankroll: float = 1000.0) -> list[BankrollPoint]:
    """Aggregate completed bets into a one-point-per-day equity curve.

    Multiple bets on the same calendar day previously each produced their
    own ``BankrollPoint`` with the same ``date`` value, so Recharts
    rendered them stacked at the same X-coordinate and the visible
    entry for that day looked stuck on the *first* per-bet bankroll
    (often the opening 1000.00) instead of the day's end-of-day result.

    We now sum P&L per day and emit exactly one point per date carrying
    the closing bankroll. The very first point anchors the chart at the
    initial bankroll on the day before the first settled bet.
    """
    from datetime import date as _date
    from datetime import timedelta

    tracker = _load_tracker()
    completed = tracker.completed_bets()
    completed.sort(key=lambda r: r.date)

    if not completed:
        return [BankrollPoint(date=_date.today().isoformat(),
                              value=round(initial_bankroll, 2))]

    daily_pnl: dict[str, float] = defaultdict(float)
    for rec in completed:
        stake = rec.bet_stake or 0.0
        if rec.bet_status == "won" and rec.bet_odds:
            daily_pnl[rec.date] += stake * (rec.bet_odds - 1)
        elif rec.bet_status == "lost":
            daily_pnl[rec.date] -= stake

    sorted_dates = sorted(daily_pnl.keys())
    try:
        anchor = (
            _date.fromisoformat(sorted_dates[0]) - timedelta(days=1)
        ).isoformat()
    except ValueError:
        anchor = sorted_dates[0]

    bankroll = initial_bankroll
    curve: list[BankrollPoint] = [
        BankrollPoint(date=anchor, value=round(bankroll, 2))
    ]
    for d in sorted_dates:
        bankroll += daily_pnl[d]
        curve.append(BankrollPoint(date=d, value=round(bankroll, 2)))
    return curve


def get_performance_summary() -> PerformanceSummary:
    tracker = _load_tracker()
    stats = tracker.roi_stats()
    completed = tracker.completed_bets()

    per_league_buckets: dict[str, list] = defaultdict(list)
    for rec in completed:
        per_league_buckets[rec.league].append(rec)

    per_league: list[PerformancePerLeague] = []
    for league_key, recs in per_league_buckets.items():
        if not recs:
            continue
        wins = sum(1 for r in recs if r.bet_status == "won")
        total_stake = sum((r.bet_stake or 0.0) for r in recs)
        profit = 0.0
        for r in recs:
            stake = r.bet_stake or 0.0
            if r.bet_status == "won" and r.bet_odds:
                profit += stake * (r.bet_odds - 1)
            elif r.bet_status == "lost":
                profit -= stake
        per_league.append(
            PerformancePerLeague(
                league=league_key,
                league_name=LEAGUES.get(league_key, type("X", (), {"name": league_key})()).name
                if league_key in LEAGUES
                else league_key,
                n_bets=len(recs),
                hit_rate=round(wins / len(recs), 4),
                roi=round(profit / total_stake, 4) if total_stake > 0 else 0.0,
            )
        )

    bankroll_curve = get_bankroll_curve()
    max_dd = _max_drawdown_pct(bankroll_curve)

    return PerformanceSummary(
        n_predictions=len(tracker.records),
        n_bets=int(stats.get("n_bets", 0)),
        hit_rate=round(stats.get("hit_rate", 0.0), 4),
        roi=round(stats.get("roi", 0.0), 4),
        total_profit=round(stats.get("total_profit", 0.0), 2),
        total_stake=round(stats.get("total_stake", 0.0), 2),
        brier_mean=None,
        rps_mean=None,
        max_drawdown_pct=max_dd,
        per_league=sorted(per_league, key=lambda p: -p.n_bets),
    )


# ─────────────────────────────────────────────────────────────────
# Public (anonymised) performance index
# ─────────────────────────────────────────────────────────────────

_PERFORMANCE_INDEX_CACHE_KEY = "performance_index:public"
_PERFORMANCE_INDEX_TTL = 3600.0  # 1 hour


def invalidate_performance_cache() -> None:
    """Evict only the performance-related cache entries.

    Called by the grading pipeline / live-settle loop after
    ``performance.json`` has been rewritten, so the next request to
    ``/performance/index`` reads fresh data without flushing unrelated
    entries (SEO slugs, Pi-Ratings, form tables, …).
    """
    cache.delete(_PERFORMANCE_INDEX_CACHE_KEY)


def get_performance_index() -> PerformanceIndexOut:
    """Return the anonymised public performance index.

    Prefers the pre-computed `performance.json` artefact written by
    `fb update-performance`; falls back to on-the-fly computation so the
    endpoint works even without the cron job.

    Self-heals like ``/history``: captures today's snapshot (idempotent)
    and re-grades all persisted snapshots before reading, so the
    homepage Transparency Tracker shows the same fresh pipeline data
    that the ``/performance`` page receives — without having to wait for
    the daily cron or the in-memory TTL to expire.

    The cache is keyed by the on-disk mtime of ``performance.json`` so
    out-of-band rewrites (cron, manual ``fb update-performance``,
    pipeline) are picked up on the very next request.
    """
    from football_betting.config import PREDICTIONS_DIR
    from football_betting.tracking import performance_index as pi

    public_path = PREDICTIONS_DIR / pi.PUBLIC_FILENAME

    try:
        from football_betting.evaluation.pipeline import (
            capture_today_snapshot,
            regrade_all,
        )

        capture_today_snapshot()
        regrade_all()
    except Exception as exc:  # pragma: no cover — never block the endpoint
        logger.warning("[api] /performance/index refresh failed: %s", exc)

    mtime = public_path.stat().st_mtime if public_path.exists() else 0.0
    cache_key = f"{_PERFORMANCE_INDEX_CACHE_KEY}:{mtime}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    payload: dict | None = None
    if public_path.exists():
        try:
            payload = json.loads(public_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning(
                "[api] /performance/index — malformed %s, recomputing.", public_path
            )
            payload = None

    if payload is None:
        payload, _ = pi.compute_payloads()

    result = PerformanceIndexOut(
        updated_at=payload.get("updated_at", ""),
        tracking_started_at=payload.get(
            "tracking_started_at", pi.TRACKING_START_DEFAULT
        ),
        n_days_tracked=int(payload.get("n_days_tracked", 0)),
        n_bets=int(payload.get("n_bets", 0)),
        hit_rate=payload.get("hit_rate"),
        current_index=float(payload.get("current_index", 100.0)),
        all_time_high_index=float(payload.get("all_time_high_index", 100.0)),
        max_drawdown_pct=float(payload.get("max_drawdown_pct", 0.0)),
        current_drawdown_pct=float(payload.get("current_drawdown_pct", 0.0)),
        equity_curve=[
            EquityIndexPoint(
                date=p["date"],
                index=float(p["index"]),
                n_bets_cumulative=int(p["n_bets_cumulative"]),
            )
            for p in payload.get("equity_curve", [])
        ],
        rule_hash=payload.get("rule_hash", ""),
        model_version=payload.get("model_version", pi.MODEL_VERSION),
    )
    cache.set(cache_key, result, ttl=_PERFORMANCE_INDEX_TTL)
    return result


# ─────────────────────────────────────────────────────────────────
# SEO match-prediction pages
# ─────────────────────────────────────────────────────────────────

def get_upcoming_match_slugs(league: str | None = None) -> MatchSlugsOut:
    """Slug list for ``/leagues/{league}/{match}`` SEO routes + sitemap."""
    from football_betting.seo.match_slugs import build_slug

    snapshot = load_today()
    if snapshot is None:
        return MatchSlugsOut(league=league, n_matches=0, matches=[])

    matches: list[MatchSlugOut] = []
    seen: set[str] = set()
    for p in snapshot.predictions:
        if league and p.league.upper() != league.upper():
            continue
        slug = build_slug(p.home_team, p.away_team, p.date)
        if slug in seen:
            continue
        seen.add(slug)
        matches.append(
            MatchSlugOut(
                slug=slug,
                league=p.league,
                league_name=p.league_name,
                home_team=p.home_team,
                away_team=p.away_team,
                date=p.date,
                kickoff_time=p.kickoff_time,
            )
        )
    return MatchSlugsOut(league=league, n_matches=len(matches), matches=matches)


def get_match_wrapper(slug: str) -> MatchWrapperOut | None:
    """Return the SEO wrapper (prose + probabilities) for a slug, or None."""
    from football_betting.seo.match_slugs import (
        attach_archive,
        build_wrapper,
        find_match_in_snapshot,
    )

    snapshot = load_today()
    if snapshot is None:
        return None
    pred = find_match_in_snapshot(snapshot, slug)
    if pred is None:
        return None

    league_name = pred.league_name
    if pred.league in LEAGUES:
        league_name = LEAGUES[pred.league].name

    wrapper = build_wrapper(pred, league_name=league_name)
    wrapper = attach_archive(wrapper)
    return MatchWrapperOut(
        slug=wrapper.slug,
        league=wrapper.league,
        league_name=wrapper.league_name,
        home_team=wrapper.home_team,
        away_team=wrapper.away_team,
        kickoff=wrapper.kickoff,
        prob_home=wrapper.prob_home,
        prob_draw=wrapper.prob_draw,
        prob_away=wrapper.prob_away,
        pick=wrapper.pick,  # type: ignore[arg-type]
        prose=wrapper.prose,
        is_archived=wrapper.is_archived,
        actual_result=wrapper.actual_result,  # type: ignore[arg-type]
        actual_score=wrapper.actual_score,
        pick_correct=wrapper.pick_correct,
    )


def get_league_fixtures(league_key: str, limit: int = 5) -> LeagueFixturesOut:
    """Return next-N upcoming fixtures + last-N past results for one league.

    * ``next_5`` is sourced from today's snapshot, filtered by league and
      ordered by date / kickoff time. Each row carries the calibrated
      probabilities and the deterministic SEO slug used by
      ``/leagues/{league}/{match}``.
    * ``last_5`` is sourced from ``data/raw/`` CSVs through
      :func:`football_betting.data.loader.load_league` so it reflects the
      authoritative historical archive. ``pick_correct`` is computed from
      the persisted prediction log when a model pick exists for the same
      match.
    """
    from football_betting.data.loader import load_league
    from football_betting.seo.match_slugs import build_slug
    from football_betting.tracking.tracker import ResultsTracker

    league_key = league_key.upper()
    league_name = LEAGUES[league_key].name if league_key in LEAGUES else league_key

    next_rows: list[LeagueFixtureOut] = []
    snapshot = load_today()
    if snapshot is not None:
        upcoming = [p for p in snapshot.predictions if p.league.upper() == league_key]
        upcoming.sort(key=lambda p: (p.date, p.kickoff_time or ""))
        for p in upcoming[:limit]:
            next_rows.append(
                LeagueFixtureOut(
                    date=p.date,
                    home_team=p.home_team,
                    away_team=p.away_team,
                    kickoff_time=p.kickoff_time,
                    prob_home=round(p.prob_home, 4),
                    prob_draw=round(p.prob_draw, 4),
                    prob_away=round(p.prob_away, 4),
                    most_likely=p.most_likely,
                    slug=build_slug(p.home_team, p.away_team, p.date),
                )
            )

    # Build a map of model picks for the last fixtures we report.
    pick_by_key: dict[tuple[str, str, str], str] = {}
    try:
        tracker = ResultsTracker()
        tracker.load()
        for rec in tracker.records:
            if rec.league.upper() != league_key:
                continue
            probs = (rec.prob_home, rec.prob_draw, rec.prob_away)
            pick = ("H", "D", "A")[probs.index(max(probs))]
            pick_by_key[(rec.date, rec.home_team, rec.away_team)] = pick
    except Exception:  # pragma: no cover — missing log is fine
        pick_by_key = {}

    last_rows: list[LeagueFixtureOut] = []
    try:
        matches = load_league(league_key)
        matches.sort(key=lambda m: m.date, reverse=True)
        for m in matches[:limit]:
            pick = pick_by_key.get((m.date.isoformat(), m.home_team, m.away_team))
            last_rows.append(
                LeagueFixtureOut(
                    date=m.date.isoformat(),
                    home_team=m.home_team,
                    away_team=m.away_team,
                    home_goals=m.home_goals,
                    away_goals=m.away_goals,
                    result=m.result,
                    pick_correct=(pick == m.result) if pick else None,
                    slug=build_slug(m.home_team, m.away_team, m.date),
                )
            )
    except FileNotFoundError:
        last_rows = []
    except Exception as exc:  # pragma: no cover — never 500 SEO endpoint
        logger.warning(
            "[api] /leagues/%s/fixtures: load_league failed: %s", league_key, exc
        )
        last_rows = []

    return LeagueFixturesOut(
        league=league_key,
        league_name=league_name,
        next_5=next_rows,
        last_5=last_rows,
    )
