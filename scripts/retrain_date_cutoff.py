"""Per-league out-of-sample retrain with explicit date cutoff + persistence.

Train: every match for ``--league`` from data start through ``--cutoff``.
Test:  matches for the same league from ``--cutoff`` + 1 day through
       ``--test-end`` (whatever exists).

The script
  * trains CatBoost on the date-filtered match list using the production
    ``CatBoostPredictor.fit`` workflow (chronological walk, time-decay
    weights, last-15% chrono val slice for early stopping). Calibration
    is INTENTIONALLY DISABLED — fitting an isotonic/auto calibrator on
    a small val slice (~200 matches) overfits and degrades short test
    windows; raw CatBoost softmax is well-calibrated when train data
    is plentiful.
  * persists the trained CatBoost + features.txt to the standard
    ``models/catboost_{LEAGUE}.*`` paths and rewrites
    ``models/model_profile_{LEAGUE}.json`` to ``model_kind=catboost`` /
    ``active_members=("catboost",)`` so the prediction pipeline picks
    up THIS model and ignores the now-stale MLP / Sequence artefacts
    (those were trained on the pre-Sofascore-fix feature set).
  * walks the test window chronologically with the trained predictor
    and reports probabilistic metrics + a selection-bucket sweep.

Usage:
    python scripts/retrain_date_cutoff.py --league BL
    python scripts/retrain_date_cutoff.py --league PL --cutoff 2026-03-01
    python scripts/retrain_date_cutoff.py --league PL --test-end 2026-04-25

To re-introduce MLP / Sequence into the ensemble after this retrain:
    fb train-mlp --league {LEAGUE}
    fb train-sequence --league {LEAGUE}
    fb tune-ensemble --league {LEAGUE} --val-season 2024-25 --objective rps
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np

# Make the local `_pl_sweep_configs` module importable when this script is
# run directly (e.g. ``python scripts/retrain_date_cutoff.py``).
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from _pl_sweep_configs import CONFIGS as PL_SWEEP_CONFIGS  # noqa: E402
from _pl_sweep_configs import SweepConfig, get_config  # noqa: E402

from football_betting.betting.kelly import kelly_stake  # noqa: E402
from football_betting.betting.margin import remove_margin  # noqa: E402
from football_betting.config import (  # noqa: E402
    BETTING_CFG,
    CATBOOST_CFG,
    FEATURE_CFG,
    MODELS_DIR,
    CalibrationConfig,
    artifact_suffix,
)
from football_betting.data.loader import load_league  # noqa: E402
from football_betting.data.models import Fixture  # noqa: E402
from football_betting.predict.catboost_model import CatBoostPredictor  # noqa: E402
from football_betting.predict.poisson import PoissonModel  # noqa: E402
from football_betting.predict.runtime import (  # noqa: E402
    LeagueModelProfile,
    make_feature_builder,
    resolve_model_profile,
    save_model_profile,
    stage_sofascore_for_seasons,
)

PURPOSE = "1x2"
WARMUP_GAMES = 100
DEFAULT_CUTOFF = date(2026, 3, 1)
DEFAULT_TEST_END = date(2026, 4, 25)
LEAGUES_ALL = ("PL", "CH", "BL", "SA", "LL")

OUTCOME_TO_INT = {"H": 0, "D": 1, "A": 2}
START_BANKROLL = 100.0

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports"


# ────────────────────────── Production retrain ──────────────────────────

def retrain_and_save(
    league: str,
    cutoff: date,
    test_end: date,
    *,
    sweep: SweepConfig | None = None,
    save_as: Path | None = None,
) -> tuple[CatBoostPredictor, list, list, dict[str, Any]]:
    """Train CatBoost on ``league`` matches ≤ ``cutoff`` and persist.

    When ``sweep`` is given, its FeatureConfig / CatBoostConfig overrides
    are applied and ``calibrate``/``calibration_method`` come from it. The
    artefact lands at ``save_as`` (or ``models/catboost_{league}.cbm`` if
    ``save_as`` is None). The production profile is only rewritten when
    we wrote to the production path — sweep runs leave it alone.

    Returns the predictor, train/test match lists, and a ``train_info``
    dict (best_iter, feature counts, ...).
    """
    tag = f"[{league}]"
    matches = load_league(league)
    matches.sort(key=lambda m: m.date)
    train_matches = [m for m in matches if m.date <= cutoff]
    test_matches = [m for m in matches if cutoff < m.date <= test_end]
    print(
        f"{tag} train={len(train_matches)} matches ({train_matches[0].date} → "
        f"{train_matches[-1].date}); test={len(test_matches)} matches "
        f"({test_matches[0].date if test_matches else '∅'} → "
        f"{test_matches[-1].date if test_matches else '∅'})"
    )
    if sweep is not None:
        print(f"{tag} Sweep config: {sweep.name} — {sweep.description}")

    fb = make_feature_builder(purpose=PURPOSE)
    if sweep is not None and sweep.feature_overrides:
        fb.cfg = replace(fb.cfg, **sweep.feature_overrides)
        print(f"{tag} FeatureConfig overrides: {sweep.feature_overrides}")

    seasons = {m.season for m in matches}
    staged = stage_sofascore_for_seasons(fb, league, seasons)
    print(f"{tag} Sofascore staged: {staged} matches across {len(seasons)} seasons")

    cb_cfg = CATBOOST_CFG
    if sweep is not None and sweep.catboost_overrides:
        cb_cfg = replace(cb_cfg, **sweep.catboost_overrides)
        print(f"{tag} CatBoostConfig overrides: {sweep.catboost_overrides}")

    calibration_cfg = None
    if sweep is not None and sweep.calibrate and sweep.calibration_method:
        calibration_cfg = CalibrationConfig(method=sweep.calibration_method)

    calibrate = bool(sweep is not None and sweep.calibrate)
    predictor = CatBoostPredictor(
        feature_builder=fb,
        cfg=cb_cfg,
        calibration_cfg=calibration_cfg,
        purpose=PURPOSE,
    )
    cal_status = "auto" if calibration_cfg is None else calibration_cfg.method
    print(
        f"{tag} Training CatBoost (calibrate={calibrate}"
        f"{', cal_method=' + cal_status if calibrate else ''})…"
    )
    result = predictor.fit(
        train_matches, warmup_games=WARMUP_GAMES, calibrate=calibrate
    )
    print(
        f"{tag} Trained: n_train={result['n_train']}, n_val={result['n_val']}, "
        f"features={result['n_features']}, "
        f"best_iter={result['best_iteration']}"
    )

    suffix = artifact_suffix(PURPOSE)
    is_prod_path = save_as is None
    model_path = save_as or (MODELS_DIR / f"catboost_{league}{suffix}.cbm")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    predictor.save(model_path)
    print(f"{tag} Saved: {model_path}")
    print(f"{tag} Saved: {model_path.with_suffix('.features.txt')}")
    if predictor.calibrator and predictor.calibrator.is_fitted:
        print(f"{tag} Saved: {model_path.with_suffix('.calibrator.joblib')}")
    else:
        stale_cal = model_path.with_suffix(".calibrator.joblib")
        if stale_cal.exists():
            stale_cal.unlink()
            print(f"{tag} Removed stale calibrator: {stale_cal}")

    if is_prod_path:
        existing = resolve_model_profile(league, purpose=PURPOSE)
        cal_method = (
            predictor.calibrator.cfg.method
            if predictor.calibrator and predictor.calibrator.is_fitted
            else None
        )
        if existing is not None and cal_method is None:
            existing = replace(existing, calibration_method=None)
        if existing is None:
            new_profile = LeagueModelProfile(
                league_key=league,
                purpose=PURPOSE,
                model_kind="catboost",
                active_members=("catboost",),
                calibration_method=cal_method,
            )
        else:
            new_profile = replace(
                existing,
                model_kind="catboost",
                active_members=("catboost",),
                calibration_method=cal_method,
                weight_objective=None,
                weight_blend=None,
            )
        save_model_profile(new_profile)
        print(f"{tag} Profile rewritten -> {new_profile.model_kind}, "
              f"active={list(new_profile.active_members)}, "
              f"calibration={new_profile.calibration_method}")
    else:
        print(f"{tag} Sweep mode: production profile NOT rewritten")

    print(f"\n{tag} Top 15 CatBoost feature importances:")
    for feat, imp in result["feature_importance"][:15]:
        print(f"  {imp:6.2f}  {feat}")

    train_info = {
        "n_train": int(result["n_train"]),
        "n_val": int(result["n_val"]),
        "n_features": int(result["n_features"]),
        "best_iteration": int(result["best_iteration"]),
        "top_15_features": [
            {"feature": f, "importance": float(imp)}
            for f, imp in result["feature_importance"][:15]
        ],
        "model_path": str(model_path),
    }
    return predictor, train_matches, test_matches, train_info


# ────────────────────────── Test-window evaluation ──────────────────────

def evaluate_test_window(
    predictor: CatBoostPredictor, test_matches: list
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    """Walk test matches chronologically with the trained predictor.

    For each match: predict, record probs+meta, then update fb state with
    the actual outcome (no leakage between test rows).
    """
    fb = predictor.feature_builder
    poisson = PoissonModel(pi_ratings=fb.pi_ratings)

    cb_probs: list[list[float]] = []
    poisson_probs: list[list[float]] = []
    y: list[int] = []
    meta: list[dict[str, Any]] = []

    for match in sorted(test_matches, key=lambda m: m.date):
        # Build the fixture WITH closing-line odds (and opening + kickoff
        # if available). Without odds, ``features_for_fixture`` zero-fills
        # the entire market_p_* / market_margin / market_fav_ratio family,
        # which are the highest-importance features the model was trained
        # on — leaking train/test distribution mismatch that destroys
        # predictions on otherwise well-priced fixtures.
        fixture = Fixture(
            date=match.date,
            league=match.league,
            home_team=match.home_team,
            away_team=match.away_team,
            odds=match.odds,
            kickoff_datetime_utc=match.kickoff_datetime_utc,
            season=match.season,
        )
        cb_pred = predictor.predict(fixture)
        po_pred = poisson.predict(fixture)

        cb_probs.append([cb_pred.prob_home, cb_pred.prob_draw, cb_pred.prob_away])
        poisson_probs.append([po_pred.prob_home, po_pred.prob_draw, po_pred.prob_away])
        y.append(OUTCOME_TO_INT[match.result])
        meta.append({
            "date": match.date.isoformat(),
            "home": match.home_team,
            "away": match.away_team,
            "actual": match.result,
            "home_goals": match.home_goals,
            "away_goals": match.away_goals,
            "odds_home": match.odds.home if match.odds else None,
            "odds_draw": match.odds.draw if match.odds else None,
            "odds_away": match.odds.away if match.odds else None,
            "season": match.season,
        })

        # Update state for next test match (chronological correctness)
        fb.update_with_match(match)

    return np.asarray(cb_probs), np.asarray(poisson_probs), meta if y else []


# ────────────────────────── Metrics + selection ─────────────────────────

def probabilistic_metrics(probs: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """RPS / Brier / log-loss / hit-rate using the codebase convention
    (RPS = 0.5 × Σ (cumP − cumA)² over k=0..K-2)."""
    eps = 1e-12
    n = len(y)
    one_hot = np.zeros_like(probs)
    one_hot[np.arange(n), y] = 1.0
    cum_p = np.cumsum(probs, axis=1)[:, :-1]
    cum_a = np.cumsum(one_hot, axis=1)[:, :-1]
    rps = float(0.5 * np.mean(np.sum((cum_p - cum_a) ** 2, axis=1)))
    brier = float(np.mean(np.sum((probs - one_hot) ** 2, axis=1)))
    log_loss = float(-np.mean(np.log(np.clip(probs[np.arange(n), y], eps, 1.0))))
    hit_rate = float(np.mean(np.argmax(probs, axis=1) == y))
    return {
        "rps": rps, "brier": brier, "log_loss": log_loss,
        "hit_rate": hit_rate, "n": n,
    }


def selection_sweep(
    probs: np.ndarray, meta: list[dict[str, Any]], cfg=BETTING_CFG, *, mode: str
) -> list[dict[str, Any]]:
    """Reconstruct bets using the production BettingConfig logic."""
    bets: list[dict[str, Any]] = []
    bankroll = START_BANKROLL
    for i, m in enumerate(meta):
        oh, od, oa = m["odds_home"], m["odds_draw"], m["odds_away"]
        if not (oh and od and oa):
            continue
        ph, pd_, pa = probs[i]
        mh, md_, ma = remove_margin(oh, od, oa, method=cfg.devig_method)
        candidates = [
            ("H", float(ph), mh, oh),
            ("D", float(pd_), md_, od),
            ("A", float(pa), ma, oa),
        ]
        if mode == "top_pick":
            candidates = [max(candidates, key=lambda c: c[1])]

        for outcome, model_p, market_p, odds in candidates:
            edge = model_p - market_p
            if edge < cfg.min_edge:
                continue
            if not (cfg.min_odds <= odds <= cfg.max_odds):
                continue
            if model_p * odds - 1.0 < cfg.min_ev_pct:
                continue
            stake = kelly_stake(model_p, odds, bankroll, cfg)
            if stake <= 0:
                continue
            won = m["actual"] == outcome
            profit = stake * (odds - 1) if won else -stake
            bankroll += profit
            bets.append({
                "date": m["date"], "home": m["home"], "away": m["away"],
                "outcome": outcome, "actual": m["actual"], "won": won,
                "model_p": model_p, "market_p": market_p, "edge": edge,
                "odds": odds, "stake": stake, "profit": profit,
            })
    return bets


def fmt_bets(bets: list[dict[str, Any]], label: str) -> str:
    n = len(bets)
    if n == 0:
        return f"{label:>22s}: n=0"
    hits = sum(1 for b in bets if b["won"])
    total_stake = sum(b["stake"] for b in bets)
    total_profit = sum(b["profit"] for b in bets)
    roi = total_profit / total_stake if total_stake else 0.0
    avg_odds = sum(b["odds"] for b in bets) / n
    win_odds = sum(b["odds"] for b in bets if b["won"]) / hits if hits else 0.0
    breakeven = 1.0 / avg_odds if avg_odds else 0.0
    return (
        f"{label:>22s}: n={n:3d} hit={hits / n:5.1%} "
        f"avg_odds={avg_odds:5.2f} win_odds={win_odds:5.2f} "
        f"breakeven_hit={breakeven:5.1%} ROI={roi:+7.1%} "
        f"profit={total_profit:+7.2f}"
    )


# ────────────────────────── Driver ───────────────────────────────────────

def _bucket_summary(bets: list[dict[str, Any]]) -> dict[str, Any]:
    if not bets:
        return {"n_bets": 0}
    hits = sum(1 for b in bets if b["won"])
    total_stake = sum(b["stake"] for b in bets)
    total_profit = sum(b["profit"] for b in bets)
    avg_odds = sum(b["odds"] for b in bets) / len(bets)
    return {
        "n_bets": len(bets),
        "hits": hits,
        "hit_rate": hits / len(bets),
        "avg_odds": avg_odds,
        "breakeven_hit": (1.0 / avg_odds) if avg_odds else 0.0,
        "total_stake": total_stake,
        "total_profit": total_profit,
        "roi": (total_profit / total_stake) if total_stake else 0.0,
    }


def run(
    league: str,
    cutoff: date,
    test_end: date,
    *,
    sweep: SweepConfig | None = None,
    save_as: Path | None = None,
) -> None:
    tag = f"[{league}]"
    label = f" config={sweep.name}" if sweep is not None else ""
    print(f"=== {league} date-cutoff retrain: train ≤ {cutoff}, test ≤ {test_end}{label} ===\n")
    predictor, _, test_matches, train_info = retrain_and_save(
        league, cutoff, test_end, sweep=sweep, save_as=save_as
    )

    if not test_matches:
        print("\nNo test matches in window — skipping evaluation.")
        return

    print(f"\n{tag} Walking test window for predictions…")
    cb_probs, po_probs, meta = evaluate_test_window(predictor, test_matches)
    y = np.asarray([OUTCOME_TO_INT[m["actual"]] for m in meta])
    blend = 0.85 * cb_probs + 0.15 * po_probs

    print("\n=== Probabilistic metrics on test window ===")
    prob_metrics: dict[str, dict[str, float]] = {}
    for name, probs in [
        ("CatBoost", cb_probs),
        ("Poisson", po_probs),
        ("Blend(.85/.15)", blend),
    ]:
        m = probabilistic_metrics(probs, y)
        prob_metrics[name] = m
        print(
            f"  {name:>16s}: n={m['n']:3d}  RPS={m['rps']:.4f}  "
            f"Brier={m['brier']:.4f}  LogLoss={m['log_loss']:.4f}  "
            f"hit={m['hit_rate']:.1%}"
        )

    print("\n=== Selection sweep on test window (CatBoost-only — matches saved profile) ===")
    print("\n--- any value bet ---")
    bets_any = selection_sweep(cb_probs, meta, mode="any")
    print(fmt_bets(bets_any, "all"))
    any_buckets: dict[str, dict[str, Any]] = {"all": _bucket_summary(bets_any)}
    for lo, hi in [(1.30, 1.80), (1.80, 2.20), (2.20, 2.60), (2.60, 3.20),
                   (3.20, 4.50), (4.50, 8.00)]:
        bucket = [b for b in bets_any if lo <= b["odds"] < hi]
        any_buckets[f"[{lo:.2f},{hi:.2f})"] = _bucket_summary(bucket)
        if bucket:
            print(fmt_bets(bucket, f"[{lo:.2f},{hi:.2f})"))

    print("\n--- top-pick only ---")
    bets_top = selection_sweep(cb_probs, meta, mode="top_pick")
    print(fmt_bets(bets_top, "all"))
    top_buckets: dict[str, dict[str, Any]] = {"all": _bucket_summary(bets_top)}
    for lo, hi in [(1.30, 1.80), (1.80, 2.20), (2.20, 2.60), (2.60, 3.20),
                   (3.20, 4.50), (4.50, 8.00)]:
        bucket = [b for b in bets_top if lo <= b["odds"] < hi]
        top_buckets[f"[{lo:.2f},{hi:.2f})"] = _bucket_summary(bucket)
        if bucket:
            print(fmt_bets(bucket, f"[{lo:.2f},{hi:.2f})"))

    print("\n=== Per-bet log (top-pick mode, CatBoost-only) ===")
    print("date        home                      vs away                    "
          "outcome  actual  odds  edge   profit")
    for b in bets_top:
        flag = "WIN " if b["won"] else "LOSS"
        print(
            f"{b['date']}  {b['home']:25s} vs {b['away']:25s}  {b['outcome']}  "
            f"  {b['actual']}    {b['odds']:5.2f}  {b['edge']:+.3f}  "
            f"{b['profit']:+6.2f}  {flag}"
        )

    # ─── Write a sweep report when a config is named ───
    if sweep is not None:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report = {
            "league": league,
            "config_name": sweep.name,
            "config_description": sweep.description,
            "feature_overrides": sweep.feature_overrides,
            "catboost_overrides": sweep.catboost_overrides,
            "calibrate": sweep.calibrate,
            "calibration_method": sweep.calibration_method,
            "cutoff": cutoff.isoformat(),
            "test_end": test_end.isoformat(),
            "train_info": train_info,
            "probabilistic_metrics": prob_metrics,
            "selection_any": {
                "buckets": any_buckets,
                "per_bet": bets_any,
            },
            "selection_top_pick": {
                "buckets": top_buckets,
                "per_bet": bets_top,
            },
        }
        out_path = REPORT_DIR / f"pl_sweep_{sweep.name}.json"
        out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\n{tag} Sweep report: {out_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--league",
        required=True,
        choices=LEAGUES_ALL,
        help="League key (PL/CH/BL/SA/LL).",
    )
    parser.add_argument(
        "--cutoff",
        default=DEFAULT_CUTOFF.isoformat(),
        help=f"Train cutoff (inclusive) — YYYY-MM-DD. Default: {DEFAULT_CUTOFF}.",
    )
    parser.add_argument(
        "--test-end",
        default=DEFAULT_TEST_END.isoformat(),
        help=f"Test window end (inclusive) — YYYY-MM-DD. Default: {DEFAULT_TEST_END}.",
    )
    parser.add_argument(
        "--config",
        default=None,
        choices=sorted(PL_SWEEP_CONFIGS.keys()),
        help="Optional sweep config name (see scripts/_pl_sweep_configs.py). "
             "Activates feature/catboost/calibration overrides AND writes a "
             "sweep JSON report. When set together with --save-as the prod "
             "model_profile is left untouched.",
    )
    parser.add_argument(
        "--save-as",
        default=None,
        help="Optional model save path (default: production "
             "models/catboost_{LEAGUE}.cbm). Use models/sweep/... during "
             "config sweeps so the production artefact stays put.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    sweep = get_config(args.config) if args.config else None
    save_as = Path(args.save_as) if args.save_as else None
    run(
        league=args.league,
        cutoff=datetime.strptime(args.cutoff, "%Y-%m-%d").date(),
        test_end=datetime.strptime(args.test_end, "%Y-%m-%d").date(),
        sweep=sweep,
        save_as=save_as,
    )
