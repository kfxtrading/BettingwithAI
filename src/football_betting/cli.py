"""
Football Betting Model CLI — v0.3.

Commands:
    fb download          — Fetch football-data.co.uk CSVs
    fb rate              — Show pi-ratings top-N
    fb train             — Train CatBoost + calibrator
    fb train-mlp         — Train PyTorch MLP (v0.3)
    fb train-support     — Train FAQ intent classifier (v0.3.1)
    fb predict           — Predict fixtures from JSON
    fb backtest          — Walk-forward backtest
    fb tune-ensemble     — Dirichlet-sampled weight tuning
    fb scrape            — Scrape Sofascore xG + lineups (v0.3)
    fb fetch-fixtures    — Pull today's fixtures + odds from The Odds API
    fb monitor           — Feature drift report (v0.3)
    fb export-onnx       — Export MLP to ONNX (v0.3)
    fb update-results    — Update prediction log
    fb stats             — Show betting performance
    fb update-performance — Refresh public performance-index JSONs
    fb snapshot          — Generate JSON snapshot for the web UI
    fb serve             — Run the FastAPI server for the web UI
"""
from __future__ import annotations

import json
from pathlib import Path

import click
import pandas as pd
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from football_betting.betting.value import find_value_bets, rank_value_bets
from football_betting.config import DATA_DIR, LEAGUES, MODELS_DIR
from football_betting.data.downloader import download_all
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture, MatchOdds
from football_betting.data.odds_snapshots import (
    append_snapshot as append_odds_snapshot,
)
from football_betting.data.odds_snapshots import (
    load_into_tracker as load_odds_snapshots,
)
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.ensemble import EnsembleModel
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.rating.pi_ratings import PiRatings
from football_betting.scraping.sofascore import SofascoreClient
from football_betting.tracking.backtest import Backtester
from football_betting.tracking.monitoring import DriftDetector
from football_betting.tracking.tracker import PredictionRecord, ResultsTracker

console = Console()


@click.group()
@click.version_option("0.3.1")
def main() -> None:
    """Football Betting Model v0.3 — CatBoost + MLP + pi-Ratings + Sofascore xG."""


# ───────────────────────── download ─────────────────────────

@main.command()
@click.option("--league", "-l", type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False), default="all")
@click.option("--seasons", "-s", multiple=True,
              default=("2021-22", "2022-23", "2023-24", "2024-25", "2025-26"))
@click.option("--force", is_flag=True)
def download(league: str, seasons: tuple[str, ...], force: bool) -> None:
    """Download football-data.co.uk historical CSVs."""
    keys = list(LEAGUES.keys()) if league.lower() == "all" else [league.upper()]
    download_all(league_keys=keys, seasons=list(seasons), force=force)


# ───────────────────────── rate ─────────────────────────

@main.command()
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True)
@click.option("--top", "-n", default=10)
def rate(league: str, top: int) -> None:
    """Show pi-ratings top-N."""
    league = league.upper()
    matches = load_league(league)
    ratings = PiRatings()
    ratings.fit(matches)

    table = Table(title=f"Pi-Ratings — {LEAGUES[league].name}")
    table.add_column("Rank", justify="right")
    table.add_column("Team")
    table.add_column("Home", justify="right")
    table.add_column("Away", justify="right")
    table.add_column("Overall", justify="right")
    for rank, (team, r) in enumerate(ratings.top_n(top), 1):
        table.add_row(str(rank), team, f"{r.home:+.3f}", f"{r.away:+.3f}", f"{r.overall:+.3f}")
    console.print(table)


# ───────────────────────── scrape (v0.3) ─────────────────────────

@main.command()
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True)
@click.option("--seasons", "-s", multiple=True, default=("2024-25", "2025-26"))
@click.option("--with-stats/--no-stats", default=True, help="Also fetch xG + lineups per match")
@click.option("--max-matches", default=None, type=int, help="Limit for testing")
def scrape(league: str, seasons: tuple[str, ...], with_stats: bool, max_matches: int | None) -> None:
    """Scrape Sofascore data for xG + lineups (v0.3)."""
    league = league.upper()
    client = SofascoreClient()

    if not client.cfg.enabled:
        console.print(
            "[red]Sofascore scraping disabled.[/red]\n"
            "Enable with: export SCRAPING_ENABLED=1"
        )
        raise click.Abort()

    console.log(f"[yellow]Note: Waiting {client.cfg.request_delay_seconds}s between requests[/yellow]")

    for season in seasons:
        console.rule(f"[bold cyan]Scraping {LEAGUES[league].name} — {season}[/bold cyan]")

        # Get all events for season
        events = client.get_season_events(league, season)
        console.log(f"Found {len(events)} events")

        if max_matches:
            events = events[:max_matches]

        matches = []
        with Progress(console=console) as progress:
            task = progress.add_task("Scraping matches…", total=len(events))
            for event in events:
                match = client.parse_match(event)
                if match is None:
                    progress.advance(task)
                    continue
                if with_stats and match.status == "finished":
                    match = client.enrich_match_with_stats(match)
                matches.append(match)
                progress.advance(task)

        path = client.save_matches(matches, league, season)
        console.log(f"[green]Saved: {path}[/green]")

    # Show cache stats
    stats = client.cache.stats()
    console.print(
        f"[dim]Cache: {stats['entries']} entries, "
        f"{stats['total_bytes'] / 1024 / 1024:.1f} MB[/dim]"
    )


