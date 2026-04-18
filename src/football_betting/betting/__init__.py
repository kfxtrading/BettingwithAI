"""Betting logic: value-bets, Kelly, margin removal."""
from football_betting.betting.kelly import kelly_fraction, kelly_stake
from football_betting.betting.margin import remove_margin
from football_betting.betting.value import ValueBet, find_value_bets

__all__ = [
    "ValueBet",
    "find_value_bets",
    "kelly_fraction",
    "kelly_stake",
    "remove_margin",
]
