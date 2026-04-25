# Value-Bet Pipeline — Report

Stand: 2026-04-25. Beschreibt, wie aktuell Value-Bet-Vorhersagen erzeugt werden, welche Features einfließen und welche Modelle/Datenquellen beteiligt sind.

## 1. Pipeline-Einstieg

Alle Vorhersagen laufen durch [build_predictions_for_fixtures()](../src/football_betting/api/services.py#L365) in [services.py:365-620](../src/football_betting/api/services.py#L365-L620).

Aufrufer:
- `fb snapshot` (Snapshot-Job, geplant)
- Fallback ad-hoc aus [get_today_payload()](../src/football_betting/api/services.py#L737), wenn kein Snapshot vorhanden ist

Eingang: Liste von Fixture-Dicts mit `league`, `date`, `home_team`, `away_team`, `odds{home,draw,away}` (+ optional `kickoff_time` / `kickoff_utc` / `season`).

## 2. Schritt-für-Schritt pro Liga

1. **Historie laden** — [load_league()](../src/football_betting/api/services.py#L405) liest die Football-Data-CSVs aus `data/raw/`.
2. **Zwei FeatureBuilder warmlaufen** ([warm_feature_builder()](../src/football_betting/predict/runtime.py#L287), Aufruf in [services.py:419-420](../src/football_betting/api/services.py#L419-L420)):
   - `purpose="1x2"` — voller Feature-Satz
   - `purpose="value"` — selbe Features, aber Blocklist-Filter `market_*` + `mm_*` aus [ValueModelConfig](../src/football_betting/config.py#L178-L196)
   - Begründung: Value-Modell darf den Markt nicht imitieren, sondern muss ihn schlagen
3. **Odds-Snapshots persistieren** ([services.py:437-478](../src/football_betting/api/services.py#L437-L478)):
   - Aktuelle Quoten landen in der Opening-Line-Datei
   - Lead-Time-Guard ≥ `snapshot_min_lead_hours = 6h` (verhindert Verschmutzung mit Closing-Line-Daten)
   - Marktverlauf wird in den `market_tracker` zurückgespielt
4. **Zwei Modelle bauen** ([build_league_model()](../src/football_betting/predict/runtime.py#L319), in [services.py:481-496](../src/football_betting/api/services.py#L481-L496)) — je `purpose` separat aus den `models/`-Artefakten geladen.
5. **Vorhersage je Fixture**:
   - 1X2-Pick aus Modell #1 → in `predictions[]` (Most-Likely-Spalte + Staking)
   - Wahrscheinlichkeiten aus Modell #2 (`value_pred`) → [find_value_bets()](../src/football_betting/betting/value.py#L83) ([services.py:553-570](../src/football_betting/api/services.py#L553-L570))
   - Fallback auf `pred`, falls Value-Artefakte fehlen

## 3. Value-Bet-Filter

Kernlogik in [value.py:83-145](../src/football_betting/betting/value.py#L83-L145). Pro Outcome (H/D/A):

| Schritt | Regel | Default |
|---|---|---|
| Devig | [remove_margin()](../src/football_betting/betting/margin.py) → faire Marktwahrscheinlichkeit | Methode `power` |
| Edge | `model_p − market_p ≥ min_edge` | `0.03` |
| Quoten-Range | `min_odds ≤ odds ≤ max_odds` | `1.30 … 15.0` |
| EV-Kissen | `(model_p × odds − 1) ≥ min_ev_pct` | `0.0` (per Liga überschreibbar) |
| Stake | Quartiel-Kelly, hart gedeckelt | `0.25 × Kelly`, max `5%` Bankroll |
| Confidence | Heuristik aus Edge × Quotenbereich | high / medium / low |

Defaults aus [BettingConfig](../src/football_betting/config.py#L695-L713). Per-Liga-Overrides via `LeagueModelProfile.betting` ([betting_config_from_profile()](../src/football_betting/predict/runtime.py#L241)).

Stake-Berechnung: [kelly_stake()](../src/football_betting/betting/kelly.py#L37). Confidence-Heuristik: [value.py:74-80](../src/football_betting/betting/value.py#L74-L80).

## 4. Modelle hinter dem Value-Pred

[EnsembleModel](../src/football_betting/predict/ensemble.py#L66) als gewichtete Simplex-Mischung von bis zu vier Membern (siehe [predict()](../src/football_betting/predict/ensemble.py#L117)):

| Member | Datei | Status |
|---|---|---|
| CatBoost | [catboost_model.py](../src/football_betting/predict/catboost_model.py) | aktiv (Default) |
| Poisson | [poisson.py](../src/football_betting/predict/poisson.py) | aktiv (Pi-Ratings-basiert) |
| MLP / TabTransformer | [mlp_model.py](../src/football_betting/predict/mlp_model.py) | optional |
| Sequence (1D-CNN + Transformer) | [sequence_model.py](../src/football_betting/predict/sequence_model.py) | optional |

Aktive Member + Gewichte pro Liga in:
- `models/model_profile_<LG>_value.json`
- `models/ensemble_weights_<LG>_value.json`

Artefakt-Suffix `_value` aus [artifact_suffix()](../src/football_betting/config.py#L173).

Wenn Value-Artefakte fehlen → Fallback auf das 1X2-Modell ([services.py:556-567](../src/football_betting/api/services.py#L556-L567)).

## 5. Features

Alle aus [FeatureBuilder.build_features()](../src/football_betting/features/builder.py#L86-L242). Für das Value-Modell **aktiv** (nach Blocklist-Filter):

| Feature-Familie | Datei | Beschreibung |
|---|---|---|
| Pi-Ratings | [pi_ratings.py](../src/football_betting/rating/pi_ratings.py) | Heim-/Auswärts-Stärke |
| Form | [form.py](../src/football_betting/features/form.py) | Gleitendes Fenster |
| xG-Proxy | [xg_proxy.py](../src/football_betting/features/xg_proxy.py) | Schussbasiert |
| Real-xG | [real_xg.py](../src/football_betting/features/real_xg.py) | Sofascore, inkl. `has_real_xg`-Flag |
| Squad-Quality | [squad_quality.py](../src/football_betting/features/squad_quality.py) | Sofascore-Lineups |
| H2H | [h2h.py](../src/football_betting/features/h2h.py) | Direkter Vergleich |
| Rest-Days | [rest_days.py](../src/football_betting/features/rest_days.py) | Tage seit letztem Spiel |
| Dynamic Home-Advantage | [home_advantage.py](../src/football_betting/features/home_advantage.py) | Zeitlich gewichtet |
| Standings | [standings.py](../src/football_betting/features/standings.py) | Saisontabelle inkl. Punktabzüge |
| Weather | [weather.py](../src/football_betting/features/weather.py) | opt-in, Kickoff-UTC-basiert |
| League-Meta | inline | `league_avg_goals`, `league_home_adv` |

Für die Value-Pipeline **bewusst entfernt** (via `_apply_blocklist`):
- `market_p_home/draw/away`, `market_margin`, `market_fav_ratio` ([builder.py:203-221](../src/football_betting/features/builder.py#L203-L221))
- `mm_*` aus [market_movement.py](../src/football_betting/features/market_movement.py)
- Microstructure aus [market_microstructure.py](../src/football_betting/features/market_microstructure.py)

## 6. Externe Datenquellen

| Quelle | Verwendung | Modul |
|---|---|---|
| Football-Data CSVs | Historie + Ergebnisse (`data/raw/`) | [data/loader.py](../src/football_betting/data/loader.py) |
| Sofascore (curl_cffi) | Real-xG, Lineups, Event-IDs | [scraping/sofascore.py](../src/football_betting/scraping/sofascore.py) |
| TheOdds-API | Live-Quoten + Opening-Line-Store | [data/odds_snapshots.py](../src/football_betting/data/odds_snapshots.py) |
| Open-Meteo | Wetter (falls aktiviert) | [features/weather.py](../src/football_betting/features/weather.py) |

## 7. Output

`ValueBetOut`-Liste in [TodayPayload](../src/football_betting/api/schemas.py) mit:
- `edge`, `edge_pct`
- `market_prob` (devigged)
- `model_prob`
- `odds`
- `kelly_stake`, `expected_value_pct`
- `confidence` (high / medium / low)

Sortiert via [rank_value_bets()](../src/football_betting/betting/value.py#L148) nach Edge absteigend.

## 8. Sequenzdiagramm (vereinfacht)

```
fixtures_data
   │
   ▼
build_predictions_for_fixtures()
   │
   ├─► load_league()                         [Football-Data CSV]
   │
   ├─► warm_feature_builder(purpose="1x2")
   ├─► warm_feature_builder(purpose="value") [Blocklist: market_*, mm_*]
   │
   ├─► append_odds_snapshot()                [Lead-time guard ≥ 6h]
   ├─► load_odds_snapshots()                 [in market_tracker]
   │
   ├─► build_league_model(purpose="1x2")     → predictions[]
   ├─► build_league_model(purpose="value")   → value_pred
   │
   ▼
find_value_bets(value_pred, bankroll, cfg)
   │   • devig (power)
   │   • edge ≥ 0.03
   │   • 1.30 ≤ odds ≤ 15.0
   │   • EV ≥ min_ev_pct
   │   • Kelly × 0.25, cap 5 %
   ▼
rank_value_bets(by="edge")
   │
   ▼
TodayPayload.value_bets
```

## 9. Wichtige Konfigurationsstellen

- [BettingConfig](../src/football_betting/config.py#L695-L713) — globale Edge/Kelly/Quoten-Defaults
- [ValueModelConfig](../src/football_betting/config.py#L178-L196) — Feature-Blocklist + Kelly-Loss-Hyperparameter für Torch-Heads
- [LeagueModelProfile](../src/football_betting/predict/runtime.py#L40) — Per-Liga-Overrides (aktive Member, Gewichte, Betting-Config)
