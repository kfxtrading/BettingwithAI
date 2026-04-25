# Trainingsdaten für Value-Bet-Optimierung — Report

Stand: 2026-04-25. Bestandsaufnahme aller im Repo verfügbaren Trainings- und Evaluations-Datenquellen, die zur Optimierung der Value-Bet-Vorhersagen herangezogen werden können.

## 1. Football-Data CSVs (Match-Historie + Pre-Game-Odds)

Pfad: [data/raw/](../data/raw/) — Quelle: football-data.co.uk

5 Ligen × bis zu 5 Saisons (2021-22 bis laufend 2025-26):

| Liga | Code | 21/22 | 22/23 | 23/24 | 24/25 | 25/26 (laufend) |
|---|---|---|---|---|---|---|
| Premier League (PL) | E0 | 380 | 380 | 380 | 380 | 332 |
| Championship (CH) | E1 | 552 | 552 | 552 | 552 | 528 |
| Bundesliga (BL) | D1 | 306 | 306 | 306 | 306 | 270 |
| Serie A (SA) | I1 | 380 | 380 | 380 | 380 | 330 |
| La Liga (LL) | SP1 | 380 | 380 | 380 | 380 | 320 |

(Werte = Anzahl gespielter Matches / Datei, ohne Header-Zeile)

**Gesamt (abgeschlossen + teilweise laufend): ~9 300 Matches.**

Pro Match enthalten: Endergebnis, Halbzeit, Schüsse/Schüsse aufs Tor, Karten, Fouls, Eckbälle plus Multi-Bookmaker-1X2-Quoten (B365, BW, IW, PS, WH, VC). Also auch **historische Closing-Odds** für CLV-/Devig-Training.

Lader: [data/loader.py](../src/football_betting/data/loader.py) → `Match`-Objekte.

## 2. Sofascore-Daten (Real-xG, Lineups, Statistiken)

Pfad: [data/sofascore/](../data/sofascore/) — Scraper: [scraping/sofascore.py](../src/football_betting/scraping/sofascore.py) (curl_cffi, chrome120-Impersonation)

| Liga | 21/22 | 22/23 | 23/24 | 24/25 |
|---|---|---|---|---|
| PL | ✅ | ✅ | ✅ | ✅ |
| CH | ✅ | ✅ | ✅ | ✅ |
| SA | ✅ | ✅ | ✅ | ✅ |
| LL | ✅ | ✅ | ✅ | ✅ |
| **BL** | ❌ | ❌ | ❌ | ✅ (+ baseline) |

> ⚠️ **Lücke:** Bundesliga-Sofascore-Daten fehlen für die Saisons 2021/22 – 2023/24. Real-xG / Squad-Quality-Features starten für BL erst mit 2024-25 — deshalb ist `has_real_xg = 0` für jede BL-Vorhersage vor diesem Zeitpunkt.

Pro Match enthalten:
- `home_xg` / `away_xg` (Sofascore Live-xG)
- `home_shots` / `home_shots_on_target`
- `home_big_chances` / `away_big_chances`
- `home_avg_rating` / `away_avg_rating` (Sofascore Player-Ratings)
- `home_starting_xi` / `away_starting_xi` (Player-IDs für Squad-Tracker)

Caches: `cache.sqlite` (Event-Lookup) + `logs/`.

## 3. Odds-Snapshots (Marktverlauf)

### 3a. Historischer Pre-Game-Pool — `data/odds_snapshots/*.parquet`

| Liga | 23/24 | 24/25 |
|---|---|---|
| PL | ✅ | ✅ |
| CH | ✅ | ✅ |
| BL | ✅ | ✅ |
| SA | ✅ | ✅ |
| LL | ✅ | ✅ |

> Nur **2 Saisons** vorhanden — vor 2023-24 keine Marktverlauf-Daten. `_credits.json` zeigt 13 340 verbrauchte Credits im April 2026.

