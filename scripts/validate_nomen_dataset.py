"""Validate and filter the Nomen QLoRA training dataset.

Scores each generated example against the 6 Netzer style rules using
regex + keyword heuristics. Examples scoring < 4/6 are rejected and
written to a separate file for human review.

Usage
-----
    python scripts/validate_nomen_dataset.py \
        --input  data/nomen_training/raw_v1.jsonl \
        --output data/nomen_training/dataset_v1.jsonl \
        --report
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── Tactical vocabulary (Rule 5) ──────────────────────────────────────────────

_TACTICAL_TERMS: dict[str, list[str]] = {
    "en": [
        "high line", "low block", "gegenpressing", "half-space", "half space",
        "press trigger", "spielverlagerung", "positional superiority",
        "vertical compact", "false nine", "inverted winger", "overload",
        "xg", "x g", "expected goals", "ppda", "progressive pass",
        "pressing intensity", "build-up", "build up", "counter-press",
        "back three", "back four", "back five", "high press",
    ],
    "de": [
        "gegenpressing", "pressing", "hohe kette", "raumdeckung", "tiefenläufe",
        "halbraum", "spielverlagerung", "positionsspiel", "umschaltsituationen",
        "xg", "erwartete tore", "ppda", "tiefenpass", "freilaufbewegungen",
        "viererkette", "dreierkette", "falscher neuner", "flügelstürmer",
    ],
    "es": [
        "presión alta", "bloque bajo", "gegenpressing", "pressing", "half-space",
        "espacio entre líneas", "xg", "goles esperados", "ppda",
        "repliegue", "transición", "superioridad posicional", "basculación",
        "línea alta", "carrilero", "mediapunta", "falso nueve",
    ],
    "fr": [
        "pressing haut", "bloc bas", "gegenpressing", "pressing", "demi-espace",
        "demi espace", "xg", "buts attendus", "ppda", "transition",
        "supériorité positionnelle", "ligne haute", "faux numéro neuf",
        "repli défensif", "verticalité", "pressing intense",
    ],
    "it": [
        "pressing alto", "blocco basso", "gegenpressing", "pressing", "mezzaspazio",
        "xg", "gol attesi", "ppda", "transizione", "superiorità posizionale",
        "linea alta", "falso nueve", "trequartista", "terzino", "ribaltamento",
        "verticalizzazione", "densità difensiva",
    ],
}

_HEDGE_PHRASES: dict[str, list[str]] = {
    "en": ["could go either way", "too close to call", "could go both ways",
           "it remains to be seen", "only time will tell", "both teams will be hoping",
           "anything could happen", "hard to predict", "difficult to say"],
    "de": ["kann in beide richtungen gehen", "schwer zu sagen", "alles ist möglich",
           "es bleibt abzuwarten", "man wird sehen", "könnte in beide richtungen gehen"],
    "es": ["puede ir para cualquier lado", "difícil predecir", "cualquier cosa puede pasar",
           "está por verse", "podría salir de cualquier manera"],
    "fr": ["ça pourrait aller dans les deux sens", "difficile à prédire", "tout est possible",
           "reste à voir", "on verra bien"],
    "it": ["può andare in entrambe le direzioni", "difficile dirlo", "tutto è possibile",
           "si vedrà", "impossibile prevedere"],
}

_BAD_OPENERS: dict[str, list[str]] = {
    "en": [" will play", " host ", " face ", " welcome ", " travel to", "today's match",
           "tonight's fixture", "in tonight's", "in today's"],
    "de": [" spielt gegen", " empfängt ", " trifft auf", " reist nach", "das heutige spiel"],
    "es": [" jugará contra", " recibe a", " se enfrenta a", "el partido de hoy"],
    "fr": [" jouera contre", " accueille ", " affronte ", " se déplace", "le match de ce soir"],
    "it": [" giocherà contro", " ospita ", " affronta ", "la partita di oggi"],
}

_PREDICTION_KEYWORDS: dict[str, list[str]] = {
    "en": ["win this", "will win", "home win", "away win", "draw", "clean sheet",
           "take the", "back ", "side will"],
    "de": ["heimsieg", "auswärtssieg", "unentschieden", "siegen", "wird gewinnen",
           "kein zweifel", "klarer sieg", "punkte holen"],
    "es": ["victoria local", "victoria visitante", "empate", "ganará", "triunfo",
           "se llevará los tres", "apuesta por"],
    "fr": ["victoire à domicile", "victoire à l'extérieur", "match nul", "gagnera",
           "l'emportera", "prendront les trois", "jouer"],
    "it": ["vittoria in casa", "vittoria in trasferta", "pareggio", "vincerà",
           "porterà a casa", "tre punti", "scommetti"],
}

_HISTORICAL_MARKERS: dict[str, list[str]] = {
    "en": ["weeks ago", "last month", "previous", "we saw", "we witnessed", "reminded",
           "similar to", "comparable to", "in their last", "recall", "back in"],
    "de": ["wochen", "letzten monat", "erinnert an", "haben wir gesehen", "ähnlich wie",
           "beim letzten", "damals", "vor kurzem", "zuvor"],
    "es": ["semanas atrás", "mes pasado", "recordamos", "vimos", "similar a",
           "en el último", "hace unas semanas", "anteriormente"],
    "fr": ["semaines", "mois dernier", "on a vu", "nous avons vu", "similaire à",
           "lors du dernier", "rappelle", "il y a quelques"],
    "it": ["settimane fa", "mese scorso", "abbiamo visto", "ci ricorda", "simile a",
           "nell'ultima", "ricordo", "in precedenza"],
}


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_article(article: str, lang: str, match_data: dict) -> dict[str, bool]:
    text = article.lower()
    first_sentence = re.split(r"[.!?]", article)[0].lower() if article else ""

    lang_key = lang if lang in _TACTICAL_TERMS else "en"

    # Rule 1: Tactical claim opener (first sentence does NOT start with team name + generic verb)
    home = match_data.get("home_team", "").split()[0].lower()
    away = match_data.get("away_team", "").split()[0].lower()
    bad_opener = any(
        (home in first_sentence or away in first_sentence) and bp in first_sentence
        for bp in _BAD_OPENERS.get(lang_key, _BAD_OPENERS["en"])
    )
    tactical_opener = not bad_opener and len(first_sentence) > 20

    # Rule 2: Bold prediction (no hedge + has prediction keyword)
    has_hedge = any(h in text for h in _HEDGE_PHRASES.get(lang_key, _HEDGE_PHRASES["en"]))
    has_prediction = any(kw in text for kw in _PREDICTION_KEYWORDS.get(lang_key, _PREDICTION_KEYWORDS["en"]))
    bold_prediction = not has_hedge and has_prediction

    # Rule 3: Statistics with context (number followed by % with surrounding text)
    has_pct_with_context = bool(re.search(r"\d{1,3}\s*%[^.]{5,}", article))
    has_stat_with_clause = bool(re.search(r"\d+\.?\d*\s*(xg|x g|ppda|goals|tor|buts|gol)", text))
    stat_with_context = has_pct_with_context or has_stat_with_clause

    # Rule 4: Historical callback
    historical = any(m in text for m in _HISTORICAL_MARKERS.get(lang_key, _HISTORICAL_MARKERS["en"]))

    # Rule 5: Tactical vocabulary (≥2 terms)
    terms_found = sum(1 for t in _TACTICAL_TERMS.get(lang_key, _TACTICAL_TERMS["en"]) if t in text)
    tactical_vocab = terms_found >= 2

    # Rule 6: Decisive closing line (last sentence is short and doesn't hedge)
    sentences = [s.strip() for s in re.split(r"[.!?]", article) if s.strip()]
    last = sentences[-1].lower() if sentences else ""
    has_closing_hedge = any(h in last for h in _HEDGE_PHRASES.get(lang_key, _HEDGE_PHRASES["en"]))
    decisive_close = len(last) > 5 and not has_closing_hedge

    return {
        "tactical_opener": tactical_opener,
        "bold_prediction": bold_prediction,
        "stat_context": stat_with_context,
        "historical_ref": historical,
        "tactical_vocab": tactical_vocab,
        "decisive_close": decisive_close,
    }


def score_total(scores: dict[str, bool]) -> int:
    return sum(1 for v in scores.values() if v)


# ── Length check ──────────────────────────────────────────────────────────────

def check_length(article: str) -> bool:
    sentences = [s.strip() for s in re.split(r"[.!?]", article) if len(s.strip()) > 10]
    return 4 <= len(sentences) <= 7


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Nomen training dataset")
    parser.add_argument("--input", default="data/nomen_training/raw_v1.jsonl")
    parser.add_argument("--output", default="data/nomen_training/dataset_v1.jsonl")
    parser.add_argument("--rejected", default=None, help="Path for rejected examples (default: auto)")
    parser.add_argument("--min-score", type=int, default=4, help="Min style score to keep (0–6)")
    parser.add_argument("--report", action="store_true", help="Print per-language breakdown")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    input_path = repo_root / args.input
    output_path = repo_root / args.output
    rejected_path = Path(args.rejected) if args.rejected else output_path.with_suffix("") .parent / (output_path.stem + "_rejected.jsonl")

    if not input_path.exists():
        print(f"[validate] Input not found: {input_path}", file=sys.stderr)
        print("[validate] Run generate_nomen_dataset.py first.", file=sys.stderr)
        sys.exit(1)

    rows: list[dict] = []
    with input_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    print(f"[validate] Loaded {len(rows)} examples from {input_path.name}")

    passed: list[dict] = []
    rejected: list[dict] = []

    lang_stats: dict[str, dict] = {}

    for row in rows:
        lang = row.get("lang", "en")
        article_msg = next(
            (m["content"] for m in row.get("messages", []) if m["role"] == "assistant"),
            row.get("article", ""),
        )
        match_data = row.get("match_data", {})

        style_scores = score_article(article_msg, lang, match_data)
        total = score_total(style_scores)
        length_ok = check_length(article_msg)
        keep = total >= args.min_score and length_ok

        annotated = {**row, "_validation": {**style_scores, "total": total, "length_ok": length_ok}}

        if keep:
            passed.append(annotated)
        else:
            rejected.append(annotated)

        if lang not in lang_stats:
            lang_stats[lang] = {"total": 0, "passed": 0, "rule_fails": {r: 0 for r in style_scores}}
        lang_stats[lang]["total"] += 1
        if keep:
            lang_stats[lang]["passed"] += 1
        for rule, ok in style_scores.items():
            if not ok:
                lang_stats[lang]["rule_fails"][rule] += 1

    # Write outputs
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in passed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with rejected_path.open("w", encoding="utf-8") as f:
        for row in rejected:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    total_pass_rate = len(passed) / len(rows) * 100 if rows else 0
    print(f"\n[validate] Results: {len(passed)}/{len(rows)} passed ({total_pass_rate:.1f}%)")
    print(f"           Clean:    {output_path}")
    print(f"           Rejected: {rejected_path}")

    if args.report:
        print("\n── Per-language breakdown ─────────────────────────────────────────")
        for lang in sorted(lang_stats):
            s = lang_stats[lang]
            pct = s["passed"] / s["total"] * 100 if s["total"] else 0
            print(f"  [{lang}] {s['passed']}/{s['total']} ({pct:.1f}%)  failures: " +
                  ", ".join(f"{r}={n}" for r, n in s["rule_fails"].items() if n > 0))

    if total_pass_rate < 85:
        print(f"\n[validate] WARNING: Pass rate {total_pass_rate:.1f}% is below the 85% target.")
        print("[validate] Review rejected examples and consider tweaking the generation prompt.")
    else:
        print(f"\n[validate] PASS: {total_pass_rate:.1f}% ≥ 85% target. Dataset ready for training.")


if __name__ == "__main__":
    main()
