# Plan: Live-Event-Latency auf der Landing Page minimieren

## Ziel
Scoreaktualisierungen laufender Spiele sollen auf der Landing Page (`/`)
mit so wenig Verzögerung wie möglich sichtbar werden. Aktuell ergibt sich
ein Worst-Case-Stack von ≈ 2 min (Backend-Polling) + 45 s
(Frontend-Polling) + 1–3 min (Odds-API-Aktualität) ≈ **3 – 5 min** — und
*für Spiele ohne pending Bet sogar „nie während des Spiels"*, weil der
Live-Loop diese Ligen komplett überspringt.

## Root-Cause-Analyse

### End-to-End-Pfad heute
```
Odds API /scores
  └─ _live_settle_loop (scheduler.py:231)        alle 2 min
        └─ settle_live() (pipeline.py:41)
              └─ pending_league_codes()          ← FILTER: nur Ligen mit pending Bet
                 poll_and_store_scores()         → data/live_scores.jsonl
                 regrade_all()
Live-Scores-JSONL
  └─ _enrich_predictions_with_live_and_graded()  (services.py:561)  on-request
        ├─ load_graded()           (jsonl-Read je Request)
        └─ load_live_matches_for_code()  (jsonl-Read je Liga je Request)
HomeClient (web/app/HomeClient.tsx:85-91)        react-query refetchInterval
        ├─ 45 s wenn ein Pred.is_live == true
        ├─ 60 s wenn Snapshot stale
        └─ false sonst
```

### Identifizierte Latenzquellen
| # | Quelle | Delta | Datei |
|---|--------|-------|-------|
| L1 | Backend-Polling /scores alle **120 s** | bis 120 s | `scheduler.py:194-200` (Default=2) |
| L2 | Frontend-Polling **45 s** wenn live | bis 45 s | `HomeClient.tsx:85-91` |
| L3 | **Pending-Bet-Gating**: Ligen ohne pending Bet werden nicht gepollt → keine Live-Updates für Matches ohne Value- / Prediction-Bet | ∞ während Spiel | `pipeline.py:53-56`, `live_results.py:136-147` |
| L4 | `_enrich_predictions_with_live_and_graded` liest bei **jedem** Request `live_scores.jsonl` + `graded_bets.jsonl` komplett neu → skaliert mit Logsize unter Last | 10–200 ms pro Request | `services.py:561-658`, `live_results.py:65-78` |
| L5 | Frontend poll wird komplett abgeschaltet (`refetchIntervalInBackground: false`) → User tabt weg, kommt zurück, sieht alte Scores | stale bei Tab-Switch | `HomeClient.tsx:92` |
| L6 | Kein Push-Kanal: jeder Client pollt blind, auch wenn Backend weiß: nichts hat sich geändert | n/a | — |

## Lösungsstrategie — in drei Stufen

Ich empfehle **Stufe 1 + 2 sofort umzusetzen** (kleine, lokale Changes,
kein Architekturumbau, ≥ 5× schnellere Updates). Stufe 3 (SSE-Push) ist
die echte Ziellösung mit < 5 s Latenz, aber höherer Review-Aufwand.

### Stufe 1 — Quick Wins (minimal, low-risk)

**1.1 Adaptive Backend-Poll-Frequenz**  
`_live_settle_loop` (`scheduler.py:231-243`) bekommt einen zweiten,
kürzeren Intervall, der greift, **solange mindestens ein Match gerade
live ist**:
- Default `LIVE_SETTLE_INTERVAL_MIN` bleibt 2 (Fallback).
- Neue Env `LIVE_SETTLE_INTERVAL_ACTIVE_SEC` (Default **30 s**) wird
  genutzt, wenn `_any_match_currently_live()` True ist (prüft
  `load_today().predictions` auf `kickoff_utc` im Fenster
  `[now - 150 min, now]` und noch nicht `completed`).
