# Hybrid GPU-Stacking Upgrade — Implementation Plan

**Ziel:** CatBoost + Poisson + MLP + Wetter-Ensemble in ein echtes, GPU-trainiertes, state-of-the-art **Hybrid-Stacking-System** heben — ausgerichtet an den sechs Pfeilern des 2026-Reports (Concept-Drift-Gewichtung ✅, Power-Devig ✅, **Hybrid-Stacking ❌**, Walk-Forward ✅, **Differentiable-Kelly-Loss ❌**, CLV-Validierung ⚠️).

Die Aspekte 1, 2, 4 und partiell 6 sind bereits im Code vorhanden; dieser Plan adressiert die Lücken **GPU**, **Sequential-Model**, **Meta-Learner-Stacking** und **Kelly-Loss** bei voller Rückwärtskompatibilität.

---

## 1. Baseline-Status (verifiziert)

| Pfeiler | Status | Quelle |
|---|---|---|
| (1) Time-Decay | ✅ `decay=0.85` | [./src/football_betting/predict/weights.py:27](./src/football_betting/predict/weights.py:27) |
| (2) Power-Devig | ✅ Default | [./src/football_betting/betting/margin.py:41](./src/football_betting/betting/margin.py:41) |
| (3) Hybrid-Stacking + LSTM/Transformer | ❌ Lineare Dirichlet-Mischung | [./src/football_betting/predict/ensemble.py:43](./src/football_betting/predict/ensemble.py:43) |
| (4) Walk-Forward | ✅ 3 Folds + Leakage-Assert | [./src/football_betting/tracking/backtest.py:322](./src/football_betting/tracking/backtest.py:322) |
| (5) Differentiable-Kelly-Loss | ❌ CE-Loss only | [./src/football_betting/predict/mlp_model.py:150](./src/football_betting/predict/mlp_model.py:150) |
| (6) CLV-Validierung | ⚠️ Nur in Ensemble-Tuning, nicht im Base-Loss | [./src/football_betting/predict/ensemble.py:181](./src/football_betting/predict/ensemble.py:181) |
| GPU CatBoost | ❌ | [./src/football_betting/predict/catboost_model.py:135](./src/football_betting/predict/catboost_model.py:135) |
| GPU MLP | ✅ CUDA auto | [./src/football_betting/predict/mlp_model.py:142](./src/football_betting/predict/mlp_model.py:142) |

---

## 2. Ziel-Architektur

```
                   Walk-Forward Fold k
    train_seasons ─┬─► inner_train (80% chrono)
                   └─► stack_val   (20% chrono, < test)
    test_season    ──► kein Kontakt mit L1/Meta-Fit

  ┌────────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐
  │ CatBoost   │ │ MLP         │ │ SeqModel     │ │ DixonColes  │
  │ GPU        │ │ GPU + AMP   │ │ GRU+Attn GPU │ │ closed-form │
  │ MultiClass │ │ CE + λ·Kelly│ │ CE + λ·Kelly │ │ Poisson     │
  └────┬───────┘ └─────┬───────┘ └─────┬────────┘ └─────┬───────┘
       └─ isotonic/Platt per-head calibration on stack_val ─┘
                             │
                             ▼  (4 × 3 probs + 4 entropies + 3 market-probs = 19 feats)
                   ┌────────────────────────┐
                   │ StackingEnsemble (L2)  │
                   │   LR (default) | NN    │
                   │ fit on stack_val OOF   │
                   └───────────┬────────────┘
                               │
                               ▼
                  Power-devig → Kelly (f*=0.25, cap 5%) → CLV-Tracker
```

---

## 3. Neue Dateien

