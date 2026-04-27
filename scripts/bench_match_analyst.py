"""Benchmark Nomen's match-article generator against today's predictions.

Loads the current snapshot, generates an article for each predicted fixture,
then scores each article on five criteria:

  1. both_teams    — both home and away team names appear in the text
  2. prob_ref      — a percentage figure (e.g. "47%") is mentioned
  3. form_ref      — at least one form letter (W/D/L) appears
  4. news_ref      — at least one news headline word is recycled (if news was fetched)
  5. length_ok     — prose is between 100 and 500 characters

Value-bet articles get a bonus check:
  6. value_signal  — words like "value", "edge", or "opportunity" appear

Usage
-----
    python scripts/bench_match_analyst.py [--lang en] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

# Allow running from the repo root without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_betting.api.schemas import MatchContext, MatchNewsItem, OddsOut
from football_betting.support.match_analyst import generate_article


# ── Scoring helpers ────────────────────────────────────────────────────────────

def _score_article(article: str, ctx: MatchContext) -> dict:
    text_lower = article.lower()

    both_teams = (
        ctx.home_team.split()[0].lower() in text_lower
        and ctx.away_team.split()[0].lower() in text_lower
    )
    prob_ref = bool(re.search(r"\d{1,3}\s*%", article))
    form_ref = bool(re.search(r"\b[WDL]{2,5}\b", article))

    news_ref = False
    if ctx.news:
        for item in ctx.news:
            first_word = item.title.split()[0].lower() if item.title.split() else ""
            if len(first_word) > 3 and first_word in text_lower:
                news_ref = True
                break
    else:
        news_ref = None  # type: ignore[assignment]  # N/A — no news available

    length_ok = 100 <= len(article) <= 500

    value_signal = None
    if ctx.value_bet:
        value_signal = any(
            kw in text_lower for kw in ("value", "edge", "opportunit", "advantage")
        )

    score = sum(
        1 for v in [both_teams, prob_ref, form_ref, news_ref, length_ok, value_signal]
        if v is True
    )
    possible = sum(
        1 for v in [both_teams, prob_ref, form_ref, news_ref, length_ok, value_signal]
        if v is not None
    )

    return {
        "both_teams": both_teams,
        "prob_ref": prob_ref,
        "form_ref": form_ref,
        "news_ref": news_ref,
        "length_ok": length_ok,
        "value_signal": value_signal,
        "score": score,
        "possible": possible,
    }


def _fmt_check(v: bool | None) -> str:
    if v is None:
        return "n/a"
    return "✓" if v else "✗"


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Nomen match analyst")
    parser.add_argument("--lang", default="en", help="Language code (en/de/es/fr/it)")
    parser.add_argument("--verbose", action="store_true", help="Print full articles")
    parser.add_argument(
        "--snapshot",
        default=None,
        help="Path to a snapshot JSON file (default: data/snapshots/today.json)",
    )
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot) if args.snapshot else (
        Path(__file__).parent.parent / "data" / "snapshots" / "today.json"
    )
    if not snapshot_path.exists():
        print(f"[bench] snapshot not found: {snapshot_path}", file=sys.stderr)
        print("[bench] Run 'fb snapshot' first to generate today.json", file=sys.stderr)
        sys.exit(1)

    with snapshot_path.open(encoding="utf-8") as f:
        raw = json.load(f)

    predictions = raw.get("predictions", [])
    value_bets_raw = raw.get("value_bets", [])
    value_pairs = {
        (vb["home_team"].lower(), vb["away_team"].lower()) for vb in value_bets_raw
    }

    if not predictions:
        print("[bench] No predictions in snapshot — nothing to benchmark.")
        sys.exit(0)

    print(f"[bench] Benchmarking Nomen on {len(predictions)} fixture(s)  lang={args.lang}")
    print("=" * 72)

    total_score = 0
    total_possible = 0
    failures = 0

    for pred in predictions:
        home = pred["home_team"]
        away = pred["away_team"]
        label = f"{home} vs {away}"

        ctx = MatchContext(
            home_team=home,
            away_team=away,
            league=pred.get("league", "?"),
            league_name=pred.get("league_name", "?"),
            kickoff_time=pred.get("kickoff_time"),
            prob_home=pred.get("prob_home", 0.0),
            prob_draw=pred.get("prob_draw", 0.0),
            prob_away=pred.get("prob_away", 0.0),
            most_likely=pred.get("most_likely", "H"),
            odds=OddsOut(**pred["odds"]) if pred.get("odds") else None,
            form_home=None,
            form_away=None,
            value_bet=(home.lower(), away.lower()) in value_pairs,
            news=[],
        )

        t0 = time.perf_counter()
        article = generate_article(ctx, lang=args.lang)
        elapsed = time.perf_counter() - t0

        if article is None:
            print(f"  FAIL  {label}  (no article — Ollama unreachable?)")
            failures += 1
            continue

        scores = _score_article(article, ctx)
        total_score += scores["score"]
        total_possible += scores["possible"]

        pct = int(scores["score"] / scores["possible"] * 100) if scores["possible"] else 0
        print(
            f"  [{pct:3d}%]  {label}  ({elapsed:.1f}s)"
        )
        print(
            f"         teams={_fmt_check(scores['both_teams'])}"
            f"  probs={_fmt_check(scores['prob_ref'])}"
            f"  form={_fmt_check(scores['form_ref'])}"
            f"  news={_fmt_check(scores['news_ref'])}"
            f"  length={_fmt_check(scores['length_ok'])}"
            + (f"  value={_fmt_check(scores['value_signal'])}" if scores["value_signal"] is not None else "")
        )

        if args.verbose:
            print()
            print("  " + article.replace("\n", "\n  "))
            print()

    print("=" * 72)
    if total_possible > 0:
        overall = int(total_score / total_possible * 100)
        print(
            f"[bench] Overall score: {total_score}/{total_possible} ({overall}%)  |"
            f"  failures={failures}/{len(predictions)}"
        )
    else:
        print(f"[bench] All {failures} fixture(s) failed — Ollama may not be running.")


if __name__ == "__main__":
    main()
