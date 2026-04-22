"""Smoke tests for :mod:`football_betting.support.transformer_model` (M3).

Heavy-dependency tests are skipped when torch / transformers are missing.
The lightweight tests here focus on: (a) module importability without torch,
(b) :func:`resolve_backbone` config wiring, and (c) end-to-end fit/predict
when the optional deps are installed (tiny backbone, 2 intents).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from football_betting.config import SUPPORT_CFG
from football_betting.support.transformer_model import resolve_backbone


def test_resolve_backbone_default_and_overrides() -> None:
    # torch-directml 0.2.5 rejects ModernGBERT's backward pass on AMD,
    # so DE falls back to XLM-R — the per-language map reflects that.
    assert resolve_backbone("de") == SUPPORT_CFG.transformer_default_backbone
    assert resolve_backbone("en") == SUPPORT_CFG.transformer_default_backbone
    assert resolve_backbone("zz") == SUPPORT_CFG.transformer_default_backbone


def test_module_imports_without_torch() -> None:
    from football_betting.support import transformer_model as tm

    assert hasattr(tm, "TransformerIntentClassifier")
    assert hasattr(tm, "export_to_onnx")


# ───────────────────────── Heavy end-to-end (opt-in) ─────────────────────────


@pytest.mark.slow
def test_transformer_fit_predict_smoke(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")

    from dataclasses import replace

    from football_betting.support.transformer_model import (
        TransformerIntentClassifier,
    )

    # Use the smallest public HF encoder we can rely on.
    try:
        tok = transformers.AutoTokenizer.from_pretrained("hf-internal-testing/tiny-random-BertModel")
        transformers.AutoModelForSequenceClassification.from_pretrained(
            "hf-internal-testing/tiny-random-BertModel", num_labels=2
        )
    except Exception as exc:  # pragma: no cover — offline CI
        pytest.skip(f"tiny HF model unavailable: {exc}")
    del tok

    cfg = replace(
        SUPPORT_CFG,
        transformer_epochs=1,
        transformer_batch_size=4,
        transformer_max_seq_length=16,
        transformer_warmup_ratio=0.0,
        transformer_early_stop_patience=0,
    )
    X = [
        "what is a value bet",
        "explain value bet",
        "define value bet",
        "value bet meaning",
        "value bet please",
        "tell me about value bets",
        "what is the kelly criterion",
        "explain kelly",
        "define kelly",
        "kelly criterion meaning",
        "how does kelly work",
        "kelly staking please",
    ]
    y = ["value_bet"] * 6 + ["kelly"] * 6

    clf = TransformerIntentClassifier(
        lang="en",
        cfg=cfg,
        backbone="hf-internal-testing/tiny-random-BertModel",
    )
    info = clf.fit(X, y, verbose=False)
    assert info["n_classes"] == 2
    preds = clf.predict_topk("what is kelly", k=2)
    assert len(preds) == 2
    assert preds[0].intent_id in {"kelly", "value_bet"}

    probs = clf.predict_proba_batch(["kelly formula", "what is value bet"])
    assert probs.shape == (2, 2)

    # Save / load roundtrip.
    target = tmp_path / "support_transformer_en"
    clf.save(target)
    loaded = TransformerIntentClassifier.load(target, cfg=cfg)
    assert loaded.classes_ == clf.classes_
    preds2 = loaded.predict_topk("what is kelly", k=2)
    assert preds2[0].intent_id == preds[0].intent_id