# ───────────────────────── fetch-fixtures (Odds API) ─────────────────────────

@main.command("fetch-fixtures")
@click.option(
    "--date", "target_date",
    default=None,
    help="ISO date (YYYY-MM-DD) — defaults to today in the server timezone.",
)
@click.option(
    "--league", "-l",
    type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False),
    default="all",
)
@click.option(
    "--out", "-o",
    type=click.Path(),
    default=None,
    help="Output path (default: data/fixtures_<date>.json).",
)
def fetch_fixtures(target_date: str | None, league: str, out: str | None) -> None:
    """Pull scheduled fixtures + consensus odds from The Odds API."""
    from datetime import date as date_cls

    from football_betting.config import DATA_DIR
    from football_betting.scraping.odds_api import OddsApiClient, OddsApiError

    day = date_cls.fromisoformat(target_date) if target_date else date_cls.today()
    keys = list(LEAGUES.keys()) if league.lower() == "all" else [league.upper()]

    client = OddsApiClient()
    try:
        fixtures = client.fetch_all_leagues_for_date(day, leagues=keys)
    except OddsApiError as exc:
        console.print(f"[red]Odds API error: {exc}[/red]")
        raise click.Abort() from exc

    if not fixtures:
        console.print(
            f"[yellow]No fixtures found for {day.isoformat()} in leagues "
            f"{', '.join(keys)}.[/yellow]"
        )
        raise click.Abort()

    payload = [f.to_fixture_dict() for f in fixtures]
    out_path = Path(out) if out else DATA_DIR / f"fixtures_{day.isoformat()}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    table = Table(title=f"Fixtures — {day.isoformat()}")
    table.add_column("League"); table.add_column("Kickoff")
    table.add_column("Match"); table.add_column("Odds (H/D/A)", justify="right")
    table.add_column("Books", justify="right")
    for f in sorted(fixtures, key=lambda x: (x.league, x.kickoff_local)):
        table.add_row(
            f.league, f.kickoff_local,
            f"{f.home_team} vs {f.away_team}",
            f"{f.odds_home:.2f} / {f.odds_draw:.2f} / {f.odds_away:.2f}",
            str(f.n_bookmakers),
        )
    console.print(table)
    console.log(f"[green]Wrote {len(fixtures)} fixtures -> {out_path}[/green]")


# ───────────────────────── train ─────────────────────────

@main.command()
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True)
@click.option("--seasons", "-s", multiple=True,
              default=("2021-22", "2022-23", "2023-24", "2024-25"))
@click.option("--warmup", default=100)
@click.option("--calibrate/--no-calibrate", default=True)
@click.option("--use-sofascore/--no-sofascore", default=True,
              help="Ingest pre-scraped Sofascore data if present")
def train(league: str, seasons: tuple[str, ...], warmup: int, calibrate: bool,
          use_sofascore: bool) -> None:
    """Train CatBoost + calibrator."""
    league = league.upper()
    matches = load_league(league, seasons=list(seasons))

    fb = FeatureBuilder()

    # Stage Sofascore data — consumed chronologically in build_training_data
    if use_sofascore:
        total_staged = 0
        for season in seasons:
            sf_data = SofascoreClient.load_matches(league, season)
            if sf_data:
                total_staged += fb.stage_sofascore_batch(sf_data)
        if total_staged > 0:
            console.log(f"[green]Staged Sofascore data: {total_staged} matches[/green]")
        else:
            console.log("[yellow]No Sofascore data found — using xG proxy[/yellow]")

    predictor = CatBoostPredictor(feature_builder=fb)
    console.log(f"[cyan]Training CatBoost for {LEAGUES[league].name}…[/cyan]")
    result = predictor.fit(matches, warmup_games=warmup, calibrate=calibrate)

    model_path = MODELS_DIR / f"catboost_{league}.cbm"
    predictor.save(model_path)
    console.log(f"[green]Model saved: {model_path}[/green]")

    console.print("\n[bold]Training summary[/bold]")
    console.print(f"  Samples: train={result['n_train']}, val={result['n_val']}")
    console.print(f"  Features: {result['n_features']}")

    table = Table(title="Top 15 features")
    table.add_column("Feature")
    table.add_column("Importance", justify="right")
    for feat, imp in result["feature_importance"][:15]:
        table.add_row(feat, f"{imp:.2f}")
    console.print(table)


