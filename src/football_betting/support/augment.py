"""Data augmentation for the support intent classifier (M2).

The pipeline brings the training corpus from ~24 utterances/intent up to
``SUPPORT_CFG.augment_target_per_intent`` (default 80) per (intent, language)
pair by chaining three layers, each optional, each idempotent for a fixed
random seed:

1. :class:`ParaphraseAugmenter` — LLM-driven paraphrase generation (opt-in,
   requires an OpenAI-compatible client + ``OPENAI_API_KEY`` env var).
2. :class:`BacktranslationAugmenter` — Marian MT round-trip through pivot
   languages (opt-in, requires ``transformers`` + ``sentencepiece``).
3. :class:`NoiseAugmenter` — pure-Python QWERTY/QWERTZ typo + punctuation +
   casing noise. **Always available** (no external deps) — the report's
   Cross-Noise Robustness Transfer Training is implemented here.

The orchestrator :func:`augment_dataset` loads an input JSONL (same schema
as ``dataset_augmented.jsonl``), computes the per-intent deficit, and fills
it layer-by-layer until the target is reached. Output is a JSONL file with
preserved schema plus ``source`` tags of the form ``augment_v2:<layer>``.
"""

from __future__ import annotations

import json
import random
import re
import string
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from football_betting.config import SUPPORT_CFG, SUPPORT_DATA_DIR, SupportConfig

# ════════════════════════════ Language metadata ════════════════════════════

_LANG_NAMES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "nl": "Dutch",
}


# ════════════════════════════ Keyboard noise maps ════════════════════════════
#
# Neighbour tables per locale. German uses the QWERTZ layout (z↔y swap, umlaut
# keys adjacent to "p"/"l"/"ö"). English/French/Spanish/Italian all use QWERTY
# with minor national variants. These are adjacency tables, not a full layout
# model — good enough for simulating realistic fat-finger typos.

_QWERTZ_NEIGHBOURS: dict[str, str] = {
    "q": "wa",
    "w": "qeasd",
    "e": "wrsdf",
    "r": "etdfg",
    "t": "rzfgh",
    "z": "tughj",
    "u": "zihjk",
    "i": "uojkl",
    "o": "iplkö",
    "p": "oüöl",
    "a": "qwsyx",
    "s": "awedxyc",
    "d": "serfxcv",
    "f": "drtgcvb",
    "g": "ftzhvbn",
    "h": "gzujbnm",
    "j": "huiknm",
    "k": "jiol,m",
    "l": "köp.",
    "y": "asx",  # German QWERTZ (y is where English has z)
    "x": "yasdc",
    "c": "xdfv",
    "v": "cfgb",
    "b": "vghn",
    "n": "bhjm",
    "m": "njk,",
    "ä": "öl",
    "ö": "pä",
    "ü": "ioö",
    "ß": "p",
}

_QWERTY_NEIGHBOURS: dict[str, str] = {
    "q": "wa",
    "w": "qeasd",
    "e": "wrsdf",
    "r": "etdfg",
    "t": "ryfgh",
    "y": "tughj",
    "u": "yihjk",
    "i": "uojkl",
    "o": "ipkl",
    "p": "ol",
    "a": "qwszx",
    "s": "awedxz",
    "d": "serfxcv",
    "f": "drtgcvb",
    "g": "ftyhvbn",
    "h": "gyujbnm",
    "j": "huiknm",
    "k": "jiolm,",
    "l": "kop.",
    "z": "asx",
    "x": "zasdc",
    "c": "xdfv",
    "v": "cfgb",
    "b": "vghn",
    "n": "bhjm",
    "m": "njk,",
}

_NEIGHBOURS_BY_LANG: dict[str, dict[str, str]] = {
    "de": _QWERTZ_NEIGHBOURS,
    "en": _QWERTY_NEIGHBOURS,
    "fr": _QWERTY_NEIGHBOURS,  # AZERTY exists but most support chat typos still stay near QWERTY
    "es": _QWERTY_NEIGHBOURS,
    "it": _QWERTY_NEIGHBOURS,
}


def _neighbours_for(lang: str) -> dict[str, str]:
    return _NEIGHBOURS_BY_LANG.get(lang, _QWERTY_NEIGHBOURS)


# ════════════════════════════ Protocols ════════════════════════════


class Augmenter(Protocol):
    """Generic augmenter contract — deterministic given ``rng``."""

    name: str

    def generate(
        self,
        question: str,
        lang: str,
        n: int,
        rng: random.Random,
    ) -> list[str]:
        """Return up to ``n`` distinct variants of ``question`` in ``lang``."""
        ...


