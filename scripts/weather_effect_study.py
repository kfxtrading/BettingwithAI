"""
Unsupervised weather-effect study (v0.4 Phase 1b).

Goal: decide **empirically** whether weather has any predictive signal
*beyond* the closing market line, before adding weather features to the
supervised pipeline.

Method
------
For every historical match with closing odds + kickoff timestamp:

    1. Fetch stadium weather around kickoff (WeatherTracker → Open-Meteo,
       cached locally at data/weather/cache.sqlite).
    2. Derive the market's margin-adjusted probability ``p_market`` for
       each outcome (H/D/A) from closing odds.
    3. Compute per-match targets:
         * ``surprise_loglik = -log(p_market[actual])``  (LL residual)
         * ``res_H / res_D / res_A = onehot(actual) - p_market``  (raw residuals)
    4. Per league, compute Spearman rank correlation between each
       weather feature and each residual target; assess significance via
       permutation test (n=1000) with Bonferroni correction across
       (features × targets).

Cross-league analysis
---------------------
For pairs of matches kicking off within ±20 min of each other (different
leagues): test whether the *difference* in weather between both venues
correlates with the *difference* in market surprise. Exhaustive for all
same-kickoff pairs across all 5 leagues.

Output
------
Compact Markdown table to stdout (and optional --save-csv). Only features
whose Bonferroni-adjusted p < 0.05 are flagged GREEN — they alone are
candidates for the supervised feature set.
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np

from football_betting.data.loader import load_league
from football_betting.features.weather import WeatherTracker

LEAGUE_KEYS: tuple[str, ...] = ("BL", "CH", "LL", "PL", "SA")


# ────────────────────────────────── Core ──────────────────────────────────


@dataclass(slots=True)
class Row:
    league: str
    match_date: date
    kickoff_utc: datetime
    home: str
    away: str
    result: str  # H/D/A
    p_home: float
    p_draw: float
    p_away: float
    weather: dict[str, float]

    @property
    def surprise(self) -> float:
        p = {"H": self.p_home, "D": self.p_draw, "A": self.p_away}[self.result]
        return -math.log(max(p, 1e-12))

    @property
    def res_h(self) -> float:
        return (1.0 if self.result == "H" else 0.0) - self.p_home

    @property
    def res_d(self) -> float:
        return (1.0 if self.result == "D" else 0.0) - self.p_draw

    @property
    def res_a(self) -> float:
        return (1.0 if self.result == "A" else 0.0) - self.p_away


def _collect_league(league_key: str, tracker: WeatherTracker) -> list[Row]:
    rows: list[Row] = []
    matches = load_league(league_key)
    skipped_no_odds = skipped_no_kickoff = skipped_no_weather = 0
    for m in matches:
        if m.odds is None:
            skipped_no_odds += 1
            continue
        ko = m.kickoff_datetime_utc
        if ko is None:
            skipped_no_kickoff += 1
            continue
        if ko.tzinfo is None:
            ko = ko.replace(tzinfo=UTC)
        wx = tracker.features_for_match(m.home_team, m.away_team, m.date, ko)
        if not wx or not any(not math.isnan(v) for v in wx.values()):
            skipped_no_weather += 1
            continue
        pH, pD, pA = m.odds.fair_probs()
        rows.append(
            Row(
                league=league_key,
                match_date=m.date,
                kickoff_utc=ko,
                home=m.home_team,
                away=m.away_team,
                result=m.result,
                p_home=pH,
                p_draw=pD,
                p_away=pA,
                weather=wx,
            )
        )
    print(
        f"  {league_key}: {len(rows)} usable  "
        f"(skipped: no_odds={skipped_no_odds}, no_kickoff={skipped_no_kickoff}, "
        f"no_weather={skipped_no_weather})"
    )
    return rows


# ──────────────────────────── Stats helpers ────────────────────────────


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation, NaN-safe."""
    mask = ~(np.isnan(x) | np.isnan(y))
    if mask.sum() < 10:
        return float("nan")
    rx = np.argsort(np.argsort(x[mask])).astype(float)
    ry = np.argsort(np.argsort(y[mask])).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = math.sqrt((rx @ rx) * (ry @ ry))
    if denom == 0.0:
        return float("nan")
    return float((rx @ ry) / denom)


def _perm_pvalue(
    x: np.ndarray,
    y: np.ndarray,
    rho_obs: float,
    n_perm: int = 1000,
    rng: np.random.Generator | None = None,
) -> float:
    """Two-sided permutation p-value for Spearman ρ."""
    if math.isnan(rho_obs):
        return float("nan")
    rng = rng or np.random.default_rng(42)
    mask = ~(np.isnan(x) | np.isnan(y))
    if mask.sum() < 10:
        return float("nan")
    xm, ym = x[mask], y[mask]
    abs_obs = abs(rho_obs)
    ge = 0
    for _ in range(n_perm):
        perm = rng.permutation(ym)
        rho = _spearman(xm, perm)
        if not math.isnan(rho) and abs(rho) >= abs_obs:
            ge += 1
    return (ge + 1) / (n_perm + 1)


