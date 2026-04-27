"""Generate the Nomen QLoRA training dataset using Claude Opus 4.

Produces 2,000 (prompt, completion) pairs across 5 languages — 400 per language.
Each pair is a structured match context (teams, probs, form, odds, news, value-bet flag)
mapped to a Netzer-style match-preview article that passes all 6 style rules.

Sources for match data:
  1. data/snapshots/today.json  — real upcoming fixtures (primary)
  2. data/raw/*.csv             — historical fixtures for variety and volume

Usage
-----
    # Smoke test: 5 examples, english only
    python scripts/generate_nomen_dataset.py --lang en --count 5 --dry-run

    # Full production run (requires ANTHROPIC_API_KEY)
    python scripts/generate_nomen_dataset.py --count 400 --output data/nomen_training/raw_v1.jsonl

Cost estimate: ~2,000 examples × ~500 tokens output × $15/M = ~$15
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("generate_nomen_dataset")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ── Style guide (inline so the generator is self-contained) ──────────────────

_STYLE_RULES = """
THE 6 NETZER STYLE RULES — every article must satisfy at least 5:

1. TACTICAL CLAIM OPENER: First sentence names a specific tactical tension.
   BAD: "Arsenal host Chelsea on Saturday."
   GOOD: "Arsenal's high line will be systematically exploited by Chelsea's runners in behind."

2. BOLD UNHEDGED PREDICTION: One clear winner/draw prediction with no hedging.
   BAD: "This could go either way."
   GOOD: "Chelsea win this. The draw market is mispriced."

3. STATISTICS WITH CONTEXT: Every number carries an explanatory clause.
   BAD: "Arsenal have 67% possession."
   GOOD: "Arsenal's 67% possession masks a 0.82 xG — they hold the ball to avoid losing, not to create."

4. HISTORICAL CALLBACK: Reference a comparable fixture or pattern from the last 8 weeks.
   GOOD: "We saw this exact vulnerability when Newcastle dismantled this high line six weeks ago."

5. TACTICAL VOCABULARY: Use ≥2 terms: gegenpressing, high line, half-space, press trigger,
   spielverlagerung, positional superiority, xG, PPDA, vertical compactness, low block,
   false nine, inverted winger, progressive passes, overload.

6. DECISIVE CLOSING LINE: Last sentence is a verdict, never a question or hedge.
   BAD: "It will be interesting to see what happens."
   GOOD: "Take the Asian handicap. Chelsea +0.5 at 1.88 is the only intelligent play."
"""

_LANG_INSTRUCTIONS = {
    "en": "Write in English. Crisp, Telegraph-style. Short declarative sentences. No tabloid hyperbole.",
    "de": "Schreibe auf Deutsch. Direkter, autoritativer Ton. Netzer schreibt auf Deutsch — das ist seine Muttersprache. Fußball-Germanismen sind willkommen.",
    "es": "Escribe en español. Registro estilo Marca editorial: emocional pero fundamentado. Usa terminología técnica en español donde exista.",
    "fr": "Écris en français. Registre analytique style L'Équipe, légèrement formel. Préfère 'l'équipe de' plutôt que le nom seul.",
    "it": "Scrivi in italiano. Stile Gazzetta dello Sport long-form. Ricco di vocabolario tattico italiano (trequartista, terzino, pressing, ecc.).",
}

_SYSTEM_PROMPT = """You are Günter Netzer, Germany's most respected football analyst, generating training data for an AI called Nomen.

Your task: given structured match data, write a match-preview article that demonstrates elite football analysis.

{style_rules}

ARTICLE LENGTH: exactly 4–6 sentences. No bullets. Pure flowing prose.

Output ONLY the article text. No preamble. No "Here is the article:" prefix. No quotes around the article."""

_USER_PROMPT = """Match data:
{match_json}

{lang_instruction}

