"""Central configuration — v0.3."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ───────────────────────── Paths ─────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PREDICTIONS_DIR = DATA_DIR / "predictions"
BACKTEST_DIR = DATA_DIR / "backtests"
SOFASCORE_DIR = DATA_DIR / "sofascore"
MONITORING_DIR = DATA_DIR / "monitoring"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
WEATHER_DIR = DATA_DIR / "weather"
MODELS_DIR = PROJECT_ROOT / "models"
SUPPORT_DATA_DIR = DATA_DIR / "support_faq"
SUPPORT_MODELS_DIR = MODELS_DIR / "support"

for d in (
    RAW_DIR, PROCESSED_DIR, PREDICTIONS_DIR,
    BACKTEST_DIR, SOFASCORE_DIR, MONITORING_DIR, SNAPSHOT_DIR, WEATHER_DIR, MODELS_DIR,
    SUPPORT_MODELS_DIR,
):
    d.mkdir(parents=True, exist_ok=True)


# ───────────────────────── League Configs ─────────────────────────

@dataclass(frozen=True, slots=True)
class LeagueConfig:
    key: str
    code: str
    name: str
    avg_goals_per_team: float
    home_advantage: float
    shot_conv_rate: float = 0.105
    sot_conv_rate: float = 0.32
    sofascore_tournament_id: int | None = None  # for Sofascore scraping
    sofascore_season_ids: dict[str, int] = field(default_factory=dict)
    download_url_template: str = (
        "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
    )

    def url(self, season: str) -> str:
        return self.download_url_template.format(season=season, code=self.code)


# Sofascore tournament IDs (verified from sofascore.com URL paths)
LEAGUES: dict[str, LeagueConfig] = {
    "PL": LeagueConfig(
        "PL", "E0", "Premier League", 1.45, 0.38, 0.110, 0.33,
        sofascore_tournament_id=17,
    ),
    "CH": LeagueConfig(
        "CH", "E1", "EFL Championship", 1.40, 0.38, 0.102, 0.31,
        sofascore_tournament_id=18,
    ),
    "BL": LeagueConfig(
        "BL", "D1", "Bundesliga", 1.50, 0.40, 0.108, 0.32,
        sofascore_tournament_id=35,
    ),
    "SA": LeagueConfig(
        "SA", "I1", "Serie A", 1.35, 0.33, 0.100, 0.30,
        sofascore_tournament_id=23,
    ),
    "LL": LeagueConfig(
        "LL", "SP1", "La Liga", 1.30, 0.32, 0.098, 0.30,
        sofascore_tournament_id=8,
    ),
}


# ───────────────────────── Pi-Ratings ─────────────────────────

@dataclass(frozen=True, slots=True)
class PiRatingsConfig:
    learning_rate: float = 0.054
    cross_venue_weight: float = 0.79
    initial_rating: float = 0.0
    diff_scale: float = 3.0


# ───────────────────────── Feature Configs ─────────────────────────

@dataclass(frozen=True, slots=True)
class FormConfig:
    window_size: int = 10
    decay_rate: float = 0.85
    min_games: int = 3


@dataclass(frozen=True, slots=True)
class XgProxyConfig:
    window_size: int = 10
    decay_rate: float = 0.85
    sot_weight: float = 3.0


@dataclass(frozen=True, slots=True)
class RealXgConfig:
    """v0.3: Real Sofascore-sourced xG."""

    window_size: int = 10
    decay_rate: float = 0.85
    home_away_split: bool = True


@dataclass(frozen=True, slots=True)
class SquadQualityConfig:
    """v0.3: Lineup-based squad features."""

    rating_window: int = 5  # last N matches for rolling squad rating
    season_xi_min_games: int = 10  # min games to establish "season XI"
    absence_threshold: float = 0.7  # player played >=70% → "key player"


@dataclass(frozen=True, slots=True)
class MarketMovementConfig:
    """v0.3: Odds movement tracking."""

    steam_threshold_pct: float = 0.05  # >5% odds change = steam
    steam_window_minutes: int = 30
    min_consensus_bookmakers: int = 3


@dataclass(frozen=True, slots=True)
class H2HConfig:
    max_games: int = 6


@dataclass(frozen=True, slots=True)
class RestDaysConfig:
    fatigue_threshold_days: int = 4
    optimal_min_days: int = 3
    optimal_max_days: int = 7
    long_break_threshold: int = 14


@dataclass(frozen=True, slots=True)
class HomeAdvantageConfig:
    min_home_games: int = 5
    window_games: int = 25


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    use_pi_ratings: bool = True
    use_form: bool = True
    use_xg_proxy: bool = True  # fallback if no Sofascore data
    use_real_xg: bool = True  # v0.3: prefer if available
    use_h2h: bool = True
    use_rest_days: bool = True
    use_home_advantage: bool = True
    use_market_odds: bool = True
    use_squad_quality: bool = True  # v0.3
    use_market_movement: bool = True  # v0.3
    use_weather: bool = True  # v0.4 (Familie A — Match-Day Weather)

    form: FormConfig = field(default_factory=FormConfig)
    xg: XgProxyConfig = field(default_factory=XgProxyConfig)
    real_xg: RealXgConfig = field(default_factory=RealXgConfig)
    squad_quality: SquadQualityConfig = field(default_factory=SquadQualityConfig)
    market_movement: MarketMovementConfig = field(default_factory=MarketMovementConfig)
    h2h: H2HConfig = field(default_factory=H2HConfig)
    rest_days: RestDaysConfig = field(default_factory=RestDaysConfig)
    home_adv: HomeAdvantageConfig = field(default_factory=HomeAdvantageConfig)


# ───────────────────────── CatBoost ─────────────────────────

@dataclass(frozen=True, slots=True)
class CatBoostConfig:
    iterations: int = 1500
    learning_rate: float = 0.03
    depth: int = 6
    l2_leaf_reg: float = 3.0
    loss_function: str = "MultiClass"
    eval_metric: str = "MultiClass"
    random_seed: int = 42
    early_stopping_rounds: int = 100
    verbose: int = 100


# ───────────────────────── MLP (v0.3) ─────────────────────────

@dataclass(frozen=True, slots=True)
class MLPConfig:
    """PyTorch MLP hyperparameters."""

    hidden_dims: tuple[int, ...] = (128, 64, 32)
    dropout: float = 0.3
    batch_norm: bool = True
    learning_rate: float = 0.001
    batch_size: int = 64
    epochs: int = 200
    early_stopping_patience: int = 20
    weight_decay: float = 1e-5
    random_seed: int = 42


# ───────────────────────── Sofascore (v0.3) ─────────────────────────

@dataclass(frozen=True, slots=True)
class SofascoreConfig:
    """Scraper configuration."""

    base_url: str = "https://api.sofascore.com/api/v1"
    request_delay_seconds: float = 25.0  # conservative rate limit
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_base: float = 2.0  # seconds
    cache_ttl_days: int = 7
    cache_ttl_live_days: int = 0  # live match data → no cache
    # Browser-like headers to bypass basic bot detection
    user_agents: tuple[str, ...] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    )

    @property
    def enabled(self) -> bool:
        """Opt-in via env var for safety."""
        return os.getenv("SCRAPING_ENABLED", "0") == "1"


# ───────────────────────── Weather (v0.4) ─────────────────────────

@dataclass(frozen=True, slots=True)
class WeatherConfig:
    """Open-Meteo weather feature configuration (v0.4 — Phase 1+2)."""

    enabled: bool = True
    use_match_day_weather: bool = True   # Familie A — active in this phase
    use_weather_shock: bool = False      # Familie B — Phase 3
    use_simons_signal: bool = False      # Familie C — Phase 3

    # ±hours around kickoff to average hourly observations
    kickoff_window_hours: int = 3
    # Fallback when Match.kickoff_datetime_utc is None
    default_kickoff_hour_utc: int = 19

    # Open-Meteo endpoints (no API key required)
    historical_api: str = "https://archive-api.open-meteo.com/v1/archive"
    forecast_api: str = "https://api.open-meteo.com/v1/forecast"
    geocoding_api: str = "https://geocoding-api.open-meteo.com/v1/search"

    # Rate limit (Open-Meteo allows 10k req/day; 0.5s ≈ 7200/h is fine)
    request_delay_seconds: float = 0.5
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    cache_ttl_days: int = 30  # historical weather is immutable

    # Forecast vs archive routing: dates older than (today - this) → archive
    forecast_horizon_days: int = 14


# ───────────────────────── The Odds API ─────────────────────────

@dataclass(frozen=True, slots=True)
class OddsApiConfig:
    """Config for https://the-odds-api.com/ — provides fixtures + odds."""

    base_url: str = "https://api.the-odds-api.com/v4"
    regions: str = "eu"
    markets: str = "h2h"
    odds_format: str = "decimal"
    date_format: str = "iso"
    timeout_seconds: float = 20.0

    # football-data CSV key → The Odds API `sport_key`
    sport_keys: dict[str, str] = field(
        default_factory=lambda: {
            "PL": "soccer_epl",
            "CH": "soccer_efl_champ",
            "BL": "soccer_germany_bundesliga",
            "SA": "soccer_italy_serie_a",
            "LL": "soccer_spain_la_liga",
        }
    )

    @property
    def api_key(self) -> str | None:
        return os.getenv("ODDS_API_KEY") or None


