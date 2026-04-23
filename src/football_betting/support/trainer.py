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
from football_betting.support.hierarchical import HierarchicalIntentClassifier
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
    console.log(f"Fit done · n_samples={fit_info['n_samples']} n_classes={fit_info['n_classes']}")

    val_chapters = [m["chapter"] for m in split.meta_val]
    metrics = clf.evaluate(split.X_val, split.y_val, chapters=val_chapters)

    out_path = out / SUPPORT_CFG.model_filename_template.format(lang=lang)
    clf.save(out_path)
    console.log(f"[green]Saved: {out_path}[/green]")

    top1 = metrics.get("top1_accuracy")
    top3 = metrics.get("top3_accuracy")
    macro_f1 = metrics.get("macro_f1")
    if top1 is not None:
        console.print(f"  top1={top1:.4f}  top3={top3:.4f}  macro-F1={macro_f1:.4f}")
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
    console.print(f"  {label}: top1={top1:.4f}  top3={top3:.4f}  macro-F1={macro_f1:.4f}")
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
        reranker = shared_reranker or CrossEncoderReranker(model_name=reranker_model_name)
        metrics_rerank = retriever.evaluate(
            split.X_val,
            split.y_val,
            chapters=val_chapters,
            reranker=reranker,
        )
        _log_metrics("rerank", metrics_rerank)
        result["metrics_rerank"] = metrics_rerank
        result["reranker_model_name"] = reranker_model_name or SUPPORT_CFG.reranker_model_name

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


# ───────────────────────── Hierarchical (Pachinko) backend ─────────────────────────


def train_hierarchical_one_language(
    lang: str,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
    *,
    include_ood: bool = True,
) -> dict[str, Any]:
    """Train + evaluate + save the chapter→intent Pachinko classifier."""
    ds_path = dataset_path or (SUPPORT_DATA_DIR / SUPPORT_CFG.dataset_filename)
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)

    console.rule(f"[bold green]Support intent (hierarchical) — {lang}[/bold green]")

    rows = load_dataset(path=ds_path, lang=lang, include_ood=include_ood)
    if not rows:
        raise RuntimeError(f"No rows for language '{lang}' in {ds_path}")

    split = stratified_split(rows)
    console.log(
        f"Loaded {len(rows)} rows · "
        f"train={split.n_train} val={split.n_val} intents={split.n_classes} "
        f"(ood_seeds_included={include_ood})"
    )

    y_chap_train = [m["chapter"] for m in split.meta_train]
    y_chap_val = [m["chapter"] for m in split.meta_val]

    clf = HierarchicalIntentClassifier(lang=lang)
    fit_info = clf.fit(split.X_train, split.y_train, y_chap_train)
    console.log(
        f"Fit done · chapters={fit_info['n_chapters']} "
        f"leaf_heads={fit_info['n_leaf_heads']} intents={fit_info['n_intents']}"
    )

    metrics = clf.evaluate(split.X_val, split.y_val, chapters=y_chap_val)
    _log_metrics("hierarchical", metrics)
    if metrics.get("ood_precision") is not None:
        console.print(
            f"  OOD precision={metrics['ood_precision']:.3f}  recall={metrics['ood_recall']:.3f}"
        )

    out_path = out / SUPPORT_CFG.hierarchical_model_filename_template.format(lang=lang)
    clf.save(out_path)
    console.log(f"[green]Saved: {out_path}[/green]")

    return {
        "lang": lang,
        "backend": "hierarchical",
        "n_train": split.n_train,
        "n_val": split.n_val,
        "n_classes": split.n_classes,
        "metrics": metrics,
        "model_path": str(out_path),
        "fit_info": fit_info,
    }


def train_hierarchical_all(
    langs: list[str] | None = None,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
    *,
    include_ood: bool = True,
) -> dict[str, Any]:
    """Train the hierarchical classifier for every requested locale."""
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)
    langs_list = list(langs) if langs else list(SUPPORT_CFG.languages)

    all_stats: list[dict[str, Any]] = []
    for lg in langs_list:
        try:
            stats = train_hierarchical_one_language(
                lg,
                dataset_path=dataset_path,
                out_dir=out,
                include_ood=include_ood,
            )
            all_stats.append(stats)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]Failed for {lg}: {exc}[/red]")

    metrics_path = out / SUPPORT_CFG.hierarchical_metrics_filename
    payload = {
        "per_language": all_stats,
        "backend": "hierarchical",
        "include_ood": include_ood,
        "config_version": "0.3.2",
    }
    metrics_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    console.log(f"[green]Wrote metrics: {metrics_path}[/green]")

    return payload


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
        "reranker_model_name": (reranker_model_name or SUPPORT_CFG.reranker_model_name)
        if use_rerank
        else None,
        "cluster_count": (n_clusters if n_clusters is not None else SUPPORT_CFG.cluster_count)
        if use_cluster
        else None,
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