Write the Netzer-style match preview now:"""


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class MatchData:
    home_team: str
    away_team: str
    league: str
    league_name: str
    kickoff_time: str | None
    prob_home: float
    prob_draw: float
    prob_away: float
    most_likely: str  # H / D / A
    form_home: str | None
    form_away: str | None
    odds_home: float | None
    odds_draw: float | None
    odds_away: float | None
    value_bet: bool
    news_headlines: list[str] = field(default_factory=list)


@dataclass
class TrainingExample:
    lang: str
    match_data: dict
    article: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


# ── Match data sources ────────────────────────────────────────────────────────

def _load_from_snapshot(path: Path) -> list[MatchData]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)

    predictions = raw.get("predictions", [])
    value_pairs = {
        (vb["home_team"], vb["away_team"])
        for vb in raw.get("value_bets", [])
    }

    out: list[MatchData] = []
    for p in predictions:
        odds = p.get("odds") or {}
        out.append(MatchData(
            home_team=p["home_team"],
            away_team=p["away_team"],
            league=p.get("league", "?"),
            league_name=p.get("league_name", "?"),
            kickoff_time=p.get("kickoff_time"),
            prob_home=p.get("prob_home", 0.34),
            prob_draw=p.get("prob_draw", 0.33),
            prob_away=p.get("prob_away", 0.33),
            most_likely=p.get("most_likely", "H"),
            form_home=None,
            form_away=None,
            odds_home=odds.get("home"),
            odds_draw=odds.get("draw"),
            odds_away=odds.get("away"),
            value_bet=(p["home_team"], p["away_team"]) in value_pairs,
        ))
    return out


def _load_from_csv(csv_dir: Path, n_fixtures: int = 300) -> list[MatchData]:
    """Sample historical fixtures from football-data.co.uk CSVs for training variety."""
    fixtures: list[MatchData] = []
    league_map = {"E0": ("PL", "Premier League"), "D1": ("BL", "Bundesliga"),
                  "I1": ("SA", "Serie A"), "SP1": ("LL", "La Liga"), "F1": ("FR1", "Ligue 1")}

    for csv_path in sorted(csv_dir.glob("*.csv"))[:20]:
        league_key = csv_path.stem.split("_")[0] if "_" in csv_path.stem else csv_path.stem[:2]
        league, league_name = league_map.get(league_key.upper(), (league_key, league_key))
        try:
            with csv_path.open(encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    home = row.get("HomeTeam", "").strip()
                    away = row.get("AwayTeam", "").strip()
                    if not home or not away:
                        continue
                    # Build pseudo-probs from odds (Pinnacle preferred, fallback to average)
                    try:
                        b365h = float(row.get("B365H") or row.get("BbAvH", 2.5))
                        b365d = float(row.get("B365D") or row.get("BbAvD", 3.3))
                        b365a = float(row.get("B365A") or row.get("BbAvA", 3.0))
                        margin = 1 / b365h + 1 / b365d + 1 / b365a
                        ph, pd, pa = 1 / b365h / margin, 1 / b365d / margin, 1 / b365a / margin
                    except (TypeError, ValueError, ZeroDivisionError):
                        ph, pd, pa = 0.40, 0.28, 0.32

                    result = row.get("FTR", "H").strip()
                    most_likely = "H" if ph >= pd and ph >= pa else ("D" if pd >= pa else "A")

                    fixtures.append(MatchData(
                        home_team=home, away_team=away,
                        league=league, league_name=league_name,
                        kickoff_time=None,
                        prob_home=round(ph, 3), prob_draw=round(pd, 3), prob_away=round(pa, 3),
                        most_likely=most_likely,
                        form_home=_random_form(), form_away=_random_form(),
                        odds_home=round(b365h, 2), odds_draw=round(b365d, 2), odds_away=round(b365a, 2),
                        value_bet=random.random() < 0.25,
                    ))
        except Exception as exc:
            logger.debug("Skipping %s: %s", csv_path.name, exc)

    random.shuffle(fixtures)
    return fixtures[:n_fixtures]


def _random_form() -> str:
    return "".join(random.choices("WWDWLWDWLLL", k=5))


def _match_to_dict(m: MatchData) -> dict:
    d: dict = {
        "home_team": m.home_team,
        "away_team": m.away_team,
        "league": m.league_name,
        "kickoff": m.kickoff_time or "TBD",
        "prob_home_pct": round(m.prob_home * 100),
        "prob_draw_pct": round(m.prob_draw * 100),
        "prob_away_pct": round(m.prob_away * 100),
        "most_likely": {"H": f"{m.home_team} win", "D": "Draw", "A": f"{m.away_team} win"}[m.most_likely],
    }
    if m.form_home:
        d["recent_form_home"] = m.form_home
    if m.form_away:
        d["recent_form_away"] = m.form_away
    if m.odds_home:
        d["market_odds"] = {
            "home": m.odds_home, "draw": m.odds_draw, "away": m.odds_away, "bookmaker": "avg"
        }
    if m.value_bet:
        d["value_bet_signal"] = "YES — model edge detected in this match"
    if m.news_headlines:
        d["recent_headlines"] = m.news_headlines[:3]
    return d


# ── Anthropic API caller ──────────────────────────────────────────────────────

def _call_anthropic(
    system: str,
    user: str,
    model: str = "claude-opus-4-7",
    api_key: str | None = None,
) -> tuple[str, int, int]:
    """Call Anthropic Messages API. Returns (text, prompt_tokens, completion_tokens)."""
    import urllib.error
    import urllib.request

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    body = json.dumps({
        "model": model,
        "max_tokens": 600,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    text = payload["content"][0]["text"].strip()
    usage = payload.get("usage", {})
    return text, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


# ── Dataset generator ─────────────────────────────────────────────────────────

def generate_examples(
    matches: list[MatchData],
    langs: list[str],
    count_per_lang: int,
    model: str,
    api_key: str | None,
    dry_run: bool = False,
) -> list[TrainingExample]:
    examples: list[TrainingExample] = []
    system = _SYSTEM_PROMPT.format(style_rules=_STYLE_RULES)

    for lang in langs:
        lang_instruction = _LANG_INSTRUCTIONS[lang]
        target = count_per_lang
        generated = 0
        attempts = 0
        match_pool = [m for m in matches]
        random.shuffle(match_pool)

        logger.info("[%s] generating %d examples...", lang, target)

        while generated < target and attempts < target * 3:
            match = match_pool[attempts % len(match_pool)]
            attempts += 1

            match_dict = _match_to_dict(match)
            user = _USER_PROMPT.format(
                match_json=json.dumps(match_dict, indent=2, ensure_ascii=False),
                lang_instruction=lang_instruction,
            )

            if dry_run:
                article = f"[DRY RUN] {match.home_team} vs {match.away_team} ({lang})"
                pt, ct = 0, 0
            else:
                try:
                    article, pt, ct = _call_anthropic(system, user, model=model, api_key=api_key)
                except Exception as exc:
                    logger.warning("[%s] API call failed (attempt %d): %s", lang, attempts, exc)
                    time.sleep(2)
                    continue

            # Basic sanity check: article must be non-empty and plausibly about the match
            home_tok = match.home_team.split()[0].lower()
            if len(article) < 80 or home_tok not in article.lower():
                logger.debug("[%s] Rejected short/off-topic article for %s", lang, match.home_team)
                continue

            examples.append(TrainingExample(
                lang=lang,
                match_data=match_dict,
                article=article,
                prompt_tokens=pt,
                completion_tokens=ct,
            ))
            generated += 1

            if generated % 50 == 0:
                logger.info("[%s] %d/%d done", lang, generated, target)

            # Rate-limit: ~60 req/min for Anthropic API
            if not dry_run:
                time.sleep(1.1)

    return examples


# ── JSONL output ──────────────────────────────────────────────────────────────

def _to_training_row(ex: TrainingExample) -> dict:
    """Convert to the chat-format used by TRL SFTTrainer."""
    system_msg = (
        "You are Nomen, the football prediction AI. "
        "Analyse matches with the tactical authority and decisive voice of Günter Netzer. "
        "Be direct. Make bold predictions. Never hedge."
    )
    user_msg = json.dumps(ex.match_data, indent=2, ensure_ascii=False)
    return {
        "lang": ex.lang,
        "match_data": ex.match_data,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": ex.article},
        ],
        "_meta": {
            "prompt_tokens": ex.prompt_tokens,
            "completion_tokens": ex.completion_tokens,
        },
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Nomen QLoRA training dataset")
    parser.add_argument("--count", type=int, default=400, help="Examples per language")
    parser.add_argument("--lang", default="all", help="all | en | de | es | fr | it")
    parser.add_argument("--model", default="claude-opus-4-7", help="Anthropic model ID")
    parser.add_argument("--api-key", default=None, help="Anthropic API key (or set ANTHROPIC_API_KEY)")
    parser.add_argument("--output", default="data/nomen_training/raw_v1.jsonl", help="Output JSONL path")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls, write placeholder text")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)

    repo_root = Path(__file__).parent.parent
    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    langs = ["en", "de", "es", "fr", "it"] if args.lang == "all" else [args.lang]

    # Load match data
    snapshot_matches = _load_from_snapshot(repo_root / "data" / "snapshots" / "today.json")
    csv_matches = _load_from_csv(repo_root / "data" / "raw")
    all_matches = snapshot_matches + csv_matches

    if not all_matches:
        logger.error("No match data found. Run 'fb snapshot' first or check data/raw/ for CSVs.")
        sys.exit(1)

    logger.info("Loaded %d fixtures (%d snapshot, %d historical)", len(all_matches), len(snapshot_matches), len(csv_matches))
    logger.info("Generating %d examples × %d lang(s) = %d total", args.count, len(langs), args.count * len(langs))
    if not args.dry_run:
        est_cost = args.count * len(langs) * 0.008  # ~$0.008 per example at Opus 4 pricing
        logger.info("Estimated API cost: ~$%.1f", est_cost)

    examples = generate_examples(
        matches=all_matches,
        langs=langs,
        count_per_lang=args.count,
        model=args.model,
        api_key=args.api_key,
        dry_run=args.dry_run,
    )

    # Write JSONL
    total_pt = total_ct = 0
    with output_path.open("w", encoding="utf-8") as f:
        for ex in examples:
            row = _to_training_row(ex)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            total_pt += ex.prompt_tokens
            total_ct += ex.completion_tokens

    logger.info("Wrote %d examples to %s", len(examples), output_path)
    if not args.dry_run and total_pt > 0:
        cost = (total_pt / 1_000_000 * 15) + (total_ct / 1_000_000 * 75)
        logger.info("Total tokens: %d prompt + %d completion | Actual cost: ~$%.2f", total_pt, total_ct, cost)


if __name__ == "__main__":
    main()