# ════════════════════════════ Built-in noise augmenter ════════════════════════════


_WORD_RE = re.compile(r"\w+|\W+", flags=re.UNICODE)
_PUNCT_TRANSLATION = str.maketrans("", "", string.punctuation + "¿¡…—")


@dataclass(slots=True)
class NoiseAugmenter:
    """Deterministic rule-based noise (no external deps).

    Applies, in sequence, per produced variant:

    * Word-level typo injection on a ``aug_word_p`` fraction of words; within
      each selected word ``aug_char_p`` fraction of characters is perturbed
      (neighbour substitution, deletion, duplication, transposition).
    * With probability :attr:`punct_drop_p`, strips all punctuation (emulates
      chat slang).
    * With probability :attr:`lowercase_p`, lowercases the whole sentence.

    The randomness is fully driven by the injected ``rng``, so two calls with
    the same source string and the same RNG state yield the same variant set.
    """

    name: str = "noise"
    aug_char_p: float = SUPPORT_CFG.noise_aug_char_p
    aug_word_p: float = SUPPORT_CFG.noise_aug_word_p
    punct_drop_p: float = SUPPORT_CFG.noise_punct_drop_p
    lowercase_p: float = SUPPORT_CFG.noise_lowercase_p
    max_attempts_multiplier: int = 3  # safeguard against pathological loops

    def _typo_word(self, word: str, neighbours: dict[str, str], rng: random.Random) -> str:
        if not word or not word.isalpha():
            return word
        chars = list(word)
        n_perturb = max(1, int(round(len(chars) * self.aug_char_p))) if rng.random() < 0.9 else 1
        # Upper bound — never shred a word completely.
        n_perturb = min(n_perturb, max(1, len(chars) // 2))
        indices = rng.sample(range(len(chars)), k=min(n_perturb, len(chars)))
        for i in indices:
            op = rng.choice(("sub", "sub", "del", "dup", "swap"))
            ch = chars[i]
            lower = ch.lower()
            if op == "sub":
                neigh = neighbours.get(lower)
                if not neigh:
                    continue
                repl = rng.choice(neigh)
                chars[i] = repl.upper() if ch.isupper() else repl
            elif op == "del" and len(chars) > 2:
                chars[i] = ""
            elif op == "dup":
                chars[i] = ch + ch
            elif op == "swap" and i + 1 < len(chars):
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
        return "".join(chars)

    def _noise_once(self, text: str, lang: str, rng: random.Random) -> str:
        neighbours = _neighbours_for(lang)
        tokens = _WORD_RE.findall(text)
        out: list[str] = []
        for tok in tokens:
            if tok.isalpha() and rng.random() < self.aug_word_p:
                out.append(self._typo_word(tok, neighbours, rng))
            else:
                out.append(tok)
        result = "".join(out)
        if rng.random() < self.punct_drop_p:
            result = result.translate(_PUNCT_TRANSLATION)
            result = re.sub(r"\s+", " ", result).strip()
        if rng.random() < self.lowercase_p:
            result = result.lower()
        return result

    def generate(
        self,
        question: str,
        lang: str,
        n: int,
        rng: random.Random,
    ) -> list[str]:
        if n <= 0 or not question.strip():
            return []
        seen: set[str] = {question.strip()}
        out: list[str] = []
        attempts = 0
        budget = max(n * self.max_attempts_multiplier, 4)
        while len(out) < n and attempts < budget:
            attempts += 1
            variant = self._noise_once(question, lang, rng).strip()
            if variant and variant not in seen:
                seen.add(variant)
                out.append(variant)
        return out


# ════════════════════════════ Optional paraphrase augmenter (LLM) ════════════════════════════


@dataclass(slots=True)
class ParaphraseAugmenter:
    """Optional LLM-based paraphrase generator.

    Uses the user-supplied ``generate_fn`` callback so the heavy dependency
    (``openai`` or any other SDK) is injected by the caller and not imported
    at module load time. ``generate_fn(prompt, n, lang) -> list[str]``.
    """

    name: str = "paraphrase"
    generate_fn: Callable[[str, int, str], list[str]] | None = None

    def generate(
        self,
        question: str,
        lang: str,
        n: int,
        rng: random.Random,  # noqa: ARG002 — LLMs manage their own sampling
    ) -> list[str]:
        if self.generate_fn is None or n <= 0:
            return []
        try:
            variants = self.generate_fn(question, n, lang)
        except Exception:  # noqa: BLE001 — LLM backends should never kill the pipeline
            return []
        # Dedup + strip + keep only non-empty, distinct-from-source entries.
        src = question.strip().lower()
        seen: set[str] = {src}
        out: list[str] = []
        for v in variants:
            s = (v or "").strip()
            if s and s.lower() not in seen:
                out.append(s)
                seen.add(s.lower())
            if len(out) >= n:
                break
        return out


# ════════════════════════════ Optional backtranslation augmenter ════════════════════════════


@dataclass(slots=True)
class BacktranslationAugmenter:
    """Optional MarianMT round-trip paraphraser.

    The actual translation function is injected via ``translate_fn`` so the
    module stays import-safe without ``transformers``. Signature:

        translate_fn(texts: list[str], src: str, tgt: str) -> list[str]

    The augmenter picks pivots from ``SUPPORT_CFG.backtranslation_pivots``.
    """

    name: str = "backtranslate"
    translate_fn: Callable[[list[str], str, str], list[str]] | None = None

    def generate(
        self,
        question: str,
        lang: str,
        n: int,
        rng: random.Random,
    ) -> list[str]:
        if self.translate_fn is None or n <= 0:
            return []
        pivots_by_lang = dict(SUPPORT_CFG.backtranslation_pivots)
        pivots = pivots_by_lang.get(lang, ())
        if not pivots:
            return []
        src = question.strip()
        seen: set[str] = {src.lower()}
        out: list[str] = []
        # Try pivots in a fixed shuffled order for reproducibility.
        shuffled_pivots = list(pivots)
        rng.shuffle(shuffled_pivots)
        for pivot in shuffled_pivots:
            if len(out) >= n:
                break
            try:
                forward = self.translate_fn([src], lang, pivot)
                if not forward:
                    continue
                backward = self.translate_fn(forward, pivot, lang)
                if not backward:
                    continue
                cand = backward[0].strip()
            except Exception:  # noqa: BLE001
                continue
            if cand and cand.lower() not in seen:
                out.append(cand)
                seen.add(cand.lower())
        return out


# ════════════════════════════ Orchestrator ════════════════════════════


@dataclass(slots=True)
class AugmentStats:
    """Summary statistics returned by :func:`augment_dataset`."""

    n_input_rows: int = 0
    n_output_rows: int = 0
    per_language: dict[str, int] = field(default_factory=dict)
    per_source: dict[str, int] = field(default_factory=dict)
    variants_per_intent_lang: dict[str, float] = field(default_factory=dict)
    per_intent_deficit_before: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_input_rows": self.n_input_rows,
            "n_output_rows": self.n_output_rows,
            "per_language": dict(self.per_language),
            "per_source": dict(self.per_source),
            "variants_per_intent_lang": dict(self.variants_per_intent_lang),
            "per_intent_deficit_before_sample": dict(
                list(self.per_intent_deficit_before.items())[:20]
            ),
        }


def _group_by_intent_lang(
    rows: list[dict[str, object]],
) -> dict[tuple[str, str], list[dict[str, object]]]:
    buckets: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for r in rows:
        key = (str(r.get("id", "")), str(r.get("lang", "")))
        buckets[key].append(r)
    return buckets


def _build_variant_row(
    template: dict[str, object], new_question: str, layer: str
) -> dict[str, object]:
    copy = dict(template)
    copy["question"] = new_question
    copy["source"] = f"augment_v2:{layer}"
    copy.pop("variant", None)
    return copy


def augment_dataset(
    input_path: Path | None = None,
    output_path: Path | None = None,
    *,
    target_per_intent: int | None = None,
    augmenters: list[Augmenter] | None = None,
    cfg: SupportConfig = SUPPORT_CFG,
    rng_seed: int | None = None,
) -> AugmentStats:
    """Fill every ``(intent, lang)`` bucket to ``target_per_intent`` utterances.

    Augmenters are run in the order supplied; when omitted the pipeline falls
    back to a single :class:`NoiseAugmenter` (always available). The returned
    :class:`AugmentStats` is also persisted next to the output JSONL.
    """
    inp = input_path or (SUPPORT_DATA_DIR / cfg.dataset_filename)
    out = output_path or (SUPPORT_DATA_DIR / cfg.augmented_v2_filename)
    target = target_per_intent or cfg.augment_target_per_intent
    seed = rng_seed if rng_seed is not None else cfg.augment_random_seed

    if not inp.exists():
        raise FileNotFoundError(f"Input dataset not found: {inp}")

    # ─── Load ───
    rows: list[dict[str, object]] = []
    with inp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    pipeline: list[Augmenter] = list(augmenters) if augmenters else [NoiseAugmenter()]

    buckets = _group_by_intent_lang(rows)
    stats = AugmentStats(n_input_rows=len(rows))
    rng = random.Random(seed)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        # ─── 1. Pass-through originals ───
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            stats.per_language[str(r.get("lang", ""))] = (
                stats.per_language.get(str(r.get("lang", "")), 0) + 1
            )
            stats.per_source[str(r.get("source", ""))] = (
                stats.per_source.get(str(r.get("source", "")), 0) + 1
            )
        stats.n_output_rows = len(rows)

        # ─── 2. Fill per-bucket deficit ───
        for (intent_id, lang), items in buckets.items():
            have = len(items)
            stats.per_intent_deficit_before[f"{intent_id}|{lang}"] = max(0, target - have)
            if have >= target:
                continue
            deficit = target - have
            # Seed rotation: cycle over existing utterances so each one gets a fair share of budget.
            if not items:
                continue
            # Per-bucket RNG derived from global rng for determinism.
            bucket_rng = random.Random(rng.random())
            source_questions = [str(it["question"]) for it in items if it.get("question")]
            if not source_questions:
                continue

            produced_texts: set[str] = {q.strip().lower() for q in source_questions}
            produced_rows: list[dict[str, object]] = []
            per_source_cap = max(1, cfg.noise_max_variants_per_source)

            for augm in pipeline:
                if len(produced_rows) >= deficit:
                    break
                # Round-robin over source questions, drawing up to `per_source_cap` per source.
                idx = 0
                while len(produced_rows) < deficit and source_questions:
                    src_q = source_questions[idx % len(source_questions)]
                    template = items[idx % len(items)]
                    idx += 1
                    need = min(per_source_cap, deficit - len(produced_rows))
                    variants = augm.generate(src_q, lang, need, bucket_rng)
                    for v in variants:
                        key = v.strip().lower()
                        if key and key not in produced_texts:
                            produced_texts.add(key)
                            produced_rows.append(_build_variant_row(template, v, augm.name))
                            if len(produced_rows) >= deficit:
                                break
                    if idx >= len(source_questions) * per_source_cap:
                        break  # one full sweep per augmenter

            for row in produced_rows:
                # Defensive validation: never write a row we cannot round-trip.
                # Protects downstream against weird LLM output (embedded control
                # chars, U+2028/U+2029 line separators, JSON-like strings etc.).
                try:
                    payload = json.dumps(row, ensure_ascii=False)
                    json.loads(payload)  # round-trip check
                except (TypeError, ValueError):
                    continue
                f.write(payload + "\n")
                stats.n_output_rows += 1
                stats.per_language[lang] = stats.per_language.get(lang, 0) + 1
                stats.per_source[str(row["source"])] = (
                    stats.per_source.get(str(row["source"]), 0) + 1
                )

    # ─── Per-intent stats ───
    # Recompute post-aug counts.
    final_counts: dict[tuple[str, str], int] = defaultdict(int)
    final_counts.update({k: len(v) for k, v in buckets.items()})
    # Tally augments we just wrote.
    for aug_source, count in stats.per_source.items():
        if aug_source.startswith("augment_v2:"):
            # Not bucketized; skip — overall counts covered by per_language.
            _ = count
    # Re-read output for precise per-intent counts (cheap: output is already on disk).
    # newline="" disables universal-newlines so \r inside strings cannot split lines;
    # malformed lines are tolerated and counted, not fatal.
    per_il: dict[str, int] = defaultdict(int)
    n_bad_lines = 0
    with out.open("r", encoding="utf-8", newline="") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                n_bad_lines += 1
                continue
            per_il[f"{r.get('id')}|{r.get('lang')}"] += 1
    if n_bad_lines:
        print(f"[augment] warning: skipped {n_bad_lines} malformed lines in {out}")
    if per_il:
        counts = list(per_il.values())
        stats.variants_per_intent_lang = {
            "min": float(min(counts)),
            "max": float(max(counts)),
            "avg": float(sum(counts) / len(counts)),
        }

    # ─── Persist stats ───
    stats_path = out.parent / cfg.augment_stats_v2_filename
    stats_path.write_text(
        json.dumps(stats.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return stats


# ════════════════════════════ Concrete backend adapters (M2b) ════════════════════════════
#
# These builders are deliberately thin: each returns a ready-to-use callback
# matching the ``generate_fn`` / ``translate_fn`` protocols defined above.
# Heavy dependencies (``openai``, ``transformers``) are imported *inside* the
# builders so ``import football_betting.support.augment`` stays cheap and the
# core unit tests keep running with the base install.


def build_openai_paraphraser(
    *,
    model: str = "gpt-4o-mini",
    client: Any | None = None,
    temperature: float = 0.8,
    max_tokens: int = 400,
    system_prompt: str | None = None,
) -> Callable[[str, int, str], list[str]]:
    """Return a ``generate_fn`` callback for :class:`ParaphraseAugmenter`.

    The callback talks to an OpenAI-compatible chat completions endpoint and
    asks for a numbered list of ``n`` paraphrases in the target language.

    ``client`` may be any object exposing ``chat.completions.create(...)``.
    When ``None`` we import ``openai`` lazily and instantiate the default
    client (requires ``OPENAI_API_KEY`` in the env).
    """
    default_sys = (
        "You generate paraphrases for a support-chatbot training set. "
        "Given one source sentence, return exactly N distinct paraphrases in the "
        "requested language. Mix imperatives, questions, short keyword phrases "
        "and longer multi-sentence forms. Preserve the original intent. "
        "Return ONE paraphrase per line, no numbering, no bullets, no commentary."
    )
    sys_prompt = system_prompt or default_sys

    def _resolve_client() -> Any:
        if client is not None:
            return client
        try:
            from openai import OpenAI  # type: ignore[import-not-found]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "openai package not installed — `pip install .[support-aug]`"
            ) from exc
        return OpenAI()

    resolved = _resolve_client()

    def generate_fn(prompt: str, n: int, lang: str) -> list[str]:
        if n <= 0 or not prompt.strip():
            return []
        lang_name = _LANG_NAMES.get(lang, lang)
        user_msg = (
            f"Source ({lang_name}): {prompt}\n"
            f"Produce {n} distinct paraphrases in {lang_name}, one per line."
        )
        resp = resolved.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ],
        )
        # Support both the official SDK response and dict-shaped fakes.
        try:
            content = resp.choices[0].message.content or ""
        except AttributeError:
            content = resp["choices"][0]["message"]["content"]  # type: ignore[index]
        lines = [ln.strip(" -\t•*0123456789.)") for ln in content.splitlines()]
        return [ln for ln in lines if ln]

    return generate_fn


