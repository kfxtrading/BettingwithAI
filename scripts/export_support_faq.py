"""Export the Support-Chatbot FAQ knowledge base as an ML-ready JSONL dataset.

Reads:
  - web/lib/faq.ts              (entry metadata: id, questionKey, answerKey, tags)
  - web/lib/i18n/{en,de,es,fr,it}.ts  (localized question + answer strings)

Writes:
  - data/support_faq/dataset.jsonl        (one row per (id, lang))
  - data/support_faq/intents.json         (id -> chapter, tags)
  - data/support_faq/stats.json           (counts per chapter / language)

Row schema (JSONL):
  {
    "id":       "basics-1x2",
    "key":      "support.faq.basics.oneX2",
    "chapter":  "basics",
    "lang":     "de",
    "question": "Was bedeutet 1X2 bei Fußballwetten?",
    "answer":   "1X2 ist der klassische Drei-Wege-Markt ...",
    "tags":     ["1x2","heim","..."]
  }

Usage:
  python scripts/export_support_faq.py
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "lib"
OUT_DIR = ROOT / "data" / "support_faq"
LANGS = ("en", "de", "es", "fr", "it")

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------
FAQ_ENTRY_RE = re.compile(
    r"\{\s*"
    r"id:\s*'([^']+)',\s*"
    r"questionKey:\s*'([^']+)',\s*"
    r"answerKey:\s*'([^']+)',\s*"
    r"tags:\s*\[([^\]]*)\],?\s*"
    r"\}",
    re.DOTALL,
)
TAG_RE = re.compile(r"'([^']*)'")
# Match:  'support.faq.X.Y.q': "text",     OR    'support.faq.X.Y.q': 'text',
I18N_LINE_RE = re.compile(
    r"^\s*'(support\.faq\.[^']+)'\s*:\s*(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')\s*,\s*$",
    re.MULTILINE,
)


def parse_faq_entries(text: str):
    entries = []
    for m in FAQ_ENTRY_RE.finditer(text):
        entry_id, qk, ak, raw_tags = m.groups()
        tags = TAG_RE.findall(raw_tags)
        entries.append(
            {"id": entry_id, "questionKey": qk, "answerKey": ak, "tags": tags}
        )
    return entries


def _unescape_ts_string(s: str) -> str:
    # Drop surrounding quote, decode standard JS escapes.
    quote = s[0]
    inner = s[1:-1]
    # JSON handles \n \t \" \\ \uXXXX and (for double quoted) is compatible.
    # Re-wrap in double quotes for json.loads regardless of original quote style.
    if quote == "'":
        inner = inner.replace("\\'", "'").replace('"', '\\"')
    return json.loads(f'"{inner}"')


def parse_i18n_file(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in I18N_LINE_RE.finditer(text):
        key, raw_val = m.group(1), m.group(2)
        try:
            out[key] = _unescape_ts_string(raw_val)
        except json.JSONDecodeError:
            out[key] = raw_val[1:-1]
    return out


def chapter_of(question_key: str) -> str:
    # support.faq.<chapter>.<slug>.q  →  chapter
    # support.faq.<slug>.q            →  "general"
    parts = question_key.split(".")
    return parts[2] if len(parts) == 5 else "general"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    faq_src = (WEB / "faq.ts").read_text(encoding="utf-8")
    entries = parse_faq_entries(faq_src)
    if not entries:
        raise SystemExit("No FAQ entries parsed — aborting.")

    locales: dict[str, dict[str, str]] = {}
    for lang in LANGS:
        path = WEB / "i18n" / f"{lang}.ts"
        locales[lang] = parse_i18n_file(path.read_text(encoding="utf-8"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = OUT_DIR / "dataset.jsonl"
    missing: list[tuple[str, str, str]] = []

    with jsonl_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            qk, ak = entry["questionKey"], entry["answerKey"]
            key = qk[:-2] if qk.endswith(".q") else qk  # strip trailing .q
            chapter = chapter_of(qk)
            for lang in LANGS:
                q = locales[lang].get(qk)
                a = locales[lang].get(ak)
                if q is None or a is None:
                    missing.append((entry["id"], lang, qk))
                    continue
                row = {
                    "id": entry["id"],
                    "key": key,
                    "chapter": chapter,
                    "lang": lang,
                    "question": q,
                    "answer": a,
                    "tags": entry["tags"],
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # intents.json — per-id metadata (language-independent)
    intents = [
        {
            "id": e["id"],
            "key": e["questionKey"][:-2] if e["questionKey"].endswith(".q") else e["questionKey"],
            "chapter": chapter_of(e["questionKey"]),
            "tags": e["tags"],
        }
        for e in entries
    ]
    (OUT_DIR / "intents.json").write_text(
        json.dumps(intents, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # stats.json
    chapter_counts = Counter(chapter_of(e["questionKey"]) for e in entries)
    lang_counts: dict[str, int] = defaultdict(int)
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            lang_counts[json.loads(line)["lang"]] += 1
    stats = {
        "n_intents": len(entries),
        "n_languages": len(LANGS),
        "n_rows": sum(lang_counts.values()),
        "per_chapter": dict(chapter_counts),
        "per_language": dict(lang_counts),
        "missing_translations": missing,
    }
    (OUT_DIR / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Wrote {jsonl_path.relative_to(ROOT)}  ({stats['n_rows']} rows)")
    print(f"      {OUT_DIR / 'intents.json'}       ({stats['n_intents']} intents)")
    print(f"      {OUT_DIR / 'stats.json'}")
    if missing:
        print(f"WARNING: {len(missing)} missing translations (see stats.json)")


if __name__ == "__main__":
    main()
