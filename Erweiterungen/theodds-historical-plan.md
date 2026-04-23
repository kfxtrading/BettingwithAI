# TheOdds API Historical — Game-Changer für Training

Die **Historical Odds API** (v4) ändert die Kalkulation komplett. Bislang
wurde `scraping/odds_api.py` nur für Live-Fixtures + Opening-Snapshots
(T-48h) genutzt. Der Historical-Endpunkt (`/v4/historical/...`) öffnet
rückwirkend einen kompletten Time-Series-Zugriff auf Quoten ab **Juni 2020**.

---

## 1. Was TheOdds Historical liefert

- **Snapshots ab Juni 2020** per
  `GET /v4/historical/sports/{sport}/odds?date=<ISO>` → beliebige
  Zeitpunkte rekonstruierbar (nicht nur Opening / Closing!)
- **Alle Bookmaker + alle Märkte**, die der API-Plan zulässt
  (`h2h`, `totals`, `spreads`, `h2h_3_way`, …)
- **Line-Movement-Granularität**, die football-data.co.uk niemals hat:
  PSCH/PSH sind nur 2 Punkte (Opening + Closing); hier bekommen wir
  **10-50 Snapshots pro Match**
- **Kosten:** 10× normale Quota pro Request — teuer, aber einmalig für
  den Backfill kalkulierbar

---

## 2. Was das für uns bedeutet

### Neue Feature-Familie D — "Market Microstructure"

| Feature | Beschreibung |
|---------|--------------|
| `mm_opening_closing_drift_h` | Echte Drift Opening → Closing (home) |
| `mm_opening_closing_drift_d` | … draw |
| `mm_opening_closing_drift_a` | … away |
| `mm_volatility_48h` | StDev der Quoten T-48h → T-0 (Steam-Move) |
| `mm_pinnacle_soft_divergence` | Median(Pinnacle) − Median(Soft-Books) |
| `mm_sharp_money_direction` | Argmax der Divergenz (+ Richtung) |
| `mm_totals_line_shift` | O/U 2.5 → 2.75 Shift-Magnitude |
| `mm_spread_line_shift` | AH-Line-Bewegung |
| `mm_n_snapshots` | Daten-Dichte (Konfidenz-Proxy) |
| `mm_time_to_kickoff_h` | Wie spät wurde der letzte Snapshot erfasst |

### Gegenüberstellung mit Sofascore

- **Sofascore** liefert **xG + Lineup-Qualität + Real-Stats**
  (bereits im `SofascoreClient` verdrahtet)
- **TheOdds** liefert **Markt-Intelligence** (wo ist das Geld?)
- **Kombiniert:** *"Team X hat xG-Überperformance +0.4 AND Sharp-Money
  kommt Richtung Away"* → starkes Regime-Shift-Signal

---

## 3. Realistische Kosten-Abschätzung

### Full Scope (5 Ligen × 5 Saisons)

```
5 Ligen × ~380 Matches × 5 Saisons × ~10 Snapshots
  = ~95.000 historische Requests
  = ~950.000 Quota-Units
```

→ **pricey**, aber einmalig. Danach nur noch Delta-Pulls für neue Matches
(T-48h → T-0 per Live-API).

### Reduced Scope (Phase 8 Vorschlag — 2 Saisons)

```
5 Ligen × ~380 Matches × 2 Saisons × ~5 Snapshots
  = ~19.000 Requests
  = ~190.000 Quota-Units
```

→ ausreichend für die erste Validierung der Familie D.

---

## 4. Prioritäten-Reihenfolge

### Phase 7.5 — GPU-Retrain (aktuell, 118 Features)

→ Baseline setzen mit Familie A + B + C + Standings.
Erst danach wissen wir, ob der neue Weather-Shock überhaupt Lift bringt.

### Phase 8 — TheOdds Historical Backfill (neu, Familie D)

1. **Backfill** 2023-24 + 2024-25 (reduced scope, ~19k Requests)
2. **Feature-Extraktion** Familie D (10 neue Features → 128 total)
3. **Ablation-Retrain:** mit vs. ohne Familie D
4. **Ehrliche Messung** des inkrementellen Lifts (ECE, RPS, ROI, CLV)

### Warum nicht jetzt alles vermischen

- Wir wissen nicht, ob Familie B/C überhaupt Lift bringt —
  muss erst backtest-validiert werden
- Historical-API-Quota ist teuer → nicht verbrennen, bevor die
  Pipeline sauber ist
- **Saubere Attribution:** Jeder Feature-Sprung bekommt seinen
  eigenen Commit + Backtest

