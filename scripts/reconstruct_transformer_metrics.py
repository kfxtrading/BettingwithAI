"""Reconstruct the v0.3.4 metrics report for an existing single-language run.

Used once to backfill ``support_intent_transformer_metrics_de.json`` after
the initial DE training (which predated the trainer's per-language report
write). Safe to run any time — it loads the saved model and re-evaluates
on the same stratified validation split.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_betting.config import SUPPORT_CFG, SUPPORT_DATA_DIR, SUPPORT_MODELS_DIR
from football_betting.support.dataset import load_dataset, stratified_split
from football_betting.support.trainer import _describe_device, _git_sha
from football_betting.support.transformer_model import TransformerIntentClassifier


def reconstruct(lang: str, *, seed: int = 42, include_ood: bool = True) -> Path:
    ds_path = SUPPORT_DATA_DIR / SUPPORT_CFG.augmented_v2_filename
    if not ds_path.exists():
        ds_path = SUPPORT_DATA_DIR / SUPPORT_CFG.dataset_filename
    rows = load_dataset(path=ds_path, lang=lang, include_ood=include_ood)
    split = stratified_split(rows)
    print(f"[{lang}] loaded {len(rows)} rows | train={split.n_train} val={split.n_val}")

    model_dir = SUPPORT_MODELS_DIR / SUPPORT_CFG.transformer_model_dirname_template.format(lang=lang)
    clf = TransformerIntentClassifier.load(model_dir)
    print(f"[{lang}] loaded model from {model_dir}")

    metrics = clf.evaluate(split.X_val, split.y_val)
    print(
        f"[{lang}] top1={metrics.get('top1_accuracy', float('nan')):.4f}  "
        f"top3={metrics.get('top3_accuracy', float('nan')):.4f}  "
        f"macro_f1={metrics.get('macro_f1', float('nan')):.4f}"
    )

    calib_info: dict = {"fitted": False}
    temp_path = model_dir / "temperature.json"
    if temp_path.exists():
        with temp_path.open("r", encoding="utf-8") as fh:
            calib_info = {"fitted": True, **json.load(fh)}

    payload = {
        "lang": lang,
        "backend": "transformer",
        "backbone": clf.backbone,
        "n_train": split.n_train,
        "n_val": split.n_val,
        "n_classes": split.n_classes,
        "metrics": metrics,
        "calibration": calib_info,
        "seed": {"seed": seed, "reconstructed": True},
        "device": _describe_device(),
        "git_sha": _git_sha(),
        "model_path": str(model_dir),
        "fit_info": {"reconstructed": True, "note": "metrics reconstructed post-hoc"},
    }
    report = {
        "per_language": [payload],
        "backend": "transformer",
        "include_ood": include_ood,
        "seed": seed,
        "device": _describe_device(),
        "git_sha": _git_sha(),
        "config_version": "0.3.4",
    }
    out = SUPPORT_MODELS_DIR / SUPPORT_CFG.transformer_metrics_filename.replace(
        ".json", f"_{lang}.json"
    )
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[{lang}] wrote {out}")
    return out


if __name__ == "__main__":
    lang = sys.argv[1] if len(sys.argv) > 1 else "de"
    reconstruct(lang)