def build_marian_backtranslator(
    *,
    model_template: str = "Helsinki-NLP/opus-mt-{src}-{tgt}",
    device: str = "cpu",
    cache: dict[tuple[str, str], Any] | None = None,
) -> Callable[[list[str], str, str], list[str]]:
    """Return a ``translate_fn`` callback for :class:`BacktranslationAugmenter`.

    Loads Marian translation pipelines lazily on first use per ``(src, tgt)``
    pair and keeps them in the provided ``cache`` (or a module-local dict).
    Raises ``RuntimeError`` if ``transformers`` is missing.
    """
    try:
        from transformers import pipeline  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "transformers package not installed — `pip install .[support-aug]`"
        ) from exc

    store: dict[tuple[str, str], Any] = cache if cache is not None else {}

    def _get_pipe(src: str, tgt: str) -> Any:
        key = (src, tgt)
        if key in store:
            return store[key]
        model_id = model_template.format(src=src, tgt=tgt)
        pipe = pipeline("translation", model=model_id, device=device)
        store[key] = pipe
        return pipe

    def translate_fn(texts: list[str], src: str, tgt: str) -> list[str]:
        if not texts or src == tgt:
            return list(texts)
        pipe = _get_pipe(src, tgt)
        out = pipe(texts)
        # ``pipeline('translation')`` returns a list of {"translation_text": ...}
        result: list[str] = []
        for item in out:
            if isinstance(item, dict):
                result.append(str(item.get("translation_text", "")))
            else:
                result.append(str(item))
        return result

    return translate_fn


__all__ = [
    "AugmentStats",
    "Augmenter",
    "BacktranslationAugmenter",
    "NoiseAugmenter",
    "ParaphraseAugmenter",
    "augment_dataset",
    "build_marian_backtranslator",
    "build_openai_paraphraser",
]
