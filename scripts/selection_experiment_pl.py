"""Bet-selection experiment on the existing PL walk-forward backtest.

Reconstructs the bet-selection logic from rows in
``data/backtests/walk_forward_PL.json`` (using the same BettingConfig the
backtest used) and reports ROI / hit-rate / CLV bucketed by minimum odds.

Goal: confirm whether filtering bets by min_odds (e.g. ≥2.40) flips PL
from -23.5% ROI to positive territory by avoiding the favorite-trap zone.

No models are loaded; this is a pure post-hoc filter on stored predictions.
"""

from __future__ import annotations

import json
from pathlib import Path

from football_betting.betting.margin import remove_margin
from football_betting.betting.kelly import kelly_stake
from football_betting.config import BETTING_CFG

OUTCOME_KEY = {"H": "prob_home", "D": "prob_draw", "A": "prob_away"}
ODDS_KEY = {"H": "odds_home", "D": "odds_draw", "A": "odds_away"}
OPEN_KEY = {"H": "opening_odds_home", "D": "opening_odds_draw", "A": "opening_odds_away"}

START_BANKROLL = 100.0
MIN_ODDS_BUCKETS = (1.30, 1.80, 2.00, 2.20, 2.40, 2.60, 2.80, 3.00, 3.50, 4.00)


def reconstruct_bets(
    rows: list[dict],
    cfg=BETTING_CFG,
    *,
    mode: str = "any",
    min_edge_override: float | None = None,
) -> list[dict]:
    """Walk rows chronologically, simulate bet-selection, return placed bets.

    mode='any':       place bets on every outcome whose edge clears the
                      threshold (matches BetingConfig defaults — what the
                      production backtest does today).
    mode='top_pick':  per match, only consider the argmax-probability
                      outcome (1 candidate max). Otherwise same filters.
    min_edge_override: if set, replaces cfg.min_edge for this run (useful
                      for sweeping the edge gate when testing top-pick).
    """
    bets = []
    bankroll = START_BANKROLL
    rows_sorted = sorted(rows, key=lambda r: r["date"])
    edge_floor = cfg.min_edge if min_edge_override is None else min_edge_override

    for row in rows_sorted:
        oh, od, oa = row["odds_home"], row["odds_draw"], row["odds_away"]
        if not (oh and od and oa):
            continue
        mh, md, ma = remove_margin(oh, od, oa, method=cfg.devig_method)

        candidates_all = [
            ("H", row["prob_home"], mh, oh, row.get("opening_odds_home")),
            ("D", row["prob_draw"], md, od, row.get("opening_odds_draw")),
            ("A", row["prob_away"], ma, oa, row.get("opening_odds_away")),
        ]

        if mode == "top_pick":
            top = max(candidates_all, key=lambda c: c[1])
            candidates = [top]
        else:
            candidates = candidates_all

        for outcome, model_p, market_p, odds, opening in candidates:
            edge = model_p - market_p
            if edge < edge_floor:
                continue
            if not (cfg.min_odds <= odds <= cfg.max_odds):
                continue
            ev_frac = model_p * odds - 1.0
            if ev_frac < cfg.min_ev_pct:
                continue

            stake = kelly_stake(model_p, odds, bankroll, cfg)
            if stake <= 0:
                continue

            won = row["actual"] == outcome
            profit = stake * (odds - 1) if won else -stake
            bankroll += profit

            clv = None
            if opening and opening > 1.0:
                # CLV vs closing: positive when our placed odds > closing odds
                # Backtest stores closing as `odds_*`; we treat that as the
                # \"close\" (since fixtures don't have a separate closing snap
                # in this dataset, opening_odds in the row is the early line).
                # Per backtest: clv = log(opening / closing); positive means
                # opening was friendlier than closing (we got the better price).
                # Actually `odds_*` here are placement odds. Use opening as
                # placement, current odds_* as closing for CLV.
                pass

            bets.append({
                "date": row["date"],
                "home": row["home_team"],
                "away": row["away_team"],
                "outcome": outcome,
                "actual": row["actual"],
                "won": won,
                "model_p": model_p,
                "market_p": market_p,
                "edge": edge,
                "ev_frac": ev_frac,
                "odds": odds,
                "opening_odds": opening,
                "stake": stake,
                "profit": profit,
                "bankroll_after": bankroll,
            })
    return bets


def clv_for_bet(bet: dict) -> float | None:
    """CLV in odds-fraction terms: positive when placed > closing.

    The backtest stores closing odds as ``odds_*`` (the football-data
    closing line) and earlier-line as ``opening_odds_*``. The walk-forward
    in this run placed at the closing line itself (no separate placement
    snapshot), so this CLV measure is best-effort.
    """
    closing = bet["odds"]
    opening = bet.get("opening_odds")
    if not opening or opening <= 1.0:
        return None
    # CLV: log of placed price / closing price (negative → we paid more)
    # Convention: closing_implied / placed_implied - 1
    closing_implied = 1.0 / closing
    placed_implied = 1.0 / opening
    return placed_implied / closing_implied - 1.0


