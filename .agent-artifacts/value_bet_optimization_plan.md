# Value-Bet Profitability Optimization Plan

Basis: SOTA-Report 2026 (Power-Devig, CLV-Tuning, Time-Decay, Walk-Forward) abgeglichen mit IST-Stand des Repos.

## Identifizierte Lücken (verifiziert)

| # | Befund | Datei:Zeile |
|---|--------|-------------|
| 1 | Naive proportionale Devigging-Methode (Multiplicative); Kommentar nennt Shin/Power "overkill" — laut Report falsch | `src/football_betting/betting/margin.py:5-19` |
| 2 | Edge = `model_p − market_p`, keine Favorite-Longshot-Bias-Korrektur | `src/football_betting/betting/value.py:96,106` |
| 3 | CatBoost-Training ohne `sample_weight` → 2021-22 gleich gewichtet wie 2024-25 | `src/football_betting/predict/catboost_model.py` |
| 4 | CLV-Funktionen vorhanden, im Backtest aber **nicht aufgerufen** | `tracking/metrics.py:62-82` vs. `tracking/backtest.py:94-232` |
| 5 | Bet-Odds == Closing-Odds (`m.odds`) → CLV degeneriert zu 0 (keine Opening-Snapshots) | `data/loader.py:30-35` (PSH = Pinnacle-Closing) |
| 6 | Heimvorteil dynamisch, aber keine COVID-Ghost-Games-Korrektur | `features/home_advantage.py` |
| 7 | Backtest = single-Test-Saison; kein Multi-Fold Walk-Forward | `tracking/backtest.py:94-100` |
| 8 | Ensemble-Tuning ausschließlich auf RPS, CLV als Ziel ungenutzt | `scripts/tune_ensemble.py`, `predict/ensemble.py` |

## Reihenfolge & Hebel

| Phase | LoC | Dauer | ROI-Hebel | Risiko |
|-------|-----|-------|-----------|--------|
| 1 Power-Devig | ~120 | 0.5 d | **Hoch** (±1–2 % ROI direkt) | Low |
| 2 Time-Decay-Weights | ~150 | 0.5 d | Mittel-hoch | Low |
| 3 CLV-Pipe im Backtest | ~200 | 1 d | Fundament für 6 | Low |
| 5 COVID-Ghost-Games | ~100 | 0.3 d | Niedrig-mittel | Low |
| 4 Closing-Snapshots | ~500 | 2–3 d | **Sehr hoch** (entsperrt 6) | Mittel |
| 6 CLV-Ensemble + Walk-Forward | ~400 | 2 d | **Höchster langfristig** | Mittel |

**Empfohlene Implementierungs-Reihenfolge:** 1 → 2 → 3 → 5 → 4 → 6.

---

## Phase 1 — Power-Devigging (Quick Win, höchster Hebel)

**Datei:** `src/football_betting/betting/margin.py`

**Neue Signaturen:**
```python
def remove_margin(
    odds_home: float, odds_draw: float, odds_away: float,
    method: Literal["multiplicative","power","shin"] = "power",
) -> tuple[float, float, float]
def _power_devig(probs, tol=1e-9, max_iter=50) -> tuple[float, ...]
def _shin_devig(probs) -> tuple[float, ...]   # optional
```

Newton-Raphson auf `f(k) = Σ π_i^(1/k) − 1`, Startwert `k=1.0`. Multiplicative bleibt als Fallback.

**Config:** `BettingConfig.devig_method: Literal["multiplicative","power","shin"] = "power"` in `config.py:314`.

**Call-Sites umstellen:**
- `betting/value.py:96` → `remove_margin(oh, od, oa, method=cfg.devig_method)`
- `tracking/backtest.py:161` → analog

**Tests:** `tests/test_margin.py` erweitern
- `test_power_devig_sums_to_one` (1e-9 Toleranz)
- `test_power_reduces_favorite_longshot_bias` (synthetisch: 1.30 vs. 15.0)
- `test_power_converges_in_finite_iter`
- `test_devig_method_switch_via_config`

**Verifikation:**
```bash
pytest tests/test_margin.py -v
fb backtest --league BL --devig-method power
ruff check src/football_betting/betting/margin.py && mypy src
```

---

## Phase 2 — Time-Decay Sample Weights

