# Performance-Index — Feature-Spezifikation

**Status:** Spec, bereit zur Implementierung
**Version:** 1.0
**Datum:** 18. April 2026
**Zielprojekt:** Kirchhof.ai Homepage + Member-Dashboard
**Abhängigkeit:** Football Betting Model v0.3

---

## 1. Ziel

Ein Abschnitt ganz unten auf der Homepage, der die hypothetische Performance des v0.3-Modells als **anonymisierten Verlaufs-Index** zeigt. Nutzer sehen, *dass* das Modell funktioniert (oder eben nicht), ohne dass konkrete Geldbeträge oder ROI-Zahlen öffentlich preisgegeben werden.

**Entscheidung:** Option 3 (anonymisiert öffentlich) + separates **Member-Dashboard** mit vollen Details hinter Login.

### Öffentlich sichtbar
- Verlaufskurve (Performance-Index, startet bei 100)
- Anzahl bisheriger Spiele
- Trefferquote in Prozent
- Maximum Drawdown in Prozent
- Zeitraum des Trackings

### Nur hinter Login
- Absolute Beträge in Euro
- ROI-Prozentzahl
- Einzelne Wetten mit Match-Details
- Tabelle der letzten 50 Wetten
- CSV-Export

---

## 2. Die feste Regel (für alle sichtbar)

Diese Regel wird exakt so im UI dokumentiert ausgeklappt anzeigbar:

```
• Startkapital: 100 Punkte (entspricht intern € 1.000)
• Wette wird platziert, wenn:
    - Modell-Edge ≥ 3 %
    - Quote zwischen 1,30 und 15,00
    - Nur 1X2-Märkte (Heim / Unentschieden / Auswärts)
• Einsatz: Quarter-Kelly (0,25 × optimaler Kelly-Bruch)
• Hardcap: maximal 5 % des aktuellen Kontostands pro Wette
• Keine Kombiwetten, keine Sonderwetten
• Einsatz wird vor jedem Spiel auf Basis der aktuellen Bankroll berechnet
```

Diese Regel stimmt 1:1 mit dem Default in `BettingConfig` des v0.3-Pakets überein (`min_edge=0.03`, `kelly_fraction=0.25`, `max_stake_pct=0.05`).

---

## 3. Berechnung des Performance-Index

Der öffentliche Chart zeigt den Verlauf normalisiert auf einen Startwert von 100.

```python
performance_index(t) = 100 × (current_balance(t) / initial_balance)
```

Bei `initial_balance = 1000 €`:
- Bankroll 1000 € → Index **100**
- Bankroll 1100 € → Index **110**
- Bankroll 875 € → Index **87,5**

### Warum das funktioniert

- **Anonym genug fürs Werberecht** — keine konkreten Euro-Werte sichtbar
- **Intuitiv verständlich** — jeder versteht „+15 %" ohne Euro-Kontext
- **Kompatibel zu Finanz-Fondskursen** — sieht aus wie ein klassischer Chart-Darstellung eines Fonds

---

## 4. Daten-Pipeline

```
┌──────────────────────┐
│  v0.3 Model Pipeline │  (täglich)
│  predict → bet → log │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  ResultsTracker      │
│  predictions_log.json│
└──────────┬───────────┘
           │
           ▼  scripts/update_performance_index.py (täglich nach Spielen)
           │
┌──────────────────────┐
│  performance.json    │  ← beide Varianten (public + private)
│  performance_full.json│
└──────────┬───────────┘
           │
           ▼
    ┌──────┴──────────────┐
    │                     │
    ▼                     ▼
┌───────────┐       ┌───────────────────┐
│ Homepage  │       │ Member-Dashboard  │
│ (public)  │       │ (login required)  │
└───────────┘       └───────────────────┘
```

### Update-Kadenz
- **Täglich um 02:00 UTC** nach Abschluss aller Vortages-Spiele
- Implementation via cron / systemd timer / GitHub Action scheduled workflow
- Bei Verbindungsausfällen: letzte gültige Version wird weiter ausgespielt, Fehler geloggt

---

## 5. JSON-Schema

### 5.1 Öffentliche Datei: `performance.json`

