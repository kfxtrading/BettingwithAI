"""Cross-encoder reranker wrapper (BAAI/bge-reranker-base by default).

Takes (query, passage) pairs and returns relevance scores — higher is better.
Used as a second stage after the bi-encoder retrieval to boost top-k accuracy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from football_betting.config import SUPPORT_CFG, SupportConfig


@dataclass(slots=True)
class CrossEncoderReranker:
    """Thin wrapper around sentence_transformers.CrossEncoder."""

    cfg: SupportConfig = SUPPORT_CFG
    model_name: str | None = None
    _model: Any = field(default=None, init=False, repr=False)

    def _resolve_model_name(self) -> str:
        return self.model_name or self.cfg.reranker_model_name

    def _ensure_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:  # pragma: no cover - optional dep
                raise RuntimeError(
                    "sentence-transformers is required for the reranker. "
                    "Install with `pip install -e \".[embedding]\"`."
                ) from exc
            self._model = CrossEncoder(self._resolve_model_name())
        return self._model

    def score(
        self,
        pairs: list[tuple[str, str]],
        batch_size: int | None = None,
    ) -> np.ndarray:
        """Return 1-D float32 relevance score per (query, passage) pair."""
        if not pairs:
            return np.zeros((0,), dtype=np.float32)
        model = self._ensure_model()
        bs = batch_size if batch_size is not None else self.cfg.reranker_batch_size
        scores = model.predict(
            list(pairs),
            batch_size=bs,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(scores, dtype=np.float32).reshape(-1)
