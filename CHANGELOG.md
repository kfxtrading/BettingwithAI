# Changelog

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