# ───────────────────────── Transformer backend (M3) ─────────────────────────


def _subsample_per_intent(rows: list[Any], max_per_intent: int, *, seed: int = 42) -> list[Any]:
    """Cap rows at ``max_per_intent`` per intent (deterministic).

    Preserves class balance for smoke/HPO runs without having to materialise
    a smaller JSONL on disk. Intent attribute is read defensively so the
    helper works for both :class:`SupportRow` dataclasses and plain dicts.
    """
    import random as _random
    from collections import defaultdict

    rng = _random.Random(seed)
    buckets: dict[str, list[Any]] = defaultdict(list)
    for r in rows:
        # Support FAQ rows use key "id" for the intent label; fall back
        # to "intent" for legacy/alternate shapes (incl. attr access).
        if isinstance(r, dict):
            intent = r.get("id") or r.get("intent")
        else:
            intent = getattr(r, "id", None) or getattr(r, "intent", None)
        buckets[str(intent)].append(r)

    out: list[Any] = []
    for intent, bucket in buckets.items():
        if len(bucket) > max_per_intent:
            bucket = rng.sample(bucket, max_per_intent)
        out.extend(bucket)
    rng.shuffle(out)
    return out


def train_transformer_one_language(
    lang: str,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
    backbone: str | None = None,
    *,
    include_ood: bool = True,
    seed: int = 42,
    calibrate: bool = True,
    epochs: int | None = None,
    max_rows_per_intent: int | None = None,
) -> dict[str, Any]:
    """Fine-tune XLM-R with CE + SupCon for one language.

    After training the classifier is evaluated with *chapters wired in*
    (per-chapter top-1 & macro-F1, per-intent F1, top confusions) and an
    optional :class:`TemperatureCalibrator` is fit on validation logits
    (written next to the HF artefact as ``temperature.json``).

    ``epochs`` / ``max_rows_per_intent`` are runtime overrides intended for
    smoke tests and HPO sweeps without having to mutate :class:`SupportConfig`
    defaults.
    """
    from dataclasses import replace as dc_replace

    from football_betting.support.calibration import TemperatureCalibrator
    from football_betting.support.reproducibility import seed_all
    from football_betting.support.transformer_model import (
        TransformerIntentClassifier,
        resolve_backbone,
    )

    seed_info = seed_all(seed)

    ds_path = dataset_path or (SUPPORT_DATA_DIR / SUPPORT_CFG.augmented_v3_filename)
    if not ds_path.exists():
        ds_path = SUPPORT_DATA_DIR / SUPPORT_CFG.augmented_v2_filename
    if not ds_path.exists():
        ds_path = SUPPORT_DATA_DIR / SUPPORT_CFG.dataset_filename
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)

    console.rule(f"[bold magenta]Support transformer - {lang}[/bold magenta]")

    rows = load_dataset(path=ds_path, lang=lang, include_ood=include_ood)
    if not rows:
        raise RuntimeError(f"No rows for language '{lang}' in {ds_path}")

    if max_rows_per_intent is not None and max_rows_per_intent > 0:
        rows = _subsample_per_intent(rows, max_rows_per_intent, seed=seed)
        console.log(
            f"[yellow]Subsampled to <={max_rows_per_intent} rows/intent "
            f"-> {len(rows)} total (smoke mode)[/yellow]"
        )

    split = stratified_split(rows)
    console.log(
        f"Loaded {len(rows)} rows | train={split.n_train} val={split.n_val} "
        f"intents={split.n_classes} (ood={include_ood}) seed={seed}"
    )

    resolved = backbone or resolve_backbone(lang)
    console.log(f"Backbone: {resolved}")

    cfg = SUPPORT_CFG
    if epochs is not None and epochs > 0:
        cfg = dc_replace(cfg, transformer_epochs=epochs)
        console.log(f"[yellow]Override: transformer_epochs={epochs}[/yellow]")

    clf = TransformerIntentClassifier(lang=lang, backbone=resolved, cfg=cfg)
    fit_info = clf.fit(
        split.X_train,
        split.y_train,
        X_val=split.X_val,
        y_val=split.y_val,
        verbose=True,
    )
    console.log(
        f"Fit done | n_samples={fit_info['n_samples']} "
        f"n_classes={fit_info['n_classes']} "
        f"best_val_f1={fit_info.get('best_val_macro_f1')}"
    )

    val_chapters = [m["chapter"] for m in split.meta_val]
    metrics = clf.evaluate(split.X_val, split.y_val, chapters=val_chapters)
    _log_metrics("transformer", metrics)

    out_path = out / SUPPORT_CFG.transformer_model_dirname_template.format(lang=lang)
    clf.save(out_path)
    console.log(f"[green]Saved: {out_path}[/green]")

    # ── Calibration (temperature scaling) on val logits ──
    calib_info: dict[str, Any] = {"fitted": False}
    if calibrate:
        import numpy as np

        val_logits = clf.predict_logits_batch(split.X_val)
        class_to_idx = {c: i for i, c in enumerate(clf.classes_)}
        labels_np = np.array([class_to_idx.get(y, -1) for y in split.y_val], dtype=np.int64)
        mask = labels_np >= 0
        if mask.sum() >= 2:
            calibrator = TemperatureCalibrator()
            info = calibrator.fit(val_logits[mask], labels_np[mask])
            calibrator.save(out_path / "temperature.json")
            calib_info = {"fitted": True, **info}
            console.log(
                f"[cyan]Calibrator T={info['temperature']:.3f} "
                f"ECE {info.get('ece_before', '?'):.4f} -> "
                f"{info.get('ece_after', '?'):.4f}[/cyan]"
            )
        else:
            console.log("[yellow]Calibration skipped (not enough val rows)[/yellow]")

    # Device + git sha for reproducibility report.
    device_name = _describe_device()
    git_sha = _git_sha()

    payload: dict[str, Any] = {
        "lang": lang,
        "backend": "transformer",
        "backbone": resolved,
        "n_train": split.n_train,
        "n_val": split.n_val,
        "n_classes": split.n_classes,
        "metrics": metrics,
        "calibration": calib_info,
        "seed": seed_info,
        "device": device_name,
        "git_sha": git_sha,
        "model_path": str(out_path),
        "fit_info": fit_info,
    }

    # Persist a per-language metrics snapshot next to the model so
    # ``train-support-transformer --lang <lg>`` (single-lang runs) leaves
    # the same v0.3.4 reproducibility trail as the aggregated ``--lang all``
    # path. The aggregator continues to write the combined report.
    single_metrics_path = out / SUPPORT_CFG.transformer_metrics_filename.replace(
        ".json", f"_{lang}.json"
    )
    single_report = {
        "per_language": [payload],
        "backend": "transformer",
        "include_ood": include_ood,
        "seed": seed,
        "device": device_name,
        "git_sha": git_sha,
        "config_version": "0.3.4",
    }
    single_metrics_path.write_text(
        json.dumps(single_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    console.log(f"[green]Wrote metrics: {single_metrics_path}[/green]")

    return payload


def train_transformer_all(
    langs: list[str] | None = None,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
    *,
    include_ood: bool = True,
    seed: int = 42,
    calibrate: bool = True,
    epochs: int | None = None,
    max_rows_per_intent: int | None = None,
) -> dict[str, Any]:
    """Fine-tune the transformer backbone per locale and dump aggregated metrics."""
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)
    langs_list = list(langs) if langs else list(SUPPORT_CFG.languages)

    all_stats: list[dict[str, Any]] = []
    for lg in langs_list:
        try:
            stats = train_transformer_one_language(
                lg,
                dataset_path=dataset_path,
                out_dir=out,
                include_ood=include_ood,
                seed=seed,
                calibrate=calibrate,
                epochs=epochs,
                max_rows_per_intent=max_rows_per_intent,
            )
            all_stats.append(stats)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]Failed for {lg}: {exc}[/red]")

    metrics_path = out / SUPPORT_CFG.transformer_metrics_filename
    payload = {
        "per_language": all_stats,
        "backend": "transformer",
        "include_ood": include_ood,
        "seed": seed,
        "device": _describe_device(),
        "git_sha": _git_sha(),
        "config_version": "0.3.4",
    }
    metrics_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    console.log(f"[green]Wrote metrics: {metrics_path}[/green]")

    return payload


