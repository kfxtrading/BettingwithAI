"""SEO helpers for per-match prediction pages.

Builds:

* a stable slug per fixture/match (``home-vs-away-YYYY-MM-DD``);
* a list of upcoming match slugs (today's snapshot + optional league filter);
* a templated 150–300 word "wrapper" prose payload for the
  ``/leagues/{league}/{match}`` SEO page, gated to ``noindex`` when not
  available.

The wrapper is intentionally template-driven (no LLM) so it ships
deterministically and stays factual. It must only describe model output
and observable team facts — no betting advice.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from football_betting.api.schemas import PredictionOut, TodayPayload
from football_betting.config import LEAGUES


__all__ = [
    "MatchWrapper",
    "build_slug",
    "list_upcoming_slugs",
    "find_match_in_snapshot",
    "build_wrapper",
    "find_archived_match",
]


def _slugify(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE).strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def build_slug(home: str, away: str, day: date | str) -> str:
    """Return the canonical SEO slug for a match.

    Format: ``{home-slug}-vs-{away-slug}-{YYYY-MM-DD}``. Stable across
    re-runs; safe for use in URLs.
    """
    if isinstance(day, date):
        day_str = day.isoformat()
    else:
        day_str = str(day)[:10]
    return f"{_slugify(home)}-vs-{_slugify(away)}-{day_str}"


def list_upcoming_slugs(snapshot: TodayPayload, league: str | None = None) -> list[str]:
    """Return slugs for every prediction in the current snapshot."""
    slugs: list[str] = []
    seen: set[str] = set()
    for p in snapshot.predictions:
        if league and p.league.upper() != league.upper():
            continue
        slug = build_slug(p.home_team, p.away_team, p.date)
        if slug in seen:
            continue
        seen.add(slug)
        slugs.append(slug)
    return slugs


def find_match_in_snapshot(
    snapshot: TodayPayload, slug: str
) -> PredictionOut | None:
    """Look up a prediction by slug. Returns ``None`` when not found."""
    for p in snapshot.predictions:
        if build_slug(p.home_team, p.away_team, p.date) == slug:
            return p
    return None


@dataclass(slots=True)
class MatchWrapper:
    """Wire-shape for the SEO match prediction page."""

    slug: str
    league: str
    league_name: str
    home_team: str
    away_team: str
    kickoff: str  # ISO datetime or YYYY-MM-DD when no time known
    prob_home: float
    prob_draw: float
    prob_away: float
    pick: str  # 'H' | 'D' | 'A'
    prose: str
    is_archived: bool = False
    actual_result: str | None = None  # 'H' | 'D' | 'A'
    actual_score: str | None = None
    pick_correct: bool | None = None
    sofascore_event_id: int | None = None


def _kickoff_iso(p: PredictionOut) -> str:
    if p.kickoff_time:
        try:
            hh, mm = p.kickoff_time.split(":")[:2]
            return f"{p.date}T{int(hh):02d}:{int(mm):02d}:00"
        except ValueError:
            pass
    return p.date


def _pick_label(pick: str, home: str, away: str) -> str:
    if pick == "H":
        return f"{home} to win at home"
    if pick == "A":
        return f"{away} to win on the road"
    return "the draw"


def build_wrapper(p: PredictionOut, league_name: str | None = None) -> MatchWrapper:
    """Construct a deterministic wrapper payload from a prediction."""
    league_name = league_name or p.league_name or p.league
    pick = p.most_likely
    pick_pct = round(
        max(p.prob_home, p.prob_draw, p.prob_away) * 100,
    )
    home_pct = round(p.prob_home * 100)
    draw_pct = round(p.prob_draw * 100)
    away_pct = round(p.prob_away * 100)

    pick_phrase = _pick_label(pick, p.home_team, p.away_team)

    paragraphs = [
        (
            f"{p.home_team} host {p.away_team} in the {league_name} on "
            f"{p.date}. The {p.model_name} ensemble — Pi-Ratings, "
            "Dixon-Coles Poisson, CatBoost and an MLP head, calibrated "
            "with isotonic regression — leans towards "
            f"{pick_phrase} at {pick_pct}% probability."
        ),
        (
            f"Calibrated probabilities: home win {home_pct}%, draw {draw_pct}%, "
            f"away win {away_pct}%. These numbers are the model's best "
            "estimate after removing the bookmaker margin from the comparable "
            "1X2 market — they are not a guarantee."
        ),
        (
            "Match context is built from each side's rolling Pi-Ratings, "
            "last-10 form, expected-goals trend and head-to-head history. "
            "Where odds are available, the page also flags whether the "
            "model disagrees with the market by more than three percentage "
            "points — the threshold we use for value bets."
        ),
        (
            "Always treat probabilistic predictions as decision support, "
            "not a tip. Past model accuracy is no guarantee of future "
            "results; bet only what you can lose, and consult our "
            "responsible-gambling page if you need help."
        ),
    ]

    return MatchWrapper(
        slug=build_slug(p.home_team, p.away_team, p.date),
        league=p.league,
        league_name=league_name,
        home_team=p.home_team,
        away_team=p.away_team,
        kickoff=_kickoff_iso(p),
        prob_home=round(p.prob_home, 4),
        prob_draw=round(p.prob_draw, 4),
        prob_away=round(p.prob_away, 4),
        pick=pick,
        prose="\n\n".join(paragraphs),
        sofascore_event_id=getattr(p, "sofascore_event_id", None),
    )


def find_archived_match(slug: str) -> tuple[str, int, int] | None:
    """Best-effort lookup of a settled result for ``slug``.

    Returns ``(ftr, home_goals, away_goals)`` when the match is in
    ``data/raw/`` archives, else ``None``. Never raises.
    """
    try:
        from football_betting.evaluation.grader import _load_results_for_league
    except Exception:  # pragma: no cover - defensive import guard
        return None

    parts = slug.rsplit("-", 3)
    if len(parts) < 4:
        return None
    day_str = parts[-1]
    try:
        day = datetime.strptime(day_str, "%Y-%m-%d").date()
    except ValueError:
        return None

    body = "-".join(parts[:-1])  # "home-vs-away"
    if "-vs-" not in body:
        return None
    home_slug, away_slug = body.split("-vs-", 1)

    for league_key, cfg in LEAGUES.items():
        try:
            results = _load_results_for_league(cfg.code)
        except Exception:  # pragma: no cover
            continue
        for (d, home_norm, away_norm), payload in results.items():
            if d != day:
                continue
            if (
                _slugify(home_norm) == home_slug
                and _slugify(away_norm) == away_slug
            ):
                return payload
    return None


def attach_archive(wrapper: MatchWrapper) -> MatchWrapper:
    """If the match has been played, fill the archive fields."""
    archive = find_archived_match(wrapper.slug)
    if archive is None:
        return wrapper
    ftr, hg, ag = archive
    wrapper.is_archived = True
    wrapper.actual_result = ftr
    wrapper.actual_score = f"{hg}-{ag}"
    wrapper.pick_correct = wrapper.pick == ftr
    return wrapper


def collect_upcoming(snapshot: TodayPayload | None) -> Iterable[str]:
    if snapshot is None:
        return []
    return list_upcoming_slugs(snapshot)
