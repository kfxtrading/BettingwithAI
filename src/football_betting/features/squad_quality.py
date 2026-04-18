"""
Squad Quality Features — from Sofascore lineup data.

Rolling average of starting-XI ratings, plus key-player-absence detection
by comparing current XI to the team's "season XI" (most-frequent starters).
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field

from football_betting.config import SquadQualityConfig


@dataclass(slots=True)
class LineupRecord:
    """Single match's lineup for one team."""

    avg_rating: float
    starting_xi: list[int]  # player IDs
    was_home: bool


@dataclass(slots=True)
class SquadQualityTracker:
    """Rolling squad-quality tracker."""

    cfg: SquadQualityConfig = field(default_factory=SquadQualityConfig)
    history: dict[str, deque[LineupRecord]] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=50))
    )
    # Player appearance counter per team (season XI identification)
    _player_counts: dict[str, Counter] = field(
        default_factory=lambda: defaultdict(Counter)
    )

    # ───────────────────────── Ingestion ─────────────────────────

    def ingest_sofascore_match(self, match_dict: dict) -> None:
        """Ingest one Sofascore match's lineup data.

        Rating alone is enough to populate the rolling-rating feature.
        Starting-XI is optional: rotation/key-absence features stay at 0
        when XI lists are missing but the avg_rating trail remains live.
        """
        home_team = match_dict["home_team"]
        away_team = match_dict["away_team"]
        home_rating = match_dict.get("home_avg_rating")
        away_rating = match_dict.get("away_avg_rating")
        home_xi = match_dict.get("home_starting_xi") or []
        away_xi = match_dict.get("away_starting_xi") or []

        if home_rating is None and away_rating is None:
            return

        if home_rating is not None:
            self.history[home_team].append(
                LineupRecord(
                    avg_rating=float(home_rating),
                    starting_xi=list(home_xi),
                    was_home=True,
                )
            )
            for pid in home_xi:
                self._player_counts[home_team][pid] += 1

        if away_rating is not None:
            self.history[away_team].append(
                LineupRecord(
                    avg_rating=float(away_rating),
                    starting_xi=list(away_xi),
                    was_home=False,
                )
            )
            for pid in away_xi:
                self._player_counts[away_team][pid] += 1

    def ingest_many(self, match_dicts: list[dict]) -> None:
        for m in match_dicts:
            self.ingest_sofascore_match(m)

    # ───────────────────────── Analysis ─────────────────────────

    def _season_xi(self, team: str) -> set[int]:
        """Identify the team's most-frequent starters."""
        total_games = len(self.history.get(team, []))
        if total_games < self.cfg.season_xi_min_games:
            return set()
        counts = self._player_counts.get(team, Counter())
        threshold = int(total_games * self.cfg.absence_threshold)
        return {pid for pid, count in counts.items() if count >= threshold}

    def _rolling_rating(self, team: str) -> float:
        """Average starting-XI rating over last N games."""
        recs = list(self.history.get(team, []))[-self.cfg.rating_window:]
        if not recs:
            return 0.0
        return sum(r.avg_rating for r in recs) / len(recs)

    def _rotation_score(self, team: str) -> float:
        """Fraction of starters changed vs. previous match. 0 = no rotation, 1 = 11 changes."""
        recs = list(self.history.get(team, []))
        if len(recs) < 2:
            return 0.0
        last = set(recs[-1].starting_xi)
        prev = set(recs[-2].starting_xi)
        changes = len(last.symmetric_difference(prev)) / 2  # each swap counts once
        return min(1.0, changes / 11)

    def _key_absences(self, team: str) -> int:
        """How many season-XI players are missing from last starting XI."""
        recs = list(self.history.get(team, []))
        if not recs:
            return 0
        season_xi = self._season_xi(team)
        if not season_xi:
            return 0
        last_xi = set(recs[-1].starting_xi)
        return len(season_xi - last_xi)

    # ───────────────────────── Features ─────────────────────────

    def features_for_match(self, home_team: str, away_team: str) -> dict[str, float]:
        h_rating = self._rolling_rating(home_team)
        a_rating = self._rolling_rating(away_team)
        h_rotation = self._rotation_score(home_team)
        a_rotation = self._rotation_score(away_team)
        h_absences = self._key_absences(home_team)
        a_absences = self._key_absences(away_team)

        return {
            "squad_home_rating": h_rating,
            "squad_away_rating": a_rating,
            "squad_rating_diff": h_rating - a_rating,
            "squad_home_rotation": h_rotation,
            "squad_away_rotation": a_rotation,
            "squad_home_key_absences": float(h_absences),
            "squad_away_key_absences": float(a_absences),
            "squad_absence_diff": float(a_absences - h_absences),  # negative = home disadvantage
        }