# ───────────────────────── train-mlp (v0.3) ─────────────────────────

@main.command("train-mlp")
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True)
@click.option("--seasons", "-s", multiple=True,
              default=("2021-22", "2022-23", "2023-24", "2024-25"))
@click.option("--warmup", default=100)
def train_mlp(league: str, seasons: tuple[str, ...], warmup: int) -> None:
    """Train PyTorch MLP classifier (v0.3)."""
    league = league.upper()
    matches = load_league(league, seasons=list(seasons))

    fb = FeatureBuilder()
    for season in seasons:
        sf_data = SofascoreClient.load_matches(league, season)
        if sf_data:
            fb.stage_sofascore_batch(sf_data)

    mlp = MLPPredictor(feature_builder=fb)
    console.log(f"[cyan]Training MLP for {LEAGUES[league].name}…[/cyan]")
    result = mlp.fit(matches, warmup_games=warmup)

    path = MODELS_DIR / f"mlp_{league}.pt"
    mlp.save(path)
    console.log(f"[green]MLP saved: {path}[/green]")
    console.print(f"  n_train={result['n_train']}, n_val={result['n_val']}")
    console.print(f"  best_val_loss={result['best_val_loss']:.4f}")


# ───────────────────────── train-support (v0.3.1) ─────────────────────────

@main.command("train-support")
@click.option(
    "--lang",
    default="all",
    help="Language code (en|de|es|fr|it) or 'all'.",
)
@click.option(
    "--dataset",
    "dataset_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to dataset_augmented.jsonl (default: data/support_faq/…)",
)
@click.option(
    "--out-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: models/support).",
)
def train_support(lang: str, dataset_path: Path | None, out_dir: Path | None) -> None:
    """Train TF-IDF + Logistic Regression FAQ intent classifier per locale."""
    from football_betting.config import SUPPORT_CFG
    from football_betting.support.trainer import train_all

    if lang.lower() == "all":
        langs: list[str] | None = None
    else:
        lg = lang.lower()
        if lg not in SUPPORT_CFG.languages:
            raise click.BadParameter(
                f"lang must be one of {('all', *SUPPORT_CFG.languages)}"
            )
        langs = [lg]

    train_all(langs=langs, dataset_path=dataset_path, out_dir=out_dir)


# ───────────────────────── export-onnx (v0.3) ─────────────────────────

@main.command("export-onnx")
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True)
def export_onnx(league: str) -> None:
    """Export trained MLP to ONNX format."""
    league = league.upper()
    model_path = MODELS_DIR / f"mlp_{league}.pt"
    if not model_path.exists():
        console.print(f"[red]No MLP at {model_path}[/red]")
        raise click.Abort()

    fb = FeatureBuilder()
    mlp = MLPPredictor(feature_builder=fb)
    mlp.load(model_path)

    onnx_path = MODELS_DIR / f"mlp_{league}.onnx"
    mlp.export_onnx(onnx_path)


# ───────────────────────── predict ─────────────────────────