| Datei | ≈ LOC | Inhalt |
|---|---:|---|
| [./src/football_betting/predict/gpu_utils.py](./src/football_betting/predict/gpu_utils.py) | 60 | `detect_gpu()`, `seed_everything(seed)`, `make_amp_scaler()` |
| [./src/football_betting/predict/losses.py](./src/football_betting/predict/losses.py) | 90 | `KellyLoss`, `CombinedLoss(ce, kelly, lam)` |
| [./src/football_betting/predict/sequence_features.py](./src/football_betting/predict/sequence_features.py) | 160 | `build_team_sequence(team, as_of_date, form, pi, n)` → `(T, F_seq)` |
| [./src/football_betting/predict/sequence_model.py](./src/football_betting/predict/sequence_model.py) | 280 | `MatchSequenceDataset`, `MatchSequenceModel` (GRU+Attn), `SequenceTrainer` |
| [./src/football_betting/predict/stacking.py](./src/football_betting/predict/stacking.py) | 220 | `StackingEnsemble` (LR / NN Meta), OOF-Split, fit/predict |
| [./tests/test_gpu_utils.py](./tests/test_gpu_utils.py) | 40 | Seed-Reproduzierbarkeit, CPU-Fallback |
| [./tests/test_kelly_loss.py](./tests/test_kelly_loss.py) | 80 | Gradient-Check, Clamping, NaN-Guard |
| [./tests/test_sequence_features.py](./tests/test_sequence_features.py) | 100 | Deque-Slice, Pi-History, Padding, Leakage |
| [./tests/test_sequence_model.py](./tests/test_sequence_model.py) | 140 | Shapes, Forward-Pass CPU, GPU-marker, Softmax-Sum |
| [./tests/test_stacking.py](./tests/test_stacking.py) | 120 | 19-Feat-Input, LR + NN, OOF-Chronologie, Fallback |
| [./tests/test_catboost_gpu.py](./tests/test_catboost_gpu.py) | 50 | `task_type`-Verdrahtung, CPU-Fallback |
| [./tests/test_backtest_stacking.py](./tests/test_backtest_stacking.py) | 90 | Fold-Refit, stack_val-vor-test, Metrics |
| [./tests/test_train_all_cli.py](./tests/test_train_all_cli.py) | 60 | Flag-Parsing, Smoke CPU 1 Fold |

**Gesamt neu:** ≈ 1 490 LOC.

## 4. Zu editierende Dateien

| Datei | ΔLOC | Änderung |
|---|---:|---|
| [./src/football_betting/predict/catboost_model.py](./src/football_betting/predict/catboost_model.py) | +35 | Neuer Param `use_gpu: bool=False`; injiziert `task_type="GPU", devices="0"` wenn `detect_gpu()`; Dokumentation GPU-Nicht-Determinismus; `bootstrap_type="Bayesian"` auf GPU |
| [./src/football_betting/predict/mlp_model.py](./src/football_betting/predict/mlp_model.py) | +60 | Optional `KellyLoss` via `use_kelly_loss=True, kelly_lambda=0.3`; AMP via `torch.cuda.amp.autocast` + `GradScaler`; Expose `predict_logits()` (vor Softmax) für Stacking |
| [./src/football_betting/predict/ensemble.py](./src/football_betting/predict/ensemble.py) | +40 | Neue `predict_with_stacking()`-Route; Legacy-`tune_dirichlet` bleibt; `EnsembleConfig.stacking: bool` |
| [./src/football_betting/tracking/backtest.py](./src/football_betting/tracking/backtest.py) | +55 | `stack_val`-Chrono-Split innerhalb `train_seasons` (letzte 20 %); L1 auf `inner_train` fitten → OOF-Probs auf `stack_val` → Meta trainieren → L1 auf `train_seasons` re-fitten; Meta bleibt eingefroren; Leakage-Asserts |
| [./src/football_betting/features/form.py](./src/football_betting/features/form.py) | +15 | `get_recent(team: str, n: int=10) -> list[MatchRecord]` (read-only Slice der bestehenden deque) |
| [./src/football_betting/rating/pi_ratings.py](./src/football_betting/rating/pi_ratings.py) | +10 | `get_history_before(date) -> list[dict]` (bereits existierendes `history`-Feld, Filter auf as-of) |
| [./src/football_betting/cli.py](./src/football_betting/cli.py) | +90 | Neues `fb train-all`-Command mit Flags (siehe §5); `fb backtest --stacking` Pass-through |
| [./scripts/train.py](./scripts/train.py) | +20 | Weiterleiten der neuen Flags |
| [./src/football_betting/config.py](./src/football_betting/config.py) | +30 | `CatBoostConfig.use_gpu`, `MLPConfig.use_kelly_loss/kelly_lambda`, `EnsembleConfig.stacking/meta_learner`, `SequenceConfig` (T, F_seq, hidden, dropout) |
| [./pyproject.toml](./pyproject.toml) | +4 | Version → 0.4.0; optional `[gpu]` Extra (`torch>=2.2`, `catboost>=1.2.5` GPU-Build-Hinweis) |

