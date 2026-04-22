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
@click.option(
    "--onnx-int8",
    is_flag=True,
    default=False,
    help="Latency-only mode: benchmark the INT8 ONNX transformer on CPU "
         "(skips the ML/Fuse/Emb accuracy table).",
)
@click.option(
    "--onnx-lang",
    default="de",
    show_default=True,
    help="Language for the ONNX latency benchmark (used with --onnx-int8).",
)
@click.option(
    "--onnx-threads",
    type=int,
    multiple=True,
    default=(1, 4),
    show_default=True,
    help="Thread counts to benchmark (repeat flag for multiple values).",
)
@click.option(
    "--onnx-runs",
    type=int,
    default=100,
    show_default=True,
    help="Number of single-sample inferences per thread-count setting.",
)
@click.option(
    "--onnx-warmup",
    type=int,
    default=10,
    show_default=True,
    help="Warmup runs (excluded from latency stats) per thread-count setting.",
)
@click.option(
    "--onnx-p95-target-ms",
    type=float,
    default=120.0,
    show_default=True,
    help="p95 latency ceiling (ms). Script exits non-zero if any setting exceeds it.",
)
def main(
    rerank: bool,
    cluster: bool,
    reranker_model_name: str | None,
    cluster_top_c: int | None,
    onnx_int8: bool,
    onnx_lang: str,
    onnx_threads: tuple[int, ...],
    onnx_runs: int,
    onnx_warmup: int,
    onnx_p95_target_ms: float,
) -> None:
    if onnx_int8:
        _bench_onnx_int8(
            lang=onnx_lang,
            thread_counts=list(onnx_threads),
            n_runs=onnx_runs,
            n_warmup=onnx_warmup,
            p95_target_ms=onnx_p95_target_ms,
        )
        return

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


# ───────────────────────── ONNX INT8 latency benchmark ─────────────────────────


def _bench_onnx_int8(
    *,
    lang: str,
    thread_counts: list[int],
    n_runs: int,
    n_warmup: int,
    p95_target_ms: float,
) -> None:
    """Single-sentence CPU latency benchmark on the INT8 ONNX transformer.

    Loads ``models/support/support_transformer_<lang>/model.int8.onnx`` (or
    ``model.onnx`` as a fallback) and the colocated tokenizer, then runs
    ``n_warmup + n_runs`` single-sentence inferences per thread-count setting
    using different realistic DE queries to avoid per-input caching effects.
    """
    import statistics
    import sys
    import time

    try:
        import numpy as np
        import onnxruntime as ort  # type: ignore[import-not-found]
        from transformers import AutoTokenizer  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        console.log(f"[red]ONNX bench requires onnxruntime + transformers: {exc}[/red]")
        sys.exit(2)

    dirname = SUPPORT_CFG.transformer_model_dirname_template.format(lang=lang)
    model_dir = SUPPORT_MODELS_DIR / dirname
    int8_path = model_dir / "model.int8.onnx"
    fp32_path = model_dir / "model.onnx"
    if int8_path.exists():
        onnx_path = int8_path
        mode = "INT8"
    elif fp32_path.exists():
        onnx_path = fp32_path
        mode = "fp32 (INT8 missing)"
    else:
        console.log(
            f"[red]No ONNX file under {model_dir} "
            f"(expected model.int8.onnx or model.onnx).[/red]"
        )
        sys.exit(3)

    console.rule(f"[cyan]ONNX latency — {lang} ({mode})[/cyan]")
    console.log(f"Model:  {onnx_path} ({onnx_path.stat().st_size / 1024:.0f} KiB)")

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    max_len = SUPPORT_CFG.transformer_max_seq_length

    # A small pool of DE queries — tokenising different strings avoids any
    # tensor-caching artefacts that would flatter the numbers.
    sample_queries = [
        "Wie berechnet ihr den Value einer Wette?",
        "Was ist das Kelly-Kriterium?",
        "Kann ich meine Einzahlung zurückbuchen lassen?",
        "Was ist ein Systemschein?",
        "Wie lange dauert eine Auszahlung?",
        "Zeigt die App auch Live-Quoten?",
        "Wie ändere ich mein Passwort?",
        "Was bedeutet CLV in der Performance-Historie?",
        "Warum ist mein Tipp nicht gewertet worden?",
        "Welche Sportarten bietet ihr an?",
    ]

    rows: list[dict[str, object]] = []
    any_over_budget = False
    for threads in thread_counts:
        sess_options = ort.SessionOptions()
        sess_options.intra_op_num_threads = int(threads)
        sess_options.inter_op_num_threads = 1
        session = ort.InferenceSession(
            str(onnx_path),
            sess_options=sess_options,
            providers=["CPUExecutionProvider"],
        )

        # Warmup
        for i in range(n_warmup):
            enc = tokenizer(
                sample_queries[i % len(sample_queries)],
                return_tensors="np",
                padding="max_length",
                truncation=True,
                max_length=max_len,
            )
            session.run(
                ["logits"],
                {
                    "input_ids": enc["input_ids"].astype(np.int64),
                    "attention_mask": enc["attention_mask"].astype(np.int64),
                },
            )

        latencies_ms: list[float] = []
        for i in range(n_runs):
            query = sample_queries[i % len(sample_queries)]
            enc = tokenizer(
                query,
                return_tensors="np",
                padding="max_length",
                truncation=True,
                max_length=max_len,
            )
            feed = {
                "input_ids": enc["input_ids"].astype(np.int64),
                "attention_mask": enc["attention_mask"].astype(np.int64),
            }
            t0 = time.perf_counter()
            session.run(["logits"], feed)
            latencies_ms.append((time.perf_counter() - t0) * 1000.0)

        latencies_ms.sort()
        p50 = latencies_ms[int(0.50 * len(latencies_ms))]
        p95 = latencies_ms[int(0.95 * len(latencies_ms))]
        p99 = latencies_ms[int(0.99 * len(latencies_ms))]
        mean = statistics.fmean(latencies_ms)
        over = p95 > p95_target_ms
        any_over_budget = any_over_budget or over
        status = "[red]OVER BUDGET[/red]" if over else "[green]ok[/green]"
        console.log(
            f"threads={threads:>2d}  runs={n_runs:>3d}  "
            f"mean={mean:6.2f}ms  p50={p50:6.2f}ms  "
            f"p95={p95:6.2f}ms  p99={p99:6.2f}ms  {status}"
        )
        rows.append(
            {
                "lang": lang,
                "onnx_path": str(onnx_path),
                "mode": mode,
                "threads": int(threads),
                "n_runs": int(n_runs),
                "n_warmup": int(n_warmup),
                "mean_ms": round(mean, 3),
                "p50_ms": round(p50, 3),
                "p95_ms": round(p95, 3),
                "p99_ms": round(p99, 3),
                "p95_target_ms": p95_target_ms,
                "over_budget": over,
            }
        )

    out_path = SUPPORT_MODELS_DIR / f"benchmark_onnx_latency_{lang}.json"
    out_path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    console.log(f"[green]Wrote {out_path}[/green]")
    if any_over_budget:
        console.log(f"[red]At least one setting exceeded p95={p95_target_ms}ms.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
