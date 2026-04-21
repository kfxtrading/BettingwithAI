"""HuggingFace-backed intent classifier (M3).

Identical public surface to :class:`IntentClassifier` (``fit``,
``predict_topk``, ``predict_proba_batch``, ``evaluate``, ``save``, ``load``)
so the evaluation harness and the hierarchical wrapper can consume either
backend interchangeably.

The training loop combines standard Cross-Entropy with Supervised Contrastive
loss (:func:`football_betting.support.losses.sup_con_loss`) on the encoder's
pooled CLS representation, following the report's §5.1 recommendation for
maximising class separation on 100+ fine-grained intents.

All heavy deps (``torch``, ``transformers``) are imported lazily inside the
methods so ``import football_betting.support.transformer_model`` is cheap.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from football_betting.config import SUPPORT_CFG, SupportConfig
from football_betting.support.text import normalize


# ───────────────────────── Backbone resolution ─────────────────────────


def resolve_backbone(lang: str, cfg: SupportConfig = SUPPORT_CFG) -> str:
    """Return the HF model id to fine-tune for the given language."""
    mapping = dict(cfg.transformer_backbone_by_lang)
    return mapping.get(lang, cfg.transformer_default_backbone)


# ───────────────────────── Helpers ─────────────────────────


def _require_torch() -> Any:
    try:
        import torch  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "torch not installed — `pip install -e .[ml]`"
        ) from exc
    return torch


def _select_device(torch: Any) -> Any:
    """Pick the best available accelerator: CUDA → DirectML (AMD/Win) → CPU."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    try:
        import torch_directml  # type: ignore[import-not-found]

        return torch_directml.device()
    except Exception:  # noqa: BLE001
        return torch.device("cpu")


def _require_transformers() -> Any:
    try:
        import transformers  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "transformers not installed — `pip install -e .[support-aug]`"
        ) from exc
    return transformers


@dataclass(frozen=True, slots=True)
class TransformerPrediction:
    """Single ranked prediction produced by :class:`TransformerIntentClassifier`."""

    intent_id: str
    score: float


# ───────────────────────── Classifier ─────────────────────────