**Gesamt editiert:** ≈ 360 LOC.

---

## 5. Neue CLI-Befehle & Config-Flags

### `fb train-all`

```bash
fb train-all --league BL \
  --gpu / --no-gpu          # Default: Auto-Detect CUDA
  --amp / --no-amp          # Mixed-Precision für MLP + Seq
  --sequence / --no-sequence
  --stacking / --no-stacking
  --kelly-lambda 0.3        # 0.0 deaktiviert Kelly-Loss
  --seq-window 10           # T in (2, T, F_seq)
  --meta-learner lr|nn      # Default: lr
  --seed 42
```

`fb train` bleibt **unverändert** für Backward-Compat. `train-all` ist die Superset-Pipeline.

### Config-Erweiterungen

```python
# config.py
@dataclass(frozen=True, slots=True)
class CatBoostConfig:
    use_gpu: bool = False           # Opt-in; Auto-Detect in train-all
    ...

@dataclass(frozen=True, slots=True)
class MLPConfig:
    use_kelly_loss: bool = False
    kelly_lambda: float = 0.3
    use_amp: bool = True
    ...

@dataclass(frozen=True, slots=True)
class SequenceConfig:
    enabled: bool = False
    window_t: int = 10
    n_features: int = 14
    gru_hidden: int = 64
    gru_layers: int = 2
    bidirectional: bool = True
    dropout: float = 0.2
    lr: float = 5e-4
    epochs: int = 25
    batch_size: int = 128

@dataclass(frozen=True, slots=True)
class EnsembleConfig:
    stacking: bool = False
    meta_learner: Literal["lr", "nn"] = "lr"
```

---

## 6. Walk-Forward + Stacking (leakage-sicher)

Innerhalb eines Folds:

```text
train_seasons = (2019-20, 2020-21, 2021-22)        # z.B.
test_season   = 2022-23

1. Chrono-Split train_seasons:
     inner_train = ältere 80 %    (z.B. 2019-20, 2020-21)
     stack_val   = jüngste 20 %   (z.B. Hälfte 2021-22)
     assert stack_val.date.max() < test.date.min()      # Leakage-Gate 1
     assert inner_train.date.max() < stack_val.date.min()

2. L1 auf inner_train fitten (CatBoost, MLP, SeqModel; Poisson closed-form)

3. OOF-Probs auf stack_val erzeugen → X_meta (19 Feats) + y_meta
     - 4 Modelle × 3 Klassen = 12 Prob-Dims
     - 4 Entropien              = 4 Dims
     - 3 Power-devigte Market-Probs = 3 Dims
     - TOTAL: 19

4. Meta-Learner (LR default) auf (X_meta, y_meta) fitten.

5. L1 auf VOLLEM train_seasons RE-FIT (Standard-Stacking-Muster).
   Meta bleibt EINGEFROREN — es hat nur stack_val gesehen (< test_season).

6. Prediction Pipeline für test_season:
     L1(refit) → probs + entropy → concat market_probs → Meta → final probs
```

Asserts:

```python
# tracking/backtest.py
assert stack_val_dates.max() < test_dates.min(), "Stacking leakage!"
assert inner_train_dates.max() < stack_val_dates.min()
```

`MatchSequenceDataset` fragt `form.get_recent(team, n, before=match.date)` ab — die Tracker werden chronologisch gefüllt, daher inhärent leakage-frei.

---

## 7. Sequence-Model — Details

**Input-Tensor:** `(B, 2, T=10, F_seq=14)` (home- + away-Team-History)

