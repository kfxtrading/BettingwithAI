"""Aggregate cross-lang chapter-level confusion stats from per-lang JSONs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "models" / "support"
LANGS = ["de", "en", "es", "fr", "it"]


def chapter(intent: str) -> str:
    return "__ood__" if intent == "__ood__" else intent.split("-")[0]


def main() -> None:
    print(f"{'=' * 70}")
    print("PER-LANG: within-chapter vs cross-chapter confusion (on top_pairs)")
    print(f"{'=' * 70}")
    for lg in LANGS:
        p = SUPPORT / f"confusion_pairs_{lg}.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        pairs = data["top_confusion_pairs"]
        within = sum(pp["count"] for pp in pairs if chapter(pp["gold"]) == chapter(pp["pred"]))
        total = sum(pp["count"] for pp in pairs)
        print(
            f"  [{lg}] top1={data['top1_accuracy']:.3f} | "
            f"n_errors={data['n_errors']} | "
            f"top_pairs cover {data['top_pairs_cover_share_of_errors'] * 100:.1f}% of errors | "
            f"within-chapter share of top pairs: {within / max(total, 1) * 100:.1f}%"
        )

    print()
    print(f"{'=' * 70}")
    print("0%-recall intents by chapter (per lang)")
    print(f"{'=' * 70}")
    for lg in LANGS:
        p = SUPPORT / f"confusion_pairs_{lg}.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        zero = [wi["intent"] for wi in data["worst_intents"] if wi["recall"] == 0.0]
        ch_zero = Counter(chapter(i) for i in zero)
        print(f"  [{lg}] chapters with 0%-recall intents: {dict(ch_zero.most_common())}")

    # Aggregate worst chapters across langs
    print()
    print(f"{'=' * 70}")
    print("CROSS-LANG: intents that are 0%-recall in >= 2 langs")
    print(f"{'=' * 70}")
    zero_per_intent: Counter[str] = Counter()
    for lg in LANGS:
        p = SUPPORT / f"confusion_pairs_{lg}.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        for wi in data["worst_intents"]:
            if wi["recall"] == 0.0:
                zero_per_intent[wi["intent"]] += 1
    for intent, n in zero_per_intent.most_common():
        if n >= 2:
            print(f"  {intent:<45} 0% in {n}/{len(LANGS)} langs")

    # Summary: all top pairs, fraction within-chapter
    print()
    print(f"{'=' * 70}")
    print("CROSS-LANG chapter-confusion signature")
    print(f"{'=' * 70}")
    summary = json.loads((SUPPORT / "confusion_summary.json").read_text(encoding="utf-8"))
    cross_pairs = summary["cross_lang_top_pairs"]
    within = sum(
        pp["count_all_langs"] for pp in cross_pairs if chapter(pp["gold"]) == chapter(pp["pred"])
    )
    total = sum(pp["count_all_langs"] for pp in cross_pairs)
    print(
        f"Top-20 cross-lang pairs: {total} total confusions, "
        f"{within} within-chapter ({within / max(total, 1) * 100:.1f}%)"
    )


if __name__ == "__main__":
    main()
