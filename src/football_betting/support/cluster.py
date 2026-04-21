"""Intent bundling: cluster the 268 intents into ~80 coarse themes.

Hierarchical pipeline:
    query → top-C theme-clusters (cosine vs. cluster centroid)
           → restrict candidates to intents in those clusters
           → fine-grained retrieval (bi-encoder or reranker)

Trained offline from the intent centroids of an ``EmbeddingIntentRetriever``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from football_betting.config import SUPPORT_CFG, SupportConfig
from football_betting.support.embedding_model import EmbeddingIntentRetriever


@dataclass(slots=True)
class IntentClusterer:
    """KMeans-based bundling of intents into coarse theme-clusters."""

    lang: str
    cfg: SupportConfig = SUPPORT_CFG
    n_clusters: int = 80
    intent_ids: list[str] = field(default_factory=list)
    intent_to_cluster: dict[str, int] = field(default_factory=dict)
    cluster_centroids: np.ndarray | None = None  # (n_clusters, dim) L2-normed

    # ───────────────────────── Fit ─────────────────────────

    def fit(
        self,
        retriever: EmbeddingIntentRetriever,
        random_state: int | None = None,
    ) -> dict[str, object]:
        """Cluster intent centroids with spherical KMeans (cosine proxy)."""
        try:
            from sklearn.cluster import KMeans
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("scikit-learn is required for clustering.") from exc

        ids, centroids = retriever.intent_centroids()
        n_eff = max(2, min(self.n_clusters, len(ids)))
        self.n_clusters = n_eff
        rs = random_state if random_state is not None else self.cfg.random_seed

        km = KMeans(n_clusters=n_eff, n_init=10, random_state=rs)
        labels = km.fit_predict(centroids)

        self.intent_ids = list(ids)
        self.intent_to_cluster = {iid: int(c) for iid, c in zip(ids, labels, strict=True)}

        cluster_vecs = np.zeros((n_eff, centroids.shape[1]), dtype=np.float32)
        counts = np.zeros(n_eff, dtype=np.int64)
        for vec, c in zip(centroids, labels, strict=True):
            cluster_vecs[c] += vec
            counts[c] += 1
        counts = np.clip(counts, 1, None)
        cluster_vecs /= counts[:, None]
        norms = np.linalg.norm(cluster_vecs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        self.cluster_centroids = (cluster_vecs / norms).astype(np.float32)

        sizes = [int(s) for s in counts.tolist()]
        return {
            "n_clusters": n_eff,
            "n_intents": len(ids),
            "mean_cluster_size": float(np.mean(sizes)),
            "min_cluster_size": int(np.min(sizes)),
            "max_cluster_size": int(np.max(sizes)),
        }

    # ───────────────────────── Inference ─────────────────────────

    def top_clusters(self, query_vec: np.ndarray, c: int | None = None) -> list[int]:
        if self.cluster_centroids is None:
            raise RuntimeError("Clusterer not trained / loaded.")
        cc = c if c is not None else self.cfg.cluster_top_c
        cc = max(1, min(cc, self.n_clusters))
        sims = self.cluster_centroids @ query_vec
        return [int(i) for i in np.argsort(-sims)[:cc]]

    def allowed_intents(self, cluster_ids: list[int]) -> set[str]:
        cset = set(cluster_ids)
        return {iid for iid, cid in self.intent_to_cluster.items() if cid in cset}

    def allowed_for_query(
        self,
        query_vec: np.ndarray,
        c: int | None = None,
    ) -> set[str]:
        return self.allowed_intents(self.top_clusters(query_vec, c=c))

    def allowed_for_batch(
        self,
        query_mat: np.ndarray,
        c: int | None = None,
    ) -> list[set[str]]:
        if self.cluster_centroids is None:
            raise RuntimeError("Clusterer not trained / loaded.")
        cc = c if c is not None else self.cfg.cluster_top_c
        cc = max(1, min(cc, self.n_clusters))
        sims = query_mat @ self.cluster_centroids.T  # (nq, n_clusters)
        topc_idx = np.argsort(-sims, axis=1)[:, :cc]
        cluster_to_intents: dict[int, list[str]] = {c: [] for c in range(self.n_clusters)}
        for iid, cid in self.intent_to_cluster.items():
            cluster_to_intents[cid].append(iid)
        out: list[set[str]] = []
        for row in topc_idx:
            allowed: set[str] = set()
            for cid in row:
                allowed.update(cluster_to_intents[int(cid)])
            out.append(allowed)
        return out

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, path: Path) -> None:
        if self.cluster_centroids is None:
            raise RuntimeError("Nothing to save — fit first.")
        path.parent.mkdir(parents=True, exist_ok=True)
        intents_sorted = list(self.intent_to_cluster.keys())
        cluster_array = np.array(
            [self.intent_to_cluster[i] for i in intents_sorted], dtype=np.int64
        )
        np.savez_compressed(
            path,
            intent_ids=np.array(intents_sorted, dtype=object),
            intent_to_cluster=cluster_array,
            cluster_centroids=self.cluster_centroids,
            n_clusters=np.array(self.n_clusters),
            lang=np.array(self.lang),
        )

    @classmethod
    def load(cls, path: Path, cfg: SupportConfig = SUPPORT_CFG) -> IntentClusterer:
        data = np.load(path, allow_pickle=True)
        lang = str(data["lang"])
        n_clusters = int(data["n_clusters"])
        inst = cls(lang=lang, cfg=cfg, n_clusters=n_clusters)
        inst.intent_ids = [str(x) for x in data["intent_ids"].tolist()]
        cluster_array = data["intent_to_cluster"].tolist()
        inst.intent_to_cluster = {
            iid: int(c) for iid, c in zip(inst.intent_ids, cluster_array, strict=True)
        }
        inst.cluster_centroids = np.asarray(data["cluster_centroids"], dtype=np.float32)
        return inst
