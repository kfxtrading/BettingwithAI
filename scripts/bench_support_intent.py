"""Benchmark trained ML intent classifier vs Fuse-like fuzzy baseline.

For each language:
- Load the trained joblib model (per-locale).
- Recreate the train/val split exactly as the trainer did.
- Build a Fuse-like baseline that matches the val query against the
  canonical question + altQuestions of every intent (the same fields
  the JS Fuse indexes), using rapidfuzz token_set_ratio as the score.
- Report top-1, top-3 for both, and the delta.

Usage: python scripts/bench_support_intent.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from rapidfuzz import fuzz, process
from rich.console import Console
from rich.table import Table

from football_betting.config import (
    SUPPORT_CFG,
    SUPPORT_DATA_DIR,
    SUPPORT_MODELS_DIR,
)
from football_betting.support.dataset import load_dataset, stratified_split
from football_betting.support.intent_model import IntentClassifier
from football_betting.support.text import normalize

ROOT = Path(__file__).resolve().parents[1]
console = Console()


def build_fuse_index(rows_lang: list[dict[str, object]]) -> dict[str, list[str]]:
    """Per-intent corpus: canonical question + alt_questions (normalized)."""
    by_intent: dict[str, list[str]] = defaultdict(list)
    for r in rows_lang:
        intent = str(r["id"])
        if r.get("source") == "original":
            q = str(r.get("question", ""))
            if q:
                by_intent[intent].append(normalize(q))
            for alt in (r.get("alt_questions") or []):
                if isinstance(alt, str) and alt:
                    by_intent[intent].append(normalize(alt))
    return dict(by_intent)


def fuse_topk(query: str, index: dict[str, list[str]], k: int = 3) -> list[str]:
    """Return top-k intent ids by max token_set_ratio across the intent's phrasings."""
    q = normalize(query)
    scored: list[tuple[str, float]] = []
    for intent_id, phrasings in index.items():
        if not phrasings:
            continue
        best = process.extractOne(
            q, phrasings, scorer=fuzz.token_set_ratio
        )
        if best is None:
            continue
        scored.append((intent_id, float(best[1])))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [iid for iid, _ in scored[:k]]


def evaluate_lang(lang: str) -> dict[str, object]:
    rows = load_dataset(lang=lang)
    split = stratified_split(rows)
    if not split.X_val:
        return {"lang": lang, "skipped": True}

    # ML model
    model_path = SUPPORT_MODELS_DIR / SUPPORT_CFG.model_filename_template.format(lang=lang)
    clf = IntentClassifier.load(model_path)
    probs = clf.predict_proba_batch(split.X_val)
    import numpy as np
    top3_idx = np.argsort(probs, axis=1)[:, ::-1][:, :3]
    classes = clf.classes_ or []

    ml_top1 = 0
    ml_top3 = 0

    # Fuse baseline
    fuse_index = build_fuse_index(rows)
    fuse_top1 = 0
    fuse_top3 = 0

    n = len(split.X_val)
    for i, true_id in enumerate(split.y_val):
        # ML
        ml_pred = [classes[j] for j in top3_idx[i].tolist()]
        if ml_pred and ml_pred[0] == true_id:
            ml_top1 += 1
        if true_id in ml_pred:
            ml_top3 += 1
        # Fuse
        f_pred = fuse_topk(split.X_val[i], fuse_index, k=3)
        if f_pred and f_pred[0] == true_id:
            fuse_top1 += 1
        if true_id in f_pred:
            fuse_top3 += 1

    return {
        "lang": lang,
        "n_val": n,
        "n_classes": split.n_classes,
        "ml_top1": ml_top1 / n,
        "ml_top3": ml_top3 / n,
        "fuse_top1": fuse_top1 / n,
        "fuse_top3": fuse_top3 / n,
    }


def main() -> None:
    out: list[dict[str, object]] = []
    for lang in SUPPORT_CFG.languages:
        console.rule(f"[cyan]Benchmark — {lang}[/cyan]")
        try:
            res = evaluate_lang(lang)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]{lang} failed: {exc}[/red]")
            continue
        out.append(res)
        if res.get("skipped"):
            console.log(f"[yellow]{lang}: no val data[/yellow]")
            continue
        console.log(
            f"ML  top1={res['ml_top1']:.4f}  top3={res['ml_top3']:.4f}   "
            f"Fuse top1={res['fuse_top1']:.4f}  top3={res['fuse_top3']:.4f}"
        )

    table = Table(title="Support Intent — ML vs Fuse baseline")
    table.add_column("Lang")
    table.add_column("#Val", justify="right")
    table.add_column("#Cls", justify="right")
    table.add_column("ML t1", justify="right")
    table.add_column("ML t3", justify="right")
    table.add_column("Fuse t1", justify="right")
    table.add_column("Fuse t3", justify="right")
    table.add_column("d t1", justify="right")
    table.add_column("d t3", justify="right")
    for r in out:
        if r.get("skipped"):
            continue
        d1 = r["ml_top1"] - r["fuse_top1"]
        d3 = r["ml_top3"] - r["fuse_top3"]
        table.add_row(
            str(r["lang"]),
            str(r["n_val"]),
            str(r["n_classes"]),
            f"{r['ml_top1']:.4f}",
            f"{r['ml_top3']:.4f}",
            f"{r['fuse_top1']:.4f}",
            f"{r['fuse_top3']:.4f}",
            f"{d1:+.4f}",
            f"{d3:+.4f}",
        )
    console.print(table)

    out_path = SUPPORT_MODELS_DIR / "benchmark_vs_fuse.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    console.log(f"[green]Wrote {out_path}[/green]")


if __name__ == "__main__":
    main()
