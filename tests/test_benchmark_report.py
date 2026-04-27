"""Tests for the model-vs-market benchmark report."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from click.testing import CliRunner

from football_betting.betting.margin import remove_margin
from football_betting.cli import main
from football_betting.tracking.backtest import BacktestResult
from football_betting.tracking.benchmark_report import (
    build_benchmark_report,
    load_opta_reference,
    market_implied_probs,
    weighted_all_outcome_clv,
)


def _row(
    *,
    match_date: str,
    home: str,
    away: str,
    actual: str,
    probs: tuple[float, float, float],
    odds: tuple[float, float, float],
    opening: tuple[float, float, float] | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "date": match_date,
        "home_team": home,
        "away_team": away,
        "actual": actual,
        "prob_home": probs[0],
        "prob_draw": probs[1],
        "prob_away": probs[2],
        "odds_home": odds[0],
        "odds_draw": odds[1],
        "odds_away": odds[2],
    }
    if opening is not None:
        row.update(
            {
                "opening_odds_home": opening[0],
                "opening_odds_draw": opening[1],
                "opening_odds_away": opening[2],
            }
        )
    return row


def test_market_implied_probs_uses_configured_devig_method() -> None:
    row = _row(
        match_date="2024-08-23",
        home="Home",
        away="Away",
        actual="H",
        probs=(0.6, 0.25, 0.15),
        odds=(2.0, 3.5, 4.0),
    )

    assert market_implied_probs(row, devig_method="multiplicative") == pytest.approx(
        remove_margin(2.0, 3.5, 4.0, method="multiplicative")
    )


def test_weighted_all_outcome_clv_requires_complete_opening_and_closing_odds() -> None:
    row = _row(
        match_date="2024-08-23",
        home="Home",
        away="Away",
        actual="H",
        probs=(0.6, 0.25, 0.15),
        odds=(2.0, 3.0, 4.0),
        opening=(2.2, 2.7, 4.4),
    )

    expected = 0.6 * (2.2 / 2.0 - 1.0) + 0.25 * (2.7 / 3.0 - 1.0) + 0.15 * (
        4.4 / 4.0 - 1.0
    )
    assert weighted_all_outcome_clv((0.6, 0.25, 0.15), row) == pytest.approx(expected)

    row_without_opening = dict(row)
    row_without_opening["opening_odds_draw"] = None
    assert weighted_all_outcome_clv((0.6, 0.25, 0.15), row_without_opening) is None


def test_build_benchmark_report_scores_model_market_and_deltas() -> None:
    rows = [
        _row(
            match_date="2024-08-23",
            home="Home",
            away="Away",
            actual="H",
            probs=(0.7, 0.2, 0.1),
            odds=(2.0, 3.0, 4.0),
            opening=(2.2, 2.7, 4.4),
        ),
        _row(
            match_date="2024-08-24",
            home="Other",
            away="Side",
            actual="A",
            probs=(0.2, 0.2, 0.6),
            odds=(2.8, 3.2, 2.6),
            opening=(2.6, 3.3, 2.9),
        ),
    ]

    report = build_benchmark_report("BL", rows, devig_method="multiplicative")

    assert report.coverage["n_predictions"] == 2
    assert report.coverage["n_with_odds"] == 2
    assert report.coverage["n_with_opening_odds"] == 2
    assert report.sources["our_model"].n == 2
    assert report.sources["market_implied"].n == 2
    assert report.sources["our_model"].mean_rps is not None
    assert report.sources["our_model"].mean_brier is not None
    assert report.sources["our_model"].ece is not None
    assert report.sources["our_model"].weighted_clv is not None
    assert report.sources["our_model"].delta_vs_market["n"] == 2


def test_opta_reference_csv_normalizes_percentages_and_tracks_unmatched(tmp_path: Path) -> None:
    path = tmp_path / "opta.csv"
    path.write_text(
        "\n".join(
            [
                "date,league,home_team,away_team,prob_home,prob_draw,prob_away,source_match_id",
                "2024-08-23,BL,Home,Away,70,20,10,opt-1",
                "2024-08-24,BL,Missing,Team,50,25,25,opt-2",
                "2024-08-25,PL,Ignored,Team,50,25,25,opt-3",
            ]
        ),
        encoding="utf-8",
    )
    refs = load_opta_reference(path, "BL")
    assert len(refs) == 2
    assert refs[0].probs == pytest.approx((0.7, 0.2, 0.1))

    rows = [
        _row(
            match_date="2024-08-23",
            home="Home",
            away="Away",
            actual="H",
            probs=(0.6, 0.3, 0.1),
            odds=(2.0, 3.0, 4.0),
            opening=(2.1, 3.1, 4.1),
        )
    ]
    report = build_benchmark_report(
        "BL",
        rows,
        devig_method="multiplicative",
        opta_reference_path=path,
    )
    assert report.coverage["n_opta_matched"] == 1
    assert report.coverage["n_opta_unmatched"] == 1
    assert report.sources["opta_reference"].n == 1


def test_opta_reference_json_shape_is_supported(tmp_path: Path) -> None:
    path = tmp_path / "opta.json"
    path.write_text(
        json.dumps(
            {
                "predictions": [
                    {
                        "date": "2024-08-23",
                        "league": "BL",
                        "home_team": "Home",
                        "away_team": "Away",
                        "prob_home": 0.7,
                        "prob_draw": 0.2,
                        "prob_away": 0.1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    refs = load_opta_reference(path, "BL")
    assert len(refs) == 1
    assert refs[0].probs == pytest.approx((0.7, 0.2, 0.1))


def test_cli_benchmark_report_smoke(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakeBacktester:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def run(self, league: str) -> BacktestResult:
            return BacktestResult(
                league=league,
                n_predictions=1,
                n_bets=0,
                metrics={},
                bet_metrics={},
                bankroll_final=1000.0,
                max_drawdown={"max_drawdown_abs": 0.0, "max_drawdown_pct": 0.0},
                rows=[
                    _row(
                        match_date=date(2024, 8, 23).isoformat(),
                        home="Home",
                        away="Away",
                        actual="H",
                        probs=(0.7, 0.2, 0.1),
                        odds=(2.0, 3.0, 4.0),
                        opening=(2.1, 3.1, 4.1),
                    )
                ],
            )

    monkeypatch.setattr("football_betting.cli.Backtester", FakeBacktester)

    result = CliRunner().invoke(
        main,
        [
            "benchmark-report",
            "--league",
            "BL",
            "--out-dir",
            str(tmp_path),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    out = tmp_path / "benchmark_report_BL.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert set(payload["sources"]) == {"our_model", "market_implied"}

