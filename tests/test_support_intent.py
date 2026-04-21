"""Tests for the support FAQ intent classifier."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from football_betting.support.dataset import load_dataset, stratified_split
from football_betting.support.intent_model import IntentClassifier, IntentPrediction
from football_betting.support.text import normalize
from football_betting.support.trainer import train_one_language


# ───────────────────────── Fixtures ─────────────────────────


def _make_row(
    intent_id: str,
    lang: str,
    question: str,
    *,
    source: str = "paraphrase",
    chapter: str = "general",
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
def tiny_dataset(tmp_path: Path) -> Path:
    """Minimal JSONL with 3 intents × 15 rows × 2 langs."""
    rows: list[dict[str, object]] = []
    templates_en = {
        "value-bet": [
            "What is a value bet?",
            "Explain value bet",
            "Define value bet please",
            "What does value bet mean",
            "Meaning of value bet",
            "Tell me about value bets",
            "How is a value bet defined",
            "value bet definition",
            "What is edge in betting",
            "Why does a value bet matter",
            "Can you explain value bet",
            "Is this a value bet",
            "Value bet meaning",
            "What is a +EV bet",
            "Describe a value bet",
        ],
        "kelly": [
            "What is the Kelly criterion",
            "Explain Kelly staking",
            "Define Kelly",
            "How does Kelly sizing work",
            "What is fractional Kelly",
            "Kelly criterion meaning",
            "Kelly formula",
            "How to use Kelly",
            "Why use Kelly staking",
            "Kelly stake explanation",
            "What is the Kelly fraction",
            "Kelly bet sizing",
            "Is Kelly safe",
            "Kelly criterion definition",
            "kelly staking explain",
        ],
        "accuracy": [
            "How accurate are predictions",
            "What is the model accuracy",
            "Prediction accuracy",
            "How good is the model",
            "Model performance",
            "Is the model accurate",
            "Accuracy of predictions",
            "How reliable are predictions",
            "What accuracy does the model have",
            "Measure model accuracy",
            "prediction performance",
            "How precise is the model",
            "What accuracy should I expect",
            "Trust in model predictions",
            "How good are forecasts",
        ],
    }
    for intent_id, qs in templates_en.items():
        for i, q in enumerate(qs):
            src = "original" if i == 0 else "paraphrase"
            rows.append(_make_row(intent_id, "en", q, source=src, variant=i))
            # German near-mirror (same structure, different tokens for char n-grams)
            de = q.replace("value bet", "Value-Wette").replace("Kelly", "Kelly")
            rows.append(_make_row(intent_id, "de", de, source=src, variant=i))

    path = tmp_path / "dataset_augmented.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


# ───────────────────────── Tests ─────────────────────────


def test_normalize_idempotent() -> None:
    s = "  What IS   a Value Bet?  "
    assert normalize(s) == normalize(normalize(s))
    assert normalize(s) == "what is a value bet?"
    assert normalize("") == ""


def test_load_dataset_filters_by_lang(tiny_dataset: Path) -> None:
    all_rows = load_dataset(tiny_dataset)
    en_rows = load_dataset(tiny_dataset, lang="en")
    de_rows = load_dataset(tiny_dataset, lang="de")
    assert len(all_rows) == len(en_rows) + len(de_rows)
    assert {r["lang"] for r in en_rows} == {"en"}
    assert {r["lang"] for r in de_rows} == {"de"}


def test_load_dataset_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "does_not_exist.jsonl")


def test_stratified_split_pins_originals_to_train(tiny_dataset: Path) -> None:
    rows = load_dataset(tiny_dataset, lang="en")
    split = stratified_split(rows)
    assert split.lang == "en"
    assert split.n_classes == 3
    assert split.n_train > 0
    # All intents must appear in train
    assert set(split.y_train) == set(split.labels)
    # Originals pinned: no `source == "original"` row in val meta
    assert all(m["source"] != "original" for m in split.meta_val)


def test_stratified_split_rejects_mixed_lang(tiny_dataset: Path) -> None:
    rows = load_dataset(tiny_dataset)  # both langs
    with pytest.raises(ValueError):
        stratified_split(rows)


def test_intent_classifier_fit_predict_topk(tiny_dataset: Path) -> None:
    rows = load_dataset(tiny_dataset, lang="en")
    split = stratified_split(rows)

    clf = IntentClassifier(lang="en")
    info = clf.fit(split.X_train, split.y_train)
    assert info["n_classes"] == 3

    top3 = clf.predict_topk("What is a value bet", k=3)
    assert len(top3) == 3
    assert all(isinstance(p, IntentPrediction) for p in top3)
    # Scores must sum ≤ 1.0 and be sorted descending
    scores = [p.score for p in top3]
    assert scores == sorted(scores, reverse=True)
    assert sum(scores) <= 1.0 + 1e-6
    assert top3[0].intent_id == "value-bet"


def test_intent_classifier_save_load_roundtrip(tiny_dataset: Path, tmp_path: Path) -> None:
    rows = load_dataset(tiny_dataset, lang="en")
    split = stratified_split(rows)
    clf = IntentClassifier(lang="en")
    clf.fit(split.X_train, split.y_train)

    path = tmp_path / "support_intent_en.joblib"
    clf.save(path)
    assert path.exists()

    loaded = IntentClassifier.load(path)
    assert loaded.lang == "en"
    assert loaded.classes_ == clf.classes_

    # Predictions match the originally trained model
    q = "Explain Kelly staking"
    assert clf.predict(q).intent_id == loaded.predict(q).intent_id


def test_intent_classifier_untrained_raises() -> None:
    clf = IntentClassifier(lang="en")
    with pytest.raises(RuntimeError):
        clf.predict("hello")


def test_train_one_language_end_to_end(tiny_dataset: Path, tmp_path: Path) -> None:
    stats = train_one_language("en", dataset_path=tiny_dataset, out_dir=tmp_path)
    assert stats["lang"] == "en"
    assert stats["n_classes"] == 3
    model_path = Path(str(stats["model_path"]))
    assert model_path.exists()

    metrics = stats["metrics"]
    # Top-1 on this near-trivial synthetic set should be high
    if metrics["top1_accuracy"] is not None:
        assert metrics["top1_accuracy"] >= 0.5
        assert metrics["top3_accuracy"] >= metrics["top1_accuracy"]
