"""Benchmark ML / Fuse / Embedding / Rerank / Cluster intent backends.

For each language:
- Load the trained joblib model (TF-IDF + LR, if present).
- Recreate the train/val split exactly as the trainer did.
- Build a Fuse-like baseline that matches the val query against the
  canonical question + altQuestions of every intent (the same fields
  the JS Fuse indexes), using rapidfuzz token_set_ratio as the score.
- Load the embedding retriever (.npz) if present.
- Optionally run the cross-encoder reranker (--rerank) on embedding top-N.
- Optionally restrict candidates to top-C theme-clusters (--cluster)
  when a cluster index (.npz) was produced by `train_support.py --cluster`.

Usage:
    python scripts/bench_support_intent.py
    python scripts/bench_support_intent.py --rerank
    python scripts/bench_support_intent.py --cluster
    python scripts/bench_support_intent.py --rerank --cluster
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import click
from rapidfuzz import fuzz, process
from rich.console import Console
from rich.table import Table

from football_betting.config import (
    SUPPORT_CFG,
    SUPPORT_DATA_DIR,
    SUPPORT_MODELS_DIR,
)
from football_betting.support.dataset import load_dataset, stratified_split
from football_betting.support.intent_model import IntentClassifier
from football_betting.support.text import normalize

ROOT = Path(__file__).resolve().parents[1]
console = Console()


def build_fuse_index(rows_lang: list[dict[str, object]]) -> dict[str, list[str]]:
    """Per-intent corpus: canonical question + alt_questions (normalized)."""
    by_intent: dict[str, list[str]] = defaultdict(list)
    for r in rows_lang:
        intent = str(r["id"])
        if r.get("source") == "original":
            q = str(r.get("question", ""))
            if q:
                by_intent[intent].append(normalize(q))
            for alt in (r.get("alt_questions") or []):
                if isinstance(alt, str) and alt:
                    by_intent[intent].append(normalize(alt))
    return dict(by_intent)


def fuse_topk(query: str, index: dict[str, list[str]], k: int = 3) -> list[str]:
    """Return top-k intent ids by max token_set_ratio across the intent's phrasings."""
    q = normalize(query)
    scored: list[tuple[str, float]] = []
    for intent_id, phrasings in index.items():
        if not phrasings:
            continue
        best = process.extractOne(
            q, phrasings, scorer=fuzz.token_set_ratio
        )
        if best is None:
            continue
        scored.append((intent_id, float(best[1])))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [iid for iid, _ in scored[:k]]


def _topk_acc(preds: list[list[str]], y_val: list[str], k: int = 1) -> float:
    hits = 0
    for pred, true in zip(preds, y_val, strict=True):
        if k == 1:
            if pred and pred[0] == true:
                hits += 1
        else:
            if true in pred[:k]:
                hits += 1
    return hits / len(y_val) if y_val else 0.0


