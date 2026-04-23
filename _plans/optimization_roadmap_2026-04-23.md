# Optimierungs-Roadmap (Stand 23. April 2026, nach CLV-Tuning)

**Kontext:** CLV ist nach Fix der Snapshot-Kontamination (Commit `24d1548d`) und CLV-objektivem Ensemble-Tuning (Commits `5a525804` + `8ede7c87`) über alle 5 Ligen positiv:

| Liga | mean CLV (val 2024-25) | n |
|------|------------------------|---|
| BL   | +0.64%                 | 255 |
| CH   | +0.14%                 | 490 |
| LL   | +0.91%                 | 355 |
| PL   | +1.17%                 | 303 |
| SA   | +1.63%                 | 341 |

Jetzt ist der positive CLV ehrlich und reproduzierbar. Die folgenden sechs Phasen bauen darauf auf, priorisiert nach erwartetem ROI ÷ Aufwand.

---

## Phase 1 — Weather-Wiring fertigstellen (Familie A)

**Status:** 70% fertig, wartet auf Integration.
**Aufwand:** 1–2 h
**Erwartung:** 5–15 bp RPS-Verbesserung pro Liga, stärker in PL/SA wegen Saisonextrema.

### Befund (Audit)
- `WeatherTracker`, `OpenMeteoClient`, 24 MB SQLite-Cache, `FeatureBuilder`-Integration und `fb weather-stadiums`-CLI existieren.
- Aber: `fb train` übergibt keinen `weather_tracker` → alle 5 CatBoost-Modelle haben **84 Features, davon 0 `weather_*`**.
- Die Vorhersagen sehen Temp/Regen/Wind/WBGT/Druck aktuell gar nicht.

### Aufgaben
- [ ] In `cli.py` (`fb train`, `fb train-tab`, `fb train-seq`, `fb backtest`) `WeatherTracker(…)` instanziieren und an `FeatureBuilder(..., weather_tracker=…)` übergeben
- [ ] Dasselbe in `api/services.py._build_feature_builder`
- [ ] Alle 5 CatBoost-Modelle neu trainieren → Feature-Liste wächst auf ~93
- [ ] Kalibrierung neu anwerfen (`fb calibrate` je Liga)
- [ ] CLV-Tuning neu (`fb tune-ensemble --league all --objective clv`) → Gewichte persistieren überschreibt `ensemble_weights_*.json`
- [ ] Delta-Backtest: RPS vor/nach Weather, Liga für Liga

### Akzeptanz
- Mindestens 3/5 Ligen mit RPS-Δ > 2 bp und CLV-Δ ≥ 0
- Falls Weather schadet (RPS-Regression): Feature-Importance prüfen, evtl. nur `weather_temp_c`, `weather_precip_mm`, `weather_wind_kmh` zulassen

---

## Phase 2 — MLP-Checkpoint-Fix + 4-way-Ensemble

**Status:** MLP aktuell in allen Ensembles mit `w_mlp=0.0` deaktiviert wegen PyTorch-2.6-Inkompatibilität.
**Aufwand:** 30 min
**Erwartung:** moderater RPS-Gewinn v.a. CH/LL/SA (dort war MLP historisch stark).

### Befund
`torch.load()` defaultet seit 2.6 auf `weights_only=True` und weigert sich, `numpy._core.multiarray._reconstruct` zu deserialisieren. Betrifft alle `mlp_*.pt` Checkpoints.

### Aufgaben
- [ ] In `predict/mlp_model.py` → `torch.load(path, map_location=..., weights_only=False)` (wir haben die Checkpoints selbst erzeugt, sind trusted), alternativ `torch.serialization.add_safe_globals([numpy._core.multiarray._reconstruct])` + `weights_only=True`
- [ ] `fb tune-ensemble --objective clv` neu je Liga, jetzt mit 4-way Simplex (CB + Po + MLP + Seq)
- [ ] Vergleich: CLV 3-way vs. 4-way je Liga

### Akzeptanz
- MLP lädt fehlerfrei über alle 5 Ligen
- 4-way CLV ≥ 3-way CLV in mindestens 3/5 Ligen

---

## Phase 3 — Weather Shock (Familie B: „Saudi-Arabien-Effekt")

**Status:** `use_weather_shock=False`, nicht implementiert.
**Aufwand:** 3–4 h
**Erwartung:** punktueller Edge-Gain bei Champions-League- und Winter-Warmwetter-Kombinationen. In den 5 Top-Ligen selten, aber wo er auftritt groß.

### Aufgaben
- [ ] Klima-Baseline pro Team-Heimatstadt aus Open-Meteo Archiv (saisonaler Mittelwert der letzten 3 Jahre pro Monat) in `features/weather.py` cachen
- [ ] 5 neue Features bauen:
  - `weather_shock_home_temp` = Spielort-Temp − Heimatklima Heimteam
  - `weather_shock_away_temp` = Spielort-Temp − Heimatklima Auswärtsteam
  - `weather_shock_away_humid` = Humidity-Delta Auswärtsteam
  - `weather_shock_away_magnitude` = gewichtete L2-Norm aller Deltas Auswärtsteam
  - `weather_travel_climate_diff` = Klimadifferenz Auswärtsteam-Stadt ↔ Spielort