# ───────────────────────── Calibration ─────────────────────────

@dataclass(frozen=True, slots=True)
class CalibrationConfig:
    method: str = "isotonic"
    min_samples_per_class: int = 50


# ───────────────────────── Monitoring (v0.3) ─────────────────────────

@dataclass(frozen=True, slots=True)
class MonitoringConfig:
    """Data quality & model drift monitoring."""

    ks_test_threshold: float = 0.1  # KS statistic; >0.1 = significant drift
    missing_rate_threshold: float = 0.05  # >5% missing values → alert
    confidence_drift_sigma: float = 2.0  # alert if mean confidence > 2σ away
    n_bins_histogram: int = 20


# ───────────────────────── Betting ─────────────────────────

@dataclass(frozen=True, slots=True)
class BettingConfig:
    min_edge: float = 0.03
    kelly_fraction: float = 0.25
    max_stake_pct: float = 0.05
    min_odds: float = 1.30
    max_odds: float = 15.0


# ───────────────────────── Point Deductions ─────────────────────────

POINT_DEDUCTIONS: dict[tuple[str, str], int] = {
    ("Leicester", "2025-26"): 6,
    ("Sheffield Weds", "2025-26"): 18,
}


# ───────────────────────── Backtesting / Ensemble ─────────────────────────

