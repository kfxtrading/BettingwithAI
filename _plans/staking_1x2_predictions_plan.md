# Plan: 1X2 Staking-Allokator – Tages-Bankroll X, konfidenzgewichtet

Erweiterung der bestehenden "Prediction"-Strategie (Argmax-1X2-Pick pro Match) um einen konfigurierbaren Staking-Allokator, der eine feste Tages-Bankroll `X` auf alle Picks eines Tages verteilt – gewichtet nach Modellwahrscheinlichkeit. Grundlage: [./Erweiterungen/Staking-Algorithmen.md](./Erweiterungen/Staking-Algorithmen.md).

## Status quo (Ist-Analyse)

- Predictions werden in [./src/football_betting/api/services.py:366](./src/football_betting/api/services.py#L366) (`build_predictions_for_fixtures`) erzeugt und in `today.json` geschrieben – **ohne Stake-Feld**.
- Stakes werden erst beim Grading in [./src/football_betting/evaluation/grader.py:185](./src/football_betting/evaluation/grader.py#L185) (`prediction_to_tracked_bet`) vergeben: **hart codiert auf 1.0 EUR flat** (Zeile 227).
- Value-Bets haben Kelly-Sizing via [./src/football_betting/betting/kelly.py](./src/football_betting/betting/kelly.py); `BettingConfig` lebt in [./src/football_betting/config.py:347](./src/football_betting/config.py#L347).
- Frontend rendert Predictions in [./web/components/PredictionCard.tsx](./web/components/PredictionCard.tsx) – **kein Stake-Feld sichtbar**; Stakes werden nur bei Value-Bets ([./web/components/ValueBetBadge.tsx:75](./web/components/ValueBetBadge.tsx#L75)) gezeigt.
- Split-Bankroll-Logik unterscheidet bereits zwischen `kind="value"` und `kind="prediction"` ([./tests/test_bankroll_split.py](./tests/test_bankroll_split.py)) – der Allokator muss nur die **Prediction-Seite** korrekt füllen.

## Ziel-Architektur

1. Neues Modul `betting/prediction_stakes.py` mit mehreren Strategien + `allocate_prediction_stakes()`-Entry-Point.
2. Neue Config `PredictionStakingConfig` in `config.py` (Strategie, Bankroll, Hyperparameter).
3. `PredictionOut`-Schema um `stake: float | None` erweitern.
4. `build_predictions_for_fixtures` füllt die Stakes nach dem Sammeln aller Predictions (eine Allokation pro Tag über alle Ligen hinweg).
5. `prediction_to_tracked_bet` liest `pred.stake`, fällt auf 1.0 EUR zurück.
6. Frontend zeigt Stake pro Pick.
7. Tests für Allokator + Invarianten (Σ stakes ≤ X, HHI/N_eff, min-p-Filter, odds-floor).

## Zu ändernde / neue Dateien

### Neu: `src/football_betting/betting/prediction_stakes.py`

Reiner NumPy-Code, keine externen Dependencies. Strategien laut Staking-Algorithmen.md:

- `flat_stakes(X, n)` → Baseline.
- `conf_stakes(X, p)` → `s_i = X · p_i / Σp_j` (Hubáček conf).
- `power_stakes(X, p, k)` → `s_i = X · p_i^k / Σp_j^k` (Softmax-äquivalent).
- `hybrid_stakes(X, p, o, k, odds_floor, min_p)` → **Produktiv-Default**, Power-k=2 mit Odds-Dämpfung (`odds_factor = min(o/odds_floor, 1.0)`) und `min_p`-Threshold. 1:1 aus der Staking-Algorithmen.md Empfehlung (Zeilen 89–108).
- `entropy_stakes(X, P_full)` → nutzt volle (p_H, p_X, p_A)-Verteilung über Shannon-Entropie.
- `diagnostics(stakes) -> dict` → `HHI`, `N_eff`, `max_weight`, `sum`.
- `allocate_prediction_stakes(preds: list[PredictionOut], cfg: PredictionStakingConfig) -> list[float]`: wählt Strategie per `cfg.strategy`, extrahiert `p_max` + zugehörige Quote je Pick, skippt Picks ohne `odds`, gibt monetäre Stakes in gleicher Reihenfolge zurück. Rundung auf 2 Nachkommastellen, Summe garantiert ≤ X (nicht > X durch Rundung).

### Änderung: `src/football_betting/config.py` (nach Zeile 352)

```python
@dataclass(frozen=True, slots=True)
class PredictionStakingConfig:
    strategy: Literal["flat", "conf", "power", "hybrid", "entropy"] = "hybrid"
    daily_bankroll: float = 1000.0
    power_k: float = 2.0
    odds_floor: float = 2.0
    min_p: float = 0.40
```

Plus Modul-Level-Singleton `PREDICTION_STAKING_CFG = PredictionStakingConfig()` analog zu `BETTING_CFG`.

### Änderung: `src/football_betting/api/schemas.py` (`PredictionOut`, Zeile 26)

```python
stake: float | None = None   # monetary units (EUR), filled by staking allocator
```

Default `None` hält Rückwärtskompatibilität zu alten `today.json`-Dateien.

### Änderung: `src/football_betting/api/services.py:366` (`build_predictions_for_fixtures`)

Am Ende der Funktion, nach dem Sammeln aller `predictions`, vor `return TodayPayload(...)`:

```python
from football_betting.betting.prediction_stakes import allocate_prediction_stakes
from football_betting.config import PredictionStakingConfig

staking_cfg = PredictionStakingConfig(daily_bankroll=bankroll)
stakes = allocate_prediction_stakes(predictions, staking_cfg)
predictions = [p.model_copy(update={"stake": s}) for p, s in zip(predictions, stakes)]
```

Parameter `bankroll` wird so an den Allokator weitergereicht – die CLI ([./src/football_betting/cli.py:1041](./src/football_betting/cli.py#L1041)) übergibt ihn bereits via `--bankroll`.

### Änderung: `src/football_betting/evaluation/grader.py:227`

```python
kelly_stake=pred.stake if pred.stake is not None else 1.0,
```

Damit behalten Alt-Snapshots das 1-EUR-Verhalten, neue nutzen den Allokator. `kind="prediction"` bleibt unverändert.

### Änderung: `web/components/PredictionCard.tsx`

Unterhalb des Most-Likely-Outcomes eine Zeile ergänzen:

```tsx
{prediction.stake != null && prediction.stake > 0 && (
  <div className="text-sm text-slate-300">
    Einsatz: <span className="font-semibold">{prediction.stake.toFixed(2)} €</span>
  </div>
)}
```

Plus TypeScript-Typ in `web/lib/api.ts` um `stake?: number | null` erweitern.

### Neu: `tests/test_prediction_stakes.py`

Deckt ab:

- `flat_stakes` → alle gleich, Σ = X.
- `conf_stakes` → Σ = X, proportional zu p.
- `power_stakes(k=2)` → stärkere Konzentration als conf (HHI steigt).
- `hybrid_stakes` → Favoriten (o<2.0) werden gedämpft, Picks mit p<min_p bekommen 0, Σ ≤ X.
- `entropy_stakes` → Σ = X, höhere Gewichtung bei niedrigerer Shannon-Entropie.
- `diagnostics` → HHI in (0,1], N_eff ≤ N.
- `allocate_prediction_stakes` mit `list[PredictionOut]`: Picks ohne `odds` → Stake 0; Gesamtsumme ≤ X; Reihenfolge erhalten.
- Edge-Case: leere Liste / alle unter `min_p` → alle Stakes 0.

## Verifikation

1. `pytest tests/test_prediction_stakes.py -v` — alle neuen Tests grün.
2. `pytest tests/test_bankroll_split.py` — bestehende Split-Logik bleibt grün (Regression).
3. `fb snapshot --bankroll 1000` und inspizieren: `data/snapshots/today.json` → jeder Eintrag in `predictions[]` hat `stake` (monetär, Summe ≤ 1000).
4. `fb serve` + `cd web && npm run dev` → PredictionCard zeigt "Einsatz: XX.XX €".
5. `ruff check . && mypy src` — keine neuen Fehler.
6. Diagnostik ad-hoc (Python-REPL): `diagnostics(stakes)` für einen Produktiv-Snapshot → `N_eff ∈ [8, 11]` laut Staking-Algorithmen.md Zielzone.

## Entscheidungen (vom User bestätigt)

1. **Default-Strategie**: `hybrid` (Power-k=2 mit Odds-Dämpfung, Report-Empfehlung).
2. **CLI-Flag**: `fb snapshot` bekommt zusätzlich `--staking-strategy {flat,conf,power,hybrid,entropy}` (Default aus Config) — an `build_predictions_for_fixtures` weiterreichen und an `PredictionStakingConfig` binden.
3. **Frontend**: `PredictionCard.tsx` zeigt **Stake in EUR + %-Anteil der Bankroll**. `PredictionOut` bekommt zusätzlich `stake_pct: float | None = None`, befüllt in `services.py` via `stake / bankroll * 100`.
4. **min_p-Threshold**: Picks unter `min_p` bekommen Stake 0 EUR, werden aber **weiterhin in der UI angezeigt** — mit Hinweis „Kein Einsatz (Konfidenz < {min_p:.0%})". Frontend-Zweig:

```tsx
{prediction.stake != null && prediction.stake > 0 ? (
  <div>Einsatz: {prediction.stake.toFixed(2)} € ({prediction.stake_pct?.toFixed(1)} %)</div>
) : (
  <div className="text-slate-500 italic">Kein Einsatz (Konfidenz zu niedrig)</div>
)}
```

## Ergänzungen zum Umsetzungsplan (durch die Entscheidungen)

- `PredictionStakingConfig.strategy` Default `"hybrid"`.
- `cli.py snapshot`: neue Option `--staking-strategy` (click.Choice), weitergereicht an `build_predictions_for_fixtures(..., staking_strategy=...)`.
- `build_predictions_for_fixtures` Signatur erweitern um `staking_strategy: str | None = None`; bei `None` → Config-Default.
- `PredictionOut` Felder: `stake: float | None = None`, `stake_pct: float | None = None`.
- Test: `test_allocate_respects_min_p_and_keeps_pick` — Pick mit `p=0.35` erhält `stake=0.0`, bleibt aber in der Ergebnisliste (Reihenfolge + Länge unverändert).
