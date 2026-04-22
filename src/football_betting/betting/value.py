"""
Value-bet identification.

A value bet exists when the model's estimated probability of an outcome
exceeds the bookmaker's implied (margin-adjusted) probability by at least
a configured threshold.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from football_betting.betting.kelly import kelly_fraction, kelly_stake
from football_betting.betting.margin import remove_margin
from football_betting.config import BETTING_CFG, BettingConfig
from football_betting.data.models import Outcome, Prediction


OUTCOME_LABELS: dict[Outcome, str] = {
    "H": "Heim",
    "D": "Unentschieden",
    "A": "Auswärts",
}


@dataclass(slots=True)
class ValueBet:
    """A single identified value-betting opportunity."""

    home_team: str
    away_team: str
    league: str
    date: str
    outcome: Outcome
    model_prob: float
    market_prob: float
    odds: float
    edge: float
    kelly_full: float
    kelly_stake: float
    expected_value_pct: float
    confidence: Literal["low", "medium", "high"] = "medium"

    @property
    def bet_label(self) -> str:
        """Human-readable description."""
        side = (
            self.home_team
            if self.outcome == "H"
            else self.away_team if self.outcome == "A"
            else "Unentschieden"
        )
        suffix = "Heimsieg" if self.outcome == "H" else "Auswärtssieg" if self.outcome == "A" else ""
        return f"{side} {suffix}".strip()

    @property
    def edge_pct(self) -> float:
        return self.edge * 100

    def __str__(self) -> str:
        stars = "⭐⭐⭐" if self.edge > 0.10 else "⭐⭐" if self.edge > 0.05 else "⭐"
        return (
            f"{stars} {self.home_team} vs {self.away_team} ({self.league})\n"
            f"   → {self.bet_label} @ {self.odds:.2f}\n"
            f"   Model: {self.model_prob * 100:.1f}% | Market: {self.market_prob * 100:.1f}% | "
            f"Edge: {self.edge_pct:+.1f}%\n"
            f"   Stake: {self.kelly_stake:.2f} | EV: {self.expected_value_pct:+.1f}%"
        )


def _confidence_level(edge: float, odds: float) -> Literal["low", "medium", "high"]:
    """Heuristic confidence based on edge and odds range."""
    if edge > 0.08 and 1.5 <= odds <= 4.0:
        return "high"
    if edge < 0.04 or odds > 6.0 or odds < 1.3:
        return "low"
    return "medium"


def find_value_bets(
    prediction: Prediction,
    bankroll: float,
    cfg: BettingConfig | None = None,
) -> list[ValueBet]:
    """
    Compare model probabilities against bookmaker odds; flag opportunities
    where edge exceeds the configured threshold.
    """
    cfg = cfg or BETTING_CFG
    fixture = prediction.fixture

    if fixture.odds is None:
        return []

    oh, od, oa = fixture.odds.home, fixture.odds.draw, fixture.odds.away
    mh, md, ma = remove_margin(oh, od, oa, method=cfg.devig_method)

    candidates: list[tuple[Outcome, float, float, float]] = [
        ("H", prediction.prob_home, mh, oh),
        ("D", prediction.prob_draw, md, od),
        ("A", prediction.prob_away, ma, oa),
    ]

    value_bets: list[ValueBet] = []
    for outcome, model_p, market_p, odds in candidates:
        edge = model_p - market_p

        if edge < cfg.min_edge:
            continue
        if not (cfg.min_odds <= odds <= cfg.max_odds):
            continue

        k_full = kelly_fraction(model_p, odds)
        stake = kelly_stake(model_p, odds, bankroll, cfg)
        ev_pct = (model_p * odds - 1.0) * 100

        value_bets.append(
            ValueBet(
                home_team=fixture.home_team,
                away_team=fixture.away_team,
                league=fixture.league,
                date=fixture.date.isoformat(),
                outcome=outcome,
                model_prob=model_p,
                market_prob=market_p,
                odds=odds,
                edge=edge,
                kelly_full=k_full,
                kelly_stake=stake,
                expected_value_pct=ev_pct,
                confidence=_confidence_level(edge, odds),
            )
        )

    return value_bets


def rank_value_bets(bets: list[ValueBet], by: str = "edge") -> list[ValueBet]:
    """Sort value bets descending by given attribute."""
    return sorted(bets, key=lambda b: getattr(b, by), reverse=True)
