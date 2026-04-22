"""Grade historical value bets against football-data.co.uk CSV results.

Output schema (JSON lines in ``data/graded_bets.jsonl``)::

    {
      "date": "2026-04-18",
      "league": "PL",
      "league_name": "Premier League",
      "home_team": "Tottenham",
      "away_team": "Brighton",
      "outcome": "A",
      "bet_label": "Brighton Auswärtssieg",
      "odds": 2.19,
      "stake": 33.26,
      "ft_result": "A",
      "ft_score": "1-2",
      "status": "won",
      "pnl": 39.46
    }

``status`` is one of ``won``, ``lost``, ``pending`` (result not yet in CSVs).
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from football_betting.api.schemas import PredictionOut, TodayPayload, ValueBetOut
from football_betting.config import DATA_DIR, LEAGUES, RAW_DIR, SNAPSHOT_DIR

GRADED_FILE = DATA_DIR / "graded_bets.jsonl"

_CODE_TO_KEY = {cfg.code: key for key, cfg in LEAGUES.items()}


@dataclass
class GradedBet:
    date: str
    league: str
    league_name: str
    home_team: str
    away_team: str
    outcome: str
    bet_label: str
    odds: float
    stake: float
    ft_result: str | None
    ft_score: str | None
    status: str  # "won" | "lost" | "pending"
    pnl: float
    kind: str = "value"  # "value" | "prediction"
    model_prob: float | None = None


def _norm(name: str) -> str:
    return name.lower().strip()


def _load_results_for_league(code: str) -> dict[tuple[date, str, str], tuple[str, int, int]]:
    """Return {(match_date, home_norm, away_norm): (ftr, fthg, ftag)} for a league.

    Merges football-data.co.uk CSV archive (authoritative) with the live
    results cache populated by the Odds-API poller. CSV wins on conflict
    so the nightly reconcile corrects any live misses.
    """
    out: dict[tuple[date, str, str], tuple[str, int, int]] = {}
    # Live results first — CSV overrides below.
    try:
        from football_betting.evaluation.live_results import load_live_results_for_code

        out.update(load_live_results_for_code(code))
    except Exception:
        # Live cache is optional — never let it break grading.
        pass
    for csv_path in RAW_DIR.glob(f"{code}_*.csv"):
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    raw_date = (row.get("Date") or "").strip()
                    if not raw_date:
                        continue
                    try:
                        d = datetime.strptime(raw_date, "%d/%m/%Y").date()
                    except ValueError:
                        try:
                            d = datetime.strptime(raw_date, "%d/%m/%y").date()
                        except ValueError:
                            continue
                    home = _norm(row.get("HomeTeam") or "")
                    away = _norm(row.get("AwayTeam") or "")
                    ftr = (row.get("FTR") or "").strip().upper()
                    if not (home and away and ftr in {"H", "D", "A"}):
                        continue
                    try:
                        fthg = int(row["FTHG"])
                        ftag = int(row["FTAG"])
                    except (KeyError, ValueError, TypeError):
                        fthg = ftag = 0
                    out[(d, home, away)] = (ftr, fthg, ftag)
        except OSError:
            continue
    return out


def _stake_amount(bet: ValueBetOut) -> float:
    """Return the € stake already carried on the value bet.

    ``ValueBetOut.kelly_stake`` is produced by
    :func:`football_betting.betting.kelly.kelly_stake`, which returns a
    monetary amount (``bankroll * capped_fraction``) — *not* a fractional
    unit. Previously this helper multiplied by 100 under the mistaken
    assumption of a (0..1) fraction, which inflated every stake 100× and
    blew up the public equity index.
    """
    return round(bet.kelly_stake, 2)


def _grade_one(bet: ValueBetOut, results: dict, kind: str = "value") -> GradedBet:
    try:
        match_date = datetime.strptime(bet.date, "%Y-%m-%d").date()
    except ValueError:
        match_date = date.min
    key = (match_date, _norm(bet.home_team), _norm(bet.away_team))
    stake = _stake_amount(bet)

    model_prob = getattr(bet, "model_prob", None)
    hit = results.get(key)
    if hit is None:
        return GradedBet(
            date=bet.date,
            league=bet.league,
            league_name=bet.league_name,
            home_team=bet.home_team,
            away_team=bet.away_team,
            outcome=bet.outcome,
            bet_label=bet.bet_label,
            odds=bet.odds,
            stake=stake,
            ft_result=None,
            ft_score=None,
            status="pending",
            pnl=0.0,
            kind=kind,
            model_prob=model_prob,
        )
    ftr, fthg, ftag = hit
    won = ftr == bet.outcome
    pnl = round(stake * (bet.odds - 1.0) if won else -stake, 2)
    return GradedBet(
        date=bet.date,
        league=bet.league,
        league_name=bet.league_name,
        home_team=bet.home_team,
        away_team=bet.away_team,
        outcome=bet.outcome,
        bet_label=bet.bet_label,
        odds=bet.odds,
        stake=stake,
        ft_result=ftr,
        ft_score=f"{fthg}-{ftag}",
        status="won" if won else "lost",
        pnl=pnl,
        kind=kind,
        model_prob=model_prob,
    )


def grade_bets(bets: Iterable[ValueBetOut], *, kind: str = "value") -> list[GradedBet]:
    """Grade a batch of value bets against the football-data CSV archive."""
    bets = list(bets)
    results_by_league: dict[str, dict] = {}
    graded: list[GradedBet] = []
    for bet in bets:
        cfg = LEAGUES.get(bet.league)
        if cfg is None:
            continue
        code = cfg.code
        if code not in results_by_league:
            results_by_league[code] = _load_results_for_league(code)
        graded.append(_grade_one(bet, results_by_league[code], kind=kind))
    return graded


def prediction_to_tracked_bet(pred: PredictionOut) -> ValueBetOut | None:
    """Wrap a most-likely prediction as a ValueBetOut with flat 1 € stake.

    Returned bet is structurally identical to a real value bet so the grader
    pipeline can grade it uniformly. Skips predictions without market odds —
    PnL cannot be computed without them.
    """
    if pred.odds is None:
        return None
    outcome = pred.most_likely
    if outcome == "H":
        odds = pred.odds.home
        model_prob = pred.prob_home
        side = pred.home_team
        suffix = "Heimsieg"
    elif outcome == "A":
        odds = pred.odds.away
        model_prob = pred.prob_away
        side = pred.away_team
        suffix = "Auswärtssieg"
    else:
        odds = pred.odds.draw
        model_prob = pred.prob_draw
        side = "Unentschieden"
        suffix = ""
    if odds <= 1.0:
        return None
    bet_label = f"{side} {suffix}".strip()
    market_prob = 1.0 / odds
    return ValueBetOut(
        date=pred.date,
        league=pred.league,
        league_name=pred.league_name,
        home_team=pred.home_team,
        away_team=pred.away_team,
        outcome=outcome,
        bet_label=bet_label,
        odds=odds,
        model_prob=model_prob,
        market_prob=market_prob,
        edge=0.0,
        edge_pct=0.0,
        kelly_stake=pred.stake if pred.stake is not None else 1.0,
        expected_value_pct=0.0,
        confidence="low",
    )


def load_snapshot(path: Path) -> TodayPayload | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    try:
        return TodayPayload(**raw)
    except Exception:
        return None


def iter_historical_snapshots() -> Iterable[tuple[str, TodayPayload]]:
    """Yield (date, payload) pairs for every dated snapshot in SNAPSHOT_DIR."""
    for path in sorted(SNAPSHOT_DIR.glob("*.json")):
        stem = path.stem
        if stem in {"today"} or not stem[:10].replace("-", "").isdigit():
            continue
        payload = load_snapshot(path)
        if payload is not None:
            yield stem[:10], payload


def write_graded(graded: Iterable[GradedBet]) -> Path:
    """Rewrite ``graded_bets.jsonl`` atomically with the given rows."""
    GRADED_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = GRADED_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in graded:
            fh.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
    tmp.replace(GRADED_FILE)
    return GRADED_FILE


def load_graded() -> list[GradedBet]:
    if not GRADED_FILE.exists():
        return []
    out: list[GradedBet] = []
    with GRADED_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(GradedBet(**json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue
    return out


def graded_as_prediction_records() -> list:
    """Return graded bets as ``PredictionRecord`` so they plug into the
    existing performance pipeline (bankroll curve, summary, public index)
    without duplicating the aggregation logic.

    Only SETTLED bets are emitted — pending bets would inflate ``n_bets`` in
    the aggregate summary before they have a result.
    """
    from football_betting.tracking.tracker import PredictionRecord

    records: list = []
    for g in load_graded():
        if g.status == "pending":
            continue
        records.append(
            PredictionRecord(
                date=g.date,
                league=g.league,
                home_team=g.home_team,
                away_team=g.away_team,
                model_name="graded",
                prob_home=0.0,
                prob_draw=0.0,
                prob_away=0.0,
                bet_outcome=g.outcome,  # type: ignore[arg-type]
                bet_odds=g.odds,
                bet_stake=g.stake,
                actual_outcome=g.ft_result,  # type: ignore[arg-type]
                bet_status=g.status,  # type: ignore[arg-type]
            )
        )
    return records
