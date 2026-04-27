# Datenhistorie und Backfill-Abdeckung

Stand: 2026-04-27. Diese Bestandsaufnahme basiert auf den lokal vorhandenen Dateien im Repository. Es wurden keine externen Provider abgefragt und kein Sofascore-Scrape ausgelöst.

## Kurzfazit

- `Football-Data`: alle 5 Ziel-Ligen von `2021-22` bis laufend `2025-26`.
- `Sofascore`: alle 5 Ziel-Ligen von `2021-22` bis `2025-26` als JSON-Dateien vorhanden.
- `Sofascore xG`: `CH` hat keine xG-Werte in `2021-22` und `2022-23`; alle anderen Ligen sind praktisch vollständig, mit zwei einzelnen fehlenden Bundesliga-xG-Spielen.
- `The Odds API Historical`: nur `2023-24` und `2024-25`, Markt `h2h`, `bookmaker=consensus`.
- `The Odds API Live`: kleine JSONL-Historie ab April 2026.
- `Understat`: nur als 2021-22 xG-Ergänzung für `PL`, `BL`, `LL`, `SA`; nicht für `CH`.
- `Zulubet`: Tips von `2024-01-01` bis `2026-04-26`, aber nicht liga-spezifisch normalisiert.

## Liga- und Provider-Codes

| Liga | Interner Key | Football-Data Code | The Odds API Sport Key |
|---|---:|---:|---|
| Premier League | `PL` | `E0` | `soccer_epl` |
| EFL Championship | `CH` | `E1` | `soccer_efl_champ` |
| Bundesliga | `BL` | `D1` | `soccer_germany_bundesliga` |
| Serie A | `SA` | `I1` | `soccer_italy_serie_a` |
| La Liga | `LL` | `SP1` | `soccer_spain_la_liga` |

Quelle der Codes: `src/football_betting/config.py`.

## Football-Data CSVs

Pfad: `data/raw/`

Diese Dateien bilden die wichtigste Match-Historie. Enthalten sind Ergebnisse, Match-Statistiken und historische Pre-Match-/Closing-Quoten verschiedener Bookmaker-Spalten, je nach Saison u. a. `B365*`, `PS*`, `Max*`, `Avg*`, `B365C*`, `PSC*`, `MaxC*`, `AvgC*`.

| Liga | Historie | Matches gesamt | Datumsbereich |
|---|---|---:|---|
| `PL` | `2021-22` bis `2025-26` | 1.852 | `2021-08-13` bis `2026-04-22` |
| `CH` | `2021-22` bis `2025-26` | 2.736 | `2021-08-06` bis `2026-04-22` |
| `BL` | `2021-22` bis `2025-26` | 1.494 | `2021-08-13` bis `2026-04-19` |
| `SA` | `2021-22` bis `2025-26` | 1.850 | `2021-08-21` bis `2026-04-20` |
| `LL` | `2021-22` bis `2025-26` | 1.840 | `2021-08-13` bis `2026-04-23` |

### Football-Data nach Saison

| Liga | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 laufend |
|---|---:|---:|---:|---:|---:|
| `PL` | 380 | 380 | 380 | 380 | 332 |
| `CH` | 552 | 552 | 552 | 552 | 528 |
| `BL` | 306 | 306 | 306 | 306 | 270 |
| `SA` | 380 | 380 | 380 | 380 | 330 |
| `LL` | 380 | 380 | 380 | 380 | 320 |

## Sofascore

Pfad: `data/sofascore/`

Sofascore-Dateien enthalten pro Match u. a. Event-ID, Teams, Score, Status, Datum, xG-Felder, Schüsse, Big Chances, durchschnittliche Player-Ratings und Starting-XI-IDs. Der Scraper ist opt-in; beim Erstellen dieser Doku wurde nicht gescraped.

Wichtige Felder:

- `home_xg`, `away_xg`
- `home_shots`, `away_shots`
- `home_shots_on_target`, `away_shots_on_target`
- `home_big_chances`, `away_big_chances`
- `home_avg_rating`, `away_avg_rating`
- `home_starting_xi`, `away_starting_xi`

