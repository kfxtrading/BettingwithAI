"""Internal ad-hoc backtest: apply the current value-bet logic over the last
N days (default 5) and report ROI per league plus overall.

The script is deliberately *not* wired into the CLI — it's a one-shot tool
for answering the question "what would the value-bet ROI of the last 5
days have been?".

Methodology
-----------
For every league in ``LEAGUES`` we:

1. Load all available seasons via :func:`load_league`.
2. Identify the backtest window ``[T - N days, T]`` where ``T`` is the
   newest match date seen across all leagues (acts as "today" in the
   historical CSVs).
3. Replay every match **before** that window chronologically through a
   fresh :class:`FeatureBuilder` (value-purpose blocklist applied) and
   through the exact same trackers the models use.
4. For each match inside the window we
   - build the fixture feature vector,
   - predict with the league's *value* ensemble
     (``catboost_<LG>_value.cbm`` + Poisson + ``mlp_<LG>_value.pt``),
   - call :func:`find_value_bets` with a fixed bankroll of 1000 units,
   - settle each bet against the actual match result
     (``payoff = stake * (odds - 1)`` on win, ``-stake`` otherwise).
5. ROI = total P/L / total staked.

Run with ``python scripts/_backtest_value_5d.py [days]``.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

# ── sklearn cross-version shim ──────────────────────────────────────────────
# Models were saved by sklearn 1.8 but the local env is 1.7.2. The 1.7
# ``LogisticRegression.predict_proba`` reads ``self.multi_class``, which 1.8
# no longer sets. Inject a default so unpickled objects stay usable.
from sklearn.linear_model import LogisticRegression as _LR  # noqa: E402

_orig_setstate = _LR.__setstate__ if hasattr(_LR, "__setstate__") else None


def _patched_setstate(self, state):  # type: ignore[no-redef]
    if _orig_setstate is not None:
        _orig_setstate(self, state)
    else:
        self.__dict__.update(state)
    if not hasattr(self, "multi_class"):
        self.multi_class = "auto"
    if not hasattr(self, "n_iter_") and hasattr(self, "coef_"):
        import numpy as _np
        self.n_iter_ = _np.array([0])


_LR.__setstate__ = _patched_setstate  # type: ignore[assignment]

from rich.console import Console
from rich.table import Table

from football_betting.betting.value import find_value_bets
from football_betting.config import LEAGUES, MODELS_DIR, VALUE_MODEL_CFG
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.ensemble import EnsembleModel, ensemble_weights_path
from football_betting.predict.mlp_model import MLPPredictor
from football_betting.predict.poisson import PoissonModel
from football_betting.scraping.sofascore import SofascoreClient

console = Console(force_terminal=True, legacy_windows=False, no_color=False, safe_box=True)

BANKROLL = 1000.0


def _build_value_fb() -> FeatureBuilder:
    return FeatureBuilder(
        feature_blocklist_prefixes=VALUE_MODEL_CFG.feature_blocklist_prefixes,
        feature_blocklist_exact=VALUE_MODEL_CFG.feature_blocklist_exact,
    )


def _load_value_model(league_key: str, fb: FeatureBuilder) -> EnsembleModel | None:
    cb_path = MODELS_DIR / f"catboost_{league_key}_value.cbm"
    if not cb_path.exists():
        return None
    cb = CatBoostPredictor.for_league(league_key, fb, purpose="value")
    poisson = PoissonModel(pi_ratings=fb.pi_ratings)
    mlp_path = MODELS_DIR / f"mlp_{league_key}_value.pt"
    mlp = MLPPredictor.for_league(league_key, fb, purpose="value") if mlp_path.exists() else None
    ensemble = EnsembleModel(catboost=cb, poisson=poisson, mlp=mlp)
    weights_path = ensemble_weights_path(league_key, purpose="value")
    if weights_path.exists():
        try:
            ensemble.load_weights(weights_path)
        except Exception as exc:
            console.log(f"[yellow]Could not load {weights_path}: {exc}[/yellow]")
    return ensemble


def _settle_bet(outcome: str, actual: str, stake: float, odds: float) -> float:
    if stake <= 0:
        return 0.0
    return stake * (odds - 1.0) if outcome == actual else -stake


def backtest_league(league_key: str, days: int) -> dict:
    matches = load_league(league_key)
    if not matches:
        return {"league": league_key, "skipped": "no data"}

    # "Today" = newest date across this league's data
    today = max(m.date for m in matches)
    window_start = today - timedelta(days=days - 1)

    pre_window = [m for m in matches if m.date < window_start]
    in_window = [m for m in matches if window_start <= m.date <= today]
    if not in_window:
        return {"league": league_key, "skipped": "no matches in window"}

    fb = _build_value_fb()

    # Stage Sofascore per season so replay hydrates real-xG / squad trackers
    seasons = {m.season for m in matches}
    for season in seasons:
        sf = SofascoreClient.load_matches(league_key, season)
        if sf:
            fb.stage_sofascore_batch(sf)

    # Chronological replay of everything BEFORE the window
    fb.fit_on_history(sorted(pre_window, key=lambda m: m.date))

    model = _load_value_model(league_key, fb)
    if model is None:
        return {"league": league_key, "skipped": "no value model"}

    n_bets = 0
    total_stake = 0.0
    total_pnl = 0.0
    wins = 0

    # Walk chronologically through the window and update trackers after settle
    for m in sorted(in_window, key=lambda m: m.date):
        if m.odds is None:
            # Still update trackers and continue
            fb.update_with_match(m)
            continue

        fixture = Fixture(
            date=m.date,
            league=m.league,
            home_team=m.home_team,
            away_team=m.away_team,
            odds=m.odds,
            season=m.season,
            kickoff_datetime_utc=m.kickoff_datetime_utc,
        )
        try:
            pred = model.predict(fixture)
        except Exception as exc:
            console.log(f"[yellow]Predict failed {m.home_team} vs {m.away_team}: {exc}[/yellow]")
            fb.update_with_match(m)
            continue

        bets = find_value_bets(pred, BANKROLL)
        for b in bets:
            pnl = _settle_bet(b.outcome, m.result, b.kelly_stake, b.odds)
            total_stake += b.kelly_stake
            total_pnl += pnl
            if pnl > 0:
                wins += 1
            n_bets += 1

        # Feed result forward
        fb.update_with_match(m)

    roi = (total_pnl / total_stake) if total_stake > 0 else 0.0
    hit_rate = (wins / n_bets) if n_bets > 0 else 0.0

    return {
        "league": league_key,
        "window_start": window_start.isoformat(),
        "window_end": today.isoformat(),
        "n_matches_in_window": len(in_window),
        "n_bets": n_bets,
        "total_stake": total_stake,
        "total_pnl": total_pnl,
        "roi_pct": roi * 100.0,
        "hit_rate": hit_rate,
    }


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    console.rule(f"[bold cyan]Value-Bet Backtest — last {days} day(s)[/bold cyan]")

    rows: list[dict] = []
    for key in LEAGUES.keys():
        try:
            stats = backtest_league(key, days)
        except Exception as exc:
            console.log(f"[red]{key} failed: {exc}[/red]")
            continue
        rows.append(stats)

    # Totals
    totals = defaultdict(float)
    for r in rows:
        if r.get("skipped"):
            continue
        totals["n_bets"] += r["n_bets"]
        totals["total_stake"] += r["total_stake"]
        totals["total_pnl"] += r["total_pnl"]
        totals["n_matches"] += r["n_matches_in_window"]

    table = Table(title=f"Value-Bet ROI — last {days} days")
    table.add_column("League")
    table.add_column("Window")
    table.add_column("#Matches", justify="right")
    table.add_column("#Bets", justify="right")
    table.add_column("Stake", justify="right")
    table.add_column("P/L", justify="right")
    table.add_column("ROI %", justify="right")
    table.add_column("Hit %", justify="right")

    for r in rows:
        if r.get("skipped"):
            table.add_row(r["league"], "-", "-", "-", "-", "-", f"[yellow]{r['skipped']}[/yellow]", "-")
            continue
        table.add_row(
            r["league"],
            f"{r['window_start']} -> {r['window_end']}",
            str(r["n_matches_in_window"]),
            str(r["n_bets"]),
            f"{r['total_stake']:.2f}",
            f"{r['total_pnl']:+.2f}",
            f"{r['roi_pct']:+.2f}",
            f"{r['hit_rate']*100:.1f}",
        )

    overall_roi = (totals["total_pnl"] / totals["total_stake"] * 100) if totals["total_stake"] else 0.0
    table.add_row(
        "[bold]TOTAL[/bold]",
        "-",
        f"{int(totals['n_matches'])}",
        f"{int(totals['n_bets'])}",
        f"{totals['total_stake']:.2f}",
        f"{totals['total_pnl']:+.2f}",
        f"[bold]{overall_roi:+.2f}[/bold]",
        "-",
    )
    console.print(table)


if __name__ == "__main__":
    main()