# ───────────────────────────── Per-league ─────────────────────────────


def _per_league_report(rows: list[Row], n_perm: int) -> list[dict]:
    if not rows:
        return []
    feat_names = sorted({k for r in rows for k in r.weather})
    targets = {
        "surprise": np.array([r.surprise for r in rows]),
        "res_H": np.array([r.res_h for r in rows]),
        "res_D": np.array([r.res_d for r in rows]),
        "res_A": np.array([r.res_a for r in rows]),
    }
    report: list[dict] = []
    m_tests = len(feat_names) * len(targets)
    for feat in feat_names:
        x = np.array([r.weather.get(feat, math.nan) for r in rows])
        for tname, y in targets.items():
            rho = _spearman(x, y)
            p = _perm_pvalue(x, y, rho, n_perm=n_perm)
            p_bonf = min(1.0, p * m_tests) if not math.isnan(p) else float("nan")
            report.append(
                {
                    "feature": feat,
                    "target": tname,
                    "rho": rho,
                    "p": p,
                    "p_bonf": p_bonf,
                    "n": int(np.sum(~np.isnan(x))),
                }
            )
    return report


def _print_top(league: str, report: list[dict], top_n: int = 10) -> None:
    if not report:
        print(f"## {league}: no data\n")
        return
    print(f"\n## {league} — top-{top_n} by |ρ| (Bonferroni-adj.)")
    print("| feature | target | ρ | p_raw | p_bonf | n | flag |")
    print("|---|---|---:|---:|---:|---:|:---:|")
    valid = [r for r in report if not math.isnan(r["rho"])]
    valid.sort(key=lambda r: abs(r["rho"]), reverse=True)
    for r in valid[:top_n]:
        flag = "🟢" if (not math.isnan(r["p_bonf"]) and r["p_bonf"] < 0.05) else "—"
        print(
            f"| `{r['feature']}` | {r['target']} | "
            f"{r['rho']:+.3f} | {r['p']:.3f} | {r['p_bonf']:.3f} | "
            f"{r['n']} | {flag} |"
        )


# ────────────────────────── Cross-league pairs ──────────────────────────