### Sofascore Gesamtübersicht

| Liga | Dateien | Records | Finished | xG vorhanden | Lineups vorhanden | Datumsbereich |
|---|---|---:|---:|---:|---:|---|
| `PL` | `2021-22` bis `2025-26` | 1.959 | 1.858 | 1.858 | 1.858 | `2021-08-13` bis `2026-05-24` |
| `CH` | `2021-22` bis `2025-26` | 2.369 | 2.280 | 1.368 | 2.280 | `2021-08-06` bis `2026-04-14` |
| `BL` | `2021-22` bis `2025-26` | 1.535 | 1.502 | 1.500 | 1.501 | `2021-08-13` bis `2026-05-16` |
| `SA` | `2021-22` bis `2025-26` | 1.911 | 1.858 | 1.858 | 1.858 | `2021-08-21` bis `2026-05-24` |
| `LL` | `2021-22` bis `2025-26` | 1.914 | 1.849 | 1.849 | 1.849 | `2021-08-13` bis `2026-05-24` |

`Records` kann größer als `Finished` sein, weil die laufende Saison `2025-26` bereits zukünftige Fixtures enthält. Für abgeschlossene Saisons kommen vereinzelt Zusatz-/Cup-/Playoff-nahe Events in den Sofascore-Dateien vor; für Trainingsfeatures zählen primär `status="finished"` und der Join auf die Football-Data-Historie.

### Sofascore nach Liga und Saison

| Liga | Saison | Datei vorhanden | Records | Finished | xG vorhanden | Lineups vorhanden | Datumsbereich |
|---|---|---:|---:|---:|---:|---:|---|
| `PL` | `2021-22` | ja | 415 | 380 | 380 | 380 | `2021-08-13` bis `2022-05-22` |
| `PL` | `2022-23` | ja | 402 | 380 | 380 | 380 | `2022-08-05` bis `2023-05-28` |
| `PL` | `2023-24` | ja | 380 | 380 | 380 | 380 | `2023-08-11` bis `2024-05-19` |
| `PL` | `2024-25` | ja | 381 | 380 | 380 | 380 | `2024-08-16` bis `2025-05-25` |
| `PL` | `2025-26` | ja | 381 | 338 | 338 | 338 | `2025-08-15` bis `2026-05-24` |
| `CH` | `2021-22` | ja | 490 | 456 | 0 | 456 | `2021-08-06` bis `2022-05-03` |
| `CH` | `2022-23` | ja | 489 | 456 | 0 | 456 | `2022-07-29` bis `2023-04-27` |
| `CH` | `2023-24` | ja | 459 | 456 | 456 | 456 | `2023-08-04` bis `2024-04-24` |
| `CH` | `2024-25` | ja | 460 | 456 | 456 | 456 | `2024-08-09` bis `2025-03-16` |
| `CH` | `2025-26` | ja | 471 | 456 | 456 | 456 | `2025-08-08` bis `2026-04-14` |
| `BL` | `2021-22` | ja | 308 | 305 | 305 | 305 | `2021-08-13` bis `2022-05-14` |
| `BL` | `2022-23` | ja | 306 | 306 | 305 | 306 | `2022-08-05` bis `2023-05-27` |
| `BL` | `2023-24` | ja | 306 | 306 | 306 | 306 | `2023-08-18` bis `2024-05-18` |
| `BL` | `2024-25` | ja | 306 | 306 | 305 | 305 | `2024-08-23` bis `2025-05-17` |
| `BL` | `2025-26` | ja | 309 | 279 | 279 | 279 | `2025-08-22` bis `2026-05-16` |
| `SA` | `2021-22` | ja | 386 | 380 | 380 | 380 | `2021-08-21` bis `2022-05-22` |
| `SA` | `2022-23` | ja | 380 | 380 | 380 | 380 | `2022-08-13` bis `2023-06-04` |
| `SA` | `2023-24` | ja | 380 | 380 | 380 | 380 | `2023-08-19` bis `2024-06-02` |
| `SA` | `2024-25` | ja | 380 | 380 | 380 | 380 | `2024-08-17` bis `2025-05-25` |
| `SA` | `2025-26` | ja | 385 | 338 | 338 | 338 | `2025-08-23` bis `2026-05-24` |
| `LL` | `2021-22` | ja | 386 | 380 | 380 | 380 | `2021-08-13` bis `2022-05-22` |
| `LL` | `2022-23` | ja | 380 | 380 | 380 | 380 | `2022-08-12` bis `2023-06-04` |
| `LL` | `2023-24` | ja | 382 | 380 | 380 | 380 | `2023-08-11` bis `2024-05-26` |
| `LL` | `2024-25` | ja | 383 | 380 | 380 | 380 | `2024-08-15` bis `2025-05-25` |
| `LL` | `2025-26` | ja | 383 | 329 | 329 | 329 | `2025-08-15` bis `2026-05-24` |

