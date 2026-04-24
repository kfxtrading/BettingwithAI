"""Tipster-platform export — formats today's value bets into ready-to-post text.

Used by the Week 3-4 SEO sprint to seed daily tipster posts on Oddspedia,
OLBG, ProTipster, Tipstrr, Typersi and Sportytrader. The platforms all
accept slightly different inputs (markdown, plain text, HTML, CSV upload),
so this module produces every common variant from a single snapshot.

The generated text is *editorial-ready*: a human still reviews and posts
it. We do not auto-post — every platform's TOS forbids bot submissions.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final, Literal, cast

OutcomeCode = Literal["H", "D", "A"]
ExportFormat = Literal["markdown", "plain", "csv", "json"]

OUTCOME_LABEL: Final[dict[str, str]] = {"H": "Home win", "D": "Draw", "A": "Away win"}


@dataclass(frozen=True, slots=True)
class TipsterPick:
    """One curated pick suitable for a tipster-platform post."""

    league_name: str
    home_team: str
    away_team: str
    kickoff_utc: str
    outcome: OutcomeCode
    pick_label: str
    odds: float | None
    model_prob: float
    market_prob: float | None
    edge_pct: float | None
    kelly_pct: float | None

    @property
    def matchup(self) -> str:
        return f"{self.home_team} vs {self.away_team}"

    @property
    def kickoff_human(self) -> str:
        try:
            return (
                datetime.fromisoformat(self.kickoff_utc.replace("Z", "+00:00"))
                .strftime("%Y-%m-%d %H:%M UTC")
            )
        except ValueError:
            return self.kickoff_utc


def _outcome_label(outcome: str, home: str, away: str) -> str:
    if outcome == "H":
        return f"{home} to win"
    if outcome == "A":
        return f"{away} to win"
    return "Draw"


def _pick_from_value_bet(vb: dict[str, Any]) -> TipsterPick:
    return TipsterPick(
        league_name=vb.get("league_name") or vb.get("league", ""),
        home_team=vb["home_team"],
        away_team=vb["away_team"],
        kickoff_utc=vb.get("kickoff_utc", vb.get("date", "")),
        outcome=vb["outcome"],
        pick_label=vb.get("bet_label")
        or _outcome_label(vb["outcome"], vb["home_team"], vb["away_team"]),
        odds=float(vb["odds"]) if vb.get("odds") is not None else None,
        model_prob=float(vb["model_prob"]),
        market_prob=float(vb["market_prob"]) if vb.get("market_prob") is not None else None,
        edge_pct=float(vb["edge_pct"]) if vb.get("edge_pct") is not None else None,
        kelly_pct=float(vb["kelly_stake"]) * 100 if vb.get("kelly_stake") is not None else None,
    )


def _pick_from_prediction(pred: dict[str, Any]) -> TipsterPick:
    """Fallback: derive a pick from a 1X2 prediction when no value bets exist."""
    probs: dict[str, float] = {
        "H": float(pred["prob_home"]),
        "D": float(pred["prob_draw"]),
        "A": float(pred["prob_away"]),
    }
    outcome = cast(OutcomeCode, max(probs, key=lambda k: probs[k]))
    return TipsterPick(
        league_name=pred.get("league_name") or pred.get("league", ""),
        home_team=pred["home_team"],
        away_team=pred["away_team"],
        kickoff_utc=pred.get("kickoff_utc", pred.get("date", "")),
        outcome=outcome,
        pick_label=_outcome_label(outcome, pred["home_team"], pred["away_team"]),
        odds=None,
        model_prob=float(probs[outcome]),
        market_prob=None,
        edge_pct=None,
        kelly_pct=None,
    )


def select_picks(
    snapshot: dict[str, Any],
    *,
    limit: int = 5,
    min_edge_pct: float = 3.0,
) -> list[TipsterPick]:
    """Return up to ``limit`` curated picks for posting today.

    Prefers genuine value bets (edge >= min_edge_pct). When the snapshot
    has no value bets (e.g. odds API quota exhausted), falls back to the
    top-N highest-confidence 1X2 predictions so the daily posting routine
    is never empty.
    """
    value_bets = list(snapshot.get("value_bets") or [])
    filtered = [
        vb for vb in value_bets
        if vb.get("edge_pct") is None or float(vb["edge_pct"]) >= min_edge_pct
    ]
    filtered.sort(
        key=lambda vb: float(vb.get("edge_pct") or 0.0),
        reverse=True,
    )
    if filtered:
        return [_pick_from_value_bet(vb) for vb in filtered[:limit]]

    preds = list(snapshot.get("predictions") or [])
    preds.sort(
        key=lambda p: max(p["prob_home"], p["prob_draw"], p["prob_away"]),
        reverse=True,
    )
    return [_pick_from_prediction(p) for p in preds[:limit]]


def _format_pct(value: float | None, *, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f}%"


def _format_odds(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}"


def render_markdown(picks: Sequence[TipsterPick], *, today: date | None = None) -> str:
    """Render picks as a markdown post (Tipstrr, OLBG, Reddit-friendly)."""
    today = today or date.today()
    lines: list[str] = []
    lines.append(f"## Daily value bets — {today.isoformat()}")
    lines.append("")
    lines.append(
        "Source: bettingwithai.app — CatBoost + Poisson + MLP ensemble, "
        "isotonic-calibrated. Stakes are fractional Kelly (25–50% of full)."
    )
    lines.append("")
    for i, p in enumerate(picks, start=1):
        edge = _format_pct(p.edge_pct)
        kelly = _format_pct(p.kelly_pct, decimals=2)
        prob = _format_pct(p.model_prob * 100)
        odds = _format_odds(p.odds)
        lines.append(
            f"**{i}. {p.league_name}: {p.matchup}** — *{p.kickoff_human}*  "
        )
        lines.append(
            f"Pick: **{p.pick_label}** @ {odds} · model {prob} · edge {edge} · Kelly {kelly}"
        )
        lines.append("")
    lines.append(
        "_Track record and methodology: https://bettingwithai.app/performance_"
    )
    return "\n".join(lines).rstrip() + "\n"


def render_plain(picks: Sequence[TipsterPick], *, today: date | None = None) -> str:
    """Render picks as plain text (Oddspedia comment box, Discord, email)."""
    today = today or date.today()
    out = [f"Daily value bets — {today.isoformat()}", ""]
    for i, p in enumerate(picks, start=1):
        line = (
            f"{i}. {p.league_name} | {p.matchup} ({p.kickoff_human}) "
            f"| Pick: {p.pick_label} @ {_format_odds(p.odds)} "
            f"| model {_format_pct(p.model_prob * 100)} "
            f"| edge {_format_pct(p.edge_pct)} "
            f"| Kelly {_format_pct(p.kelly_pct, decimals=2)}"
        )
        out.append(line)
    out.append("")
    out.append("More: bettingwithai.app/performance")
    return "\n".join(out) + "\n"


def render_csv(picks: Sequence[TipsterPick]) -> str:
    """Render picks as CSV (Tipstrr / ProTipster bulk-upload friendly)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "league",
            "kickoff_utc",
            "home_team",
            "away_team",
            "pick",
            "odds",
            "model_prob",
            "market_prob",
            "edge_pct",
            "kelly_pct",
        ]
    )
    for p in picks:
        writer.writerow(
            [
                p.league_name,
                p.kickoff_utc,
                p.home_team,
                p.away_team,
                p.pick_label,
                "" if p.odds is None else f"{p.odds:.2f}",
                f"{p.model_prob:.4f}",
                "" if p.market_prob is None else f"{p.market_prob:.4f}",
                "" if p.edge_pct is None else f"{p.edge_pct:.2f}",
                "" if p.kelly_pct is None else f"{p.kelly_pct:.4f}",
            ]
        )
    return buf.getvalue()