def _find_simultaneous_pairs(
    all_rows: list[Row], window_minutes: int = 20
) -> list[tuple[Row, Row]]:
    """Return pairs of matches (different leagues) kicking off within ±window."""
    # Bucket by UTC kickoff rounded to nearest minute
    by_bucket: dict[int, list[Row]] = defaultdict(list)
    for r in all_rows:
        bucket = int(r.kickoff_utc.timestamp() // 60)  # minute bucket
        by_bucket[bucket].append(r)

    delta = window_minutes
    keys = sorted(by_bucket.keys())
    pairs: list[tuple[Row, Row]] = []
    for i, k in enumerate(keys):
        # only look forward within window
        for k2 in keys[i:]:
            if k2 - k > delta:
                break
            for a in by_bucket[k]:
                for b in by_bucket[k2]:
                    if a is b:
                        continue
                    if a.league == b.league:
                        continue
                    # Canonical order to avoid dupes
                    if (a.league, a.home, a.match_date) < (b.league, b.home, b.match_date):
                        pairs.append((a, b))
                    else:
                        pairs.append((b, a))
    # Deduplicate (same pair might appear from both buckets)
    seen: set[tuple] = set()
    unique: list[tuple[Row, Row]] = []
    for a, b in pairs:
        key = (a.league, a.match_date, a.home, b.league, b.match_date, b.home)
        if key in seen:
            continue
        seen.add(key)
        unique.append((a, b))
    return unique


def _cross_league_report(pairs: list[tuple[Row, Row]], n_perm: int) -> None:
    if not pairs:
        print("\n## Cross-league (same-kickoff): 0 pairs found.")
        return
    print(f"\n## Cross-league: {len(pairs)} simultaneous-kickoff pairs")
    # Per pair: weather-diff vector (feat: a.wx - b.wx), surprise-diff
    feat_names = sorted({k for a, b in pairs for k in set(a.weather) & set(b.weather)})
    d_surprise = np.array([a.surprise - b.surprise for a, b in pairs])
    d_resH = np.array([a.res_h - b.res_h for a, b in pairs])
    d_resA = np.array([a.res_a - b.res_a for a, b in pairs])
    targets = {"Δ_surprise": d_surprise, "Δ_res_H": d_resH, "Δ_res_A": d_resA}
    m_tests = len(feat_names) * len(targets)
    results: list[dict] = []
    for feat in feat_names:
        diffs = np.array(
            [a.weather.get(feat, math.nan) - b.weather.get(feat, math.nan) for a, b in pairs]
        )
        for tname, y in targets.items():
            rho = _spearman(diffs, y)
            p = _perm_pvalue(diffs, y, rho, n_perm=n_perm)
            p_bonf = min(1.0, p * m_tests) if not math.isnan(p) else float("nan")
            results.append(
                {
                    "feature": feat,
                    "target": tname,
                    "rho": rho,
                    "p": p,
                    "p_bonf": p_bonf,
                    "n": int(np.sum(~np.isnan(diffs))),
                }
            )
    print("| weather-diff | target | ρ | p_raw | p_bonf | n | flag |")
    print("|---|---|---:|---:|---:|---:|:---:|")
    results.sort(key=lambda r: abs(r["rho"]) if not math.isnan(r["rho"]) else -1, reverse=True)
    for r in results[:15]:
        flag = "🟢" if (not math.isnan(r["p_bonf"]) and r["p_bonf"] < 0.05) else "—"
        rho = r["rho"]
        p = r["p"]
        pb = r["p_bonf"]
        rho_s = f"{rho:+.3f}" if not math.isnan(rho) else "nan"
        p_s = f"{p:.3f}" if not math.isnan(p) else "nan"
        pb_s = f"{pb:.3f}" if not math.isnan(pb) else "nan"
        print(
            f"| `{r['feature']}` | {r['target']} | {rho_s} | {p_s} | {pb_s} | {r['n']} | {flag} |"
        )


# ──────────────────────────────── Main ────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Unsupervised weather-effect study.")
    parser.add_argument("--leagues", nargs="+", default=list(LEAGUE_KEYS))
    parser.add_argument("--n-perm", type=int, default=1000)
    parser.add_argument(
        "--window-min",
        type=int,
        default=20,
        help="Cross-league kickoff-match tolerance in minutes.",
    )
    parser.add_argument("--save-csv", type=Path, default=None)
    args = parser.parse_args()

    # Force weather tracker ON regardless of config (audit-mode)
    from football_betting.config import WeatherConfig

    tracker = WeatherTracker(
        cfg=WeatherConfig(
            enabled=True,
            use_match_day_weather=True,
            use_weather_shock=True,
            use_simons_signal=True,
        )
    )

    print(f"# Weather-Effect Study — {datetime.now(UTC).strftime('%Y-%m-%d %H:%MZ')}")
    print(
        f"\nLeagues: {', '.join(args.leagues)} · n_perm={args.n_perm} · "
        f"cross-league window=±{args.window_min}min\n"
    )

    all_rows: list[Row] = []
    all_reports: dict[str, list[dict]] = {}
    print("## Data collection")
    for lg in args.leagues:
        rows = _collect_league(lg, tracker)
        all_rows.extend(rows)
        all_reports[lg] = _per_league_report(rows, n_perm=args.n_perm)

    for lg in args.leagues:
        _print_top(lg, all_reports[lg], top_n=10)

    pairs = _find_simultaneous_pairs(all_rows, window_minutes=args.window_min)
    _cross_league_report(pairs, n_perm=args.n_perm)

    # ───── Overall summary ─────
    all_flat = [(lg, r) for lg, rep in all_reports.items() for r in rep]
    green = [(lg, r) for lg, r in all_flat if not math.isnan(r["p_bonf"]) and r["p_bonf"] < 0.05]
    print("\n## Summary")
    print(f"* Total (league, feature, target) tests: {len(all_flat)}")
    print(f"* Tests surviving Bonferroni α=0.05: **{len(green)}**")
    if green:
        print("\n🟢 Features with significant signal:")
        for lg, r in green:
            print(
                f"  * {lg} → `{r['feature']}` vs {r['target']}: "
                f"ρ={r['rho']:+.3f}, p_bonf={r['p_bonf']:.3f}, n={r['n']}"
            )
    else:
        print(
            "\n⚠️  **No weather feature survives Bonferroni correction** — "
            "current evidence does **not** support adding weather to the "
            "supervised feature set. Recommendation: keep `use_weather=False`."
        )

    if args.save_csv:
        import csv

        args.save_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.save_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["league", "feature", "target", "rho", "p", "p_bonf", "n"])
            for lg, rep in all_reports.items():
                for r in rep:
                    w.writerow(
                        [
                            lg,
                            r["feature"],
                            r["target"],
                            f"{r['rho']:.6f}",
                            f"{r['p']:.6f}",
                            f"{r['p_bonf']:.6f}",
                            r["n"],
                        ]
                    )
        print(f"\nSaved raw results → {args.save_csv}")


if __name__ == "__main__":
    main()