@main.command()
@click.option("--fixtures", "-f", required=True, type=click.Path(exists=True))
@click.option("--bankroll", "-b", default=1000.0)
@click.option("--save/--no-save", default=True)
def predict(fixtures: str, bankroll: float, save: bool) -> None:
    """Predict fixtures from a JSON file."""
    fixtures_data = json.loads(Path(fixtures).read_text())
    by_league: dict[str, list[dict]] = {}
    for fd in fixtures_data:
        by_league.setdefault(fd["league"], []).append(fd)

    tracker = ResultsTracker() if save else None
    if tracker:
        tracker.load()

    all_bets = []
    for league_key, league_fixtures in by_league.items():
        console.rule(f"[bold cyan]{LEAGUES[league_key].name}[/bold cyan]")
        matches = load_league(league_key)
        fb = FeatureBuilder()
        # Stage Sofascore BEFORE replay → consumed chronologically by fit_on_history
        for season in {m.season for m in matches}:
            sf_data = SofascoreClient.load_matches(league_key, season)
            if sf_data:
                fb.stage_sofascore_batch(sf_data)
        fb.fit_on_history(matches)

        # Persist current odds + reload full history into market tracker
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
                except Exception as exc:
                    console.log(
                        f"[yellow]Skip odds snapshot for "
                        f"{fd['home_team']} vs {fd['away_team']}: {exc}[/yellow]"
                    )
        load_odds_snapshots(league_key, fb.market_tracker, only_future=True)

        model_path = MODELS_DIR / f"catboost_{league_key}.cbm"
        if model_path.exists():
            cb = CatBoostPredictor.for_league(league_key, fb)
            poisson = PoissonModel(pi_ratings=fb.pi_ratings)
            mlp = MLPPredictor.for_league(league_key, fb)
            model = EnsembleModel(catboost=cb, poisson=poisson, mlp=mlp)
            console.log(f"[green]Using Ensemble{' (with MLP)' if mlp else ''}[/green]")
        else:
            model = PoissonModel(pi_ratings=fb.pi_ratings)
            console.log("[yellow]No CatBoost — using Poisson baseline[/yellow]")

        for fd in league_fixtures:
            odds = MatchOdds(**fd["odds"]) if "odds" in fd else None
            fixture = Fixture(
                date=fd["date"], league=league_key,
                home_team=fd["home_team"], away_team=fd["away_team"],
                odds=odds,
                season=fd.get("season"),
            )
            pred = model.predict(fixture)
            bets = find_value_bets(pred, bankroll)
            all_bets.extend(bets)

            console.print(
                f"\n⚽ [bold]{fixture.home_team}[/bold] vs [bold]{fixture.away_team}[/bold]"
            )
            console.print(
                f"   Model: H={pred.prob_home * 100:.1f}% / "
                f"D={pred.prob_draw * 100:.1f}% / A={pred.prob_away * 100:.1f}%"
            )
            if odds:
                console.print(
                    f"   Odds:  {odds.home:.2f} / {odds.draw:.2f} / {odds.away:.2f} "
                    f"(margin {odds.margin * 100:.1f}%)"
                )

            if save and tracker is not None:
                rec = PredictionRecord(
                    date=fixture.date.isoformat(), league=league_key,
                    home_team=fixture.home_team, away_team=fixture.away_team,
                    model_name=pred.model_name,
                    prob_home=pred.prob_home, prob_draw=pred.prob_draw, prob_away=pred.prob_away,
                    odds_home=odds.home if odds else None,
                    odds_draw=odds.draw if odds else None,
                    odds_away=odds.away if odds else None,
                )
                if bets:
                    best = max(bets, key=lambda b: b.edge)
                    rec.bet_outcome = best.outcome
                    rec.bet_odds = best.odds
                    rec.bet_stake = best.kelly_stake
                    rec.bet_edge = best.edge
                    rec.bet_status = "pending"
                tracker.add(rec)

    console.rule("[bold green]VALUE BETS[/bold green]")
    if all_bets:
        ranked = rank_value_bets(all_bets)
        table = Table()
        table.add_column("#", justify="right"); table.add_column("Match")
        table.add_column("Bet"); table.add_column("Odds", justify="right")
        table.add_column("Model", justify="right"); table.add_column("Edge", justify="right")
        table.add_column("Stake", justify="right"); table.add_column("Conf.")
        for i, b in enumerate(ranked, 1):
            table.add_row(
                str(i), f"{b.home_team} vs {b.away_team}",
                b.bet_label, f"{b.odds:.2f}",
                f"{b.model_prob * 100:.1f}%", f"{b.edge_pct:+.1f}%",
                f"{b.kelly_stake:.2f}", b.confidence,
            )
        console.print(table)
    else:
        console.print("[yellow]No value bets identified.[/yellow]")

    if save and tracker is not None:
        tracker.save()


# ───────────────────────── backtest ─────────────────────────

@main.command()
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True)
@click.option("--bankroll", default=1000.0)
@click.option("--no-ensemble", is_flag=True)
def backtest(league: str, bankroll: float, no_ensemble: bool) -> None:
    """Walk-forward backtest."""
    league = league.upper()
    bt = Backtester(initial_bankroll=bankroll, use_ensemble=not no_ensemble)
    result = bt.run(league)

    console.rule(f"[bold green]Backtest — {LEAGUES[league].name}[/bold green]")
    console.print(f"  Predictions: {result.n_predictions}")
    console.print(f"  Bets placed: {result.n_bets}")
    console.print(f"  Bankroll final: {result.bankroll_final:.2f}")
    console.print(f"  Max drawdown: {result.max_drawdown['max_drawdown_pct'] * 100:.1f}%")

    table = Table(title="Metrics")
    table.add_column("Metric"); table.add_column("Value", justify="right")
    for k, v in {**result.metrics, **result.bet_metrics}.items():
        table.add_row(k, f"{v:.4f}" if isinstance(v, float) else str(v))
    console.print(table)

    result.save()


