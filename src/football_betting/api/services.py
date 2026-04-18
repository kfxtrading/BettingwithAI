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
    HealthOut,
    LeagueOut,
    LeagueRatingSummary,
    ModelAvailability,
    OddsOut,
    PerformanceIndexOut,
    PerformancePerLeague,
    PerformanceSummary,
    PredictionOut,
    RatingRow,
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
    "get_performance_summary",
    "get_performance_index",
    "get_bankroll_curve",
    "get_team_detail",
    "list_leagues",
]


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


def _latest_fixtures_file() -> Path | None:
    candidates = sorted(DATA_DIR.glob("fixtures_*.json"))
    return candidates[-1] if candidates else None


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
    tracker = ResultsTracker()
    tracker.load()
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
    tracker = _load_tracker()
    completed = tracker.completed_bets()
    completed.sort(key=lambda r: r.date)

    bankroll = initial_bankroll
    curve: list[BankrollPoint] = [
        BankrollPoint(date=completed[0].date if completed else date.today().isoformat(),
                       value=round(bankroll, 2))
    ]
    for rec in completed:
        stake = rec.bet_stake or 0.0
        if rec.bet_status == "won" and rec.bet_odds:
            bankroll += stake * (rec.bet_odds - 1)
        elif rec.bet_status == "lost":
            bankroll -= stake
        curve.append(BankrollPoint(date=rec.date, value=round(bankroll, 2)))
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


def get_performance_index() -> PerformanceIndexOut:
    """Return the anonymised public performance index.

    Prefers the pre-computed `performance.json` artefact written by
    `fb update-performance`; falls back to on-the-fly computation so the
    endpoint works even without the cron job.
    """
    cached = cache.get(_PERFORMANCE_INDEX_CACHE_KEY)
    if cached is not None:
        return cached

    from football_betting.config import PREDICTIONS_DIR
    from football_betting.tracking import performance_index as pi

    public_path = PREDICTIONS_DIR / pi.PUBLIC_FILENAME
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
    cache.set(_PERFORMANCE_INDEX_CACHE_KEY, result, ttl=_PERFORMANCE_INDEX_TTL)
    return result

