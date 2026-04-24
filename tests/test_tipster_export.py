"""Tests for the tipster-platform export pipeline (Week 3-4 SEO sprint)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from football_betting.seo.tipster_export import (
    TipsterPick,
    export_from_snapshot,
    render,
    render_csv,
    render_json,
    render_markdown,
    render_plain,
    select_picks,
)


def _vb(home: str, away: str, edge_pct: float, **overrides) -> dict:
    base = {
        "league_name": "Premier League",
        "home_team": home,
        "away_team": away,
        "kickoff_utc": "2026-04-25T14:00:00Z",
        "outcome": "H",
        "bet_label": "Home",
        "odds": 2.10,
        "model_prob": 0.55,
        "market_prob": 0.48,
        "edge_pct": edge_pct,
        "kelly_stake": 0.025,
    }
    base.update(overrides)
    return base


def _pred(home: str, away: str, ph: float, pd: float, pa: float) -> dict:
    return {
        "league_name": "Premier League",
        "league": "PL",
        "home_team": home,
        "away_team": away,
        "kickoff_utc": "2026-04-25T14:00:00Z",
        "date": "2026-04-25",
        "prob_home": ph,
        "prob_draw": pd,
        "prob_away": pa,
    }


def test_select_picks_prefers_value_bets_sorted_by_edge() -> None:
    snap = {
        "value_bets": [
            _vb("A", "B", edge_pct=4.0),
            _vb("C", "D", edge_pct=10.0),
            _vb("E", "F", edge_pct=1.0),  # below default 3% floor
            _vb("G", "H", edge_pct=7.5),
        ],
        "predictions": [],
    }
    picks = select_picks(snap, limit=3)
    assert [p.matchup for p in picks] == ["C vs D", "G vs H", "A vs B"]


def test_select_picks_falls_back_to_top_predictions_when_no_value_bets() -> None:
    snap = {
        "value_bets": [],
        "predictions": [
            _pred("Low", "Conf", 0.40, 0.30, 0.30),
            _pred("High", "Conf", 0.70, 0.20, 0.10),
            _pred("Mid", "Conf", 0.55, 0.25, 0.20),
        ],
    }
    picks = select_picks(snap, limit=2)
    assert picks[0].matchup == "High vs Conf"
    assert picks[0].outcome == "H"
    assert picks[1].matchup == "Mid vs Conf"


def test_select_picks_respects_min_edge_pct_filter() -> None:
    snap = {"value_bets": [_vb("A", "B", edge_pct=2.5)], "predictions": []}
    picks = select_picks(snap, min_edge_pct=3.0)
    assert picks == []


def test_render_markdown_contains_methodology_signals() -> None:
    picks = [TipsterPick(
        league_name="La Liga",
        home_team="Real Madrid",
        away_team="Sevilla",
        kickoff_utc="2026-04-26T19:00:00Z",
        outcome="H",
        pick_label="Real Madrid to win",
        odds=1.85,
        model_prob=0.62,
        market_prob=0.54,
        edge_pct=8.0,
        kelly_pct=3.2,
    )]
    out = render_markdown(picks, today=date(2026, 4, 25))
    assert "Daily value bets — 2026-04-25" in out
    assert "Real Madrid to win" in out
    assert "@ 1.85" in out
    assert "edge 8.0%" in out
    assert "Kelly 3.20%" in out
    assert "bettingwithai.app/performance" in out


def test_render_plain_one_line_per_pick() -> None:
    picks = [TipsterPick(
        league_name="Bundesliga",
        home_team="Bayern",
        away_team="Dortmund",
        kickoff_utc="2026-04-26T17:30:00Z",
        outcome="H",
        pick_label="Bayern to win",
        odds=1.70,
        model_prob=0.60,
        market_prob=0.55,
        edge_pct=5.0,
        kelly_pct=2.5,
    )]
    out = render_plain(picks, today=date(2026, 4, 25))
    body = [line for line in out.splitlines() if line.startswith("1. ")]
    assert len(body) == 1
    assert "Bayern vs Dortmund" in body[0]


def test_render_csv_has_header_and_row() -> None:
    picks = [TipsterPick(
        league_name="Serie A",
        home_team="Inter",
        away_team="Lazio",
        kickoff_utc="2026-04-26T18:45:00Z",
        outcome="H",
        pick_label="Inter to win",
        odds=1.55,
        model_prob=0.66,
        market_prob=0.62,
        edge_pct=4.0,
        kelly_pct=1.8,
    )]
    out = render_csv(picks)
    lines = out.strip().splitlines()
    assert lines[0].startswith("league,kickoff_utc,home_team,away_team,pick,odds")
    assert "Inter,Lazio,Inter to win,1.55" in lines[1]


def test_render_json_roundtrip() -> None:
    picks = [TipsterPick(
        league_name="Ligue 1",
        home_team="PSG",
        away_team="Lille",
        kickoff_utc="2026-04-26T19:00:00Z",
        outcome="H",
        pick_label="PSG to win",
        odds=1.40,
        model_prob=0.72,
        market_prob=0.68,
        edge_pct=4.5,
        kelly_pct=2.2,
    )]
    out = render_json(picks)
    parsed = json.loads(out)
    assert parsed[0]["home_team"] == "PSG"
    assert parsed[0]["edge_pct"] == 4.5


def test_render_dispatcher_unknown_format_raises() -> None:
    with pytest.raises(ValueError):
        render([], "yaml")  # type: ignore[arg-type]


def test_export_from_snapshot_writes_all_formats(tmp_path: Path) -> None:
    snap = {
        "value_bets": [_vb("A", "B", edge_pct=6.0)],
        "predictions": [_pred("A", "B", 0.55, 0.25, 0.20)],
    }
    snap_path = tmp_path / "today.json"
    snap_path.write_text(json.dumps(snap), encoding="utf-8")
    out_dir = tmp_path / "out"

    written = export_from_snapshot(
        snap_path,
        formats=("markdown", "plain", "csv", "json"),
        output_dir=out_dir,
        today=date(2026, 4, 25),
    )
    assert set(written) == {"markdown", "plain", "csv", "json"}
    assert written["markdown"].name == "tipster-2026-04-25.md"
    assert written["csv"].read_text(encoding="utf-8").startswith("league,kickoff_utc")
    assert written["json"].read_text(encoding="utf-8").lstrip().startswith("[")