# ───────────────────────── tune-ensemble ─────────────────────────

@main.command("tune-ensemble")
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True)
@click.option("--val-season", default="2024-25")
def tune_ensemble(league: str, val_season: str) -> None:
    """Dirichlet-sampled ensemble weight tuning."""
    league = league.upper()
    matches = load_league(league)
    val_matches = [m for m in matches if m.season == val_season]
    train_matches = [m for m in matches if m.season < val_season]

    fb = FeatureBuilder()
    for season in {m.season for m in train_matches}:
        sf = SofascoreClient.load_matches(league, season)
        if sf:
            fb.stage_sofascore_batch(sf)
    fb.fit_on_history(train_matches)

    model_path = MODELS_DIR / f"catboost_{league}.cbm"
    if not model_path.exists():
        console.print(f"[red]No CatBoost at {model_path}[/red]")
        raise click.Abort()

    cb = CatBoostPredictor.for_league(league, fb)
    poisson = PoissonModel(pi_ratings=fb.pi_ratings)
    mlp = MLPPredictor.for_league(league, fb)
    ensemble = EnsembleModel(catboost=cb, poisson=poisson, mlp=mlp)

    fixtures = []
    actuals = []
    for m in sorted(val_matches, key=lambda m: m.date):
        fixtures.append(Fixture(
            date=m.date, league=m.league,
            home_team=m.home_team, away_team=m.away_team, odds=m.odds,
        ))
        actuals.append(m.result)

    result = ensemble.tune_weights(fixtures, actuals)
    console.print("[bold]Best weights:[/bold]")
    console.print(f"  CatBoost: {result['best_w_catboost']:.3f}")
    console.print(f"  Poisson:  {result['best_w_poisson']:.3f}")
    if mlp is not None:
        console.print(f"  MLP:      {result['best_w_mlp']:.3f}")
    metric_key = next(k for k in result if k.startswith("best_") and k != "best_w_catboost"
                      and k != "best_w_poisson" and k != "best_w_mlp")
    console.print(f"  {metric_key}: {result[metric_key]:.4f}")


# ───────────────────────── monitor (v0.3) ─────────────────────────

@main.command()
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True)
@click.option("--recent-days", default=30, help="Production window in days")
def monitor(league: str, recent_days: int) -> None:
    """Feature drift detection (v0.3)."""
    league = league.upper()
    matches = load_league(league)

    # Split by date: most recent `recent_days` = production; rest = training
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=recent_days)
    train_matches = [m for m in matches if m.date < cutoff]
    prod_matches = [m for m in matches if m.date >= cutoff]

    if len(prod_matches) < 10:
        console.print(f"[yellow]Too few production matches ({len(prod_matches)}) "
                      f"in last {recent_days} days.[/yellow]")
        return

    console.log(f"Training window: {len(train_matches)} matches")
    console.log(f"Production window: {len(prod_matches)} matches")

    # Build features separately
    train_fb = FeatureBuilder()
    train_rows = []
    sorted_train = sorted(train_matches, key=lambda m: m.date)
    for m in sorted_train[-500:]:  # last 500 training matches
        train_fb.update_with_match(m)
    for m in sorted_train[-200:]:
        feats = train_fb.build_features(
            m.home_team, m.away_team, m.league, m.date,
            odds_home=m.odds.home if m.odds else None,
            odds_draw=m.odds.draw if m.odds else None,
            odds_away=m.odds.away if m.odds else None,
            kickoff_datetime_utc=m.kickoff_datetime_utc,
        )
        train_rows.append(feats)
    train_df = pd.DataFrame(train_rows)

    prod_rows = []
    for m in sorted(prod_matches, key=lambda m: m.date):
        feats = train_fb.build_features(
            m.home_team, m.away_team, m.league, m.date,
            odds_home=m.odds.home if m.odds else None,
            odds_draw=m.odds.draw if m.odds else None,
            odds_away=m.odds.away if m.odds else None,
            kickoff_datetime_utc=m.kickoff_datetime_utc,
        )
        prod_rows.append(feats)
        train_fb.update_with_match(m)  # update for next
    prod_df = pd.DataFrame(prod_rows)

    detector = DriftDetector()
    report = detector.analyze(train_df, prod_df, league)

    console.rule(f"[bold yellow]Drift Report — {LEAGUES[league].name}[/bold yellow]")
    console.print(f"  Production samples: {report.n_production_samples}")
    console.print(f"  Drifted features: {report.n_drifted_features}")

    if report.alerts:
        console.print("\n[red bold]Alerts:[/red bold]")
        for alert in report.alerts[:10]:
            console.print(f"  • {alert}")

    path = report.save()
    console.log(f"[green]Full report: {path}[/green]")


