"""Runtime service for the public support-chatbot endpoint.

Wraps :class:`football_betting.support.two_head_transformer.TwoHeadTransformerIntentClassifier`
with a single-slot LRU cache so only one language model lives in RAM at a
time (the trained XLM-R-base encoder is ~1.1 GB per language, which is too
much to keep loaded simultaneously on Railway).

Temperature calibration (``temperature.json`` next to each encoder) is applied
post-hoc here because ``TwoHeadTransformerIntentClassifier.load`` does not
restore it at present; applying it sharpens top-k probabilities without
changing argmax.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from football_betting.config import SUPPORT_CFG, SUPPORT_MODELS_DIR

logger = logging.getLogger("football_betting.api")

# Languages for which a ``support_twohead_{lang}`` directory was shipped.
_SUPPORTED_LANGS: tuple[str, ...] = ("de", "en", "es", "fr", "it")

# Low-confidence / out-of-distribution thresholds. When the top-1 intent is
# ``__ood__`` **or** its calibrated probability falls below this gate, the
# endpoint reports an empty ``predictions`` list so the frontend can fall back
# to its Fuse.js FAQ search.
_OOD_INTENT_ID = "__ood__"
_MIN_CONFIDENCE = 0.20


@dataclass(frozen=True, slots=True)
class SupportPrediction:
    intent_id: str
    chapter: str
    score: float
    chapter_score: float


class SupportModelUnavailable(RuntimeError):
    """Raised when the two-head model cannot be loaded (missing dir, bad deps)."""


class _SingleSlotCache:
    """Thread-safe cache that keeps at most one classifier in RAM."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current_lang: str | None = None
        self._current_clf: object | None = None
        self._current_temperature: float = 1.0

    def get(self, lang: str) -> tuple[object, float]:
        with self._lock:
            if self._current_lang == lang and self._current_clf is not None:
                return self._current_clf, self._current_temperature
            # Evict the previous classifier *before* loading the next one so
            # peak RSS stays below ~1.5 GB instead of ~2.5 GB.
            self._current_clf = None
            self._current_lang = None
            self._current_temperature = 1.0
            clf, temperature = _load_classifier(lang)
            self._current_clf = clf
            self._current_lang = lang
            self._current_temperature = temperature
            return clf, temperature


_cache = _SingleSlotCache()


def _model_dir(lang: str) -> Path:
    return SUPPORT_MODELS_DIR / SUPPORT_CFG.two_head_model_dirname_template.format(lang=lang)


def _load_classifier(lang: str) -> tuple[object, float]:
    directory = _model_dir(lang)
    if not directory.exists():
        raise SupportModelUnavailable(f"Support model directory missing: {directory}")

    try:
        from football_betting.support.two_head_transformer import (
            TwoHeadTransformerIntentClassifier,
        )
    except ImportError as exc:  # missing torch/transformers extras
        raise SupportModelUnavailable(
            "Support runtime requires torch + transformers (install [api] extras)."
        ) from exc

    logger.info("[support] loading two-head model for lang=%s", lang)
    clf = TwoHeadTransformerIntentClassifier.load(directory)

    temperature = 1.0
    temp_path = directory / "temperature.json"
    if temp_path.exists():
        try:
            payload = json.loads(temp_path.read_text(encoding="utf-8"))
            t_val = float(payload.get("temperature", 1.0))
            if t_val > 0:
                temperature = t_val
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("[support] invalid temperature.json for %s: %s", lang, exc)

    logger.info("[support] loaded lang=%s (T=%.3f)", lang, temperature)
    return clf, temperature


def _normalize_lang(lang: str) -> str:
    norm = (lang or "en").strip().lower()[:2]
    return norm if norm in _SUPPORTED_LANGS else "en"


def _apply_temperature(score: float, temperature: float) -> float:
    """Sharpen/soften a softmax probability by rescaling its logit by 1/T.

    Because :meth:`predict_topk` only returns the per-intent probability (not
    the full logits vector), this is a first-order approximation good enough
    for display — it does not change ranking.
    """
    if temperature <= 0 or abs(temperature - 1.0) < 1e-6:
        return score
    score = min(max(score, 1e-9), 1 - 1e-9)
    import math

    logit = math.log(score / (1.0 - score))
    scaled = logit / temperature
    return 1.0 / (1.0 + math.exp(-scaled))


def classify(question: str, lang: str, top_k: int = 3) -> list[SupportPrediction]:
    """Classify a user question.

    Returns an empty list when the top-1 prediction is out-of-distribution or
    below the confidence gate — the caller should fall back to FAQ search in
    that case.
    """
    question = (question or "").strip()
    if not question:
        return []

    resolved = _normalize_lang(lang)
    clf, temperature = _cache.get(resolved)

    # ``TwoHeadTransformerIntentClassifier`` exposes ``predict_topk``.
    predictions = clf.predict_topk(question, k=max(1, min(int(top_k), 10)))  # type: ignore[attr-defined]
    if not predictions:
        return []

    top = predictions[0]
    if top.intent_id == _OOD_INTENT_ID:
        return []
    if _apply_temperature(top.score, temperature) < _MIN_CONFIDENCE:
        return []

    out: list[SupportPrediction] = []
    for p in predictions:
        if p.intent_id == _OOD_INTENT_ID:
            continue
        out.append(
            SupportPrediction(
                intent_id=p.intent_id,
                chapter=p.chapter,
                score=_apply_temperature(p.score, temperature),
                chapter_score=p.chapter_score,
            )
        )
    return out


def supported_languages() -> tuple[str, ...]:
    return _SUPPORTED_LANGS
