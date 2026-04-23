# Plan — Full GPU Retrain + End-to-End Validation After Familie B/C + Standings

**Context.** The feature schema expanded from 94 → **118 features** (Standings 17 + Weather Familie A 9 + Familie B 5 + Familie C 3). All persisted `models/catboost_{LEAGUE}.cbm`, `models/mlp_{LEAGUE}.pt`, `models/sequence_{LEAGUE}.pt`, `models/tabtransformer_{LEAGUE}.pt`, `models/ensemble_weights_{LEAGUE}.json` still use the old schema. A full retrain on GPU is the next logical step to exploit the new signals.

---

## Objective

Retrain the complete stack (CatBoost on GPU, PyTorch MLP/Sequence/FT-Transformer on CUDA) for the 5 target leagues, re-tune ensemble weights + CLV-Dirichlet + EV-cushion per league, then run a walk-forward backtest on 2024-25 to measure the incremental lift from the 25 new features (Standings + Weather B/C).

## Target leagues

`BL, PL, SA, LL, CH` (same scope as prior multi-league test run).

---

## Step-by-step Execution

| # | Command | Notes |
|---|---------|-------|
| 1 | `set FB_TORCH_DEVICE=cuda` (cmd) or `$env:FB_TORCH_DEVICE="cuda"` (PS) | Force CUDA for PyTorch models. Fallback = CPU. |
| 2 | `fb download --league all` | Refresh Football-Data CSVs (idempotent; fast). |
| 3 | `fb train --league BL --use-sofascore --calibrate` *(repeat for PL, SA, LL, CH)* | CatBoost GPU (`task_type=GPU`) + MLP/Sequence/TabTransformer CUDA + isotonic calibration. |
| 4 | `fb tune-ensemble --league <L> --val-season 2024-25 --objective blended --use-sequence --save` | Re-tune ensemble weights + CLV-Dirichlet per league; persists to `models/ensemble_weights_<L>.json`. |
| 5 | `fb calibration-audit --league <L> --n-bins 10` | Re-check ECE per league; apply sigmoid override where LL/CH still show under-confidence (keep prior `--calibration-method sigmoid` flag for LL). |
| 6 | `fb sweep-cushion --league <L> --cushions 0.00,0.05,0.08,0.10,0.12,0.15 --bankroll 1000 --stacking` | Pick the `min_ev_pct` cushion that maximises bankroll on 2024-25 holdout. |
| 7 | `fb backtest --league <L> --walk-forward --stacking --folds-auto --sliding --calibration-method <sigmoid\|isotonic>` | 2024-25 walk-forward; record ROI, CLV, RPS, Brier, bankroll. |
| 8 | Aggregate per-league metrics into a summary table (RPS Δ, ECE Δ, CLV Δ, ROI Δ vs. pre-retrain baseline from commit `91f5e7d3`). |

All steps are `cd /d c:\Users\Marcel\source\repos\BettingwithAI && …`.

## Critical files referenced (no edits expected during retrain)

- `src/football_betting/cli.py:348` — `fb train` entrypoint
- `src/football_betting/predict/catboost_model.py:157` — `task_type=GPU`
- `src/football_betting/predict/gpu_utils.py` — `resolve_device`, `detect_gpu`, `make_amp_scaler`
- `src/football_betting/predict/mlp_model.py:157` — CUDA `.to(device)`
- `src/football_betting/predict/sequence_model.py:191` — CUDA `.to(device)`
- `scripts/train.py` — reference multi-league orchestration (hard-coded seasons 2021-22 … 2024-25)
- `models/*.cbm`, `models/*.pt`, `models/ensemble_weights_*.json` — artifacts to be overwritten

## Potential risks & mitigations

1. **CatBoost GPU quirk** — requires `bootstrap_type="Bayesian"`; already enforced in `CatBoostConfig` when `use_gpu=True`. No change needed.
2. **DirectML on non-NVIDIA** — if CUDA unavailable, PyTorch falls back to DirectML (no pinned memory → slightly slower). Acceptable.
3. **Feature-schema drift** — older `.cbm` files become stale. `fb train` writes a fresh `.features.txt` per model; downstream `fb tune-ensemble` and `fb backtest` re-read it. Safe.
4. **Paris Familie-C API quota** — Open-Meteo allows 10k req/day; a full retrain hits ~2k Paris-day cache lookups. Cache (`data/weather/cache.sqlite`) is persistent across runs — no repeated hits.
5. **Runtime estimate** — CatBoost GPU ~5 min/league × 5 = 25 min; PyTorch MLP/Sequence/FT-Transformer ~3–8 min/league × 5 × 3 = 60 min; tune-ensemble + backtest + sweep ~15 min/league × 5 = 75 min. **Total ~3 h wall-clock** on a single CUDA GPU.

## Verification

1. `python -m pytest tests/test_weather.py tests/test_standings.py tests/test_features.py --no-cov -q` — sanity check feature schema (must stay 118 features).
2. Per league, after step 3 inspect `models/catboost_<L>.features.txt` — confirm the file lists 118 entries and contains `standings_*`, `weather_shock_*`, `simons_paris_*`.
3. After step 7, the walk-forward backtest JSON under `results/backtest_<L>_2024-25.json` must report finite numbers for `rps`, `brier`, `clv_pct`, `roi_pct`, `bankroll_end`.
4. Compare to the pre-Familie-B/C baseline (commit `91f5e7d3`): expect LL ECE ≤ 0.033 improved, CH ECE ≤ 0.0175 improved, BL RPS roughly flat or better. SA should remain profitable (prior +2.18% ROI).
5. If any league regresses >1pp ROI vs. baseline, ablate Familie B and C independently via `WeatherConfig(use_weather_shock=False, use_simons_signal=True)` etc. to isolate which family hurt — do not ship the regression.

## Success criteria

- All 5 leagues retrain end-to-end without crashes.
- At least 2 leagues show ECE reduction ≥ 5% relative to `91f5e7d3` baseline.
- Ensemble CLV does not regress on BL/SA.
- Familie C (Simons) shows |β| ≈ 0 as expected — if it unexpectedly dominates, flag for ablation (likely leakage/overfit, not a real signal).

## Follow-ups (NOT part of this plan)

- Hybrid-stacking Phase 7 re-tune on the 118-feature schema.
- `fb snapshot && fb serve` for API layer (only after backtest validates).
- Optional CHANGELOG / version bump in `pyproject.toml` — only if user requests.
