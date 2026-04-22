"""ONNX export roundtrip test for the M3 transformer classifier.

Trains a tiny 2-class model, exports to ONNX (fp32 and INT8), and asserts
the ONNX outputs match PyTorch within tight numerical tolerances.

Marked ``slow`` — downloads tiny HF weights and runs a 1-epoch fit on CPU.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


@pytest.mark.slow
def test_export_to_onnx_roundtrip(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    pytest.importorskip("onnx")
    ort = pytest.importorskip("onnxruntime")

    from dataclasses import replace

    from football_betting.config import SUPPORT_CFG
    from football_betting.support.transformer_model import (
        TransformerIntentClassifier,
        export_to_onnx,
    )

    backbone = "hf-internal-testing/tiny-random-BertModel"
    try:
        transformers.AutoTokenizer.from_pretrained(backbone)
        transformers.AutoModelForSequenceClassification.from_pretrained(
            backbone, num_labels=2
        )
    except Exception as exc:  # pragma: no cover — offline CI
        pytest.skip(f"tiny HF model unavailable: {exc}")

    cfg = replace(
        SUPPORT_CFG,
        transformer_epochs=1,
        transformer_batch_size=4,
        transformer_max_seq_length=16,
        transformer_warmup_ratio=0.0,
        transformer_early_stop_patience=0,
        supcon_weight=0.0,  # simpler loss surface → deterministic-enough
    )
    X = [
        "value bet explained",
        "what is a value bet",
        "define value bet",
        "explain value bet",
        "value bet meaning",
        "what is kelly",
        "kelly criterion explained",
        "define kelly",
        "kelly meaning",
        "explain kelly",
    ]
    y = ["value_bet"] * 5 + ["kelly"] * 5

    clf = TransformerIntentClassifier(lang="en", cfg=cfg, backbone=backbone)
    clf.fit(X, y, verbose=False)

    # ── Reference logits from PyTorch (CPU, eval mode) ──
    clf._model.to("cpu")
    clf._device = torch.device("cpu")
    clf._model.eval()

    probe = [
        "what is a value bet",
        "tell me about kelly",
        "random unrelated text that should still produce logits",
    ]
    batch = clf._tokenizer(
        probe,
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=cfg.transformer_max_seq_length,
    )
    with torch.no_grad():
        torch_logits = (
            clf._model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            )
            .logits.detach()
            .cpu()
            .numpy()
        )

    # ── fp32 ONNX export ──
    fp32_path = tmp_path / "model.onnx"
    returned_fp32 = export_to_onnx(clf, fp32_path, int8=False)
    assert returned_fp32 == fp32_path
    assert fp32_path.exists() and fp32_path.stat().st_size > 0

    sess_fp32 = ort.InferenceSession(
        str(fp32_path), providers=["CPUExecutionProvider"]
    )
    onnx_fp32_logits = sess_fp32.run(
        ["logits"],
        {
            "input_ids": batch["input_ids"].numpy(),
            "attention_mask": batch["attention_mask"].numpy(),
        },
    )[0]

    assert onnx_fp32_logits.shape == torch_logits.shape
    fp32_diff = float(np.abs(onnx_fp32_logits - torch_logits).max())
    assert fp32_diff < 1e-3, f"fp32 ONNX diff too high: {fp32_diff}"
    # Argmax must match exactly.
    np.testing.assert_array_equal(
        onnx_fp32_logits.argmax(axis=1), torch_logits.argmax(axis=1)
    )


@pytest.mark.slow
def test_export_to_onnx_int8_tolerance(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    pytest.importorskip("onnx")
    ort = pytest.importorskip("onnxruntime")
    pytest.importorskip("onnxruntime.quantization")

    from dataclasses import replace

    from football_betting.config import SUPPORT_CFG
    from football_betting.support.transformer_model import (
        TransformerIntentClassifier,
        export_to_onnx,
    )

    backbone = "hf-internal-testing/tiny-random-BertModel"
    try:
        transformers.AutoTokenizer.from_pretrained(backbone)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"tiny HF model unavailable: {exc}")

    cfg = replace(
        SUPPORT_CFG,
        transformer_epochs=1,
        transformer_batch_size=4,
        transformer_max_seq_length=16,
        transformer_warmup_ratio=0.0,
        transformer_early_stop_patience=0,
        supcon_weight=0.0,
    )
    X = ["value bet"] * 6 + ["kelly criterion"] * 6
    y = ["value_bet"] * 6 + ["kelly"] * 6

    clf = TransformerIntentClassifier(lang="en", cfg=cfg, backbone=backbone)
    clf.fit(X, y, verbose=False)

    clf._model.to("cpu")
    clf._device = torch.device("cpu")
    clf._model.eval()

    probe = ["value bet", "kelly criterion"]
    batch = clf._tokenizer(
        probe,
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=cfg.transformer_max_seq_length,
    )
    with torch.no_grad():
        torch_logits = (
            clf._model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            )
            .logits.detach()
            .cpu()
            .numpy()
        )

    fp32_path = tmp_path / "model.onnx"
    int8_path = export_to_onnx(clf, fp32_path, int8=True)
    # int8=True returns a different path (.int8.onnx) next to the fp32 file.
    assert int8_path != fp32_path
    assert int8_path.exists() and int8_path.stat().st_size > 0

    sess_int8 = ort.InferenceSession(
        str(int8_path), providers=["CPUExecutionProvider"]
    )
    onnx_int8_logits = sess_int8.run(
        ["logits"],
        {
            "input_ids": batch["input_ids"].numpy(),
            "attention_mask": batch["attention_mask"].numpy(),
        },
    )[0]

    # INT8 tolerance is much looser — we only require that logits stay within
    # a sane neighbourhood and that top-1 class assignment still matches on
    # the canonical probes the model was actually trained on.
    int8_diff = float(np.abs(onnx_int8_logits - torch_logits).max())
    assert int8_diff < 5e-1, f"int8 ONNX diff too high: {int8_diff}"
    np.testing.assert_array_equal(
        onnx_int8_logits.argmax(axis=1), torch_logits.argmax(axis=1)
    )