### Sofascore-Lücken

| Liga | Saison | Problem | Umfang |
|---|---|---|---:|
| `CH` | `2021-22` | keine xG-Werte | 456 finished Matches ohne xG |
| `CH` | `2022-23` | keine xG-Werte | 456 finished Matches ohne xG |
| `BL` | `2022-23` | einzelnes finished Match ohne xG | 1 |
| `BL` | `2024-25` | einzelnes finished Match ohne xG und Lineup | 1 |

Einzelne Bundesliga-Lücken:

| Liga | Saison | Datum | Heim | Auswärts | Score |
|---|---|---|---|---|---|
| `BL` | `2022-23` | `2023-04-16` | `1. FC Union Berlin` | `VfL Bochum 1848` | `1-1` |
| `BL` | `2024-25` | `2024-12-14` | `1. FC Union Berlin` | `VfL Bochum 1848` | `1-1` |

Zusatzdatei:

- `data/sofascore/BL_2024-25.baseline.json`: 3 alte Baseline-Records.

## The Odds API Historical

Pfad: `data/odds_snapshots/`

Diese Daten stammen aus dem Historical Endpoint und werden als Parquet je Liga/Saison gespeichert. Aktuell vorhanden ist nur Markt `h2h` mit aggregiertem `bookmaker=consensus`. Die Daten speisen den `MarketMovementTracker` und damit die `mm_*`-Featurefamilie.

| Liga | Historie | Rows | Unique Fixtures | Snapshot-Zeitpunkte | Match-Datumsbereich |
|---|---|---:|---:|---:|---|
| `PL` | `2023-24`, `2024-25` | 4.839 | 776 | 257 | `2023-08-11` bis `2025-05-25` |
| `CH` | `2023-24`, `2024-25` | 3.931 | 1.035 | 260 | `2023-08-04` bis `2025-05-24` |
| `BL` | `2023-24`, `2024-25` | 4.340 | 620 | 260 | `2023-08-18` bis `2025-05-26` |
| `SA` | `2023-24`, `2024-25` | 4.883 | 824 | 262 | `2023-08-19` bis `2025-05-25` |
| `LL` | `2023-24`, `2024-25` | 4.924 | 800 | 260 | `2023-08-11` bis `2025-05-25` |

### The Odds API Historical nach Saison

