"""
Train the Support FAQ intent classifier — one model per language.

Usage:
    python scripts/train_support.py                            # all langs, embedding backend
    python scripts/train_support.py --lang en                  # single language
    python scripts/train_support.py --backend tfidf            # legacy TF-IDF + LR
    python scripts/train_support.py --backend embedding        # multilingual-e5
"""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from football_betting.config import SUPPORT_CFG
from football_betting.support.trainer import train_all, train_embeddings_all

console = Console()


@click.command()
@click.option(
    "--lang",
    default="all",
    type=click.Choice(["all", *SUPPORT_CFG.languages], case_sensitive=False),
)
@click.option(
    "--backend",
    default="embedding",
    type=click.Choice(["tfidf", "embedding"], case_sensitive=False),
    help="Intent backend: 'embedding' (multilingual-e5) or 'tfidf' (legacy).",
)
@click.option(
    "--model-name",
    default=None,
    help="Override the sentence-transformers model (embedding backend only).",
)
@click.option(
    "--rerank/--no-rerank",
    default=False,
    help="Evaluate (and use) a BAAI/bge-reranker-base cross-encoder re-ranker.",
)
@click.option(
    "--reranker-model-name",
    default=None,
    help="Override the cross-encoder model (defaults to BAAI/bge-reranker-base).",
)
@click.option(
    "--cluster/--no-cluster",
    default=False,
    help="Build an intent-cluster index and evaluate the hierarchical pipeline.",
)
@click.option(
    "--n-clusters",
    type=int,
    default=None,
    help="Number of theme-clusters (default: SUPPORT_CFG.cluster_count = 80).",
)
@click.option(
    "--cluster-top-c",
    type=int,
    default=None,
    help="Top-C clusters kept at query time (default: SUPPORT_CFG.cluster_top_c = 8).",
)
@click.option(
    "--dataset",
    "dataset_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to dataset_augmented.jsonl (default: data/support_faq/…)",
)
@click.option(
    "--out-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: models/support).",
)
def main(
    lang: str,
    backend: str,
    model_name: str | None,
    rerank: bool,
    reranker_model_name: str | None,
    cluster: bool,
    n_clusters: int | None,
    cluster_top_c: int | None,
    dataset_path: Path | None,
    out_dir: Path | None,
) -> None:
    """Train per-locale intent classifiers (TF-IDF or multilingual embeddings)."""
    langs = None if lang.lower() == "all" else [lang.lower()]
    backend_norm = backend.lower()

    if backend_norm == "embedding":
        result = train_embeddings_all(
            langs=langs,
            dataset_path=dataset_path,
            out_dir=out_dir,
            model_name=model_name,
            use_rerank=rerank,
            reranker_model_name=reranker_model_name,
            use_cluster=cluster,
            n_clusters=n_clusters,
            cluster_top_c=cluster_top_c,
        )
        header = "[bold green]Summary (embedding backend)[/bold green]"
    else:
        if model_name:
            console.log("[yellow]--model-name ignored for tfidf backend.[/yellow]")
        if rerank or cluster:
            console.log("[yellow]--rerank/--cluster only apply to the embedding backend.[/yellow]")
        result = train_all(langs=langs, dataset_path=dataset_path, out_dir=out_dir)
        header = "[bold green]Summary (tfidf backend)[/bold green]"

    console.rule(header)

    def _fmt(x: float | None) -> str:
        return f"{x:.4f}" if isinstance(x, float) else "—"

    has_rerank = any("metrics_rerank" in s for s in result["per_language"])
    has_cluster = any("metrics_cluster" in s for s in result["per_language"])
    has_rc = any("metrics_rerank_cluster" in s for s in result["per_language"])

    table = Table()
    table.add_column("Lang")
    table.add_column("#Train", justify="right")
    table.add_column("#Val", justify="right")
    table.add_column("#Cls", justify="right")
    table.add_column("Top-1", justify="right")
    table.add_column("Top-3", justify="right")
    table.add_column("macro-F1", justify="right")
    if has_cluster:
        table.add_column("Cl t1", justify="right")
        table.add_column("Cl t3", justify="right")
    if has_rerank:
        table.add_column("Re t1", justify="right")
        table.add_column("Re t3", justify="right")
    if has_rc:
        table.add_column("R+C t1", justify="right")
        table.add_column("R+C t3", justify="right")

    for s in result["per_language"]:
        m = s["metrics"]
        row = [
            str(s["lang"]),
            str(s["n_train"]),
            str(s["n_val"]),
            str(s["n_classes"]),
            _fmt(m.get("top1_accuracy")),
            _fmt(m.get("top3_accuracy")),
            _fmt(m.get("macro_f1")),
        ]
        if has_cluster:
            mc = s.get("metrics_cluster") or {}
            row += [_fmt(mc.get("top1_accuracy")), _fmt(mc.get("top3_accuracy"))]
        if has_rerank:
            mr = s.get("metrics_rerank") or {}
            row += [_fmt(mr.get("top1_accuracy")), _fmt(mr.get("top3_accuracy"))]
        if has_rc:
            mrc = s.get("metrics_rerank_cluster") or {}
            row += [_fmt(mrc.get("top1_accuracy")), _fmt(mrc.get("top3_accuracy"))]
        table.add_row(*row)
    console.print(table)


if __name__ == "__main__":
    main()