def evaluate_lang(
    lang: str,
    *,
    shared_reranker=None,
    use_rerank: bool = False,
    use_cluster: bool = False,
    cluster_top_c: int | None = None,
) -> dict[str, object]:
    rows = load_dataset(lang=lang)
    split = stratified_split(rows)
    if not split.X_val:
        return {"lang": lang, "skipped": True}

    n = len(split.X_val)
    res: dict[str, object] = {
        "lang": lang,
        "n_val": n,
        "n_classes": split.n_classes,
    }

    # ─── ML (TF-IDF + LR) ───
    ml_model_path = SUPPORT_MODELS_DIR / SUPPORT_CFG.model_filename_template.format(lang=lang)
    if ml_model_path.exists():
        clf = IntentClassifier.load(ml_model_path)
        probs = clf.predict_proba_batch(split.X_val)
        import numpy as np
        top3_idx = np.argsort(probs, axis=1)[:, ::-1][:, :3]
        classes = clf.classes_ or []
        ml_pred = [[classes[j] for j in top3_idx[i].tolist()] for i in range(n)]
        res["ml_top1"] = _topk_acc(ml_pred, split.y_val, k=1)
        res["ml_top3"] = _topk_acc(ml_pred, split.y_val, k=3)
    else:
        console.log(f"[yellow]{lang}: ML model not found at {ml_model_path}[/yellow]")

    # ─── Embedding retriever ───
    emb_model_path = SUPPORT_MODELS_DIR / SUPPORT_CFG.embedding_filename_template.format(lang=lang)
    retriever = None
    allowed_per_q = None
    if emb_model_path.exists():
        try:
            from football_betting.support.embedding_model import EmbeddingIntentRetriever

            retriever = EmbeddingIntentRetriever.load(emb_model_path)
            preds = retriever.predict_topk_batch(split.X_val, k=3)
            emb_pred = [[iid for iid, _ in p] for p in preds]
            res["emb_top1"] = _topk_acc(emb_pred, split.y_val, k=1)
            res["emb_top3"] = _topk_acc(emb_pred, split.y_val, k=3)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]{lang}: embedding backend failed: {exc}[/red]")
    else:
        console.log(f"[yellow]{lang}: embedding index not found at {emb_model_path}[/yellow]")

    # ─── Cluster filter ───
    if use_cluster and retriever is not None:
        cluster_path = SUPPORT_MODELS_DIR / SUPPORT_CFG.cluster_filename_template.format(lang=lang)
        if cluster_path.exists():
            try:
                from football_betting.support.cluster import IntentClusterer

                clusterer = IntentClusterer.load(cluster_path)
                q_mat = retriever._encode_queries(split.X_val)
                allowed_per_q = clusterer.allowed_for_batch(q_mat, c=cluster_top_c)
                cl_preds = retriever.predict_topk_batch(
                    split.X_val, k=3, allowed_intents_per_query=allowed_per_q
                )
                cl_pred = [[iid for iid, _ in p] for p in cl_preds]
                res["cluster_top1"] = _topk_acc(cl_pred, split.y_val, k=1)
                res["cluster_top3"] = _topk_acc(cl_pred, split.y_val, k=3)
            except Exception as exc:  # noqa: BLE001
                console.log(f"[red]{lang}: cluster backend failed: {exc}[/red]")
        else:
            console.log(f"[yellow]{lang}: cluster index not found at {cluster_path}[/yellow]")

    # ─── Reranker ───
    if use_rerank and retriever is not None and shared_reranker is not None:
        try:
            rr_preds = retriever.predict_topk_reranked_batch(
                split.X_val, reranker=shared_reranker, k=3
            )
            rr_pred = [[iid for iid, _ in p] for p in rr_preds]
            res["rerank_top1"] = _topk_acc(rr_pred, split.y_val, k=1)
            res["rerank_top3"] = _topk_acc(rr_pred, split.y_val, k=3)

            if allowed_per_q is not None:
                rrc_preds = retriever.predict_topk_reranked_batch(
                    split.X_val,
                    reranker=shared_reranker,
                    k=3,
                    allowed_intents_per_query=allowed_per_q,
                )
                rrc_pred = [[iid for iid, _ in p] for p in rrc_preds]
                res["rerank_cluster_top1"] = _topk_acc(rrc_pred, split.y_val, k=1)
                res["rerank_cluster_top3"] = _topk_acc(rrc_pred, split.y_val, k=3)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]{lang}: reranker failed: {exc}[/red]")

    # ─── Fuse baseline ───
    fuse_index = build_fuse_index(rows)
    fuse_pred = [fuse_topk(split.X_val[i], fuse_index, k=3) for i in range(n)]
    res["fuse_top1"] = _topk_acc(fuse_pred, split.y_val, k=1)
    res["fuse_top3"] = _topk_acc(fuse_pred, split.y_val, k=3)
    return res


def _fmt(val: object) -> str:
    if isinstance(val, float):
        return f"{val:.4f}"
    if val is None:
        return "—"
    return str(val)


