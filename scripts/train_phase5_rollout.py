"""Phase 5: fine-tune EN/ES/FR/IT (DE already trained).

Uses ``train_transformer_all`` with an explicit language subset so the
already-trained DE model is not overwritten. On failure of a single
language the aggregator continues with the next one.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_betting.support.trainer import train_transformer_all


def main() -> int:
    langs = ["en", "es", "fr", "it"]
    print(f"[phase5] training languages: {langs}")
    report = train_transformer_all(langs=langs, seed=42)
    n_ok = sum(1 for s in report.get("per_language", []) if s.get("metrics"))
    print(f"[phase5] done: {n_ok}/{len(langs)} languages trained successfully")
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