Keine Euro-Werte, keine Match-Details.

```json
{
  "updated_at": "2026-04-18T02:00:00Z",
  "tracking_started_at": "2026-01-01",
  "n_days_tracked": 108,
  "n_bets": 84,
  "hit_rate": 0.472,
  "current_index": 124.73,
  "all_time_high_index": 128.15,
  "max_drawdown_pct": 0.124,
  "current_drawdown_pct": 0.027,
  "equity_curve": [
    {"date": "2026-01-01", "index": 100.00, "n_bets_cumulative": 0},
    {"date": "2026-01-03", "index": 101.25, "n_bets_cumulative": 2},
    {"date": "2026-01-05", "index": 99.83,  "n_bets_cumulative": 5}
  ],
  "rule_hash": "sha256:abc...",
  "model_version": "0.3.0"
}
```

### 5.2 Private Datei: `performance_full.json`

Alle Details für eingeloggte Nutzer.

```json
{
  "updated_at": "2026-04-18T02:00:00Z",
  "tracking_started_at": "2026-01-01",
  "initial_balance_eur": 1000.00,
  "current_balance_eur": 1247.30,
  "all_time_high_balance_eur": 1281.50,
  "roi_pct": 0.2473,
  "n_bets": 84,
  "wins": 40,
  "losses": 44,
  "hit_rate": 0.472,
  "avg_stake_eur": 23.40,
  "avg_odds_taken": 2.18,
  "max_drawdown_pct": 0.124,
  "max_drawdown_eur": 158.90,
  "current_drawdown_pct": 0.027,
  "sharpe_ratio": 0.81,
  "clv_mean": 0.012,
  "clv_pct_positive": 0.58,
  "equity_curve": [
    {"date": "2026-01-01", "balance_eur": 1000.00, "n_bets_cumulative": 0}
  ],
  "recent_bets": [
    {
      "date": "2026-04-17",
      "match": "Inter vs Cagliari",
      "bet": "Inter Heim",
      "odds": 1.20,
      "stake_eur": 45.20,
      "edge_pct": 0.117,
      "status": "won",
      "profit_eur": 9.04
    }
  ],
  "rule_hash": "sha256:abc...",
  "model_version": "0.3.0"
}
```

### 5.3 `rule_hash`

Hash über die aktuelle `BettingConfig` — wenn sich Regeln ändern (z.B. `min_edge` auf 2 %), ändert sich der Hash. Das Frontend kann dann einen Hinweis anzeigen:

> „Regeländerung am 2026-06-15. Vorheriger Performance-Track als Baseline-Index zurückgesetzt."

Damit bleibt die Historie ehrlich auch bei Modell-Updates.

---

## 6. Berechnungen im Detail

### 6.1 Equity-Kurve mit Punkten pro Tag

Für jeden Kalendertag seit Tracking-Start wird ein Datenpunkt erzeugt:
- Wenn an diesem Tag keine Wetten stattfanden → Index bleibt gleich
- Wenn Wetten stattfanden → Index wird nach Abschluss aller Spiele berechnet

**Daten-Kompaktierung:**
- Bei > 500 Datenpunkten: Frontend zeigt **pro Woche gemittelt** statt pro Tag
- Bei > 2000 Punkten: **pro Monat**
- Frontend-seitige Aggregation, Backend liefert immer alle Rohpunkte

### 6.2 Max Drawdown

```python
def max_drawdown(equity_values: list[float]) -> float:
    peak = equity_values[0]
    max_dd = 0.0
    for v in equity_values:
        peak = max(peak, v)
        dd = (peak - v) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
    return max_dd
```

Das ist identisch zur Logik in `v0.2/tracking/metrics.py::max_drawdown`.

### 6.3 Current Drawdown (nur public)

Differenz zwischen aktuellem Index und dem bisherigen All-Time-High:

```python
current_drawdown_pct = max(0, (ath_index - current_index) / ath_index)
```

Diese Metrik ist wichtig, weil sie sofort zeigt, ob das Modell gerade eine Durststrecke hat — **kein Verstecken von schlechten Phasen**.

### 6.4 Hit-Rate