**Neue Datei:** `src/football_betting/predict/weights.py`
```python
def season_decay_weights(
    seasons: Sequence[str], ref_season: str, decay: float = 0.85
) -> np.ndarray:
    """Inverse-distance: w_s = decay**(ref_idx − s_idx); clipped to [0.1, 1.0]."""
```

Erwartung: `2021-22→0.40, 2022-23→0.55, 2023-24→0.75, 2024-25→1.0` (decay=0.85).

**Datei:** `src/football_betting/predict/catboost_model.py`
```python
def fit(self, matches, ..., time_decay: float | None = 0.85):
    seasons = np.array([m.season for m in train])
    sw = season_decay_weights(seasons, ref_season=seasons.max(), decay=time_decay) if time_decay else None
    self._model.fit(X, y, sample_weight=sw, ...)
```

**Optional:** MLP — gewichteter `nn.CrossEntropyLoss(reduction="none")` × `sw`.

**Config:** `CatBoostConfig.time_decay: float = 0.85`.

**Tests:** `tests/test_weights.py` (neu)
- `test_weights_monotonic_in_recency`
- `test_ref_season_weight_is_one`
- `test_catboost_accepts_sample_weight` (Smoke: RPS auf Holdout ≤ Baseline + 0.005)

**Verifikation:**
```bash
fb train --league BL --time-decay 0.85
pytest tests/test_weights.py -v
```

---

## Phase 3 — CLV-Metrik im Backtest aktivieren

**Datei:** `src/football_betting/tracking/backtest.py:94-232`

Erweitere `bet_records` um `bet_odds_at_placement` und `closing_odds`. In Phase 3 sind beide identisch (`m.odds`) → CLV ≡ 0, aber Pipeline funktional. Phase 4 füllt mit echten Snapshots.

**Erweiterung `BacktestResult`:**
```python
metrics["clv_mean"] = clv_summary(bet_odds, close_odds)["mean_clv"]
metrics["clv_pct_positive"] = clv_summary(...)["pct_positive"]
```

**Robustheit:** `clv_summary` muss `None`-Closing-Odds tolerieren (skip statt crash).

**Tests:** `tests/test_backtest_clv.py` (neu)
- `test_clv_zero_when_bet_equals_closing`
- `test_clv_positive_when_bet_odds_higher`
- `test_clv_summary_in_result_dict`

**Verifikation:**
```bash
pytest tests/test_backtest_clv.py tests/test_metrics.py -v
fb backtest --league BL  # CLV-Spalten im Report
```

---

## Phase 5 — COVID-Ghost-Games-Korrektur (vorgezogen wegen Aufwand)

**Datei:** `src/football_betting/features/home_advantage.py`

```python
GHOST_PERIODS = [(date(2020, 3, 1), date(2021, 6, 30)),
                 (date(2021, 8, 1), date(2021, 12, 31))]

def dynamic_home_advantage(match_date: date, base: float,
                           ghost_factor: float = 0.35) -> float:
    return base * ghost_factor if any(s <= match_date <= e for s, e in GHOST_PERIODS) else base
```

**Integration:** in `HomeAdvantageTracker.team_home_advantage()` und Dixon-Coles-Aufruf einhängen.

**Config:** `FeatureConfig.ghost_factor: float = 0.35`, `FeatureConfig.ghost_periods` (Default oben).

**Tests:** `tests/test_home_advantage.py` erweitern
- `test_ghost_period_reduces_home_advantage`
- `test_non_ghost_date_unchanged`
- `test_ghost_boundary_inclusive_exclusive`

**Verifikation:**
```bash
pytest tests/test_home_advantage.py -v
fb backtest --league BL  # RPS auf 2021-22 sollte sinken
```

---

## Phase 4 — Closing-Line-Snapshots

**Ziel:** Echte Opening→Closing-Spreizung damit CLV nicht degeneriert.

**Schema-Erweiterung:** `data/models.py`
```python
class Match(BaseModel):
    ...
    odds: MatchOdds | None              # = closing (football-data PSH)
    opening_odds: MatchOdds | None = None   # T-48h Snapshot
```

**Neue Datei:** `src/football_betting/data/snapshot_service.py`
```python
def capture_odds_snapshot(fixtures, t_minus_hours: int, source: str) -> list[OddsSnapshot]
def merge_snapshots_into_matches(matches, opening_window="T-48h") -> list[Match]
```

`odds_snapshots.py`-Schema bereits da → nur Loader/Merger ergänzen.

