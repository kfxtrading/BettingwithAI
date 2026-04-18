# Plan: Performance-Index auf der Homepage (v1)

Spec: [./Erweiterungen/performance-tracker-spec.md](./Erweiterungen/performance-tracker-spec.md)

## Scope-Entscheidung für v1

Die Spec beschreibt **zwei** Sichten: (a) anonymisierter Public-Index auf der Homepage und (b) Member-Dashboard (€ + Details) hinter Login. Das bestehende Repo hat **kein Auth-System** (`web/app/performance/page.tsx` ist bereits eine öffentliche Dashboard-Seite mit Euro-Werten).

Daher v1-Umfang:

1. **Backend**: Daten-Export-Script + Public-Anonymisierungs-Endpoint `/performance/index`
2. **Frontend**: Neue Komponente `<PerformanceTracker />` als letzter Abschnitt der **Homepage** (`web/app/page.tsx`) — anonym (Index-Kurve, keine €-Werte), mit Regel-Akkordeon + Disclaimer
3. **CLI**: Neue Subcommand `fb update-performance`
4. Die bestehende `/performance`-Page bleibt unverändert als „Full-Detail"-Dashboard (dient als der in der Spec genannte Private-Teil). CSV-Export + Auth sind **v2**.

## 1. Backend

### 1.1 Neue Datei: `scripts/update_performance_index.py`
Thin wrapper im Stil von `scripts/predict_today.py` (click + rich). Ruft Logik im Package auf. Berechnet beide JSONs und schreibt sie nach `data/predictions/`:
- `data/predictions/performance.json` (anonym, Schema 5.1 der Spec)
- `data/predictions/performance_full.json` (komplett, Schema 5.2 der Spec)

### 1.2 Neue Datei: `src/football_betting/tracking/performance_index.py`
Enthält die eigentliche Logik (damit sie auch von Services + CLI importiert werden kann):

```python
INITIAL_BALANCE = 1000.0
TRACKING_START_DEFAULT = "2026-01-01"

def compute_rule_hash(cfg: BettingConfig) -> str: ...
def build_daily_equity_curve(completed: list[PredictionRecord],
                             tracking_start: str,
                             today: date) -> list[dict]:
    """Täglicher Datenpunkt (statt pro Bet) — wie in Spec 6.1 gefordert.
    An Tagen ohne Wetten bleibt Index identisch."""

def build_public_payload(...) -> dict   # Schema 5.1
def build_private_payload(...) -> dict  # Schema 5.2
def write_performance_files() -> tuple[Path, Path]
```

Wiederverwendet:
- `ResultsTracker.completed_bets()` / `roi_stats()` aus [./src/football_betting/tracking/tracker.py](./src/football_betting/tracking/tracker.py)
- `max_drawdown()` aus [./src/football_betting/tracking/metrics.py](./src/football_betting/tracking/metrics.py)
- `BETTING_CFG`, `PREDICTIONS_DIR` aus [./src/football_betting/config.py](./src/football_betting/config.py)

### 1.3 Neue API-Route: `GET /performance/index` (public, anonym)
- Datei: [./src/football_betting/api/routes.py](./src/football_betting/api/routes.py) — Route ergänzen
- Datei: [./src/football_betting/api/services.py](./src/football_betting/api/services.py) — neue Funktion `get_performance_index() -> PerformanceIndexOut`
- Liest `data/predictions/performance.json`. Wenn Datei fehlt → on-the-fly aus `ResultsTracker` berechnen (damit das Feature sofort ohne Cron läuft).
- Cache via vorhandenem `api.cache` (TTL 3600s)

### 1.4 Neue Schemas
Datei: [./src/football_betting/api/schemas.py](./src/football_betting/api/schemas.py)
```python
class EquityIndexPoint(BaseModel):
    date: str
    index: float
    n_bets_cumulative: int

class PerformanceIndexOut(BaseModel):
    updated_at: str
    tracking_started_at: str
    n_bets: int
    hit_rate: float | None
    current_index: float
    all_time_high_index: float
    max_drawdown_pct: float
    current_drawdown_pct: float
    equity_curve: list[EquityIndexPoint]
    rule_hash: str
    model_version: str
```

### 1.5 CLI-Subcommand
Datei: [./src/football_betting/cli.py](./src/football_betting/cli.py)
```python
@main.command("update-performance")
def update_performance() -> None:
    """Regenerate performance.json + performance_full.json."""
    from football_betting.tracking.performance_index import write_performance_files
    p, pf = write_performance_files()
    console.log(f"[green]Written: {p}[/green]")
    console.log(f"[green]Written: {pf}[/green]")
```

Auch im Docstring-Index am Anfang der `cli.py` ergänzen.

## 2. Frontend

### 2.1 Types erweitern
Datei: [./web/lib/types.ts](./web/lib/types.ts) — ergänzen:
```ts
export interface EquityIndexPoint { date: string; index: number; n_bets_cumulative: number; }
export interface PerformanceIndex {
  updated_at: string;
  tracking_started_at: string;
  n_bets: number;
  hit_rate: number | null;
  current_index: number;
  all_time_high_index: number;
  max_drawdown_pct: number;
  current_drawdown_pct: number;
  equity_curve: EquityIndexPoint[];
  rule_hash: string;
  model_version: string;
}
```

### 2.2 API-Client erweitern
Datei: [./web/lib/api.ts](./web/lib/api.ts)
- `api.performanceIndex: () => request<PerformanceIndex>('/performance/index')`
- `queryKeys.performanceIndex: ['performance', 'index'] as const`

