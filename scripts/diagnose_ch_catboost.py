"""Diagnose: why do CH predictions look uniform?

Runs the CH CatBoost predictor on every CH fixture in
data/fixtures_2026-04-25.json and prints raw vs calibrated probabilities for
each match. Helps separate "CatBoost is uninformative" from "calibrator is
collapsing everything to the same point".

Usage::

    python scripts/diagnose_ch_catboost.py
"""

from __future__ import annotations

import json

import pandas as pd

from football_betting.config import DATA_DIR
from football_betting.data.loader import load_league
from football_betting.data.models import Fixture
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.predict.runtime import warm_feature_builder


def _to_fixture(d: dict) -> Fixture:
    return Fixture(
        date=d["date"],
        league=d["league"],
        home_team=d["home_team"],
        away_team=d["away_team"],
        kickoff_time=d.get("kickoff_time"),
    )


def main() -> None:
    fixtures_path = DATA_DIR / "fixtures_2026-04-25.json"
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    ch_fixtures = [f for f in fixtures if f["league"] == "CH"]
    print(f"CH fixtures: {len(ch_fixtures)}\n")

    matches = load_league("CH")
    print(f"Loaded {len(matches)} CH matches; warming feature builder...")
    fb, _ = warm_feature_builder("CH", matches, purpose="1x2")
    cb = CatBoostPredictor.for_league("CH", feature_builder=fb)

    if cb.model is None:
        print("CatBoost CH model not loaded.")
        return

    print(f"Calibrator fitted: {cb.calibrator and cb.calibrator.is_fitted}")
    print(f"Feature count: {len(cb.feature_names)}\n")

    rows = []
    for fx in ch_fixtures:
        fixture = _to_fixture(fx)
        feats = fb.features_for_fixture(fixture)
        X = pd.DataFrame([feats])[cb.feature_names]
        raw = cb.model.predict_proba(X)[0]
        if cb.calibrator and cb.calibrator.is_fitted:
            cal = cb.calibrator.transform(raw.reshape(1, -1))[0]
        else:
            cal = raw
        rows.append(
            {
                "match": f"{fx['home_team']:>20} vs {fx['away_team']:<18}",
                "raw_H": f"{raw[0]:.3f}",  # OUTCOME_TO_INT: H=0, D=1, A=2
                "raw_D": f"{raw[1]:.3f}",
                "raw_A": f"{raw[2]:.3f}",
                "cal_H": f"{cal[0]:.3f}",
                "cal_D": f"{cal[1]:.3f}",
                "cal_A": f"{cal[2]:.3f}",
            }
        )

    # Print as table
    print(
        f"{'Match':45} {'raw H':>6} {'raw D':>6} {'raw A':>6}  {'cal H':>6} {'cal D':>6} {'cal A':>6}"
    )
    print("-" * 95)
    for r in rows:
        print(
            f"{r['match']:45} {r['raw_H']:>6} {r['raw_D']:>6} {r['raw_A']:>6}  {r['cal_H']:>6} {r['cal_D']:>6} {r['cal_A']:>6}"
        )

    # Spread analysis
    raw_h = [float(r["raw_H"]) for r in rows]
    cal_h = [float(r["cal_H"]) for r in rows]
    print(
        f"\nraw H spread:  min={min(raw_h):.3f} max={max(raw_h):.3f}  range={max(raw_h) - min(raw_h):.3f}"
    )
    print(
        f"cal H spread:  min={min(cal_h):.3f} max={max(cal_h):.3f}  range={max(cal_h) - min(cal_h):.3f}"
    )


if __name__ == "__main__":
    main()
