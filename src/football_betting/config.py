"""Central configuration — v0.3."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

# ───────────────────────── Paths ─────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no external dep).

    Populates ``os.environ`` with ``KEY=VALUE`` pairs from ``path`` unless
    the variable is already set. Quotes, blank lines and ``#`` comments
    are stripped. Silently ignored if the file does not exist.
    """
    if not path.is_file():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export ") :].lstrip()
            key, _, value = line.partition("=")
            key = key.strip()
            if not key or key in os.environ:
                continue
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value
    except OSError:
        return


_load_dotenv(PROJECT_ROOT / ".env")

FixtureProvider = Literal["odds_api", "football_data", "sofascore"]
ScoreProvider = Literal["odds_api", "football_data"]


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def odds_api_disabled() -> bool:
    """Whether all automatic The Odds API calls should be bypassed."""
    return env_flag("ODDS_API_DISABLED", default=False)


def _normalise_fixture_provider(
    raw: str | None,
    default: FixtureProvider,
) -> FixtureProvider:
    value = (raw or default).strip().lower().replace("-", "_").replace(".", "_")
    if value in {"football_data", "footballdata", "football_data_co_uk"}:
        return "football_data"
    if value in {"sofascore", "sofa_score"}:
        return "sofascore"
    return "odds_api"


def _normalise_score_provider(raw: str | None, default: ScoreProvider) -> ScoreProvider:
    value = (raw or default).strip().lower().replace("-", "_").replace(".", "_")
    if value in {"football_data", "footballdata", "football_data_co_uk"}:
        return "football_data"
    return "odds_api"


def snapshot_fixture_source() -> FixtureProvider:
    """Provider used by the scheduler / CLI for the daily fixture snapshot."""
    raw = os.getenv("SNAPSHOT_FIXTURE_SOURCE") or os.getenv("FIXTURE_SOURCE")
    default: FixtureProvider = "football_data" if odds_api_disabled() else "odds_api"
    return _normalise_fixture_provider(raw, default)


def live_score_source() -> ScoreProvider:
    """Provider used by the live/result settlement loop."""
    raw = os.getenv("LIVE_SCORE_SOURCE") or os.getenv("SCORE_SOURCE")
    default: ScoreProvider = "football_data" if odds_api_disabled() else "odds_api"
    return _normalise_score_provider(raw, default)

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PREDICTIONS_DIR = DATA_DIR / "predictions"
BACKTEST_DIR = DATA_DIR / "backtests"
SOFASCORE_DIR = DATA_DIR / "sofascore"
MONITORING_DIR = DATA_DIR / "monitoring"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
ODDS_SNAPSHOT_DIR = DATA_DIR / "odds_snapshots"
WEATHER_DIR = DATA_DIR / "weather"
MODELS_DIR = PROJECT_ROOT / "models"
SUPPORT_DATA_DIR = DATA_DIR / "support_faq"
SUPPORT_MODELS_DIR = MODELS_DIR / "support"

