"""Sequence feature builder — shapes, padding, leakage-safety."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from football_betting.data.models import Match, MatchOdds
from football_betting.features.form import FormTracker
from football_betting.predict.sequence_features import (
    N_SEQ_FEATURES,
    SequenceBuilder,
    build_dataset,
    fixture_tensors,
)
from football_betting.rating.pi_ratings import PiRatings


def _mk_match(day: int, home: str, away: str, hg: int, ag: int) -> Match:
    return Match(
        date=date(2024, 1, 1) + timedelta(days=day),
        league="BL",
        season="2023-24",
        home_team=home,
        away_team=away,
        home_goals=hg,
        away_goals=ag,
        odds=MatchOdds(home=2.0, draw=3.5, away=4.0),
    )


def test_sequence_shape_and_padding():
    form = FormTracker()
    pi = PiRatings()
    builder = SequenceBuilder(form=form, pi=pi, window_t=10)
    # No history → all padding
    seq, mask = builder.build_team_sequence("A")
    assert seq.shape == (10, N_SEQ_FEATURES)
    assert mask.shape == (10,)
    assert mask.sum() == 0.0


def test_sequence_fills_from_newest_position():
    form = FormTracker()
    pi = PiRatings()
    for i in range(3):
        m = _mk_match(i, "A", "B", 2, 1)
        form.update(m)
        pi.update(m)
    builder = SequenceBuilder(form=form, pi=pi, window_t=10)
    seq, mask = builder.build_team_sequence("A")
    assert mask[:7].sum() == 0.0       # padded at front
    assert mask[7:].sum() == 3.0        # 3 recent games at end


def test_build_dataset_chronological():
    pi = PiRatings()
    form = FormTracker()
    matches = [_mk_match(i, "A", "B", i % 3, (i + 1) % 3) for i in range(150)]
    h, hm, a, am, y, odds = build_dataset(
        matches, form, pi, window_t=10, warmup_games=100
    )
    assert len(y) == 50
    assert h.shape == (50, 10, N_SEQ_FEATURES)
    assert hm.shape == (50, 10)
    assert a.shape == (50, 10, N_SEQ_FEATURES)
    assert am.shape == (50, 10)
    assert odds.shape == (50, 3)
    assert y.dtype == np.int64


def test_fixture_tensors_shape():
    form = FormTracker()
    pi = PiRatings()
    hs, hm, as_, am = fixture_tensors("A", "B", form, pi, window_t=10)
    assert hs.shape == (10, N_SEQ_FEATURES)
    assert hm.shape == (10,)
    assert as_.shape == (10, N_SEQ_FEATURES)
    assert am.shape == (10,)
