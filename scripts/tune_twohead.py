"""Hyperparameter sweep for the two-head transformer (support intent classifier).

Iterates over a small grid of loss/optim HPs on a **subsampled** language
(default: DE) and writes a JSON + CSV summary to ``models/support/tuning/``.

Key knobs:

* ``chapter_head_weight`` (α) — weight of the auxiliary chapter CE loss.
* ``supcon_weight`` — weight of the Supervised Contrastive loss.
* ``transformer_learning_rate`` — AdamW LR on the shared encoder.

After training, the ``chapter_gate`` is inference-time free so each model is
evaluated with **multiple gates** (1.0 = disabled, 0.7, 0.6, 0.5) to find the
best post-hoc threshold without retraining.

Usage::

    python scripts/tune_twohead.py --lang de --max-rows-per-intent 50 --epochs 2

Output: ``models/support/tuning/twohead_sweep_<lang>.{json,csv}``

The runs write their own scratch model dirs under
``models/support/tuning/<run_name>/`` so the real ``support_twohead_*`` model
artefacts are never overwritten.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import shutil
import sys
import time
from dataclasses import replace as dc_replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_betting.config import SUPPORT_CFG  # noqa: E402

DEFAULT_GRID: dict[str, list[float]] = {
    "chapter_head_weight": [0.1, 0.3, 0.5, 1.0],
    "supcon_weight": [0.3],  # Fixed at default; expand later if needed.
    "transformer_learning_rate": [2e-5],  # Fixed at default.
}
GATE_VALUES = [1.0, 0.7, 0.6, 0.5]


def _make_grid(grid: dict[str, list[float]]) -> list[dict[str, float]]:
    keys = list(grid.keys())
    out: list[dict[str, float]] = []
    for values in itertools.product(*(grid[k] for k in keys)):
        out.append(dict(zip(keys, values, strict=True)))
    return out


def _run_name(overrides: dict[str, float]) -> str:
    parts = []
    for k, v in overrides.items():
        short = {
            "chapter_head_weight": "cw",
            "supcon_weight": "sw",
            "transformer_learning_rate": "lr",
        }.get(k, k)
        parts.append(f"{short}{v:g}")
    return "_".join(parts)


def _eval_all_gates(
    clf: Any, X_val: list[str], y_val: list[str], chap_val: list[str]
) -> dict[str, dict[str, Any]]:
    """Re-run evaluation for several chapter gates without retraining."""
    results: dict[str, dict[str, Any]] = {}
    for gate in GATE_VALUES:
        # Swap cfg in-place with a gate-specific copy. predict_proba_batch
        # reads cfg.two_head_chapter_gate when called without explicit gate.
        original_cfg = clf.cfg
        clf.cfg = dc_replace(original_cfg, two_head_chapter_gate=float(gate))
        try:
            m = clf.evaluate(X_val, y_val, chapters=chap_val, top_confusions=5)
            results[f"gate_{gate:g}"] = {
                "top1_accuracy": m.get("top1_accuracy"),
                "top3_accuracy": m.get("top3_accuracy"),
                "macro_f1": m.get("macro_f1"),
                "chapter_head_top1": m.get("chapter_head_top1"),
            }
        finally:
            clf.cfg = original_cfg
    return results


def _train_one(
    lang: str,
    overrides: dict[str, float],
    scratch_dir: Path,
    epochs: int,
    max_rows_per_intent: int,
) -> dict[str, Any]:
    """Train once with ``overrides`` applied, return an evaluation record."""
    # Import lazily so the CLI `--help` stays fast.
    from football_betting.config import SUPPORT_DATA_DIR
    from football_betting.support.dataset import load_dataset, stratified_split
    from football_betting.support.trainer import train_two_head_one_language
    from football_betting.support.two_head_transformer import (
        TwoHeadTransformerIntentClassifier,
        _derive_chapter,
    )

    run_name = _run_name(overrides)
    out_dir = scratch_dir / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    payload = train_two_head_one_language(
        lang,
        out_dir=out_dir,
        include_ood=True,
        seed=42,
        calibrate=False,  # skip for sweep speed
        epochs=epochs,
        max_rows_per_intent=max_rows_per_intent,
        cfg_overrides=overrides,
    )
    train_seconds = time.time() - t0

    # Multi-gate post-hoc evaluation using the fresh checkpoint.
    model_path = Path(payload["model_path"])
    clf = TwoHeadTransformerIntentClassifier.load(model_path)

    ds_path = SUPPORT_DATA_DIR / SUPPORT_CFG.augmented_v3_filename
    if not ds_path.exists():
        ds_path = SUPPORT_DATA_DIR / SUPPORT_CFG.augmented_v2_filename
    rows = load_dataset(path=ds_path, lang=lang, include_ood=True)
    # Re-subsample deterministically to match training split.
    from football_betting.support.trainer import _subsample_per_intent

    rows = _subsample_per_intent(rows, max_rows_per_intent, seed=42)
    split = stratified_split(rows)
    chap_val = [
        _derive_chapter(str(i), m.get("chapter"))
        for i, m in zip(split.y_val, split.meta_val, strict=True)
    ]
    per_gate = _eval_all_gates(clf, split.X_val, split.y_val, chap_val)

    return {
        "run_name": run_name,
        "overrides": overrides,
        "train_seconds": round(train_seconds, 1),
        "default_gate_metrics": {
            "top1_accuracy": payload["metrics"]["top1_accuracy"],
            "top3_accuracy": payload["metrics"]["top3_accuracy"],
            "macro_f1": payload["metrics"]["macro_f1"],
            "chapter_head_top1": payload["metrics"]["chapter_head_top1"],
            "chapter_head_macro_f1": payload["metrics"]["chapter_head_macro_f1"],
        },
        "per_gate": per_gate,
        "n_train": payload["n_train"],
        "n_val": payload["n_val"],
        "n_classes": payload["n_classes"],
        "n_chapters": payload["n_chapters"],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lang", default="de", choices=list(SUPPORT_CFG.languages))
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--max-rows-per-intent", type=int, default=50)
    p.add_argument(
        "--chapter-head-weights",
        type=float,
        nargs="+",
        default=DEFAULT_GRID["chapter_head_weight"],
        help="Values to sweep for chapter_head_weight (α).",
    )
    p.add_argument(
        "--supcon-weights",
        type=float,
        nargs="+",
        default=DEFAULT_GRID["supcon_weight"],
    )
    p.add_argument(
        "--lrs",
        type=float,
        nargs="+",
        default=DEFAULT_GRID["transformer_learning_rate"],
    )
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "models" / "support" / "tuning",
        help="Output directory for the sweep summary + scratch models.",
    )
    p.add_argument(
        "--keep-models",
        action="store_true",
        help="Keep scratch model dirs (default: delete after summarising).",
    )
    args = p.parse_args()

    grid = {
        "chapter_head_weight": list(args.chapter_head_weights),
        "supcon_weight": list(args.supcon_weights),
        "transformer_learning_rate": list(args.lrs),
    }
    combos = _make_grid(grid)
    args.out.mkdir(parents=True, exist_ok=True)
    scratch_dir = args.out / f"scratch_{args.lang}"
    scratch_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'=' * 70}")
    print(
        f"Two-head HP sweep — lang={args.lang} epochs={args.epochs} "
        f"rows/intent≤{args.max_rows_per_intent}"
    )
    print(f"  {len(combos)} configs × {len(GATE_VALUES)} gates")
    print(f"{'=' * 70}")

    records: list[dict[str, Any]] = []
    for i, overrides in enumerate(combos, 1):
        print(f"\n[{i}/{len(combos)}] overrides={overrides}")
        try:
            rec = _train_one(
                args.lang,
                overrides,
                scratch_dir,
                epochs=args.epochs,
                max_rows_per_intent=args.max_rows_per_intent,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {exc}")
            records.append(
                {"run_name": _run_name(overrides), "overrides": overrides, "error": str(exc)}
            )
            continue
        # Pretty-print per-gate
        for gate_key, m in rec["per_gate"].items():
            print(
                f"  {gate_key:10s}: top1={m['top1_accuracy']:.4f} "
                f"top3={m['top3_accuracy']:.4f} "
                f"macro_f1={m['macro_f1']:.4f}"
            )
        print(
            f"  chapter_head_top1={rec['default_gate_metrics']['chapter_head_top1']:.4f} "
            f"({rec['train_seconds']:.0f}s)"
        )
        records.append(rec)

    # ── Write summary ──
    json_path = args.out / f"twohead_sweep_{args.lang}.json"
    csv_path = args.out / f"twohead_sweep_{args.lang}.csv"
    json_path.write_text(
        json.dumps({"lang": args.lang, "records": records}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Flat CSV: one row per (run, gate)
    fieldnames = [
        "run_name",
        "chapter_head_weight",
        "supcon_weight",
        "transformer_learning_rate",
        "gate",
        "top1",
        "top3",
        "macro_f1",
        "chapter_head_top1",
        "train_seconds",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rec in records:
            if "error" in rec:
                continue
            ov = rec["overrides"]
            base = {
                "run_name": rec["run_name"],
                "chapter_head_weight": ov["chapter_head_weight"],
                "supcon_weight": ov["supcon_weight"],
                "transformer_learning_rate": ov["transformer_learning_rate"],
                "train_seconds": rec["train_seconds"],
            }
            for gate_key, m in rec["per_gate"].items():
                gate_val = float(gate_key.split("_")[1])
                w.writerow(
                    {
                        **base,
                        "gate": gate_val,
                        "top1": round(m["top1_accuracy"], 4)
                        if m.get("top1_accuracy") is not None
                        else "",
                        "top3": round(m["top3_accuracy"], 4)
                        if m.get("top3_accuracy") is not None
                        else "",
                        "macro_f1": round(m["macro_f1"], 4)
                        if m.get("macro_f1") is not None
                        else "",
                        "chapter_head_top1": round(m["chapter_head_top1"], 4)
                        if m.get("chapter_head_top1") is not None
                        else "",
                    }
                )

    # ── Leaderboard ──
    print(f"\n{'=' * 70}")
    print("LEADERBOARD (sorted by macro_f1 desc)")
    print(f"{'=' * 70}")
    flat: list[tuple[dict[str, Any], str, dict[str, Any]]] = []
    for rec in records:
        if "error" in rec:
            continue
        for gate_key, m in rec["per_gate"].items():
            flat.append((rec["overrides"], gate_key, m))
    flat.sort(key=lambda t: t[2].get("macro_f1") or 0.0, reverse=True)
    print(f"  {'overrides':<55} {'gate':<10} {'top1':<8} {'top3':<8} {'macro_f1':<8}")
    for ov, gate_key, m in flat[:15]:
        ov_str = " ".join(f"{k.split('_')[0][:4]}={v:g}" for k, v in ov.items())
        print(
            f"  {ov_str:<55} {gate_key:<10} "
            f"{(m.get('top1_accuracy') or 0):.4f}  "
            f"{(m.get('top3_accuracy') or 0):.4f}  "
            f"{(m.get('macro_f1') or 0):.4f}"
        )

    print(f"\nWrote: {json_path}")
    print(f"Wrote: {csv_path}")

    if not args.keep_models and scratch_dir.exists():
        shutil.rmtree(scratch_dir, ignore_errors=True)
        print(f"Cleaned scratch dir: {scratch_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