- Wenn kein Live-Match aktiv → normaler 2-min-Rhythmus (spart
  Odds-API-Kontingent).

**1.2 Live-Poll entkoppeln vom Pending-Bet-Filter (L3)**  
Heute springt `settle_live()` mit `(0,0)` raus, falls keine pending Bets
existieren — dadurch sehen Spiele ohne aktiven Value-/Prediction-Bet
**gar keine** Live-Scores. Fix:
- `settle_live()` bekommt Parameter `force_leagues: set[str] | None`.
- Neuer Helper in `scheduler.py`: `_live_display_league_codes()` liest
  `load_today().predictions`, filtert auf Matches mit Kickoff im
  `[-150 min, +15 min]`-Fenster, mappt League → `LEAGUES[k].code`.
- `_settle_live_blocking()` übergibt die Union aus
  `pending_league_codes()` ∪ Display-Codes an eine neue Funktion
  `poll_live_scores_for_codes(codes)` (extrahiert aus
  `poll_and_store_scores`, gleicher Body, nur ohne Gating). Regrade
  läuft weiterhin nur, wenn pending Bets existieren.
- Ergebnis: `live_scores.jsonl` wird für **alle** Spiele gefüllt, die
  auf der Landing Page angezeigt werden.

**1.3 Frontend-Polling enger ziehen + Background-Aktualisierung**  
In `HomeClient.tsx:85-93`:
- `refetchInterval` auf **20 s** wenn `hasLive` (statt 45 s).
- `refetchIntervalInBackground: true` (L5) — sonst wird beim Zurück-
  Tabben eine Stale-Score angezeigt.
- `refetchOnWindowFocus: true` hinzufügen, damit Focus-Change
  sofortigen Refetch triggert.

**1.4 mtime-Cache im Enrich-Pfad (L4)**  
`live_results._load_rows()` und `grader.load_graded()` lesen bei jedem
Request die komplette JSONL. Unter 45 s × N Clients summiert sich das.
- In `live_results.py` einen modulprivaten Cache `(_cache_rows,
  _cache_mtime)` hinzufügen; nur neu parsen, wenn `os.stat(...).st_mtime`
  neuer ist.
- Analog für `load_graded()` (separate Task, nur wenn dessen Load
  messbar ist — optional).
- **Kein funktionaler Unterschied**, nur Performance. Vorteil: Enrich
  bleibt schnell, selbst wenn wir Polling verdoppeln.

### Stufe 2 — Broadcast nach jedem Write (mittel)

Nach jedem erfolgreichen Odds-API-Poll (also da, wo heute
`_refresh_performance_artifacts()` getriggert wird), **zusätzlich**
die Next.js Revalidation triggern, damit SSR-Caches nicht veralten:
- In `_settle_live_blocking()` (`scheduler.py:203-224`): Nach
  `invalidate_performance_cache()` einen Aufruf von
  `revalidate_snapshot_paths(["/[locale]"])` hinzufügen (nur Root-Page,
  selektiv — spart Revalidation-Kosten).
- Damit sieht jeder *neu geladene* Request ohne Verzögerung den Score.

### Stufe 3 — Server-Sent Events (optional, maximum pay-off)

Echter Push-Kanal; < 5 s Wahrnehmungslatenz möglich. Nur wenn Aufwand
gewünscht:
1. Neuer FastAPI-Endpoint `GET /predictions/today/stream` in
   `routes.py`, liefert `text/event-stream`.
2. In `services.py` ein `asyncio.Queue`-Fanout
   (`LiveScoreBroadcaster`). `_settle_live_blocking()` ruft
   `broadcaster.publish(changed_rows)` nach jedem erfolgreichen Poll.
3. Frontend (`HomeClient.tsx`) eröffnet `EventSource` nur wenn
   `hasLive`; bei Event wird `queryClient.setQueryData(queryKeys.today,
   ...)` inkrementell gepatcht. Fallback = bisheriges Polling.