---

## 5. Optionen

### Option A (empfohlen)
GPU-Retrain jetzt durchführen wie im
`.agent-artifacts/f7c3a9d2_gpu_retrain_plan.md` geplant →
Baseline-Metriken festhalten → dann Historical-API Phase 8 planen.

### Option B
Historical-API zuerst integrieren, Retrain verschieben →
größerer Scope, aber eine große kombinierte Verbesserung.
**Nachteil:** keine saubere Attribution des Weather-Lifts.

### Option C (parallel, effizient)
- **Hintergrund:** GPU-Retrain starten (läuft ~3 h Wall-Clock)
- **Vordergrund:** in der Zeit das Historical-Backfill-Modul
  `scraping/odds_api_historical.py` + Feature-Extraktor
  `features/market_microstructure.py` schreiben
- Nach Retrain: direkt Phase 8 Backfill starten

---

## 6. Konkrete Implementation (Phase 8)

### 6.1 Neue Dateien

```
src/football_betting/
├── scraping/
│   └── odds_api_historical.py    # Historical Snapshots Client
└── features/
    └── market_microstructure.py  # Familie D Tracker

data/
└── odds_snapshots/               # Parquet-Cache pro (league, season)
    ├── BL_2024-25.parquet
    └── ...
```

### 6.2 Config-Erweiterung (`config.py`)

```python
@dataclass(frozen=True, slots=True)
class OddsApiHistoricalConfig:
    base_url: str = "https://api.the-odds-api.com/v4"
    markets: str = "h2h,totals,spreads"
    regions: str = "eu,uk"
    snapshot_hours_before: tuple[int, ...] = (168, 72, 48, 24, 6, 1)
    # 6 Snapshots pro Match → 5 Ligen × 380 × 2 × 6 ≈ 22.800 Requests
```

### 6.3 Integration in FeatureBuilder

```python
@dataclass(slots=True)
class FeatureBuilder:
    # ... existing trackers ...
    microstructure_tracker: MarketMicrostructureTracker | None = None

    def build_features(self, ...):
        # ... existing features ...
        if self.cfg.use_market_microstructure and self.microstructure_tracker:
            feats.update(
                self.microstructure_tracker.features_for_match(
                    home, away, match_date
                )
            )
```

### 6.4 Backfill-CLI-Kommando

```bash
fb backfill-historical-odds \
    --league BL --seasons 2023-24,2024-25 \
    --snapshots 168h,72h,48h,24h,6h,1h \
    --markets h2h,totals
```

---

## 7. Erfolgskriterien Phase 8

- Mindestens **eine Liga** zeigt RPS-Verbesserung ≥ 0.5 % relativ zur
  Phase-7.5-Baseline durch Familie D
- **CLV-Lift** auf mindestens 2 von 5 Ligen (insb. BL, SA)
- **ECE-Neutralität:** Familie D darf die Kalibrierung nicht
  verschlechtern (ΔECE ≤ +0.005)
- Falls Familie D keinen Lift bringt: **feature-ablate + dokumentieren**,
  nicht in den Produktivpfad shippen

---

## 8. Risiken

1. **API-Kosten-Explosion** — Reduced Scope verwenden, nicht Full Scope.
2. **Zeit-Offset zwischen Bookmakern** — verschiedene Books liefern
   Snapshots zu unterschiedlichen Zeiten → Interpolation nötig.
3. **Team-Name-Normalisierung** — `scraping/team_names.py` bereits
   vorhanden, aber Historical-Payloads können andere Schreibweisen haben.
4. **Rate-Limit** — 10× Quota pro Historical Call; Token-Bucket-Limiter
   notwendig.
5. **Leakage-Risiko** — Snapshots **vor** Match-Kickoff klar filtern
   (nie `commence_time + Delta` in Features).

---

## 9. Follow-ups (nach Phase 8)

- **Live-Betrieb:** Delta-Pull T-48h → T-0 in `snapshot_odds` hooken →
  Familie D wird live für Value-Bet-Detection verfügbar
- **Cross-League-Transfer:** Familie D Features sind liga-unabhängig
  interpretierbar → könnte domänen-übergreifend helfen
- **Historical-API auch für andere Sportarten** (wenn Scope erweitert wird)

---

## 10. Empfehlung

**Option A** — sauber, attributierbar, minimales Risiko.
**Option C** — falls du die 3 h Retrain-Wallclock parallel nutzen willst.

**Kein Option B** — vermischt zwei große Features und verliert die
saubere Messung des Weather-Lifts.