for d in (
    RAW_DIR,
    PROCESSED_DIR,
    PREDICTIONS_DIR,
    BACKTEST_DIR,
    SOFASCORE_DIR,
    MONITORING_DIR,
    SNAPSHOT_DIR,
    ODDS_SNAPSHOT_DIR,
    WEATHER_DIR,
    MODELS_DIR,
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
    download_url_template: str = "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"

    def url(self, season: str) -> str:
        return self.download_url_template.format(season=season, code=self.code)


# Sofascore tournament IDs (verified from sofascore.com URL paths)
LEAGUES: dict[str, LeagueConfig] = {
    "PL": LeagueConfig(
        "PL",
        "E0",
        "Premier League",
        1.45,
        0.38,
        0.110,
        0.33,
        sofascore_tournament_id=17,
    ),
    "CH": LeagueConfig(
        "CH",
        "E1",
        "EFL Championship",
        1.40,
        0.38,
        0.102,
        0.31,
        sofascore_tournament_id=18,
    ),
    "BL": LeagueConfig(
        "BL",
        "D1",
        "Bundesliga",
        1.50,
        0.40,
        0.108,
        0.32,
        sofascore_tournament_id=35,
    ),
    "SA": LeagueConfig(
        "SA",
        "I1",
        "Serie A",
        1.35,
        0.33,
        0.100,
        0.30,
        sofascore_tournament_id=23,
    ),
    "LL": LeagueConfig(
        "LL",
        "SP1",
        "La Liga",
        1.30,
        0.32,
        0.098,
        0.30,
        sofascore_tournament_id=8,
    ),
}


# ───────────────────────── Model Purpose (dual-model split) ─────────────────────────

ModelPurpose = Literal["1x2", "value"]

# File-name suffix appended to every model artefact (``.cbm``, ``.pt``,
# ``ensemble_weights_*.json``) so the 1X2 pipeline and the value-bet
# pipeline can be trained and served completely independently.
MODEL_ARTIFACT_SUFFIX: dict[str, str] = {"1x2": "", "value": "_value"}


def artifact_suffix(purpose: ModelPurpose) -> str:
    """Return the filename suffix associated with a model purpose."""
    return MODEL_ARTIFACT_SUFFIX[purpose]


@dataclass(frozen=True, slots=True)
class ValueModelConfig:
    """Separate hyper-parameters for the value-bet model family.

    The value model must not learn from the market consensus directly — it
    has to beat it. We therefore drop every feature whose key matches one
    of the prefixes in ``feature_blocklist_prefixes`` before fitting. The
    Kelly-Loss is enabled for the Torch heads so the learner directly
    optimises expected log-growth rather than pure cross-entropy.
    """

    feature_blocklist_prefixes: tuple[str, ...] = (
        "market_",
        "mm_",
    )
    feature_blocklist_exact: tuple[str, ...] = ()
    use_kelly_loss: bool = True
    kelly_lambda: float = 0.5
    kelly_f_cap: float = 0.25


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
    # COVID ghost-games correction (empty stadiums reduce home advantage).
    # Applied multiplicatively to the team/league HA when a match date falls
    # inside one of the configured periods.
    ghost_factor: float = 0.35
    ghost_periods: tuple[tuple[date, date], ...] = (
        (date(2020, 3, 1), date(2021, 6, 30)),
        (date(2021, 8, 1), date(2021, 12, 31)),
    )


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
    use_market_microstructure: bool = False  # Phase 8 — opt-in, needs backfill
    use_weather: bool = (
        True  # v0.4 Phase 1: Familie A match-day weather enabled (Roadmap 2026-04-23)
    )
    use_standings: bool = False  # v0.4: A/B test — disabled to isolate CLV regression

    form: FormConfig = field(default_factory=FormConfig)
    xg: XgProxyConfig = field(default_factory=XgProxyConfig)
    real_xg: RealXgConfig = field(default_factory=RealXgConfig)
    squad_quality: SquadQualityConfig = field(default_factory=SquadQualityConfig)
    market_movement: MarketMovementConfig = field(default_factory=MarketMovementConfig)
    market_microstructure: MarketMicrostructureConfig = field(
        default_factory=lambda: MarketMicrostructureConfig()
    )
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
    # Time-decay sample weighting: newest season gets 1.0, older seasons get
    # decay**Δ. Set to None to disable weighting.
    time_decay: float | None = 0.85
    # GPU training (v0.4). Opt-in — default stays CPU for bit-reproducibility.
    use_gpu: bool = False
    gpu_devices: str = "0"
    # v0.4: CPU throughput tuning. ``thread_count=None`` keeps CatBoost's
    # auto-detection; ``grow_policy="Lossguide"`` + ``max_bin=254`` give a
    # moderate speedup over the default ``SymmetricTree`` on CPU.
    thread_count: int | None = None
    grow_policy: Literal["SymmetricTree", "Lossguide", "Depthwise"] = "SymmetricTree"
    max_bin: int = 254


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
    # v0.4: Differentiable Kelly-loss + AMP
    use_kelly_loss: bool = False
    kelly_lambda: float = 0.3
    kelly_f_cap: float = 0.25
    use_amp: bool = True
    # Phase C of gpu_kelly_training_plan: CLV-aware training on opening odds
    # + KL-shrinkage to market, masked on rows without opening odds.
    use_shrinkage_kelly: bool = False
    kelly_beta: float = 0.1
    kelly_warmup_epochs: int = 5
    kelly_lam_max: float = 0.5


@dataclass(frozen=True, slots=True)
class SequenceConfig:
    """v0.4: 1D-CNN + Transformer sequence model over last-N matches per team.

    Replaces the earlier GRU+Attention head. The CNN captures local temporal
    patterns (2–3 match streaks), then a small Transformer encoder models
    longer-range dependencies across the ``window_t`` match history.

    The ``gru_*`` / ``bidirectional`` fields are kept for config-file
    backwards-compat but are no longer read by the active network.
    """

    enabled: bool = False
    window_t: int = 10
    n_features: int = 14
    # Legacy (unused by 1D-CNN+Transformer — retained for deserialization) ---
    gru_hidden: int = 64
    gru_layers: int = 2
    bidirectional: bool = True
    # 1D-CNN + Transformer hyperparams ---------------------------------------
    conv_channels: int = 64
    conv_kernel: int = 3
    tx_layers: int = 2
    tx_heads: int = 4
    tx_ffn_factor: int = 2
    head_hidden: int = 128
    # Shared training hyperparams --------------------------------------------
    dropout: float = 0.2
    learning_rate: float = 5e-4
    batch_size: int = 128
    epochs: int = 25
    weight_decay: float = 1e-4
    use_kelly_loss: bool = False
    kelly_lambda: float = 0.3
    kelly_f_cap: float = 0.25
    # Phase C: CLV-aware opening-odds training + KL shrinkage.
    use_shrinkage_kelly: bool = False
    kelly_beta: float = 0.1
    kelly_warmup_epochs: int = 5
    kelly_lam_max: float = 0.5
    random_seed: int = 42


@dataclass(frozen=True, slots=True)
class TabTransformerConfig:
    """v0.4: FT-Transformer head over tabular features (1x2 classifier).

    Drop-in successor to the simple MLP head. ``d_token`` is the per-feature
    embedding width; the encoder runs ``n_blocks`` multi-head attention layers
    before the [CLS] token is routed through a 3-class linear head.
    """

    d_token: int = 96
    n_heads: int = 8
    n_blocks: int = 3
    ffn_factor: int = 2
    dropout: float = 0.2
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    batch_size: int = 256
    epochs: int = 120
    warmup_fraction: float = 0.08
    early_stopping_patience: int = 15
    label_smoothing: float = 0.02
    random_seed: int = 42
    # Phase C: CLV-aware opening-odds training + KL shrinkage.
    use_kelly_loss: bool = False
    kelly_lambda: float = 0.3
    kelly_f_cap: float = 0.25
    use_shrinkage_kelly: bool = False
    kelly_beta: float = 0.1
    kelly_warmup_epochs: int = 5
    kelly_lam_max: float = 0.5


@dataclass(frozen=True, slots=True)
class StackingConfig:
    """v0.4: Level-2 meta-learner stacking."""

    enabled: bool = False
    meta_learner: Literal["lr", "nn"] = "lr"
    inner_train_fraction: float = 0.80  # chrono split within train_seasons
    lr_C: float = 1.0
    lr_max_iter: int = 1000
    nn_hidden: int = 32
    nn_epochs: int = 50
    nn_lr: float = 1e-3
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
    use_match_day_weather: bool = True  # Familie A — active
    use_weather_shock: bool = False  # Familie B — Phase 3 evaluated 2026-04-25: net CLV −101 bp on 2024-25 (PL 1x2 −61 bp, SA value −43 bp). Importance present but markets price it in. Rolled back; re-evaluate after Phase 5/6 walk-forward.
    use_simons_signal: bool = False  # Familie C — inactive (control hypothesis; re-enable only for the Phase 6 permutation test)

    # ±hours around kickoff to average hourly observations
    kickoff_window_hours: int = 3
    # Fallback when Match.kickoff_datetime_utc is None
    default_kickoff_hour_utc: int = 19

    # Simons-Signal Paris morning window (UTC hours)
    simons_morning_hour_start: int = 6
    simons_morning_hour_end: int = 9
    # Paris reference coords (kept here for completeness; tracker hard-codes
    # the value to avoid unnecessary mutability).
    simons_reference_city: tuple[float, float] = (48.8566, 2.3522)

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

    @property
    def fallback_api_keys(self) -> list[str]:
        """Additional Odds-API keys tried when the primary one is exhausted.

        Comma-separated via env var ``ODDS_API_FALLBACK_KEYS``. If present,
        ``THEODDS_HISTORICAL_API_KEY`` is also accepted as a temporary
        fallback for the live/fixture endpoints so operators do not have to
        duplicate the same secret under two names. When no explicit fallback
        list is configured, a shared free-tier key is kept as a last resort so
        quota exhaustion on the primary key never silently breaks the
        live-score loop.
        """
        raw = os.getenv("ODDS_API_FALLBACK_KEYS")
        keys = [k.strip() for k in raw.split(",") if k.strip()] if raw is not None else []

        historical_key = os.getenv("THEODDS_HISTORICAL_API_KEY")
        if historical_key:
            keys.append(historical_key.strip())

        if raw is None:
            keys.append("b94acc93535fc7a76b87b326a1b71f5c")

        return [k for k in keys if k]

    @property
    def api_keys(self) -> list[str]:
        """Ordered list of usable keys: primary first, then fallbacks."""
        keys: list[str] = []
        primary = self.api_key
        if primary:
            keys.append(primary)
        for k in self.fallback_api_keys:
            if k and k not in keys:
                keys.append(k)
        return keys


# ───────────────────────── The Odds API — Historical (Phase 8) ─────────────────────────


@dataclass(frozen=True, slots=True)
class OddsApiHistoricalConfig:
    """Config for https://the-odds-api.com/ ``/v4/historical`` endpoint.

    Each historical call costs ``10 × (regions × markets)`` credits and
    returns **all upcoming events** for the sport at ``date``. With
    ``regions=eu`` + ``markets=h2h`` the cost is 10 credits / call.

    Opt-in via env var ``THEODDS_HISTORICAL_ENABLED=1``.
    """

    base_url: str = "https://api.the-odds-api.com/v4"
    regions: str = "eu"
    markets: str = "h2h"
    odds_format: str = "decimal"
    date_format: str = "iso"
    timeout_seconds: float = 30.0
    request_delay_seconds: float = 1.1  # polite: stays well under free-tier RPS

    # Snapshot timestamps relative to kickoff (hours before).
    # 168h ≈ opening line, 24h ≈ pre-weekend close, 2h ≈ closing.
    snapshot_hours_before: tuple[int, ...] = (168, 24, 2)

    # Budget guard (20 k credits / month @ h2h+eu → 2 k calls).
    monthly_budget_credits: int = 20_000
    # Bail out if this fraction of the monthly budget is consumed by a single run.
    max_credits_per_run: int = 10_000

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
        # Prefer a dedicated key but fall back to the shared ODDS_API_KEY.
        return os.getenv("THEODDS_HISTORICAL_API_KEY") or os.getenv("ODDS_API_KEY") or None

    @property
    def enabled(self) -> bool:
        return os.getenv("THEODDS_HISTORICAL_ENABLED", "0") == "1"

    def credits_per_call(self) -> int:
        """10 × regions × markets per The Odds API pricing."""
        n_regions = len([r for r in self.regions.split(",") if r.strip()])
        n_markets = len([m for m in self.markets.split(",") if m.strip()])
        return 10 * max(1, n_regions) * max(1, n_markets)


# ───────────────────────── Market Microstructure (Phase 8) ─────────────────────────


@dataclass(frozen=True, slots=True)
class MarketMicrostructureConfig:
    """Feature-extractor config for the Family-D ``mm_*`` features.

    Built from persisted historical snapshots under ``data/odds_snapshots/``.
    Features describe odds drift, volatility and sharp/soft divergence
    leading up to kickoff.
    """

    #: Window (hours) around kickoff used for the volatility estimator.
    volatility_window_hours: int = 48
    #: Minimum snapshots required to emit non-neutral features.
    min_snapshots: int = 2
    #: Hard cap: never include snapshots taken after kickoff (leakage guard).
    max_snapshot_age_hours: int = 400


# ───────────────────────── Calibration ─────────────────────────


@dataclass(frozen=True, slots=True)
class CalibrationConfig:
    method: str = "auto"  # "isotonic" | "sigmoid" | "auto" (pick lower val-ECE)
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
    devig_method: Literal["multiplicative", "power", "shin"] = "power"
    #: Extra positive-EV cushion (decimal, e.g. 0.02 → require ≥2 % EV beyond
    #: break-even). Guards against negative closing-line-value: if the line
    #: drifts by 1-2 % between selection and kick-off we still stay in the
    #: green. 0.0 (default) disables the guard to preserve legacy behaviour.
    min_ev_pct: float = 0.0
    #: Minimum lead time (in hours before kickoff) required for an odds
    #: capture to be persisted into the opening-line store. Near-kickoff
    #: captures would pollute the store with closing-line data and collapse
    #: CLV measurement to noise. Default 6h: anything within 6h of kickoff
    #: is treated as "closing-ish" and skipped.
    snapshot_min_lead_hours: float = 6.0


@dataclass(frozen=True, slots=True)
class PredictionStakingConfig:
    """1X2-Prediction staking allocator (see Erweiterungen/Staking-Algorithmen.md)."""

    strategy: Literal["flat", "conf", "power", "hybrid", "entropy"] = "hybrid"
    daily_bankroll: float = 1000.0
    daily_bankroll_pct: float = 0.05
    power_k: float = 2.0
    odds_floor: float = 2.0
    min_p: float = 0.40


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
    """Dirichlet sampler config for k-way ensemble weight tuning.

    ``dirichlet_alpha`` is a prior over the *active* ensemble members, applied
    in order (CatBoost, Poisson, MLP/TabTransformer, Sequence). The tuner
    truncates to the number of active members at runtime, so supplying a
    4-tuple here is safe even when the sequence model is disabled.
    """

    catboost_weights: tuple[float, ...] = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
    dirichlet_samples: int = 500
    # CB, Poisson, MLP/TabTx, Sequence — CatBoost dominates prior, sequence gets
    # moderate prior weight given its stronger capacity vs. the tabular MLP.
    dirichlet_alpha: tuple[float, ...] = (2.0, 1.0, 1.8, 1.5)
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

    # Embedding backend (intfloat/multilingual-e5-large-instruct)
    embedding_model_name: str = "intfloat/multilingual-e5-large-instruct"
    embedding_filename_template: str = "support_emb_{lang}.npz"
    embedding_metrics_filename: str = "support_intent_embedding_metrics.json"
    embedding_batch_size: int = 64
    embedding_score_cutoff: float = 0.78

    # Cross-encoder reranker (BAAI/bge-reranker-base)
    reranker_model_name: str = "BAAI/bge-reranker-base"
    reranker_retrieve_n: int = 20  # candidate rows from bi-encoder
    reranker_batch_size: int = 32

    # Class bundling (hierarchical coarse→fine classification)
    cluster_count: int = 80  # ~268 / 3.4 intents per cluster
    cluster_filename_template: str = "support_clusters_{lang}.npz"
    cluster_top_c: int = 8  # keep top-C clusters at inference time
    cluster_metrics_filename: str = "support_intent_cluster_metrics.json"

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

    # Hierarchical (Pachinko) classifier — chapter → intent
    hierarchical_model_filename_template: str = "support_hier_{lang}.joblib"
    hierarchical_metrics_filename: str = "support_intent_hier_metrics.json"
    topic_top_c: int = 3  # expand leaf heads for top-C chapters
    topic_min_mass: float = 0.90  # stop expanding once cumulative P reaches this

    # Out-Of-Domain handling
    ood_label: str = "__ood__"
    ood_chapter: str = "__ood__"
    ood_topic_threshold: float = 0.5  # P(__ood__) ≥ → reject
    ood_seed_filename_template: str = "ood_seed_{lang}.jsonl"

    # Disambiguation gates (used by API in M4)
    confidence_threshold: float = 0.70
    delta_margin_threshold: float = 0.15

    # Augmentation pipeline (M2) — data escalation to >= 80 utterances / intent
    augmented_v2_filename: str = "dataset_augmented_v2.jsonl"
    augment_stats_v2_filename: str = "augment_stats_v2.json"
    augment_target_per_intent: int = 80
    augment_random_seed: int = 1337

    # LLM-paraphrase augmentation (v3) — qwen2.5:7b-instruct via Ollama
    augmented_v3_filename: str = "dataset_augmented_v3.jsonl"

    # Built-in noise augmenter (no external deps).
    noise_aug_char_p: float = 0.06  # prob. that a char inside a "noised" word is perturbed
    noise_aug_word_p: float = 0.15  # prob. that a word is selected for typo noise
    noise_punct_drop_p: float = 0.5  # prob. of dropping all punctuation in a sentence
    noise_lowercase_p: float = 0.6  # prob. of lowercasing the sentence
    noise_max_variants_per_source: int = (
        6  # hard cap on noise variants spawned from one source utterance
    )

    # Backtranslation (optional; requires transformers + sentencepiece).
    # Pivot language list per source: order matters (first is highest-quality).
    backtranslation_pivots: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("de", ("nl", "fr", "it")),
        ("en", ("fr", "nl", "de")),
        ("fr", ("en", "it", "nl")),
        ("es", ("it", "fr", "en")),
        ("it", ("fr", "es", "en")),
    )

    # ─── Transformer fine-tune (M3) — XLM-R + SupCon hybrid loss ───
    # NOTE: originally ModernGBERT_134M was planned for DE, but its backward
    # pass is not supported on torch-directml 0.2.5 (AMD/Windows) — a DML
    # internal op fails to materialise during gradient computation on AMD
    # W7700. XLM-R-base is used for all languages; it trains end-to-end on
    # DML and remains strong on German (multilingual corpus includes de).
    transformer_model_dirname_template: str = "support_transformer_{lang}"
    transformer_metrics_filename: str = "support_intent_transformer_metrics.json"
    transformer_default_backbone: str = "FacebookAI/xlm-roberta-base"
    transformer_backbone_by_lang: tuple[tuple[str, str], ...] = (
        ("de", "FacebookAI/xlm-roberta-base"),
        ("en", "FacebookAI/xlm-roberta-base"),
        ("es", "FacebookAI/xlm-roberta-base"),
        ("fr", "FacebookAI/xlm-roberta-base"),
        ("it", "FacebookAI/xlm-roberta-base"),
    )
    transformer_max_seq_length: int = 128
    transformer_batch_size: int = 16
    transformer_eval_batch_size: int = 64
    transformer_epochs: int = 4
    transformer_learning_rate: float = 2e-5
    transformer_warmup_ratio: float = 0.1
    transformer_weight_decay: float = 0.01
    transformer_early_stop_patience: int = 2
    # Hybrid loss: total = ce_weight · CE + supcon_weight · SupCon
    supcon_weight: float = 0.3
    ce_weight: float = 1.0
    supcon_temperature: float = 0.07
    # Two-head (chapter + intent) joint classifier:
    #   total = ce_weight·CE_intent + chapter_head_weight·CE_chapter + supcon_weight·SupCon
    # Confusion analysis (v3) showed 95%+ of errors stay within-chapter, so an
    # auxiliary chapter head acts as a strong regulariser that pushes the
    # encoder to first separate chapters cleanly.
    two_head_model_dirname_template: str = "support_twohead_{lang}"
    two_head_metrics_filename: str = "support_intent_twohead_metrics.json"
    chapter_head_weight: float = 0.3
    # At inference: when the chapter head's top-1 prob exceeds this gate, we
    # zero out intent probabilities that do not belong to the predicted chapter
    # before re-normalising. Set to 1.0+ to disable chapter-masked inference.
    # Tuned on DE v3 subsample (cf. models/support/tuning/twohead_sweep_de.csv):
    # 0.7 beats 0.6 / 1.0 at cw=0.3 (winner) and cw=0.5.
    two_head_chapter_gate: float = 0.7
    # ONNX export
    onnx_filename_template: str = "support_transformer_{lang}.onnx"
    onnx_opset: int = 17
    onnx_int8_quantize: bool = True


