"""
Train the Support FAQ intent classifier — one model per language.

Usage:
    python scripts/train_support.py                 # all languages
    python scripts/train_support.py --lang en       # single language
"""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from football_betting.config import SUPPORT_CFG
from football_betting.support.trainer import train_all

console = Console()


@click.command()
@click.option(
    "--lang",
    default="all",
    type=click.Choice(["all", *SUPPORT_CFG.languages], case_sensitive=False),
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
def main(lang: str, dataset_path: Path | None, out_dir: Path | None) -> None:
    """Train per-locale TF-IDF + LR intent classifiers."""
    langs = None if lang.lower() == "all" else [lang.lower()]
    result = train_all(langs=langs, dataset_path=dataset_path, out_dir=out_dir)

    console.rule("[bold green]Summary[/bold green]")
    table = Table()
    table.add_column("Lang")
    table.add_column("#Train", justify="right")
    table.add_column("#Val", justify="right")
    table.add_column("#Classes", justify="right")
    table.add_column("Top-1", justify="right")
    table.add_column("Top-3", justify="right")
    table.add_column("macro-F1", justify="right")
    for s in result["per_language"]:
        m = s["metrics"]
        top1 = m.get("top1_accuracy")
        top3 = m.get("top3_accuracy")
        mf1 = m.get("macro_f1")
        table.add_row(
            str(s["lang"]),
            str(s["n_train"]),
            str(s["n_val"]),
            str(s["n_classes"]),
            f"{top1:.4f}" if top1 is not None else "—",
            f"{top3:.4f}" if top3 is not None else "—",
            f"{mf1:.4f}" if mf1 is not None else "—",
        )
    console.print(table)


if __name__ == "__main__":
    main()
