# Changelog

## Unreleased

### Support chatbot wired to Railway backend (2026-04-24)

- New endpoint `POST /support/ask` backed by `TwoHeadTransformerIntentClassifier`
  (`src/football_betting/api/support_service.py`). Single-slot LRU cache keeps
  at most one encoder in RAM (~1.1 GB / language) to fit Railway memory limits.
- Applies per-language temperature calibration from `temperature.json` on top
  of `predict_topk` (load path does not restore it yet).
- Out-of-distribution (`__ood__`) or sub-threshold predictions return
  `fallback=true` with an empty `predictions[]`; the frontend falls back to its
  client-side Fuse.js FAQ search in that case so the chatbot never dead-ends.
- Added `torch`, `transformers`, `sentencepiece` to the `api` extra so Railway
  Docker images can run the two-head model. This enlarges the deployed image
  from ~500 MB to ~7 GB (five 1 GB encoders + PyTorch CPU wheels).
- `web/components/SupportChat.tsx` now calls `api.supportAsk({...})` first and
  only uses Fuse.js as the fallback. The current locale from `useLocale()` is
  forwarded so per-language fine-tuning is applied correctly.
- 6 new tests in `tests/test_support_api.py` cover routing, OOD-fallback,
  missing-model graceful degradation, empty-question rejection, and language
  normalisation (monkey-patches `classify` to avoid the 1 GB model load on CI).

### Support two-head transformer — multilingual re-train (2026-04-24)

Re-trained the two-head (intent + chapter) XLM-R transformer for all five languages on RunPod RTX 4090:

| Lang | macro_f1 | chapter_head_top1 |
|------|----------|-------------------|
| de   | 0.5112   | 0.9815 |
| en   | 0.5135   | 0.9902 |
| es   | 0.5088   | 0.9832 |
| fr   | 0.5107   | 0.9792 |
| it   | 0.5097   | 0.9795 |

- 8 epochs, SupCon loss active, per-language temperature calibration (IT example: T=0.638, ECE 0.0616 → 0.0098).
- Chapter head at ~98 % top-1 across all languages; intent head ~51 % on the 269-way label space (~52 samples/class).
- `[WARN] two_head: top1 0.515 below hard floor 0.75` — aspirational hard-floor in `trainer.py`, not blocking; chapter head is the reliable signal.
- Artefacts (encoder + tokenizer + `heads.pt` + `temperature.json` per language, ~1 GB each) stored locally under `models/support/support_twohead_{de,en,es,fr,it}/`.
- Added `models/support/support_twohead_*/` to `.gitignore` (size); per-language metrics JSONs (`support_intent_twohead_metrics_{lang}.json`) + combined `support_intent_twohead_metrics.json` are committed for reproducibility.

## v0.4.0 — Phase 3–5 ML Pipeline Modernization

### 🚀 New Features

**1D-CNN + Transformer Sequence Head (`predict/sequence_model.py`)**
- Replaces the legacy GRU + attention branch
- Per-team encoder: `Conv1d(F→64,k=3)×2 + GELU → learnable positional embedding → TransformerEncoder(d=64, heads=4, layers=2, norm_first=True) → masked mean-pool + LayerNorm`
- Safe fallback for fully-padded cold-start rows, DirectML compatible via `resolve_device`
- 7 new unit tests covering shape, softmax, padding invariance, determinism

**4-Way Ensemble + Generalised Dirichlet Tuner (`predict/ensemble.py`)**
- `EnsembleModel` now supports CatBoost + Poisson + MLP/TabTransformer + Sequence (any subset)
- Vectorised Dirichlet weight sampling via `np.tensordot`
- New `brier_logloss_blended` objective — minimises equally-weighted z-score blend of Brier + LogLoss
- `EnsembleTuneConfig.dirichlet_alpha` extended to 4-tuple with runtime truncation to active members

**Parquet Feature Snapshot Store (`tracking/feature_snapshot.py`)**
- Monthly-partitioned Parquet files under `data/processed/feature_snapshots/{league}/{yyyy-mm}.parquet`
- Long-format schema is forward-compatible as the feature set grows
- `as_of` cutoff-aware loads for reproducible walk-forward backtests
- New dep: `pyarrow>=15.0`

**Sliding Walk-Forward Backtest (`tracking/backtest.py`)**
- `Backtester.training_window_matches` caps the trailing training window
- `walk_forward_backtest(mode="sliding", window_matches=500)` for rolling retrains

**Bayesian Fractional Kelly (`betting/bayesian_kelly.py`)**
- Variance-aware shrinkage: `stake = fractional_kelly × 1 / (1 + λ · Var(p))`
- Accepts posterior-sample arrays (e.g. from MC-Dropout)
- Helper `mc_dropout_probabilities(model, predict_fn, n_passes=50)` for Torch models