# ───────────────────────── update-results ─────────────────────────

@main.command("update-results")
@click.option("--results-file", "-r", required=True, type=click.Path(exists=True))
def update_results(results_file: str) -> None:
    """Update prediction log with actual results."""
    results = json.loads(Path(results_file).read_text())
    tracker = ResultsTracker()
    tracker.load()

    updated = 0
    for r in results:
        if tracker.update_result(
            home_team=r["home_team"], away_team=r["away_team"],
            match_date=r["date"],
            home_goals=r["home_goals"], away_goals=r["away_goals"],
        ):
            updated += 1
    tracker.save()
    console.log(f"[green]Updated {updated}/{len(results)} records.[/green]")


# ───────────────────────── stats ─────────────────────────

@main.command()
def stats() -> None:
    """Show betting performance."""
    tracker = ResultsTracker()
    tracker.load()
    if not tracker.records:
        console.print("[yellow]No predictions logged yet.[/yellow]")
        return

    roi_stats = tracker.roi_stats()
    console.print("\n[bold]Betting Performance[/bold]")
    for k, v in roi_stats.items():
        if isinstance(v, float):
            console.print(f"  {k}: {v:.4f}")
        else:
            console.print(f"  {k}: {v}")


# ───────────────────────── update-performance ─────────────────────────

@main.command("update-performance")
@click.option(
    "--tracking-start",
    default=None,
    help="ISO date when tracking began (default: spec value).",
)
def update_performance(tracking_start: str | None) -> None:
    """Regenerate performance.json + performance_full.json for the web tracker."""
    from football_betting.tracking.performance_index import (
        TRACKING_START_DEFAULT,
        write_performance_files,
    )

    start = tracking_start or TRACKING_START_DEFAULT
    public_path, private_path = write_performance_files(tracking_start=start)
    console.log(f"[green]Wrote {public_path}[/green]")
    console.log(f"[green]Wrote {private_path}[/green]")


# ───────────────────────── settle-live ─────────────────────────

@main.command("settle-live")
@click.option(
    "--days-from",
    type=click.IntRange(1, 3),
    default=3,
    help="How many days of scores to pull from the Odds API (max 3).",
)
def settle_live_cmd(days_from: int) -> None:
    """Poll The Odds API /scores and settle pending bets."""
    from football_betting.evaluation.live_results import pending_league_codes
    from football_betting.evaluation.pipeline import settle_live

    pending = pending_league_codes()
    if not pending:
        console.log("[yellow]No pending bets — nothing to settle.[/yellow]")
        return
    console.log(f"Pending leagues: {sorted(pending)}")
    added, settled = settle_live(days_from=days_from)
    console.log(f"[green]+{added} live result rows[/green]")
    console.log(f"[green]{settled} bet(s) newly settled[/green]")


# ───────────────────────── snapshot (web UI) ─────────────────────────

@main.command()
@click.option(
    "--fixtures",
    "-f",
    type=click.Path(exists=True),
    default=None,
    help="Path to a fixtures JSON file (defaults to latest data/fixtures_*.json).",
)
@click.option("--bankroll", "-b", default=1000.0)
def snapshot(fixtures: str | None, bankroll: float) -> None:
    """Generate today.json snapshot consumed by the web UI."""
    from football_betting.api.services import build_predictions_for_fixtures
    from football_betting.api.snapshots import write_today
    from football_betting.config import DATA_DIR

    if fixtures is None:
        candidates = sorted(DATA_DIR.glob("fixtures_*.json"))
        if not candidates:
            console.print("[red]No fixtures_*.json found in data/.[/red]")
            raise click.Abort()
        path = candidates[-1]
        console.log(f"Using latest fixtures: {path.name}")
    else:
        path = Path(fixtures)

    fixtures_data = json.loads(path.read_text(encoding="utf-8"))
    payload = build_predictions_for_fixtures(fixtures_data, bankroll=bankroll)
    out_path = write_today(payload)

    console.log(
        f"[green]Snapshot written: {out_path}[/green] "
        f"({len(payload.predictions)} predictions, {len(payload.value_bets)} value bets)"
    )

    # Best-effort IndexNow ping so Bing/Yandex/Yep see fresh content quickly.
    try:
        from football_betting.seo.indexnow import build_snapshot_urls, ping_indexnow

        leagues = sorted({p.league for p in payload.predictions if getattr(p, "league", None)})
        urls = build_snapshot_urls(leagues=leagues)
        if urls and ping_indexnow(urls):
            console.log(f"[green]IndexNow notified ({len(urls)} URLs)[/green]")
    except Exception as exc:  # pragma: no cover - never block snapshotting
        console.log(f"[yellow]IndexNow skipped: {exc}[/yellow]")