### 2.3 Neue Komponenten
Alle unter `web/components/`:
- `PerformanceTracker.tsx` — Haupt-Section, nutzt `useQuery(api.performanceIndex)`. Layout gem. Spec 7.2 (Desktop) & 7.3 (Mobile):
  - Header „Transparency Tracker / since <tracking_started_at>"
  - 3 KPI-Kacheln (reuse `<KpiTile />`): Index, Hit Rate, Bets
  - `<PerformanceIndexChart />` — 300–360 px Höhe
  - „Max Drawdown" Zeile
  - Regel-Akkordeon (siehe unten)
  - Disclaimer (Spec 9) statisch
  - CTA-Button „Full transparency →" → Link zu `/performance`

- `PerformanceIndexChart.tsx` — Recharts `<AreaChart>` (nicht LineChart, damit Gradient unter/über 100 funktioniert):
  - X-Axis: `date`, Y-Axis: `index`, Referenzlinie bei 100 (`ReferenceLine`)
  - Linie grün oberhalb 100, rot unterhalb via zwei overlayed Areas (Split bei y=100)
  - Kein Euro, keine €-Werte im Tooltip — nur `date` + `index` + `n_bets_cumulative`
  - Reuse Tailwind-Tokens (`var(--positive)`, `var(--negative)`, `var(--accent)`)
  - Frontend-Aggregation (Spec 6.1): wenn `length > 500` → wöchentlich mitteln; wenn `> 2000` → monatlich

- `RuleAccordion.tsx` — Einfaches Details/Summary-Element (kein Radix nötig — Dependencies sollen schlank bleiben). Drei Abschnitte: „Regel-Details", „Wie wird berechnet?", „Kein Finanzrat". Texte siehe Spec 2 + 9.

### 2.4 Homepage-Integration
Datei: [./web/app/page.tsx](./web/app/page.tsx) — am Ende nach dem „Today's Predictions" Section einfügen:
```tsx
<PerformanceTracker />
```

### 2.5 Styling
Keine neuen Tailwind-Tokens nötig. Die vorhandenen CSS-Variablen `--positive`, `--negative`, `--accent`, `--surface`, `--muted` reichen (vgl. [./web/tailwind.config.ts](./web/tailwind.config.ts)). Section nutzt ein etwas dunkleres Wrapper-`bg-surface-2` um sich abzusetzen, volle Seitenbreite innerhalb des bestehenden `max-w-page` Layouts.

## 3. Edge-Cases (Spec 10)

- `n_bets == 0` → Hit-Rate „—", Chart zeigt Platzhalter („Wenige Daten bisher")
- Stale Daten (`now - updated_at > 48h`) → dezenter Hinweis „Data updating" unter dem Chart
- Bet-Status `"void"` → Einsatz bleibt, zählt nicht in Hit-Rate (bereits Logik in `ResultsTracker.roi_stats`, aber nochmal prüfen)
- `current_drawdown_pct` wird **immer** gezeigt — nichts verstecken

## 4. Dateien die angefasst werden

Neu:
- [./src/football_betting/tracking/performance_index.py](./src/football_betting/tracking/performance_index.py)
- [./scripts/update_performance_index.py](./scripts/update_performance_index.py)
- [./web/components/PerformanceTracker.tsx](./web/components/PerformanceTracker.tsx)
- [./web/components/PerformanceIndexChart.tsx](./web/components/PerformanceIndexChart.tsx)
- [./web/components/RuleAccordion.tsx](./web/components/RuleAccordion.tsx)
- [./tests/test_performance_index.py](./tests/test_performance_index.py)

Edits:
- [./src/football_betting/api/schemas.py](./src/football_betting/api/schemas.py) (neue Pydantic-Modelle)
- [./src/football_betting/api/services.py](./src/football_betting/api/services.py) (+`get_performance_index`)
- [./src/football_betting/api/routes.py](./src/football_betting/api/routes.py) (+Route `/performance/index`)
- [./src/football_betting/cli.py](./src/football_betting/cli.py) (+Subcommand, Docstring)
- [./web/lib/types.ts](./web/lib/types.ts)
- [./web/lib/api.ts](./web/lib/api.ts)
- [./web/app/page.tsx](./web/app/page.tsx) (Tracker einbinden)

## 5. Verifikation

### Backend
```bash
fb update-performance               # schreibt beide JSONs
pytest tests/test_performance_index.py -v
ruff check src/football_betting/tracking/performance_index.py
mypy src
```
- Test deckt ab: equity_curve monoton pro Tag, `max_drawdown_pct` korrekt, `rule_hash` stabil, public vs private Felder (€-Werte nur in private JSON).

### API
```bash
fb snapshot && fb serve
curl http://localhost:8000/performance/index | jq .
```
Erwartung: valides PerformanceIndexOut-Payload (auch mit 0 Bets → current_index=100, hit_rate=null).

### Frontend
```bash
cd web && npm run lint && npm run type-check && npm run dev
```
Homepage öffnen → Tracker-Section unten sichtbar, Chart rendert, Hover zeigt KEINE €-Werte, Disclaimer sichtbar, Regel-Akkordeon klappt auf. Mobile-Layout via DevTools (<768px) — Kacheln stapeln sich.

### E2E-Spot-Check
Mit leerem `predictions_log.json` (0 Bets): Index-Line bleibt bei 100, Tracker zeigt „—" für Hit Rate, kein Crash.