@dataclass(slots=True)
class TransformerIntentClassifier:
    """Fine-tuned encoder classifier with hybrid CE + SupCon loss."""

    lang: str
    cfg: SupportConfig = SUPPORT_CFG
    backbone: str | None = None
    classes_: list[str] = field(default_factory=list)
    # Lazy state — populated by fit/load:
    _tokenizer: Any = None
    _model: Any = None
    _device: Any = None

    # ───────────────────────── Training ─────────────────────────

    def fit(
        self,
        X: list[str],
        y: list[str],
        *,
        X_val: list[str] | None = None,
        y_val: list[str] | None = None,
        verbose: bool = True,
    ) -> dict[str, Any]:
        """Fine-tune the backbone on (X, y) with CE + SupCon hybrid loss."""
        if len(X) != len(y):
            raise ValueError(f"X/y length mismatch: {len(X)} vs {len(y)}")
        if len(X) < 10:
            raise ValueError(f"Too few training samples: {len(X)}")

        torch = _require_torch()
        transformers = _require_transformers()
        from football_betting.support.losses import sup_con_loss

        backbone = self.backbone or resolve_backbone(self.lang, self.cfg)
        self.backbone = backbone

        # ── Label mapping ──
        self.classes_ = sorted(set(y))
        label2id = {lbl: i for i, lbl in enumerate(self.classes_)}
        id2label = {i: lbl for lbl, i in label2id.items()}

        # ── Tokeniser & model ──
        tokenizer = transformers.AutoTokenizer.from_pretrained(backbone, use_fast=True)
        model = transformers.AutoModelForSequenceClassification.from_pretrained(
            backbone,
            num_labels=len(self.classes_),
            id2label=id2label,
            label2id=label2id,
            problem_type="single_label_classification",
        )
        device = _select_device(torch)
        model.to(device)

        self._tokenizer = tokenizer
        self._model = model
        self._device = device

        # ── Dataset ──
        X_norm = [normalize(x) for x in X]
        y_ids = [label2id[lbl] for lbl in y]
        enc = tokenizer(
            X_norm,
            padding=True,
            truncation=True,
            max_length=self.cfg.transformer_max_seq_length,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"]
        attention_mask = enc["attention_mask"]
        labels = torch.tensor(y_ids, dtype=torch.long)

        dataset = torch.utils.data.TensorDataset(input_ids, attention_mask, labels)
        loader = torch.utils.data.DataLoader(
            dataset,
            batch_size=self.cfg.transformer_batch_size,
            shuffle=True,
        )

        # ── Optimiser / scheduler ──
        no_decay = ("bias", "LayerNorm.weight")
        grouped = [
            {
                "params": [
                    p for n, p in model.named_parameters()
                    if not any(nd in n for nd in no_decay)
                ],
                "weight_decay": self.cfg.transformer_weight_decay,
            },
            {
                "params": [
                    p for n, p in model.named_parameters()
                    if any(nd in n for nd in no_decay)
                ],
                "weight_decay": 0.0,
            },
        ]
        optimizer = torch.optim.AdamW(
            grouped, lr=self.cfg.transformer_learning_rate
        )
        total_steps = max(1, len(loader) * self.cfg.transformer_epochs)
        warmup_steps = int(self.cfg.transformer_warmup_ratio * total_steps)
        scheduler = transformers.get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
        )

        ce_loss_fn = torch.nn.CrossEntropyLoss()

        # ── Training loop with early stopping on val macro-F1 ──
        best_val_f1 = -1.0
        best_state: dict[str, Any] | None = None
        patience_left = self.cfg.transformer_early_stop_patience
        history: list[dict[str, float]] = []

        for epoch in range(self.cfg.transformer_epochs):
            model.train()
            epoch_loss = 0.0
            epoch_ce = 0.0
            epoch_supcon = 0.0
            n_batches = 0
            for batch_ids, batch_mask, batch_labels in loader:
                batch_ids = batch_ids.to(device)
                batch_mask = batch_mask.to(device)
                batch_labels = batch_labels.to(device)

                optimizer.zero_grad()
                outputs = model(
                    input_ids=batch_ids,
                    attention_mask=batch_mask,
                    output_hidden_states=True,
                )
                logits = outputs.logits
                ce = ce_loss_fn(logits, batch_labels)

                # Pooled CLS features for SupCon.
                hidden = outputs.hidden_states[-1]  # (B, T, H)
                pooled = hidden[:, 0, :]            # CLS
                sc = sup_con_loss(
                    pooled, batch_labels, temperature=self.cfg.supcon_temperature
                )

                loss = self.cfg.ce_weight * ce + self.cfg.supcon_weight * sc
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()

                epoch_loss += float(loss.item())
                epoch_ce += float(ce.item())
                epoch_supcon += float(sc.item())
                n_batches += 1

            row = {
                "epoch": float(epoch + 1),
                "train_loss": epoch_loss / max(1, n_batches),
                "train_ce": epoch_ce / max(1, n_batches),
                "train_supcon": epoch_supcon / max(1, n_batches),
            }

            # Evaluation / early stop.
            if X_val and y_val:
                val_metrics = self.evaluate(X_val, y_val)
                f1 = val_metrics.get("macro_f1") or 0.0
                row["val_top1"] = float(val_metrics.get("top1_accuracy") or 0.0)
                row["val_macro_f1"] = float(f1)
                if f1 > best_val_f1:
                    best_val_f1 = float(f1)
                    best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                    patience_left = self.cfg.transformer_early_stop_patience
                else:
                    patience_left -= 1
            history.append(row)
            if verbose:
                print(f"[{self.lang}] epoch {epoch + 1}: {row}")
            if X_val and patience_left < 0:
                break

        if best_state is not None:
            model.load_state_dict(best_state)

        return {
            "n_samples": len(X),
            "n_classes": len(self.classes_),
            "backbone": backbone,
            "best_val_macro_f1": None if best_val_f1 < 0 else best_val_f1,
            "history": history,
        }

    # ───────────────────────── Inference ─────────────────────────

    def _ensure_loaded(self) -> None:
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Classifier not trained / loaded.")

    def predict(self, text: str) -> TransformerPrediction:
        top = self.predict_topk(text, k=1)
        return top[0]

    def predict_topk(
        self, text: str, k: int | None = None
    ) -> list[TransformerPrediction]:
        self._ensure_loaded()
        kk = k if k is not None else self.cfg.default_topk
        kk = max(1, min(kk, len(self.classes_)))
        probs = self.predict_proba_batch([text])[0]
        idx = np.argsort(probs)[::-1][:kk]
        return [
            TransformerPrediction(
                intent_id=self.classes_[int(i)], score=float(probs[int(i)])
            )
            for i in idx
        ]

    def predict_proba_batch(self, texts: list[str]) -> np.ndarray:
        self._ensure_loaded()
        torch = _require_torch()
        assert self._model is not None and self._tokenizer is not None
        self._model.eval()

        normed = [normalize(t) for t in texts]
        batch_size = self.cfg.transformer_eval_batch_size
        out: list[np.ndarray] = []
        with torch.no_grad():
            for i in range(0, len(normed), batch_size):
                chunk = normed[i : i + batch_size]
                enc = self._tokenizer(
                    chunk,
                    padding=True,
                    truncation=True,
                    max_length=self.cfg.transformer_max_seq_length,
                    return_tensors="pt",
                )
                enc = {k: v.to(self._device) for k, v in enc.items()}
                logits = self._model(**enc).logits
                probs = torch.softmax(logits, dim=-1).cpu().numpy()
                out.append(probs)
        return np.concatenate(out, axis=0) if out else np.zeros((0, len(self.classes_)))

    # ───────────────────────── Evaluation ─────────────────────────

    def evaluate(
        self,
        X_val: list[str],
        y_val: list[str],
        chapters: list[str] | None = None,
    ) -> dict[str, Any]:
        """Top-1 / top-3 accuracy and macro-F1. Matches IntentClassifier schema."""
        from collections import defaultdict

        from sklearn.metrics import f1_score

        if not X_val:
            return {
                "n_val": 0,
                "top1_accuracy": None,
                "top3_accuracy": None,
                "macro_f1": None,
                "per_chapter_top1": {},
            }

        probs = self.predict_proba_batch(X_val)
        assert probs.shape[1] == len(self.classes_)
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}

        top3_idx = np.argsort(probs, axis=1)[:, ::-1][:, :3]
        top1_preds: list[str] = []
        top1_hits = 0
        top3_hits = 0
        per_chap_total: dict[str, int] = defaultdict(int)
        per_chap_hits: dict[str, int] = defaultdict(int)

        for i, true_id in enumerate(y_val):
            top1 = int(top3_idx[i, 0])
            pred_id = self.classes_[top1]
            top1_preds.append(pred_id)
            true_idx = class_to_idx.get(true_id)
            if true_idx is None:
                continue
            if top1 == true_idx:
                top1_hits += 1
            if true_idx in top3_idx[i].tolist():
                top3_hits += 1
            if chapters is not None:
                chap = chapters[i]
                per_chap_total[chap] += 1
                if top1 == true_idx:
                    per_chap_hits[chap] += 1

        macro_f1 = float(
            f1_score(y_val, top1_preds, average="macro", zero_division=0.0)
        )
        per_chapter_top1 = {
            chap: per_chap_hits[chap] / per_chap_total[chap]
            for chap in per_chap_total
            if per_chap_total[chap] > 0
        }
        return {
            "n_val": len(y_val),
            "top1_accuracy": top1_hits / len(y_val),
            "top3_accuracy": top3_hits / len(y_val),
            "macro_f1": macro_f1,
            "per_chapter_top1": per_chapter_top1,
        }

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, directory: Path) -> None:
        """Persist tokenizer + model + metadata to a HF-style directory."""
        self._ensure_loaded()
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        assert self._model is not None and self._tokenizer is not None
        self._model.save_pretrained(directory)
        self._tokenizer.save_pretrained(directory)
        meta = {
            "lang": self.lang,
            "backbone": self.backbone,
            "classes_": list(self.classes_),
        }
        (directory / "support_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @classmethod
    def load(
        cls, directory: Path, cfg: SupportConfig = SUPPORT_CFG
    ) -> TransformerIntentClassifier:
        torch = _require_torch()
        transformers = _require_transformers()
        directory = Path(directory)
        meta = json.loads(
            (directory / "support_meta.json").read_text(encoding="utf-8")
        )
        inst = cls(
            lang=str(meta["lang"]),
            cfg=cfg,
            backbone=str(meta.get("backbone", "") or None),
            classes_=list(meta["classes_"]),
        )
        inst._tokenizer = transformers.AutoTokenizer.from_pretrained(directory)
        inst._model = transformers.AutoModelForSequenceClassification.from_pretrained(
            directory
        )
        inst._device = _select_device(torch)
        inst._model.to(inst._device)
        inst._model.eval()
        return inst


# ───────────────────────── ONNX export ─────────────────────────


def export_to_onnx(
    clf: TransformerIntentClassifier,
    output_path: Path,
    *,
    opset: int | None = None,
    int8: bool | None = None,
) -> Path:
    """Export a fine-tuned classifier to an ONNX file (optionally INT8)."""
    torch = _require_torch()
    clf._ensure_loaded()
    assert clf._model is not None and clf._tokenizer is not None
    cfg = clf.cfg
    opset_v = opset if opset is not None else cfg.onnx_opset
    do_int8 = int8 if int8 is not None else cfg.onnx_int8_quantize

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Dummy inputs for tracing.
    dummy = clf._tokenizer(
        "dummy input",
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=cfg.transformer_max_seq_length,
    )
    input_ids = dummy["input_ids"].to(clf._device)
    attention_mask = dummy["attention_mask"].to(clf._device)

    clf._model.eval()
    torch.onnx.export(
        clf._model,
        (input_ids, attention_mask),
        str(output_path),
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "seq"},
            "attention_mask": {0: "batch", 1: "seq"},
            "logits": {0: "batch"},
        },
        opset_version=opset_v,
        do_constant_folding=True,
    )

    if do_int8:
        try:
            from onnxruntime.quantization import QuantType, quantize_dynamic  # type: ignore[import-not-found]
        except Exception:  # noqa: BLE001 — optional dep
            return output_path
        quant_path = output_path.with_suffix(".int8.onnx")
        quantize_dynamic(
            str(output_path), str(quant_path), weight_type=QuantType.QInt8
        )
        return quant_path
    return output_path


__all__ = [
    "TransformerIntentClassifier",
    "TransformerPrediction",
    "export_to_onnx",
    "resolve_backbone",
]
