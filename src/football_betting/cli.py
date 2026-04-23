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
    fb snapshot-odds     — Capture pre-match opening lines (Phase 4 CLV)
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
from datetime import UTC
from pathlib import Path

import click
import pandas as pd
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from football_betting.betting.value import find_value_bets, rank_value_bets
from football_betting.config import BETTING_CFG, DATA_DIR, LEAGUES, MODELS_DIR, BettingConfig
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
from football_betting.features.weather import WeatherTracker


def _make_feature_builder(purpose: str = "1x2") -> FeatureBuilder:
    """Construct FeatureBuilder with WeatherTracker wired in (v0.4 Phase 1).

    When ``purpose="value"`` the value-bet feature blocklist (``market_*``
    and ``mm_*``) is applied so the value specialist cannot learn the
    market consensus directly.
    """
    from football_betting.config import VALUE_MODEL_CFG

    if purpose == "value":
        return FeatureBuilder(
            weather_tracker=WeatherTracker(),
            feature_blocklist_prefixes=VALUE_MODEL_CFG.feature_blocklist_prefixes,
            feature_blocklist_exact=VALUE_MODEL_CFG.feature_blocklist_exact,
        )
    return FeatureBuilder(weather_tracker=WeatherTracker())


from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.ensemble import EnsembleModel
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.predict.tabular_transformer import TabTransformerPredictor
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
@click.option(
    "--league",
    "-l",
    type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False),
    default="all",
)
@click.option(
    "--seasons",
    "-s",
    multiple=True,
    default=("2021-22", "2022-23", "2023-24", "2024-25", "2025-26"),
)
@click.option("--force", is_flag=True)
def download(league: str, seasons: tuple[str, ...], force: bool) -> None:
    """Download football-data.co.uk historical CSVs."""
    keys = list(LEAGUES.keys()) if league.lower() == "all" else [league.upper()]
    download_all(league_keys=keys, seasons=list(seasons), force=force)


# ───────────────────────── rate ─────────────────────────


@main.command()
@click.option(
    "--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True
)
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
@click.option(
    "--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True
)
@click.option("--seasons", "-s", multiple=True, default=("2024-25", "2025-26"))
@click.option("--with-stats/--no-stats", default=True, help="Also fetch xG + lineups per match")
@click.option("--max-matches", default=None, type=int, help="Limit for testing")
def scrape(
    league: str, seasons: tuple[str, ...], with_stats: bool, max_matches: int | None
) -> None:
    """Scrape Sofascore data for xG + lineups (v0.3)."""
    league = league.upper()
    client = SofascoreClient()

    if not client.cfg.enabled:
        console.print(
            "[red]Sofascore scraping disabled.[/red]\nEnable with: export SCRAPING_ENABLED=1"
        )
        raise click.Abort()

    console.log(
        f"[yellow]Note: Waiting {client.cfg.request_delay_seconds}s between requests[/yellow]"
    )

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
        f"[dim]Cache: {stats['entries']} entries, {stats['total_bytes'] / 1024 / 1024:.1f} MB[/dim]"
    )


# ───────────────────────── fetch-fixtures (Odds API) ─────────────────────────


@main.command("fetch-fixtures")
@click.option(
    "--date",
    "target_date",
    default=None,
    help="ISO date (YYYY-MM-DD) — defaults to today in the server timezone.",
)
@click.option(
    "--league",
    "-l",
    type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False),
    default="all",
)
@click.option(
    "--out",
    "-o",
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
    table.add_column("League")
    table.add_column("Kickoff")
    table.add_column("Match")
    table.add_column("Odds (H/D/A)", justify="right")
    table.add_column("Books", justify="right")
    for f in sorted(fixtures, key=lambda x: (x.league, x.kickoff_local)):
        table.add_row(
            f.league,
            f.kickoff_local,
            f"{f.home_team} vs {f.away_team}",
            f"{f.odds_home:.2f} / {f.odds_draw:.2f} / {f.odds_away:.2f}",
            str(f.n_bookmakers),
        )
    console.print(table)
    console.log(f"[green]Wrote {len(fixtures)} fixtures -> {out_path}[/green]")


# ───────────────────────── snapshot-odds (Phase 4 opening lines) ──────────


@main.command("snapshot-odds")
@click.option(
    "--league",
    "-l",
    type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False),
    default="all",
)
@click.option(
    "--t-minus",
    "t_minus_hours",
    type=int,
    default=48,
    help="Only capture fixtures whose kickoff is within T-<hours> from now.",
)
@click.option(
    "--source",
    type=click.Choice(["odds_api", "sofascore"], case_sensitive=False),
    default="odds_api",
    help="Pre-match odds source (sofascore requires SCRAPING_ENABLED=1).",
)
def snapshot_odds(league: str, t_minus_hours: int, source: str) -> None:
    """Capture pre-match opening-line snapshots for upcoming fixtures (Phase 4)."""
    from datetime import date as date_cls

    from football_betting.data.snapshot_service import capture_odds_snapshot
    from football_betting.scraping.odds_api import OddsApiClient, OddsApiError

    source = source.lower()
    keys = list(LEAGUES.keys()) if league.lower() == "all" else [league.upper()]

    if source == "sofascore":
        client = SofascoreClient()
        if not client.cfg.enabled:
            console.print(
                "[red]Sofascore scraping disabled.[/red]\nEnable with: export SCRAPING_ENABLED=1"
            )
            raise click.Abort()
        console.print(
            "[yellow]Sofascore opening-snapshot capture is not yet wired. "
            "Falling back to odds_api.[/yellow]"
        )
        source = "odds_api"

    odds_client = OddsApiClient()
    today = date_cls.today()
    total = 0
    for key in keys:
        try:
            fx_list = odds_client.fetch_for_date(key, today)
        except OddsApiError as exc:
            console.print(f"[red]Odds API error for {key}: {exc}[/red]")
            continue
        fixtures: list[Fixture] = []
        for fo in fx_list:
            payload = fo.to_fixture_dict()
            try:
                fixtures.append(
                    Fixture(
                        **{
                            "date": payload["date"],
                            "league": payload["league"],
                            "home_team": payload["home_team"],
                            "away_team": payload["away_team"],
                            "kickoff_time": payload.get("kickoff_time"),
                            "odds": MatchOdds(
                                home=payload["odds"]["home"],
                                draw=payload["odds"]["draw"],
                                away=payload["odds"]["away"],
                                bookmaker="odds_api_opening",
                            ),
                            "kickoff_datetime_utc": fo.kickoff_utc,
                        }
                    )
                )
            except Exception as exc:  # pragma: no cover
                console.log(
                    f"[yellow]Skip fixture {fo.home_team} vs {fo.away_team}: {exc}[/yellow]"
                )
        captured = capture_odds_snapshot(key, fixtures, t_minus_hours=t_minus_hours, source=source)
        total += len(captured)
        console.log(
            f"[green]{key}: captured {len(captured)} opening snapshots "
            f"(T-{t_minus_hours}h window)[/green]"
        )
    console.log(f"[green]Total opening snapshots persisted: {total}[/green]")


# ───────────────────────── train ─────────────────────────