Nicht Teil dieses Plans — separat nach Umsetzung Stufe 1+2 bewerten.

## Konkret zu ändernde Dateien (Stufe 1+2)

| Datei | Change |
|-------|--------|
| `src/football_betting/api/scheduler.py` | Adaptive Loop (1.1), Display-Code-Collection (1.2), Revalidate-Hook (Stufe 2) |
| `src/football_betting/evaluation/pipeline.py` | `settle_live(force_leagues=...)` Parameter |
| `src/football_betting/evaluation/live_results.py` | `poll_live_scores_for_codes()` (Gate-Free-Variante) + mtime-Cache in `_load_rows()` |
| `web/app/HomeClient.tsx` | `refetchInterval` 20 s, `refetchIntervalInBackground: true`, `refetchOnWindowFocus: true` |
| `tests/test_scheduler_live.py` *(neu)* oder bestehenden Test erweitern | Adaptive-Interval-Logik, force-Leagues |

### Neue / geänderte Env-Variablen
- `LIVE_SETTLE_INTERVAL_MIN` *(bestehend, Idle-Fallback)*, Default 2.
- `LIVE_SETTLE_INTERVAL_ACTIVE_SEC` *(neu)*, Default 30.
- `FRONTEND_LIVE_POLL_SEC` wird **nicht** extern konfiguriert — fix im
  Code, weil UI-Seite.

## Erwartete Latenz nach Stufe 1+2
| Phase | Heute | Nach 1+2 |
|-------|------:|---------:|
| Odds-API → `live_scores.jsonl` | bis 120 s | **bis 30 s** |
| Ligen ohne pending Bet | nie | ≤ 30 s |
| Disk → Frontend | bis 45 s | **bis 20 s** |
| **End-to-End Worst-Case** | ~165 s | **~50 s** |
| End-to-End Typical | ~90 s | ~25 s |

## Verifikation (End-to-End)

1. **Unit**: `pytest tests/test_scheduler_live.py -v` — new tests:
   - Active-Interval greift, wenn Prediction mit Kickoff in [-90min,0] vorliegt.
   - `settle_live(force_leagues={"soccer_epl"})` pollt, obwohl keine pending Bets.
   - `_load_rows()` mtime-Cache: zweiter Aufruf ohne Datei-Touch erzeugt **keinen** neuen Parse (Mock `os.stat`).
2. **Lint/Types**: `ruff check . && mypy src` — Strict-Mode darf nicht regressieren.
3. **Manuell / lokal**:
   - `fb serve` starten mit gesetztem `ODDS_API_KEY`, während ein echtes Live-Match läuft.
   - `tail -f logs/*.log` zeigt `[live-settle] ... polling /scores every 30 s` im Active-Fenster und 2-min-Cadence außerhalb.
   - Browser-DevTools → Network: `/predictions/today` sollte alle ~20 s refetched werden; Payload-Diff sichtbar bei jedem Tor.
4. **Acceptance**: Beobachtung eines Live-Spiels mit kürzlichem Torereignis
   (siehe externe Score-Seite als Referenz); erwartete Anzeige in UI
   innerhalb **≤ 60 s** nach Tor (vs. bisher 2–5 min).

## Risiken & Mitigation
- **Odds-API-Quota**: 30-s-Cadence nur im Active-Fenster × Anzahl
  Spieltage × Ligen. Bei typisch 1–2 aktiven Ligen/Tag ≈ +200 Requests/Tag.
  Sicher innerhalb üblicher Paid-Tier-Quoten; bei Bedarf Env
  `LIVE_SETTLE_INTERVAL_ACTIVE_SEC=60` als Sicherheit.
- **Regrade-Kosten**: `regrade_all()` läuft nur, wenn wirklich pending
  Bets existieren — keine Regression.
- **Frontend-Traffic**: 20-s-Poll × User-Count. Bei Skalierung auf >100
  Concurrent-User langfristig Stufe 3 (SSE) umsetzen.
