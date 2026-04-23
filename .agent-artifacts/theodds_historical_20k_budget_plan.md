# TheOdds Historical Backfill — 20k Credits/Monat Budget-Plan

> Folge-Plan zu `Erweiterungen/theodds-historical-plan.md` (Phase 8).
> Anpassung an reale Quota: **20.000 Credits/Monat**.

---

## 1. Status quo: Welche Daten fließen heute in Value Bets & 1x2?

### 1x2-Prognose (Feature-Pipeline)

Inputs in `features/builder.py` → Modelle (Poisson, CatBoost, MLP, TabTransformer, Ensemble):

| Feature-Familie | Quelle | Persistiert in |
|---|---|---|
| **Pi-Ratings, Form, H2H, Rest-Days, Standings, Home-Advantage** | `data/raw/*.csv` (football-data.co.uk, 5 Ligen × 5 Saisons 2021-22…2025-26) | `data/processed/` |
| **Market Odds** (`market_p_home/draw/away`, `market_margin`, `market_fav_ratio`) | CSV-Spalten PSCH/PSCD/PSCA → Bet365 → Avg (loader.py:32-39) | `Match.odds` |
| **Market Movement** (`mm_steam_detected`, `mm_home/draw/away_odds_drift`, `mm_sharp_indicator`, `mm_n_snapshots`) | **TheOdds Live-API** → `data/snapshots/odds_<LEAGUE>.jsonl` | JSONL (aktuell je Liga nur 13-38 Zeilen, letzte Wochen) |
| **xG, Real-Stats, Lineup-Qualität** | Sofascore (opt-in, 4 Saisons 2021-22…2024-25) | `data/sofascore/` |
| **Wetter** | OpenWeather | `data/weather/` |

### Value-Bet-Erkennung (`betting/value.py`)

- Nutzt **nur Closing-Quote** aus `Fixture.odds` (TheOdds-Live-Consensus, Median über Bookmaker) + Opening-Snapshot für CLV-Messung im Backtest
- Devigging via `margin.py` (power / shin / multiplicative)
- Value-Model trainiert **ohne** `market_*` + `mm_*` (Blocklist in `ValueModelConfig`) → intrinsische Features only

### Lücke
- **Keinerlei historische Quoten jenseits von PSCH/B365CH (football-data.co.uk: nur 2 Punkte: Opening + Closing)**
- Market-Microstructure-Features (`mm_*`) laufen **nur live**, weil für Trainingsdaten die Line-Movement-Historie fehlt
- In Backtests sind `mm_n_snapshots ≈ 0` → `mm_*` neutral → kein Training-Signal
- Kein Zugriff auf **Totals (O/U)** und **Asian-Handicap** überhaupt

---

## 2. Budget-Reality-Check

### Quota-Modell TheOdds Historical

`GET /v4/historical/sports/{sport}/odds?date=ISO` kostet
`10 × (regions × markets)` Credits pro Call und liefert **alle upcoming Events** des Sports zu diesem Timestamp (nicht pro Match!).

| Konfiguration | Credits/Call |
|---|---|
| `regions=eu`, `markets=h2h` | **10** |
| `regions=eu`, `markets=h2h,totals` | 20 |
| `regions=eu`, `markets=h2h,totals,spreads` | 30 |
| `regions=eu,uk`, `markets=h2h,totals,spreads` | 60 |

### Budget 20.000/Monat

| Strategie | Credits/Call | Calls/Monat |
|---|---|---|
| h2h + eu | 10 | **2.000** |
| h2h + totals + eu | 20 | 1.000 |
| h2h + totals + spreads + eu | 30 | 666 |

→ Der Plan aus `theodds-historical-plan.md` (19k Requests = 190k Credits) ist **10× zu teuer**. Wir müssen scopen.

---

## 3. Empfohlener Scope — 3 Monats-Tranchen

