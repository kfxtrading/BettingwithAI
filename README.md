# Football Betting Model — v0.3

CatBoost + PyTorch MLP + pi-Ratings + Sofascore-Daten — Wettmodell für Top-5-Ligen
(EPL, EFL Championship, Bundesliga, Serie A, La Liga).

## What's new in v0.3

See [CHANGELOG.md](CHANGELOG.md). Highlights:

- **70+ Features** (v0.2: 56, v0.1: 14)
- **Echtes xG via Sofascore** — ersetzt Schuss-Proxy wenn Daten vorhanden
- **Squad-Quality-Features** — Starting-XI-Rating, Key-Player-Absence-Detection
- **Market-Movement-Tracking** — Steam-Moves, Sharp-Money-Indicator
- **PyTorch MLP** — 3. Ensemble-Member neben CatBoost + Poisson
- **Dirichlet-Sampling** — effizienteres Weight-Tuning für 3-Way-Ensemble
- **Data-Drift-Monitoring** — KS-Test-basierte Feature-Drift-Detection

## Setup

```bash
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
pip install -e ".[ml,dev]"     # inkl. PyTorch + ONNX
```

## Workflow

### 1. Football-Data-CSVs herunterladen
```bash
fb download --league all
```

### 2. Sofascore-Daten scrapen (v0.3, optional aber empfohlen)
```bash
export SCRAPING_ENABLED=1
fb scrape --league BL --seasons 2024-25 2025-26
```

⚠️ **Scraper ist rate-limited** (25 Sekunden pro Request). Eine volle Saison dauert
ca. 3-4 Stunden. Daten werden in SQLite gecacht — spätere Läufe sind schnell.

### 3. CatBoost trainieren
```bash
fb train --league BL --use-sofascore
```

### 4. MLP trainieren (v0.3, optional)
```bash
fb train-mlp --league BL
```

### 5. Ensemble-Gewichte tunen (v0.3: Dirichlet)
```bash
fb tune-ensemble --league BL --val-season 2024-25
```

### 6. Backtest
```bash
fb backtest --league BL
```

### 7. Heutige Spiele vorhersagen
```bash
fb predict --fixtures data/fixtures_2026-04-18.json --bankroll 1000
```

### 8. Ergebnisse nachtragen
```bash
fb update-results --results-file data/results_2026-04-18.json
```

### 9. Drift-Report (v0.3)
```bash
fb monitor --league BL --recent-days 30
```

### 10. MLP als ONNX exportieren (Production)
```bash
fb export-onnx --league BL
```

## Architektur

```
src/football_betting/
├── config.py                    # v0.3: +4 Configs (Sofascore, MLP, Monitoring, EnsembleTune)
├── cli.py                       # 12 Commands
├── data/                        # Match, Fixture Models + CSV Loader
├── rating/                      # Pi-Ratings
├── scraping/                    # 🆕 v0.3
│   ├── sofascore.py             # Async-Client mit Retry + Browser-Headers
│   ├── rate_limiter.py          # Thread-safe Token-Bucket
│   └── cache.py                 # SQLite TTL-Cache
├── features/                    # 70+ Features
│   ├── form.py                  # v0.2: Exp-Decay Form
│   ├── xg_proxy.py              # v0.2: Schuss-basiert (Fallback)
│   ├── real_xg.py               # 🆕 v0.3: Sofascore xG
│   ├── squad_quality.py         # 🆕 v0.3: Lineups + Ratings
│   ├── market_movement.py       # 🆕 v0.3: Odds-Drift
│   ├── h2h.py                   # v0.2
│   ├── rest_days.py             # v0.2
│   ├── home_advantage.py        # v0.2
│   └── builder.py               # Orchestrator (v0.3 update)
├── predict/
│   ├── poisson.py               # Dixon-Coles
│   ├── catboost_model.py        # CatBoost + Calibration
│   ├── mlp_model.py             # 🆕 v0.3: PyTorch MLP
│   ├── calibration.py           # v0.2: Isotonic/Platt
│   └── ensemble.py              # v0.3: 3-Way Dirichlet-tuned
├── betting/                     # Kelly, Margin, ValueBet
└── tracking/
    ├── metrics.py               # RPS, Brier, CLV, Sharpe, Drawdown
    ├── tracker.py               # Persistence
    ├── backtest.py              # Walk-Forward
    └── monitoring.py            # 🆕 v0.3: Drift-Detection

scripts/
├── train.py, backtest.py
├── tune_ensemble.py
└── predict_today.py

tests/ (80+ Tests)
├── test_pi_ratings.py, test_poisson.py, test_betting.py
├── test_features.py, test_calibration.py
├── test_scraping.py             # 🆕 v0.3
├── test_v03_features.py         # 🆕 v0.3
└── test_monitoring.py           # 🆕 v0.3
```

## Feature Inventar (70+)

| Kategorie | Count | v0.3 |
|-----------|-------|------|
| Pi-Ratings | 9 | ↔ |
| Form (Home/Away-Split) | 15 | ↔ |
| xG (Proxy oder Real) | 9-13 | 🆕 Real xG |
| Squad Quality | 8 | 🆕 |
| Market Movement | 6 | 🆕 |
| H2H | 8 | ↔ |
| Rest Days | 5 | ↔ |
| Home Advantage | 2 | ↔ |
| League Meta | 2 | ↔ |
| Market Odds | 5 | ↔ |
| Point Deductions | 2 | ↔ |