**Quellen-Strategie (Fallback-Kette):**
1. Sofascore-Pre-Match-Odds (hinter `SCRAPING_ENABLED=1`)
2. The-Odds-API Pre-Match (`ODDS_API_KEY`)
3. Proxy: `B365H` als Opening, `PSH` als Closing (best-effort)

**CLI:** `fb snapshot-odds --league BL --t-minus 48`

**Backtest-Anpassung:** `bet_odds = m.opening_odds or m.odds`, `closing_odds = m.odds`.

**Tests:** `tests/test_snapshots.py` (neu)
- `test_snapshot_schema_roundtrip_sqlite`
- `test_merge_falls_back_to_closing_when_opening_missing`
- `test_clv_nondegenerate_with_real_snapshots`

**Verifikation:**
```bash
SCRAPING_ENABLED=1 fb snapshot-odds --league BL --t-minus 48
pytest tests/test_snapshots.py -v
fb backtest --league BL  # CLV-Mean sollte ≠ 0 sein
```

---

## Phase 6 — Ensemble-Tuning auf CLV + Multi-Season Walk-Forward

**Datei:** `src/football_betting/predict/ensemble.py` + `scripts/tune_ensemble.py`

```python
def tune_dirichlet(val_probs, val_y, val_odds, val_closing,
                   objective: Literal["rps","clv","blended"] = "blended",
                   blend: float = 0.5) -> DirichletWeights
```

`blended = 0.5 * z(−rps) + 0.5 * z(clv_mean)` (z-normalisiert über Sample-Pool).

**Walk-Forward-Schema** in `tracking/backtest.py`:
```python
def walk_forward_backtest(league, train_windows, test_seasons) -> list[BacktestResult]
```

| Fold | Train | Test |
|------|-------|------|
| 1 | 2019-22 | 2022-23 |
| 2 | 2020-23 | 2023-24 |
| 3 | 2021-24 | 2024-25 |

Aggregiere mean/std von CLV, ROI, RPS über Folds.

**Tests:** `tests/test_ensemble_tuning.py`, `tests/test_walk_forward.py` (beide neu)
- `test_tune_objective_clv_picks_different_weights_than_rps`
- `test_blended_objective_monotone_in_blend_parameter`
- `test_walk_forward_yields_n_folds`
- `test_walk_forward_no_train_test_leakage` (Datum-Assertion: `max(train_date) < min(test_date)`)

**Verifikation:**
```bash
fb tune-ensemble --league BL --objective blended
fb backtest --league BL --walk-forward
pytest tests/test_ensemble_tuning.py tests/test_walk_forward.py -v
ruff check src && mypy src
```

---

## Globale Backward-Compat-Strategie

| Mechanismus | Anwendung |
|---|---|
| Config-Default-Wechsel | `devig_method=power`, `time_decay=0.85`, `ghost_factor=0.35` |
| CLI/Env-Flag | `--devig-method`, `--no-time-decay`, `SCRAPING_ENABLED` |
| Graceful-None | `opening_odds`, `clv_*` → `None` statt Crash |
| Dual-Path | Tuning-Objective `rps` weiterhin selektierbar (Reproduzierbarkeit Baseline) |

## Erwarteter Profitability-Gain (kumuliert)

| Stand | Erwartete Verbesserung vs. Baseline |
|-------|--------------------------------------|
| Phase 1 | +1–2 % ROI (korrekte Edge) |
| Phase 1+2 | +1.5–3 % ROI, RPS −0.003 |
| Phase 1+2+3+5 | +2–4 % ROI, ECE −0.5 % |
| Alle 6 Phasen | +3–6 % ROI, CLV-Mean > 0, robuste Out-of-Sample-Performance |

## Globale End-to-End-Verifikation

```bash
ruff check . && mypy src                      # Lint + Strict-Type
pytest --cov=football_betting                 # Test-Coverage
fb train --league BL                          # Phase 2 aktiv
fb tune-ensemble --league BL --objective blended   # Phase 6
fb backtest --league BL --walk-forward        # Phase 6
fb snapshot && fb serve                        # API-Smoke
```

Erfolgs-Kriterium pro Liga (Out-of-Sample, 2024-25):
- RPS ≤ Baseline (siehe `baseline_metrics.md`)
- CLV-Mean > 0 nach Phase 4
- ROI auf Backtest > +2 % (Pinnacle-Closing als Referenz)
