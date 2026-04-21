"""High-level training helper for the support intent classifier."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

from football_betting.config import SUPPORT_CFG, SUPPORT_DATA_DIR, SUPPORT_MODELS_DIR
from football_betting.support.cluster import IntentClusterer
from football_betting.support.dataset import load_dataset, stratified_split
from football_betting.support.embedding_model import EmbeddingIntentRetriever
from football_betting.support.intent_model import IntentClassifier
from football_betting.support.reranker import CrossEncoderReranker

console = Console()


def train_one_language(
    lang: str,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Train + evaluate + save a single-locale intent classifier."""
    ds_path = dataset_path or (SUPPORT_DATA_DIR / SUPPORT_CFG.dataset_filename)
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)

    console.rule(f"[bold cyan]Support intent classifier — {lang}[/bold cyan]")

    rows = load_dataset(path=ds_path, lang=lang)
    if not rows:
        raise RuntimeError(f"No rows for language '{lang}' in {ds_path}")

    split = stratified_split(rows)
    console.log(
        f"Loaded {len(rows)} rows · "
        f"train={split.n_train} val={split.n_val} intents={split.n_classes}"
    )

    clf = IntentClassifier(lang=lang)
    fit_info = clf.fit(split.X_train, split.y_train)
    console.log(
        f"Fit done · n_samples={fit_info['n_samples']} "
        f"n_classes={fit_info['n_classes']}"
    )

    val_chapters = [m["chapter"] for m in split.meta_val]
    metrics = clf.evaluate(split.X_val, split.y_val, chapters=val_chapters)

    out_path = out / SUPPORT_CFG.model_filename_template.format(lang=lang)
    clf.save(out_path)
    console.log(f"[green]Saved: {out_path}[/green]")

    top1 = metrics.get("top1_accuracy")
    top3 = metrics.get("top3_accuracy")
    macro_f1 = metrics.get("macro_f1")
    if top1 is not None:
        console.print(
            f"  top1={top1:.4f}  top3={top3:.4f}  macro-F1={macro_f1:.4f}"
        )
        if top1 < SUPPORT_CFG.min_top1_accuracy:
            console.print(
                f"[red][WARN] top1 {top1:.3f} below hard floor "
                f"{SUPPORT_CFG.min_top1_accuracy}[/red]"
            )
        elif top1 < SUPPORT_CFG.target_top1_accuracy:
            console.print(
                f"[yellow][WARN] top1 {top1:.3f} below target "
                f"{SUPPORT_CFG.target_top1_accuracy}[/yellow]"
            )
    else:
        console.print("[yellow]No validation samples — skipping metrics.[/yellow]")

    return {
        "lang": lang,
        "n_train": split.n_train,
        "n_val": split.n_val,
        "n_classes": split.n_classes,
        "metrics": metrics,
        "model_path": str(out_path),
    }


