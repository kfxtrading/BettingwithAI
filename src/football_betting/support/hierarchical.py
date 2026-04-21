"""Hierarchical ("Pachinko") intent classifier: chapter → intent.

Motivated by the external intent-classification report (2026-04-21) which
recommends splitting a flat 268-way softmax into a topic (chapter) head plus
local per-chapter leaf classifiers.  Topics are noun-based (general, basics,
analysis, strategy, mistakes, ai, market, profit, platform) which the report
considers the safer grouping for German-language support chat traffic.

A dedicated ``__ood__`` chapter is trained alongside the real 9 chapters as
the first-line rejection gate for off-topic queries.

The module keeps the same feature pipeline as :class:`IntentClassifier` so
the two models share text-preprocessing behaviour and are comparable on the
same benchmark harness.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from football_betting.config import SUPPORT_CFG, SupportConfig
from football_betting.support.text import normalize


# ───────────────────────── Results ─────────────────────────


@dataclass(frozen=True, slots=True)
class HierarchicalPrediction:
    """Top-k prediction produced by :class:`HierarchicalIntentClassifier`."""

    intent_id: str
    score: float                  # joint P(chapter) · P(intent | chapter)
    chapter: str
    chapter_score: float          # P(chapter)
    is_ood: bool


# ───────────────────────── Pipeline factory ─────────────────────────


def _build_pipeline(cfg: SupportConfig) -> Pipeline:
    """Same char+word TF-IDF → LR pipeline used by the flat classifier."""
    char_vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(cfg.char_ngram_min, cfg.char_ngram_max),
        min_df=cfg.min_df,
        sublinear_tf=cfg.sublinear_tf,
        lowercase=False,
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


# ───────────────────────── Classifier ─────────────────────────


@dataclass(slots=True)
class HierarchicalIntentClassifier:
    """Two-level Pachinko classifier — topic head + per-chapter leaf heads.

    Notes on the OOD chapter
    ------------------------
    ``SUPPORT_CFG.ood_chapter`` is trained just like any other chapter in the
    topic head.  If its posterior probability exceeds
    ``SUPPORT_CFG.ood_topic_threshold`` the prediction is flagged
    ``is_ood=True`` and no leaf expansion is required for routing.
    """

    lang: str
    cfg: SupportConfig = SUPPORT_CFG
    topic_clf: Pipeline | None = None
    leaf_clfs: dict[str, Pipeline] = field(default_factory=dict)
    topic_labels_: list[str] = field(default_factory=list)
    leaf_labels_: dict[str, list[str]] = field(default_factory=dict)
    intent_to_chapter_: dict[str, str] = field(default_factory=dict)

    # ───────────────────────── Training ─────────────────────────

    def fit(
        self,
        X: list[str],
        y_intent: list[str],
        y_chapter: list[str],
    ) -> dict[str, Any]:
        """Fit topic head + one leaf head per chapter.

        ``y_intent`` may include the ``__ood__`` sentinel — those rows train
        only the topic head (no leaf head is created for ``__ood__``).
        """
        if not (len(X) == len(y_intent) == len(y_chapter)):
            raise ValueError(
                "X / y_intent / y_chapter length mismatch: "
                f"{len(X)} / {len(y_intent)} / {len(y_chapter)}"
            )
        if len(X) < 10:
            raise ValueError(f"Too few training samples: {len(X)}")

        X_norm = [normalize(q) for q in X]

        # ─── Topic head over all chapters (incl. __ood__ if present) ───
        self.topic_clf = _build_pipeline(self.cfg)
        self.topic_clf.fit(X_norm, y_chapter)
        self.topic_labels_ = list(self.topic_clf.classes_)

        # ─── Group rows by chapter for the leaf heads ───
        grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
        intent_to_chap: dict[str, str] = {}
        for xi, yi, ci in zip(X_norm, y_intent, y_chapter, strict=True):
            grouped[ci].append((xi, yi))
            if yi != self.cfg.ood_label:
                intent_to_chap[yi] = ci
        self.intent_to_chapter_ = intent_to_chap

        # ─── Per-chapter leaf heads (skip OOD + singleton-intent chapters) ───
        self.leaf_clfs = {}
        self.leaf_labels_ = {}
        for chap, items in grouped.items():
            if chap == self.cfg.ood_chapter:
                # OOD is handled by the topic head; no intent resolution needed.
                continue
            xs = [xy[0] for xy in items]
            ys = [xy[1] for xy in items]
            uniq = sorted(set(ys))
            if not xs or not uniq:
                continue
            if len(uniq) == 1:
                # Only one intent under this chapter — constant head is enough.
                self.leaf_labels_[chap] = uniq
                continue
            leaf = _build_pipeline(self.cfg)
            leaf.fit(xs, ys)
            self.leaf_clfs[chap] = leaf
            self.leaf_labels_[chap] = list(leaf.classes_)

        return {
            "n_samples": len(X),
            "n_chapters": len(self.topic_labels_),
            "n_leaf_heads": len(self.leaf_clfs),
            "n_intents": len({i for i in y_intent if i != self.cfg.ood_label}),
        }

    # ───────────────────────── Inference ─────────────────────────

    def _topic_proba(self, text: str) -> np.ndarray:
        assert self.topic_clf is not None
        return self.topic_clf.predict_proba([normalize(text)])[0]

    def _leaf_proba(self, chap: str, text: str) -> tuple[list[str], np.ndarray]:
        """Return ``(labels, probs)`` for the leaf head of ``chap``.

        Handles the singleton case (only one intent in the chapter) and the
        unseen-chapter case (returns an empty tuple so the caller can skip).
        """
        labels = self.leaf_labels_.get(chap, [])
        if not labels:
            return [], np.empty((0,), dtype=float)
        leaf = self.leaf_clfs.get(chap)
        if leaf is None:
            # Singleton head — deterministic 1.0 on its sole intent.
            return labels, np.ones(1, dtype=float)
        probs = leaf.predict_proba([normalize(text)])[0]
        return list(leaf.classes_), probs

    def predict(self, text: str) -> HierarchicalPrediction:
        top = self.predict_topk(text, k=1)
        return top[0]

    def predict_topk(
        self,
        text: str,
        k: int | None = None,
    ) -> list[HierarchicalPrediction]:
        """Return top-``k`` joint predictions across all plausible chapters.

        Algorithm:
        1. Compute the topic posterior :math:`P(c)`.
        2. If :math:`P(\\text{ood}) \\ge` ``ood_topic_threshold`` → emit a
           single OOD prediction (still returns ``k`` entries to satisfy
           the top-k contract, padded with zero-score OOD placeholders).
        3. Otherwise expand the top ``topic_top_c`` chapters (or until the
           cumulative topic mass reaches ``topic_min_mass``), score all
           intents under them as :math:`P(c) \\cdot P(i \\mid c)` and take
           the overall top-k.
        """
        if self.topic_clf is None:
            raise RuntimeError("Classifier not trained / loaded.")
        cfg = self.cfg
        kk = k if k is not None else cfg.default_topk
        kk = max(1, kk)

        topic_probs = self._topic_proba(text)
        topic_order = np.argsort(topic_probs)[::-1]

        # ─── OOD short-circuit ───
        ood_idx: int | None = None
        if cfg.ood_chapter in self.topic_labels_:
            ood_idx = self.topic_labels_.index(cfg.ood_chapter)
        if ood_idx is not None:
            p_ood = float(topic_probs[ood_idx])
            if p_ood >= cfg.ood_topic_threshold:
                ood_pred = HierarchicalPrediction(
                    intent_id=cfg.ood_label,
                    score=p_ood,
                    chapter=cfg.ood_chapter,
                    chapter_score=p_ood,
                    is_ood=True,
                )
                return [ood_pred] * kk

        # ─── Expand leaf heads for top-C chapters ───
        scored: list[HierarchicalPrediction] = []
        cumulative = 0.0
        expanded = 0
        for j in topic_order:
            chap = self.topic_labels_[int(j)]
            p_c = float(topic_probs[int(j)])
            if chap == cfg.ood_chapter:
                continue
            labels, probs = self._leaf_proba(chap, text)
            if not labels:
                continue
            for lbl, pi in zip(labels, probs, strict=True):
                scored.append(
                    HierarchicalPrediction(
                        intent_id=lbl,
                        score=p_c * float(pi),
                        chapter=chap,
                        chapter_score=p_c,
                        is_ood=False,
                    )
                )
            expanded += 1
            cumulative += p_c
            if expanded >= cfg.topic_top_c and cumulative >= cfg.topic_min_mass:
                break

        if not scored:
            # Pathological: topic head only knew OOD at training time.
            fallback = HierarchicalPrediction(
                intent_id=cfg.ood_label,
                score=0.0,
                chapter=cfg.ood_chapter,
                chapter_score=float(topic_probs[ood_idx]) if ood_idx is not None else 0.0,
                is_ood=True,
            )
            return [fallback] * kk

        scored.sort(key=lambda p: p.score, reverse=True)
        return scored[:kk]

    def predict_proba_batch(self, texts: list[str]) -> np.ndarray:
        """Return a ``(n_texts, n_intents)`` matrix of joint probabilities.

        Intent column order matches ``self.classes_``.
        """
        if self.topic_clf is None:
            raise RuntimeError("Classifier not trained / loaded.")
        labels = self.classes_
        idx_of = {lbl: i for i, lbl in enumerate(labels)}
        out = np.zeros((len(texts), len(labels)), dtype=float)

        normed = [normalize(t) for t in texts]
        topic_probs_batch = self.topic_clf.predict_proba(normed)

        # Pre-compute per-chapter leaf probabilities batched for speed.
        for chap, leaf in self.leaf_clfs.items():
            if chap not in self.topic_labels_:
                continue
            chap_col = self.topic_labels_.index(chap)
            leaf_probs = leaf.predict_proba(normed)
            leaf_labels = list(leaf.classes_)
            for li, lbl in enumerate(leaf_labels):
                col = idx_of.get(lbl)
                if col is None:
                    continue
                out[:, col] = topic_probs_batch[:, chap_col] * leaf_probs[:, li]

        # Singleton heads (one intent per chapter → probability == P(chapter)).
        for chap, lbls in self.leaf_labels_.items():
            if chap in self.leaf_clfs:
                continue
            if chap not in self.topic_labels_ or len(lbls) != 1:
                continue
            chap_col = self.topic_labels_.index(chap)
            only = lbls[0]
            col = idx_of.get(only)
            if col is not None:
                out[:, col] = topic_probs_batch[:, chap_col]

        # OOD column (if tracked in classes_).
        if self.cfg.ood_label in idx_of and self.cfg.ood_chapter in self.topic_labels_:
            col = idx_of[self.cfg.ood_label]
            chap_col = self.topic_labels_.index(self.cfg.ood_chapter)
            out[:, col] = topic_probs_batch[:, chap_col]

        return out

    # ───────────────────────── Evaluation ─────────────────────────

    @property
    def classes_(self) -> list[str]:
        """Flat list of all intent ids known to this classifier (incl. OOD)."""
        ids: list[str] = []
        for chap in self.topic_labels_:
            if chap == self.cfg.ood_chapter:
                ids.append(self.cfg.ood_label)
                continue
            ids.extend(self.leaf_labels_.get(chap, []))
        # Deduplicate while preserving first occurrence.
        seen: set[str] = set()
        uniq: list[str] = []
        for i in ids:
            if i not in seen:
                uniq.append(i)
                seen.add(i)
        return uniq

    def evaluate(
        self,
        X_val: list[str],
        y_val: list[str],
        chapters: list[str] | None = None,
    ) -> dict[str, Any]:
        """Top-1 / top-3 accuracy, macro-F1, per-chapter top-1, OOD metrics."""
        from sklearn.metrics import f1_score

        if not X_val:
            return {
                "n_val": 0,
                "top1_accuracy": None,
                "top3_accuracy": None,
                "macro_f1": None,
                "per_chapter_top1": {},
                "ood_precision": None,
                "ood_recall": None,
            }

        labels = self.classes_
        probs = self.predict_proba_batch(X_val)
        assert probs.shape == (len(X_val), len(labels))
        idx_of = {lbl: i for i, lbl in enumerate(labels)}

        top3_idx = np.argsort(probs, axis=1)[:, ::-1][:, :3]
        top1_preds = [labels[int(top3_idx[i, 0])] for i in range(len(X_val))]
        top1_hits = 0
        top3_hits = 0
        per_chap_total: dict[str, int] = defaultdict(int)
        per_chap_hits: dict[str, int] = defaultdict(int)
        ood_tp = ood_fp = ood_fn = 0

        ood_label = self.cfg.ood_label

        for i, true_id in enumerate(y_val):
            pred_id = top1_preds[i]
            if pred_id == true_id:
                top1_hits += 1
            true_col = idx_of.get(true_id)
            if true_col is not None and true_col in top3_idx[i].tolist():
                top3_hits += 1
            if chapters is not None:
                chap = chapters[i]
                per_chap_total[chap] += 1
                if pred_id == true_id:
                    per_chap_hits[chap] += 1
            # OOD detection metrics
            pred_is_ood = pred_id == ood_label
            true_is_ood = true_id == ood_label
            if pred_is_ood and true_is_ood:
                ood_tp += 1
            elif pred_is_ood and not true_is_ood:
                ood_fp += 1
            elif not pred_is_ood and true_is_ood:
                ood_fn += 1

        macro_f1 = float(
            f1_score(y_val, top1_preds, average="macro", zero_division=0.0)
        )
        per_chapter_top1 = {
            chap: per_chap_hits[chap] / per_chap_total[chap]
            for chap in per_chap_total
            if per_chap_total[chap] > 0
        }
        ood_precision = (
            ood_tp / (ood_tp + ood_fp) if (ood_tp + ood_fp) > 0 else None
        )
        ood_recall = (
            ood_tp / (ood_tp + ood_fn) if (ood_tp + ood_fn) > 0 else None
        )

        return {
            "n_val": len(y_val),
            "top1_accuracy": top1_hits / len(y_val),
            "top3_accuracy": top3_hits / len(y_val),
            "macro_f1": macro_f1,
            "per_chapter_top1": per_chapter_top1,
            "ood_precision": ood_precision,
            "ood_recall": ood_recall,
        }

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, path: Path) -> None:
        if self.topic_clf is None:
            raise RuntimeError("Nothing to save — fit first.")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "lang": self.lang,
                "topic_clf": self.topic_clf,
                "leaf_clfs": self.leaf_clfs,
                "topic_labels_": self.topic_labels_,
                "leaf_labels_": self.leaf_labels_,
                "intent_to_chapter_": self.intent_to_chapter_,
            },
            path,
        )

    @classmethod
    def load(
        cls,
        path: Path,
        cfg: SupportConfig = SUPPORT_CFG,
    ) -> HierarchicalIntentClassifier:
        payload = joblib.load(path)
        inst = cls(lang=str(payload["lang"]), cfg=cfg)
        inst.topic_clf = payload["topic_clf"]
        inst.leaf_clfs = dict(payload["leaf_clfs"])
        inst.topic_labels_ = list(payload["topic_labels_"])
        inst.leaf_labels_ = {
            k: list(v) for k, v in dict(payload["leaf_labels_"]).items()
        }
        inst.intent_to_chapter_ = dict(payload["intent_to_chapter_"])
        return inst


__all__ = ["HierarchicalIntentClassifier", "HierarchicalPrediction"]
