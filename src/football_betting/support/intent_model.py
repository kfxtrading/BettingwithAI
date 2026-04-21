"""Support FAQ intent classifier — TF-IDF (char+word) + Logistic Regression.

Trained once per language. Predicts an intent ID (the FAQ `id`) from a free
form user question. Artefacts are persisted via joblib.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from football_betting.config import SUPPORT_CFG, SupportConfig
from football_betting.support.text import normalize


@dataclass(frozen=True, slots=True)
class IntentPrediction:
    intent_id: str
    score: float


def _build_pipeline(cfg: SupportConfig) -> Pipeline:
    """sklearn pipeline: FeatureUnion(char_wb, word) → LogisticRegression."""
    char_vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(cfg.char_ngram_min, cfg.char_ngram_max),
        min_df=cfg.min_df,
        sublinear_tf=cfg.sublinear_tf,
        lowercase=False,  # already normalized
    )
    word_vec = TfidfVectorizer(
        analyzer="word",
        ngram_range=(cfg.word_ngram_min, cfg.word_ngram_max),
        min_df=cfg.min_df,
        sublinear_tf=cfg.sublinear_tf,
        token_pattern=r"(?u)\b\w+\b",
        lowercase=False,
    )
    features = FeatureUnion([("char", char_vec), ("word", word_vec)])
    clf = LogisticRegression(
        C=cfg.lr_C,
        class_weight=cfg.lr_class_weight,
        max_iter=cfg.lr_max_iter,
        solver=cfg.lr_solver,
        random_state=cfg.random_seed,
    )
    return Pipeline([("features", features), ("clf", clf)])


@dataclass(slots=True)
class IntentClassifier:
    """TF-IDF + LR intent classifier for a single language."""

    lang: str
    cfg: SupportConfig = SUPPORT_CFG
    pipeline: Pipeline | None = None
    classes_: list[str] | None = None

    # ───────────────────────── Training ─────────────────────────

    def fit(self, X: list[str], y: list[str]) -> dict[str, Any]:
        if len(X) != len(y):
            raise ValueError(f"X/y length mismatch: {len(X)} vs {len(y)}")
        if len(X) < 10:
            raise ValueError(f"Too few training samples: {len(X)}")

        X_norm = [normalize(q) for q in X]
        self.pipeline = _build_pipeline(self.cfg)
        self.pipeline.fit(X_norm, y)
        self.classes_ = list(self.pipeline.classes_)
        return {"n_samples": len(X), "n_classes": len(self.classes_)}

    # ───────────────────────── Inference ─────────────────────────

    def predict(self, text: str) -> IntentPrediction:
        top = self.predict_topk(text, k=1)
        return top[0]

    def predict_topk(self, text: str, k: int | None = None) -> list[IntentPrediction]:
        if self.pipeline is None or self.classes_ is None:
            raise RuntimeError("Classifier not trained / loaded.")
        kk = k if k is not None else self.cfg.default_topk
        kk = max(1, min(kk, len(self.classes_)))

        probs = self.pipeline.predict_proba([normalize(text)])[0]
        idx = np.argsort(probs)[::-1][:kk]
        return [
            IntentPrediction(intent_id=self.classes_[i], score=float(probs[i]))
            for i in idx
        ]

    def predict_proba_batch(self, texts: list[str]) -> np.ndarray:
        if self.pipeline is None:
            raise RuntimeError("Classifier not trained / loaded.")
        normed = [normalize(t) for t in texts]
        return self.pipeline.predict_proba(normed)

    # ───────────────────────── Evaluation ─────────────────────────

    def evaluate(
        self,
        X_val: list[str],
        y_val: list[str],
        chapters: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return top-1 / top-3 accuracy, macro-F1, per-chapter top-1 accuracy."""
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
        assert self.classes_ is not None
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}

        top1_preds: list[str] = []
        top3_hits = 0
        top1_hits = 0
        per_chap_total: dict[str, int] = defaultdict(int)
        per_chap_hits: dict[str, int] = defaultdict(int)

        top3_idx = np.argsort(probs, axis=1)[:, ::-1][:, :3]

        for i, true_id in enumerate(y_val):
            top1_idx = int(top3_idx[i, 0])
            pred_id = self.classes_[top1_idx]
            top1_preds.append(pred_id)

            true_idx = class_to_idx.get(true_id)
            if true_idx is None:
                continue
            if top1_idx == true_idx:
                top1_hits += 1
            if true_idx in top3_idx[i].tolist():
                top3_hits += 1

            if chapters is not None:
                chap = chapters[i]
                per_chap_total[chap] += 1
                if top1_idx == true_idx:
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

    def save(self, path: Path) -> None:
        if self.pipeline is None:
            raise RuntimeError("Nothing to save — fit first.")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "lang": self.lang,
                "pipeline": self.pipeline,
                "classes_": self.classes_,
            },
            path,
        )

    @classmethod
    def load(cls, path: Path, cfg: SupportConfig = SUPPORT_CFG) -> IntentClassifier:
        payload = joblib.load(path)
        inst = cls(lang=str(payload["lang"]), cfg=cfg)
        inst.pipeline = payload["pipeline"]
        inst.classes_ = list(payload["classes_"])
        return inst
