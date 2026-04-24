"""Two-headed transformer intent classifier (chapter + intent).

Shares a single XLM-R encoder with two linear heads:

* **Chapter head** – 9-class coarse classifier (``basics``, ``strategy``,
  ``ai``, ``mistakes``, ``platform``, ``market``, ``profit``, ``analysis``,
  ``general``).
* **Intent head** – full 269-class fine-grained classifier.

The loss is a weighted sum::

    L = ce_weight · CE_intent
      + chapter_head_weight · CE_chapter
      + supcon_weight · SupCon(intent)

Rationale (v3 confusion findings, April 2026): 95–100% of fine-grained
confusions stay *within* the same chapter. Adding a coarse chapter head
forces the encoder to first separate chapters cleanly, so the fine head
operates on a well-organised latent space.

At inference we expose:

* ``predict_proba_batch(texts)`` – intent probabilities (same contract as
  :class:`TransformerIntentClassifier`), so the evaluation harness, the
  calibration pipeline and the confusion analysis scripts can consume a
  two-head model without modification.
* ``predict_chapter_proba_batch(texts)`` – chapter head softmax.
* An optional *chapter gate* (``cfg.two_head_chapter_gate``): when the
  chapter head's top-1 probability exceeds the gate, intent logits outside
  that chapter are zeroed out before re-normalisation.

All heavy deps (``torch``, ``transformers``) are imported lazily so
``import football_betting.support.two_head_transformer`` stays cheap.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from football_betting.config import SUPPORT_CFG, SupportConfig
from football_betting.support.text import normalize
from football_betting.support.transformer_model import (
    _require_torch,
    _require_transformers,
    _select_device,
    resolve_backbone,
)

# ───────────────────────── Helpers ─────────────────────────


def _ood_chapter() -> str:
    """Dedicated chapter bucket for the out-of-domain sentinel intent."""
    return "__ood__"


def _derive_chapter(intent_id: str, chapter_field: str | None = None) -> str:
    """Prefer the explicit ``chapter`` meta field; fall back to id-prefix."""
    if intent_id == "__ood__":
        return _ood_chapter()
    if chapter_field:
        return chapter_field
    # Fallback for rows without chapter meta (shouldn't happen on v2/v3 data).
    return intent_id.split("-", 1)[0]


# ───────────────────────── Torch module ─────────────────────────


def _build_torch_module(
    backbone: str,
    n_chapters: int,
    n_intents: int,
    dropout: float = 0.1,
) -> Any:
    """Return an ``nn.Module`` with encoder + chapter head + intent head."""
    torch = _require_torch()
    transformers = _require_transformers()

    encoder = transformers.AutoModel.from_pretrained(backbone, attn_implementation="eager")
    hidden_size = int(encoder.config.hidden_size)

    nn = torch.nn

    class TwoHead(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = encoder
            self.dropout = nn.Dropout(dropout)
            self.chapter_head = nn.Linear(hidden_size, n_chapters)
            self.intent_head = nn.Linear(hidden_size, n_intents)

        def forward(self, input_ids: Any, attention_mask: Any) -> tuple[Any, Any, Any]:
            out = self.encoder(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=False,
            )
            # Pooled CLS representation (xlm-roberta returns a `pooler_output`
            # by default; fall back to CLS of last_hidden_state if missing).
            pooled = getattr(out, "pooler_output", None)
            if pooled is None:
                pooled = out.last_hidden_state[:, 0, :]
            feats = self.dropout(pooled)
            chap_logits = self.chapter_head(feats)
            int_logits = self.intent_head(feats)
            return chap_logits, int_logits, pooled

    return TwoHead()


# ───────────────────────── Prediction tuple ─────────────────────────


@dataclass(frozen=True, slots=True)
class TwoHeadPrediction:
    """Single ranked prediction produced by :class:`TwoHeadTransformerIntentClassifier`."""

    intent_id: str
    score: float
    chapter: str
    chapter_score: float


# ───────────────────────── Classifier ─────────────────────────


@dataclass(slots=True)
class TwoHeadTransformerIntentClassifier:
    """Two-headed transformer classifier (chapter + intent, shared encoder)."""

    lang: str
    cfg: SupportConfig = SUPPORT_CFG
    backbone: str | None = None
    # Intent classes (kept as ``classes_`` for API parity with
    # :class:`TransformerIntentClassifier`).
    classes_: list[str] = field(default_factory=list)
    chapters_: list[str] = field(default_factory=list)
    intent_to_chapter_: dict[str, str] = field(default_factory=dict)

    # Lazy state:
    _tokenizer: Any = None
    _model: Any = None
    _device: Any = None

    # ───────────────────────── Training ─────────────────────────

    def fit(
        self,
        X: list[str],
        y: list[str],
        chapters: list[str],
        *,
        X_val: list[str] | None = None,
        y_val: list[str] | None = None,
        chapters_val: list[str] | None = None,
        verbose: bool = True,
    ) -> dict[str, Any]:
        """Fine-tune encoder + chapter head + intent head with weighted loss."""
        if len(X) != len(y) or len(X) != len(chapters):
            raise ValueError(f"X/y/chapters length mismatch: {len(X)}/{len(y)}/{len(chapters)}")
        if len(X) < 10:
            raise ValueError(f"Too few training samples: {len(X)}")

        torch = _require_torch()
        transformers = _require_transformers()
        from football_betting.support.losses import sup_con_loss

        backbone = self.backbone or resolve_backbone(self.lang, self.cfg)
        self.backbone = backbone

        # ── Label mappings ──
        self.classes_ = sorted(set(y))
        self.chapters_ = sorted(set(chapters))
        intent2id = {lbl: i for i, lbl in enumerate(self.classes_)}
        chap2id = {lbl: i for i, lbl in enumerate(self.chapters_)}
        self.intent_to_chapter_ = {intent: ch for intent, ch in zip(y, chapters, strict=True)}
        # Ensure every training intent has a known chapter (pin most-frequent).
        # (If conflicts arose we'd take the last write; fine for a clean taxonomy.)

        # ── Tokeniser + torch module ──
        tokenizer = transformers.AutoTokenizer.from_pretrained(backbone, use_fast=True)
        model = _build_torch_module(
            backbone=backbone,
            n_chapters=len(self.chapters_),
            n_intents=len(self.classes_),
        )
        device = _select_device(torch)
        model.to(device)

        self._tokenizer = tokenizer
        self._model = model
        self._device = device

        # ── Dataset ──
        X_norm = [normalize(x) for x in X]
        y_int = [intent2id[lbl] for lbl in y]
        y_chap = [chap2id[c] for c in chapters]

        enc = tokenizer(
            X_norm,
            padding=True,
            truncation=True,
            max_length=self.cfg.transformer_max_seq_length,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"]
        attention_mask = enc["attention_mask"]
        y_int_t = torch.tensor(y_int, dtype=torch.long)
        y_chap_t = torch.tensor(y_chap, dtype=torch.long)

        dataset = torch.utils.data.TensorDataset(input_ids, attention_mask, y_int_t, y_chap_t)
        loader = torch.utils.data.DataLoader(
            dataset, batch_size=self.cfg.transformer_batch_size, shuffle=True
        )

        # ── Optimiser / scheduler ──
        no_decay = ("bias", "LayerNorm.weight")
        grouped = [
            {
                "params": [
                    p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)
                ],
                "weight_decay": self.cfg.transformer_weight_decay,
            },
            {
                "params": [
                    p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)
                ],
                "weight_decay": 0.0,
            },
        ]
        optimizer = torch.optim.AdamW(grouped, lr=self.cfg.transformer_learning_rate)
        total_steps = max(1, len(loader) * self.cfg.transformer_epochs)
        warmup_steps = int(self.cfg.transformer_warmup_ratio * total_steps)
        scheduler = transformers.get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
        )

        ce = torch.nn.CrossEntropyLoss()

        best_val_f1 = -1.0
        best_state: dict[str, Any] | None = None
        patience_left = self.cfg.transformer_early_stop_patience
        history: list[dict[str, float]] = []

        for epoch in range(self.cfg.transformer_epochs):
            model.train()
            epoch_loss = 0.0
            epoch_ce_int = 0.0
            epoch_ce_chap = 0.0
            epoch_supcon = 0.0
            n_batches = 0
            for batch_ids, batch_mask, batch_int, batch_chap in loader:
                batch_ids = batch_ids.to(device)
                batch_mask = batch_mask.to(device)
                batch_int = batch_int.to(device)
                batch_chap = batch_chap.to(device)

                optimizer.zero_grad()
                chap_logits, int_logits, pooled = model(batch_ids, batch_mask)

                loss_int = ce(int_logits, batch_int)
                loss_chap = ce(chap_logits, batch_chap)
                loss_supcon = sup_con_loss(
                    pooled, batch_int, temperature=self.cfg.supcon_temperature
                )

                loss = (
                    self.cfg.ce_weight * loss_int
                    + self.cfg.chapter_head_weight * loss_chap
                    + self.cfg.supcon_weight * loss_supcon
                )
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()

                epoch_loss += float(loss.item())
                epoch_ce_int += float(loss_int.item())
                epoch_ce_chap += float(loss_chap.item())
                epoch_supcon += float(loss_supcon.item())
                n_batches += 1

            row = {
                "epoch": float(epoch + 1),
                "train_loss": epoch_loss / max(1, n_batches),
                "train_ce_intent": epoch_ce_int / max(1, n_batches),
                "train_ce_chapter": epoch_ce_chap / max(1, n_batches),
                "train_supcon": epoch_supcon / max(1, n_batches),
            }

            if X_val and y_val:
                val_metrics = self.evaluate(X_val, y_val, chapters=chapters_val)
                f1 = val_metrics.get("macro_f1") or 0.0
                row["val_top1"] = float(val_metrics.get("top1_accuracy") or 0.0)
                row["val_macro_f1"] = float(f1)
                row["val_chapter_top1"] = float(val_metrics.get("chapter_head_top1") or 0.0)
                if f1 > best_val_f1:
                    best_val_f1 = float(f1)
                    best_state = {
                        k: v.detach().cpu().clone() for k, v in model.state_dict().items()
                    }
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
            "n_intents": len(self.classes_),
            "n_chapters": len(self.chapters_),
            "backbone": backbone,
            "best_val_macro_f1": None if best_val_f1 < 0 else best_val_f1,
            "history": history,
        }

    # ───────────────────────── Inference ─────────────────────────

    def _ensure_loaded(self) -> None:
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Classifier not trained / loaded.")

    def _forward_batch(self, texts: list[str]) -> tuple[np.ndarray, np.ndarray]:
        """Return (chapter_logits, intent_logits) for a batch."""
        self._ensure_loaded()
        torch = _require_torch()
        assert self._model is not None and self._tokenizer is not None
        self._model.eval()

        normed = [normalize(t) for t in texts]
        batch_size = self.cfg.transformer_eval_batch_size
        chap_out: list[np.ndarray] = []
        int_out: list[np.ndarray] = []
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
                chap_logits, int_logits, _ = self._model(enc["input_ids"], enc["attention_mask"])
                chap_out.append(chap_logits.detach().cpu().numpy())
                int_out.append(int_logits.detach().cpu().numpy())
        if not chap_out:
            return (
                np.zeros((0, len(self.chapters_))),
                np.zeros((0, len(self.classes_))),
            )
        return np.concatenate(chap_out, axis=0), np.concatenate(int_out, axis=0)

    def predict_chapter_proba_batch(self, texts: list[str]) -> np.ndarray:
        chap_logits, _ = self._forward_batch(texts)
        # softmax
        e = np.exp(chap_logits - chap_logits.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)

    def predict_logits_batch(self, texts: list[str]) -> np.ndarray:
        """Intent logits (for temperature calibration parity)."""
        _, int_logits = self._forward_batch(texts)
        return int_logits

    def predict_proba_batch(
        self,
        texts: list[str],
        *,
        chapter_gate: float | None = None,
    ) -> np.ndarray:
        """Intent probabilities, optionally masked by a confident chapter head.

        When ``chapter_gate`` (default :attr:`cfg.two_head_chapter_gate`) is
        below 1.0, rows where the chapter head's top-1 prob exceeds the gate
        get their out-of-chapter intent logits set to ``-inf`` before softmax.
        """
        gate = chapter_gate if chapter_gate is not None else self.cfg.two_head_chapter_gate
        chap_logits, int_logits = self._forward_batch(texts)

        # Chapter softmax
        e_chap = np.exp(chap_logits - chap_logits.max(axis=1, keepdims=True))
        chap_probs = e_chap / e_chap.sum(axis=1, keepdims=True)
        chap_top = chap_probs.argmax(axis=1)
        chap_top_prob = chap_probs.max(axis=1)

        if gate < 1.0 and self.intent_to_chapter_ and chap_logits.shape[0]:
            # Build an (n_intents,) -> chapter_idx lookup once.
            chap2id = {c: i for i, c in enumerate(self.chapters_)}
            intent_chap_idx = np.array(
                [chap2id.get(self.intent_to_chapter_.get(cls, ""), -1) for cls in self.classes_],
                dtype=np.int64,
            )
            for row in range(int_logits.shape[0]):
                if chap_top_prob[row] >= gate:
                    bad = intent_chap_idx != int(chap_top[row])
                    if bad.any():
                        int_logits[row, bad] = -1e9

        e_int = np.exp(int_logits - int_logits.max(axis=1, keepdims=True))
        probs = e_int / e_int.sum(axis=1, keepdims=True)
        return probs

    def predict_topk(self, text: str, k: int | None = None) -> list[TwoHeadPrediction]:
        self._ensure_loaded()
        kk = k if k is not None else self.cfg.default_topk
        kk = max(1, min(kk, len(self.classes_)))
        chap_probs = self.predict_chapter_proba_batch([text])[0]
        probs = self.predict_proba_batch([text])[0]
        top_chap_i = int(chap_probs.argmax())
        top_chap = self.chapters_[top_chap_i] if self.chapters_ else ""
        top_chap_p = float(chap_probs[top_chap_i]) if self.chapters_ else 0.0
        idx = np.argsort(probs)[::-1][:kk]
        return [
            TwoHeadPrediction(
                intent_id=self.classes_[int(i)],
                score=float(probs[int(i)]),
                chapter=top_chap,
                chapter_score=top_chap_p,
            )
            for i in idx
        ]

    # ───────────────────────── Evaluation ─────────────────────────

    def evaluate(
        self,
        X_val: list[str],
        y_val: list[str],
        chapters: list[str] | None = None,
        *,
        top_confusions: int = 15,
    ) -> dict[str, Any]:
        """Same shape as :meth:`TransformerIntentClassifier.evaluate`.

        Additional keys: ``chapter_head_top1`` and ``chapter_head_macro_f1``
        (the chapter head's own accuracy, NOT the per-intent breakdown).
        """
        from collections import Counter, defaultdict

        from sklearn.metrics import f1_score

        if not X_val:
            return {
                "n_val": 0,
                "top1_accuracy": None,
                "top3_accuracy": None,
                "macro_f1": None,
                "per_chapter_top1": {},
                "per_chapter_macro_f1": {},
                "per_intent_f1": {},
                "top_confusions": [],
                "chapter_head_top1": None,
                "chapter_head_macro_f1": None,
            }

        chap_probs = self.predict_chapter_proba_batch(X_val)
        probs = self.predict_proba_batch(X_val)
        assert probs.shape[1] == len(self.classes_)
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}

        top3_idx = np.argsort(probs, axis=1)[:, ::-1][:, :3]
        top1_preds: list[str] = []
        top1_hits = 0
        top3_hits = 0
        per_chap_total: dict[str, int] = defaultdict(int)
        per_chap_hits: dict[str, int] = defaultdict(int)
        per_chap_true: dict[str, list[str]] = defaultdict(list)
        per_chap_pred: dict[str, list[str]] = defaultdict(list)
        confusions: Counter[tuple[str, str]] = Counter()

        for i, true_id in enumerate(y_val):
            top1 = int(top3_idx[i, 0])
            pred_id = self.classes_[top1]
            top1_preds.append(pred_id)
            true_idx = class_to_idx.get(true_id)
            if true_idx is None:
                continue
            if top1 == true_idx:
                top1_hits += 1
            else:
                confusions[(true_id, pred_id)] += 1
            if true_idx in top3_idx[i].tolist():
                top3_hits += 1
            if chapters is not None:
                chap = chapters[i]
                per_chap_total[chap] += 1
                per_chap_true[chap].append(true_id)
                per_chap_pred[chap].append(pred_id)
                if top1 == true_idx:
                    per_chap_hits[chap] += 1

        macro_f1 = float(f1_score(y_val, top1_preds, average="macro", zero_division=0.0))
        per_chapter_top1 = {
            chap: per_chap_hits[chap] / per_chap_total[chap]
            for chap in per_chap_total
            if per_chap_total[chap] > 0
        }
        per_chapter_macro_f1 = {
            chap: float(
                f1_score(
                    per_chap_true[chap],
                    per_chap_pred[chap],
                    average="macro",
                    zero_division=0.0,
                )
            )
            for chap in per_chap_total
            if per_chap_total[chap] > 0
        }
        per_intent_f1_raw = f1_score(
            y_val, top1_preds, labels=self.classes_, average=None, zero_division=0.0
        )
        per_intent_f1 = {
            intent: float(score)
            for intent, score in zip(self.classes_, per_intent_f1_raw, strict=False)
        }
        top_conf = [
            {"true": true_id, "pred": pred_id, "count": count}
            for (true_id, pred_id), count in confusions.most_common(top_confusions)
        ]

        # Chapter-head own accuracy (independent of the intent head).
        chap_head_top1: float | None = None
        chap_head_macro_f1: float | None = None
        if chapters is not None and self.chapters_:
            chap_idx = chap_probs.argmax(axis=1)
            chap_preds = [self.chapters_[int(i)] for i in chap_idx]
            hits = sum(1 for p, g in zip(chap_preds, chapters, strict=True) if p == g)
            chap_head_top1 = hits / len(chapters)
            chap_head_macro_f1 = float(
                f1_score(chapters, chap_preds, average="macro", zero_division=0.0)
            )

        return {
            "n_val": len(y_val),
            "top1_accuracy": top1_hits / len(y_val),
            "top3_accuracy": top3_hits / len(y_val),
            "macro_f1": macro_f1,
            "per_chapter_top1": per_chapter_top1,
            "per_chapter_macro_f1": per_chapter_macro_f1,
            "per_intent_f1": per_intent_f1,
            "top_confusions": top_conf,
            "chapter_head_top1": chap_head_top1,
            "chapter_head_macro_f1": chap_head_macro_f1,
        }

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, directory: Path) -> None:
        """Persist tokenizer + encoder + head weights + meta to ``directory``.

        Layout::

            <directory>/
              encoder/             HF pretrained save of the shared backbone
              tokenizer/           HF tokenizer save
              heads.pt             torch.save of chapter_head + intent_head state dicts
              support_meta.json    classes_, chapters_, intent_to_chapter_, backbone

        The encoder is temporarily moved to CPU (DirectML tensors cannot be
        introspected by safetensors), same pattern as
        :class:`TransformerIntentClassifier`.
        """
        self._ensure_loaded()
        torch = _require_torch()
        directory = Path(directory)
        (directory / "encoder").mkdir(parents=True, exist_ok=True)
        (directory / "tokenizer").mkdir(parents=True, exist_ok=True)
        assert self._model is not None and self._tokenizer is not None
        original_device = next(self._model.parameters()).device
        needs_cpu_move = str(original_device) != "cpu"
        try:
            if needs_cpu_move:
                self._model.to("cpu")
            self._model.encoder.save_pretrained(directory / "encoder")
            # Save head state dicts.
            torch.save(
                {
                    "chapter_head": self._model.chapter_head.state_dict(),
                    "intent_head": self._model.intent_head.state_dict(),
                },
                directory / "heads.pt",
            )
        finally:
            if needs_cpu_move:
                self._model.to(original_device)
        self._tokenizer.save_pretrained(directory / "tokenizer")
        meta = {
            "lang": self.lang,
            "backbone": self.backbone,
            "classes_": list(self.classes_),
            "chapters_": list(self.chapters_),
            "intent_to_chapter_": dict(self.intent_to_chapter_),
            "model_type": "two_head_transformer",
        }
        (directory / "support_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @classmethod
    def load(
        cls, directory: Path, cfg: SupportConfig = SUPPORT_CFG
    ) -> TwoHeadTransformerIntentClassifier:
        torch = _require_torch()
        transformers = _require_transformers()
        directory = Path(directory)
        meta = json.loads((directory / "support_meta.json").read_text(encoding="utf-8"))
        if meta.get("model_type") != "two_head_transformer":
            raise ValueError(
                f"{directory} is not a two_head_transformer model "
                f"(model_type={meta.get('model_type')})"
            )
        inst = cls(
            lang=str(meta["lang"]),
            cfg=cfg,
            backbone=str(meta.get("backbone", "") or None),
            classes_=list(meta["classes_"]),
            chapters_=list(meta["chapters_"]),
            intent_to_chapter_=dict(meta.get("intent_to_chapter_", {})),
        )
        inst._tokenizer = transformers.AutoTokenizer.from_pretrained(directory / "tokenizer")
        # Rebuild the torch module and restore weights.
        model = _build_torch_module(
            backbone=str(meta["backbone"]),
            n_chapters=len(inst.chapters_),
            n_intents=len(inst.classes_),
        )
        # Replace the freshly-downloaded encoder with the saved one.
        model.encoder = transformers.AutoModel.from_pretrained(
            directory / "encoder", attn_implementation="eager"
        )
        heads = torch.load(directory / "heads.pt", map_location="cpu", weights_only=True)
        model.chapter_head.load_state_dict(heads["chapter_head"])
        model.intent_head.load_state_dict(heads["intent_head"])
        inst._model = model
        inst._device = _select_device(torch)
        inst._model.to(inst._device)
        inst._model.eval()
        return inst
