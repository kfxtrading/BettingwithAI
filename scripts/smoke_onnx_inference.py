"""Smoke-test that exported ONNX files produce sensible predictions.

For each language: load model.int8.onnx + tokenizer, push a short probe,
print top-3 predictions. Fast sanity check after export.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

from football_betting.config import SUPPORT_CFG, SUPPORT_MODELS_DIR

PROBES = {
    "de": "Wie funktioniert das Kelly-Kriterium?",
    "en": "How does the Kelly criterion work?",
    "es": "¿Cómo funciona el criterio de Kelly?",
    "fr": "Comment fonctionne le critère de Kelly ?",
    "it": "Come funziona il criterio di Kelly?",
}


def smoke(lang: str) -> bool:
    model_dir = SUPPORT_MODELS_DIR / SUPPORT_CFG.transformer_model_dirname_template.format(
        lang=lang
    )
    onnx_path = model_dir / "model.int8.onnx"
    if not onnx_path.exists():
        onnx_path = model_dir / "model.onnx"
    if not onnx_path.exists():
        print(f"[{lang}] SKIP: no ONNX under {model_dir}")
        return False

    sess_opts = ort.SessionOptions()
    sess_opts.intra_op_num_threads = 1
    sess = ort.InferenceSession(
        str(onnx_path), sess_options=sess_opts, providers=["CPUExecutionProvider"]
    )
    tok = AutoTokenizer.from_pretrained(str(model_dir))

    # Load classes_ from support_meta.json
    import json as _json

    meta = _json.loads((model_dir / "support_meta.json").read_text(encoding="utf-8"))
    classes = meta["classes_"]

    query = PROBES[lang]
    enc = tok(
        query,
        return_tensors="np",
        padding="max_length",
        truncation=True,
        max_length=SUPPORT_CFG.transformer_max_seq_length,
    )
    logits = sess.run(
        ["logits"],
        {
            "input_ids": enc["input_ids"].astype(np.int64),
            "attention_mask": enc["attention_mask"].astype(np.int64),
        },
    )[0]
    probs = np.exp(logits - logits.max(axis=-1, keepdims=True))
    probs = probs / probs.sum(axis=-1, keepdims=True)
    top3 = np.argsort(probs[0])[::-1][:3]
    print(f"[{lang}] {query!r}")
    for rank, idx in enumerate(top3, 1):
        print(f"   {rank}. {classes[idx]:<40s} p={probs[0, idx]:.4f}")
    return True


if __name__ == "__main__":
    langs = sys.argv[1:] or ["de", "en", "es", "it"]
    ok = sum(1 for lg in langs if smoke(lg))
    print(f"\nDone: {ok}/{len(langs)} languages")
