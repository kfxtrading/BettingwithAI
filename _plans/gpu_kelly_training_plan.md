# GPU-gestütztes Kelly/CLV-Training der Deep-Modelle

**Datum:** 2026-04-24
**Host:** RunPod RTX 4090 (analog Support-TX-Retrain)
**Ziel:** MLP + Sequence + TabTransformer auf einem **Profit-/CLV-ausgerichteten Objective** trainieren statt auf reinem Cross-Entropy + Post-hoc-Kalibrierung + Post-hoc-Gewichts-Tuning. Bankroll-ROI (aktuell BL −22 %) ist der Engpass, nicht Point-Accuracy.

## Ausgangslage (verifiziert im Code)

- `KellyLoss` + `CombinedLoss(CE + λ·Kelly)` existieren bereits in [losses.py](../src/football_betting/predict/losses.py). Clamped `[0, f_cap=0.25]`, numerisch abgesichert.
- `MLPConfig.use_kelly_loss = True` → Hook in [mlp_model.py:175](../src/football_betting/predict/mlp_model.py) aktiv.
- `SequenceConfig.use_kelly_loss = False`, `TabTransformerConfig.use_kelly_loss = False` → Hooks da, aber deaktiviert.
- Trainings-Loader bauen `odds_array` aus `Match.odds` = **Closing-Odds**, mit Fallback `(2.0, 3.5, 3.5)` bei Fehlen → Kelly-Gradient verzerrt durch Platzhalter-Samples.
- `Match.opening_odds` ist im Datenmodell vorhanden, wird aktuell **nicht** in die Trainings-Daten gezogen. Das ist der entscheidende Hebel: Bet wird zur Opening-Line platziert, CLV misst Opening→Closing — also muss Kelly auf **Opening-Odds** trainiert werden, nicht Closing.
- Post-CE-Isotonic läuft in `predict/calibration.py` — muss nach Kelly-Training re-evaluiert werden (Isotonic kann Kelly-optimale Extremwerte wieder einebnen).

## Leitlinien

1. **Kein Regress:** CE-Objective bleibt Default. Kelly-Modus wird **additiv** per CLI-Flag (`--kelly`) und Config-Schalter aktiviert. Bestehende Checkpoints bleiben valide.
2. **CLV-Alignment:** Training auf Opening-Odds, Validation-Metrik auf Opening→Closing-CLV plus Standard-RPS. Wenn nur Closing verfügbar ist, Sample maskieren (Opening fehlt) — nicht mit Closing faken, sonst trainieren wir gegen unser eigenes Signal.
3. **Shrinkage gegen Markt:** KL(p_model ‖ p_market_opening) als Regularizer, Gewicht `β` wird gesweept. Verhindert degenerate Extrema, die Kelly-Loss ohne Regularisierung liebt.
4. **Reproducibility:** Alle Runs loggen Seed, Commit, Konfiguration, Opening-Odds-Coverage, Val-RPS, Val-Brier, Val-CLV, Val-Kelly-Growth in `models/_runs/*.json`. Artefakte via `scp` von RunPod nach `models/` in lokalen Commit.
5. **Akzeptanz ehrlich:** Multi-Fold-Walk-Forward-Validierung (Phase 5 der bestehenden Roadmap) **zwingend vor** Produktions-Rollout. Ein besserer 2024-25-Val-CLV reicht nicht.

## Phasenplan

### Phase A — Opening-Odds in Trainingsdaten (Vorbereitung, CPU)

**Aufwand:** 2–3 h. Lokal, kein GPU nötig.

**Aufgaben:**
- [ ] `MLPPredictor.build_training_data` erweitern: `opening_array` neben `odds_array` (Closing) ausgeben. Shape `(N, 3)` mit `np.nan`, wenn `match.opening_odds is None`.
- [ ] Analog `SequencePredictor.build_training_data` und `TabTransformerPredictor.build_training_data`.
- [ ] Neue Column `kelly_mask` (Bool, `N×1`) → `True` wenn alle 3 Opening-Odds vorhanden und > 1.0. Wird von `CombinedLoss`-Aufrufer genutzt, um Kelly-Term nur auf gültigen Samples zu mitteln.
- [ ] Unit-Test `tests/test_opening_odds_loader.py`: synth. Matches mit/ohne Opening-Odds → `kelly_mask`-Korrektheit + `opening_array` NaN-Placement.

**Akzeptanz:** `fb train --league BL --dry-run` loggt "kelly-mask coverage X %" pro Liga. BL muss ≥ 60 % erreichen (Sofascore-Rescrape ist solide); PL/CH/LL/SA dokumentieren den Ist-Zustand (kann niedrig sein → Hinweis für Snapshot-Phase 4).

### Phase B — `CombinedLoss` CLV-tauglich (refactor losses.py)

**Aufwand:** 2 h. Lokal, kein GPU.

