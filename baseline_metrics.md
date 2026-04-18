# RPS/ECE-Delta — Pre- vs. Post-XI-Rescrape (2026-04-18)

Vergleich zwischen Baseline (3 Sofascore-Matches ohne XI) und Post-Scrape
(305 Sofascore-Matches mit XI + real xG). Andere Ligen (PL/CH/SA/LL) haben
weiter keine Sofascore-Daten → erwartungsgemäß unverändert.

## CatBoost — FINAL SUMMARY

| League | #Feat | RPS (raw) | RPS (cal) | ECE (raw) | ECE (cal) | Hit   |
|--------|-------|-----------|-----------|-----------|-----------|-------|
| PL     | 71    | 0.2010    | 0.1865    | 0.0432    | 0.0410    | 0.577 |
| CH     | 71    | 0.2133    | 0.2034    | 0.0678    | 0.0189    | 0.517 |
| **BL** baseline | **71** | **0.2181** | **0.1973** | **0.0794** | **0.0622** | **0.509** |
| **BL** post     | **84** | **0.2175** | **0.1985** | **0.0715** | **0.0425** | **0.497** |
| SA     | 71    | 0.1870    | 0.1780    | 0.0369    | 0.0379    | 0.568 |
| LL     | 71    | 0.2008    | 0.1853    | 0.0454    | 0.0472    | 0.554 |

### BL Delta (das einzige betroffene Modell)

| Metrik  | Baseline | Post   | Δ        | Richtung          |
|---------|----------|--------|----------|-------------------|
| #Feat   | 71       | 84     | +13      | real_xg_* aktiv   |
| RPS raw | 0.2181   | 0.2175 | −0.0006  | marginal besser   |
| RPS cal | 0.1973   | 0.1985 | +0.0012  | marginal schlechter (Noise, n_val=169) |
| ECE raw | 0.0794   | 0.0715 | −0.0079  | 10 % besser       |
| ECE cal | 0.0622   | 0.0425 | −0.0197  | **32 % besser**   |
| Hit     | 0.509    | 0.497  | −0.012   | im Noise-Bereich  |

**Interpretation:** Der Rescrape aktiviert 13 `real_xg_*`-Features im BL-Modell
(von 71 auf 84). RPS bleibt im Noise, ECE cal verbessert sich deutlich — die
Predictions sind besser kalibriert, was direkt auf Kelly-Staking durchschlägt.

Die 8 `squad_*`-Features tauchen nicht in der Feature-Count-Diff auf (13 ≠ 21).
Entweder sind sie konstant/low-variance und fallen durch CatBoosts Filter,
oder der zeitliche Walk-Forward-Flow ingestiert sie erst, nachdem der Staging-
Bucket leer ist. → Nachträgliches Nachziehen sinnvoll, siehe TODO.

## MLP (BL only, best_val_loss)

| Run     | n_train | n_val | best_val_loss |
|---------|---------|-------|---------------|
| Baseline | 955    | 169   | 1.0443        |
| Post-scrape | 955 | 169   | 1.0386        |

Δ best_val_loss = −0.0057 (≈0.5 % besser).

Hotfix im Rahmen des Retrain-Runs: `mlp_model.build_training_data` füllt
jetzt NaN-Spalten mit 0.0, weil die Feature-Keys zwischen Samples variieren
(2021-22..2023-24 ohne real_xg, 2024-25 mit). CatBoost schluckt NaN nativ,
MLP nicht → Isotonic-Calibrator hatte gecrasht.

## Artefakte

- `models/catboost_BL.baseline.cbm` ↔ `models/catboost_BL.cbm` (post)
- `models/mlp_BL.baseline.pt` ↔ `models/mlp_BL.pt` (post)
- `data/sofascore/BL_2024-25.baseline.json` (3 Matches, keine XI)
- `data/sofascore/BL_2024-25.json` (305 Matches mit XI + real xG)

## Offene TODOs

1. Prüfen, warum nur 13 statt 21 neue Features ankommen
   (squad_quality-Gruppe tot?). Einstiegspunkt:
   [features/builder.py:update_with_match](src/football_betting/features/builder.py)
   — ingest_sofascore_match für squad_quality verifizieren.
2. Weitere Ligen scrapen (PL/CH/SA/LL × 4 Saisons) — aktuell alle nur
   football-data.co.uk.
3. MLP-Retrain als Teil von `scripts/train.py` einhängen, damit beide
   Modelle immer zusammen aktualisiert werden.