**Kernidee:** 1 Call pro *(Liga, Snapshot-Timestamp)* deckt alle upcoming Matches der Liga ab. Ein Spieltag = typischerweise 3-4 Tage Window → 3 Snapshots (T-168h / T-24h / T-2h) genügen für robuste Drift-Features.

### Volumenrechnung pro Saison (5 Ligen)

```
34 Spieltage × 3 Snapshots × 5 Ligen = 510 Calls/Saison
  → h2h-only:        5.100 Credits/Saison
  → h2h+totals:     10.200 Credits/Saison
  → h2h+tot+spr:    15.300 Credits/Saison
```

### 3-Monats-Roadmap

| Monat | Tranche | Calls | Credits | Rest-Budget |
|---|---|---|---|---|
| **M1** | **2 Saisons h2h-only** (2023-24 + 2024-25, 5 Ligen) | 1.020 | 10.200 | 9.800 für Live-Pulls + Experimente |
| **M2** | **1 Saison 2022-23 h2h + Totals auf BL/SA 2023-24 + 2024-25** | ~1.000 | ~14.000 | 6.000 Reserve |
| **M3** | **Spreads (AH) für BL/SA/PL 2024-25** + laufende Live-Deltas | ~800 | ~15.000 | 5.000 Reserve |

Nach 3 Monaten haben wir:
- 3 Saisons × 5 Ligen mit h2h-Microstructure (Drift, Steam, Volatilität)
- 2 Saisons mit Totals für BL/SA (für Over/Under-Value-Bets nachrüstbar)
- 1 Saison Spreads (AH-Line-Movement für Top-3-Ligen)

### Alternative "Lean" (falls Totals/Spreads niedrigere Priorität)

3 volle Saisons h2h-only in Monat 1-2 (15.300 Credits) → M3 komplett für Live-Pulls & Experimente frei.

---

## 4. Prioritäten-Begründung

1. **h2h zuerst** — direkter Lift bei 1x2-Modellen und CLV-Messung bei Value-Bets.
2. **BL + SA bevorzugt bei Totals/Spreads** — laut `theodds-historical-plan.md` Erfolgskriterien (`CLV-Lift auf mindestens 2 von 5 Ligen (insb. BL, SA)`).
3. **2024-25 > 2023-24 > 2022-23** — näher an aktueller Markt-Dynamik, bessere Generalisierung auf laufende Saison 2025-26.
4. **Nur `eu` Region** — Sharp/Soft-Divergenz ist innerhalb EU-Bookmaker bereits gut messbar; `uk` verdoppelt Quota-Kosten ohne signifikant neue Signale.

---

## 5. Technische Umsetzung

### Neue/zu ändernde Dateien

| Datei | Zweck |
|---|---|
| `src/football_betting/scraping/odds_api_historical.py` | **NEU** — Client für `/v4/historical/sports/{sport}/odds`, Token-Bucket-Limiter, Disk-Cache (Parquet), `credits_consumed`-Tracker |
| `src/football_betting/config.py` | **EDIT** — `OddsApiHistoricalConfig` mit `snapshot_hours_before = (168, 24, 2)`, `markets`, `regions`, `monthly_budget_credits = 20000` |
| `src/football_betting/features/market_microstructure.py` | **NEU** — Tracker mit Features `mm_opening_closing_drift_*`, `mm_volatility_48h`, `mm_pinnacle_soft_divergence`, `mm_sharp_money_direction`, `mm_time_to_kickoff_h` |
| `src/football_betting/features/builder.py` | **EDIT** — Opt-in-Hook `use_market_microstructure` analog zum bestehenden `use_market_movement` |
| `src/football_betting/cli.py` | **EDIT** — neues Subcommand `fb backfill-historical-odds --league BL --seasons 2024-25 --markets h2h --snapshots 168h,24h,2h --max-credits 5000` |
| `data/odds_snapshots/` | **NEU-DIR** — Parquet-Cache `{league}_{season}_{markets}.parquet`, Schema `(match_date, home, away, snapshot_ts, bookmaker, market, price_home, price_draw, price_away, line)` |
| `tests/test_odds_historical.py` | **NEU** — Mock-Responses, Budget-Guard, Parquet-Roundtrip |

