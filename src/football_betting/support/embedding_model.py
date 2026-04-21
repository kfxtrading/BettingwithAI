"""Dense multilingual embedding retriever for support intents.

Uses ``intfloat/multilingual-e5-large-instruct`` (or any sentence-transformers
compatible model) to embed FAQ phrasings once, then resolves user queries via
cosine similarity with per-intent max aggregation.

Instruction prefixes follow the E5 convention:
    passages = f"passage: {text}"
    queries  = f"query: {text}"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from football_betting.config import SUPPORT_CFG, SupportConfig
from football_betting.support.text import normalize


@dataclass(frozen=True, slots=True)
class EmbeddingPrediction:
    intent_id: str
    score: float


@dataclass(slots=True)
class EmbeddingIntentRetriever:
    """Nearest-neighbor retriever backed by multilingual sentence embeddings."""

    lang: str
    cfg: SupportConfig = SUPPORT_CFG
    model_name: str | None = None
    embeddings: np.ndarray | None = None  # (N, dim) float32, L2-normalized
    row_to_intent: list[str] = field(default_factory=list)
    passages: list[str] = field(default_factory=list)  # raw training phrasings (len N)
    intent_ids: list[str] = field(default_factory=list)
    _model: Any = None  # lazy sentence_transformers.SentenceTransformer

    # ───────────────────────── Model loading ─────────────────────────

    def _resolve_model_name(self) -> str:
        return self.model_name or self.cfg.embedding_model_name

    def _ensure_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - optional dep
                raise RuntimeError(
                    "sentence-transformers is required for the embedding "
                    "backend. Install with `pip install -e \".[embedding]\"`."
                ) from exc
            self._model = SentenceTransformer(self._resolve_model_name())
        return self._model

    # ───────────────────────── Training ─────────────────────────

    def fit(
        self,
        X: list[str],
        y: list[str],
        *,
        batch_size: int | None = None,
        show_progress_bar: bool = True,
    ) -> dict[str, Any]:
        if len(X) != len(y):
            raise ValueError(f"X/y length mismatch: {len(X)} vs {len(y)}")
        if not X:
            raise ValueError("Empty training set.")

        model = self._ensure_model()
        bs = batch_size if batch_size is not None else self.cfg.embedding_batch_size
        passages = [f"passage: {normalize(q)}" for q in X]
        emb = model.encode(
            passages,
            normalize_embeddings=True,
            batch_size=bs,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
        )
        self.embeddings = np.asarray(emb, dtype=np.float32)
        self.row_to_intent = [str(yi) for yi in y]
        self.passages = [str(q) for q in X]
        self.intent_ids = sorted(set(self.row_to_intent))
        return {
            "n_samples": int(self.embeddings.shape[0]),
            "n_classes": len(self.intent_ids),
            "dim": int(self.embeddings.shape[1]),
        }

    # ───────────────────────── Inference ─────────────────────────

    def _encode_query(self, text: str) -> np.ndarray:
        model = self._ensure_model()
        vec = model.encode(
            [f"query: {normalize(text)}"],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]
        return np.asarray(vec, dtype=np.float32)

    def _encode_queries(self, texts: list[str], batch_size: int | None = None) -> np.ndarray:
        model = self._ensure_model()
        bs = batch_size if batch_size is not None else self.cfg.embedding_batch_size
        emb = model.encode(
            [f"query: {normalize(t)}" for t in texts],
            normalize_embeddings=True,
            batch_size=bs,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(emb, dtype=np.float32)

    def _aggregate_max_per_intent(self, sims: np.ndarray) -> dict[str, float]:
        best: dict[str, float] = {}
        for score, intent in zip(sims.tolist(), self.row_to_intent, strict=True):
            s = float(score)
            if s > best.get(intent, -1.0):
                best[intent] = s
        return best

    def predict_topk(
        self,
        text: str,
        k: int | None = None,
        *,
        allowed_intents: set[str] | None = None,
    ) -> list[EmbeddingPrediction]:
        if self.embeddings is None or not self.row_to_intent:
            raise RuntimeError("Retriever not trained / loaded.")
        kk = k if k is not None else self.cfg.default_topk
        kk = max(1, min(kk, len(self.intent_ids)))

        q = self._encode_query(text)
        sims = self.embeddings @ q
        if allowed_intents is not None:
            mask = np.array(
                [intent in allowed_intents for intent in self.row_to_intent],
                dtype=bool,
            )
            if not mask.any():
                # fall back to unrestricted scoring if the cluster filter
                # rejected every candidate (defensive, shouldn't happen).
                mask = np.ones_like(mask, dtype=bool)
            sims = np.where(mask, sims, -np.inf)
        best = self._aggregate_max_per_intent(sims)
        ranked = sorted(best.items(), key=lambda x: x[1], reverse=True)[:kk]
        return [EmbeddingPrediction(intent_id=i, score=s) for i, s in ranked]

    def top_candidate_rows(
        self,
        text: str,
        n: int = 20,
        *,
        allowed_intents: set[str] | None = None,
    ) -> list[tuple[int, float]]:
        """Return top-N (row_index, cosine_score) pairs — used for reranking."""
        if self.embeddings is None or not self.row_to_intent:
            raise RuntimeError("Retriever not trained / loaded.")
        q = self._encode_query(text)
        sims = self.embeddings @ q
        if allowed_intents is not None:
            mask = np.array(
                [intent in allowed_intents for intent in self.row_to_intent],
                dtype=bool,
            )
            if mask.any():
                sims = np.where(mask, sims, -np.inf)
        n_eff = max(1, min(n, sims.shape[0]))
        top_idx = np.argpartition(-sims, n_eff - 1)[:n_eff]
        ordered = top_idx[np.argsort(-sims[top_idx])]
        return [(int(i), float(sims[i])) for i in ordered if sims[i] > -np.inf]

    def predict_topk_reranked(
        self,
        text: str,
        reranker: Any,
        k: int | None = None,
        retrieve_n: int | None = None,
        *,
        allowed_intents: set[str] | None = None,
    ) -> list[EmbeddingPrediction]:
        """Two-stage retrieval: bi-encoder shortlist → cross-encoder rerank."""
        if self.embeddings is None or not self.row_to_intent:
            raise RuntimeError("Retriever not trained / loaded.")
        if not self.passages:
            raise RuntimeError(
                "Reranker needs raw passages — retrain the index with the "
                "updated EmbeddingIntentRetriever."
            )
        kk = k if k is not None else self.cfg.default_topk
        kk = max(1, min(kk, len(self.intent_ids)))
        n = retrieve_n if retrieve_n is not None else self.cfg.reranker_retrieve_n

        cand = self.top_candidate_rows(text, n=n, allowed_intents=allowed_intents)
        if not cand:
            return []
        pairs = [(text, self.passages[row]) for row, _ in cand]
        scores = reranker.score(pairs)
        best: dict[str, float] = {}
        for (row, _), rerank_score in zip(cand, scores, strict=True):
            intent = self.row_to_intent[row]
            s = float(rerank_score)
            if s > best.get(intent, -float("inf")):
                best[intent] = s
        ranked = sorted(best.items(), key=lambda x: x[1], reverse=True)[:kk]
        return [EmbeddingPrediction(intent_id=i, score=s) for i, s in ranked]

    def predict_topk_batch(
        self,
        texts: list[str],
        k: int = 3,
        batch_size: int | None = None,
        *,
        allowed_intents_per_query: list[set[str]] | None = None,
    ) -> list[list[tuple[str, float]]]:
        if self.embeddings is None or not self.row_to_intent:
            raise RuntimeError("Retriever not trained / loaded.")
        if not texts:
            return []
        if allowed_intents_per_query is not None and len(allowed_intents_per_query) != len(texts):
            raise ValueError("allowed_intents_per_query must match texts length.")
        q = self._encode_queries(texts, batch_size=batch_size)
        sims_mat = q @ self.embeddings.T  # (n_queries, N)
        row_intents = np.array(self.row_to_intent)
        out: list[list[tuple[str, float]]] = []
        for i, row in enumerate(sims_mat):
            if allowed_intents_per_query is not None:
                allowed = allowed_intents_per_query[i]
                mask = np.isin(row_intents, list(allowed))
                if mask.any():
                    row = np.where(mask, row, -np.inf)
            best = self._aggregate_max_per_intent(row)
            ranked = sorted(best.items(), key=lambda x: x[1], reverse=True)[:k]
            out.append(ranked)
        return out

    def predict_topk_reranked_batch(
        self,
        texts: list[str],
        reranker: Any,
        k: int = 3,
        retrieve_n: int | None = None,
        *,
        allowed_intents_per_query: list[set[str]] | None = None,
    ) -> list[list[tuple[str, float]]]:
        """Batched two-stage retrieval. One reranker forward per query group."""
        if self.embeddings is None or not self.row_to_intent or not self.passages:
            raise RuntimeError("Retriever not trained / loaded with passages.")
        if not texts:
            return []
        if allowed_intents_per_query is not None and len(allowed_intents_per_query) != len(texts):
            raise ValueError("allowed_intents_per_query must match texts length.")
        n = retrieve_n if retrieve_n is not None else self.cfg.reranker_retrieve_n

        q_mat = self._encode_queries(texts)
        sims_mat = q_mat @ self.embeddings.T
        row_intents = np.array(self.row_to_intent)

        all_pairs: list[tuple[str, str]] = []
        per_query_ranges: list[tuple[int, int, list[int]]] = []
        cursor = 0
        for i, sims in enumerate(sims_mat):
            if allowed_intents_per_query is not None:
                mask = np.isin(row_intents, list(allowed_intents_per_query[i]))
                if mask.any():
                    sims = np.where(mask, sims, -np.inf)
            n_eff = max(1, min(n, sims.shape[0]))
            top_idx = np.argpartition(-sims, n_eff - 1)[:n_eff]
            ordered = top_idx[np.argsort(-sims[top_idx])]
            cand_rows = [int(r) for r in ordered if sims[r] > -np.inf]
            start = cursor
            for r in cand_rows:
                all_pairs.append((texts[i], self.passages[r]))
                cursor += 1
            per_query_ranges.append((start, cursor, cand_rows))

        if not all_pairs:
            return [[] for _ in texts]
        rerank_scores = reranker.score(all_pairs)

        out: list[list[tuple[str, float]]] = []
        for i, (start, end, cand_rows) in enumerate(per_query_ranges):
            scores = rerank_scores[start:end]
            best: dict[str, float] = {}
            for row, s in zip(cand_rows, scores, strict=True):
                intent = self.row_to_intent[row]
                sv = float(s)
                if sv > best.get(intent, -float("inf")):
                    best[intent] = sv
            ranked = sorted(best.items(), key=lambda x: x[1], reverse=True)[:k]
            out.append(ranked)
        return out

    # ───────────────────────── Intent centroids ─────────────────────────

    def intent_centroids(self) -> tuple[list[str], np.ndarray]:
        """Return (intent_ids, centroid_matrix) where centroids are L2-normalized."""
        if self.embeddings is None or not self.row_to_intent:
            raise RuntimeError("Retriever not trained / loaded.")
        ids = self.intent_ids or sorted(set(self.row_to_intent))
        dim = int(self.embeddings.shape[1])
        centroids = np.zeros((len(ids), dim), dtype=np.float32)
        id_to_idx = {iid: i for i, iid in enumerate(ids)}
        counts = np.zeros(len(ids), dtype=np.int64)
        for row_idx, intent in enumerate(self.row_to_intent):
            j = id_to_idx[intent]
            centroids[j] += self.embeddings[row_idx]
            counts[j] += 1
        counts = np.clip(counts, 1, None)
        centroids = centroids / counts[:, None]
        norms = np.linalg.norm(centroids, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        centroids = centroids / norms
        return ids, centroids.astype(np.float32)

    # ───────────────────────── Evaluation ─────────────────────────

    def evaluate(
        self,
        X_val: list[str],
        y_val: list[str],
        chapters: list[str] | None = None,
        k_top: int = 3,
        batch_size: int | None = None,
        *,
        reranker: Any = None,
        retrieve_n: int | None = None,
        allowed_intents_per_query: list[set[str]] | None = None,
    ) -> dict[str, Any]:
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

        if reranker is not None:
            preds = self.predict_topk_reranked_batch(
                X_val,
                reranker=reranker,
                k=k_top,
                retrieve_n=retrieve_n,
                allowed_intents_per_query=allowed_intents_per_query,
            )
        else:
            preds = self.predict_topk_batch(
                X_val,
                k=k_top,
                batch_size=batch_size,
                allowed_intents_per_query=allowed_intents_per_query,
            )
        top1_preds: list[str] = []
        top1_hits = 0
        top3_hits = 0
        per_chap_total: dict[str, int] = defaultdict(int)
        per_chap_hits: dict[str, int] = defaultdict(int)

        for i, true_id in enumerate(y_val):
            ranked = preds[i]
            pred_ids = [iid for iid, _ in ranked]
            top1 = pred_ids[0] if pred_ids else ""
            top1_preds.append(top1)
            hit = top1 == true_id
            if hit:
                top1_hits += 1
            if true_id in pred_ids:
                top3_hits += 1
            if chapters is not None:
                chap = chapters[i]
                per_chap_total[chap] += 1
                if hit:
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
        if self.embeddings is None:
            raise RuntimeError("Nothing to save — fit first.")
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            embeddings=self.embeddings,
            row_to_intent=np.array(self.row_to_intent, dtype=object),
            passages=np.array(self.passages, dtype=object),
            intent_ids=np.array(self.intent_ids, dtype=object),
            lang=np.array(self.lang),
            model_name=np.array(self._resolve_model_name()),
        )

    @classmethod
    def load(
        cls,
        path: Path,
        cfg: SupportConfig = SUPPORT_CFG,
        model_name: str | None = None,
    ) -> EmbeddingIntentRetriever:
        data = np.load(path, allow_pickle=True)
        lang = str(data["lang"])
        stored_model = str(data["model_name"]) if "model_name" in data.files else None
        inst = cls(
            lang=lang,
            cfg=cfg,
            model_name=model_name or stored_model or cfg.embedding_model_name,
        )
        inst.embeddings = np.asarray(data["embeddings"], dtype=np.float32)
        inst.row_to_intent = [str(x) for x in data["row_to_intent"].tolist()]
        inst.intent_ids = [str(x) for x in data["intent_ids"].tolist()]
        if "passages" in data.files:
            inst.passages = [str(x) for x in data["passages"].tolist()]
        return inst