# ───────────────────── resolve-sofascore-ids ─────────────────────


@main.command("resolve-sofascore-ids")
@click.option(
    "--snapshot", "snapshot_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to today.json (defaults to data/snapshots/today.json).",
)
@click.option(
    "--force", is_flag=True,
    help="Re-resolve slugs that already have an override entry.",
)
def resolve_sofascore_ids(snapshot_path: str | None, force: bool) -> None:
    """Resolve missing sofascore_event_id for today's snapshot and persist.

    Operators run this locally (or in a trusted CI runner) where Sofascore
    is reachable. Results are written to the bundled overrides file so
    production hosts that cannot reach Sofascore serve event IDs directly.
    """
    import os

    from football_betting.api.snapshots import SNAPSHOT_PATH
    from football_betting.scraping.sofascore import SofascoreClient
    from football_betting.scraping.sofascore_overrides import (
        OVERRIDES_PATH,
        load_all,
        set_override,
    )
    from football_betting.seo.match_slugs import build_slug

    os.environ.setdefault("SCRAPING_ENABLED", "1")

    path = Path(snapshot_path) if snapshot_path else SNAPSHOT_PATH
    if not path.exists():
        console.print(f"[red]Snapshot not found: {path}[/red]")
        raise click.Abort()

    data = json.loads(path.read_text(encoding="utf-8"))
    preds = data.get("predictions", [])
    if not preds:
        console.log("[yellow]Snapshot contains no predictions.[/yellow]")
        return

    existing = load_all()
    client = SofascoreClient()
    resolved = 0
    skipped = 0
    missed = 0

    for pred in preds:
        slug = build_slug(pred["home_team"], pred["away_team"], pred["date"])
        if not force and slug in existing:
            skipped += 1
            continue
        try:
            ev_id = client.find_event_id(
                pred["league"].upper(),
                pred["home_team"],
                pred["away_team"],
                pred["date"],
            )
        except Exception as exc:
            console.log(f"[red]{slug}: lookup error ({exc})[/red]")
            missed += 1
            continue
        if ev_id is None:
            console.log(f"[yellow]{slug}: no Sofascore match found[/yellow]")
            missed += 1
            continue
        set_override(slug, ev_id)
        console.log(f"[green]{slug} -> {ev_id}[/green]")
        resolved += 1

    console.log(
        f"[cyan]Overrides written to {OVERRIDES_PATH}[/cyan] "
        f"(new={resolved}, skipped={skipped}, missed={missed})"
    )


# ───────────────────────── weather-stadiums (v0.4) ─────────────────────────