**Aufgaben:**
- [ ] `CombinedLoss.__call__` um `mask: Tensor[bool]` erweitern. Kelly-Term mittelt nur über `mask==True`; CE weiter über alles.
- [ ] Neue Klasse `ShrinkageCombinedLoss(CE + λ·Kelly + β·KL(p_model ‖ p_market))`. `p_market` aus margin-removed Opening-Odds.
- [ ] `LambdaSchedule`: warmup `lam=0.0` für erste `warmup_epochs` (z. B. 5), dann linear auf `lam_max` (z. B. 0.5) rampen. Verhindert, dass CE-freie Kelly-Gradienten ein untrainiertes Netz in Minima pushen.
- [ ] Unit-Tests `tests/test_losses.py`: Gradient-Check (`torch.autograd.gradcheck` auf Mini-Batch), Mask-Korrektheit, Degenerate-Odds (`odds ≤ 1.0`) → Gradient endlich.

**Akzeptanz:** `pytest tests/test_losses.py` grün. Gradient bleibt bei `f*=0`-Clamp (Modell-Prob unterhalb Break-even) finit.

### Phase C — Trainings-Loops verdrahten (RunPod)

**Aufwand:** 3–4 h Code + über-Nacht-Training.

**Aufgaben:**
- [ ] `MLPPredictor.fit`, `SequencePredictor.fit`, `TabTransformerPredictor.fit` erhalten neuen Pfad `use_shrinkage_kelly=True`: nimmt `opening_array` + `kelly_mask` + `p_market` in die `DataLoader`-Tupel auf.
- [ ] Optimizer: AdamW `lr=3e-4`, cosine-decay, `weight_decay=1e-4`, gradient-clip `1.0`. Batch-Size `256` (MLP), `128` (Seq), `192` (TabTX) — auf 4090 kein Speicher-Problem.
- [ ] CUDA-Autocast (fp16) + `GradScaler`. MLP/TabTX profitieren stark, Seq-Transformer moderat.
- [ ] **Validation-Hook pro Epoche**: Opening-Odds-basierter Kelly-Growth (`mean log(1 + f* · r)`) + RPS + Brier. Early-Stopping auf Kelly-Growth (nicht val-loss!).
- [ ] `scripts/train.py --kelly` Flag: schaltet für alle gewählten Backbones den neuen Pfad ein; persistiert Checkpoints unter `models/{catboost,mlp,seq,tab}_{LEAGUE}.kelly.*` parallel zu den CE-Baselines.
- [ ] Dockerfile / RunPod-Bootstrap: `pip install -e .[ml,api]` reicht; kein neues Dep.

**Akzeptanz:**
- Training-Kurven (TensorBoard oder `rich`-Log) in `models/_runs/` zeigen monoton steigenden Val-Kelly-Growth.
- 5 Ligen × 3 Modelle = 15 Runs fertig, alle `.kelly.*`-Artefakte erzeugt, kein Run < Baseline-RPS-raw + 0.005 (Sicherheits-Guard, sonst Early-Stop).

### Phase D — Post-Kelly-Kalibrierung neu entscheiden

**Aufwand:** 2 h. Lokal.

**Aufgaben:**
- [ ] Je Modell/Liga drei Kalibrierungs-Varianten evaluieren: **(a)** keine, **(b)** Isotonic wie bisher, **(c)** Temperature-Scaling (1 Parameter).
- [ ] Auf Val: ECE + CLV + Kelly-Growth tabellieren. Gewinnerin wird produktiv, default bleibt "none" für Kelly-trainierte Modelle.
- [ ] `calibration.py`: neues Feature `method="temperature"` ergänzen (ein-parametrig, kein Isotonic-Overfit-Risiko).

**Akzeptanz:** Für jeden der 15 Runs ist die Gewinner-Kalibrierung in `models/*.kelly.calibrator.joblib` persistiert, die Wahl in `models/_runs/*.json` begründet.

### Phase E — Ensemble-Re-Tuning & Backtest

**Aufwand:** 1 h Rechenzeit + Review.

**Aufgaben:**
- [ ] `fb tune-ensemble --league all --objective clv --use-kelly-checkpoints` → Dirichlet-Sampling über Simplex (CB[CE] + Poisson + MLP[Kelly] + Seq[Kelly] + TabTX[Kelly]).
- [ ] Neue Gewichte nach `models/ensemble_weights_{lang}_kelly.json` schreiben, nicht die CE-Variante überschreiben (A/B-fähig bleiben).
- [ ] `fb backtest --league all --ensemble kelly` → ROI / CLV / Sharpe / Max-Drawdown vs. CE-Baseline tabellieren.

**Akzeptanz (harter Gate):**
| Metrik                            | Baseline (BL val 2024-25) | Ziel              |
|-----------------------------------|---------------------------|-------------------|
| Backtest-ROI                      | −22.4 %                   | > −5 % (BL), > 0 (Mittel über 5 Ligen) |
| Mean CLV                          | +0.64 %                   | ≥ Baseline        |
| Sharpe                            | −2.33                     | > 0               |
| Val-RPS cal                       | 0.1985                    | ≤ Baseline + 0.003 |