Diese Daten speisen den `MarketMovementTracker` und damit die `mm_*`-Features (welche im Value-Modell **nicht** verwendet werden — siehe [ValueModelConfig](../src/football_betting/config.py#L178-L196)). Für die Value-Pipeline daher **nur indirekt** relevant: zur **CLV-Auswertung** und zum **Devigging** historischer Märkte.

### 3b. Live-Snapshots — `data/snapshots/odds_<LG>.jsonl`

| Liga | Zeilen |
|---|---|
| PL | 25 |
| CH | 28 |
| BL | 12 |
| SA | 10 |
| LL | 12 |

Format pro Zeile:
```json
{"league":"PL","date":"2026-04-18","home":"Arsenal","away":"Chelsea",
 "timestamp":"2026-04-18T14:54:54","home_odds":1.85,"draw_odds":3.75,
 "away_odds":4.2,"bookmaker":"avg"}
```

**Sehr klein** — wächst nur seit aktivem Tracking (Paid-Plan Start ~2026-04-20). Für robustes Movement-Training nicht ausreichend.

## 4. Wetter-Cache

Pfad: [data/weather/cache.sqlite](../data/weather/) — Open-Meteo-Antworten pro Stadion/Kickoff. Gespeist von [features/weather.py](../src/football_betting/features/weather.py). Stadion-Koordinaten in [data/stadiums.json](../data/stadiums.json).

Liefert: Temperatur, Niederschlag, Windgeschwindigkeit, Schnee. Wird als opt-in Feature-Familie getriggert.

## 5. Live-Tracking & Ergebnishistorie (für Value-Bet-Evaluation)

| Datei | Zeilen | Zweck |
|---|---|---|
| [data/predictions/predictions_log.json](../data/predictions/predictions_log.json) | 946 | Persistierte Vorhersagen mit Stake / Edge / Outcome |
| [data/graded_bets.jsonl](../data/graded_bets.jsonl) | 25 | Settled Value- + 1X2-Bets mit `kind`-Diskriminator, `pnl` |
| [data/live_scores.jsonl](../data/live_scores.jsonl) | 58 | Odds-API Live-Resultate für Self-Healing-Grading |
| [data/snapshots/today.json](../data/snapshots/today.json) | – | Aktueller Snapshot (Vorhersage + Value-Bets) |
| [data/snapshots/2026-04-*.json](../data/snapshots/) | 7 Tage | Tagesarchiv (regradet) |
| [data/predictions/performance.json](../data/predictions/performance.json) | – | Anonymisierte Index-Kurve fürs Frontend |

Graded-Bet-Beispiel (Trainingssignal für Value-Modell):
```json
{"date":"2026-04-18","league":"PL","outcome":"A","bet_label":"Brighton Auswärtssieg",
 "odds":2.195,"stake":33.26,"ft_result":"D","ft_score":"2-2","status":"lost",
 "pnl":-33.26,"kind":"value","model_prob":0.528}
```

**Bewertung:** Die graded/live-Bestände sind **klein** (25 graded Bets, 58 live scores) und erst nach dem Dual-Model-Cutoff am **2026-04-15** ([VALUE_SNAPSHOT_CUTOFF](../src/football_betting/api/services.py#L1251)) für die neue Value-Pipeline gültig. Davor: 5-tägige interne Backtest-Baseline mit 58 Bets / 1139 € Stake / +642 € P/L (siehe [VALUE_SNAPSHOT_BASELINE](../src/football_betting/api/services.py#L1266-L1274)).

## 6. Backtest-Artefakte

Pfad: [data/backtests/](../data/backtests/)

| Datei | Inhalt |
|---|---|
| `backtest_PL.json` | 380 preds / 286 bets / RPS 0.211 / ROI -0.230 / CLV-Mean -0.025 |
| `backtest_BL.json` | analog |
| `backtest_SA.json` | analog |
| `backtest_LL.json` | analog |
| `walk_forward_BL.json` | Walk-Forward-Detail-Lauf (BL) |

> ⚠️ **CH fehlt** — kein Backtest-Artefakt. ROIs sind durchwachsen → klares Optimierungsfeld.

Liefern u. a. `mean_brier`, `mean_log_loss`, `mean_rps`, `clv_mean`, `clv_pct_positive`, `max_drawdown_pct`. Eingang für die Ensemble-Weight-Tuner ([predict/weights.py](../src/football_betting/predict/weights.py), [predict/ensemble.py](../src/football_betting/predict/ensemble.py)).

## 7. Feature-Vektor des Value-Modells

Aus [models/catboost_PL_value.features.txt](../models/catboost_PL_value.features.txt) und [models/mlp_PL_value.meta.json](../models/mlp_PL_value.meta.json):

- **CatBoost**: 81 Features
- **MLP**: 73 numerische Features (aus 81 nach Embedding-/Categorical-Strip)
- **1X2-Pendant**: 92 Features (zusätzlich `market_*` + `mm_*`)

Familien:
- Pi-Ratings (9): `pi_home_*`, `pi_away_*`, `pi_diff_*`, `pi_expected_gd`
- Form (14): `form_home_*`, `form_away_*`, Diffs, At-Home/At-Away-Splits
- xG-Proxy (9): `xg_home_*`, `xg_away_*`, `xg_matchup_diff`
- Real-xG (14): `real_xg_*` + `has_real_xg`
- Squad (8): `squad_home_rating`, `squad_*_rotation`, `squad_*_key_absences`
- H2H (8): `h2h_*`
- Rest (5): `rest_home_days`, `rest_*_fatigue`, `rest_diff`
- Home-Advantage (2): `home_team_ha`, `home_team_ha_vs_default`
- League-Meta (2): `league_avg_goals`, `league_home_adv`
- Punktabzüge (2): `home_point_ded`, `away_point_ded`
- (Wetter-Familie nur wenn opt-in aktiv)

> 🚫 Bewusst **ausgeschlossen** beim Value-Modell: `market_p_home/draw/away`, `market_margin`, `market_fav_ratio`, sämtliche `mm_*`. Begründung: das Modell muss den Markt **schlagen**, nicht imitieren.

## 8. Bestehende trainierte Artefakte

[models/](../models/)

| Liga | CatBoost (1X2) | CatBoost (value) | MLP (value) | Sequence (value) | Ensemble-Profile |
|---|:---:|:---:|:---:|:---:|:---:|
| PL | ✅ | ✅ | ✅ | ✅ | `model_profile_PL_value.json` |
| CH | ✅ | ✅ | ✅ | ✅ | ✅ |
| BL | ✅ + baseline | ✅ | ✅ | ✅ | ✅ |
| SA | ✅ | ✅ | ✅ | ✅ | ✅ |
| LL | ✅ | ✅ | ✅ | ✅ | ✅ |

Pro Modell zusätzlich: Calibrator (`*.calibrator.joblib`), Feature-Liste, Metadaten, ggf. `*.kelly.*`-Variante (Kelly-Loss-Phase). Pro Liga ein Profil + Ensemble-Gewichte (z. B. PL value: `w_catboost=0.114, w_poisson=0.746, w_mlp=0.031, w_sequence=0.110`, Objective = `clv`).

## 9. Bewertung — Lücken & Optimierungspotenzial

### Stärken
- ✅ **5 Saisons Match-Historie × 5 Ligen** mit Multi-Bookmaker-1X2-Quoten
- ✅ Sofascore-Real-xG/Lineups für 4/5 Ligen × 4 Saisons
- ✅ Vollständige Modell-Familie (CatBoost + Poisson + MLP + Sequence) für alle Ligen
- ✅ Walk-Forward-Backtest-Pipeline + CLV-Tuning aktiv

### Lücken
- ❌ **BL-Sofascore vor 2024-25 fehlt** → Real-xG/Squad-Features taub für 3 Saisons in BL
- ❌ **Odds-Movement-Daten erst ab 2023-24** → mm_*-Familie für PL/CH/BL/SA/LL nur 2 Saisons (für Value-Modell ohnehin geblockt, aber für CLV-Eval limitiert)
- ❌ **Live graded_bets.jsonl mit nur 25 Zeilen** → echte Live-Validierung der neuen Value-Pipeline noch unterdimensioniert (Backtest-Baseline + 9 Tage Live)
- ❌ **CH-Backtest-Artefakt fehlt**
- ❌ **Closing-Odds-Snapshots** werden zwar in `MarketMovementTracker` gefüttert, aber kein dedizierter "Closing-Line"-Store je Match → CLV-Berechnung läuft auf der `bet_odds`-vs-`market_avg`-Heuristik
- ❌ **Predictions-Log carries `Poisson+PiRatings` als `model_name`** für 2026-04-18 Einträge → für die Phase vor Dual-Model-Rollout dokumentiert, dass damals noch das Fallback aktiv war

### Konkrete Optimierungs-Hebel
1. **BL-Sofascore-Backfill** für 2021/22, 2022/23, 2023/24 → einheitliche Real-xG-Coverage. Roadmap-Memo `project_training_roadmap`: *Historical-Retrain via separates Odds-API-Abo* unterstützt das.
2. **Mehr Live-graded-Bets** aufbauen (Pre-publish-Polling der Roadmap) → robustes Live-Reward-Signal statt nur 5-Tage-Baseline.
3. **Dedizierter Opening + Closing Snapshot-Store** je Match (statt nur Pool-Parquet) → präzises CLV-Training für Kelly-Loss-Variante.
4. **CH-Backtest erzeugen** (`scripts/backtest.py --league CH`) → Lücke schließen, Ensemble-Weights für CH valide tunen.
5. **Wetter-Daten** sind bereits gecached, aber `use_weather` ist opt-in — A/B-Test gegen Hold-out könnte zeigen, ob es das Value-Modell verbessert.

## 10. Datenfluss in die Trainings-Pipeline (Querverweis)

```
data/raw/<CODE>_<SS>.csv  ──┐
                            ├─► load_league() ──► List[Match]
data/sofascore/*.json     ──┤                       │
                            │                       ▼
data/odds_snapshots/*.pq  ──┤      stage_sofascore_batch()
                            │                       │
data/weather/cache.sqlite ──┘                       ▼
                                       FeatureBuilder.fit_on_history()
                                                    │
                                                    ▼
                                  scripts/train.py / tune_ensemble.py
                                                    │
                                                    ▼
                              models/{catboost,mlp,sequence}_<LG>_value.{cbm,pt}
                              models/ensemble_weights_<LG>_value.json
                              models/model_profile_<LG>_value.json
```

Trainingsskripte:
- [scripts/train.py](../scripts/train.py) — Haupt-Trainer (CatBoost + MLP + Sequence)
- [scripts/tune_ensemble.py](../scripts/tune_ensemble.py) — Dirichlet-Weight-Tuner
- [scripts/tune_twohead.py](../scripts/tune_twohead.py) — Two-Head-Variante
- [scripts/train_phase5_rollout.py](../scripts/train_phase5_rollout.py) — Phase-5-Sequenz
- [scripts/_backtest_value_5d.py](../scripts/_backtest_value_5d.py) — 5-Tages-Value-Backtest
- [scripts/promote_kelly_models.py](../scripts/promote_kelly_models.py) — Kelly-Variante in Produktion heben