```python
F_seq = [
  "pi_home_rating", "pi_away_rating", "goals_for", "goals_against",
  "shots", "shots_on_target", "is_home", "xg_proxy", "points",
  "opp_strength", "days_since_last", "rest_delta", "form_trend_ema",
  "result_win_onehot",  # (D/L können als implizit via points abgeleitet werden)
]
```

**Padding:** Bei < T Matches → Pre-Pad mit Zero-Vektor + Binär-Maske.

**Architektur:**

```python
class MatchSequenceModel(nn.Module):
    def __init__(self, F_seq=14, T=10, hidden=64, layers=2):
        super().__init__()
        self.gru = nn.GRU(F_seq, hidden, num_layers=layers,
                          batch_first=True, bidirectional=True, dropout=0.2)
        self.attn = nn.Linear(hidden*2, 1)   # additive attention pooling
        self.head = nn.Sequential(
            nn.Linear(hidden*2*2, 128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 3),
        )

    def forward(self, home_seq, away_seq, home_mask, away_mask):
        h_h = self._encode(home_seq, home_mask)   # (B, hidden*2)
        h_a = self._encode(away_seq, away_mask)
        return self.head(torch.cat([h_h, h_a], dim=-1))  # logits (B,3)
```

---

## 8. Loss-Funktionen — CE + λ·Kelly

```python
# losses.py
class KellyLoss(nn.Module):
    def __init__(self, f_cap: float = 0.25, eps: float = 1e-6):
        super().__init__()
        self.f_cap, self.eps = f_cap, eps

    def forward(self, probs, odds, y_onehot):
        # probs: (B,3) softmax; odds: (B,3) decimal; y_onehot: (B,3)
        p = probs.clamp(self.eps, 1 - self.eps)
        b = odds - 1.0
        f_star = ((b * p - (1 - p)) / b).clamp(0.0, self.f_cap)
        r = (odds * y_onehot - 1.0)                    # realized return per class
        growth = (1.0 + f_star * r).clamp(min=self.eps)
        return -(p * torch.log(growth)).sum(dim=1).mean()
```

**Kombination:** `L = CE(logits, y) + λ · KellyLoss(softmax(logits), odds, y_onehot)`

| Phase | λ |
|---|---|
| Warmup (Epoch 1–3) | 0.0 |
| Main (Epoch 4–25) | 0.3 |
| Fine-tune (letzte 5) | 0.5 |

- Angewendet auf **MLP** und **SequenceModel**.
- CatBoost bleibt MultiClass; Poisson unverändert.
- Unter AMP: KellyLoss in `fp32` (autocast disabled) wegen Clamp-Numerik.

---

## 9. Training-Schedule

### CatBoost (GPU)

```python
CatBoostClassifier(
    iterations=1500, depth=6, learning_rate=0.05,
    task_type="GPU" if detect_gpu() else "CPU",
    devices="0",
    bootstrap_type="Bayesian",          # Pflicht auf GPU
    random_seed=42, classes_count=3,
    loss_function="MultiClass", eval_metric="MultiClass",
    early_stopping_rounds=100,
)
```
GPU-Reproduzierbarkeit ist **nicht bitweise exakt** — in Docstring + Tests dokumentiert (Toleranz RPS ±1e-3).

### MLP (PyTorch AMP)

- Batch 256 · 30 Epochen · AdamW `lr=1e-3`, `weight_decay=1e-4` · CosineAnnealingLR
- Dropout 0.3, BatchNorm, AMP on
- Early-Stop auf Val-RPS, Patience=5
- `predict_logits()` extrahiert Pre-Softmax-Logits für Stacking

### Sequence-Model

- Batch 128 · 25 Epochen · AdamW `lr=5e-4` · OneCycleLR
- Dropout 0.2, grad-clip 1.0, AMP on
- Checkpoint pro Fold → `models/seq_<league>_fold{k}.pt`

### Meta-Learner

| Variante | Config |
|---|---|
| `lr` (Default) | `LogisticRegression(C=1.0, multi_class="multinomial", max_iter=1000)` |
| `nn` | `Linear(19,32) → ReLU → Dropout(0.2) → Linear(32,3)`, 50 Epochen, Adam 1e-3 |