Fallback-Kriterium: wenn **keines** der 15 Kelly-Modelle die Gates besetzt, ganze Variante deaktivieren und auf Phase A+B als Infrastruktur-Gewinn reduzieren. Kein Silent-Degrade.

### Phase F — Walk-Forward-Robustheits-Check (bindet Phase 5 der Haupt-Roadmap ein)

**Aufwand:** 2–3 h + CSV-Download.

**Aufgaben:**
- [ ] `fb download --seasons 2019-20,2020-21,2021-22,2022-23` (falls nicht schon vorhanden).
- [ ] `fb backtest --league all --walk-forward --folds 5 --ensemble kelly` vs. `--ensemble ce-baseline`.
- [ ] Pro Fold/Liga: Kelly-Growth, ROI, CLV, Max-DD. LCB-Metrik `mean − 1.5·std`.

**Akzeptanz:** LCB-ROI > −5 % in ≥ 3/5 Ligen. Kein Fold mit ROI < −15 % in irgendeiner Liga. Sonst Roll-back auf CE-Ensemble, Kelly-Variante bleibt experimentell.

### Phase G — Produktions-Rollout (nur bei grünem Phase E+F)

**Aufwand:** 1 h.

**Aufgaben:**
- [ ] `SUPPORT_CFG`-analoges Runtime-Feature-Flag `PREDICT_KELLY_MODE` (env-var, default `off`) in `api/services.py`. `on` → lädt `.kelly.*`-Artefakte + `ensemble_weights_*_kelly.json`.
- [ ] Flag erst **nur für BL** aktivieren (stärkstes Datensignal wegen Sofascore-Rescrape), 2 Wochen live CLV-Tracking im `monitoring/`-Dashboard beobachten.
- [ ] Nach Freigabe sukzessive PL → LL → SA → CH freischalten.
- [ ] CHANGELOG-Eintrag + dieser Plan als "erledigt" abhaken.

**Akzeptanz:** 2 Wochen live-CLV mean > 0 pro freigeschalteter Liga, kein Drawdown > 30 %.

## Risiken & Gegenmaßnahmen

- **Kelly-Gradient-Blow-up** bei `f* · r ≈ −1` (growth → 0): schon in `KellyLoss` clamped, zusätzlich `torch.nn.utils.clip_grad_norm_(1.0)`.
- **Opening-Odds-Coverage zu niedrig** (PL/CH/LL/SA unter 30 %): dann trainieren wir effektiv mit 70 % reinem CE und hoffen, dass die restlichen 30 % Kelly-Gradient reichen. Ausweg: Phase 4 der Haupt-Roadmap (Opening-Odds-Secret) **vorziehen**, sonst bleibt Kelly-Training auf BL beschränkt.
- **Isotonic killt Kelly-Kanten** wieder: daher Phase D explizit als Entscheidungsschritt.
- **Deep-Model-Instabilität auf 4090 vs. DirectML lokal**: alle Modelle nutzen `resolve_device()`, sollte transparent sein. Trotzdem: finalen Sanity-Check auf CPU, bevor Checkpoint in `models/` committet wird — Training auf GPU, Inferenz muss aber überall laufen.
- **Overfitting auf 2024-25** ohne Walk-Forward erkennbar → Phase F ist **nicht optional**.

## Abhängigkeiten zur bestehenden Roadmap

- Phase 4 (Opening-Odds-Workflow-Secret) der [optimization_roadmap_2026-04-23.md](optimization_roadmap_2026-04-23.md) sollte **vor** Phase C laufen, sonst ist Opening-Odds-Coverage für 4/5 Ligen zu dünn.
- Phase 1 (Weather-Wiring) ist orthogonal, kann parallel passieren.
- Phase 2 (MLP-Checkpoint-Fix torch 2.6) ist **Voraussetzung** für Phase C — sonst laden unsere neuen Kelly-Checkpoints später in Produktion nicht.

## Zeitschätzung (ohne Wartezeit auf RunPod-Training)

| Phase | Aufwand (aktiv) | Blocking? |
|-------|-----------------|-----------|
| A     | 2–3 h           | ja        |
| B     | 2 h             | ja        |
| C     | 3–4 h + Training über Nacht | ja |
| D     | 2 h             | ja        |
| E     | 1 h             | ja        |
| F     | 2–3 h           | ja (Gate) |
| G     | 1 h             | nein      |
| **Σ** | **~15 h aktiv** + 1 RunPod-Nacht + 2 Wochen Live-Monitoring |

## Nächster konkreter Schritt

Nach Freigabe dieses Plans: **Phase A** starten — Opening-Odds-Loader erweitern + `kelly_mask`, Tests schreiben, dann Phase B im gleichen Commit-Block. Erst nach grünem `pytest` RunPod-Pod hochfahren für Phase C.