# ───────────────────────── Defaults ─────────────────────────

PI_CFG = PiRatingsConfig()
FEATURE_CFG = FeatureConfig()
CATBOOST_CFG = CatBoostConfig()
MLP_CFG = MLPConfig()
SEQUENCE_CFG = SequenceConfig()
STACKING_CFG = StackingConfig()
TAB_TRANSFORMER_CFG = TabTransformerConfig()
SOFASCORE_CFG = SofascoreConfig()
WEATHER_CFG = WeatherConfig()
ODDS_API_CFG = OddsApiConfig()
ODDS_API_HISTORICAL_CFG = OddsApiHistoricalConfig()
MARKET_MICROSTRUCTURE_CFG = MarketMicrostructureConfig()
CALIBRATION_CFG = CalibrationConfig()
MONITORING_CFG = MonitoringConfig()
BETTING_CFG = BettingConfig()
PREDICTION_STAKING_CFG = PredictionStakingConfig()
BACKTEST_CFG = BacktestConfig()
ENSEMBLE_TUNE_CFG = EnsembleTuneConfig()
SUPPORT_CFG = SupportConfig()
VALUE_MODEL_CFG = ValueModelConfig()


def should_drop_feature(feature_name: str, cfg: ValueModelConfig = VALUE_MODEL_CFG) -> bool:
    """Return True if ``feature_name`` is on the value-model blocklist."""
    if feature_name in cfg.feature_blocklist_exact:
        return True
    return any(feature_name.startswith(p) for p in cfg.feature_blocklist_prefixes)
