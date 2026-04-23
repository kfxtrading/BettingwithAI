"""Phase 5 / v3: fine-tune all 5 languages on dataset_augmented_v3.jsonl.

The v3 dataset (LLM-paraphrase augmentation via Ollama qwen2.5:7b-instruct)
adds ~44k diverse paraphrases on top of v2's noise-only variants. We re-train
all locales (DE included) so every language benefits from the new data.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_betting.support.trainer import train_transformer_all


def main() -> int:
    langs = ["de", "en", "es", "fr", "it"]
    print(f"[v3-rollout] training languages: {langs}")
    report = train_transformer_all(langs=langs, seed=42)
    n_ok = sum(1 for s in report.get("per_language", []) if s.get("metrics"))
    print(f"[v3-rollout] done: {n_ok}/{len(langs)} languages trained successfully")
    for stats in report.get("per_language", []):
        lg = stats.get("lang", "?")
        m = stats.get("metrics", {}) or {}
        c = stats.get("calibration", {}) or {}
        print(
            f"  [{lg}] top1={m.get('top1_accuracy', 'nan'):.4f} "
            f"macro_f1={m.get('macro_f1', 'nan'):.4f} "
            f"ECE {c.get('ece_before', 'nan'):.4f} -> {c.get('ece_after', 'nan'):.4f}"
        )
    return 0 if n_ok == len(langs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