def render_json(picks: Sequence[TipsterPick]) -> str:
    """Render picks as JSON (machine-readable, for our own posting bots)."""
    payload = [
        {
            "league_name": p.league_name,
            "home_team": p.home_team,
            "away_team": p.away_team,
            "kickoff_utc": p.kickoff_utc,
            "outcome": p.outcome,
            "pick_label": p.pick_label,
            "odds": p.odds,
            "model_prob": p.model_prob,
            "market_prob": p.market_prob,
            "edge_pct": p.edge_pct,
            "kelly_pct": p.kelly_pct,
        }
        for p in picks
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


_VALID_FORMATS: Final[frozenset[str]] = frozenset(
    {"markdown", "plain", "csv", "json"}
)


def render(
    picks: Sequence[TipsterPick],
    fmt: ExportFormat,
    *,
    today: date | None = None,
) -> str:
    if fmt not in _VALID_FORMATS:
        raise ValueError(f"Unknown format: {fmt!r}")
    if fmt == "markdown":
        return render_markdown(picks, today=today)
    if fmt == "plain":
        return render_plain(picks, today=today)
    if fmt == "csv":
        return render_csv(picks)
    return render_json(picks)


def export_from_snapshot(
    snapshot_path: Path,
    *,
    formats: Iterable[ExportFormat] = ("markdown", "plain", "csv", "json"),
    output_dir: Path,
    limit: int = 5,
    min_edge_pct: float = 3.0,
    today: date | None = None,
) -> dict[ExportFormat, Path]:
    """Read a today.json snapshot and write tipster posts to ``output_dir``.

    Returns a mapping ``{format: written_path}``.
    """
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    picks = select_picks(snapshot, limit=limit, min_edge_pct=min_edge_pct)

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = (today or date.today()).isoformat()
    suffix_map: dict[ExportFormat, str] = {
        "markdown": "md",
        "plain": "txt",
        "csv": "csv",
        "json": "json",
    }

    written: dict[ExportFormat, Path] = {}
    for fmt in formats:
        text = render(picks, fmt, today=today)
        path = output_dir / f"tipster-{stamp}.{suffix_map[fmt]}"
        path.write_text(text, encoding="utf-8")
        written[fmt] = path
    return written