# ───────────────────────── Runtime env helpers ─────────────────────────


def _describe_device() -> dict[str, Any]:
    """Return a small dict describing the torch device actually picked up."""
    info: dict[str, Any] = {"kind": "cpu", "name": "cpu"}
    try:
        import torch  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001
        return info
    if torch.cuda.is_available():
        info = {
            "kind": "cuda",
            "name": str(torch.cuda.get_device_name(0)),
            "memory_gb": round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1),
        }
        return info
    try:
        import torch_directml as dml  # type: ignore[import-not-found]

        if dml.device_count() > 0:
            info = {
                "kind": "dml",
                "name": str(dml.device_name(0)),
                "device_count": int(dml.device_count()),
            }
    except Exception:  # noqa: BLE001 — DML not installed
        pass
    return info


def _git_sha() -> str | None:
    """Short git SHA of the working tree (best-effort, returns None on failure)."""
    import subprocess

    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return out.decode("utf-8").strip() or None
    except Exception:  # noqa: BLE001 — git absent or non-repo
        return None


# ───────────────────────── Two-head transformer backend ─────────────────────────


def train_two_head_one_language(
    lang: str,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
    backbone: str | None = None,
    *,
    include_ood: bool = True,
    seed: int = 42,
    calibrate: bool = True,
    epochs: int | None = None,
    max_rows_per_intent: int | None = None,
    cfg_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fine-tune the two-head (chapter + intent) transformer for one language.

    ``cfg_overrides`` applies :func:`dataclasses.replace` to :data:`SUPPORT_CFG`
    (e.g. ``{"chapter_head_weight": 0.5, "transformer_learning_rate": 3e-5}``)
    so HP sweeps don't need to mutate globals.
    """
    from dataclasses import replace as dc_replace

    from football_betting.support.calibration import TemperatureCalibrator
    from football_betting.support.reproducibility import seed_all
    from football_betting.support.transformer_model import resolve_backbone
    from football_betting.support.two_head_transformer import (
        TwoHeadTransformerIntentClassifier,
        _derive_chapter,
    )

    seed_info = seed_all(seed)

    ds_path = dataset_path or (SUPPORT_DATA_DIR / SUPPORT_CFG.augmented_v3_filename)
    if not ds_path.exists():
        ds_path = SUPPORT_DATA_DIR / SUPPORT_CFG.augmented_v2_filename
    if not ds_path.exists():
        ds_path = SUPPORT_DATA_DIR / SUPPORT_CFG.dataset_filename
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)

    console.rule(f"[bold magenta]Support two-head transformer - {lang}[/bold magenta]")

    rows = load_dataset(path=ds_path, lang=lang, include_ood=include_ood)
    if not rows:
        raise RuntimeError(f"No rows for language '{lang}' in {ds_path}")

    if max_rows_per_intent is not None and max_rows_per_intent > 0:
        rows = _subsample_per_intent(rows, max_rows_per_intent, seed=seed)
        console.log(
            f"[yellow]Subsampled to <={max_rows_per_intent} rows/intent "
            f"-> {len(rows)} total (smoke mode)[/yellow]"
        )

    split = stratified_split(rows)
    console.log(
        f"Loaded {len(rows)} rows | train={split.n_train} val={split.n_val} "
        f"intents={split.n_classes} (ood={include_ood}) seed={seed}"
    )

    # Derive chapter labels from meta (with id-prefix fallback for robustness).
    chap_train = [
        _derive_chapter(str(i), m.get("chapter"))
        for i, m in zip(split.y_train, split.meta_train, strict=True)
    ]
    chap_val = [
        _derive_chapter(str(i), m.get("chapter"))
        for i, m in zip(split.y_val, split.meta_val, strict=True)
    ]
    n_chapters = len({*chap_train, *chap_val})
    console.log(f"Chapter labels derived | n_chapters={n_chapters}")

    resolved = backbone or resolve_backbone(lang)
    console.log(f"Backbone: {resolved}")

    cfg = SUPPORT_CFG
    if epochs is not None and epochs > 0:
        cfg = dc_replace(cfg, transformer_epochs=epochs)
        console.log(f"[yellow]Override: transformer_epochs={epochs}[/yellow]")
    if cfg_overrides:
        cfg = dc_replace(cfg, **cfg_overrides)
        console.log(f"[yellow]Override: {cfg_overrides}[/yellow]")
    console.log(
        f"Loss weights: intent_ce={cfg.ce_weight} "
        f"chapter_ce={cfg.chapter_head_weight} supcon={cfg.supcon_weight}"
    )

    clf = TwoHeadTransformerIntentClassifier(lang=lang, backbone=resolved, cfg=cfg)
    fit_info = clf.fit(
        split.X_train,
        split.y_train,
        chap_train,
        X_val=split.X_val,
        y_val=split.y_val,
        chapters_val=chap_val,
        verbose=True,
    )
    console.log(
        f"Fit done | n_samples={fit_info['n_samples']} "
        f"intents={fit_info['n_intents']} chapters={fit_info['n_chapters']} "
        f"best_val_f1={fit_info.get('best_val_macro_f1')}"
    )

    metrics = clf.evaluate(split.X_val, split.y_val, chapters=chap_val)
    _log_metrics("two_head", metrics)
    if metrics.get("chapter_head_top1") is not None:
        console.print(
            f"  chapter_head_top1={metrics['chapter_head_top1']:.3f}  "
            f"chapter_head_macro_f1={metrics['chapter_head_macro_f1']:.3f}"
        )

    out_path = out / SUPPORT_CFG.two_head_model_dirname_template.format(lang=lang)
    clf.save(out_path)
    console.log(f"[green]Saved: {out_path}[/green]")

    # ── Calibration on intent logits ──
    calib_info: dict[str, Any] = {"fitted": False}
    if calibrate:
        import numpy as np

        val_logits = clf.predict_logits_batch(split.X_val)
        class_to_idx = {c: i for i, c in enumerate(clf.classes_)}
        labels_np = np.array([class_to_idx.get(y, -1) for y in split.y_val], dtype=np.int64)
        mask = labels_np >= 0
        if mask.sum() >= 2:
            calibrator = TemperatureCalibrator()
            info = calibrator.fit(val_logits[mask], labels_np[mask])
            calibrator.save(out_path / "temperature.json")
            calib_info = {"fitted": True, **info}
            console.log(
                f"[cyan]Calibrator T={info['temperature']:.3f} "
                f"ECE {info.get('ece_before', '?'):.4f} -> "
                f"{info.get('ece_after', '?'):.4f}[/cyan]"
            )
        else:
            console.log("[yellow]Calibration skipped (not enough val rows)[/yellow]")

    device_name = _describe_device()
    git_sha = _git_sha()

    payload: dict[str, Any] = {
        "lang": lang,
        "backend": "two_head_transformer",
        "backbone": resolved,
        "n_train": split.n_train,
        "n_val": split.n_val,
        "n_classes": split.n_classes,
        "n_chapters": fit_info["n_chapters"],
        "loss_weights": {
            "intent_ce": cfg.ce_weight,
            "chapter_ce": cfg.chapter_head_weight,
            "supcon": cfg.supcon_weight,
            "chapter_gate": cfg.two_head_chapter_gate,
        },
        "metrics": metrics,
        "calibration": calib_info,
        "seed": seed_info,
        "device": device_name,
        "git_sha": git_sha,
        "model_path": str(out_path),
        "fit_info": fit_info,
    }

    single_metrics_path = out / SUPPORT_CFG.two_head_metrics_filename.replace(
        ".json", f"_{lang}.json"
    )
    single_report = {
        "per_language": [payload],
        "backend": "two_head_transformer",
        "include_ood": include_ood,
        "seed": seed,
        "device": device_name,
        "git_sha": git_sha,
        "config_version": "0.3.5",
    }
    single_metrics_path.write_text(
        json.dumps(single_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    console.log(f"[green]Wrote metrics: {single_metrics_path}[/green]")

    return payload


def train_two_head_all(
    langs: list[str] | None = None,
    dataset_path: Path | None = None,
    out_dir: Path | None = None,
    *,
    include_ood: bool = True,
    seed: int = 42,
    calibrate: bool = True,
    epochs: int | None = None,
    max_rows_per_intent: int | None = None,
) -> dict[str, Any]:
    """Fine-tune the two-head transformer per locale and dump aggregated metrics."""
    out = out_dir or SUPPORT_MODELS_DIR
    out.mkdir(parents=True, exist_ok=True)
    langs_list = list(langs) if langs else list(SUPPORT_CFG.languages)

    all_stats: list[dict[str, Any]] = []
    for lg in langs_list:
        try:
            stats = train_two_head_one_language(
                lg,
                dataset_path=dataset_path,
                out_dir=out,
                include_ood=include_ood,
                seed=seed,
                calibrate=calibrate,
                epochs=epochs,
                max_rows_per_intent=max_rows_per_intent,
            )
            all_stats.append(stats)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[red]Failed for {lg}: {exc}[/red]")

    metrics_path = out / SUPPORT_CFG.two_head_metrics_filename
    payload = {
        "per_language": all_stats,
        "backend": "two_head_transformer",
        "include_ood": include_ood,
        "seed": seed,
        "device": _describe_device(),
        "git_sha": _git_sha(),
        "config_version": "0.3.5",
    }
    metrics_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    console.log(f"[green]Wrote metrics: {metrics_path}[/green]")

    return payload
