"""Load + split the augmented support FAQ dataset."""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from football_betting.config import SUPPORT_CFG, SUPPORT_DATA_DIR


@dataclass(slots=True)
class DatasetSplit:
    """Train/val split for a single language."""

    lang: str
    X_train: list[str]
    y_train: list[str]
    X_val: list[str]
    y_val: list[str]
    labels: list[str]  # sorted unique intent ids
    meta_train: list[dict[str, str]]
    meta_val: list[dict[str, str]]

    @property
    def n_train(self) -> int:
        return len(self.X_train)

    @property
    def n_val(self) -> int:
        return len(self.X_val)

    @property
    def n_classes(self) -> int:
        return len(self.labels)


def _default_dataset_path() -> Path:
    return SUPPORT_DATA_DIR / SUPPORT_CFG.dataset_filename


def load_dataset(
    path: Path | None = None,
    lang: str | None = None,
    *,
    include_ood: bool = False,
) -> list[dict[str, object]]:
    """Load JSONL rows, optionally filtered by language.

    When ``include_ood=True`` the curated OOD seed bank for ``lang`` (or for
    every language, if ``lang is None``) is appended to the returned rows.
    The seeds share the standard schema so they flow through
    :func:`stratified_split` like any other utterance.
    """
    p = path or _default_dataset_path()
    if not p.exists():
        raise FileNotFoundError(f"Support FAQ dataset not found: {p}")

    rows: list[dict[str, object]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if lang is not None and row.get("lang") != lang:
                continue
            rows.append(row)

    if include_ood:
        from football_betting.support.ood import build_ood_rows

        langs = [lang] if lang is not None else list(SUPPORT_CFG.languages)
        for lg in langs:
            try:
                rows.extend(build_ood_rows(lg))
            except KeyError:
                # Unknown language — silently skip, nothing to seed.
                pass
    return rows


def stratified_split(
    rows: list[dict[str, object]],
    val_fraction: float = SUPPORT_CFG.val_fraction,
    random_seed: int = SUPPORT_CFG.random_seed,
) -> DatasetSplit:
    """Stratified train/val split on intent `id`.

    Guarantees:
    - Every intent appears in train (at least 1 sample).
    - Rows tagged ``source == "original"`` are always placed in train so the
      canonical phrasing is never hidden from the model.
    - If only one sample exists for an intent it goes to train (val skipped).
    """
    import random

    if not rows:
        raise ValueError("Empty dataset — cannot split.")

    by_intent: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_intent[str(row["id"])].append(row)

    rng = random.Random(random_seed)

    X_train: list[str] = []
    y_train: list[str] = []
    X_val: list[str] = []
    y_val: list[str] = []
    meta_train: list[dict[str, str]] = []
    meta_val: list[dict[str, str]] = []

    lang_set = {str(r.get("lang", "")) for r in rows}
    if len(lang_set) != 1:
        raise ValueError(
            f"stratified_split expects a single language, got {sorted(lang_set)}"
        )
    (lang,) = lang_set

    for intent_id, items in by_intent.items():
        # Pin originals to train.
        originals = [r for r in items if r.get("source") == "original"]
        paraphrases = [r for r in items if r.get("source") != "original"]

        rng.shuffle(paraphrases)
        n_val = int(round(len(paraphrases) * val_fraction))
        val_rows = paraphrases[:n_val]
        train_rows = originals + paraphrases[n_val:]

        if not train_rows:  # pathological: only one paraphrase, no original
            train_rows = val_rows
            val_rows = []

        for r in train_rows:
            X_train.append(str(r["question"]))
            y_train.append(intent_id)
            meta_train.append({"chapter": str(r.get("chapter", "")),
                                "source": str(r.get("source", ""))})
        for r in val_rows:
            X_val.append(str(r["question"]))
            y_val.append(intent_id)
            meta_val.append({"chapter": str(r.get("chapter", "")),
                              "source": str(r.get("source", ""))})

    labels = sorted(by_intent.keys())
    return DatasetSplit(
        lang=lang,
        X_train=X_train, y_train=y_train,
        X_val=X_val, y_val=y_val,
        labels=labels,
        meta_train=meta_train, meta_val=meta_val,
    )