| Liga | Saison | Rows | Unique Fixtures | Snapshot-Zeitpunkte | Match-Datumsbereich | Stunden vor Kickoff |
|---|---|---:|---:|---:|---|---|
| `PL` | `2023-24` | 2.418 | 392 | 127 | `2023-08-11` bis `2024-05-19` | 6,6 bis 680,3 |
| `PL` | `2024-25` | 2.421 | 384 | 130 | `2024-08-16` bis `2025-05-25` | 0,6 bis 583,1 |
| `CH` | `2023-24` | 2.275 | 560 | 130 | `2023-08-04` bis `2024-05-26` | 0,6 bis 891,1 |
| `CH` | `2024-25` | 1.656 | 475 | 130 | `2024-08-09` bis `2025-05-24` | 1,6 bis 415,1 |
| `BL` | `2023-24` | 2.212 | 310 | 130 | `2023-08-18` bis `2024-05-27` | 6,6 bis 746,6 |
| `BL` | `2024-25` | 2.128 | 310 | 130 | `2024-08-23` bis `2025-05-26` | 6,6 bis 723,6 |
| `SA` | `2023-24` | 2.516 | 421 | 132 | `2023-08-19` bis `2024-06-02` | 4,6 bis 582,8 |
| `SA` | `2024-25` | 2.367 | 403 | 130 | `2024-08-17` bis `2025-05-25` | 4,6 bis 582,8 |
| `LL` | `2023-24` | 2.551 | 403 | 130 | `2023-08-11` bis `2024-05-26` | 4,1 bis 607,1 |
| `LL` | `2024-25` | 2.373 | 397 | 130 | `2024-08-15` bis `2025-05-25` | 5,1 bis 608,1 |

Aktuelle Lücken:

- keine Historical-Parquets für `2021-22`
- keine Historical-Parquets für `2022-23`
- keine Historical-Parquets für laufend `2025-26`
- keine per-Bookmaker-Zeilen, sondern nur `consensus`
- keine `totals` oder `spreads`, weil der aktuelle Backfill nur `h2h` enthält

## The Odds API Live-Snapshots

Pfad: `data/snapshots/odds_<LG>.jsonl`

Diese JSONL-Dateien wachsen durch Live-/Pre-Kickoff-Snapshotting. Sie sind aktuell klein und eher Monitoring-/CLV-Material als robuste Trainingshistorie.

| Liga | Zeilen | Unique Fixtures | Match-Dates | Snapshot-Zeitbereich |
|---|---:|---:|---|---|
| `PL` | 30 | 14 | `2026-04-18` bis `2026-04-25` | `2026-04-18T14:54:54` bis `2026-04-25T11:06:37` |
| `CH` | 37 | 22 | `2026-04-18` bis `2026-04-25` | `2026-04-18T14:54:56` bis `2026-04-25T11:06:42` |
| `BL` | 18 | 13 | `2026-04-18` bis `2026-04-25` | `2026-04-18T14:54:55` bis `2026-04-25T11:06:47` |
| `SA` | 13 | 7 | `2026-04-18` bis `2026-04-25` | `2026-04-18T14:54:55` bis `2026-04-25T11:06:50` |
| `LL` | 20 | 10 | `2026-04-18` bis `2026-04-25` | `2026-04-18T14:54:56` bis `2026-04-25T11:32:59` |

## The Odds API Live-Scores

Pfad: `data/live_scores.jsonl`

Diese Daten werden für Settlement/Regrading genutzt und sind ebenfalls erst ab April 2026 lokal vorhanden.

| Liga | Score-Zeilen | Match-Dates | Fetch-Zeitbereich |
|---|---:|---|---|
| `PL` | 15 | `2026-04-18` bis `2026-04-25` | `2026-04-19T04:31:14Z` bis `2026-04-25T11:30:09Z` |
| `CH` | 28 | `2026-04-17` bis `2026-04-25` | `2026-04-19T04:34:23Z` bis `2026-04-25T11:55:14Z` |
| `BL` | 7 | `2026-04-17` bis `2026-04-24` | `2026-04-19T04:31:13Z` bis `2026-04-25T08:33:40Z` |
| `SA` | 6 | `2026-04-17` bis `2026-04-24` | `2026-04-19T04:31:15Z` bis `2026-04-25T08:33:40Z` |
| `LL` | 12 | `2026-04-21` bis `2026-04-25` | `2026-04-22T09:26:33Z` bis `2026-04-25T12:00:12Z` |

## Understat xG-Backfill

Pfad: `data/sofascore/_understat_cache/`

Skript: `scripts/backfill_xg_understat.py`

Der Understat-Backfill wurde verwendet, um fehlende 2021-22 xG-Werte in Sofascore-JSON-Dateien zu ergänzen. Der Backfill ist auf Ligen beschränkt, für die Understat-Daten vorhanden sind.