```python
hit_rate = wins / n_bets
```

Achtung — die Hit-Rate bei Value-Betting ist **niedriger als man denkt**:
- Wer Favoriten (Quote ~1.3) backt → Hit-Rate ~70 %
- Wer Außenseiter (Quote ~5.0) backt → Hit-Rate ~20 %
- Profit kommt vom **Erwartungswert**, nicht von der Trefferquote

Das sollte eine erklärende Tooltip-Info im UI sein.

---

## 7. Frontend-Spezifikation

### 7.1 Position auf der Homepage

Als letzter Abschnitt vor dem Footer, volle Viewport-Breite, eigener Farbhintergrund (dunkel grau `#1a1a1a`) um sich vom Rest abzuheben.

### 7.2 Desktop-Layout

```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│   TRANSPARENZ-TRACKER                     seit 01. Jan. 2026   │
│   ─────────────────────                                         │
│                                                                 │
│   ┌─────────────┐  ┌─────────────┐  ┌──────────────┐           │
│   │   124,73    │  │   47,2 %    │  │    84        │           │
│   │  Index      │  │  Trefferquote│  │  Spiele      │           │
│   └─────────────┘  └─────────────┘  └──────────────┘           │
│                                                                 │
│   ┌──────────────────────────────────────────────────────┐     │
│   │  130                                        ╱╲       │     │
│   │  125                                    ╱───╯ ╲_     │     │
│   │  120                               ╱────╯        ╲   │     │
│   │  115                        ╱──────╯                 │     │
│   │  110                  ╱────╯                         │     │
│   │  105  ────╱──────────╯                               │     │
│   │  100  ────╯ · · · · · · · · · · · · · · · · · · · · │     │
│   │   95      ╲╱                                         │     │
│   │       Jan    Feb    Mär    Apr                       │     │
│   └──────────────────────────────────────────────────────┘     │
│                                                                 │
│   Max. Drawdown: -12,4 %                                        │
│                                                                 │
│   ▾ Regel-Details    ▾ Wie wird berechnet?    ▾ Kein Finanzrat │
│                                                                 │
│                       [ Jetzt registrieren → ]                  │
└────────────────────────────────────────────────────────────────┘
```

### 7.3 Mobile-Layout (< 768 px)

```
┌──────────────────────────┐
│  TRANSPARENZ-TRACKER      │
│  ─────────────────        │
│  seit 01. Jan. 2026       │
│                           │
│  ┌─────────────┐          │
│  │   124,73    │          │
│  │   Index     │          │
│  └─────────────┘          │
│  ┌─────────────┐          │
│  │  47,2 %     │          │
│  │ Trefferquote│          │
│  └─────────────┘          │
│  ┌─────────────┐          │
│  │   84        │          │
│  │  Spiele     │          │
│  └─────────────┘          │
│                           │
│  ┌──────────────────────┐│
│  │                 ╱╲   ││
│  │            ╱────╯ ╲  ││
│  │       ╱────╯        ││
│  │  ────╯               ││
│  └──────────────────────┘│
│                           │
│  Max Drawdown -12,4 %     │
│                           │
│  ▾ Details                │
└──────────────────────────┘
```

### 7.4 Farbcodierung im Chart

- Linie: `#4ade80` (grün) oberhalb 100, `#f87171` (rot) unterhalb 100
- Gestrichelte horizontale Referenzlinie bei 100: `#6b7280`
- Hintergrund-Gradient subtil: grün-transparent oberhalb 100, rot-transparent unterhalb
- Aktueller Punkt hervorgehoben mit größerem Marker + Wert-Label

### 7.5 Interaktion

- **Hover** auf Chart-Punkt: Zeigt Tooltip mit Datum + Index + kumulativer Anzahl Spiele (keine Euro-Werte)
- **Click/Tap** auf KPI-Box: Zeigt erklärenden Text (Was ist Trefferquote? Was ist Max Drawdown?)
- **Registrierungs-CTA** am unteren Rand: Leitet zur Anmeldung, um volle Details zu sehen

### 7.6 Empfohlene Tech-Komponenten

