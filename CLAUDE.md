# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python backend

```bash
# Install (full: ML models + API server + dev tools)
pip install -e ".[ml,dev,api]"

# Run tests
pytest                                         # all tests with coverage
pytest tests/test_poisson.py::test_name        # single test
pytest -m "not slow and not gpu"               # skip slow/GPU tests

# Lint + type check
ruff check . && mypy src

# CLI (entrypoint: fb)
fb download --league all                       # fetch football-data.co.uk CSVs
fb train --league BL --use-sofascore           # train CatBoost per league
fb train-mlp --league BL                       # train PyTorch MLP
fb tune-ensemble --league BL --val-season 2024-25
fb backtest --league BL
fb snapshot                                    # build data/snapshots/today.json
fb serve                                       # FastAPI at http://localhost:8000
fb predict --fixtures data/fixtures_*.json --bankroll 1000
fb monitor --league BL --recent-days 30        # feature drift report
fb export-onnx --league BL
```

### Frontend (run from `web/`)

```bash
npm install
cp .env.local.example .env.local
npm run dev          # http://localhost:3000
npm run build
npm run lint
npm run type-check
```

### VS Code shortcut

`Ctrl+Shift+P → Tasks: Run Task → dev: all` starts FastAPI + Next.js in parallel.

## Architecture

### Overview

This is a football betting prediction platform with three layers:
1. **Python ML backend** (`src/football_betting/`) — data pipeline, feature engineering, model training
2. **FastAPI server** (`src/football_betting/api/`) — serves pre-computed snapshots to the frontend
3. **Next.js 14 frontend** (`web/`) — public UI + internal owner dashboard

Data flows: raw CSVs + odds API → features → ensemble predictions → `data/snapshots/today.json` → FastAPI → Next.js.

### Python package (`src/football_betting/`)

Installed as `football_betting`, exposed via the `fb` CLI (`cli.py`). Layers are decoupled:

- **`config.py`** — central frozen dataclass configs for every subsystem (model hyperparams, feature flags, league definitions). All league keys are `PL`, `CH`, `BL`, `SA`, `LL`. Instantiated singletons at bottom of file (`FEATURE_CFG`, `BETTING_CFG`, etc.).
- **`data/`** — CSV downloader (football-data.co.uk), `Match`/`Fixture`/`MatchOdds` Pydantic models, odds snapshot persistence.
- **`rating/pi_ratings.py`** — Pi-Ratings (Constantinou & Fenton 2013).
- **`features/builder.py`** — orchestrates all 70+ features; `FeatureBuilder` is the single entry point for feature matrix construction.
- **`predict/`** — four ensemble members: `CatBoostPredictor`, `PoissonModel` (Dixon-Coles), `MLPPredictor` (PyTorch), `SequencePredictor` (1D-CNN + Transformer). `ensemble.py` blends them with Dirichlet-tuned weights. `runtime.py` owns model loading and `LeagueModelProfile` persistence (`models/model_profile_{league}.json`).
- **`betting/`** — Kelly sizing, devig (multiplicative/power/shin), value-bet detection.
- **`tracking/`** — walk-forward backtest, RPS/Brier/CLV/Sharpe metrics, KS-test drift monitoring.
- **`support/`** — FAQ chatbot intent classifier: TF-IDF + LR baseline, XLM-R two-head transformer (chapter + intent heads) fine-tuned per locale, ONNX export, OOD detection.
- **`scraping/`** — opt-in Sofascore async client with SQLite TTL cache; Zulubet tip scraper. Never call without `SCRAPING_ENABLED=1`.
- **`seo/`** — track-record data for SEO pages, tipster export.

### Dual-model system

Every model artefact exists in two variants distinguished by a filename suffix:
- `1x2` purpose → no suffix (e.g. `catboost_PL.cbm`, `ensemble_weights_PL.json`)
- `value` purpose → `_value` suffix (e.g. `catboost_PL_value.cbm`, `ensemble_weights_PL_value.json`)

The value model **drops** all `market_*` and `mm_*` features (see `ValueModelConfig.feature_blocklist_prefixes`) to avoid learning the market consensus it needs to beat. Use `config.should_drop_feature()` to check blocklist membership.

### FastAPI (`src/football_betting/api/`)

- `app.py` creates the FastAPI app, seeds CSVs on startup if `/data/raw/` is empty, and launches the async scheduler.
- `routes.py` — all public REST endpoints (`/health`, `/leagues`, `/predictions/today`, `/leagues/{key}/ratings`, `/performance/summary`, `/support/ask`, etc.).
- `scheduler.py` — in-process async loop that refreshes `today.json` at configured UTC hours and runs a 2-min live-score settlement loop.
- `support_service.py` — single-slot LRU cache for the two-head XLM-R classifier (one model in RAM at a time, ~1.1 GB per language).
- `snapshots.py` — reads/writes `data/snapshots/today.json`; `data/snapshots/odds_{league}.jsonl` for per-league odds movement.

### Next.js frontend (`web/`)

- **App Router** with a mandatory `[locale]` prefix (`/en/`, `/de/`, `/es/`, `/fr/`, `/it/`). Middleware (`middleware.ts`) handles locale detection, cookie pinning, HTTPS upgrades, and `www.` redirect.
- **`web/lib/types.ts`** mirrors all FastAPI Pydantic schemas — keep them in sync when adding fields.
- **`web/lib/server-api.ts`** is the SSR fetch layer; uses `API_INTERNAL_URL` env var when set (Railway private networking), otherwise falls back to `NEXT_PUBLIC_API_URL`.
- **Admin dashboard** lives at `/admin/*` and is only reachable on the `INTERNAL_HOST` hostname (Cloudflare Access / Zero Trust in production). In local dev, set `DEV_INTERNAL=1` to access `/admin` on the same port.
- i18n strings are in `web/lib/i18n/{en,de,es,fr,it}.ts`.

### Deployment

- **Docker** (`Dockerfile`) — Python 3.12 slim, installs `.[api]` only, runs `uvicorn football_betting.api.app:create_app --factory`.
- **Railway** (`railway.toml`) — uses Dockerfile, runs `python scripts/bootstrap_data.py` as pre-deploy command, healthcheck at `/health`.
- The frontend is deployed separately (Vercel or Railway). Required production env vars: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_URL`.

## Key conventions

- **Python**: 3.11+, 4-space indent, `ruff` (line-length 100, rules `E,F,W,I,N,UP,B,C4,SIM`, `E501` ignored), `mypy --strict`.
- **Pytest markers**: `slow` (>5s), `gpu` (CUDA), `dml` (torch-directml AMD/Windows) — deselect with `-m "not slow and not gpu"`.
- **League keys** are always short uppercase: `PL`, `CH`, `BL`, `SA`, `LL`.
- **Model artefacts** follow `{model_type}_{league_key}[_value].{ext}` under `models/`. `_value` suffix = value-bet variant.
- **Scraping** is always opt-in: check `SCRAPING_ENABLED=1` before any Sofascore or Zulubet calls. The Sofascore client rate-limits to 25 s/request.
- **Odds API key**: `ODDS_API_KEY` env var; fallbacks via `ODDS_API_FALLBACK_KEYS` (comma-separated).
- **Frontend types**: `web/lib/types.ts` must mirror `src/football_betting/api/schemas.py` — update both when changing the API contract.
- Commit subject lines use area prefixes: `features:`, `api:`, `web:`, `train:`, etc.
