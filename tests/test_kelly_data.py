"""Phase A of _plans/gpu_kelly_training_plan.md — opening-odds + Kelly-mask.

Covers :func:`collect_opening_odds_and_mask` and :func:`coverage` in
``football_betting.predict.kelly_data``.

The key invariants under test:
    1. Walk order matches ``sorted(matches, key=lambda m: m.date)``.
    2. ``warmup_games`` entries are skipped — N = max(0, len − warmup).
    3. Missing ``opening_odds`` → row NaN + mask False.
    4. Any opening odd ≤ 1.0 (degenerate Kelly ``b ≤ 0``) → mask False.
    5. All three opening odds > 1.0 → mask True, opening preserved.
    6. Row alignment with :func:`build_dataset` labels (regression test).
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from football_betting.data.models import Match, MatchOdds
from football_betting.features.form import FormTracker
from football_betting.predict.kelly_data import (
    collect_opening_odds_and_mask,
    coverage,
)
from football_betting.predict.sequence_features import build_dataset
from football_betting.rating.pi_ratings import PiRatings


def _mk_match(
    day: int,
    home: str,
    away: str,
    hg: int,
    ag: int,
    *,
    closing: MatchOdds | None = None,
    opening: MatchOdds | None = None,
) -> Match:
    return Match(
        date=date(2024, 1, 1) + timedelta(days=day),
        league="BL",
        season="2023-24",
        home_team=home,
        away_team=away,
        home_goals=hg,
        away_goals=ag,
        odds=closing or MatchOdds(home=2.0, draw=3.5, away=4.0),
        opening_odds=opening,
    )


def test_returns_empty_shapes_when_matches_shorter_than_warmup() -> None:
    matches = [_mk_match(i, "A", "B", 1, 0) for i in range(3)]
    opening, mask = collect_opening_odds_and_mask(matches, warmup_games=100)
    assert opening.shape == (0, 3)
    assert mask.shape == (0,)
    assert opening.dtype == np.float32
    assert mask.dtype == bool
    assert coverage(mask) == 0.0


def test_missing_opening_odds_yields_nan_and_false_mask() -> None:
    matches = [_mk_match(i, "A", "B", 1, 0) for i in range(5)]  # opening=None
    opening, mask = collect_opening_odds_and_mask(matches, warmup_games=2)
    assert opening.shape == (3, 3)
    assert mask.shape == (3,)
    assert np.isnan(opening).all()
    assert mask.sum() == 0
    assert coverage(mask) == 0.0


def test_all_valid_opening_odds_yield_true_mask() -> None:
    op = MatchOdds(home=2.5, draw=3.2, away=2.9)
    matches = [_mk_match(i, "A", "B", 1, 0, opening=op) for i in range(5)]
    opening, mask = collect_opening_odds_and_mask(matches, warmup_games=2)
    assert opening.shape == (3, 3)
    assert np.allclose(opening, [[2.5, 3.2, 2.9]] * 3)
    assert mask.all()
    assert coverage(mask) == pytest.approx(1.0)


def test_degenerate_opening_odds_marked_false_but_kept_numeric() -> None:
    # ``MatchOdds`` enforces ``odds > 1`` via Pydantic, so degenerate triples
    # cannot come from regular construction. ``model_construct`` skips
    # validation and simulates a hypothetical upstream regression (e.g.
    # truncation to exactly 1.0). The mask must still reject the row so the
    # Kelly gradient never divides by zero via ``b = odds − 1``.
    bad = MatchOdds.model_construct(home=2.5, draw=1.0, away=3.0)
    good = MatchOdds(home=2.1, draw=3.3, away=3.0)
    matches = [
        _mk_match(0, "A", "B", 1, 0, opening=bad),
        _mk_match(1, "A", "B", 1, 0, opening=good),
        _mk_match(2, "A", "B", 1, 0, opening=None),
    ]
    opening, mask = collect_opening_odds_and_mask(matches, warmup_games=0)
    assert mask.tolist() == [False, True, False]
    # First row numeric but flagged, second all-valid, third NaN
    assert not np.isnan(opening[0]).any()
    assert not np.isnan(opening[1]).any()
    assert np.isnan(opening[2]).all()
    assert coverage(mask) == pytest.approx(1.0 / 3.0)


def test_walk_order_is_chronological_not_insertion_order() -> None:
    op = MatchOdds(home=2.0, draw=3.5, away=4.0)
    # Insertion order reversed so the unsorted walk would yield the wrong row.
    matches = [
        _mk_match(5, "A", "B", 1, 0, opening=op),
        _mk_match(2, "A", "B", 1, 0, opening=None),
        _mk_match(8, "A", "B", 1, 0, opening=op),
    ]
    opening, mask = collect_opening_odds_and_mask(matches, warmup_games=1)
    # After sort: days [2, 5, 8]. warmup skips day 2. Rows should map to
    # days 5 (has opening → True) and 8 (has opening → True).
    assert mask.tolist() == [True, True]
    assert np.allclose(opening, [[2.0, 3.5, 4.0], [2.0, 3.5, 4.0]])


def test_row_alignment_with_build_dataset() -> None:
    """Row i of ``opening`` must describe the same match as row i of
    ``build_dataset``'s labels/odds output — otherwise the Kelly gradient
    applies to the wrong outcome."""
    op = MatchOdds(home=2.5, draw=3.5, away=3.0)
    # Half the matches get opening odds, rest don't.
    matches = [
        _mk_match(
            i,
            "A",
            "B",
            (i % 3),
            ((i + 1) % 3),
            opening=op if i % 2 == 0 else None,
        )
        for i in range(150)
    ]
    opening, mask = collect_opening_odds_and_mask(matches, warmup_games=100)

    form = FormTracker()
    pi = PiRatings()
    h, hm, a, am, y, closing = build_dataset(matches, form, pi, window_t=10, warmup_games=100)

    assert opening.shape[0] == closing.shape[0] == y.shape[0] == 50
    # Closing odds are populated for every row (placeholder fallback), opening
    # only where source match had opening_odds. Every True in mask must
    # correspond to a row whose opening triple is fully numeric.
    assert mask.sum() > 0
    assert mask.sum() < mask.shape[0]
    for i in range(mask.shape[0]):
        if mask[i]:
            assert not np.isnan(opening[i]).any()
        else:
            # Either NaN (no opening_odds) or flagged-degenerate. In this
            # test setup we only use the NaN branch.
            assert np.isnan(opening[i]).any()


def test_coverage_helper_matches_mask_mean() -> None:
    mask = np.array([True, False, True, True, False])
    assert coverage(mask) == pytest.approx(0.6)
    assert coverage(np.array([], dtype=bool)) == 0.0
