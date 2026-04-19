# Plan: Kickoff-Uhrzeit mit DST (Sommer-/Winterzeit) korrekt behandeln

## Problem

Die Uhrzeiten im Projekt werden an mehreren Stellen inkonsistent behandelt. DST (CET ↔ CEST, GMT ↔ BST) wird nur teilweise berücksichtigt:

| # | Ort | Status | Problem |
|---|-----|--------|---------|
| 1 | `data/loader.py::_extract_kickoff` | naive datetime aus CSV | Feld heißt `kickoff_datetime_utc`, enthält aber **local league time** ohne tz-Info → DST wird ignoriert |
| 2 | `scraping/odds_api.py` | UTC → `ZoneInfo(league)` | korrekt, aber liefert nur `HH:MM` als String (keine UTC-Info für Client) |
| 3 | `api/services.py` | `datetime.utcnow()` naive | Frontend parst als Local Time → 1–2 h Abweichung je nach DST |
| 4 | `web/components/LeagueFixturesWidget.tsx` | zeigt `kickoff_time` direkt | User in anderer TZ sieht Liga-Lokalzeit statt Eigenzeit, DST-Wechsel unsichtbar |
| 5 | `web/components/RecentBets.tsx` | `new Date("YYYY-MM-DD")` | JS interpretiert als UTC-Mitternacht → Datum springt westlich von UTC |

## Ziel

1. Alle Kickoff-Zeiten **intern durchgängig als UTC-aware ISO-8601 (`...Z`)** führen.
2. Die jeweilige **Ligazeitzone** (IANA-Name, z. B. `Europe/Berlin`) mitliefern, damit Sommer-/Winterzeit automatisch via `ZoneInfo` (Python) bzw. `Intl.DateTimeFormat` (Browser) aufgelöst wird — **keine hardcodierten `+1/+2` Offsets**.
3. Im Frontend die Zeit **in der User-Zeitzone** rendern, mit optionaler Zusatzanzeige der Ligazeit.
4. Bestehendes Verhalten (HH:MM-String im Snapshot) **rückwärtskompatibel** halten.

## Umzusetzende Änderungen

### Backend (Python)

**1. `src/football_betting/scraping/odds_api.py`**
- `_LEAGUE_TIMEZONES` als öffentliches Modul exportieren (z. B. in neues Modul `src/football_betting/utils/timezones.py` verschieben) und um fehlende Ligen erweitern (`FL` → `Europe/Paris`, `NL` → `Europe/Amsterdam` falls genutzt — vorher via Grep in `config.py` prüfen).
- `FixtureOdds` um `kickoff_utc: datetime` ergänzen (zusätzlich zu `kickoff_local`), in `to_fixture_dict()` als `"kickoff_utc": isoformat-Z` ausgeben.

**2. `src/football_betting/data/loader.py::_extract_kickoff`**
- `_extract_kickoff(row, league_key)` erweitern: naive Lokalzeit mit `ZoneInfo(league_tz)` lokalisieren (DST-korrekt via `.replace(tzinfo=tz)` oder direkter Konstruktion), dann `.astimezone(timezone.utc)` → UTC-aware datetime zurückgeben.
- `Match.kickoff_datetime_utc` enthält damit echte UTC-Zeit. Ambigue/fehlende Stunden beim DST-Sprung (02:00–03:00 Ende März) per `fold=0` deterministisch auflösen.

**3. `src/football_betting/api/services.py`**
- Alle `datetime.utcnow()` → `datetime.now(timezone.utc)` (tz-aware).
- Beim Serialisieren von `generated_at` / Kickoff: immer `isoformat()` mit `+00:00` bzw. `Z`-Suffix.
- Neues Feld `kickoff_utc: str | None` zusätzlich zu `kickoff_time` in die relevanten Schemas/Payloads (`schemas.py` Zeilen 32, 273, 310) aufnehmen. `kickoff_time` bleibt als bestehender HH:MM-Liga-String (rückwärtskompatibel).
- `league_timezone: str` pro Liga in Fixtures-Payloads aufnehmen (IANA-Name), damit Frontend sie Liga-lokal formatieren kann.