@main.command("weather-stadiums")
@click.option(
    "--league", "-l",
    type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False),
    default="all",
    help="Resolve stadiums for one league or all.",
)
@click.option(
    "--seasons", "-s", multiple=True,
    default=("2021-22", "2022-23", "2023-24", "2024-25", "2025-26"),
    help="Seasons to scan for the team universe.",
)
@click.option(
    "--out", "-o",
    type=click.Path(),
    default=str(DATA_DIR / "stadiums.json"),
    help="Output JSON path.",
)
@click.option("--force", is_flag=True, help="Overwrite existing entries.")
def weather_stadiums(league: str, seasons: tuple[str, ...], out: str, force: bool) -> None:
    """Geocode stadium coordinates for all teams via Open-Meteo (v0.4).

    Iterates teams encountered in football-data.co.uk CSVs, resolves
    each via the Open-Meteo geocoding API, and writes a JSON lookup
    consumed by `WeatherTracker`.
    """
    from football_betting.scraping.weather import OpenMeteoClient

    out_path = Path(out)
    existing: dict[str, dict] = {}
    if out_path.exists() and not force:
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

    keys = list(LEAGUES.keys()) if league.lower() == "all" else [league.upper()]
    teams: dict[str, str] = {}  # canonical team name → league key (for context)
    for k in keys:
        try:
            matches = load_league(k, seasons=list(seasons))
        except FileNotFoundError as e:
            console.log(f"[yellow]Skip {k}: {e}[/yellow]")
            continue
        for m in matches:
            teams.setdefault(m.home_team, k)
            teams.setdefault(m.away_team, k)

    console.log(f"[cyan]Resolving {len(teams)} unique teams[/cyan]")
    client = OpenMeteoClient()
    resolved = dict(existing)
    failed: list[str] = []

    with Progress(console=console) as progress:
        task = progress.add_task("Geocoding", total=len(teams))
        for team, league_key in teams.items():
            if team in resolved and resolved[team] is not None and not force:
                progress.advance(task)
                continue
            # Try team name first (often resolves to home city); fall back to a
            # bare city/country query if needed.
            result = client.geocode(team)
            if result is None:
                result = client.geocode(f"{team} football")
            if result is None:
                failed.append(team)
                resolved[team] = None
            else:
                resolved[team] = {
                    "lat": result.lat,
                    "lon": result.lon,
                    "city": result.name,
                    "country": result.country,
                    "league": league_key,
                }
                console.log(f"  {team} → {result.name}, {result.country} ({result.lat:.3f}, {result.lon:.3f})")
            progress.advance(task)

    out_path.write_text(json.dumps(resolved, indent=2, ensure_ascii=False), encoding="utf-8")
    console.log(f"[green]Wrote {out_path}[/green]")
    console.log(f"  resolved: {sum(1 for v in resolved.values() if v)}")
    console.log(f"  unresolved: {len(failed)}")
    if failed:
        console.log(f"[yellow]Unresolved: {', '.join(failed[:10])}{'...' if len(failed) > 10 else ''}[/yellow]")


# ───────────────────────── serve (web UI) ─────────────────────────

@main.command("sofascore-find")
@click.argument("league")
@click.argument("home")
@click.argument("away")
@click.argument("day")
def sofascore_find(league: str, home: str, away: str, day: str) -> None:
    """Diagnose Sofascore event-id lookup for one fixture.

    Example: fb sofascore-find SA Lecce Fiorentina 2026-04-20
    """
    from datetime import date as _date

    from football_betting.scraping.sofascore import (
        SofascoreClient,
        _name_matches,
        _normalise_team_name,
    )

    target = _date.fromisoformat(day)
    client = SofascoreClient()
    cfg = LEAGUES.get(league.upper())
    if cfg is None or cfg.sofascore_tournament_id is None:
        raise click.ClickException(
            f"League {league} has no sofascore_tournament_id configured."
        )
    tid = cfg.sofascore_tournament_id
    h_norm = _normalise_team_name(home)
    a_norm = _normalise_team_name(away)
    console.log(
        f"[cyan]Looking up tournament_id={tid} | "
        f"home='{home}'->'{h_norm}' | away='{away}'->'{a_norm}'[/cyan]"
    )
    table = Table(show_header=True, header_style="bold magenta")
    for col in ("date", "event_id", "home", "away", "h_norm", "a_norm", "match"):
        table.add_column(col)
    for delta in (0, -1, 1):
        target_d = target.fromordinal(target.toordinal() + delta)
        events = client.get_scheduled_events_for_date(target_d)
        for ev in events:
            t_obj = ev.get("tournament", {}) or {}
            ut_obj = t_obj.get("uniqueTournament", {}) or {}
            ev_tid = int(ut_obj.get("id") or t_obj.get("id") or 0)
            if ev_tid != tid:
                continue
            ev_home = str((ev.get("homeTeam") or {}).get("name", ""))
            ev_away = str((ev.get("awayTeam") or {}).get("name", ""))
            hn = _normalise_team_name(ev_home)
            an = _normalise_team_name(ev_away)
            ok = "yes" if (
                _name_matches(hn, h_norm) and _name_matches(an, a_norm)
            ) else ""
            table.add_row(
                target_d.isoformat(), str(ev.get("id", "")),
                ev_home, ev_away, hn, an, ok,
            )
    console.print(table)
    resolved = client.find_event_id(league.upper(), home, away, target)
    console.log(f"[green]Resolved event_id: {resolved}[/green]")


@main.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000, type=int)
@click.option("--reload/--no-reload", default=False)
def serve(host: str, port: int, reload: bool) -> None:
    """Run the FastAPI server backing the web interface."""
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - guidance only
        raise click.ClickException(
            "uvicorn is not installed. Run: pip install -e \".[api]\""
        ) from exc

    console.log(f"[cyan]Serving Betting with AI on http://{host}:{port}[/cyan]")
    uvicorn.run(
        "football_betting.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