| Element | Empfehlung |
|---------|------------|
| Chart | **Recharts** (React) oder **Chart.js** + wrapper |
| Number-Animation | `react-countup` für Zähler 0 → 124,73 |
| Date-Formatierung | `date-fns` mit `de`-Locale |
| Tooltip | Recharts built-in oder `@radix-ui/react-tooltip` |
| Accordion (Details) | `@radix-ui/react-accordion` |

---

## 8. API-Endpoints

### 8.1 Public Endpoint

```
GET /api/performance
Content-Type: application/json
Cache-Control: public, max-age=3600

→ performance.json
```

Rate limiting auf IP-Basis (10 Requests/Minute reicht).

### 8.2 Private Endpoint (login required)

```
GET /api/performance/full
Authorization: Bearer <JWT>
Content-Type: application/json

→ performance_full.json
```

Bei fehlender/ungültiger Authentifizierung: `401 Unauthorized`, Frontend redirectet auf Login.

### 8.3 CSV-Export (private only)

```
GET /api/performance/export.csv
Authorization: Bearer <JWT>
Content-Type: text/csv

→ Spalten: date, match, bet, odds, stake_eur, edge_pct, status, profit_eur, balance_after
```

---

## 9. Pflicht-Disclaimer

Direkt unter dem Chart, klein aber lesbar:

```
Hypothetische Simulation eines statistischen Modells auf Basis
vergangener Spieldaten. Keine Aufforderung zum Glücksspiel.
Keine Gewähr auf zukünftige Ergebnisse. Glücksspiele bergen
finanzielle Risiken. Hilfe unter www.bundesweite-suchtberatung.de
oder Tel. 0800 1 372 700. Nur für Personen ab 18 Jahren.
```

Dieser Text wird statisch gerendert und darf **nicht** durch Ad-Blocker oder Cookie-Banner verdeckt werden.

---

## 10. Edge-Cases und Fehlerbehandlung

### 10.1 Tracking-Start-Tag
- Zeige bei `n_bets == 0` keine Trefferquote, sondern "—"
- Chart-Minimum 7 Datenpunkte bevor er sinnvoll aussieht

### 10.2 Cron-Update fehlgeschlagen
- Frontend zeigt `updated_at`-Zeitstempel
- Wenn `now - updated_at > 48h`: dezenter Hinweis „Daten werden aktualisiert" ohne Alarmismus

### 10.3 Drawdown-Phase
- **NICHT** verstecken oder beschönigen
- UI bleibt unverändert, rote Kurve ist bewusst sichtbar
- Eventuell kleine Info-Box: „Aktuell in Drawdown (-5,2 %) — das ist normal. Das Modell ist langfristig profitabel bei ausreichender Statistik."

### 10.4 Regel-Änderung (Admin-Eingriff)
- Vorheriger Verlauf wird **nicht gelöscht**, sondern visuell durch eine **vertikale Trennlinie** markiert
- Tooltip über der Linie: „Regel geändert am XX.XX.XXXX"
- Neue Baseline startet rechts der Linie wieder bei 100? Oder läuft weiter? → Entscheidung: **läuft weiter**, Trennlinie zeigt nur den Regel-Wechsel

### 10.5 Zukünftige Wetten (noch nicht abgeschlossen)
- Werden **nicht** in `equity_curve` aufgenommen
- Nur abgeschlossene Spiele zählen rein

### 10.6 Annulierte / gevoidete Wetten
- Status `"void"` → Einsatz wird zurückgegeben, Balance bleibt unverändert
- Zählt nicht in Hit-Rate, zählt in `n_bets` nur als informativer Wert

---

## 11. Implementierungs-Checkliste

### Backend
- [ ] Python-Script `scripts/update_performance_index.py` erstellen
  - Liest `predictions_log.json` aus dem v0.3-ResultsTracker
  - Berechnet Equity-Kurve + alle Metriken
  - Schreibt `performance.json` + `performance_full.json`
- [ ] Cron/Timer einrichten (täglich 02:00 UTC)
- [ ] API-Routen in FastAPI/Flask implementieren
  - `/api/performance` (public, gecached)
  - `/api/performance/full` (auth-required)
  - `/api/performance/export.csv` (auth-required)
