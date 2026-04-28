"""Phase 0 of the 1x2 training plan: feature-impact analysis per league.

Builds a chronological, no-leakage (X, y) matrix per league using the existing
``FeatureBuilder``, then runs three supervised importance estimators and a set
of unsupervised diagnostics. Outputs are written to:

    data/feature_matrices/{LG}_1x2.parquet
    data/feature_matrices/{LG}_1x2_meta.json
    reports/feature_impact_{LG}.json
    reports/feature_impact_summary.md  (only when --league=all)

Usage::

    python scripts/feature_impact_report.py --league PL
    python scripts/feature_impact_report.py --league all

The script does not modify any model artefacts or configs. It is informational
input for the Phase 0 sign-off described in the plan.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.decomposition import PCA
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import StandardScaler

from football_betting.config import DATA_DIR
from football_betting.data.loader import load_league
from football_betting.predict.runtime import (
    make_feature_builder,
    stage_sofascore_for_seasons,
)

OUTCOME_TO_INT = {"H": 0, "D": 1, "A": 2}
LEAGUES_ALL = ("PL", "CH", "BL", "SA", "LL")
DEFAULT_TRAIN_SEASONS = ("2021-22", "2022-23")
DEFAULT_VAL_SEASON = "2023-24"
WARMUP_GAMES = 100

REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_DIR = REPO_ROOT / "data" / "feature_matrices"
REPORT_DIR = REPO_ROOT / "reports"

# Order matters — first matching prefix wins. "" is the catch-all and must
# stay last.
FAMILY_RULES: tuple[tuple[str, str], ...] = (
    ("has_real_xg", "real_xg"),
    ("real_xg_", "real_xg"),
    ("xg_", "xg_proxy"),
    ("pi_", "pi_ratings"),
    ("form_", "form"),
    ("squad_", "squad_quality"),
    ("mm_", "market_microstructure"),
    ("market_", "market_odds"),
    ("h2h_", "h2h"),
    ("rest_", "rest_days"),
    ("home_team_ha", "home_advantage"),
    ("league_home_adv", "home_advantage"),
    ("league_avg_goals", "league_meta"),
    ("league_", "league_meta"),
    ("weather_", "weather"),
    ("standings_", "standings"),
    ("home_point_ded", "point_deductions"),
    ("away_point_ded", "point_deductions"),
    ("", "other"),
)


def family_for(name: str) -> str:
    for prefix, family in FAMILY_RULES:
        if prefix == "" or name.startswith(prefix):
            return family
    return "other"


@dataclass(slots=True)
class LeagueMatrix:
    league: str
    feature_names: list[str]
    X_train: pd.DataFrame
    y_train: np.ndarray
    X_val: pd.DataFrame
    y_val: np.ndarray
    seasons_train: list[str]
    seasons_val: list[str]


def build_matrix(
    league: str,
    train_seasons: tuple[str, ...] | None = None,
    val_season: str | None = None,
    *,
    cutoff: date | None = None,
    test_end: date | None = None,
) -> LeagueMatrix:
    """Build a chronological no-leakage (X, y) matrix for one league.

    Two modes — provide exactly one:
      * Season-based (legacy default): train_seasons + val_season filter
        rows by ``match.season``.
      * Date-cutoff (Phase A of the PL addendum): train rows = matches
        with date ≤ ``cutoff``; val rows = ``cutoff`` < date ≤ ``test_end``.
    """
    season_mode = train_seasons is not None and val_season is not None
    cutoff_mode = cutoff is not None and test_end is not None
    if season_mode == cutoff_mode:
        raise ValueError(
            "build_matrix: pass exactly one of (train_seasons, val_season) "
            "or (cutoff, test_end) — got both or neither."
        )

    matches = load_league(league)
    fb = make_feature_builder(purpose="1x2")
    seasons_set = {m.season for m in matches}
    stage_sofascore_for_seasons(fb, league, seasons_set)
    fb.reset(keep_staged_sofascore=True)

    rows: list[dict[str, float]] = []
    labels: list[int] = []
    seasons: list[str] = []
    dates: list[date] = []

    if season_mode:
        train_seasons_set = set(train_seasons)
        used_seasons = train_seasons_set | {val_season}

    for idx, match in enumerate(sorted(matches, key=lambda m: m.date)):
        if idx < WARMUP_GAMES:
            fb.update_with_match(match)
            continue

        if season_mode:
            keep = match.season in used_seasons
        else:
            keep = match.date <= test_end

        if keep:
            feats = fb.build_features(
                home_team=match.home_team,
                away_team=match.away_team,
                league_key=match.league,
                match_date=match.date,
                odds_home=match.odds.home if match.odds else None,
                odds_draw=match.odds.draw if match.odds else None,
                odds_away=match.odds.away if match.odds else None,
                season=match.season,
                kickoff_datetime_utc=match.kickoff_datetime_utc,
            )
            rows.append(feats)
            labels.append(OUTCOME_TO_INT[match.result])
            seasons.append(match.season)
            dates.append(match.date)
        fb.update_with_match(match)

    if not rows:
        raise RuntimeError(f"No rows generated for {league} (after warmup + filter)")

    df = pd.DataFrame(rows).fillna(0.0)
    feature_names = list(df.columns)
    y = np.asarray(labels, dtype=np.int64)
    seasons_arr = np.asarray(seasons)
    dates_arr = np.asarray(dates)

    if season_mode:
        train_mask = np.isin(seasons_arr, list(train_seasons_set))
        val_mask = seasons_arr == val_season
    else:
        train_mask = dates_arr <= cutoff
        val_mask = dates_arr > cutoff

    return LeagueMatrix(
        league=league,
        feature_names=feature_names,
        X_train=df.iloc[train_mask].reset_index(drop=True),
        y_train=y[train_mask],
        X_val=df.iloc[val_mask].reset_index(drop=True),
        y_val=y[val_mask],
        seasons_train=seasons_arr[train_mask].tolist(),
        seasons_val=seasons_arr[val_mask].tolist(),
    )


def persist_matrix(matrix: LeagueMatrix, *, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = []
    for split, X, y, seasons in (
        ("train", matrix.X_train, matrix.y_train, matrix.seasons_train),
        ("val", matrix.X_val, matrix.y_val, matrix.seasons_val),
    ):
        part = X.copy()
        part["_y"] = y
        part["_season"] = seasons
        part["_split"] = split
        parts.append(part)
    full = pd.concat(parts, ignore_index=True)
    parquet_path = out_dir / f"{matrix.league}_1x2.parquet"
    full.to_parquet(parquet_path, index=False)

    meta = {
        "league": matrix.league,
        "n_train": int(len(matrix.X_train)),
        "n_val": int(len(matrix.X_val)),
        "n_features": len(matrix.feature_names),
        "feature_names": matrix.feature_names,
        "feature_family": {name: family_for(name) for name in matrix.feature_names},
    }
    (out_dir / f"{matrix.league}_1x2_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return parquet_path


def fit_quick_catboost(matrix: LeagueMatrix) -> tuple[CatBoostClassifier, Pool]:
    train_pool = Pool(
        matrix.X_train,
        matrix.y_train,
        feature_names=matrix.feature_names,
    )
    val_pool = Pool(
        matrix.X_val,
        matrix.y_val,
        feature_names=matrix.feature_names,
    )
    model = CatBoostClassifier(
        iterations=500,
        learning_rate=0.05,
        depth=6,
        loss_function="MultiClass",
        eval_metric="MultiClass",
        early_stopping_rounds=50,
        random_seed=42,
        verbose=False,
        classes_count=3,
    )
    model.fit(train_pool, eval_set=val_pool)
    return model, val_pool


def importance_catboost_default(
    model: CatBoostClassifier, feature_names: list[str]
) -> list[dict[str, Any]]:
    raw = model.get_feature_importance()
    pairs = sorted(
        zip(feature_names, raw, strict=True), key=lambda kv: kv[1], reverse=True
    )
    return [{"feature": name, "score": float(score)} for name, score in pairs]


def importance_catboost_loss(
    model: CatBoostClassifier, val_pool: Pool, feature_names: list[str]
) -> list[dict[str, Any]]:
    raw = model.get_feature_importance(type="LossFunctionChange", data=val_pool)
    pairs = sorted(
        zip(feature_names, raw, strict=True), key=lambda kv: kv[1], reverse=True
    )
    return [{"feature": name, "score": float(score)} for name, score in pairs]


def importance_permutation(
    model: CatBoostClassifier, matrix: LeagueMatrix
) -> list[dict[str, Any]]:
    result = permutation_importance(
        model,
        matrix.X_val,
        matrix.y_val,
        n_repeats=10,
        scoring="neg_log_loss",
        random_state=42,
        n_jobs=1,
    )
    pairs = sorted(
        zip(matrix.feature_names, result.importances_mean, result.importances_std, strict=True),
        key=lambda t: t[1],
        reverse=True,
    )
    return [
        {"feature": name, "mean": float(mean), "std": float(std)}
        for name, mean, std in pairs
    ]


def collate_high_impact(
    cb_default: list[dict[str, Any]],
    cb_loss: list[dict[str, Any]],
    perm: list[dict[str, Any]],
    *,
    top_k: int = 15,
) -> list[dict[str, Any]]:
    top_default = {row["feature"] for row in cb_default[:top_k]}
    top_loss = {row["feature"] for row in cb_loss[:top_k]}
    top_perm = {row["feature"] for row in perm[:top_k]}
    counts: dict[str, int] = {}
    for s in (top_default, top_loss, top_perm):
        for name in s:
            counts[name] = counts.get(name, 0) + 1
    qualified = sorted(
        ((name, n) for name, n in counts.items() if n >= 2),
        key=lambda kv: (-kv[1], kv[0]),
    )
    return [
        {"feature": name, "method_count": n, "family": family_for(name)}
        for name, n in qualified
    ]


def variance_audit(matrix: LeagueMatrix) -> list[dict[str, Any]]:
    flagged = []
    full = pd.concat([matrix.X_train, matrix.X_val], ignore_index=True)
    ranges = (full.max() - full.min()).abs()
    stds = full.std(ddof=0)
    for name in matrix.feature_names:
        if stds[name] < 1e-4 or ranges[name] < 1e-4:
            flagged.append(
                {
                    "feature": name,
                    "std": float(stds[name]),
                    "range": float(ranges[name]),
                    "family": family_for(name),
                }
            )
    return flagged


def correlation_pairs(matrix: LeagueMatrix, *, threshold: float = 0.9) -> list[dict[str, Any]]:
    full = pd.concat([matrix.X_train, matrix.X_val], ignore_index=True)
    nonconst = [c for c in matrix.feature_names if full[c].std(ddof=0) > 1e-6]
    if len(nonconst) < 2:
        return []
    corr = full[nonconst].corr().abs()
    pairs = []
    cols = corr.columns.tolist()
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = float(corr.at[a, b])
            if r >= threshold:
                pairs.append(
                    {
                        "a": a,
                        "b": b,
                        "abs_r": r,
                        "family_a": family_for(a),
                        "family_b": family_for(b),
                    }
                )
    pairs.sort(key=lambda p: p["abs_r"], reverse=True)
    return pairs


def pca_summary(matrix: LeagueMatrix) -> dict[str, float]:
    full = pd.concat([matrix.X_train, matrix.X_val], ignore_index=True)
    nonconst = [c for c in matrix.feature_names if full[c].std(ddof=0) > 1e-6]
    if not nonconst:
        return {}
    scaled = StandardScaler().fit_transform(full[nonconst].to_numpy())
    n_components = min(20, scaled.shape[0], scaled.shape[1])
    if n_components == 0:
        return {}
    pca = PCA(n_components=n_components)
    pca.fit(scaled)
    cum = np.cumsum(pca.explained_variance_ratio_)
    out: dict[str, float] = {"total_columns": float(len(nonconst))}
    for k in (5, 10, 20):
        if k <= n_components:
            out[f"cumvar_{k}"] = float(cum[k - 1])
    return out


def missingness_audit(matrix: LeagueMatrix) -> list[dict[str, Any]]:
    out = []
    full = pd.concat(
        [
            matrix.X_train.assign(_split="train", _season=matrix.seasons_train),
            matrix.X_val.assign(_split="val", _season=matrix.seasons_val),
        ],
        ignore_index=True,
    )
    n_total = len(full)
    for name in matrix.feature_names:
        col = full[name]
        zero_frac_total = float((col == 0).sum() / n_total) if n_total else 0.0
        per_season: dict[str, float] = {}
        for season, group in full.groupby("_season"):
            n = len(group)
            if n:
                per_season[str(season)] = float((group[name] == 0).sum() / n)
        out.append(
            {
                "feature": name,
                "family": family_for(name),
                "zero_fraction_total": zero_frac_total,
                "zero_fraction_by_season": per_season,
            }
        )
    out.sort(key=lambda row: row["zero_fraction_total"], reverse=True)
    return out


def family_aggregate(
    high_impact: list[dict[str, Any]], feature_names: list[str]
) -> dict[str, dict[str, int]]:
    family_total: dict[str, int] = {}
    for name in feature_names:
        fam = family_for(name)
        family_total[fam] = family_total.get(fam, 0) + 1
    family_high: dict[str, int] = {}
    for row in high_impact:
        fam = row["family"]
        family_high[fam] = family_high.get(fam, 0) + 1
    return {
        fam: {
            "n_total": family_total[fam],
            "n_high_impact": family_high.get(fam, 0),
        }
        for fam in sorted(family_total)
    }


def run_league(
    league: str,
    train_seasons: tuple[str, ...] | None = None,
    val_season: str | None = None,
    *,
    cutoff: date | None = None,
    test_end: date | None = None,
    min_val_rows: int = 50,
) -> dict[str, Any]:
    print(f"\n=== {league} ===", flush=True)
    matrix = build_matrix(
        league,
        train_seasons=train_seasons,
        val_season=val_season,
        cutoff=cutoff,
        test_end=test_end,
    )
    print(
        f"  matrix: train={len(matrix.X_train)}, val={len(matrix.X_val)}, "
        f"features={len(matrix.feature_names)}",
        flush=True,
    )
    if len(matrix.X_train) < 200 or len(matrix.X_val) < min_val_rows:
        raise RuntimeError(
            f"{league}: insufficient rows (train={len(matrix.X_train)}, val={len(matrix.X_val)})"
        )

    parquet_path = persist_matrix(matrix, out_dir=MATRIX_DIR)
    print(f"  matrix written: {parquet_path}", flush=True)

    print("  training quick CatBoost (500 iters)…", flush=True)
    model, val_pool = fit_quick_catboost(matrix)

    print("  computing importance: catboost_default", flush=True)
    cb_default = importance_catboost_default(model, matrix.feature_names)
    print("  computing importance: catboost_loss", flush=True)
    cb_loss = importance_catboost_loss(model, val_pool, matrix.feature_names)
    print("  computing importance: permutation (sklearn, 10 repeats)", flush=True)
    perm = importance_permutation(model, matrix)

    print("  unsupervised diagnostics: variance / corr / pca / missingness", flush=True)
    high_impact = collate_high_impact(cb_default, cb_loss, perm)
    variance = variance_audit(matrix)
    corr = correlation_pairs(matrix, threshold=0.9)
    pca = pca_summary(matrix)
    miss = missingness_audit(matrix)
    families = family_aggregate(high_impact, matrix.feature_names)

    report: dict[str, Any] = {
        "league": league,
        "mode": "cutoff" if cutoff is not None else "season",
        "train_seasons": list(train_seasons) if train_seasons else None,
        "val_season": val_season,
        "cutoff": cutoff.isoformat() if cutoff else None,
        "test_end": test_end.isoformat() if test_end else None,
        "n_train": int(len(matrix.X_train)),
        "n_val": int(len(matrix.X_val)),
        "n_features": len(matrix.feature_names),
        "supervised": {
            "catboost_prediction_values_change": cb_default,
            "catboost_loss_function_change": cb_loss,
            "permutation_importance_neg_log_loss": perm,
        },
        "unsupervised": {
            "variance_threshold_flags": variance,
            "correlation_pairs_above_0_9": corr,
            "pca_cumulative_variance": pca,
            "missingness": miss,
        },
        "high_impact_features": high_impact,
        "family_aggregate": families,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORT_DIR / f"feature_impact_{league}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  report written: {out_path}", flush=True)
    return report


def write_summary(reports: list[dict[str, Any]]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Feature-impact summary (1x2)\n"]
    lines.append(f"Train seasons: {reports[0]['train_seasons']}; val season: {reports[0]['val_season']}\n")

    families = sorted({fam for r in reports for fam in r["family_aggregate"]})
    lines.append("## Family — high-impact feature count per league\n")
    header = "| Family | " + " | ".join(r["league"] for r in reports) + " |"
    sep = "|---|" + "|".join(["---:"] * len(reports)) + "|"
    lines.append(header)
    lines.append(sep)
    for fam in families:
        cells = []
        for r in reports:
            agg = r["family_aggregate"].get(fam, {"n_high_impact": 0, "n_total": 0})
            cells.append(f"{agg['n_high_impact']}/{agg['n_total']}")
        lines.append(f"| {fam} | " + " | ".join(cells) + " |")

    lines.append("\n## Top 5 high-impact features per league\n")
    for r in reports:
        lines.append(f"### {r['league']}")
        if not r["high_impact_features"]:
            lines.append("_no feature qualified_\n")
            continue
        for row in r["high_impact_features"][:5]:
            lines.append(f"- `{row['feature']}` ({row['family']}, {row['method_count']}/3 methods)")
        lines.append("")

    lines.append("## Phase-0 sign-off checks\n")
    for r in reports:
        lg = r["league"]
        miss = {row["feature"]: row for row in r["unsupervised"]["missingness"]}
        real_xg_zero = {
            f: m["zero_fraction_by_season"]
            for f, m in miss.items()
            if m["family"] == "real_xg" and f != "has_real_xg"
        }
        # CH 2021-22/2022-23 expectation
        ch_check = ""
        if lg == "CH" and real_xg_zero:
            zero_2021 = next(iter(real_xg_zero.values())).get("2021-22", -1.0)
            zero_2022 = next(iter(real_xg_zero.values())).get("2022-23", -1.0)
            ch_check = f" — CH real_xg zero-fraction: 2021-22={zero_2021:.2f}, 2022-23={zero_2022:.2f}"
        top_families = {
            row["family"] for row in r["high_impact_features"][:5]
        }
        anchors = {"pi_ratings", "market_odds"}
        anchors_present = ", ".join(sorted(top_families & anchors)) or "(none)"
        lines.append(
            f"- **{lg}**: anchors in top-5 = {anchors_present}{ch_check}"
        )

    out = REPORT_DIR / "feature_impact_summary.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--league",
        default="all",
        help="League key (PL/CH/BL/SA/LL) or 'all' (default).",
    )
    parser.add_argument(
        "--train-seasons",
        default=",".join(DEFAULT_TRAIN_SEASONS),
        help="Comma-separated train seasons (season-mode default: 2021-22,2022-23). "
             "Ignored when --cutoff is given.",
    )
    parser.add_argument(
        "--val-season",
        default=DEFAULT_VAL_SEASON,
        help="Validation season (season-mode default: 2023-24). Ignored when --cutoff is given.",
    )
    parser.add_argument(
        "--cutoff",
        default=None,
        help="Optional date-cutoff mode (YYYY-MM-DD). Train rows ≤ cutoff, "
             "val rows in (cutoff, --test-end]. Overrides --train-seasons / --val-season.",
    )
    parser.add_argument(
        "--test-end",
        default=None,
        help="Date-cutoff val window end (YYYY-MM-DD). Required if --cutoff is given.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    league_arg = args.league.upper()
    leagues = LEAGUES_ALL if league_arg == "ALL" else (league_arg,)
    if league_arg != "ALL" and league_arg not in LEAGUES_ALL:
        print(f"Unknown league: {league_arg}", file=sys.stderr)
        return 2

    cutoff: date | None = None
    test_end: date | None = None
    train_seasons: tuple[str, ...] | None = None
    val_season: str | None = None
    if args.cutoff:
        if not args.test_end:
            print("--cutoff requires --test-end", file=sys.stderr)
            return 2
        cutoff = datetime.strptime(args.cutoff, "%Y-%m-%d").date()
        test_end = datetime.strptime(args.test_end, "%Y-%m-%d").date()
        if cutoff >= test_end:
            print("--cutoff must be strictly before --test-end", file=sys.stderr)
            return 2
    else:
        train_seasons = tuple(s.strip() for s in args.train_seasons.split(",") if s.strip())
        val_season = args.val_season.strip()

    print(f"Data dir: {DATA_DIR}")
    if cutoff:
        print(f"Mode: cutoff   train ≤ {cutoff}   val ({cutoff}, {test_end}]")
    else:
        print(f"Mode: season   train_seasons={train_seasons}   val_season={val_season}")
    print(f"Leagues: {leagues}")

    reports = []
    for lg in leagues:
        try:
            reports.append(
                run_league(
                    lg,
                    train_seasons=train_seasons,
                    val_season=val_season,
                    cutoff=cutoff,
                    test_end=test_end,
                    # Cutoff val window may be small (~50 PL matches); allow.
                    min_val_rows=30 if cutoff else 50,
                )
            )
        except Exception as exc:
            print(f"  ERROR for {lg}: {exc}", file=sys.stderr)
            raise

    if len(reports) > 1:
        summary_path = write_summary(reports)
        print(f"\nSummary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