Kein KellyLoss im Meta-Learner (Interpretierbarkeit + wenig Daten im stack_val).

### Reproduzierbarkeit

```python
def seed_everything(seed=42):
    random.seed(seed); np.random.seed(seed)
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

CatBoost-GPU + AMP ≈ RPS-Drift < 1e-3 pro Lauf.

---

## 10. Tests (verpflichtend)

| Datei | Tests |
|---|---|
| `tests/test_catboost_gpu.py` | `test_gpu_flag_wires_task_type`, `test_cpu_fallback_when_no_cuda`, `test_predict_shape_unchanged` [marker: `gpu`] |
| `tests/test_kelly_loss.py` | `test_gradient_flow`, `test_f_cap_clamp`, `test_zero_loss_perfect_prediction`, `test_no_nan_on_zero_prob`, `test_combined_loss_lambda_scaling` |
| `tests/test_sequence_features.py` | `test_deque_slice_returns_latest_n`, `test_pi_history_before_date`, `test_pads_when_fewer_than_N`, `test_home_away_tensors_disjoint`, `test_no_future_leakage` |
| `tests/test_sequence_model.py` | `test_tensor_shapes`, `test_forward_cpu`, `test_softmax_sums_to_1`, `test_forward_amp_gpu` [marker: `gpu`], `test_padding_mask_ignored` |
| `tests/test_stacking.py` | `test_meta_input_is_19_features`, `test_lr_meta_fit_predict`, `test_nn_meta_fit_predict`, `test_oof_split_is_chronological`, `test_no_leakage_into_test`, `test_fallback_to_linear_when_stacking_false` |
| `tests/test_backtest_stacking.py` | `test_fold_refits_l1_after_meta`, `test_stack_val_before_test_assertion`, `test_metrics_emitted_for_stacking_run` |
| `tests/test_train_all_cli.py` | `test_train_all_flags_parse`, `test_train_all_smoke_cpu_1fold_1league` |
| `tests/test_gpu_utils.py` | `test_seed_everything_reproducible`, `test_detect_gpu_returns_bool` |

Alle GPU-Tests hinter `@pytest.mark.gpu`, CI-Default bleibt grün (CPU).

---

## 11. Risiken & Mitigationen

| Risiko | Mitigation |
|---|---|
| CatBoost-GPU Nicht-Determinismus | `@pytest.mark.gpu` + `rtol=1e-2`; CPU bleibt Default |
| SeqModel-Overfit auf ≈3 800 Matches/Saison | Dropout 0.2, Weight-Decay, Early-Stop; Joint-Pretrain über alle 5 Ligen, Per-Liga-Finetune |
| KellyLoss NaN bei extremen Quoten | Clamp `p ∈ [ε, 1−ε]`, `f ∈ [0, 0.25]`, `growth ≥ ε`; Unit-Test |
| Leakage via FormTracker / PiRatings | `get_recent(before=date)`-Signatur + Assert `max(seq.date) < match.date` |
| Stacking-Meta-Overfit (nur 20 % stack_val) | LR (starker Bias) Default; L2 `C=1.0`; `nn` nur Opt-in |
| 3-Fold Meta sehr klein | Per-Fold-Meta trainieren; optional Pooling mit `fold_id` als kategorisches Feature |
| AMP Spikes mit KellyLoss | KellyLoss in `fp32` via `autocast(enabled=False)` |
| Bricht 326 bestehende Tests | Alle neuen Pfade hinter Flags (`--stacking/--sequence`); `fb train` bleibt bit-identisch |
| RTX 3080 OOM | Grad-Accumulation ×2; GRU-Hidden 64 statt 128 |
| CatBoost-GPU braucht `Bayesian`-Bootstrap | Dokumentiert; CPU-Pfad bleibt `Bernoulli` |

---

## 12. Erfolgskriterien — BL 2024-25 (out-of-sample)

Aktueller Baseline (nach Phase-6 + Wetter):

| Metric | Baseline |
|---|---:|
| mean_RPS | 0.2164 |
| mean_log_loss | 1.0413 |
| ECE | ≈ 1.4 % |
| CLV-Mean | −3.12 % |
| ROI | −19.8 % |
| Sharpe | −1.14 |

**Zielwerte nach Implementation:**

| Metric | Ziel | Hard-Gate (CI-Failure darunter) |
|---|---:|---:|
| mean_RPS | ≤ 0.210 | ≤ 0.218 |
| log_loss | ≤ 0.985 | ≤ 1.02 |
| ECE | ≤ 1.2 % | ≤ 1.6 % |
| **CLV-Mean** | **≥ 0 %** | ≥ −0.5 % |
| **ROI** | **≥ +2 %** | ≥ 0 % |
| Sharpe | ≥ +0.3 | ≥ 0.0 |

---

## 13. End-to-End-Verifikation

```bash
# 1. Install GPU extras
pip install -e ".[ml,dev,gpu]"