### CLI-Safety-Rails

- **Budget-Guard**: Befehl bricht ab, bevor `monthly_budget_credits` überschritten wird; persistenter Counter in `data/odds_snapshots/_credits.json` (reset 1. des Monats)
- **Dry-Run** (`--dry-run`) gibt geschätzte Kosten ohne Call
- **Resume**: Parquet idempotent → schon gecachte Snapshots werden übersprungen
- **Opt-in**: nur bei `THEODDS_HISTORICAL_ENABLED=1` aktiv (analog zu `SCRAPING_ENABLED=1`)

### Integration in Training

1. `FeatureBuilder` lädt Microstructure-Features für jede Partie mit Match-Date in bereits gebackfilltem Range
2. **Saubere Attribution**: Ablation-Run mit vs. ohne `mm_*` (`fb train --feature-set baseline_plus_mm`) → ECE/RPS/CLV-Delta messen (siehe `theodds-historical-plan.md` Sektion 7)
3. Falls Lift < 0.5 % RPS: dokumentieren, nicht in Produktivpfad shippen

---

## 6. Verifikation / End-to-End-Test

1. `fb backfill-historical-odds --league BL --seasons 2024-25 --markets h2h --dry-run` → zeigt `≈204 calls × 10 credits = 2.040 credits`
2. `fb backfill-historical-odds --league BL --seasons 2024-25 --markets h2h --max-credits 2500` → echt laufen, Parquet prüfen:
   ```python
   import pandas as pd
   df = pd.read_parquet("data/odds_snapshots/BL_2024-25_h2h.parquet")
   assert {"snapshot_ts","home","away","price_home"} <= set(df.columns)
   assert df["snapshot_ts"].nunique() >= 3 * 34 - 5
   ```
3. `pytest tests/test_odds_historical.py -v` (mock-basiert, kein echter API-Call)
4. `fb train --league BL --feature-set baseline` + `fb train --league BL --feature-set baseline_plus_mm` + `fb backtest --league BL` → RPS/CLV-Delta in `baseline_metrics.md` festhalten
5. `data/odds_snapshots/_credits.json` prüfen — Soll < 20.000 im aktuellen Monat

---

## 7. Erwartete Wirkung

- **1x2**: Zusätzliche Feature-Familie D (8-10 Features) → Ziel ≥ 0.5 % RPS-Lift auf ≥ 1 Liga
- **Value Bets**: Microstructure-Features bleiben im Value-Model **geblockt** (bewusst kein Market-Echo), aber Kalibrierung der 1x2-Probabilities wird besser → Edge-Schätzungen präziser → CLV-Lift auf BL/SA
- **Neue Märkte**: Mit Totals-Backfill (M2) + Spreads (M3) wird Value-Detection auf O/U und AH überhaupt erst möglich (heute komplett abwesend)

---

## 8. Risiken & Stopps

| Risiko | Mitigation |
|---|---|
| Quota-Überschreitung | Monatlicher Counter + hard-abort + `--max-credits` pro Run |
| Team-Name-Drift (Historical-Payload ≠ Live) | `scraping/team_names.py` erweitern, Mapping-Tests |
| Snapshot-Timestamp-Leakage in Trainingsfeatures | Filter `snapshot_ts < kickoff_utc` hart im Tracker |
| Kein Lift trotz Backfill | Features ablaten, Monat-3-Budget in Totals/Spreads umleiten |

---

## 9. Offene Entscheidungen für dich

1. **Lean-Pfad** (3 Saisons h2h-only in 2 Monaten) oder **Full-Pfad** (h2h + Totals + Spreads gemixt über 3 Monate)?
2. Startliga für M1-Pilot: `BL` allein (1.020 Credits) als Proof-of-Concept oder direkt alle 5 Ligen (5.100 Credits)?
3. Totals/Spreads nur für BL+SA oder auch PL?
