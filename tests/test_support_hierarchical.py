"""Tests for the hierarchical (Pachinko) support intent classifier + OOD."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from football_betting.config import SUPPORT_CFG
from football_betting.support.dataset import load_dataset, stratified_split
from football_betting.support.hierarchical import (
    HierarchicalIntentClassifier,
    HierarchicalPrediction,
)
from football_betting.support.ood import build_ood_rows, get_seed_bank
from football_betting.support.trainer import train_hierarchical_one_language


# ───────────────────────── Fixtures ─────────────────────────


def _row(
    intent_id: str,
    lang: str,
    chapter: str,
    question: str,
    *,
    source: str = "paraphrase",
    variant: int = 0,
) -> dict[str, object]:
    return {
        "id": intent_id,
        "lang": lang,
        "chapter": chapter,
        "question": question,
        "answer": f"Answer for {intent_id}.",
        "tags": [intent_id],
        "variant": variant,
        "source": source,
    }


@pytest.fixture
def hier_dataset(tmp_path: Path) -> Path:
    """2 chapters × 2 intents × 15 paraphrases, English only."""
    rows: list[dict[str, object]] = []
    templates = {
        ("general", "value-bet"): [
            "what is a value bet",
            "explain value bet",
            "define value bet please",
            "what does value bet mean",
            "meaning of value bet",
            "tell me about value bets",
            "how is a value bet defined",
            "value bet definition",
            "what is edge in betting",
            "why does a value bet matter",
            "can you explain value bet",
            "is this a value bet",
            "value bet meaning",
            "what is a plus ev bet",
            "describe a value bet",
        ],
        ("general", "accuracy"): [
            "how accurate are predictions",
            "what is the model accuracy",
            "prediction accuracy",
            "how good is the model",
            "model performance",
            "is the model accurate",
            "accuracy of predictions",
            "how reliable are predictions",
            "what accuracy does the model have",
            "measure model accuracy",
            "prediction performance",
            "how precise is the model",
            "what accuracy should i expect",
            "trust in model predictions",
            "how good are forecasts",
        ],
        ("strategy", "kelly"): [
            "what is the kelly criterion",
            "explain kelly staking",
            "define kelly",
            "how does kelly sizing work",
            "what is fractional kelly",
            "kelly criterion meaning",
            "kelly formula",
            "how to use kelly",
            "why use kelly staking",
            "kelly stake explanation",
            "what is the kelly fraction",
            "kelly bet sizing",
            "is kelly safe",
            "kelly criterion definition",
            "kelly staking explain",
        ],
        ("strategy", "bankroll"): [
            "what is bankroll management",
            "how to manage my bankroll",
            "bankroll sizing",
            "explain bankroll",
            "manage betting bankroll",
            "bankroll strategy",
            "how big should bankroll be",
            "starting bankroll size",
            "protect my bankroll",
            "bankroll rules",
            "what is a betting bankroll",
            "bankroll management basics",
            "why manage bankroll",
            "bankroll discipline",
            "bankroll growth strategy",
        ],
    }
    for (chap, intent), qs in templates.items():
        for i, q in enumerate(qs):
            src = "original" if i == 0 else "paraphrase"
            rows.append(_row(intent, "en", chap, q, source=src, variant=i))

    path = tmp_path / "dataset_augmented.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


# ───────────────────────── OOD seed bank ─────────────────────────


def test_ood_seed_bank_has_all_languages() -> None:
    for lg in SUPPORT_CFG.languages:
        seeds = get_seed_bank(lg)
        assert len(seeds) >= 25, f"{lg}: too few OOD seeds ({len(seeds)})"
        kinds = {s.kind for s in seeds}
        assert kinds == {"ood_generic", "id_oos"}


def test_build_ood_rows_schema() -> None:
    rows = build_ood_rows("en")
    assert rows
    for r in rows:
        assert r["id"] == SUPPORT_CFG.ood_label
        assert r["chapter"] == SUPPORT_CFG.ood_chapter
        assert r["lang"] == "en"
        assert isinstance(r["question"], str) and r["question"]
        assert str(r["source"]).startswith("ood_seed:")


def test_load_dataset_with_ood_injection(hier_dataset: Path) -> None:
    without = load_dataset(hier_dataset, lang="en", include_ood=False)
    with_ood = load_dataset(hier_dataset, lang="en", include_ood=True)
    assert len(with_ood) > len(without)
    assert any(r["id"] == SUPPORT_CFG.ood_label for r in with_ood)
    assert not any(r["id"] == SUPPORT_CFG.ood_label for r in without)


# ───────────────────────── Hierarchical classifier ─────────────────────────


def test_hier_fit_predict_topk(hier_dataset: Path) -> None:
    rows = load_dataset(hier_dataset, lang="en")
    split = stratified_split(rows)
    chaps = [m["chapter"] for m in split.meta_train]

    clf = HierarchicalIntentClassifier(lang="en")
    info = clf.fit(split.X_train, split.y_train, chaps)
    assert info["n_chapters"] == 2
    assert info["n_leaf_heads"] == 2
    assert info["n_intents"] == 4

    top3 = clf.predict_topk("what is kelly staking", k=3)
    assert len(top3) == 3
    assert all(isinstance(p, HierarchicalPrediction) for p in top3)
    assert top3[0].intent_id == "kelly"
    assert top3[0].chapter == "strategy"
    assert 0.0 < top3[0].chapter_score <= 1.0
    assert top3[0].score <= top3[0].chapter_score  # joint ≤ marginal


def test_hier_proba_batch_shape_and_sum(hier_dataset: Path) -> None:
    rows = load_dataset(hier_dataset, lang="en")
    split = stratified_split(rows)
    chaps = [m["chapter"] for m in split.meta_train]

    clf = HierarchicalIntentClassifier(lang="en")
    clf.fit(split.X_train, split.y_train, chaps)

    probs = clf.predict_proba_batch(["explain value bet", "kelly formula"])
    assert probs.shape == (2, len(clf.classes_))
    # Row sums ≈ 1.0 since leaf heads are proper distributions per chapter.
    assert all(0.99 <= probs[i].sum() <= 1.01 for i in range(probs.shape[0]))


def test_hier_save_load_roundtrip(hier_dataset: Path, tmp_path: Path) -> None:
    rows = load_dataset(hier_dataset, lang="en")
    split = stratified_split(rows)
    chaps = [m["chapter"] for m in split.meta_train]

    clf = HierarchicalIntentClassifier(lang="en")
    clf.fit(split.X_train, split.y_train, chaps)

    path = tmp_path / "support_hier_en.joblib"
    clf.save(path)
    loaded = HierarchicalIntentClassifier.load(path)
    assert loaded.lang == "en"
    assert loaded.topic_labels_ == clf.topic_labels_
    assert set(loaded.leaf_clfs.keys()) == set(clf.leaf_clfs.keys())

    q = "how accurate is the model"
    assert loaded.predict(q).intent_id == clf.predict(q).intent_id


def test_hier_untrained_raises() -> None:
    clf = HierarchicalIntentClassifier(lang="en")
    with pytest.raises(RuntimeError):
        clf.predict("hello")


def test_hier_ood_detected_when_trained_with_seeds(hier_dataset: Path) -> None:
    rows = load_dataset(hier_dataset, lang="en", include_ood=True)
    split = stratified_split(rows)
    chaps = [m["chapter"] for m in split.meta_train]

    clf = HierarchicalIntentClassifier(lang="en")
    clf.fit(split.X_train, split.y_train, chaps)

    # Off-topic queries should be routed to OOD.
    for q in ("what is the weather in berlin", "recipe for carbonara"):
        pred = clf.predict(q)
        assert pred.is_ood, f"Expected OOD for {q!r}, got {pred}"
        assert pred.intent_id == SUPPORT_CFG.ood_label

    # In-domain queries should still route to a real intent.
    pred = clf.predict("explain kelly staking")
    assert not pred.is_ood
    assert pred.intent_id == "kelly"


# ───────────────────────── Trainer wiring ─────────────────────────


def test_train_hierarchical_one_language_end_to_end(
    hier_dataset: Path, tmp_path: Path
) -> None:
    stats = train_hierarchical_one_language(
        "en",
        dataset_path=hier_dataset,
        out_dir=tmp_path,
        include_ood=True,
    )
    assert stats["lang"] == "en"
    assert stats["backend"] == "hierarchical"
    assert Path(str(stats["model_path"])).exists()

    metrics = stats["metrics"]
    if metrics["top1_accuracy"] is not None:
        assert metrics["top1_accuracy"] >= 0.5
        assert metrics["top3_accuracy"] >= metrics["top1_accuracy"]
        assert "per_chapter_top1" in metrics
