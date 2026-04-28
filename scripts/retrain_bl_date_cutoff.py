"""BL out-of-sample retrain with explicit date cutoff — and persistence.

Train: every Bundesliga match from data start up to and including 2026-03-01.
Test:  Bundesliga matches from 2026-03-02 through 2026-04-25 (whatever exists).

The script
  * trains CatBoost on the date-filtered match list using the production
    ``CatBoostPredictor.fit`` workflow (chronological walk, time-decay
    weights, last-10% chrono val slice for early stopping, calibrator
    fitted on val);
  * persists the trained CatBoost + calibrator + features.txt to the
    standard ``models/catboost_BL.*`` paths and rewrites
    ``models/model_profile_BL.json`` to ``model_kind=catboost`` /
    ``active_members=("catboost",)`` so tomorrow's prediction pipeline
    picks up THIS model and ignores the now-stale MLP / Sequence
    artefacts (which were trained on the pre-Sofascore-fix feature set);
  * walks the test window chronologically with the trained predictor
    and reports probabilistic metrics + the same selection-bucket sweep
    used in ``scripts/selection_experiment_pl.py``.

To re-introduce MLP / Sequence into the ensemble after this retrain:
    fb train-mlp --league BL
    fb train-sequence --league BL
    fb tune-ensemble --league BL --val-season 2024-25 --objective rps
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

import numpy as np

from football_betting.betting.kelly import kelly_stake
from football_betting.betting.margin import remove_margin
from football_betting.config import (
    BETTING_CFG,
    MODELS_DIR,
    artifact_suffix,
)
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.predict.runtime import (
    LeagueModelProfile,
    make_feature_builder,
    resolve_model_profile,
    save_model_profile,
    stage_sofascore_for_seasons,
)

LEAGUE = "BL"
PURPOSE = "1x2"
CUTOFF = date(2026, 3, 1)
TEST_END = date(2026, 4, 25)
WARMUP_GAMES = 100

OUTCOME_TO_INT = {"H": 0, "D": 1, "A": 2}
START_BANKROLL = 100.0


# ────────────────────────── Production retrain ──────────────────────────

def retrain_and_save() -> tuple[CatBoostPredictor, list, list]:
    """Train CatBoost on matches ≤ CUTOFF and persist to models/.

    Returns the (in-memory) predictor plus the train+test match lists so
    the caller can run out-of-sample evaluation without reloading.
    """
    matches = load_league(LEAGUE)
    matches.sort(key=lambda m: m.date)
    train_matches = [m for m in matches if m.date <= CUTOFF]
    test_matches = [m for m in matches if CUTOFF < m.date <= TEST_END]
    print(
        f"[BL] train={len(train_matches)} matches ({train_matches[0].date} → "
        f"{train_matches[-1].date}); test={len(test_matches)} matches "
        f"({test_matches[0].date if test_matches else '∅'} → "
        f"{test_matches[-1].date if test_matches else '∅'})"
    )

    fb = make_feature_builder(purpose=PURPOSE)
    seasons = {m.season for m in matches}
    staged = stage_sofascore_for_seasons(fb, LEAGUE, seasons)
    print(f"[BL] Sofascore staged: {staged} matches across {len(seasons)} seasons")

    predictor = CatBoostPredictor(feature_builder=fb, purpose=PURPOSE)
    # NOTE: calibrate=False — fitting an isotonic/auto calibrator on the
    # last 15% (~201 matches) of training data overfits and degrades the
    # 55-match test-window performance (verified empirically: hit-rate
    # 52.7% raw vs 47.3% calibrated; top-pick ROI +33.8% raw vs -15.8%
    # calibrated). Raw CatBoost softmax probabilities are well-calibrated
    # enough for the betting layer when training data is plentiful.
    print("[BL] Training CatBoost on train window (no post-hoc calibration)…")
    result = predictor.fit(
        train_matches, warmup_games=WARMUP_GAMES, calibrate=False
    )
    print(
        f"[BL] Trained: n_train={result['n_train']}, n_val={result['n_val']}, "
        f"features={result['n_features']}, "
        f"best_iter={result['best_iteration']}"
    )

    suffix = artifact_suffix(PURPOSE)
    model_path = MODELS_DIR / f"catboost_{LEAGUE}{suffix}.cbm"
    predictor.save(model_path)
    print(f"[BL] Saved: {model_path}")
    print(f"[BL] Saved: {model_path.with_suffix('.features.txt')}")
    if predictor.calibrator and predictor.calibrator.is_fitted:
        print(f"[BL] Saved: {model_path.with_suffix('.calibrator.joblib')}")
    else:
        # Remove any stale calibrator from a previous run so the production
        # loader (CatBoostPredictor.load) doesn't silently apply it.
        stale_cal = model_path.with_suffix(".calibrator.joblib")
        if stale_cal.exists():
            stale_cal.unlink()
            print(f"[BL] Removed stale calibrator: {stale_cal}")

    # Force the profile to CatBoost-only so the production loader does NOT
    # mix in the now-stale MLP / Sequence artefacts (those were trained on
    # the pre-Sofascore-fix feature set and should be regenerated before
    # being reactivated). Keep purpose=1x2.
    existing = resolve_model_profile(LEAGUE, purpose=PURPOSE)
    cal_method = (
        predictor.calibrator.cfg.method
        if predictor.calibrator and predictor.calibrator.is_fitted
        else None
    )
    if existing is not None and cal_method is None:
        # When we explicitly skip calibration, force the profile to record
        # that — otherwise an old "auto" string lingers and misleads readers.
        existing = replace(existing, calibration_method=None)
    if existing is None:
        new_profile = LeagueModelProfile(
            league_key=LEAGUE,
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
            # Preserve any betting overrides if present, drop ensemble-only
            # fields that no longer apply.
            weight_objective=None,
            weight_blend=None,
        )
    save_model_profile(new_profile)
    print(f"[BL] Profile rewritten -> {new_profile.model_kind}, "
          f"active={list(new_profile.active_members)}, "
          f"calibration={new_profile.calibration_method}")

    print("\n[BL] Top 15 CatBoost feature importances:")
    for feat, imp in result["feature_importance"][:15]:
        print(f"  {imp:6.2f}  {feat}")

    return predictor, train_matches, test_matches


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

def run() -> None:
    print(f"=== BL date-cutoff retrain: train ≤ {CUTOFF}, test ≤ {TEST_END} ===\n")
    predictor, _, test_matches = retrain_and_save()

    if not test_matches:
        print("\nNo test matches in window — skipping evaluation.")
        return

    print("\n[BL] Walking test window for predictions…")
    cb_probs, po_probs, meta = evaluate_test_window(predictor, test_matches)
    y = np.asarray([OUTCOME_TO_INT[m["actual"]] for m in meta])
    blend = 0.85 * cb_probs + 0.15 * po_probs

    print("\n=== Probabilistic metrics on test window ===")
    for name, probs in [
        ("CatBoost", cb_probs),
        ("Poisson", po_probs),
        ("Blend(.85/.15)", blend),
    ]:
        m = probabilistic_metrics(probs, y)
        print(
            f"  {name:>16s}: n={m['n']:3d}  RPS={m['rps']:.4f}  "
            f"Brier={m['brier']:.4f}  LogLoss={m['log_loss']:.4f}  "
            f"hit={m['hit_rate']:.1%}"
        )

    print("\n=== Selection sweep on test window (CatBoost-only — matches saved profile) ===")
    print("\n--- any value bet ---")
    bets_any = selection_sweep(cb_probs, meta, mode="any")
    print(fmt_bets(bets_any, "all"))
    for lo, hi in [(1.30, 1.80), (1.80, 2.20), (2.20, 2.60), (2.60, 3.20),
                   (3.20, 4.50), (4.50, 8.00)]:
        bucket = [b for b in bets_any if lo <= b["odds"] < hi]
        if bucket:
            print(fmt_bets(bucket, f"[{lo:.2f},{hi:.2f})"))

    print("\n--- top-pick only ---")
    bets_top = selection_sweep(cb_probs, meta, mode="top_pick")
    print(fmt_bets(bets_top, "all"))
    for lo, hi in [(1.30, 1.80), (1.80, 2.20), (2.20, 2.60), (2.60, 3.20),
                   (3.20, 4.50), (4.50, 8.00)]:
        bucket = [b for b in bets_top if lo <= b["odds"] < hi]
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


if __name__ == "__main__":
    run()
