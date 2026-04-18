"""
Performance index — anonymised public transparency tracker.

Reads `predictions_log.json` via ResultsTracker and emits two artefacts:

* `performance.json`       — anonymised (index-based, no EUR amounts)
* `performance_full.json`  — full detail (EUR, individual bets, ROI)

The public index normalises the bankroll to a starting value of 100:
    index(t) = 100 * balance(t) / INITIAL_BALANCE

See `Erweiterungen/performance-tracker-spec.md` for the rationale.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from football_betting.config import BETTING_CFG, PREDICTIONS_DIR, BettingConfig
from football_betting.tracking.metrics import max_drawdown
from football_betting.tracking.tracker import PredictionRecord, ResultsTracker

INITIAL_BALANCE: float = 1000.0
TRACKING_START_DEFAULT: str = "2026-01-01"
MODEL_VERSION: str = "0.3.0"

PUBLIC_FILENAME: str = "performance.json"
PRIVATE_FILENAME: str = "performance_full.json"


# ───────────────────────── Helpers ─────────────────────────


def compute_rule_hash(cfg: BettingConfig | None = None) -> str:
    """Hash of the active betting rules. Changes when any parameter changes."""
    cfg = cfg or BETTING_CFG
    payload = (
        f"{cfg.min_edge}|{cfg.kelly_fraction}|{cfg.max_stake_pct}"
        f"|{cfg.min_odds}|{cfg.max_odds}"
    )
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:16]


def _bet_profit(rec: PredictionRecord) -> float:
    """Signed profit contribution of a single settled bet (void → 0)."""
    stake = rec.bet_stake or 0.0
    if rec.bet_status == "won" and rec.bet_odds:
        return stake * (rec.bet_odds - 1.0)
    if rec.bet_status == "lost":
        return -stake
    return 0.0


def _parse_date(s: str) -> date:
    return datetime.strptime(s[:10], "%Y-%m-%d").date()


# ───────────────────────── Equity curve ─────────────────────────


@dataclass(slots=True)
class EquityPoint:
    date: str
    balance_eur: float
    n_bets_cumulative: int


def build_daily_equity_curve(
    completed: list[PredictionRecord],
    tracking_start: str = TRACKING_START_DEFAULT,
    today: date | None = None,
    initial_balance: float = INITIAL_BALANCE,
) -> list[EquityPoint]:
    """Build a per-calendar-day equity curve.

    Days without a settled bet carry the previous day's balance forward.
    """
    start = _parse_date(tracking_start)
    today = today or date.today()
    if today < start:
        today = start

    # Group PnL by date (completed bets only)
    pnl_by_day: dict[date, float] = {}
    bets_by_day: dict[date, int] = {}
    for rec in completed:
        try:
            d = _parse_date(rec.date)
        except ValueError:
            continue
        if d < start or d > today:
            continue
        pnl_by_day[d] = pnl_by_day.get(d, 0.0) + _bet_profit(rec)
        bets_by_day[d] = bets_by_day.get(d, 0) + 1

    curve: list[EquityPoint] = []
    balance = initial_balance
    n_bets = 0
    d = start
    one_day = timedelta(days=1)
    while d <= today:
        balance += pnl_by_day.get(d, 0.0)
        n_bets += bets_by_day.get(d, 0)
        curve.append(
            EquityPoint(
                date=d.isoformat(),
                balance_eur=round(balance, 2),
                n_bets_cumulative=n_bets,
            )
        )
        d += one_day
    return curve


# ───────────────────────── Aggregates ─────────────────────────


def _aggregate_stats(completed: list[PredictionRecord]) -> dict[str, Any]:
    """Wins, losses, hit-rate, total stake, avg odds — void bets excluded from rates."""
    n_bets = len(completed)
    settled = [r for r in completed if r.bet_status in ("won", "lost")]
    wins = sum(1 for r in settled if r.bet_status == "won")
    losses = sum(1 for r in settled if r.bet_status == "lost")
    total_stake = sum((r.bet_stake or 0.0) for r in completed)
    odds_list = [r.bet_odds for r in completed if r.bet_odds]
    avg_odds = sum(odds_list) / len(odds_list) if odds_list else 0.0
    hit_rate = wins / len(settled) if settled else None
    return {
        "n_bets": n_bets,
        "wins": wins,
        "losses": losses,
        "hit_rate": hit_rate,
        "total_stake": total_stake,
        "avg_stake": total_stake / n_bets if n_bets else 0.0,
        "avg_odds": avg_odds,
    }


# ───────────────────────── Payload builders ─────────────────────────


def build_public_payload(
    curve: list[EquityPoint],
    stats: dict[str, Any],
    *,
    tracking_start: str,
    updated_at: str,
    initial_balance: float = INITIAL_BALANCE,
    rule_hash: str | None = None,
) -> dict[str, Any]:
    balances = [p.balance_eur for p in curve] or [initial_balance]
    current_balance = balances[-1]
    ath = max(balances)
    dd = max_drawdown(balances)
    current_dd_pct = (ath - current_balance) / ath if ath > 0 else 0.0
    current_dd_pct = max(0.0, current_dd_pct)

    return {
        "updated_at": updated_at,
        "tracking_started_at": tracking_start,
        "n_days_tracked": len(curve),
        "n_bets": stats["n_bets"],
        "hit_rate": round(stats["hit_rate"], 4) if stats["hit_rate"] is not None else None,
        "current_index": round(100.0 * current_balance / initial_balance, 2),
        "all_time_high_index": round(100.0 * ath / initial_balance, 2),
        "max_drawdown_pct": round(float(dd["max_drawdown_pct"]), 4),
        "current_drawdown_pct": round(current_dd_pct, 4),
        "equity_curve": [
            {
                "date": p.date,
                "index": round(100.0 * p.balance_eur / initial_balance, 2),
                "n_bets_cumulative": p.n_bets_cumulative,
            }
            for p in curve
        ],
        "rule_hash": rule_hash or compute_rule_hash(),
        "model_version": MODEL_VERSION,
    }


def build_private_payload(
    curve: list[EquityPoint],
    completed: list[PredictionRecord],
    stats: dict[str, Any],
    *,
    tracking_start: str,
    updated_at: str,
    initial_balance: float = INITIAL_BALANCE,
    rule_hash: str | None = None,
    recent_limit: int = 50,
) -> dict[str, Any]:
    balances = [p.balance_eur for p in curve] or [initial_balance]
    current_balance = balances[-1]
    ath = max(balances)
    dd = max_drawdown(balances)
    current_dd_pct = max(0.0, (ath - current_balance) / ath) if ath > 0 else 0.0

    recent = sorted(completed, key=lambda r: r.date, reverse=True)[:recent_limit]
    recent_bets = []
    for r in recent:
        recent_bets.append(
            {
                "date": r.date,
                "league": r.league,
                "match": f"{r.home_team} vs {r.away_team}",
                "bet": r.bet_outcome,
                "odds": r.bet_odds,
                "stake_eur": round(r.bet_stake, 2) if r.bet_stake else 0.0,
                "edge_pct": round(r.bet_edge, 4) if r.bet_edge is not None else None,
                "status": r.bet_status,
                "profit_eur": round(_bet_profit(r), 2),
            }
        )

    return {
        "updated_at": updated_at,
        "tracking_started_at": tracking_start,
        "initial_balance_eur": round(initial_balance, 2),
        "current_balance_eur": round(current_balance, 2),
        "all_time_high_balance_eur": round(ath, 2),
        "roi_pct": round((current_balance / initial_balance) - 1.0, 4),
        "n_bets": stats["n_bets"],
        "wins": stats["wins"],
        "losses": stats["losses"],
        "hit_rate": round(stats["hit_rate"], 4) if stats["hit_rate"] is not None else None,
        "avg_stake_eur": round(stats["avg_stake"], 2),
        "avg_odds_taken": round(stats["avg_odds"], 3),
        "max_drawdown_pct": round(float(dd["max_drawdown_pct"]), 4),
        "max_drawdown_eur": round(float(dd["max_drawdown_abs"]), 2),
        "current_drawdown_pct": round(current_dd_pct, 4),
        "equity_curve": [
            {
                "date": p.date,
                "balance_eur": p.balance_eur,
                "n_bets_cumulative": p.n_bets_cumulative,
            }
            for p in curve
        ],
        "recent_bets": recent_bets,
        "rule_hash": rule_hash or compute_rule_hash(),
        "model_version": MODEL_VERSION,
    }


# ───────────────────────── IO ─────────────────────────


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def compute_payloads(
    tracker: ResultsTracker | None = None,
    *,
    tracking_start: str = TRACKING_START_DEFAULT,
    today: date | None = None,
    initial_balance: float = INITIAL_BALANCE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute (public, private) payloads from a ResultsTracker."""
    if tracker is None:
        tracker = ResultsTracker()
        tracker.load()
    completed = tracker.completed_bets()
    completed.sort(key=lambda r: r.date)

    curve = build_daily_equity_curve(
        completed,
        tracking_start=tracking_start,
        today=today,
        initial_balance=initial_balance,
    )
    stats = _aggregate_stats(completed)
    updated_at = _now_iso_utc()
    rule_hash = compute_rule_hash()

    public = build_public_payload(
        curve,
        stats,
        tracking_start=tracking_start,
        updated_at=updated_at,
        initial_balance=initial_balance,
        rule_hash=rule_hash,
    )
    private = build_private_payload(
        curve,
        completed,
        stats,
        tracking_start=tracking_start,
        updated_at=updated_at,
        initial_balance=initial_balance,
        rule_hash=rule_hash,
    )
    return public, private


def write_performance_files(
    *,
    tracking_start: str = TRACKING_START_DEFAULT,
    today: date | None = None,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Compute + write both JSON artefacts. Returns (public_path, private_path)."""
    output_dir = output_dir or PREDICTIONS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    public, private = compute_payloads(tracking_start=tracking_start, today=today)

    public_path = output_dir / PUBLIC_FILENAME
    private_path = output_dir / PRIVATE_FILENAME
    public_path.write_text(
        json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    private_path.write_text(
        json.dumps(private, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return public_path, private_path


__all__ = [
    "INITIAL_BALANCE",
    "TRACKING_START_DEFAULT",
    "MODEL_VERSION",
    "PUBLIC_FILENAME",
    "PRIVATE_FILENAME",
    "EquityPoint",
    "build_daily_equity_curve",
    "build_public_payload",
    "build_private_payload",
    "compute_payloads",
    "compute_rule_hash",
    "write_performance_files",
]