def train_all(
    langs: list[str] | None = None,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Train all locales, write aggregated metrics JSON, return summary."""
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)
    langs_list = list(langs) if langs else list(SUPPORT_CFG.languages)

    all_stats: list[dict[str, Any]] = []
    for lg in langs_list:
        try:
            stats = train_one_language(lg, dataset_path, out)
            all_stats.append(stats)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]Failed for {lg}: {exc}[/red]")

    metrics_path = out / SUPPORT_CFG.metrics_filename
    payload = {"per_language": all_stats, "config_version": "0.3.1"}
    metrics_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    console.log(f"[green]Wrote metrics: {metrics_path}[/green]")

    return payload


# ───────────────────────── Embedding backend ─────────────────────────


def _log_metrics(label: str, metrics: dict[str, Any]) -> None:
    top1 = metrics.get("top1_accuracy")
    top3 = metrics.get("top3_accuracy")
    macro_f1 = metrics.get("macro_f1")
    if top1 is None:
        console.print(f"[yellow]{label}: no val samples — skipping metrics.[/yellow]")
        return
    console.print(
        f"  {label}: top1={top1:.4f}  top3={top3:.4f}  macro-F1={macro_f1:.4f}"
    )
    if top1 < SUPPORT_CFG.min_top1_accuracy:
        console.print(
            f"[red][WARN] {label}: top1 {top1:.3f} below hard floor "
            f"{SUPPORT_CFG.min_top1_accuracy}[/red]"
        )
    elif top1 < SUPPORT_CFG.target_top1_accuracy:
        console.print(
            f"[yellow][WARN] {label}: top1 {top1:.3f} below target "
            f"{SUPPORT_CFG.target_top1_accuracy}[/yellow]"
        )


def train_embeddings_one_language(
    lang: str,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
    model_name: str | None = None,
    *,
    use_rerank: bool = False,
    reranker_model_name: str | None = None,
    use_cluster: bool = False,
    n_clusters: int | None = None,
    cluster_top_c: int | None = None,
    shared_reranker: CrossEncoderReranker | None = None,
) -> dict[str, Any]:
    """Train + evaluate + save an embedding-based intent retriever.

    Optionally evaluates the cross-encoder reranker and/or the clustered
    hierarchical variant and persists a cluster index to disk.
    """
    ds_path = dataset_path or (SUPPORT_DATA_DIR / SUPPORT_CFG.dataset_filename)
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)

    console.rule(f"[bold magenta]Support intent (embeddings) — {lang}[/bold magenta]")

    rows = load_dataset(path=ds_path, lang=lang)
    if not rows:
        raise RuntimeError(f"No rows for language '{lang}' in {ds_path}")

    split = stratified_split(rows)
    console.log(
        f"Loaded {len(rows)} rows · "
        f"train={split.n_train} val={split.n_val} intents={split.n_classes}"
    )

    retriever = EmbeddingIntentRetriever(lang=lang, model_name=model_name)
    fit_info = retriever.fit(split.X_train, split.y_train)
    console.log(
        f"Fit done · n_samples={fit_info['n_samples']} "
        f"n_classes={fit_info['n_classes']} dim={fit_info['dim']}"
    )

    val_chapters = [m["chapter"] for m in split.meta_val]

    # ─── Base (bi-encoder only) ───
    metrics = retriever.evaluate(split.X_val, split.y_val, chapters=val_chapters)
    _log_metrics("bi-encoder", metrics)

    out_path = out / SUPPORT_CFG.embedding_filename_template.format(lang=lang)
    retriever.save(out_path)
    console.log(f"[green]Saved: {out_path}[/green]")

    result: dict[str, Any] = {
        "lang": lang,
        "backend": "embedding",
        "model_name": model_name or SUPPORT_CFG.embedding_model_name,
        "n_train": split.n_train,
        "n_val": split.n_val,
        "n_classes": split.n_classes,
        "metrics": metrics,
        "model_path": str(out_path),
    }

    # ─── Clustering (fit once, used by both cluster-only + rerank+cluster) ───
    clusterer: IntentClusterer | None = None
    if use_cluster:
        nc = n_clusters if n_clusters is not None else SUPPORT_CFG.cluster_count
        clusterer = IntentClusterer(lang=lang, n_clusters=nc)
        cluster_info = clusterer.fit(retriever)
        console.log(
            f"Clusters: k={cluster_info['n_clusters']}  "
            f"mean_size={cluster_info['mean_cluster_size']:.2f}  "
            f"min={cluster_info['min_cluster_size']}  max={cluster_info['max_cluster_size']}"
        )
        cluster_path = out / SUPPORT_CFG.cluster_filename_template.format(lang=lang)
        clusterer.save(cluster_path)
        console.log(f"[green]Saved: {cluster_path}[/green]")
        result["cluster_info"] = cluster_info
        result["cluster_path"] = str(cluster_path)

        # Precompute allowed intents per val query
        if split.X_val:
            q_mat = retriever._encode_queries(split.X_val)
            allowed_per_q = clusterer.allowed_for_batch(q_mat, c=cluster_top_c)
            metrics_cluster = retriever.evaluate(
                split.X_val,
                split.y_val,
                chapters=val_chapters,
                allowed_intents_per_query=allowed_per_q,
            )
            _log_metrics("cluster-filtered", metrics_cluster)
            result["metrics_cluster"] = metrics_cluster

    # ─── Reranker (optionally combined with cluster-filter) ───
    if use_rerank:
        reranker = shared_reranker or CrossEncoderReranker(
            model_name=reranker_model_name
        )
        metrics_rerank = retriever.evaluate(
            split.X_val,
            split.y_val,
            chapters=val_chapters,
            reranker=reranker,
        )
        _log_metrics("rerank", metrics_rerank)
        result["metrics_rerank"] = metrics_rerank
        result["reranker_model_name"] = (
            reranker_model_name or SUPPORT_CFG.reranker_model_name
        )

        if clusterer is not None and split.X_val:
            q_mat = retriever._encode_queries(split.X_val)
            allowed_per_q = clusterer.allowed_for_batch(q_mat, c=cluster_top_c)
            metrics_rerank_cluster = retriever.evaluate(
                split.X_val,
                split.y_val,
                chapters=val_chapters,
                reranker=reranker,
                allowed_intents_per_query=allowed_per_q,
            )
            _log_metrics("rerank+cluster", metrics_rerank_cluster)
            result["metrics_rerank_cluster"] = metrics_rerank_cluster

    return result


def train_embeddings_all(
    langs: list[str] | None = None,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
    model_name: str | None = None,
    *,
    use_rerank: bool = False,
    reranker_model_name: str | None = None,
    use_cluster: bool = False,
    n_clusters: int | None = None,
    cluster_top_c: int | None = None,
) -> dict[str, Any]:
    """Train embedding retrievers for all locales and dump aggregated metrics."""
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)
    langs_list = list(langs) if langs else list(SUPPORT_CFG.languages)

    # Share one cross-encoder across languages to avoid reloading ~1 GB.
    shared_reranker: CrossEncoderReranker | None = None
    if use_rerank:
        shared_reranker = CrossEncoderReranker(model_name=reranker_model_name)

    all_stats: list[dict[str, Any]] = []
    for lg in langs_list:
        try:
            stats = train_embeddings_one_language(
                lg,
                dataset_path=dataset_path,
                out_dir=out,
                model_name=model_name,
                use_rerank=use_rerank,
                reranker_model_name=reranker_model_name,
                use_cluster=use_cluster,
                n_clusters=n_clusters,
                cluster_top_c=cluster_top_c,
                shared_reranker=shared_reranker,
            )
            all_stats.append(stats)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]Failed for {lg}: {exc}[/red]")

    metrics_path = out / SUPPORT_CFG.embedding_metrics_filename
    payload = {
        "per_language": all_stats,
        "backend": "embedding",
        "model_name": model_name or SUPPORT_CFG.embedding_model_name,
        "reranker_model_name": (
            reranker_model_name or SUPPORT_CFG.reranker_model_name
        ) if use_rerank else None,
        "cluster_count": (
            n_clusters if n_clusters is not None else SUPPORT_CFG.cluster_count
        ) if use_cluster else None,
        "use_rerank": use_rerank,
        "use_cluster": use_cluster,
        "config_version": "0.3.1",
    }
    metrics_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    console.log(f"[green]Wrote metrics: {metrics_path}[/green]")

    return payload
