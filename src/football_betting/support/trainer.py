"""High-level training helper for the support intent classifier."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

from football_betting.config import SUPPORT_CFG, SUPPORT_DATA_DIR, SUPPORT_MODELS_DIR
from football_betting.support.dataset import load_dataset, stratified_split
from football_betting.support.intent_model import IntentClassifier

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
