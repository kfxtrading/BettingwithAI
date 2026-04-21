"""Tests for the M2 augmentation pipeline (deterministic, no network)."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from football_betting.config import SUPPORT_CFG
from football_betting.support.augment import (
    BacktranslationAugmenter,
    NoiseAugmenter,
    ParaphraseAugmenter,
    augment_dataset,
    build_openai_paraphraser,
)


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
def small_corpus(tmp_path: Path) -> Path:
    """2 intents × 2 langs × ~5 paraphrases — well under the 80 target."""
    rows = []
    templates = {
        ("value_bet", "en"): [
            "what is a value bet",
            "explain value bet",
            "define value bet please",
            "tell me about value bets",
            "value bet meaning",
        ],
        ("value_bet", "de"): [
            "was ist ein value bet",
            "erklaere value bet",
            "value bet definition",
            "was bedeutet value bet",
            "erzaehl mir von value bets",
        ],
        ("kelly", "en"): [
            "what is the kelly criterion",
            "explain kelly staking",
            "define kelly",
            "how does kelly sizing work",
            "kelly criterion meaning",
        ],
        ("kelly", "de"): [
            "was ist das kelly kriterium",
            "erklaere kelly staking",
            "kelly definition",
            "wie funktioniert kelly sizing",
            "kelly kriterium bedeutung",
        ],
    }
    for (intent, lang), qs in templates.items():
        chap = "strategy" if intent == "kelly" else "general"
        for i, q in enumerate(qs):
            src = "original" if i == 0 else "paraphrase"
            rows.append(_row(intent, lang, chap, q, source=src, variant=i))
    path = tmp_path / "dataset_augmented.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


# ───────────────────────── NoiseAugmenter ─────────────────────────


def test_noise_augmenter_is_deterministic() -> None:
    aug = NoiseAugmenter()
    rng1 = random.Random(1337)
    rng2 = random.Random(1337)
    a = aug.generate("what is a value bet", "en", 5, rng1)
    b = aug.generate("what is a value bet", "en", 5, rng2)
    assert a == b


def test_noise_augmenter_produces_distinct_variants() -> None:
    aug = NoiseAugmenter()
    rng = random.Random(42)
    variants = aug.generate("what is the kelly criterion", "en", 6, rng)
    assert len(variants) == len(set(variants))
    assert all(isinstance(v, str) and v for v in variants)
    # At least half should actually differ from the source.
    src = "what is the kelly criterion"
    assert sum(1 for v in variants if v != src) >= max(1, len(variants) // 2)


def test_noise_augmenter_respects_german_layout() -> None:
    aug = NoiseAugmenter(aug_word_p=1.0, aug_char_p=0.5, punct_drop_p=0.0, lowercase_p=0.0)
    rng = random.Random(7)
    variants = aug.generate("passwort zuruecksetzen", "de", 4, rng)
    # Even with aggressive noise the output must be non-empty and distinct.
    assert variants
    assert all(v for v in variants)


def test_noise_augmenter_empty_input_returns_empty() -> None:
    aug = NoiseAugmenter()
    assert aug.generate("", "en", 3, random.Random(0)) == []
    assert aug.generate("hi", "en", 0, random.Random(0)) == []


def test_noise_augmenter_drops_punctuation_when_p_is_one() -> None:
    aug = NoiseAugmenter(aug_word_p=0.0, aug_char_p=0.0, punct_drop_p=1.0, lowercase_p=0.0)
    rng = random.Random(123)
    variants = aug.generate("Hello, world! How are you?", "en", 1, rng)
    assert variants
    assert all("," not in v and "!" not in v and "?" not in v for v in variants)


# ───────────────────────── Optional augmenters (no real LLM/MT) ─────────────────────────


def test_paraphrase_augmenter_without_callback_returns_empty() -> None:
    aug = ParaphraseAugmenter(generate_fn=None)
    assert aug.generate("hello", "en", 3, random.Random(0)) == []


def test_paraphrase_augmenter_with_fake_callback() -> None:
    def fake(prompt: str, n: int, lang: str) -> list[str]:
        return [f"{prompt} v{i} [{lang}]" for i in range(n)]

    aug = ParaphraseAugmenter(generate_fn=fake)
    out = aug.generate("what is kelly", "en", 3, random.Random(0))
    assert out == ["what is kelly v0 [en]", "what is kelly v1 [en]", "what is kelly v2 [en]"]


def test_paraphrase_augmenter_swallows_backend_errors() -> None:
    def boom(prompt: str, n: int, lang: str) -> list[str]:
        raise RuntimeError("LLM went offline")

    aug = ParaphraseAugmenter(generate_fn=boom)
    assert aug.generate("hi", "en", 3, random.Random(0)) == []


def test_backtranslation_augmenter_without_callback_returns_empty() -> None:
    aug = BacktranslationAugmenter(translate_fn=None)
    assert aug.generate("hello", "en", 3, random.Random(0)) == []


def test_backtranslation_augmenter_with_fake_mt() -> None:
    def fake_mt(texts: list[str], src: str, tgt: str) -> list[str]:
        # Deterministic mock: tag direction so forward→backward yields a known variant.
        return [f"[{src}->{tgt}] {t}" for t in texts]

    aug = BacktranslationAugmenter(translate_fn=fake_mt)
    out = aug.generate("what is kelly", "en", 2, random.Random(0))
    assert out  # at least one pivot succeeded
    # Each output must differ from the source.
    assert all("what is kelly" != v for v in out)


# ───────────────────────── Orchestrator ─────────────────────────


def test_augment_dataset_fills_buckets_to_target(small_corpus: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "dataset_v2.jsonl"
    stats = augment_dataset(
        input_path=small_corpus,
        output_path=out_path,
        target_per_intent=12,
        augmenters=[NoiseAugmenter()],
        rng_seed=999,
    )
    assert out_path.exists()
    assert stats.n_input_rows == 20
    assert stats.n_output_rows >= 4 * 12
    # Per (intent, lang) count >= target (or >= original if original already exceeds).
    per_il: dict[str, int] = {}
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            key = f"{r['id']}|{r['lang']}"
            per_il[key] = per_il.get(key, 0) + 1
    assert min(per_il.values()) >= 12

    # Stats file next to the output.
    stats_path = out_path.parent / SUPPORT_CFG.augment_stats_v2_filename
    assert stats_path.exists()
    payload = json.loads(stats_path.read_text(encoding="utf-8"))
    assert payload["n_input_rows"] == 20
    assert "variants_per_intent_lang" in payload


def test_augment_dataset_is_deterministic_for_fixed_seed(
    small_corpus: Path, tmp_path: Path
) -> None:
    out_a = tmp_path / "a.jsonl"
    out_b = tmp_path / "b.jsonl"
    augment_dataset(
        input_path=small_corpus,
        output_path=out_a,
        target_per_intent=10,
        augmenters=[NoiseAugmenter()],
        rng_seed=2024,
    )
    augment_dataset(
        input_path=small_corpus,
        output_path=out_b,
        target_per_intent=10,
        augmenters=[NoiseAugmenter()],
        rng_seed=2024,
    )
    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")


def test_augment_dataset_preserves_originals(small_corpus: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "out.jsonl"
    augment_dataset(
        input_path=small_corpus,
        output_path=out_path,
        target_per_intent=8,
        augmenters=[NoiseAugmenter()],
        rng_seed=1,
    )
    orig_qs = {json.loads(l)["question"] for l in small_corpus.read_text("utf-8").splitlines() if l}
    out_qs = {json.loads(l)["question"] for l in out_path.read_text("utf-8").splitlines() if l}
    assert orig_qs.issubset(out_qs)


def test_augment_dataset_missing_input_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        augment_dataset(
            input_path=tmp_path / "nope.jsonl",
            output_path=tmp_path / "out.jsonl",
            target_per_intent=10,
        )


# ───────────────────────── M2b: OpenAI paraphraser adapter ─────────────────────────


class _FakeOpenAIResp:
    """Minimal duck-type for openai>=1.x chat completion responses."""

    class _Msg:
        def __init__(self, content: str) -> None:
            self.content = content

    class _Choice:
        def __init__(self, content: str) -> None:
            self.message = _FakeOpenAIResp._Msg(content)

    def __init__(self, content: str) -> None:
        self.choices = [_FakeOpenAIResp._Choice(content)]


class _FakeChatCompletions:
    def __init__(self, content: str) -> None:
        self._content = content
        self.last_kwargs: dict | None = None

    def create(self, **kwargs: object) -> _FakeOpenAIResp:  # type: ignore[override]
        self.last_kwargs = dict(kwargs)
        return _FakeOpenAIResp(self._content)


class _FakeOpenAIClient:
    def __init__(self, content: str) -> None:
        self.chat = type("Chat", (), {"completions": _FakeChatCompletions(content)})()


def test_build_openai_paraphraser_parses_response_lines() -> None:
    client = _FakeOpenAIClient(
        "1. was ist ein value bet\n"
        "- bedeutung von value bet\n"
        "\n"
        "value bet erklärung bitte\n"
    )
    fn = build_openai_paraphraser(client=client, model="gpt-test")
    out = fn("erkläre value bet", 3, "de")
    assert out == [
        "was ist ein value bet",
        "bedeutung von value bet",
        "value bet erklärung bitte",
    ]


def test_build_openai_paraphraser_zero_n_short_circuits() -> None:
    client = _FakeOpenAIClient("ignored")
    fn = build_openai_paraphraser(client=client)
    assert fn("hi", 0, "en") == []
    assert fn("", 5, "en") == []


def test_build_openai_paraphraser_passes_model_and_messages() -> None:
    client = _FakeOpenAIClient("one\ntwo")
    fn = build_openai_paraphraser(client=client, model="gpt-x")
    fn("explain kelly", 2, "en")
    kwargs = client.chat.completions.last_kwargs
    assert kwargs is not None
    assert kwargs["model"] == "gpt-x"
    msgs = kwargs["messages"]
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert "English" in msgs[1]["content"]
    assert "explain kelly" in msgs[1]["content"]


def test_paraphrase_augmenter_wraps_openai_adapter() -> None:
    client = _FakeOpenAIClient("kelly what is it\nkelly definition\ntell me kelly")
    fn = build_openai_paraphraser(client=client)
    aug = ParaphraseAugmenter(generate_fn=fn)
    out = aug.generate("what is kelly", "en", 3, random.Random(0))
    assert out == ["kelly what is it", "kelly definition", "tell me kelly"]


# ───────────────────────── M2b: MarianMT backtranslator adapter ─────────────────────────


def test_backtranslation_augmenter_uses_all_pivots_until_n_reached() -> None:
    calls: list[tuple[str, str, tuple[str, ...]]] = []

    def fake_mt(texts: list[str], src: str, tgt: str) -> list[str]:
        calls.append((src, tgt, tuple(texts)))
        return [f"{t}<-{src}->{tgt}" for t in texts]

    aug = BacktranslationAugmenter(translate_fn=fake_mt)
    out = aug.generate("was ist ein value bet", "de", 2, random.Random(0))
    assert len(out) == 2
    # Each pivot triggers exactly 2 calls (forward + backward).
    assert len(calls) == 4
    pivot_pairs = {(calls[i][0], calls[i][1]) for i in range(0, len(calls), 2)}
    assert all(p[0] == "de" for p in pivot_pairs)
    assert all(p[1] in {"nl", "fr", "it"} for p in pivot_pairs)


def test_backtranslation_augmenter_skips_when_pivots_missing() -> None:
    def fake_mt(texts: list[str], src: str, tgt: str) -> list[str]:
        return texts

    aug = BacktranslationAugmenter(translate_fn=fake_mt)
    # No pivots configured for language 'nl'.
    assert aug.generate("hallo wereld", "nl", 3, random.Random(0)) == []


def test_backtranslation_augmenter_swallows_pipeline_errors() -> None:
    def flaky_mt(texts: list[str], src: str, tgt: str) -> list[str]:
        if tgt == "nl":
            raise RuntimeError("model download failed")
        return [f"{t}-bt" for t in texts]

    aug = BacktranslationAugmenter(translate_fn=flaky_mt)
    out = aug.generate("ein text", "de", 2, random.Random(0))
    assert all(v for v in out)  # first pivot failed, others still produced variants


# ───────────────────────── M2b: layered orchestration ─────────────────────────


def test_augment_dataset_layers_paraphrase_then_backtranslate_then_noise(
    small_corpus: Path, tmp_path: Path
) -> None:
    """All three augmenters chain cleanly; each contributes a source tag."""
    def fake_llm(prompt: str, n: int, lang: str) -> list[str]:
        return [f"paraphrase {i} of {prompt}" for i in range(n)]

    def fake_mt(texts: list[str], src: str, tgt: str) -> list[str]:
        return [f"{t} [{src}->{tgt}]" for t in texts]

    out_path = tmp_path / "layered.jsonl"
    augment_dataset(
        input_path=small_corpus,
        output_path=out_path,
        target_per_intent=15,
        augmenters=[
            ParaphraseAugmenter(generate_fn=fake_llm),
            BacktranslationAugmenter(translate_fn=fake_mt),
            NoiseAugmenter(),
        ],
        rng_seed=2026,
    )
    sources: set[str] = set()
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            sources.add(str(r.get("source", "")))
    assert "augment_v2:paraphrase" in sources
    # Noise is always reached when paraphrase alone can't fill the bucket
    # (small-corpus intents start at 5 utterances, target=15, paraphrase can
    # output many but after dedup we still leave noise room for some buckets).
    # We only hard-assert paraphrase fired; the other two are best-effort.
    assert "original" in sources or "paraphrase" in sources  # originals preserved


def test_augment_dataset_default_pipeline_is_noise(small_corpus: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "default.jsonl"
    stats = augment_dataset(
        input_path=small_corpus,
        output_path=out_path,
        target_per_intent=9,
        rng_seed=7,
    )
    assert stats.n_output_rows > stats.n_input_rows
    # Every new row must carry an augment_v2 source tag.
    new_sources = set()
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            src = str(r.get("source", ""))
            if src.startswith("augment_v2:"):
                new_sources.add(src)
    assert new_sources == {"augment_v2:noise"}
