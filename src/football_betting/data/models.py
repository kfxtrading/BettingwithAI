"""Data models (dataclasses & pydantic) for matches, fixtures, odds, predictions."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Outcome = Literal["H", "D", "A"]


class MatchOdds(BaseModel):
    """Bookmaker 1X2 odds for a single match."""

    home: float = Field(gt=1.0, description="Decimal odds for home win")
    draw: float = Field(gt=1.0, description="Decimal odds for draw")
    away: float = Field(gt=1.0, description="Decimal odds for away win")
    bookmaker: str = "avg"

    @property
    def margin(self) -> float:
        """Bookmaker overround (e.g. 0.05 = 5% margin)."""
        return (1 / self.home + 1 / self.draw + 1 / self.away) - 1.0

    def fair_probs(self) -> tuple[float, float, float]:
        """Margin-adjusted implied probabilities (sum to 1)."""
        total = 1 / self.home + 1 / self.draw + 1 / self.away
        return (
            (1 / self.home) / total,
            (1 / self.draw) / total,
            (1 / self.away) / total,
        )


class Match(BaseModel):
    """Historical match with result and (optional) closing odds."""

    date: date
    league: str
    season: str
    home_team: str
    away_team: str
    home_goals: int = Field(ge=0)
    away_goals: int = Field(ge=0)
    home_shots: int | None = None
    away_shots: int | None = None
    home_shots_on_target: int | None = None
    away_shots_on_target: int | None = None
    odds: MatchOdds | None = None
    # Phase 4: optional pre-match (opening / T-48h) odds snapshot. When present,
    # downstream code treats `odds` as the closing-line and `opening_odds` as
    # the price at placement, enabling non-degenerate CLV computation.
    opening_odds: MatchOdds | None = None
    # v0.4: best-effort kickoff timestamp. Always UTC-aware when populated from
    # the Sofascore scraper or football-data.co.uk loader (DST-resolved via
    # ``football_betting.utils.timezones``). Legacy naive values may appear in
    # older snapshots; downstream code should treat ``tzinfo is None`` as UTC.
    kickoff_datetime_utc: datetime | None = None

    @property
    def result(self) -> Outcome:
        if self.home_goals > self.away_goals:
            return "H"
        if self.home_goals < self.away_goals:
            return "A"
        return "D"

    @property
    def goal_diff(self) -> int:
        return self.home_goals - self.away_goals

    @field_validator("date", mode="before")
    @classmethod
    def _parse_date(cls, v: str | date | datetime) -> date:
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unrecognised date: {v}")
        raise TypeError(f"Bad date type: {type(v)}")

    @field_validator("kickoff_datetime_utc", mode="before")
    @classmethod
    def _parse_kickoff(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        raise TypeError(f"Bad kickoff_datetime_utc type: {type(v)}")


class Fixture(BaseModel):
    """Upcoming match without a result yet."""

    date: date
    league: str
    home_team: str
    away_team: str
    kickoff_time: str | None = None
    odds: MatchOdds | None = None
    season: str | None = None
    # v0.4: same semantics as Match.kickoff_datetime_utc.
    kickoff_datetime_utc: datetime | None = None

    @field_validator("date", mode="before")
    @classmethod
    def _parse_date(cls, v: str | date | datetime) -> date:
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unrecognised date: {v}")
        raise TypeError(f"Bad date type: {type(v)}")

    @field_validator("kickoff_datetime_utc", mode="before")
    @classmethod
    def _parse_kickoff(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        raise TypeError(f"Bad kickoff_datetime_utc type: {type(v)}")

    def resolve_kickoff(self) -> datetime | None:
        """Return kickoff datetime, deriving from `kickoff_time` (HH:MM) if needed."""
        if self.kickoff_datetime_utc is not None:
            return self.kickoff_datetime_utc
        if self.kickoff_time:
            try:
                hh, mm = self.kickoff_time.split(":")[:2]
                return datetime(self.date.year, self.date.month, self.date.day, int(hh), int(mm))
            except (ValueError, IndexError):
                return None
        return None

    def effective_season(self) -> str:
        """Return `season` if provided, else infer from `date` (Aug split)."""
        if self.season:
            return self.season
        year = self.date.year
        if self.date.month >= 8:
            return f"{year}-{str(year + 1)[-2:]}"
        return f"{year - 1}-{str(year)[-2:]}"


class Prediction(BaseModel):
    """A single model prediction for a fixture."""

    fixture: Fixture
    model_name: str
    prob_home: float = Field(ge=0.0, le=1.0)
    prob_draw: float = Field(ge=0.0, le=1.0)
    prob_away: float = Field(ge=0.0, le=1.0)
    expected_home_goals: float | None = None
    expected_away_goals: float | None = None

    @field_validator("prob_away")
    @classmethod
    def _check_sum(cls, v: float, info) -> float:
        probs = (
            info.data.get("prob_home", 0),
            info.data.get("prob_draw", 0),
            v,
        )
        if not (0.98 <= sum(probs) <= 1.02):
            raise ValueError(f"Probs must sum to 1: got {sum(probs):.4f}")
        return v

    @property
    def most_likely_outcome(self) -> Outcome:
        probs = [self.prob_home, self.prob_draw, self.prob_away]
        return ["H", "D", "A"][probs.index(max(probs))]

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.prob_home, self.prob_draw, self.prob_away)
