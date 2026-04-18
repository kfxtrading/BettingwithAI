# Baseline-Metriken (vor XI-Reschape) — 2026-04-18

## CatBoost (alle Ligen, 71 Features, TRAIN_SEASONS=2021-22..2024-25)

| League | #Feat | RPS (raw) | RPS (cal) | ECE (raw) | ECE (cal) | Hit   |
|--------|-------|-----------|-----------|-----------|-----------|-------|
| PL     | 71    | 0.2010    | 0.1865    | 0.0432    | 0.0410    | 0.577 |
| CH     | 71    | 0.2133    | 0.2034    | 0.0678    | 0.0189    | 0.517 |
| BL     | 71    | 0.2181    | 0.1973    | 0.0794    | 0.0622    | 0.509 |
| SA     | 71    | 0.1870    | 0.1780    | 0.0369    | 0.0379    | 0.568 |
| LL     | 71    | 0.2008    | 0.1853    | 0.0454    | 0.0472    | 0.554 |

Sofascore-Staging (BL): 3 matches (nur Pre-Scrape-Daten ohne XI)

## MLP (BL only)

- n_train=955, n_val=169
- best_val_loss=1.0443

## Artefakte

- `models/catboost_BL.baseline.cbm`
- `models/mlp_BL.baseline.pt`
- `data/sofascore/BL_2024-25.baseline.json` (3 matches, keine XI)