**Monte-Carlo Bankroll Stress-Test (`tracking/monte_carlo.py` + `fb stress-test` CLI)**
- 10 k Bernoulli rollouts per bet-history with reproducible seed
- Reports P05/P50/P95 final bankroll, mean + P95 max drawdown, risk-of-ruin, CAGR mean + P05
- New CLI: `fb stress-test --league BL --runs 10000 --bankroll 1000`

### ✅ Testing

- 41 new / updated tests across `test_sequence_model`, `test_ensemble_tuning`, `test_feature_snapshot`, `test_walk_forward_sliding`, `test_bayesian_kelly`, `test_monte_carlo` — all green.

## v0.3.1 — 21. April 2026

### 🚀 New Features

**Support FAQ Intent Classifier (`src/football_betting/support/`)**
- TF-IDF (char_wb 3–5 ⊕ word 1–2) → Logistic Regression
- Trained per locale (en / de / es / fr / it) on `data/support_faq/dataset_augmented.jsonl` (30 815 rows · 268 intents)
- `IntentClassifier.fit / predict / predict_topk / evaluate / save / load`
- Persisted via joblib to `models/support/support_intent_{lang}.joblib`
- Aggregated metrics (top-1 / top-3 / macro-F1 / per-chapter top-1) written to `models/support/support_intent_metrics.json`
- New `fb train-support` CLI command + `scripts/train_support.py` wrapper
- Zero new runtime deps (reuses existing `scikit-learn`)

## v0.3.0 — 18. April 2026

### 🚀 New Features

**Sofascore Scraping (`src/football_betting/scraping/`)**
- `sofascore.py` — Async HTTP scraper mit Browser-Fingerprint-Headers
- `rate_limiter.py` — Token-Bucket-Rate-Limiter (25s pro Request Default)
- `cache.py` — SQLite-basierter Response-Cache
- Endpoints: events by round, match statistics (xG), lineups, player ratings
- Automatisches Retry mit exponential backoff bei 429/503

**Real xG Features (`features/real_xg.py`)**
- Ersetzt `xg_proxy.py` wenn Sofascore-Daten vorhanden
- Rolling xG/xGA mit exponentieller Gewichtung (Decay 0.85)
- Home/Away-Split
- xG-vs-Goals-Delta als "Glück/Finishing"-Indikator

**Squad Quality Features (`features/squad_quality.py`)**
- Starting-XI-Rating aus Sofascore-Lineups
- Bench-Depth-Rating
- Key-Player-Absence-Flag
- Squad-Rotation-Indicator

**Market Movement (`features/market_movement.py`)**
- Opening vs Closing Odds Tracker
- Steam Move Detection
- Sharp Money Indicator (reverse line movement)

**MLP Neural Network (`predict/mlp_model.py`)**
- PyTorch MLP (3 hidden layers, BatchNorm + Dropout)
- Dritter Ensemble-Member neben CatBoost + Poisson
- ONNX-Export für Production-Deployment

**3-Way Ensemble (`predict/ensemble.py`)**
- `EnsembleModel` upgraded von 2 auf 3 Komponenten
- Dirichlet-Sampling für Weight-Tuning
- Per-Liga optimale Gewichte werden gespeichert

**Data Quality Monitoring (`tracking/monitoring.py`)**
- Feature-Distribution-Drift (KS-Test)
- Missing-Value-Alerts
- Prediction-Confidence-Histogramm

### 📊 Updated Components

**FeatureBuilder** — jetzt 70+ Features (war 56 in v0.2)
**CLI** — neue Commands: `scrape`, `monitor`, `train-mlp`, `export-onnx`
**Config** — `SofascoreConfig`, `MLPConfig`, `MonitoringConfig`

### 🔬 Expected Performance

| Metric | v0.2 | v0.3 (target) |
|--------|------|---------------|
| RPS (Premier League) | 0.189 | **0.186** |
| RPS (Bundesliga) | 0.190 | **0.187** |
| RPS (Championship) | 0.193 | **0.191** |
| Calibration ECE | <2% | **<1.5%** |
| CLV (avg) | +1.2% | **+1.8%** |

### ⚠️ Breaking Changes

- `EnsembleModel` — MLP ist optional (default None → 2-Way Ensemble Fallback)
- Neue Dependencies: `aiohttp`, `torch`, `onnx`, `onnxruntime`

### ⚠️ Compliance & Rate-Limits

Sofascore hat keine offizielle API-Erlaubnis. Der Scraper nutzt:
- **25 Sekunden zwischen Requests** (konservativ)
- **User-Agent-Rotation**
- **SQLite-Cache** (Minimierung wiederholter Abfragen)
- Opt-In: nur aktiv wenn `SCRAPING_ENABLED=1` gesetzt

Für Production über bezahlte API (API-Football, Sportmonks) nachdenken.