@click.command()
@click.option("--rerank/--no-rerank", default=False, help="Also evaluate the cross-encoder rerank stage.")
@click.option("--cluster/--no-cluster", default=False, help="Also evaluate the cluster-filtered variant.")
@click.option("--reranker-model-name", default=None, help="Override BAAI/bge-reranker-base.")
@click.option("--cluster-top-c", type=int, default=None, help="Top-C clusters to keep (default cfg).")
def main(
    rerank: bool,
    cluster: bool,
    reranker_model_name: str | None,
    cluster_top_c: int | None,
) -> None:
    shared_reranker = None
    if rerank:
        from football_betting.support.reranker import CrossEncoderReranker

        shared_reranker = CrossEncoderReranker(model_name=reranker_model_name)
        console.log("[cyan]Loaded cross-encoder reranker.[/cyan]")

    out: list[dict[str, object]] = []
    for lang in SUPPORT_CFG.languages:
        console.rule(f"[cyan]Benchmark — {lang}[/cyan]")
        try:
            res = evaluate_lang(
                lang,
                shared_reranker=shared_reranker,
                use_rerank=rerank,
                use_cluster=cluster,
                cluster_top_c=cluster_top_c,
            )
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]{lang} failed: {exc}[/red]")
            continue
        out.append(res)
        if res.get("skipped"):
            console.log(f"[yellow]{lang}: no val data[/yellow]")
            continue
        parts = []
        if "ml_top1" in res:
            parts.append(f"ML  t1={res['ml_top1']:.4f}")
        if "emb_top1" in res:
            parts.append(f"Emb t1={res['emb_top1']:.4f}")
        if "cluster_top1" in res:
            parts.append(f"Clus t1={res['cluster_top1']:.4f}")
        if "rerank_top1" in res:
            parts.append(f"Rrk t1={res['rerank_top1']:.4f}")
        if "rerank_cluster_top1" in res:
            parts.append(f"R+C t1={res['rerank_cluster_top1']:.4f}")
        parts.append(f"Fuse t1={res['fuse_top1']:.4f}")
        console.log("   ".join(parts))

    table = Table(title="Support Intent — Backend comparison")
    table.add_column("Lang")
    table.add_column("#Val", justify="right")
    table.add_column("#Cls", justify="right")
    table.add_column("ML t1", justify="right")
    table.add_column("ML t3", justify="right")
    table.add_column("Fuse t1", justify="right")
    table.add_column("Fuse t3", justify="right")
    table.add_column("Emb t1", justify="right")
    table.add_column("Emb t3", justify="right")
    if cluster:
        table.add_column("Cl t1", justify="right")
        table.add_column("Cl t3", justify="right")
    if rerank:
        table.add_column("Re t1", justify="right")
        table.add_column("Re t3", justify="right")
    if rerank and cluster:
        table.add_column("R+C t1", justify="right")
        table.add_column("R+C t3", justify="right")

    for r in out:
        if r.get("skipped"):
            continue
        row = [
            str(r["lang"]),
            str(r["n_val"]),
            str(r["n_classes"]),
            _fmt(r.get("ml_top1")),
            _fmt(r.get("ml_top3")),
            _fmt(r.get("fuse_top1")),
            _fmt(r.get("fuse_top3")),
            _fmt(r.get("emb_top1")),
            _fmt(r.get("emb_top3")),
        ]
        if cluster:
            row += [_fmt(r.get("cluster_top1")), _fmt(r.get("cluster_top3"))]
        if rerank:
            row += [_fmt(r.get("rerank_top1")), _fmt(r.get("rerank_top3"))]
        if rerank and cluster:
            row += [
                _fmt(r.get("rerank_cluster_top1")),
                _fmt(r.get("rerank_cluster_top3")),
            ]
        table.add_row(*row)
    console.print(table)

    out_path = SUPPORT_MODELS_DIR / "benchmark_3way.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    console.log(f"[green]Wrote {out_path}[/green]")


if __name__ == "__main__":
    main()