# 2. Unit + Integration
pytest tests/test_kelly_loss.py tests/test_sequence_features.py \
       tests/test_sequence_model.py tests/test_stacking.py \
       tests/test_backtest_stacking.py tests/test_train_all_cli.py -v

# 3. Bestehende 326 Tests müssen grün bleiben
pytest

# 4. Full Training (≈ 50 min auf RTX 3080)
fb train-all --league BL --gpu --amp --sequence --stacking --kelly-lambda 0.3

# 5. Walk-Forward-Backtest mit Stacking
fb backtest --league BL --walk-forward --stacking

# 6. A/B-Vergleich (baseline vs neu)
fb backtest --league BL --compare-baseline
# Emittiert reports/bl_2024_25_ab.json mit PASS/FAIL gegen Hard-Gates

# 7. Lint + Type-Check
ruff check src && mypy src
```

**CI-Blocker:** Phase-6-Tests (16) + neue Tests (≈ 11) müssen alle grün sein; `--compare-baseline` muss alle **Hard-Gates** erfüllen (nicht nur Targets).

---

## 14. Aufwand & Zeitplan

| Phase | Aufwand |
|---|---|
| GPU-Utils + CatBoost-GPU + Tests | 0.5 h |
| KellyLoss + Tests | 0.5 h |
| SequenceFeatures + Tests | 1.0 h |
| SequenceModel + Dataset + Tests | 1.5 h |
| StackingEnsemble + Tests | 1.0 h |
| Backtest-Integration + Tests | 1.0 h |
| CLI `train-all` + Config | 0.5 h |
| End-to-End-Lauf + A/B-Report | 0.5 h Coding + 1 h Training |
| **Gesamt** | **~ 6.5 h Coding + 1 h Training** |

Für alle 5 Ligen parallel: ≈ 4 h Training-Wall-Clock.

---

## 15. Kritische Dateien (Read-First-Referenz für Umsetzung)

1. [./src/football_betting/predict/ensemble.py](./src/football_betting/predict/ensemble.py) — bestehende Blend-Logik + `tune_dirichlet`
2. [./src/football_betting/predict/catboost_model.py](./src/football_betting/predict/catboost_model.py) — CatBoost-Fit, Sample-Weights
3. [./src/football_betting/predict/mlp_model.py](./src/football_betting/predict/mlp_model.py) — PyTorch-Setup, CUDA-Selektion
4. [./src/football_betting/tracking/backtest.py](./src/football_betting/tracking/backtest.py) — Walk-Forward-Schema, Feature-Builder-Injektion
5. [./src/football_betting/features/form.py](./src/football_betting/features/form.py) — `deque[MatchRecord]` je Team (Sequence-Quelle)
6. [./src/football_betting/rating/pi_ratings.py](./src/football_betting/rating/pi_ratings.py) — `history: list[dict]` (Pi-Zeitreihe)
7. [./src/football_betting/betting/margin.py](./src/football_betting/betting/margin.py) — Power-Devig-Referenz für Market-Probs
8. [./src/football_betting/betting/kelly.py](./src/football_betting/betting/kelly.py) — Fractional-Kelly-Semantik (Referenz für Differentiable-Variante)
9. [./src/football_betting/config.py](./src/football_betting/config.py) — alle Configs
10. [./pyproject.toml](./pyproject.toml) — PyTest-Marker (`gpu`, `dml`)
