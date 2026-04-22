"""Sequence-feature extraction for the GRU+Attention match-history model.

Emits ``(T, F_seq)`` tensors per team using only matches that occurred
BEFORE the target match — leakage-free by construction because the
underlying FormTracker / PiRatings are updated chronologically.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from football_betting.features.form import FormTracker, MatchRecord
from football_betting.rating.pi_ratings import PiRatings

SEQ_FEATURE_NAMES: tuple[str, ...] = (
    "goals_for",
    "goals_against",
    "goal_diff",
    "shots",
    "shots_on_target",
    "is_home",
    "result_win",
    "result_draw",
    "result_loss",
    "points",
    "pi_home",
    "pi_away",
    "pi_overall",
    "ewma_idx",
)
N_SEQ_FEATURES = len(SEQ_FEATURE_NAMES)


def _record_vec(rec: MatchRecord, pi_home: float, pi_away: float, idx: int) -> list[float]:
    win = 1.0 if rec.result == "W" else 0.0
    draw = 1.0 if rec.result == "D" else 0.0
    loss = 1.0 if rec.result == "L" else 0.0
    points = 3.0 * win + 1.0 * draw
    shots = float(rec.shots) if rec.shots is not None else 0.0
    sot = float(rec.shots_on_target) if rec.shots_on_target is not None else 0.0
    return [
        float(rec.goals_scored),
        float(rec.goals_conceded),
        float(rec.goals_scored - rec.goals_conceded),
        shots,
        sot,
        1.0 if rec.was_home else 0.0,
        win,
        draw,
        loss,
        points,
        pi_home,
        pi_away,
        (pi_home + pi_away) / 2.0,
        float(idx) / 10.0,  # positional hint (oldest → newest)
    ]


@dataclass(slots=True)
class SequenceBuilder:
    """Builds ``(T, F_seq)`` team-history tensors from FormTracker + PiRatings."""

    form: FormTracker
    pi: PiRatings
    window_t: int = 10

    def build_team_sequence(self, team: str) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(seq, mask)`` — both shape ``(T,)`` for mask, ``(T, F_seq)`` for seq.

        ``mask[t] = 1`` → valid timestep, ``0`` → padding.
        Uses the team's CURRENT Pi-rating as a static channel (cheap proxy;
        per-timestep history would require `PiRatings.history` lookups by date).
        """
        recs = self.form.get_recent(team, self.window_t)
        t_dim = self.window_t
        seq = np.zeros((t_dim, N_SEQ_FEATURES), dtype=np.float32)
        mask = np.zeros((t_dim,), dtype=np.float32)
        if not recs:
            return seq, mask

        rating = self.pi.ratings[team]
        pi_h, pi_a = rating.home, rating.away

        # pad at the front so newest record sits at index t_dim-1
        start = t_dim - len(recs)
        for i, rec in enumerate(recs):
            seq[start + i] = _record_vec(rec, pi_h, pi_a, i)
            mask[start + i] = 1.0
        return seq, mask

    def build_pair(
        self,
        home_team: str,
        away_team: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return (home_seq, home_mask, away_seq, away_mask)."""
        hs, hm = self.build_team_sequence(home_team)
        as_, am = self.build_team_sequence(away_team)
        return hs, hm, as_, am


def build_dataset(
    matches: list,  # list[Match]
    form: FormTracker,
    pi: PiRatings,
    window_t: int = 10,
    warmup_games: int = 100,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Walk matches chronologically; extract sequences BEFORE each match, then update trackers.

    Returns (home_seq, home_mask, away_seq, away_mask, labels, odds) with shapes:
      (N, T, F), (N, T), (N, T, F), (N, T), (N,), (N, 3)
    """
    from football_betting.predict.catboost_model import OUTCOME_TO_INT

    form_local = form  # caller must pass a fresh / reset tracker
    pi_local = pi

    builder = SequenceBuilder(form=form_local, pi=pi_local, window_t=window_t)
    matches_sorted = sorted(matches, key=lambda m: m.date)

    h_seqs: list[np.ndarray] = []
    h_masks: list[np.ndarray] = []
    a_seqs: list[np.ndarray] = []
    a_masks: list[np.ndarray] = []
    labels: list[int] = []
    odds_rows: list[tuple[float, float, float]] = []

    for idx, m in enumerate(matches_sorted):
        if idx >= warmup_games:
            hs, hm, as_, am = builder.build_pair(m.home_team, m.away_team)
            h_seqs.append(hs)
            h_masks.append(hm)
            a_seqs.append(as_)
            a_masks.append(am)
            labels.append(OUTCOME_TO_INT[m.result])
            if m.odds:
                odds_rows.append((m.odds.home, m.odds.draw, m.odds.away))
            else:
                odds_rows.append((2.0, 3.5, 3.5))
        # update trackers AFTER feature extraction
        form_local.update(m)
        pi_local.update(m)

    return (
        np.asarray(h_seqs, dtype=np.float32),
        np.asarray(h_masks, dtype=np.float32),
        np.asarray(a_seqs, dtype=np.float32),
        np.asarray(a_masks, dtype=np.float32),
        np.asarray(labels, dtype=np.int64),
        np.asarray(odds_rows, dtype=np.float32),
    )


def fixture_tensors(
    home_team: str,
    away_team: str,
    form: FormTracker,
    pi: PiRatings,
    window_t: int = 10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Produce inference tensors for a single fixture."""
    builder = SequenceBuilder(form=form, pi=pi, window_t=window_t)
    return builder.build_pair(home_team, away_team)


__all__ = [
    "SEQ_FEATURE_NAMES",
    "N_SEQ_FEATURES",
    "SequenceBuilder",
    "build_dataset",
    "fixture_tensors",
]
