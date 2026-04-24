"""Confusion analysis for the v3 transformer intent classifier.

Loads every per-language fine-tune, re-runs the validation split, and
surfaces the largest confusion pairs (gold → predicted). Output:

  * per-lang Top-N confusion pairs printed to stdout
  * ``models/support/confusion_pairs_<lang>.json`` with the full ranked list
  * ``models/support/confusion_summary.json`` aggregating top pairs across langs

Usage::

    python scripts/analyze_intent_confusion.py            # all 5 langs, top 20
    python scripts/analyze_intent_confusion.py --lang de --top 30

The dataset + stratified split are deterministic (seed 42) and match the
trainer exactly, so the "val" set here is the same ~2.5k rows the trainer
evaluated on during the final epoch.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_betting.config import SUPPORT_CFG, SUPPORT_DATA_DIR, SUPPORT_MODELS_DIR
from football_betting.support.dataset import load_dataset, stratified_split
from football_betting.support.transformer_model import TransformerIntentClassifier


def _resolve_dataset_path() -> Path:
    """Match the trainer's fallback chain: v3 → v2 → base."""
    for name in (
        SUPPORT_CFG.augmented_v3_filename,
        SUPPORT_CFG.augmented_v2_filename,
        SUPPORT_CFG.dataset_filename,
    ):
        p = SUPPORT_DATA_DIR / name
        if p.exists():
            return p
    raise FileNotFoundError("No dataset found (v3/v2/base all missing)")


def _model_dir(lang: str) -> Path:
    return SUPPORT_MODELS_DIR / f"support_transformer_{lang}"


def analyze_lang(lang: str, *, top_n: int = 20) -> dict[str, Any]:
    ds_path = _resolve_dataset_path()
    rows = load_dataset(path=ds_path, lang=lang, include_ood=True)
    split = stratified_split(rows)  # deterministic seed
    texts = list(split.X_val)
    gold = list(split.y_val)

    mdir = _model_dir(lang)
    if not mdir.exists():
        raise FileNotFoundError(f"Model dir missing: {mdir}")

    clf = TransformerIntentClassifier.load(mdir)

    probs = clf.predict_proba_batch(texts)
    pred_idx = probs.argmax(axis=1)
    pred = [clf.classes_[int(i)] for i in pred_idx]

    # Per-intent tallies for accuracy + confusion pairs (gold != pred).
    per_intent_total: Counter[str] = Counter()
    per_intent_correct: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    for g, p in zip(gold, pred, strict=True):
        per_intent_total[g] += 1
        if g == p:
            per_intent_correct[g] += 1
        else:
            pair_counts[(g, p)] += 1

    n_val = len(texts)
    n_correct = sum(per_intent_correct.values())
    n_errors = n_val - n_correct

    # Worst intents by recall (sorted ascending), min 3 samples
    worst_intents: list[dict[str, Any]] = []
    for intent, total in per_intent_total.most_common():
        if total < 3:
            continue
        correct = per_intent_correct[intent]
        recall = correct / total
        worst_intents.append(
            {
                "intent": intent,
                "recall": round(recall, 3),
                "correct": correct,
                "total": total,
            }
        )
    worst_intents.sort(key=lambda x: (x["recall"], -x["total"]))

    ranked_pairs = [
        {
            "gold": g,
            "pred": p,
            "count": c,
            "share_of_errors": round(c / max(n_errors, 1), 3),
        }
        for (g, p), c in pair_counts.most_common(top_n * 3)
    ]

    # Cumulative share covered by top_n pairs
    top_pairs = ranked_pairs[:top_n]
    cum_share = sum(p["share_of_errors"] for p in top_pairs)

    return {
        "lang": lang,
        "n_val": n_val,
        "n_correct": n_correct,
        "n_errors": n_errors,
        "top1_accuracy": round(n_correct / n_val, 4) if n_val else 0.0,
        "top_confusion_pairs": top_pairs,
        "top_pairs_cover_share_of_errors": round(cum_share, 3),
        "worst_intents": worst_intents[:top_n],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="all", help="Language code or 'all'")
    ap.add_argument("--top", type=int, default=20, help="Top-N confusion pairs")
    ap.add_argument("--no-write", action="store_true", help="Skip JSON file output")
    args = ap.parse_args()

    langs = list(SUPPORT_CFG.languages) if args.lang == "all" else [args.lang]

    per_lang_reports: list[dict[str, Any]] = []
    for lg in langs:
        print(f"\n{'=' * 60}\n[{lg}] analyzing …\n{'=' * 60}")
        try:
            rep = analyze_lang(lg, top_n=args.top)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{lg}] FAILED: {exc}")
            continue

        print(f"  val={rep['n_val']}  errors={rep['n_errors']}  top1={rep['top1_accuracy']:.3f}")
        print(
            f"  Top {args.top} pairs cover "
            f"{rep['top_pairs_cover_share_of_errors'] * 100:.1f}% of errors"
        )
        print(f"\n  --- Top {args.top} confusion pairs (gold → pred, count) ---")
        for p in rep["top_confusion_pairs"]:
            print(f"    {p['gold']:<40} → {p['pred']:<40} {p['count']:3d}")

        print(f"\n  --- Bottom {args.top} intents by recall ---")
        for wi in rep["worst_intents"]:
            print(
                f"    {wi['intent']:<40} recall={wi['recall']:.2f} ({wi['correct']}/{wi['total']})"
            )

        if not args.no_write:
            out = SUPPORT_MODELS_DIR / f"confusion_pairs_{lg}.json"
            out.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  wrote {out}")

        per_lang_reports.append(rep)

    # Aggregate: which gold→pred pairs appear across multiple langs?
    global_pairs: Counter[tuple[str, str]] = Counter()
    for rep in per_lang_reports:
        for p in rep["top_confusion_pairs"]:
            global_pairs[(p["gold"], p["pred"])] += p["count"]

    summary = {
        "per_lang_summary": [
            {
                "lang": r["lang"],
                "n_val": r["n_val"],
                "n_errors": r["n_errors"],
                "top1": r["top1_accuracy"],
                "top_pairs_cover_share": r["top_pairs_cover_share_of_errors"],
            }
            for r in per_lang_reports
        ],
        "cross_lang_top_pairs": [
            {"gold": g, "pred": p, "count_all_langs": c}
            for (g, p), c in global_pairs.most_common(args.top)
        ],
    }

    print(f"\n{'=' * 60}\nCROSS-LANG TOP {args.top} CONFUSERS\n{'=' * 60}")
    for p in summary["cross_lang_top_pairs"]:
        print(f"  {p['gold']:<40} → {p['pred']:<40} {p['count_all_langs']:3d}")

    if not args.no_write and per_lang_reports:
        out = SUPPORT_MODELS_DIR / "confusion_summary.json"
        out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