## Performance-Ziele

| Liga | v0.1 | v0.2 | v0.3 | Bookmaker |
|------|------|------|------|-----------|
| EPL | 0.195 | 0.189 | **0.186** | 0.191 |
| Bundesliga | 0.196 | 0.190 | **0.187** | 0.193 |
| Serie A | 0.197 | 0.192 | **0.189** | 0.194 |
| La Liga | 0.198 | 0.193 | **0.190** | 0.194 |
| Championship | 0.199 | 0.193 | **0.191** | 0.196 |

ECE-Ziel: **<1.5%** nach Calibration (v0.2: <2%).

## Wichtiger Hinweis zu Sofascore

Sofascore hat keine offiziell lizenzierte API. Der Scraper in v0.3 ist für
**persönliche Forschung** gedacht:

- **Opt-In nur** via `SCRAPING_ENABLED=1` Environment-Variable
- **25 Sekunden zwischen Requests** (konservativ)
- **SQLite-Cache** minimiert wiederholte Anfragen
- **User-Agent-Rotation**

Für kommerzielle/Production-Nutzung bezahlte API wie API-Football, Sportmonks,
oder StatsBomb Open Data empfehlen.

## Theoretischer Hintergrund

- **Pi-Ratings**: Constantinou & Fenton (2013)
- **Dixon-Coles**: Dixon & Coles (1997)
- **Kelly Criterion**: Kelly (1956)
- **CatBoost**: Prokhorenkova et al. (2018)
- **Isotonic Calibration**: Zadrozny & Elkan (2002)
- **Platt Scaling**: Platt (1999)

## Web Interface — Betting with AI

Eine designorientierte Homepage (Jony Ive / ARC Browser Ästhetik) zeigt heutige
Vorhersagen, Value Bets, ein Performance-Dashboard und Liga-/Team-Übersichten.
Die Seite kommuniziert über eine FastAPI-Schicht mit dem ML-Backend.

### Architektur

```
src/football_betting/api/   # FastAPI: schemas, services, routes, app
web/                        # Next.js 14 (App Router, TypeScript, Tailwind)
data/snapshots/             # vorberechnete today.json + per-league JSON
```

### Setup & Start

**Backend (Shell 1):**

```bash
pip install -e ".[api]"
fb snapshot                                  # nimmt automatisch das neueste data/fixtures_*.json
fb serve                                     # http://localhost:8000  (/docs für OpenAPI)
```

`fb snapshot` nutzt den vorhandenen Predict-Pipelinecode. Wenn noch kein
CatBoost trainiert wurde, fällt es auf den Poisson-Baseline zurück — die UI
funktioniert end-to-end nach `fb download`.

**Frontend (Shell 2):**

```bash
cd web
npm install
cp .env.local.example .env.local
npm run dev                                  # http://localhost:3000
```

### Preview direkt aus VS Code

Alle nötigen Tasks und Launch-Configs liegen bereits in `.vscode/`.

1. `Ctrl+Shift+P` → **Tasks: Run Task** → **dev: all**
   Startet FastAPI und den Next.js-Dev-Server parallel in zwei Terminal-Panels.
   (Beim ersten Mal stattdessen **dev: full bootstrap** wählen — installiert
   npm-Deps, erzeugt den heutigen Snapshot und startet beide Server.)
2. Sobald `http://localhost:3000` im Next-Terminal erscheint:
   `Ctrl+Shift+P` → **Simple Browser: Show** → `http://localhost:3000`.
   Die Homepage läuft danach im VS-Code-Tab daneben — Hot-Reload bleibt aktiv.
3. Alternative per **Run & Debug** (F5):
   - **Dev: Full Stack (API + Web)** → startet API (mit Debugger) + Next.js
     parallel in je einem Terminal; sobald Next.js ready ist, öffnet sich
     automatisch der Browser auf `http://localhost:3000`.
   - **API: Debug FastAPI** → nur Backend mit Breakpoints.
   - **Web: Next Dev** → nur Frontend (ohne Debugger-Attach).

> **"Go Live"** (Live Server Extension) funktioniert hier nicht — sie serviert
> statische HTML-Files. Next.js hat seinen eigenen Dev-Server mit Hot-Reload;
> nutze daher `web: dev` oder die Run-&-Debug-Configs oben.

Die empfohlenen Extensions (`.vscode/extensions.json`) liefern zusätzlich
Tailwind-IntelliSense und ESLint-Integration.

### Endpoints (Auswahl)

| GET | Beschreibung |
|---|---|
| `/health` | Modellverfügbarkeit, Snapshot-Status |
| `/leagues` | Liga-Stammdaten |
| `/predictions/today?league=PL` | Heutige Vorhersagen + Value Bets |
| `/leagues/{key}/ratings` | Pi-Ratings-Tabelle |
| `/performance/summary` | ROI, Trefferquote, Drawdown |
| `/performance/bankroll` | Bankroll-Verlauf |

## Lizenz

MIT