@main.command()
@click.option(
    "--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True
)
@click.option(
    "--seasons", "-s", multiple=True, default=("2021-22", "2022-23", "2023-24", "2024-25")
)
@click.option("--warmup", default=100)
@click.option("--calibrate/--no-calibrate", default=True)
@click.option(
    "--use-sofascore/--no-sofascore",
    default=True,
    help="Ingest pre-scraped Sofascore data if present",
)
@click.option(
    "--purpose",
    type=click.Choice(["1x2", "value"], case_sensitive=False),
    default="1x2",
    show_default=True,
    help="Dual-model split: 1X2 (default) or value-bet specialist.",
)
def train(
    league: str,
    seasons: tuple[str, ...],
    warmup: int,
    calibrate: bool,
    use_sofascore: bool,
    purpose: str,
) -> None:
    """Train CatBoost + calibrator."""
    from football_betting.config import artifact_suffix

    league = league.upper()
    purpose = purpose.lower()
    matches = load_league(league, seasons=list(seasons))

    fb = _make_feature_builder(purpose=purpose)

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

    predictor = CatBoostPredictor(feature_builder=fb, purpose=purpose)  # type: ignore[arg-type]
    console.log(
        f"[cyan]Training CatBoost for {LEAGUES[league].name} (purpose={purpose})…[/cyan]"
    )
    result = predictor.fit(matches, warmup_games=warmup, calibrate=calibrate)

    suffix = artifact_suffix(purpose)  # type: ignore[arg-type]
    model_path = MODELS_DIR / f"catboost_{league}{suffix}.cbm"
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
@click.option(
    "--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True
)
@click.option(
    "--seasons", "-s", multiple=True, default=("2021-22", "2022-23", "2023-24", "2024-25")
)
@click.option("--warmup", default=100)
@click.option(
    "--purpose",
    type=click.Choice(["1x2", "value"], case_sensitive=False),
    default="1x2",
    show_default=True,
    help="Dual-model split: 1X2 (default) or value-bet specialist.",
)
def train_mlp(league: str, seasons: tuple[str, ...], warmup: int, purpose: str) -> None:
    """Train PyTorch MLP classifier (v0.3)."""
    from dataclasses import replace

    from football_betting.config import MLP_CFG, VALUE_MODEL_CFG, artifact_suffix

    league = league.upper()
    purpose = purpose.lower()
    matches = load_league(league, seasons=list(seasons))

    fb = _make_feature_builder(purpose=purpose)
    for season in seasons:
        sf_data = SofascoreClient.load_matches(league, season)
        if sf_data:
            fb.stage_sofascore_batch(sf_data)

    cfg = MLP_CFG
    if purpose == "value":
        cfg = replace(
            MLP_CFG,
            use_kelly_loss=VALUE_MODEL_CFG.use_kelly_loss,
            kelly_lambda=VALUE_MODEL_CFG.kelly_lambda,
            kelly_f_cap=VALUE_MODEL_CFG.kelly_f_cap,
        )

    mlp = MLPPredictor(feature_builder=fb, cfg=cfg, purpose=purpose)  # type: ignore[arg-type]
    console.log(f"[cyan]Training MLP for {LEAGUES[league].name} (purpose={purpose})…[/cyan]")
    result = mlp.fit(matches, warmup_games=warmup)

    suffix = artifact_suffix(purpose)  # type: ignore[arg-type]
    path = MODELS_DIR / f"mlp_{league}{suffix}.pt"
    mlp.save(path)
    console.log(f"[green]MLP saved: {path}[/green]")
    console.print(f"  n_train={result['n_train']}, n_val={result['n_val']}")
    console.print(f"  best_val_loss={result['best_val_loss']:.4f}")


# ───────────────────────── train-tab (v0.4) ─────────────────────────