**4. `src/football_betting/config.py`**
- `default_kickoff_hour_utc` umbenennen/ergänzen zu `default_kickoff_hour_local=19` + League-TZ-Lookup; Weather-Feature soll die echte UTC-Stunde via TZ-Konvertierung nutzen.

### Frontend (Next.js)

**5. `web/lib/datetime.ts`** (neue Datei)
- Helper `formatKickoff(utcIso, { locale, timeZone?, showTz? })` → nutzt `Intl.DateTimeFormat` mit gewünschter `timeZone` (default: User-Browser-TZ). DST wird von `Intl` automatisch gehandhabt.
- Helper `formatMatchDate(dateStr)` → parst `YYYY-MM-DD` bewusst als lokalen Tag (`new Date(y, m-1, d)`), verhindert UTC-Midnight-Bug.

**6. `web/components/LeagueFixturesWidget.tsx`**
- `kickoff_time`-Anzeige durch `formatKickoff(row.kickoff_utc, { locale })` ersetzen, Fallback auf bestehendes `kickoff_time` wenn `kickoff_utc` fehlt (alte Snapshots).
- Optional Badge „CET" / „CEST" via `Intl.DateTimeFormat` mit `timeZoneName: 'short'`.

**7. `web/components/RecentBets.tsx`**
- `new Date("YYYY-MM-DD")` → `formatMatchDate(...)` verwenden.

**8. `web/app/HomeClient.tsx`**
- `generated_at` mit `formatKickoff` oder `toLocaleString(locale)` auf aware-ISO umstellen; Backend liefert ab jetzt `...Z`.

**9. `web/lib/server-api.ts`**
- Types erweitern: `kickoff_utc?: string | null`, `league_timezone?: string | null`.

### Tests

**10. `tests/test_loader.py`** (bzw. passender Testfile)
- Neue Tests: Kickoff 28.03. 15:30 Berlin → vor DST (CET=UTC+1) ergibt `14:30 UTC`; 15.06. 15:30 Berlin → CEST=UTC+2 ergibt `13:30 UTC`.
- Edge case: Mehrdeutige Stunde am DST-Ende (27.10. 02:30 Berlin) → deterministisch via `fold=0`.

**11. `tests/test_odds_api.py`**
- Fixture mit UTC-Commence-Timestamp im Winter vs. Sommer → `kickoff_local` und neues `kickoff_utc` korrekt.

**12. `web/` Typescript**
- `npm run type-check` durchlaufen lassen.

## Kritische Dateien

- `src/football_betting/data/loader.py:37-59` (Kickoff-Parsing)
- `src/football_betting/scraping/odds_api.py:26-32, 60-90, 205-240` (TZ-Map, FixtureOdds)
- `src/football_betting/api/services.py` (utcnow, Payload-Aufbau)
- `src/football_betting/api/schemas.py:32, 273, 310`
- `src/football_betting/config.py` (default_kickoff_hour_utc)
- `web/components/LeagueFixturesWidget.tsx:52-58`
- `web/components/RecentBets.tsx` (Date-Parsing)
- `web/app/HomeClient.tsx` (generated_at)
- `web/lib/server-api.ts` (Types)
- **Neu:** `src/football_betting/utils/timezones.py`, `web/lib/datetime.ts`

## Verifikation

```bash
# Backend
pytest tests/test_loader.py tests/test_odds_api.py -v
ruff check . && mypy src

# Snapshot end-to-end
fb snapshot
type data\snapshots\today.json | findstr kickoff_utc   # Feld vorhanden, Z-Suffix

# API
fb serve &
curl http://localhost:8000/api/today | jq ".fixtures[0].kickoff_utc"

# Frontend
cd web && npm run type-check && npm run lint && npm run build
# Manueller Smoke-Test in DevTools: Browser-TZ auf "America/New_York" stellen,
# Bundesliga-Fixture prüfen → Zeit muss 5–6 h (je nach DST) früher als Berliner Lokalzeit stehen.
```

## Rollout-Hinweise

- `kickoff_time` (HH:MM Liga-lokal) bleibt im Payload erhalten → alte Frontend-Builds funktionieren weiter.
- Neue Frontend-Version bevorzugt `kickoff_utc`, fällt auf `kickoff_time + league_timezone` zurück, wenn UTC nicht geliefert wurde.
- Keine Migration nötig; nächster `fb snapshot` erzeugt korrekte Daten.