- [ ] JWT-Authentifizierung prüfen (vermutlich existiert bei Kirchhof.ai schon)

### Frontend
- [ ] React-Komponente `<PerformanceTracker />` mit Recharts
- [ ] Mobile-responsive Design (Testing auf iPhone SE + iPad)
- [ ] Accordion für ausklappbare Details
- [ ] Tooltip-System für KPI-Erklärungen
- [ ] Disclaimer-Text statisch, immer sichtbar
- [ ] Integration in bestehende Homepage-Komponente

### Legal / Content
- [ ] Anwalt-Review der Disclaimer-Formulierung
- [ ] Datenschutz-Hinweis ergänzen falls Login-Daten neu
- [ ] AGB-Passage zum Demo-Tracker falls nötig
- [ ] Impressum-Check

### Testing
- [ ] Mit Mock-Daten (100, 200, 500, 2000 Datenpunkte) testen
- [ ] Performance-Test: Chart-Rendering < 500ms auch bei 2000 Punkten
- [ ] Drawdown-Szenario testen (was passiert wenn Modell 20% verliert)
- [ ] API-Endpoint bei fehlender `performance.json` → 503

---

## 12. Künftige Erweiterungen (v2)

Ideen für spätere Iterationen, nicht für v1:

- **Liga-Filter:** „Nur Bundesliga-Performance anzeigen"
- **Strategie-Vergleich:** „Quarter-Kelly vs. Flat-Stakes vs. Half-Kelly"
- **Vergleichsindex:** Performance des Modells vs. ein Naive-Home-Model
- **Monatliche Highlights:** „Bester Wert-Tipp des Monats" (nur Historie, nie live)
- **Newsletter-Integration:** „Jede Woche Update per Mail"
- **Backtest-Modus:** Nutzer können hypothetisch wählen „Was wäre wenn ich ab März 2024 begonnen hätte?"

---

## 13. Was ausdrücklich **nicht** passiert

Diese Dinge sind bewusst ausgeschlossen um die Seriosität zu wahren:

- ❌ Keine konkreten Euro-Beträge auf der Homepage
- ❌ Keine „Gewinnversprechen"
- ❌ Kein Countdown mit „Melde dich jetzt an, bevor Quote fällt!"
- ❌ Keine grellen Farben, keine Konfetti-Animationen
- ❌ Keine FOMO-Sprache („Andere haben schon 47 % gemacht")
- ❌ Keine fingierten Testimonials
- ❌ Keine Anzeige einzelner konkreter Wetten öffentlich (Schutz gegen Nachmachen ohne Kontext)
- ❌ Keine versteckten Drawdown-Phasen oder „nur-Sonnenschein"-Darstellung
- ❌ Kein Werben für externe Buchmacher / keine Affiliate-Links

---

## 14. Quellen der Wahrheit

Bei Implementierungsfragen immer zuerst hier nachsehen:

| Was | Wo |
|-----|----|
| Regel-Definition | `BettingConfig` in v0.3 `src/football_betting/config.py` |
| Wett-Logik | `v0.3/src/football_betting/betting/value.py` |
| Kelly-Berechnung | `v0.3/src/football_betting/betting/kelly.py` |
| Result-Tracking | `v0.3/src/football_betting/tracking/tracker.py` |
| Drawdown / Equity | `v0.3/src/football_betting/tracking/metrics.py` |
| Backtest als Referenz | `v0.3/src/football_betting/tracking/backtest.py` |

Das v0.3-Paket enthält bereits **alle** notwendigen Berechnungen. Die neue Komponente wickelt diese nur in einen täglichen Export + API-Endpoint + Frontend-Chart.

---

## Anhang — Minimaler Python-Export-Prototyp

Zur Orientierung, nicht final. Erwartet dass `predictions_log.json` aus v0.3 vorhanden ist.

```python
"""scripts/update_performance_index.py"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from football_betting.config import BETTING_CFG, PREDICTIONS_DIR
from football_betting.tracking.metrics import max_drawdown
from football_betting.tracking.tracker import ResultsTracker

INITIAL_BALANCE = 1000.0
OUT_PUBLIC = PREDICTIONS_DIR / "performance.json"
OUT_PRIVATE = PREDICTIONS_DIR / "performance_full.json"
TRACKING_START = "2026-01-01"


def compute_rule_hash() -> str:
    cfg = BETTING_CFG
    payload = f"{cfg.min_edge}|{cfg.kelly_fraction}|{cfg.max_stake_pct}|{cfg.min_odds}|{cfg.max_odds}"
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:16]


def build_equity_curve(completed_bets) -> list[dict]:
    balance = INITIAL_BALANCE
    curve = [{"date": TRACKING_START, "balance_eur": balance, "n_bets_cumulative": 0}]
    n_bets = 0
    for r in sorted(completed_bets, key=lambda x: x.date):
        stake = r.bet_stake or 0
        if r.bet_status == "won" and r.bet_odds:
            balance += stake * (r.bet_odds - 1)
        elif r.bet_status == "lost":
            balance -= stake
        n_bets += 1
        curve.append({"date": r.date, "balance_eur": round(balance, 2),
                      "n_bets_cumulative": n_bets})
    return curve


def main() -> None:
    tracker = ResultsTracker()
    tracker.load()
    completed = tracker.completed_bets()
    stats = tracker.roi_stats()
    curve = build_equity_curve(completed)
    balances = [p["balance_eur"] for p in curve]
    dd = max_drawdown(balances)

    current_balance = balances[-1]
    ath = max(balances)
    current_index = round(100 * current_balance / INITIAL_BALANCE, 2)
    ath_index = round(100 * ath / INITIAL_BALANCE, 2)
    current_dd = max(0, (ath - current_balance) / ath) if ath > 0 else 0

    # Public JSON (anonymisiert)
    public = {
        "updated_at": date.today().isoformat() + "T02:00:00Z",
        "tracking_started_at": TRACKING_START,
        "n_bets": stats["n_bets"],
        "hit_rate": round(stats["hit_rate"], 4) if stats["n_bets"] else None,
        "current_index": current_index,
        "all_time_high_index": ath_index,
        "max_drawdown_pct": round(dd["max_drawdown_pct"], 4),
        "current_drawdown_pct": round(current_dd, 4),
        "equity_curve": [
            {"date": p["date"],
             "index": round(100 * p["balance_eur"] / INITIAL_BALANCE, 2),
             "n_bets_cumulative": p["n_bets_cumulative"]}
            for p in curve
        ],
        "rule_hash": compute_rule_hash(),
        "model_version": "0.3.0",
    }

    # Private JSON (volle Details)
    private = {
        **public,
        "initial_balance_eur": INITIAL_BALANCE,
        "current_balance_eur": round(current_balance, 2),
        "all_time_high_balance_eur": round(ath, 2),
        "roi_pct": round((current_balance / INITIAL_BALANCE) - 1.0, 4),
        "wins": stats.get("wins", 0),
        "losses": stats.get("losses", 0),
        "avg_stake_eur": round(stats["total_stake"] / stats["n_bets"], 2)
                          if stats["n_bets"] else 0,
        "max_drawdown_eur": round(dd["max_drawdown_abs"], 2),
        "recent_bets": [
            {"date": r.date, "match": f"{r.home_team} vs {r.away_team}",
             "bet": r.bet_outcome, "odds": r.bet_odds,
             "stake_eur": r.bet_stake, "edge_pct": r.bet_edge,
             "status": r.bet_status,
             "profit_eur": (r.bet_stake or 0) * ((r.bet_odds or 1) - 1)
                           if r.bet_status == "won" else
                           -(r.bet_stake or 0) if r.bet_status == "lost" else 0}
            for r in sorted(completed, key=lambda x: x.date, reverse=True)[:50]
        ],
    }

    OUT_PUBLIC.write_text(json.dumps(public, indent=2, ensure_ascii=False))
    OUT_PRIVATE.write_text(json.dumps(private, indent=2, ensure_ascii=False))
    print(f"Written: {OUT_PUBLIC}")
    print(f"Written: {OUT_PRIVATE}")


if __name__ == "__main__":
    main()
```

---

**Ende der Spezifikation.**