@main.command("train-tab")
@click.option(
    "--league",
    "-l",
    type=click.Choice(list(LEAGUES.keys()), case_sensitive=False),
    required=True,
)
@click.option(
    "--seasons",
    "-s",
    multiple=True,
    default=("2021-22", "2022-23", "2023-24", "2024-25"),
)
@click.option("--warmup", default=100, show_default=True)
@click.option(
    "--device",
    type=click.Choice(["auto", "cuda", "dml", "cpu"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Torch backend: auto → CUDA → DirectML (AMD/Intel) → CPU.",
)
@click.option(
    "--purpose",
    type=click.Choice(["1x2", "value"], case_sensitive=False),
    default="1x2",
    show_default=True,
    help="Dual-model split: 1X2 (default) or value-bet specialist.",
)
def train_tab(
    league: str, seasons: tuple[str, ...], warmup: int, device: str, purpose: str
) -> None:
    """Train FT-Transformer tabular classifier (v0.4, GPU-friendly)."""
    import os as _os

    from football_betting.config import artifact_suffix

    league = league.upper()
    purpose = purpose.lower()
    _os.environ["FB_TORCH_DEVICE"] = device.lower()

    matches = load_league(league, seasons=list(seasons))

    fb = _make_feature_builder(purpose=purpose)
    for season in seasons:
        sf_data = SofascoreClient.load_matches(league, season)
        if sf_data:
            fb.stage_sofascore_batch(sf_data)

    tab = TabTransformerPredictor(feature_builder=fb, purpose=purpose)  # type: ignore[arg-type]
    console.log(
        f"[cyan]Training FT-Transformer for {LEAGUES[league].name} "
        f"(purpose={purpose})…[/cyan]"
    )
    result = tab.fit(matches, warmup_games=warmup)

    suffix = artifact_suffix(purpose)  # type: ignore[arg-type]
    path = MODELS_DIR / f"tabtransformer_{league}{suffix}.pt"
    tab.save(path)
    console.log(f"[green]TabTransformer saved: {path}[/green]")
    console.print(f"  n_train={result['n_train']}, n_val={result['n_val']}")
    console.print(f"  n_features={result['n_features']}, backend={result['backend']}")
    console.print(f"  best_val_loss={result['best_val_loss']:.4f}")


# ───────────────────────── train-sequence (v0.4) ─────────────────────────


@main.command("train-sequence")
@click.option(
    "--league",
    "-l",
    type=click.Choice(list(LEAGUES.keys()), case_sensitive=False),
    required=True,
)
@click.option(
    "--seasons",
    "-s",
    multiple=True,
    default=("2021-22", "2022-23", "2023-24", "2024-25"),
)
@click.option("--warmup", default=100, show_default=True)
@click.option(
    "--device",
    type=click.Choice(["auto", "cuda", "dml", "cpu"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Torch backend: auto → CUDA → DirectML → CPU.",
)
@click.option(
    "--purpose",
    type=click.Choice(["1x2", "value"], case_sensitive=False),
    default="1x2",
    show_default=True,
    help="Dual-model split: 1X2 (default) or value-bet specialist.",
)
def train_sequence(
    league: str,
    seasons: tuple[str, ...],
    warmup: int,
    device: str,
    purpose: str,
) -> None:
    """Train 1D-CNN + Transformer sequence head (v0.4)."""
    import os as _os

    from football_betting.config import artifact_suffix
    from football_betting.predict.sequence_model import SequencePredictor

    league = league.upper()
    purpose = purpose.lower()
    _os.environ["FB_TORCH_DEVICE"] = device.lower()

    matches = load_league(league, seasons=list(seasons))

    seq = SequencePredictor(purpose=purpose)  # type: ignore[arg-type]
    console.log(
        f"[cyan]Training Sequence head for {LEAGUES[league].name} "
        f"(purpose={purpose})…[/cyan]"
    )
    result = seq.fit(matches, warmup_games=warmup)

    suffix = artifact_suffix(purpose)  # type: ignore[arg-type]
    path = MODELS_DIR / f"sequence_{league}{suffix}.pt"
    seq.save(path)
    console.log(f"[green]Sequence model saved: {path}[/green]")
    console.print(f"  n_train={result.get('n_train', '?')}, n_val={result.get('n_val', '?')}")
    if "best_val_loss" in result:
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
            raise click.BadParameter(f"lang must be one of {('all', *SUPPORT_CFG.languages)}")
        langs = [lg]

    train_all(langs=langs, dataset_path=dataset_path, out_dir=out_dir)


# ─────────────────── train-support-hier (v0.3.2 — Pachinko) ───────────────────


@main.command("train-support-hier")
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
@click.option(
    "--no-ood",
    is_flag=True,
    default=False,
    help="Skip the curated OOD seed bank (train without __ood__ class).",
)
def train_support_hier(
    lang: str,
    dataset_path: Path | None,
    out_dir: Path | None,
    no_ood: bool,
) -> None:
    """Train hierarchical (chapter -> intent) FAQ classifier with OOD head."""
    from football_betting.config import SUPPORT_CFG
    from football_betting.support.trainer import train_hierarchical_all

    if lang.lower() == "all":
        langs: list[str] | None = None
    else:
        lg = lang.lower()
        if lg not in SUPPORT_CFG.languages:
            raise click.BadParameter(f"lang must be one of {('all', *SUPPORT_CFG.languages)}")
        langs = [lg]

    train_hierarchical_all(
        langs=langs,
        dataset_path=dataset_path,
        out_dir=out_dir,
        include_ood=not no_ood,
    )


# ─────────────────── augment-support (v0.3.3 - Data x3.3) ───────────────────


@main.command("augment-support")
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Input JSONL (default: data/support_faq/dataset_augmented.jsonl).",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output JSONL (default: data/support_faq/dataset_augmented_v2.jsonl).",
)
@click.option(
    "--target",
    "target_per_intent",
    type=int,
    default=None,
    help="Target utterances per (intent, lang). Default: SUPPORT_CFG.augment_target_per_intent.",
)
@click.option(
    "--seed",
    "rng_seed",
    type=int,
    default=None,
    help="Override the augmentation RNG seed (reproducibility knob).",
)
@click.option(
    "--noise/--no-noise",
    default=True,
    help="Enable built-in QWERTY/QWERTZ noise augmenter (default: on).",
)
@click.option(
    "--paraphrase/--no-paraphrase",
    default=False,
    help="Enable LLM paraphrase augmenter (needs [support-aug] + OPENAI_API_KEY).",
)
@click.option(
    "--paraphrase-model",
    default="gpt-4o-mini",
    show_default=True,
    help="OpenAI chat model for --paraphrase.",
)
@click.option(
    "--backtranslate/--no-backtranslate",
    default=False,
    help="Enable MarianMT backtranslation augmenter (needs [support-aug]).",
)
@click.option(
    "--bt-device",
    default="cpu",
    show_default=True,
    help="Device for MarianMT pipelines ('cpu' / 'cuda').",
)
def augment_support(
    input_path: Path | None,
    output_path: Path | None,
    target_per_intent: int | None,
    rng_seed: int | None,
    noise: bool,
    paraphrase: bool,
    paraphrase_model: str,
    backtranslate: bool,
    bt_device: str,
) -> None:
    """Fill support-FAQ buckets to >= 80 utterances/intent via layered augmenters.

    Layer order when multiple are enabled:
    1. LLM paraphrase (highest lexical diversity),
    2. MarianMT backtranslation (structural diversity),
    3. Built-in noise (typo / punctuation / casing — always last).
    """
    from football_betting.support.augment import (
        BacktranslationAugmenter,
        NoiseAugmenter,
        ParaphraseAugmenter,
        augment_dataset,
        build_marian_backtranslator,
        build_openai_paraphraser,
    )

    augmenters: list[object] = []
    if paraphrase:
        try:
            generate_fn = build_openai_paraphraser(model=paraphrase_model)
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc
        augmenters.append(ParaphraseAugmenter(generate_fn=generate_fn))
    if backtranslate:
        try:
            translate_fn = build_marian_backtranslator(device=bt_device)
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc
        augmenters.append(BacktranslationAugmenter(translate_fn=translate_fn))
    if noise:
        augmenters.append(NoiseAugmenter())

    stats = augment_dataset(
        input_path=input_path,
        output_path=output_path,
        target_per_intent=target_per_intent,
        augmenters=augmenters or None,
        rng_seed=rng_seed,
    )
    click.echo(
        f"Augmented: {stats.n_input_rows} -> {stats.n_output_rows} rows "
        f"(avg/intent-lang={stats.variants_per_intent_lang.get('avg', 0):.1f})"
    )


# ─────────────────── train-support-transformer (v0.3.4 - M3) ───────────────────


@main.command("train-support-transformer")
@click.option(
    "--lang",
    type=str,
    default="all",
    show_default=True,
    help="Locale to fine-tune (one of en/de/es/fr/it) or 'all'.",
)
@click.option(
    "--dataset",
    "dataset_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Dataset JSONL (default: dataset_augmented_v2.jsonl with fallback to dataset_augmented.jsonl).",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: models/support).",
)
@click.option(
    "--backbone",
    type=str,
    default=None,
    help="Override HF backbone (default: XLM-R base for all languages — "
    "ModernGBERT's backward pass is not DirectML-compatible on W7700).",
)
@click.option(
    "--include-ood/--no-ood",
    default=True,
    show_default=True,
    help="Inject curated OOD seed rows during training.",
)
@click.option(
    "--seed",
    type=int,
    default=42,
    show_default=True,
    help="Seed for Python/NumPy/torch RNGs (cuDNN-deterministic only on CUDA).",
)
@click.option(
    "--calibrate/--no-calibrate",
    default=True,
    show_default=True,
    help="Fit a 1-parameter Temperature calibrator on the validation split.",
)
@click.option(
    "--epochs",
    type=int,
    default=None,
    help="Override transformer_epochs (e.g. 1 for a smoke run).",
)
@click.option(
    "--max-rows-per-intent",
    type=int,
    default=None,
    help="Cap training rows per intent (smoke/HPO). Class balance preserved.",
)
def train_support_transformer(
    lang: str,
    dataset_path: Path | None,
    out_dir: Path | None,
    backbone: str | None,
    include_ood: bool,
    seed: int,
    calibrate: bool,
    epochs: int | None,
    max_rows_per_intent: int | None,
) -> None:
    """Fine-tune an encoder (XLM-R / ModernGBERT) with CE + SupCon loss."""
    from football_betting.support.trainer import (
        train_transformer_all,
        train_transformer_one_language,
    )

    if lang == "all":
        train_transformer_all(
            dataset_path=dataset_path,
            out_dir=out_dir,
            include_ood=include_ood,
            seed=seed,
            calibrate=calibrate,
            epochs=epochs,
            max_rows_per_intent=max_rows_per_intent,
        )
    else:
        train_transformer_one_language(
            lang,
            dataset_path=dataset_path,
            out_dir=out_dir,
            backbone=backbone,
            include_ood=include_ood,
            seed=seed,
            calibrate=calibrate,
            epochs=epochs,
            max_rows_per_intent=max_rows_per_intent,
        )


# ─────────────────── export-support-onnx (v0.3.4 - M3) ───────────────────


@main.command("export-support-onnx")
@click.option(
    "--lang",
    type=str,
    default="all",
    show_default=True,
    help="Locale to export or 'all'.",
)
@click.option(
    "--model-dir",
    "model_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Models root (default: models/support).",
)
@click.option(
    "--int8/--no-int8",
    default=True,
    show_default=True,
    help="Post-export dynamic INT8 quantisation (needs onnxruntime.quantization).",
)
def export_support_onnx(lang: str, model_dir: Path | None, int8: bool) -> None:
    """Export fine-tuned support transformer(s) to ONNX (optionally INT8)."""
    from football_betting.config import SUPPORT_CFG, SUPPORT_MODELS_DIR
    from football_betting.support.transformer_model import (
        TransformerIntentClassifier,
        export_to_onnx,
    )

    root = model_dir or SUPPORT_MODELS_DIR
    langs = list(SUPPORT_CFG.languages) if lang == "all" else [lang]
    for lg in langs:
        src_dir = root / SUPPORT_CFG.transformer_model_dirname_template.format(lang=lg)
        if not src_dir.exists():
            click.echo(f"[skip] no model dir for {lg}: {src_dir}")
            continue
        out_file = root / SUPPORT_CFG.onnx_filename_template.format(lang=lg)
        clf = TransformerIntentClassifier.load(src_dir)
        final = export_to_onnx(clf, out_file, int8=int8)
        click.echo(f"[{lg}] exported: {final}")


# ───────────────────────── export-onnx (v0.3) ─────────────────────────


@main.command("export-onnx")
@click.option(
    "--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True
)
def export_onnx(league: str) -> None:
    """Export trained MLP to ONNX format."""
    league = league.upper()
    model_path = MODELS_DIR / f"mlp_{league}.pt"
    if not model_path.exists():
        console.print(f"[red]No MLP at {model_path}[/red]")
        raise click.Abort()

    fb = _make_feature_builder()
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
        fb = _make_feature_builder()
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
                date=fd["date"],
                league=league_key,
                home_team=fd["home_team"],
                away_team=fd["away_team"],
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
                    date=fixture.date.isoformat(),
                    league=league_key,
                    home_team=fixture.home_team,
                    away_team=fixture.away_team,
                    model_name=pred.model_name,
                    prob_home=pred.prob_home,
                    prob_draw=pred.prob_draw,
                    prob_away=pred.prob_away,
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
        table.add_column("#", justify="right")
        table.add_column("Match")
        table.add_column("Bet")
        table.add_column("Odds", justify="right")
        table.add_column("Model", justify="right")
        table.add_column("Edge", justify="right")
        table.add_column("Stake", justify="right")
        table.add_column("Conf.")
        for i, b in enumerate(ranked, 1):
            table.add_row(
                str(i),
                f"{b.home_team} vs {b.away_team}",
                b.bet_label,
                f"{b.odds:.2f}",
                f"{b.model_prob * 100:.1f}%",
                f"{b.edge_pct:+.1f}%",
                f"{b.kelly_stake:.2f}",
                b.confidence,
            )
        console.print(table)
    else:
        console.print("[yellow]No value bets identified.[/yellow]")

    if save and tracker is not None:
        tracker.save()


# ───────────────────────── backtest ─────────────────────────


@main.command()
@click.option(
    "--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True
)
@click.option("--bankroll", default=1000.0)
@click.option("--no-ensemble", is_flag=True)
@click.option(
    "--walk-forward",
    "walk_forward",
    is_flag=True,
    help="Run the Phase 6 multi-fold walk-forward schedule",
)
@click.option(
    "--stacking",
    is_flag=True,
    help="Phase 7: level-2 stacking meta-learner (CatBoost+Poisson L1 OOF → LR meta)",
)
@click.option(
    "--folds-auto",
    "folds_auto",
    is_flag=True,
    help="Filter the Phase 6 walk-forward schedule to folds whose train+test seasons have CSVs on disk.",
)
@click.option(
    "--sliding/--expanding",
    "sliding",
    default=False,
    help="Walk-forward window mode. Sliding keeps only the trailing --window-matches from each fold's train set.",
)
@click.option(
    "--window-matches",
    type=click.IntRange(100, 10_000),
    default=500,
    show_default=True,
    help="Trailing window size for --sliding walk-forward.",
)
@click.option(
    "--calibration-method",
    type=click.Choice(["auto", "isotonic", "sigmoid"], case_sensitive=False),
    default=None,
    help="Override the CatBoost calibration method (default: auto).",
)
def backtest(
    league: str,
    bankroll: float,
    no_ensemble: bool,
    walk_forward: bool,
    stacking: bool,
    folds_auto: bool,
    sliding: bool,
    window_matches: int,
    calibration_method: str | None,
) -> None:
    """Walk-forward backtest (single season or Phase 6 multi-fold)."""
    league = league.upper()

    if walk_forward:
        from football_betting.tracking.backtest import (
            DEFAULT_WALK_FORWARD_FOLDS,
            walk_forward_backtest,
        )

        folds = None
        if folds_auto:
            league_code = LEAGUES[league].code
            available_seasons = {
                p.stem.split("_", 1)[1] for p in (DATA_DIR / "raw").glob(f"{league_code}_*.csv")
            }

            # football-data suffix is YYYY without dash, e.g. 2122 for 2021-22.
            def _fd(season: str) -> str:
                return season[2:4] + season[-2:]

            folds = tuple(
                (train, test)
                for train, test in DEFAULT_WALK_FORWARD_FOLDS
                if _fd(test) in available_seasons
                and all(_fd(s) in available_seasons for s in train)
            )
            if not folds:
                console.print(
                    f"[red]No walk-forward folds have complete CSV coverage for {league}.[/red]"
                )
                raise click.Abort()
            console.print(
                f"[green]--folds-auto: {len(folds)}/{len(DEFAULT_WALK_FORWARD_FOLDS)} folds retained.[/green]"
            )

        summary = walk_forward_backtest(
            league,
            folds=folds,
            bankroll=bankroll,
            use_ensemble=not no_ensemble,
            use_stacking=stacking,
            mode="sliding" if sliding else "expanding",
            window_matches=window_matches,
        )
        console.rule(f"[bold green]Walk-Forward — {LEAGUES[league].name}[/bold green]")
        console.print(f"  Folds: {len(summary.folds)}")
        for fold in summary.folds:
            console.print(
                f"    • test={fold.league}: "
                f"n_preds={fold.n_predictions}, n_bets={fold.n_bets}, "
                f"bankroll={fold.bankroll_final:.2f}"
            )

        table = Table(title="Aggregate (mean ± std across folds)")
        table.add_column("Metric")
        table.add_column("Mean", justify="right")
        table.add_column("Std", justify="right")
        table.add_column("Min", justify="right")
        table.add_column("Max", justify="right")
        for metric, stats in summary.aggregate.items():
            table.add_row(
                metric,
                f"{stats['mean']:.4f}",
                f"{stats['std']:.4f}",
                f"{stats['min']:.4f}",
                f"{stats['max']:.4f}",
            )
        console.print(table)
        summary.save()
        return

    bt = Backtester(
        initial_bankroll=bankroll,
        use_ensemble=not no_ensemble,
        use_stacking=stacking,
        calibration_method=calibration_method,
    )
    result = bt.run(league)

    console.rule(f"[bold green]Backtest — {LEAGUES[league].name}[/bold green]")
    console.print(f"  Predictions: {result.n_predictions}")
    console.print(f"  Bets placed: {result.n_bets}")
    console.print(f"  Bankroll final: {result.bankroll_final:.2f}")
    console.print(f"  Max drawdown: {result.max_drawdown['max_drawdown_pct'] * 100:.1f}%")

    table = Table(title="Metrics")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for k, v in {**result.metrics, **result.bet_metrics}.items():
        table.add_row(k, f"{v:.4f}" if isinstance(v, float) else str(v))
    console.print(table)

    result.save()


# ───────────────────────── sweep-cushion ─────────────────────────


@main.command("sweep-cushion")
@click.option(
    "--league",
    "-l",
    type=click.Choice(list(LEAGUES.keys()), case_sensitive=False),
    required=True,
)
@click.option(
    "--cushions",
    default="0.0,0.02,0.03,0.05,0.08",
    show_default=True,
    help="Comma-separated min_ev_pct values to sweep on the standard test holdout.",
)
@click.option("--bankroll", default=1000.0, show_default=True)
@click.option("--no-ensemble", is_flag=True)
@click.option(
    "--calibration-method",
    type=click.Choice(["auto", "isotonic", "sigmoid"], case_sensitive=False),
    default=None,
    help="Override the CatBoost calibration method (default: auto).",
)
@click.option(
    "--stacking",
    is_flag=True,
    help="Use Phase 7 stacking meta-learner for prediction (matches backtest --stacking).",
)
def sweep_cushion(
    league: str,
    cushions: str,
    bankroll: float,
    no_ensemble: bool,
    calibration_method: str | None,
    stacking: bool,
) -> None:
    """Sweep BettingConfig.min_ev_pct on the standard backtest holdout.

    Trains the model once, then re-runs the financial layer for each cushion
    value to find the CLV-neutral sweet spot. Reports n_bets, ROI, CLV mean
    and CLV % positive per cushion.
    """
    league = league.upper()
    try:
        grid = sorted({float(x.strip()) for x in cushions.split(",") if x.strip()})
    except ValueError as exc:
        raise click.BadParameter(f"Invalid cushion grid: {exc}") from exc
    if not grid:
        raise click.BadParameter("At least one cushion value is required")

    table = Table(title=f"min_ev_pct sweep — {LEAGUES[league].name}")
    table.add_column("min_ev_pct", justify="right")
    table.add_column("n_bets", justify="right")
    table.add_column("ROI", justify="right")
    table.add_column("CLV mean", justify="right")
    table.add_column("CLV %+", justify="right")
    table.add_column("Bankroll", justify="right")

    for cushion in grid:
        bet_cfg = BettingConfig(
            min_edge=BETTING_CFG.min_edge,
            kelly_fraction=BETTING_CFG.kelly_fraction,
            max_stake_pct=BETTING_CFG.max_stake_pct,
            min_odds=BETTING_CFG.min_odds,
            max_odds=BETTING_CFG.max_odds,
            devig_method=BETTING_CFG.devig_method,
            min_ev_pct=cushion,
        )
        bt = Backtester(
            bet_cfg=bet_cfg,
            initial_bankroll=bankroll,
            use_ensemble=not no_ensemble,
            use_stacking=stacking,
            calibration_method=calibration_method,
        )
        result = bt.run(league)
        bm = result.bet_metrics
        table.add_row(
            f"{cushion:.3f}",
            str(int(bm.get("n_bets", 0))),
            f"{bm.get('roi', 0.0):+.2%}",
            f"{bm.get('clv_mean', 0.0):+.4f}",
            f"{bm.get('clv_pct_positive', 0.0):.1%}",
            f"{result.bankroll_final:,.2f}",
        )

    console.print(table)


# ───────────────────────── calibration-audit ─────────────────────────


@main.command("calibration-audit")
@click.option(
    "--league",
    "-l",
    type=click.Choice(list(LEAGUES.keys()), case_sensitive=False),
    required=True,
)
@click.option("--n-bins", type=click.IntRange(5, 30), default=10, show_default=True)
@click.option("--bankroll", default=1000.0, show_default=True)
@click.option(
    "--cb-only",
    is_flag=True,
    default=False,
    help="Audit CatBoost head in isolation (bypass ensemble blending).",
)
@click.option(
    "--calibration-method",
    type=click.Choice(["auto", "isotonic", "sigmoid"], case_sensitive=False),
    default=None,
    help="Override the CatBoost calibration method (default: auto).",
)
def calibration_audit(
    league: str,
    n_bins: int,
    bankroll: float,
    cb_only: bool,
    calibration_method: str | None,
) -> None:
    """ECE + reliability bins on the standard backtest holdout.

    Runs the model through the holdout season and reports Expected
    Calibration Error plus a per-bin breakdown of confidence vs realised
    accuracy. ECE > 1.5% on any league flags a calibration issue that
    will systematically bias value-bet selection.
    """
    import numpy as np

    from football_betting.predict.calibration import (
        expected_calibration_error,
        reliability_diagram_data,
    )

    league = league.upper()
    bt = Backtester(
        initial_bankroll=bankroll,
        use_ensemble=not cb_only,
        calibration_method=calibration_method,
    )
    result = bt.run(league)

    rows = [r for r in result.rows if "prob_home" in r and "actual" in r]
    if not rows:
        console.print("[red]Backtest produced no per-match rows with prob/actual.[/red]")
        raise click.Abort()

    label_to_idx = {"H": 0, "D": 1, "A": 2}
    probs = np.array([[r["prob_home"], r["prob_draw"], r["prob_away"]] for r in rows], dtype=float)
    y_true = np.array([label_to_idx[str(r["actual"])] for r in rows], dtype=int)

    ece = expected_calibration_error(probs, y_true, n_bins=n_bins)
    rel = reliability_diagram_data(probs, y_true, n_bins=n_bins)

    verdict = (
        "[green]EXCELLENT[/green]"
        if ece < 0.015
        else "[yellow]ACCEPTABLE[/yellow]"
        if ece < 0.03
        else "[red]MISCALIBRATED — refit calibrator[/red]"
    )
    console.rule(f"[bold cyan]Calibration audit — {LEAGUES[league].name}[/bold cyan]")
    console.print(f"  ECE ({n_bins} bins, n={len(rows)}): [bold]{ece:.4f}[/bold]  ->  {verdict}")

    table = Table(title="Reliability bins")
    table.add_column("conf bin", justify="right")
    table.add_column("n", justify="right")
    table.add_column("conf mean", justify="right")
    table.add_column("acc", justify="right")
    table.add_column("gap", justify="right")
    for c, conf, acc, n in zip(
        rel["bin_center"],
        rel["bin_confidence"],
        rel["bin_accuracy"],
        rel["bin_count"],
        strict=False,
    ):
        gap = float(conf) - float(acc)
        colour = "red" if abs(gap) > 0.05 else "yellow" if abs(gap) > 0.02 else "green"
        table.add_row(
            f"{float(c):.2f}",
            str(int(n)),
            f"{float(conf):.3f}",
            f"{float(acc):.3f}",
            f"[{colour}]{gap:+.3f}[/{colour}]",
        )
    console.print(table)


# ───────────────────────── snapshot-freshness-audit ─────────────────────────


@main.command("snapshot-freshness-audit")
@click.option(
    "--league",
    "-l",
    type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False),
    default="all",
    show_default=True,
)
@click.option(
    "--min-lead-hours",
    type=int,
    default=24,
    show_default=True,
    help="Lead time (kickoff - capture) below which a snapshot is not 'opening'.",
)
def snapshot_freshness_audit(league: str, min_lead_hours: int) -> None:
    """Audit whether persisted odds snapshots actually capture opening lines.

    For CLV to be a meaningful signal, ``bet_odds_at_placement`` must be
    recorded significantly before kickoff — ideally T-24h to T-48h. If the
    median lead time is near zero the 'opening' line is effectively the
    closing line, and CLV measurement degenerates to noise.
    """
    import statistics
    from datetime import date as date_cls
    from datetime import datetime

    from football_betting.data.loader import load_league
    from football_betting.data.odds_snapshots import _iter_records

    leagues = list(LEAGUES.keys()) if league.lower() == "all" else [league.upper()]

    console.rule("[bold cyan]Snapshot freshness audit[/bold cyan]")
    overall_ok = True

    summary = Table(title="Per-league freshness")
    summary.add_column("League")
    summary.add_column("rows", justify="right")
    summary.add_column("fixtures", justify="right")
    summary.add_column("≥2 snap", justify="right")
    summary.add_column("median lead (h)", justify="right")
    summary.add_column("p90 lead (h)", justify="right")
    summary.add_column("fresh %", justify="right")
    summary.add_column("verdict")

    for lg in leagues:
        rows = list(_iter_records(lg))
        if not rows:
            summary.add_row(lg, "0", "-", "-", "-", "-", "-", "[red]NO DATA[/red]")
            overall_ok = False
            continue

        # Build kickoff lookup from CSV-loaded Match objects.
        try:
            matches = load_league(lg)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]{lg}: could not load matches: {exc}[/red]")
            continue
        kickoff_by_key: dict[tuple[str, str, str], datetime] = {}
        for m in matches:
            if m.kickoff_datetime_utc is None:
                continue
            ko = m.kickoff_datetime_utc
            if ko.tzinfo is None:
                ko = ko.replace(tzinfo=UTC)
            kickoff_by_key[(m.date.isoformat(), m.home_team, m.away_team)] = ko

        fixtures: dict[tuple[str, str, str], list[datetime]] = {}
        for rec in rows:
            try:
                key = (rec["date"], rec["home"], rec["away"])
                ts = datetime.fromisoformat(rec["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
            except (KeyError, ValueError):
                continue
            fixtures.setdefault(key, []).append(ts)

        # Lead time = kickoff - earliest capture. Fall back to 18:00 UTC on
        # match date when real kickoff is unavailable (CSVs lag live fixtures).
        leads: list[float] = []
        for key, stamps in fixtures.items():
            earliest = min(stamps)
            ko = kickoff_by_key.get(key)
            if ko is None:
                try:
                    ko = datetime.fromisoformat(key[0]).replace(hour=18, tzinfo=UTC)
                except ValueError:
                    continue
            leads.append((ko - earliest).total_seconds() / 3600.0)

        n_fix = len(fixtures)
        n_multi = sum(1 for v in fixtures.values() if len(v) >= 2)
        if leads:
            median_lead = statistics.median(leads)
            p90_lead = statistics.quantiles(leads, n=10)[-1] if len(leads) >= 10 else max(leads)
            n_fresh = sum(1 for h in leads if h >= min_lead_hours)
            fresh_pct = 100.0 * n_fresh / len(leads)
        else:
            median_lead = p90_lead = fresh_pct = 0.0

        if median_lead >= min_lead_hours:
            verdict = "[green]OK[/green]"
        elif median_lead >= 1.0:
            verdict = "[yellow]TOO LATE[/yellow]"
            overall_ok = False
        else:
            verdict = "[red]CLOSING-ONLY[/red]"
            overall_ok = False

        summary.add_row(
            lg,
            str(len(rows)),
            str(n_fix),
            str(n_multi),
            f"{median_lead:+.2f}",
            f"{p90_lead:+.2f}",
            f"{fresh_pct:.0f}%",
            verdict,
        )

    console.print(summary)

    # Training-data degeneracy: how many historical matches have
    # opening_odds == odds (i.e. CLV == 0 by construction)?
    deg_table = Table(title="CSV opening-vs-closing degeneracy (training data)")
    deg_table.add_column("League")
    deg_table.add_column("matches", justify="right")
    deg_table.add_column("with opening", justify="right")
    deg_table.add_column("degenerate", justify="right")
    deg_table.add_column("non-degenerate %", justify="right")

    for lg in leagues:
        try:
            matches = load_league(lg)
        except Exception:  # noqa: BLE001
            continue
        n_total = len(matches)
        n_with_op = sum(1 for m in matches if m.opening_odds is not None)
        n_degen = 0
        n_nondeg = 0
        for m in matches:
            if m.opening_odds is None or m.odds is None:
                continue
            same = (
                m.opening_odds.home == m.odds.home
                and m.opening_odds.draw == m.odds.draw
                and m.opening_odds.away == m.odds.away
            )
            if same:
                n_degen += 1
            else:
                n_nondeg += 1
        nd_pct = 100.0 * n_nondeg / n_with_op if n_with_op else 0.0
        deg_table.add_row(lg, str(n_total), str(n_with_op), str(n_degen), f"{nd_pct:.1f}%")

    console.print(deg_table)

    if not overall_ok:
        console.print(
            "\n[yellow]Action:[/yellow] run [bold]fb snapshot-odds[/bold] on a "
            f"schedule that captures T-{min_lead_hours}h+ before kickoff "
            "(e.g. cron daily at 06:00 UTC, not on matchday)."
        )
    _ = date_cls  # silence unused-import


# ───────────────────────── tune-ensemble ─────────────────────────


@main.command("tune-ensemble")
@click.option(
    "--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True
)
@click.option("--val-season", default="2024-25")
@click.option(
    "--objective",
    type=click.Choice(
        ["rps", "log_loss", "brier", "clv", "blended", "brier_logloss_blended"],
        case_sensitive=False,
    ),
    default="rps",
    help="Tuning objective. 'clv'/'blended' require opening-line snapshots. "
    "'brier_logloss_blended' minimises equally-weighted z(Brier)+z(LogLoss) (Phase 4).",
)
@click.option(
    "--blend",
    default=0.5,
    show_default=True,
    help="Weight of RPS in 'blended' objective (0 = CLV only, 1 = RPS only).",
)
@click.option(
    "--use-sequence/--no-sequence",
    default=True,
    show_default=True,
    help="Include 1D-CNN+Transformer sequence head in the ensemble (if trained).",
)
@click.option(
    "--use-mlp/--no-mlp",
    default=True,
    show_default=True,
    help="Include MLP head in the ensemble (if trained).",
)
@click.option(
    "--save/--no-save",
    default=True,
    show_default=True,
    help="Persist tuned weights to models/ensemble_weights_<LEAGUE>.json.",
)
@click.option(
    "--purpose",
    type=click.Choice(["1x2", "value"], case_sensitive=False),
    default="1x2",
    show_default=True,
    help="Dual-model split: tune weights for the 1X2 stack (default) or the value-bet stack.",
)
def tune_ensemble(
    league: str,
    val_season: str,
    objective: str,
    blend: float,
    use_sequence: bool,
    use_mlp: bool,
    save: bool,
    purpose: str,
) -> None:
    """Dirichlet-sampled ensemble weight tuning (RPS / CLV / blended / Brier+LogLoss)."""
    from football_betting.config import artifact_suffix
    from football_betting.data.snapshot_service import merge_snapshots_into_matches
    from football_betting.predict.ensemble import ensemble_weights_path
    from football_betting.predict.sequence_model import SequencePredictor

    league = league.upper()
    objective = objective.lower()
    purpose = purpose.lower()
    suffix = artifact_suffix(purpose)  # type: ignore[arg-type]
    matches = load_league(league)
    val_matches = [m for m in matches if m.season == val_season]
    train_matches = [m for m in matches if m.season < val_season]

    # Phase 6 + Phase 4: overlay opening-line snapshots so CLV is non-degenerate
    val_matches = merge_snapshots_into_matches(val_matches, league)

    fb = _make_feature_builder(purpose=purpose)
    all_seasons = {m.season for m in train_matches} | {val_season}
    for season in all_seasons:
        sf = SofascoreClient.load_matches(league, season)
        if sf:
            fb.stage_sofascore_batch(sf)
    fb.fit_on_history(train_matches)

    model_path = MODELS_DIR / f"catboost_{league}{suffix}.cbm"
    if not model_path.exists():
        console.print(f"[red]No CatBoost at {model_path}[/red]")
        raise click.Abort()

    cb = CatBoostPredictor.for_league(league, fb, purpose=purpose)  # type: ignore[arg-type]
    poisson = PoissonModel(pi_ratings=fb.pi_ratings)
    mlp = (
        MLPPredictor.for_league(league, fb, purpose=purpose)  # type: ignore[arg-type]
        if use_mlp
        else None
    )

    # Optional 4th ensemble member: 1D-CNN + Transformer sequence head
    sequence: SequencePredictor | None = None
    seq_path = MODELS_DIR / f"sequence_{league}{suffix}.pt"
    if use_sequence and seq_path.exists():
        from football_betting.predict.sequence_features import (
            build_dataset as seq_build_dataset,
        )

        sequence = SequencePredictor(purpose=purpose)  # type: ignore[arg-type]
        sequence.load(seq_path)
        # Replay history so form/pi trackers are current by val_season kickoff
        seq_build_dataset(
            sorted(train_matches, key=lambda m: m.date),
            sequence.form_tracker,
            sequence.pi_ratings,
            window_t=sequence.cfg.window_t,
            warmup_games=0,
        )
        console.log(f"[green]Sequence head loaded: {seq_path}[/green]")
    elif use_sequence:
        console.log(f"[yellow]No Sequence model at {seq_path} — skipping.[/yellow]")

    ensemble = EnsembleModel(
        catboost=cb,
        poisson=poisson,
        mlp=mlp,
        sequence=sequence,
    )

    fixtures = []
    actuals = []
    bet_odds_triples: list[tuple[float, float, float] | None] = []
    close_odds_triples: list[tuple[float, float, float] | None] = []
    for m in sorted(val_matches, key=lambda m: m.date):
        fixtures.append(
            Fixture(
                date=m.date,
                league=m.league,
                home_team=m.home_team,
                away_team=m.away_team,
                odds=m.odds,
            )
        )
        actuals.append(m.result)
        closing = m.odds
        opening = getattr(m, "opening_odds", None) or closing
        bet_odds_triples.append((opening.home, opening.draw, opening.away) if opening else None)
        close_odds_triples.append((closing.home, closing.draw, closing.away) if closing else None)

    if objective in ("clv", "blended"):
        result = ensemble.tune_dirichlet(
            fixtures,
            actuals,
            bet_odds=bet_odds_triples,
            closing_odds=close_odds_triples,
            objective=objective,  # type: ignore[arg-type]
            blend=blend,
        )
    elif objective in ("log_loss", "brier", "brier_logloss_blended"):
        result = ensemble.tune_dirichlet(
            fixtures,
            actuals,
            objective=objective,  # type: ignore[arg-type]
        )
    else:
        result = ensemble.tune_weights(fixtures, actuals)

    console.print(f"[bold]Best weights (objective={objective}):[/bold]")
    console.print(f"  CatBoost: {result['best_w_catboost']:.3f}")
    console.print(f"  Poisson:  {result['best_w_poisson']:.3f}")
    if mlp is not None:
        console.print(f"  MLP:      {result['best_w_mlp']:.3f}")
    if sequence is not None:
        console.print(f"  Sequence: {result['best_w_sequence']:.3f}")
    skip = {
        "best_w_catboost",
        "best_w_poisson",
        "best_w_mlp",
        "best_w_sequence",
        "n_samples_tried",
        "objective",
    }
    if save:
        weights_path = ensemble_weights_path(league, purpose=purpose)  # type: ignore[arg-type]
        ensemble.save_weights(
            weights_path,
            metadata={
                "league": league,
                "purpose": purpose,
                "val_season": val_season,
                "objective": objective,
                "blend": blend if objective == "blended" else None,
                "active_members": result.get("active_members"),
                "score_key": next(
                    (
                        k
                        for k in result
                        if k.startswith("best_")
                        and k
                        not in {
                            "best_w_catboost",
                            "best_w_poisson",
                            "best_w_mlp",
                            "best_w_sequence",
                        }
                    ),
                    None,
                ),
                "score_value": next(
                    (
                        float(v)
                        for k, v in result.items()
                        if k.startswith("best_")
                        and k
                        not in {
                            "best_w_catboost",
                            "best_w_poisson",
                            "best_w_mlp",
                            "best_w_sequence",
                        }
                        and isinstance(v, (int, float))
                    ),
                    None,
                ),
            },
        )
        console.print(f"[green]Saved weights → {weights_path}[/green]")

    for k, v in result.items():
        if k in skip:
            continue
        if isinstance(v, float):
            console.print(f"  {k}: {v:.4f}")
        else:
            console.print(f"  {k}: {v}")


# ───────────────────────── monitor (v0.3) ─────────────────────────


@main.command()
@click.option(
    "--league", "-l", type=click.Choice(list(LEAGUES.keys()), case_sensitive=False), required=True
)
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
        console.print(
            f"[yellow]Too few production matches ({len(prod_matches)}) "
            f"in last {recent_days} days.[/yellow]"
        )
        return

    console.log(f"Training window: {len(train_matches)} matches")
    console.log(f"Production window: {len(prod_matches)} matches")

    # Build features separately
    train_fb = _make_feature_builder()
    train_rows = []
    sorted_train = sorted(train_matches, key=lambda m: m.date)
    for m in sorted_train[-500:]:  # last 500 training matches
        train_fb.update_with_match(m)
    for m in sorted_train[-200:]:
        feats = train_fb.build_features(
            m.home_team,
            m.away_team,
            m.league,
            m.date,
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
            m.home_team,
            m.away_team,
            m.league,
            m.date,
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
            home_team=r["home_team"],
            away_team=r["away_team"],
            match_date=r["date"],
            home_goals=r["home_goals"],
            away_goals=r["away_goals"],
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
@click.option(
    "--staking-strategy",
    type=click.Choice(["flat", "conf", "power", "hybrid", "entropy"]),
    default=None,
    help="1X2 prediction staking strategy (default: config value, usually 'hybrid').",
)
def snapshot(fixtures: str | None, bankroll: float, staking_strategy: str | None) -> None:
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
    payload = build_predictions_for_fixtures(
        fixtures_data, bankroll=bankroll, staking_strategy=staking_strategy
    )
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
    "--snapshot",
    "snapshot_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to today.json (defaults to data/snapshots/today.json).",
)
@click.option(
    "--force",
    is_flag=True,
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
    "--league",
    "-l",
    type=click.Choice(["all", *LEAGUES.keys()], case_sensitive=False),
    default="all",
    help="Resolve stadiums for one league or all.",
)
@click.option(
    "--seasons",
    "-s",
    multiple=True,
    default=("2021-22", "2022-23", "2023-24", "2024-25", "2025-26"),
    help="Seasons to scan for the team universe.",
)
@click.option(
    "--out",
    "-o",
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
                console.log(
                    f"  {team} → {result.name}, {result.country} ({result.lat:.3f}, {result.lon:.3f})"
                )
            progress.advance(task)

    out_path.write_text(json.dumps(resolved, indent=2, ensure_ascii=False), encoding="utf-8")
    console.log(f"[green]Wrote {out_path}[/green]")
    console.log(f"  resolved: {sum(1 for v in resolved.values() if v)}")
    console.log(f"  unresolved: {len(failed)}")
    if failed:
        console.log(
            f"[yellow]Unresolved: {', '.join(failed[:10])}{'...' if len(failed) > 10 else ''}[/yellow]"
        )


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
        raise click.ClickException(f"League {league} has no sofascore_tournament_id configured.")
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
            ok = "yes" if (_name_matches(hn, h_norm) and _name_matches(an, a_norm)) else ""
            table.add_row(
                target_d.isoformat(),
                str(ev.get("id", "")),
                ev_home,
                ev_away,
                hn,
                an,
                ok,
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
            'uvicorn is not installed. Run: pip install -e ".[api]"'
        ) from exc

    console.log(f"[cyan]Serving Betting with AI on http://{host}:{port}[/cyan]")
    uvicorn.run(
        "football_betting.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


# ───────────────────────── stress-test (Phase 5) ─────────────────────────


@main.command("stress-test")
@click.option(
    "--league",
    "-l",
    type=click.Choice(list(LEAGUES.keys()), case_sensitive=False),
    default="BL",
    show_default=True,
)
@click.option(
    "--bets-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="JSONL of bets (stake, odds, prob). Defaults to data/graded_bets.jsonl.",
)
@click.option(
    "--runs",
    type=click.IntRange(100, 1_000_000),
    default=10_000,
    show_default=True,
    help="Monte-Carlo paths.",
)
@click.option("--bankroll", type=float, default=1000.0, show_default=True)
@click.option(
    "--ruin-fraction",
    type=float,
    default=0.1,
    show_default=True,
    help="Bankroll floor as fraction of initial.",
)
@click.option("--seed", type=int, default=42, show_default=True)
def stress_test(
    league: str,
    bets_file: Path | None,
    runs: int,
    bankroll: float,
    ruin_fraction: float,
    seed: int,
) -> None:
    """Monte-Carlo bankroll stress test (Phase 5).

    Reads a bet history (graded_bets.jsonl by default), simulates N
    independent outcome sequences and reports drawdown + ruin risk.
    """
    import numpy as np

    from football_betting.tracking.monte_carlo import simulate_bankroll_paths

    path = bets_file or (DATA_DIR / "graded_bets.jsonl")
    if not path.exists():
        console.print(f"[red]Bets file not found: {path}[/red]")
        raise click.Abort()

    league_uc = league.upper()
    stakes: list[float] = []
    odds: list[float] = []
    probs: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("league", "").upper() != league_uc:
            continue
        try:
            s = float(rec.get("stake", 0.0))
            o = float(rec.get("odds", 0.0))
            raw_p = rec.get("prob", rec.get("model_prob"))
            # Fallback: use status-derived realized prob if no model prob is
            # stored. This lets legacy bet records (pre-model_prob) still be
            # stress-tested against odds alone via the 1/odds implied prob.
            if raw_p is None:
                if o > 1.0:
                    p = 1.0 / o
                else:
                    continue
            else:
                p = float(raw_p)
        except (TypeError, ValueError):
            continue
        if s > 0.0 and o > 1.0 and 0.0 < p < 1.0:
            stakes.append(s)
            odds.append(o)
            probs.append(p)

    if not stakes:
        console.print(f"[yellow]No eligible bets for {league_uc} in {path}[/yellow]")
        raise click.Abort()

    res = simulate_bankroll_paths(
        np.asarray(stakes),
        np.asarray(odds),
        np.asarray(probs),
        initial_bankroll=bankroll,
        n_paths=runs,
        ruin_threshold_fraction=ruin_fraction,
        seed=seed,
    )

    table = Table(title=f"Bankroll Stress Test — {league_uc} ({len(stakes)} bets, {runs} paths)")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta", justify="right")
    table.add_row("Initial bankroll", f"{res.initial_bankroll:.2f}")
    table.add_row("Final bankroll mean", f"{res.final_bankroll_mean:.2f}")
    table.add_row("Final bankroll median", f"{res.final_bankroll_median:.2f}")
    table.add_row("Final bankroll P05", f"{res.final_bankroll_p05:.2f}")
    table.add_row("Final bankroll P95", f"{res.final_bankroll_p95:.2f}")
    table.add_row("Max drawdown mean", f"{res.max_drawdown_mean:.2%}")
    table.add_row("Max drawdown P95", f"{res.max_drawdown_p95:.2%}")
    table.add_row("Risk of ruin", f"{res.risk_of_ruin:.2%}")
    table.add_row("CAGR mean", f"{res.cagr_mean:.2%}")
    table.add_row("CAGR P05", f"{res.cagr_p05:.2%}")
    console.print(table)


if __name__ == "__main__":
    main()
