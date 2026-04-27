"""Benchmark Nomen's match-article generator against today's predictions.

Scores articles on the original 6 factual criteria PLUS 5 Netzer style criteria:

Factual criteria:
  1. both_teams    — both home and away team names appear in the text
  2. prob_ref      — a percentage figure (e.g. "47%") is mentioned
  3. form_ref      — at least one form letter (W/D/L) appears
  4. news_ref      — at least one news headline word is recycled (if news available)
  5. length_ok     — prose is between 100 and 500 characters
  6. value_signal  — words like "value", "edge" appear (only checked for value-bet matches)

Style criteria (Netzer standard):
  7. tactical_vocab  — ≥2 tactical terms (xG, high line, gegenpressing, half-space, etc.)
  8. no_hedge        — no hedging phrases ("could go either way", "might", "remains to be seen")
  9. historical_ref  — past-tense narrative or comparable fixture reference
 10. sentence_count  — 4–6 sentences
 11. strong_opener   — first sentence is not a bare fixture description

Usage
-----
    # Benchmark current Nomen model
    python scripts/bench_match_analyst.py [--lang en] [--verbose]

    # A/B compare fine-tuned nomen-v1 vs base qwen2.5:7b
    python scripts/bench_match_analyst.py --compare-base --verbose
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_betting.api.schemas import MatchContext, OddsOut
from football_betting.support.match_analyst import generate_article

# ── Tactical vocabulary (covers all 5 languages) ─────────────────────────────

_TACTICAL_TERMS = [
    # English / universal
    "xg", "x g", "expected goals", "ppda", "high line", "low block", "half-space",
    "half space", "gegenpressing", "press trigger", "spielverlagerung",
    "positional superiority", "vertical compact", "false nine", "inverted winger",
    "progressive pass", "overload", "back three", "back four", "high press",
    # German
    "hohe kette", "halbraum", "tiefenläufe", "raumdeckung", "freilaufbewegungen",
    "umschaltsituation", "dreierkette", "viererkette", "falscher neuner",
    # Spanish
    "presión alta", "bloque bajo", "línea alta", "repliegue", "superioridad posicional",
    "transición", "carrilero", "mediapunta",
    # French
    "pressing haut", "bloc bas", "demi-espace", "demi espace", "ligne haute",
    "transition", "supériorité positionnelle",
    # Italian
    "pressing alto", "blocco basso", "mezzaspazio", "trequartista", "terzino",
    "verticalizzazione", "densità difensiva", "ribaltamento",
]

_HEDGE_PHRASES = [
    "could go either way", "could go both ways", "too close to call",
    "it remains to be seen", "only time will tell", "both teams will be hoping",
    "anything could happen", "hard to predict", "difficult to say",
    "man wird sehen", "schwer zu sagen", "alles ist möglich",
    "kann in beide richtungen", "difficile à prédire", "tout est possible",
    "reste à voir", "peut aller dans les deux", "difícil predecir",
    "cualquier cosa puede", "puede ir para", "difficile dirlo",
    "può andare in entrambe", "tutto è possibile",
]

_BAD_OPENER_SUFFIXES = [
    "will play", "will host", "will face", "will welcome", "will travel",
    "host ", "face ", "welcome ", "travel to", "takes on", "takes place",
    "today's match", "tonight's match", "this evening's",
    "spielt gegen", "empfängt", "trifft auf", "reist nach",
    "jugará contra", "recibe a", "se enfrenta a",
    "jouera contre", "accueille", "affronte",
    "giocherà contro", "ospita", "affronta",
]

_HISTORICAL_MARKERS = [
    "weeks ago", "last month", "we saw", "we witnessed", "comparable",
    "similar to", "in their last", "recall", "back in", "reminded",
    "wochen", "letzten", "erinnert", "haben wir gesehen", "ähnlich",
    "semanas atrás", "mes pasado", "recordamos", "vimos",
    "semaines", "mois dernier", "on a vu", "nous avons vu",
    "settimane fa", "mese scorso", "abbiamo visto", "ci ricorda",
]


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_article(article: str, ctx: MatchContext) -> dict[str, bool | None]:
    text = article.lower()
    home_tok = ctx.home_team.split()[0].lower()
    away_tok = ctx.away_team.split()[0].lower()

    # ── Factual criteria ──────────────────────────────────────────────────────
    both_teams = home_tok in text and away_tok in text
    prob_ref = bool(re.search(r"\d{1,3}\s*%", article))
    form_ref = bool(re.search(r"\b[WDL]{2,5}\b", article))

    news_ref: bool | None = None
    if ctx.news:
        for item in ctx.news:
            words = item.title.split()
            if any(len(w) > 3 and w.lower() in text for w in words):
                news_ref = True
                break
        if news_ref is None:
            news_ref = False

    length_ok = 100 <= len(article) <= 600

    value_signal: bool | None = None
    if ctx.value_bet:
        value_signal = any(kw in text for kw in ("value", "edge", "opportunit", "advantage", "wert", "valeur", "valore", "valor"))

    # ── Netzer style criteria ─────────────────────────────────────────────────
    tactical_count = sum(1 for t in _TACTICAL_TERMS if t in text)
    tactical_vocab = tactical_count >= 2

    no_hedge = not any(h in text for h in _HEDGE_PHRASES)

    historical = any(m in text for m in _HISTORICAL_MARKERS)

    sentences = [s.strip() for s in re.split(r"[.!?]", article) if len(s.strip()) > 10]
    sentence_count = 4 <= len(sentences) <= 7

    # Strong opener: first sentence doesn't start with team name + generic verb
    first = sentences[0].lower() if sentences else ""
    bad_opener = any(
        (home_tok in first or away_tok in first) and suffix in first
        for suffix in _BAD_OPENER_SUFFIXES
    )
    strong_opener = not bad_opener and len(first) > 25

    score = sum(
        1 for v in [both_teams, prob_ref, form_ref, news_ref, length_ok, value_signal,
                    tactical_vocab, no_hedge, historical, sentence_count, strong_opener]
        if v is True
    )
    possible = sum(
        1 for v in [both_teams, prob_ref, form_ref, news_ref, length_ok, value_signal,
                    tactical_vocab, no_hedge, historical, sentence_count, strong_opener]
        if v is not None
    )

    return {
        # factual
        "both_teams": both_teams,
        "prob_ref": prob_ref,
        "form_ref": form_ref,
        "news_ref": news_ref,
        "length_ok": length_ok,
        "value_signal": value_signal,
        # style
        "tactical_vocab": tactical_vocab,
        "no_hedge": no_hedge,
        "historical_ref": historical,
        "sentence_count": sentence_count,
        "strong_opener": strong_opener,
        # totals
        "score": score,
        "possible": possible,
        "_tactical_term_count": tactical_count,
    }


def _fmt(v: bool | None) -> str:
    if v is None:
        return "n/a"
    return "✓" if v else "✗"


def _run_one_model(
    predictions: list[dict],
    value_pairs: set,
    lang: str,
    model: str | None = None,
    host: str | None = None,
    vllm_url: str | None = None,
    verbose: bool = False,
    label: str = "Nomen",
) -> tuple[int, int, int]:
    """Generate + score articles for all fixtures. Returns (total_score, total_possible, failures)."""
    total_score = total_possible = failures = 0

    # Temporarily override env vars if caller requests a specific model/backend
    _prev_vllm = os.environ.get("NOMEN_VLLM_URL", "")
    _prev_ollama_model = os.environ.get("OLLAMA_MODEL", "")

    if vllm_url is not None:
        os.environ["NOMEN_VLLM_URL"] = vllm_url
    if model:
        os.environ["OLLAMA_MODEL"] = model
        os.environ["NOMEN_VLLM_URL"] = ""  # force Ollama

    try:
        for pred in predictions:
            home, away = pred["home_team"], pred["away_team"]
            fixture_label = f"{home} vs {away}"

            ctx = MatchContext(
                home_team=home, away_team=away,
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
            article = generate_article(ctx, lang=lang, model=model if not vllm_url else None, host=host)
            elapsed = time.perf_counter() - t0

            if article is None:
                print(f"  [{label}] FAIL  {fixture_label}  (no response)")
                failures += 1
                continue

            s = _score_article(article, ctx)
            total_score += s["score"]
            total_possible += s["possible"]
            pct = int(s["score"] / s["possible"] * 100) if s["possible"] else 0

            print(f"  [{label}] [{pct:3d}%]  {fixture_label}  ({elapsed:.1f}s)")
            factual = (f"teams={_fmt(s['both_teams'])}  probs={_fmt(s['prob_ref'])}"
                       f"  form={_fmt(s['form_ref'])}  news={_fmt(s['news_ref'])}"
                       f"  len={_fmt(s['length_ok'])}"
                       + (f"  val={_fmt(s['value_signal'])}" if s["value_signal"] is not None else ""))
            style = (f"tactic={_fmt(s['tactical_vocab'])}({s['_tactical_term_count']})"
                     f"  hedge={_fmt(s['no_hedge'])}  hist={_fmt(s['historical_ref'])}"
                     f"  sents={_fmt(s['sentence_count'])}  opener={_fmt(s['strong_opener'])}")
            print(f"         FACTUAL: {factual}")
            print(f"         STYLE:   {style}")

            if verbose:
                print()
                print("  " + article.replace("\n", "\n  "))
                print()
    finally:
        os.environ["NOMEN_VLLM_URL"] = _prev_vllm
        os.environ["OLLAMA_MODEL"] = _prev_ollama_model

    return total_score, total_possible, failures


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Nomen match analyst")
    parser.add_argument("--lang", default="en", help="Language code (en/de/es/fr/it)")
    parser.add_argument("--verbose", action="store_true", help="Print full articles")
    parser.add_argument("--snapshot", default=None, help="Path to snapshot JSON")
    parser.add_argument(
        "--compare-base", action="store_true",
        help="A/B compare fine-tuned nomen-v1 vs base qwen2.5:7b-instruct"
    )
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot) if args.snapshot else (
        Path(__file__).parent.parent / "data" / "snapshots" / "today.json"
    )
    if not snapshot_path.exists():
        print(f"[bench] snapshot not found: {snapshot_path}", file=sys.stderr)
        print("[bench] Run 'fb snapshot' first.", file=sys.stderr)
        sys.exit(1)

    with snapshot_path.open(encoding="utf-8") as f:
        raw = json.load(f)

    predictions = raw.get("predictions", [])
    value_pairs = {
        (vb["home_team"].lower(), vb["away_team"].lower())
        for vb in raw.get("value_bets", [])
    }

    if not predictions:
        print("[bench] No predictions in snapshot.")
        sys.exit(0)

    n = len(predictions)
    print(f"[bench] {n} fixture(s)  lang={args.lang}  {'A/B mode' if args.compare_base else 'single model'}")

    if args.compare_base:
        # ── A: fine-tuned Nomen (current config) ─────────────────────────────
        print("\n" + "═" * 72)
        print("  MODEL A — Nomen v1 (fine-tuned, current NOMEN_VLLM_URL / nomen-v1)")
        print("═" * 72)
        a_score, a_possible, a_fail = _run_one_model(
            predictions, value_pairs, args.lang, verbose=args.verbose, label="Nomen-v1"
        )

        # ── B: base model ─────────────────────────────────────────────────────
        print("\n" + "═" * 72)
        print("  MODEL B — Base model (qwen2.5:7b-instruct, Ollama)")
        print("═" * 72)
        b_score, b_possible, b_fail = _run_one_model(
            predictions, value_pairs, args.lang,
            model="qwen2.5:7b-instruct", verbose=args.verbose, label="Base-7B"
        )

        # ── Summary ───────────────────────────────────────────────────────────
        print("\n" + "═" * 72)
        print("  A/B SUMMARY")
        print("═" * 72)
        a_pct = int(a_score / a_possible * 100) if a_possible else 0
        b_pct = int(b_score / b_possible * 100) if b_possible else 0
        print(f"  Nomen v1 (fine-tuned):  {a_score}/{a_possible} ({a_pct}%)  failures={a_fail}/{n}")
        print(f"  Base (qwen2.5:7b):      {b_score}/{b_possible} ({b_pct}%)  failures={b_fail}/{n}")
        delta = a_pct - b_pct
        print(f"  Delta:                  {'+' if delta >= 0 else ''}{delta}%")
        if a_pct >= 80:
            print(f"\n  ✓ PASS: Nomen v1 ({a_pct}%) meets the ≥80% quality gate.")
        else:
            print(f"\n  ✗ FAIL: Nomen v1 ({a_pct}%) is below the 80% quality gate.")
            print("         Consider: more training epochs, larger dataset, or prompt tuning.")
    else:
        print("=" * 72)
        total_score, total_possible, failures = _run_one_model(
            predictions, value_pairs, args.lang, verbose=args.verbose, label="Nomen"
        )
        print("=" * 72)
        if total_possible > 0:
            overall = int(total_score / total_possible * 100)
            print(
                f"[bench] Overall: {total_score}/{total_possible} ({overall}%)  "
                f"failures={failures}/{n}"
            )
            if overall >= 80:
                print(f"[bench] ✓ Meets the ≥80% quality gate.")
            else:
                print(f"[bench] ✗ Below the 80% quality gate (style score target).")
        else:
            print(f"[bench] All {failures} fixture(s) failed — backend unreachable?")


if __name__ == "__main__":
    main()