- [ ] `WeatherConfig.use_weather_shock = True`
- [ ] Alle Modelle retrain + calibrate + tune-ensemble
- [ ] Feature-Importance-Report → sind Shock-Features relevant, oder nur 2024-25-Zufall?

### Akzeptanz
- RPS-Δ > 0 auf Holdout und Walk-Forward (Phase 6), nicht nur 2024-25
- Mindestens 1 Shock-Feature in den Top-20 CatBoost-Importances

---

## Phase 4 — Daily Opening-Odds Workflow aktivieren (Production-Hygiene)

**Status:** GitHub Actions Workflow [.github/workflows/snapshot-opening-odds.yml](.github/workflows/snapshot-opening-odds.yml) gedeployt aber inaktiv (kein `ODDS_API_KEY` Secret).
**Aufwand:** 5 min (manuell, extern).
**Erwartung:** Ohne das läuft CLV in 2–3 Wochen wieder stale, weil keine neuen Opening-Lines mehr einkommen.

### Aufgaben
- [ ] GitHub → Settings → Secrets and variables → Actions → `New repository secret`
  - Name: `ODDS_API_KEY`
  - Value: aktueller Odds-API-Key
- [ ] Manuell triggern: Actions → „Snapshot opening odds (T-48h)" → `Run workflow`
- [ ] Nach 24 h: `fb snapshot-freshness-audit --league all` → Verdict sollte bei neuen Fixtures auf **green OK** springen

### Akzeptanz
- Workflow läuft grün im 06:00-UTC-Cron
- `data/snapshots/odds_*.jsonl` bekommt täglich neue Zeilen mit Lead ≥ 24h für kommende Spiele

---

## Phase 5 — Multi-fold Walk-Forward Robustheits-Check

**Status:** Aktuelle CLV-Zahlen nur auf Validation-Season 2024-25 belegt.
**Aufwand:** 2–3 h + CSV-Download.
**Erwartung:** Reality-Check. Falls CLV auf älteren Folds negativ ist, ist das aktuelle +0.14…+1.63% teilweise Overfitting.

### Aufgaben
- [ ] `fb download --league all --seasons 2019-20,2020-21` (Fußball-Daten CSVs)
- [ ] `fb backtest --league all --walk-forward --folds 5` (rolling train 4 Seasons → val 1 Season)
- [ ] CLV pro Fold je Liga tabellieren
- [ ] Stabilitäts-Metrik: `mean(CLV_folds) - 1.5*std(CLV_folds)` muss > 0 bleiben (Lower-Confidence-Bound)

### Akzeptanz
- LCB-CLV > 0 in mindestens 3/5 Ligen
- Kein Fold mit CLV < -1.5% in irgendeiner Liga

---

## Phase 6 — Simons/Paris-Signal (Familie C, Kontrollhypothese)

**Status:** `use_simons_signal=False`, bewusst zurückgestellt.
**Aufwand:** 2 h
**Erwartung:** **wahrscheinlich null Prognose-Wert.** Das ist der Punkt — wir testen die Hypothese, wir glauben sie nicht.

### Wissenschaftlicher Kontext
Mercer (Renaissance Tech) fand sonniges Morgenwetter in Börsenstädten → leicht positive Tagesrendite. Hirshleifer & Shumway (2003) bestätigten es an 26 Börsen. Bei Fußball ist der Mechanismus (Spielerleistung) direkter, aber das Paris-Signal selbst hat keinen kausalen Bezug zum Spielort. Wenn es „funktioniert", ist das fast sicher Multiple-Testing-Artefakt (bei 90+ Features wird eines immer zufällig signifikant).

### Aufgaben
- [ ] In `features/weather.py` Familie C aktivierbar machen
- [ ] 3 neue Features:
  - `simons_paris_sunny_morning` = Sonnenscheindauer Paris 6-9 UTC
  - `simons_paris_pressure` = Luftdruck Paris zum Spieltag
  - `simons_paris_temp_anomaly` = Temp-Abweichung Paris vom saisonalen Mittel
- [ ] **Separat loggen** in der Feature-Importance: Beitrag zu RPS isoliert reporten
- [ ] Permutation-Test: 1000× Shuffle der Paris-Features, vergleiche echten RPS-Gain mit Null-Verteilung
- [ ] Falls p > 0.05 → deaktiviert lassen, als wissenschaftliche Dokumentation belassen

### Akzeptanz
- Dokumentierte Null-Hypothese bestätigt oder verworfen
- Bei Verwerfung: permutation-p < 0.01 erforderlich, sonst bleibt es ein Overfitting-Verdacht

---

## Abhängigkeiten und Reihenfolge

```
Phase 4 (Secret)  —— unabhängig, sofort ——▶ CLV bleibt langfristig ehrlich
Phase 1 (Weather A) ──▶ Phase 3 (Weather B) ──▶ Phase 6 (Weather C)
Phase 2 (MLP-Fix)    ── unabhängig von Weather
Phase 5 (Walk-Fwd) ── profitiert von 1+2+3, sollte danach laufen
```

**Empfohlene Reihenfolge:**
1. Phase 4 (5 min, extern)
2. Phase 1 (1-2 h, größter Hebel pro Zeit)
3. Phase 2 (30 min, Ensemble-Vervollständigung)
4. Phase 5 (Robustheits-Check der bisherigen Gewinne)
5. Phase 3 (erst nachdem 1+2 validiert sind)
6. Phase 6 (reine Wissenschafts-Übung, zum Schluss)