def summarise(bets: list[dict], label: str) -> dict:
    n = len(bets)
    hits = sum(1 for b in bets if b["won"])
    total_stake = sum(b["stake"] for b in bets)
    total_profit = sum(b["profit"] for b in bets)
    roi = (total_profit / total_stake) if total_stake else 0.0
    hit_rate = (hits / n) if n else 0.0
    avg_odds = (sum(b["odds"] for b in bets) / n) if n else 0.0
    avg_winning_odds = (
        sum(b["odds"] for b in bets if b["won"]) / hits if hits else 0.0
    )

    clv_vals = [clv_for_bet(b) for b in bets]
    clv_vals = [c for c in clv_vals if c is not None]
    clv_mean = (sum(clv_vals) / len(clv_vals)) if clv_vals else 0.0
    clv_pos_rate = (sum(1 for c in clv_vals if c > 0) / len(clv_vals)) if clv_vals else 0.0

    return {
        "label": label,
        "n_bets": n,
        "hits": hits,
        "hit_rate": hit_rate,
        "total_stake": round(total_stake, 2),
        "total_profit": round(total_profit, 2),
        "roi": roi,
        "avg_odds": avg_odds,
        "avg_winning_odds": avg_winning_odds,
        "clv_n": len(clv_vals),
        "clv_mean": clv_mean,
        "clv_pct_positive": clv_pos_rate,
        "final_bankroll": round(START_BANKROLL + total_profit, 2),
    }


def fmt(d: dict) -> str:
    return (
        f"{d['label']:>16s}: n={d['n_bets']:4d} hit={d['hit_rate']:5.1%} "
        f"avg_odds={d['avg_odds']:5.2f} win_odds={d['avg_winning_odds']:5.2f} "
        f"ROI={d['roi']:+7.1%} profit={d['total_profit']:+8.2f} "
        f"CLV={d['clv_mean']:+5.2%} CLV+={d['clv_pct_positive']:5.1%}"
    )


def main() -> None:
    wf_path = Path("data/backtests/walk_forward_PL.json")
    wf = json.loads(wf_path.read_text(encoding="utf-8"))
    rows = wf["folds"][0]["rows"]
    print(f"Loaded {len(rows)} prediction rows from {wf_path}")

    all_bets = reconstruct_bets(rows)
    print(f"Reconstructed {len(all_bets)} bets (no min-odds filter beyond cfg.min_odds)\n")

    print(fmt(summarise(all_bets, "all (>=1.30)")))
    print()
    print("--- Filter by minimum decimal odds ---")
    for floor in MIN_ODDS_BUCKETS:
        filtered = [b for b in all_bets if b["odds"] >= floor]
        print(fmt(summarise(filtered, f">= {floor:.2f}")))

    print()
    print("--- Filter by odds bucket (range) ---")
    bucket_edges = [(1.30, 1.80), (1.80, 2.20), (2.20, 2.60), (2.60, 3.20),
                    (3.20, 4.50), (4.50, 8.00), (8.00, 15.00)]
    for lo, hi in bucket_edges:
        filtered = [b for b in all_bets if lo <= b["odds"] < hi]
        print(fmt(summarise(filtered, f"[{lo:.2f},{hi:.2f})")))

    print()
    print("--- Filter by edge magnitude ---")
    for edge_floor in (0.03, 0.05, 0.08, 0.10, 0.15, 0.20):
        filtered = [b for b in all_bets if b["edge"] >= edge_floor]
        print(fmt(summarise(filtered, f"edge >= {edge_floor:.2f}")))

    # ─────────────────────── Option 2: top-pick only ───────────────────────
    print()
    print("=" * 80)
    print("OPTION 2 — Top-pick only (argmax of model probabilities, 1 per match)")
    print("=" * 80)

    # Sweep the edge floor — including 0.0 to test \"always bet the top pick\"
    for edge_floor in (0.0, 0.03, 0.05, 0.08, 0.10):
        bets = reconstruct_bets(rows, mode="top_pick", min_edge_override=edge_floor)
        print()
        print(f"--- top_pick, min_edge >= {edge_floor:.2f} (n={len(bets)} bets) ---")
        print(fmt(summarise(bets, f"top, e>={edge_floor:.2f}")))
        if not bets:
            continue
        for floor in (1.30, 1.80, 2.00, 2.20, 2.40, 2.60, 3.00, 3.50):
            f_bets = [b for b in bets if b["odds"] >= floor]
            if f_bets:
                print(fmt(summarise(f_bets, f"  +odds>={floor:.2f}")))
        print(f"  --- top-pick odds buckets (edge >= {edge_floor:.2f}) ---")
        for lo, hi in [(1.30, 1.80), (1.80, 2.20), (2.20, 2.60), (2.60, 3.20),
                       (3.20, 4.50), (4.50, 8.00)]:
            f_bets = [b for b in bets if lo <= b["odds"] < hi]
            if f_bets:
                print(fmt(summarise(f_bets, f"  [{lo:.2f},{hi:.2f})")))


if __name__ == "__main__":
    main()
