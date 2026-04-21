"""Paraphrase-augment the ML-ready support FAQ dataset.

Reads:
  - data/support_faq/dataset.jsonl   (670 original rows; 134 intents x 5 langs)

Writes:
  - data/support_faq/dataset_augmented.jsonl
      One row per (id, lang, variant). Schema adds:
        "variant":  integer >= 0   (0 = original canonical question)
        "source":   "original" | "paraphrase"
  - data/support_faq/augment_stats.json
      Counts per chapter/language/source.

Strategy (deterministic, reproducible, no API calls):
  Per (id, lang) we emit:
    1. the canonical question                                         (1 row)
    2. N prefix-wrapped paraphrases  ("Can you explain: <q>", ...)    (~6 rows)
    3. N topic-based paraphrases     ("Explain <topic>", ...)         (~3 rows)
    4. tag-based micro-queries       (lowercase tag words)            (~3 rows)
    5. lower/no-punct normalisations                                  (~2 rows)
  Duplicates are dropped; target is ~10-15 rows per (id, lang),
  i.e. ~6.700-10.000 paraphrase rows in addition to the 670 originals.

Usage:
  python scripts/augment_support_faq.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "support_faq" / "dataset.jsonl"
OUT_PATH = ROOT / "data" / "support_faq" / "dataset_augmented.jsonl"
STATS_PATH = ROOT / "data" / "support_faq" / "augment_stats.json"

# ---------------------------------------------------------------------------
# Per-language linguistic resources
# ---------------------------------------------------------------------------

# Leading interrogative phrases that should be stripped when extracting the
# "topic" of a question. Order matters: longer phrases first.
STRIP_PREFIXES: dict[str, list[str]] = {
    "en": [
        "what does", "what is", "what are", "how does", "how do", "how can",
        "how is", "how are", "why is", "why are", "why does", "why do",
        "when should", "where can", "which ", "who is", "who are",
        "can you explain", "can i", "should i", "tell me about",
        "explain", "define",
    ],
    "de": [
        "was versteht man unter", "was bedeutet", "was ist", "was sind",
        "wie funktioniert", "wie funktionieren", "wie berechnet",
        "wie berechne ich", "wie analysiere ich", "wie erkenne ich",
        "wie vermeide ich", "wie wichtig ist", "wie wichtig sind",
        "wie viel", "wie hoch ist", "wie lange", "wie oft",
        "wie nutze ich", "wie baue ich", "wie finde ich", "wie teste ich",
        "wie integriert man", "wie zeigt man", "wie automatisiert man",
        "wie kombiniert man", "wie misst man", "wie entstehen", "wie",
        "warum ist", "warum sind", "warum verlieren", "warum sollte man",
        "warum ändern sich", "warum", "welche", "welcher", "welches",
        "wann sollte ich", "wann", "kann man", "ist ", "sind ",
        "sollte ich",
    ],
    "es": [
        "qué es", "qué son", "qué significa", "cómo funciona",
        "cómo funcionan", "cómo analizo", "cómo identifico",
        "cómo evito", "cómo reconozco", "cómo calculo",
        "cuánto", "cuánta", "cuántos", "cuántas", "cuándo",
        "por qué", "cuál es", "cuál", "cuáles son", "cuáles",
        "puedo", "debería",
    ],
    "fr": [
        "qu'est-ce qu'", "qu'est-ce que", "qu'est-ce qui",
        "c'est quoi", "comment fonctionne", "comment fonctionnent",
        "comment analyser", "comment identifier", "comment éviter",
        "comment reconnaître", "comment calculer",
        "combien", "quand", "pourquoi", "quel est", "quelle est",
        "quels sont", "quelles sont", "quel", "quelle", "quels", "quelles",
        "puis-je", "devrais-je",
    ],
    "it": [
        "che cos'è", "che cos’è", "cos'è", "cos’è", "che cosa",
        "come funziona", "come funzionano", "come analizzo",
        "come identifico", "come evito", "come riconosco",
        "come calcolo", "quanto", "quanta", "quanti", "quante",
        "quando", "perché", "qual è", "qual", "quali sono", "quali",
        "posso", "dovrei",
    ],
}

# Prefix-wrapper templates; {q} = original question (with trailing ? preserved)
PREFIX_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "Can you explain: {q}",
        "I want to know: {q}",
        "Please help: {q}",
        "Quick question — {q}",
        "Could you answer: {q}",
        "I'm wondering, {q}",
    ],
    "de": [
        "Kannst du mir erklären: {q}",
        "Ich möchte wissen: {q}",
        "Bitte um Hilfe: {q}",
        "Kurze Frage — {q}",
        "Könntest du mir sagen: {q}",
        "Ich frage mich, {q}",
    ],
    "es": [
        "¿Puedes explicar: {q}",
        "Quiero saber: {q}",
        "Ayuda por favor: {q}",
        "Pregunta rápida — {q}",
        "¿Podrías responder: {q}",
        "Me pregunto, {q}",
    ],
    "fr": [
        "Peux-tu expliquer : {q}",
        "Je veux savoir : {q}",
        "Aide-moi s'il te plaît : {q}",
        "Question rapide — {q}",
        "Pourrais-tu répondre : {q}",
        "Je me demande, {q}",
    ],
    "it": [
        "Puoi spiegare: {q}",
        "Voglio sapere: {q}",
        "Aiutami per favore: {q}",
        "Domanda veloce — {q}",
        "Potresti rispondere: {q}",
        "Mi chiedo, {q}",
    ],
}

# Topic-based templates; {t} = extracted topic (prefix stripped, no "?")
TOPIC_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "Tell me about {t}.",
        "Explain {t}.",
        "{t} — what does that mean?",
        "I need info on {t}.",
    ],
    "de": [
        "Erkläre mir {t}.",
        "Sag mir mehr zu {t}.",
        "{t} — was heißt das?",
        "Ich brauche Infos zu {t}.",
    ],
    "es": [
        "Cuéntame sobre {t}.",
        "Explícame {t}.",
        "{t} — ¿qué significa?",
        "Necesito información sobre {t}.",
    ],
    "fr": [
        "Parle-moi de {t}.",
        "Explique {t}.",
        "{t} — ça veut dire quoi ?",
        "J'ai besoin d'infos sur {t}.",
    ],
    "it": [
        "Parlami di {t}.",
        "Spiegami {t}.",
        "{t} — che significa?",
        "Mi servono informazioni su {t}.",
    ],
}

# Single-keyword stop-words we don't want as standalone tag queries.
STOPWORD_TAGS = {
    "a", "an", "the", "is", "are", "to", "of", "in", "on", "for",
    "und", "oder", "der", "die", "das", "ein", "eine", "mit", "für",
    "de", "la", "el", "los", "las", "un", "una", "y", "o",
    "du", "de", "le", "les", "un", "une", "et", "ou",
    "il", "lo", "la", "gli", "le", "un", "una", "e",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def strip_question_punct(q: str) -> str:
    """Return the question body without leading/trailing ¿ ? or quotes/spaces."""
    return q.strip().strip("¿¡").rstrip("?!.").strip()


def lowercase_key(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def extract_topic(question: str, lang: str) -> str | None:
    """Strip a known interrogative prefix; return remaining topic or None."""
    body = strip_question_punct(question)
    low = body.lower()
    for p in STRIP_PREFIXES.get(lang, []):
        if low.startswith(p):
            topic = body[len(p):].strip(" ,:;—-")
            if topic and len(topic) >= 3:
                return topic
    return None


def paraphrases_for(row: dict) -> list[str]:
    """Generate unique paraphrase strings for one (id, lang) row."""
    lang: str = row["lang"]
    q: str = row["question"]
    tags: list[str] = row.get("tags", [])

    out: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = _nfkc(s).strip()
        if not s:
            return
        k = lowercase_key(s)
        if k in seen:
            return
        seen.add(k)
        out.append(s)

    # 0) canonical (variant 0) — added by caller, but we register its lowered form
    seen.add(lowercase_key(q))

    # 1) prefix-wrapped variants (preserve trailing ? if any)
    q_trim = q.rstrip()
    for tpl in PREFIX_TEMPLATES.get(lang, []):
        add(tpl.format(q=q_trim))

    # 2) topic-based variants
    topic = extract_topic(q, lang)
    if topic:
        for tpl in TOPIC_TEMPLATES.get(lang, []):
            add(tpl.format(t=topic))
        # 2b) bare topic as a short query
        add(topic)
        add(f"{topic}?")
        add(topic.lower())

    # 3) lower-case / no-punctuation normalisations
    add(q.lower())
    add(strip_question_punct(q))
    add(strip_question_punct(q).lower())

    # 4) tag-based micro-queries (only substantive tokens)
    for tag in tags:
        t = tag.strip()
        if len(t) < 3 or t.lower() in STOPWORD_TAGS:
            continue
        add(t)
        add(f"{t}?")
    # 4b) first-two-tags combo for more natural keyword-style queries
    clean_tags = [
        t for t in tags
        if len(t) >= 3 and t.lower() not in STOPWORD_TAGS
    ]
    if len(clean_tags) >= 2:
        add(f"{clean_tags[0]} {clean_tags[1]}")

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    if not IN_PATH.exists():
        raise SystemExit(f"Input not found: {IN_PATH}. Run export_support_faq.py first.")

    rows = [json.loads(line) for line in IN_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

    total = 0
    per_chapter: Counter[str] = Counter()
    per_lang: Counter[str] = Counter()
    per_source: Counter[str] = Counter()
    per_intent_lang_counts: Counter[str] = Counter()

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            base = {
                "id": row["id"],
                "key": row["key"],
                "chapter": row["chapter"],
                "lang": row["lang"],
                "answer": row["answer"],
                "tags": row.get("tags", []),
            }

            # variant 0 = original
            original = {
                **base,
                "variant": 0,
                "source": "original",
                "question": row["question"],
            }
            f.write(json.dumps(original, ensure_ascii=False) + "\n")
            total += 1
            per_chapter[row["chapter"]] += 1
            per_lang[row["lang"]] += 1
            per_source["original"] += 1
            per_intent_lang_counts[f"{row['id']}|{row['lang']}"] += 1

            # paraphrase variants
            for i, p in enumerate(paraphrases_for(row), start=1):
                out = {
                    **base,
                    "variant": i,
                    "source": "paraphrase",
                    "question": p,
                }
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
                total += 1
                per_chapter[row["chapter"]] += 1
                per_lang[row["lang"]] += 1
                per_source["paraphrase"] += 1
                per_intent_lang_counts[f"{row['id']}|{row['lang']}"] += 1

    variants_list = list(per_intent_lang_counts.values())
    stats = {
        "n_input_rows": len(rows),
        "n_output_rows": total,
        "per_chapter": dict(per_chapter),
        "per_language": dict(per_lang),
        "per_source": dict(per_source),
        "variants_per_intent_lang": {
            "min": min(variants_list) if variants_list else 0,
            "max": max(variants_list) if variants_list else 0,
            "avg": round(sum(variants_list) / len(variants_list), 2) if variants_list else 0,
        },
    }
    STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {total} rows to {OUT_PATH.relative_to(ROOT)}")
    print(f"Wrote stats to  {STATS_PATH.relative_to(ROOT)}")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
