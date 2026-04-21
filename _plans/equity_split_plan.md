# Plan — Equity-Chart / ROI / Drawdown nach Strategie splitten

## Ziel
Auf Landing-Page und `/performance`:
- **Zwei Linien** im Equity-Chart: Value Bets vs. Prognosen 1x2 (statt addiert).
- **ROI** zweimal (Value Bets, Prognosen 1x2).
- **Max-Drawdown** zweimal (Value Bets, Prognosen 1x2).
- Kombinierte Werte bleiben rückwärtskompatibel erhalten.

## Ist-Zustand
- `data/graded_bets.jsonl` trägt bereits das Feld `kind: "value" | "prediction"` (siehe `src/football_betting/evaluation/grader.py`).
- `graded_as_prediction_records()` verwirft dieses `kind` beim Mapping auf `PredictionRecord`.
- `api/services.py::get_bankroll_curve()` und `get_performance_summary()` aggregieren alles kombiniert.
- Frontend `BankrollChart`, `PerformanceTracker`, `PerformanceClient` zeigen je eine Linie / ein Set KPIs.

## Strategie
Split-Metriken direkt aus `load_graded()` berechnen (`kind` ist dort erhalten) — **kein** Schema-Change an `PredictionRecord`, keine Migration der `predictions_log.json`.

---

## Backend

### 1. `src/football_betting/api/schemas.py`
Rückwärtskompatibel erweitern.

```python
class BankrollPoint(BaseModel):
    date: str
    value: float                       # combined (legacy)
    value_bets: float | None = None
    predictions: float | None = None

class StrategyStats(BaseModel):
    n_bets: int
    hit_rate: float
    roi: float
    total_profit: float
    total_stake: float
    max_drawdown_pct: float

class PerformanceSummary(BaseModel):
    # existing combined fields unchanged
    ...
    value_bets: StrategyStats | None = None
    predictions: StrategyStats | None = None
```

### 2. `src/football_betting/api/services.py`
- Helper `_daily_pnl_by_kind()` → `(value_pnl, pred_pnl, combined_pnl)` pro Datum direkt aus `load_graded()` (pending überspringen, Legacy-Zeilen ohne `kind` als `"value"` behandeln).
- `get_bankroll_curve()` auf die drei Ströme umbauen. Gemeinsamer Anker = Tag vor dem frühesten gesetteltem Bet, alle drei Serien starten bei `initial_bankroll`. Jeder `BankrollPoint` trägt `value`, `value_bets`, `predictions`.
- `_strategy_stats(rows, series)` liefert `StrategyStats` inkl. Max-DD via bestehendem `_max_drawdown_pct()`.
- `get_performance_summary()` füllt die neuen Felder (None bei 0 Bets pro Kind); kombinierte Felder bleiben.

### 3. `src/football_betting/api/routes.py`
Kein Pfad-Change; Response-Models ziehen die Erweiterung automatisch mit.

---

## Frontend

### 4. `web/lib/types.ts`
`BankrollPoint` und `PerformanceSummary` an Backend spiegeln:

```ts
export interface BankrollPoint {
  date: string;
  value: number;
  value_bets?: number | null;
  predictions?: number | null;
}
export interface StrategyStats {
  n_bets: number; hit_rate: number; roi: number;
  total_profit: number; total_stake: number;
  max_drawdown_pct: number;
}
export interface PerformanceSummary {
  /* existing */
  value_bets?: StrategyStats | null;
  predictions?: StrategyStats | null;
}
```

### 5. `web/components/BankrollChart.tsx`
- Zwei sichtbare Linien:
  - `dataKey="value_bets"` — Akzentfarbe, Label `t('bankroll.series.valueBets')`.
  - `dataKey="predictions"` — Sekundärfarbe, Label `t('bankroll.series.predictions')`.
- `<Legend />` aktivieren; Tooltip mit series-name formatieren.
- Bestehende kombinierte `value`-Linie optional als dezente gestrichelte Linie (`strokeDasharray="4 4"`) oder ganz entfernen — Default: weglassen, da die User-Anforderung klar zwei Linien fordert.

### 6. `web/components/PerformanceTracker.tsx` (Landing)
- KPI-Block in zwei Gruppen teilen (je eigene `h3`-Überschrift via i18n):
  - **Value Bets**: Bets · Hit-Rate · ROI · Max-DD
  - **Prognosen 1x2**: Bets · Hit-Rate · ROI · Max-DD
- Grid: `grid-cols-2 md:grid-cols-4`, zwei Reihen.

### 7. `web/app/performance/PerformanceClient.tsx`
Analog: `performance.section.coreMetrics` in zwei Untergruppen (Value Bets / Prognosen 1x2). Chart nutzt die neue Multi-Serie automatisch.

### 8. `web/lib/i18n/{de,en,es,fr,it}.ts`
Neue Keys:
- `bankroll.series.valueBets`, `bankroll.series.predictions`, `bankroll.series.combined`
- `transparency.group.valueBets`, `transparency.group.predictions`
- Wiederverwendung von `kpi.roi` / `kpi.maxDrawdown` in der jeweiligen Gruppe reicht — keine eigenen Suffix-Keys nötig, da die Gruppenheader den Kontext liefern.

---

## Kritische Dateien
- [./src/football_betting/api/schemas.py](./src/football_betting/api/schemas.py)
- [./src/football_betting/api/services.py](./src/football_betting/api/services.py)
- [./web/lib/types.ts](./web/lib/types.ts)
- [./web/components/BankrollChart.tsx](./web/components/BankrollChart.tsx)
- [./web/components/PerformanceTracker.tsx](./web/components/PerformanceTracker.tsx)
- [./web/app/performance/PerformanceClient.tsx](./web/app/performance/PerformanceClient.tsx)
- [./web/lib/i18n/de.ts](./web/lib/i18n/de.ts) (+ en/es/fr/it)

## Tests
Neuer `tests/test_bankroll_split.py`:
- Gemischtes `graded_bets.jsonl` → `get_bankroll_curve()` liefert korrekte per-Kind Kurven, konsistente `value`-Summe.
- `get_performance_summary()` getrennte `StrategyStats`; Summen = kombinierte Totalsumme.
- Edge cases: nur value / nur prediction / leer / nur pending / Legacy-Zeilen ohne `kind`.

## Verifikation
1. `pytest tests/test_bankroll_split.py -v` (neu) und ganze Suite.
2. `ruff check . && mypy src`.
3. Dev-Stack via VS Code Task **dev: all**.
4. `curl http://localhost:8000/performance/bankroll` → enthält `value_bets`/`predictions` pro Punkt.
5. `curl http://localhost:8000/performance/summary` → enthält Sub-Objekte `value_bets` / `predictions` mit eigenen `roi` und `max_drawdown_pct`.
6. Browser `/` und `/performance`:
   - Chart zeigt zwei benannte Linien mit Legende und Tooltip.
   - Je Strategie ein eigenes ROI- und Max-DD-Tile.
7. Konsistenz-Check: `value_bets[-1] + predictions[-1] − 2·initial ≈ value[-1] − initial`.

## Rückwärtskompatibilität
- `BankrollPoint.value` bleibt kombinierte Bankroll — alte Clients funktionieren weiter.
- Neue Felder optional (`None` erlaubt); Legacy graded-Zeilen ohne `kind` werden als `"value"` behandelt.
