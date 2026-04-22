"""Rebuild the aggregated ``support_intent_transformer_metrics.json``.

Collects the per-language metric JSONs (v0.3.4 schema) and composes a
fresh aggregated report. Useful after single-language retraining that
bypasses the ``train_transformer_all`` aggregator.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_betting.config import SUPPORT_CFG, SUPPORT_MODELS_DIR
from football_betting.support.trainer import _describe_device, _git_sha


def main(langs: list[str]) -> Path:
    per_language: list[dict] = []
    for lg in langs:
        p = SUPPORT_MODELS_DIR / SUPPORT_CFG.transformer_metrics_filename.replace(
            ".json", f"_{lg}.json"
        )
        if not p.exists():
            print(f"[skip] no per-lang metrics for {lg}: {p}")
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        entries = data.get("per_language", [])
        if entries:
            per_language.append(entries[0])
            m = entries[0].get("metrics", {})
            print(
                f"[{lg}] top1={m.get('top1_accuracy', float('nan')):.4f}  "
                f"macro_f1={m.get('macro_f1', float('nan')):.4f}"
            )

    report = {
        "per_language": per_language,
        "backend": "transformer",
        "include_ood": True,
        "seed": 42,
        "device": _describe_device(),
        "git_sha": _git_sha(),
        "config_version": "0.3.4",
    }
    out = SUPPORT_MODELS_DIR / SUPPORT_CFG.transformer_metrics_filename
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote aggregate: {out}")
    return out


if __name__ == "__main__":
    langs = sys.argv[1:] or ["de", "en", "es", "fr", "it"]
    main(langs)