| Liga | Understat-Datei | Abdeckung |
|---|---|---|
| `BL` | `bundesliga_shot_data.rds` | 2021-22 xG-Ergänzung |
| `PL` | `epl_shot_data.rds` | 2021-22 xG-Ergänzung |
| `LL` | `la_liga_shot_data.rds` | 2021-22 xG-Ergänzung |
| `SA` | `serie_a_shot_data.rds` | 2021-22 xG-Ergänzung |
| `CH` | keine Datei | nicht abgedeckt |

## Zulubet

Pfad: `data/zulubet/zulubet_tips.parquet`

Zulubet ist als Tips-Quelle vorhanden, aber nicht sauber als historische Match-/Quotenquelle für die 5 Ziel-Ligen gemappt.

| Quelle | Rows | Datumsbereich | Spalten |
|---|---:|---|---|
| `zulubet_tips.parquet` | 60.713 | `2024-01-01` bis `2026-04-26` | `date`, `home`, `away`, `tip` |

## Wetter-Cache

Pfad: `data/weather/cache.sqlite`

Der Wetter-Cache enthält HTTP-Antworten des Wetter-Clients und ist kein liga-saison-spezifischer Match-Backfill. Er ist für Feature-Building relevant, wenn Wetterfeatures aktiviert werden.

| Tabelle | Zeilen | Zweck |
|---|---:|---|
| `response_cache` | 10.747 | gecachte Wetter-API-Antworten |

## Backtest- und Evaluationsartefakte

Pfad: `data/backtests/`

| Datei | Status |
|---|---|
| `backtest_PL.json` | vorhanden |
| `backtest_BL.json` | vorhanden |
| `backtest_SA.json` | vorhanden |
| `backtest_LL.json` | vorhanden |
| `walk_forward_BL.json` | vorhanden |
| `backtest_CH.json` | nicht vorhanden |

Weitere Live-/Evaluation-Dateien:

| Datei | Zweck |
|---|---|
| `data/predictions/predictions_log.json` | persistierte Vorhersagen |
| `data/graded_bets.jsonl` | gesettelte Bets |
| `data/live_scores.jsonl` | Live-/Result-Settlement |
| `data/snapshots/today.json` | aktueller Public Snapshot |
| `data/snapshots/YYYY-MM-DD.json` | Tagesarchive |

## Relevante Datenlücken

1. `CH` Sofascore xG fehlt komplett für `2021-22` und `2022-23`.
2. `BL` hat zwei einzelne finished Matches ohne xG, siehe Sofascore-Lücken.
3. The Odds API Historical deckt nur `2023-24` und `2024-25` ab.
4. The Odds API Historical enthält aktuell nur `h2h` und nur `consensus`, keine per-Bookmaker-Historie.
5. Live-Snapshots und Live-Scores sind erst ab April 2026 vorhanden und für Training noch klein.
6. `CH` hat kein `data/backtests/backtest_CH.json`.
7. Zulubet ist vorhanden, aber nicht in die 5-Ligen-Historie normalisiert.

## Konsequenzen für Training und Evaluation

- Für klassische 1X2-Modelle ist die Football-Data-Historie über alle 5 Ligen und 5 Saisons solide.
- Real-xG-/Squad-Features sind für `PL`, `BL`, `SA`, `LL` ab `2021-22` weitgehend nutzbar.
- Bei `CH` sind Real-xG-Features erst ab `2023-24` belastbar; `2021-22` und `2022-23` sollten mit `has_real_xg=0` oder äquivalenter Missingness behandelt werden.
- Marktbewegungsfeatures aus The Odds API Historical sind nur für `2023-24` und `2024-25` geeignet.
- Für Value-Modell-Training sollten direkte Marktfeatures weiterhin kontrolliert oder blockiert werden, wenn das Modell den Markt schlagen und nicht imitieren soll.
- CLV-Analysen auf Basis von Live-Snapshots sind noch nicht robust, weil die Live-Historie nur wenige Tage umfasst.
