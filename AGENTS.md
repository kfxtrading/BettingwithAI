# Repository Guidelines

## Project Structure & Module Organization

Python package lives under `src/football_betting/` (installed editable as `football_betting`). Pipeline flows through decoupled layers:

- `data/` — CSV downloader, `Match`/`Fixture` models, odds snapshots.
- `rating/pi_ratings.py` + `features/` — Pi-Ratings then 70+ engineered features orchestrated by `features/builder.py`.
- `scraping/` — opt-in Sofascore async client with SQLite TTL cache and token-bucket rate limiter (25s/request).
- `predict/` — Dixon-Coles Poisson, CatBoost, PyTorch MLP, isotonic/Platt calibration, Dirichlet-tuned 3-way ensemble.
- `betting/` — Kelly sizing, margin removal, value-bet detection.
- `tracking/` — walk-forward backtest, RPS/Brier/CLV metrics, KS-test drift monitoring.
- `api/` — FastAPI app (`app.py`, `routes.py`, `services.py`, `schemas.py`) serving snapshot JSON from `data/snapshots/`.
- `cli.py` — single Click entrypoint wiring all 12 subcommands (`fb ...`).

`scripts/` holds thin wrappers (`train.py`, `backtest.py`, `predict_today.py`, `tune_ensemble.py`, `scrape_sofascore.py`). The Next.js 14 App-Router frontend is in `web/` (`app/`, `components/`, `lib/`), consuming the FastAPI backend.

## Build, Test, and Development Commands

```bash
pip install -e ".[ml,dev,api]"   # full install (torch, onnx, fastapi, pytest, ruff, mypy)
fb download --league all          # fetch Football-Data CSVs
fb train --league BL --use-sofascore
fb tune-ensemble --league BL --val-season 2024-25
fb backtest --league BL
fb snapshot && fb serve           # build today.json, start FastAPI at :8000
pytest                            # runs with -v --cov (configured in pyproject)
pytest tests/test_poisson.py::test_name   # single test
ruff check . && mypy src          # lint + strict type-check
```

Frontend (`cd web`): `npm install`, `npm run dev`, `npm run build`, `npm run lint`, `npm run type-check`.

VS Code task **dev: all** (or **dev: full bootstrap** on first run) starts API + Next.js in parallel.

## Coding Style & Naming Conventions

- Python 3.11, 4-space indent, `ruff` (line-length 100; rules `E,F,W,I,N,UP,B,C4,SIM`; `E501` ignored).
- `mypy` runs in **strict** mode with `ignore_missing_imports = true` — add precise type hints to new code.
- Package layout uses `snake_case` modules; Pydantic models and classes use `PascalCase`; CLI subcommands are kebab-case (`fb tune-ensemble`).
- Frontend: TypeScript + Tailwind; ESLint via `next lint` (`eslint-config-next`).
- Scraping is **opt-in**: never call Sofascore without `SCRAPING_ENABLED=1`.

## Testing Guidelines

- Framework: `pytest` with `pytest-cov`. Tests under `tests/` follow `test_<module>.py`; target ~80+ tests covering features, calibration, betting, scraping, monitoring.
- Coverage report prints to terminal (`--cov=football_betting --cov-report=term-missing`).
- Match accuracy targets: RPS per league per `README.md` table; ECE < 1.5% after calibration.

## Commit & Pull Request Guidelines

Git history is minimal (single initial commit). Use concise, imperative subject lines; if scope is useful, prefix with area (`features:`, `api:`, `web:`). Group related changes per commit, reference CHANGELOG entries when bumping the package version in `pyproject.toml`.