@dataclass(frozen=True, slots=True)
class BacktestConfig:
    train_seasons: tuple[str, ...] = ("2021-22", "2022-23", "2023-24")
    test_season: str = "2024-25"
    min_train_games: int = 500
    update_frequency_days: int = 30


@dataclass(frozen=True, slots=True)
class EnsembleTuneConfig:
    """v0.3: now also supports 3-way Dirichlet sampling."""

    catboost_weights: tuple[float, ...] = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
    dirichlet_samples: int = 500  # for 3-way tuning
    dirichlet_alpha: tuple[float, float, float] = (2.0, 1.0, 1.5)  # CB, Poisson, MLP prior
    metric: str = "rps"


# ───────────────────────── Support Intent Classifier ─────────────────────────

@dataclass(frozen=True, slots=True)
class SupportConfig:
    """TF-IDF + Logistic Regression intent classifier for the FAQ chatbot."""

    # Dataset
    dataset_filename: str = "dataset_augmented.jsonl"
    metrics_filename: str = "support_intent_metrics.json"
    model_filename_template: str = "support_intent_{lang}.joblib"
    languages: tuple[str, ...] = ("en", "de", "es", "fr", "it")

    # Split
    val_fraction: float = 0.15
    random_seed: int = 42

    # Char n-gram vectorizer
    char_ngram_min: int = 3
    char_ngram_max: int = 5

    # Word n-gram vectorizer
    word_ngram_min: int = 1
    word_ngram_max: int = 2

    # Shared
    min_df: int = 2
    sublinear_tf: bool = True

    # Logistic Regression
    lr_C: float = 4.0
    lr_max_iter: int = 2000
    lr_solver: str = "lbfgs"
    lr_class_weight: str = "balanced"

    # Inference
    default_topk: int = 3

    # Soft quality gate (warn only)
    min_top1_accuracy: float = 0.75
    target_top1_accuracy: float = 0.88
    target_top3_accuracy: float = 0.97
    target_macro_f1: float = 0.85


# ───────────────────────── Defaults ─────────────────────────

PI_CFG = PiRatingsConfig()
FEATURE_CFG = FeatureConfig()
CATBOOST_CFG = CatBoostConfig()
MLP_CFG = MLPConfig()
SOFASCORE_CFG = SofascoreConfig()
WEATHER_CFG = WeatherConfig()
ODDS_API_CFG = OddsApiConfig()
CALIBRATION_CFG = CalibrationConfig()
MONITORING_CFG = MonitoringConfig()
BETTING_CFG = BettingConfig()
BACKTEST_CFG = BacktestConfig()
ENSEMBLE_TUNE_CFG = EnsembleTuneConfig()
SUPPORT_CFG = SupportConfig()
