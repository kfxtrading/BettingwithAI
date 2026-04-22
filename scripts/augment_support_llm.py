"""LLM-driven paraphrase augmentation for the support intent classifier.

Pluggable LLM backend that feeds :class:`ParaphraseAugmenter` in
``football_betting.support.augment``. Targets 100-200 utterances per
(intent, language) by combining:

    1. original canonical + hand-crafted alt_questions  (~6 rows)
    2. LLM paraphrases via this script                  (~80-120 rows)
    3. MarianMT back-translation (optional)             (~10-20 rows)
    4. Rule-based noise (QWERTZ typos, casing, punct)    (fills remainder)

Output: ``data/support_faq/dataset_augmented_v3.jsonl`` (configurable).

=========================================================================
Backends
=========================================================================

--backend ollama       (default; needs local Ollama daemon on :11434)
    Tested models: llama3.1:8b-instruct, qwen2.5:7b-instruct, gemma2:9b
    Install: https://ollama.com/download
    Then:    ollama pull qwen2.5:7b-instruct

--backend openai       (needs OPENAI_API_KEY)
    Model:  gpt-4o-mini (~$0.15 / 1M input tokens → ~$2 for full run)

--backend anthropic    (needs ANTHROPIC_API_KEY)
    Model:  claude-haiku-4.5 or claude-3-5-haiku-latest

--backend dry          (no network; prints prompts only → for QA)

=========================================================================
Usage
=========================================================================

Quick smoke test (only 3 intents, DE only, 10 paraphrases each)::

    python scripts/augment_support_llm.py \\
        --backend ollama --model qwen2.5:7b-instruct \\
        --lang de --limit-intents 3 --n-per-intent 10 \\
        --output data/support_faq/smoke_v3.jsonl

Full production run (all 5 langs × 268 intents, 100 paraphrases/intent)::

    python scripts/augment_support_llm.py \\
        --backend ollama --model qwen2.5:7b-instruct \\
        --target 150 --n-per-intent 100 \\
        --output data/support_faq/dataset_augmented_v3.jsonl

Then retrain::

    $env:PYTHONIOENCODING="utf-8"
    .\\.venv\\Scripts\\python.exe scripts\\train_phase5_rollout.py \\
        --dataset data/support_faq/dataset_augmented_v3.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_betting.config import SUPPORT_CFG, SUPPORT_DATA_DIR  # noqa: E402
from football_betting.support.augment import (  # noqa: E402
    NoiseAugmenter,
    ParaphraseAugmenter,
    augment_dataset,
)

_LANG_NAMES = {
    "en": "English",
    "de": "German (Deutsch)",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "it": "Italian (Italiano)",
}


# ═══════════════════════════════════════════════════════════════════════
# Prompt template
# ═══════════════════════════════════════════════════════════════════════


def _build_prompt(question: str, n: int, lang: str) -> str:
    """Prompt instructing the LLM to produce N stylistically varied paraphrases."""
    lang_full = _LANG_NAMES.get(lang, lang)
    return f"""You are generating training data for a support-intent classifier.

Original user question ({lang_full}):
"{question}"

Produce {n} paraphrases of this question that a real user might type into
a chat box, preserving the exact same intent. Follow these rules:

- Language: {lang_full} only. Do NOT mix languages.
- Keep the core meaning identical. Do not change what is being asked.
- Vary the style across the batch:
  * {max(1, n // 5)} formal / polite phrasing
  * {max(1, n // 5)} casual chat-style (lowercase, short)
  * {max(1, n // 5)} very short (3-6 words)
  * {max(1, n // 5)} with minor typos or colloquialisms
  * {max(1, n // 5)} question-rephrased as a statement of need
- No duplicates.
- No explanations, no numbering, no markdown.

Output format: one paraphrase per line, {n} lines total."""


# ═══════════════════════════════════════════════════════════════════════
# Backends — each exposes generate_fn(question, n, lang) -> list[str]
# ═══════════════════════════════════════════════════════════════════════


def _parse_lines(raw: str, n: int) -> list[str]:
    """Extract up to n cleaned paraphrases from raw LLM output."""
    out: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        # Strip common LLM artefacts: leading numbering, bullets, quotes.
        s = re.sub(r"^\s*(?:\d+[.)]|[-*•])\s*", "", s)
        s = s.strip("\"'` ")
        # Drop obvious meta-comments.
        if s.lower().startswith(("here are", "paraphrase", "variant", "note:")):
            continue
        if len(s) < 3 or len(s) > 400:
            continue
        out.append(s)
        if len(out) >= n:
            break
    return out


def make_ollama_backend(
    model: str,
    host: str = "http://localhost:11434",
    timeout: float = 120.0,
) -> Callable[[str, int, str], list[str]]:
    def gen(question: str, n: int, lang: str) -> list[str]:
        body = json.dumps(
            {
                "model": model,
                "prompt": _build_prompt(question, n, lang),
                "stream": False,
                "options": {"temperature": 0.8, "top_p": 0.95},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{host}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                payload = json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [ollama] ERROR: {e}", file=sys.stderr)
            return []
        raw = payload.get("response", "") or ""
        return _parse_lines(raw, n)

    return gen


def make_openai_backend(
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
) -> Callable[[str, int, str], list[str]]:
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    def gen(question: str, n: int, lang: str) -> list[str]:
        body = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": _build_prompt(question, n, lang)}],
                "temperature": 0.8,
                "top_p": 0.95,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                payload = json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [openai] ERROR: {e}", file=sys.stderr)
            return []
        raw = payload["choices"][0]["message"]["content"]
        return _parse_lines(raw, n)

    return gen


def make_anthropic_backend(
    model: str = "claude-3-5-haiku-latest",
    api_key: str | None = None,
) -> Callable[[str, int, str], list[str]]:
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    def gen(question: str, n: int, lang: str) -> list[str]:
        body = json.dumps(
            {
                "model": model,
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": _build_prompt(question, n, lang)}],
                "temperature": 0.8,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                payload = json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [anthropic] ERROR: {e}", file=sys.stderr)
            return []
        raw = payload["content"][0]["text"]
        return _parse_lines(raw, n)

    return gen


def make_dry_backend() -> Callable[[str, int, str], list[str]]:
    """Prints the prompt that would be sent, returns []."""
    counter = {"n": 0}

    def gen(question: str, n: int, lang: str) -> list[str]:
        counter["n"] += 1
        if counter["n"] <= 3:
            print(f"\n[DRY #{counter['n']}] lang={lang} n={n} question={question!r}")
            print(_build_prompt(question, n, lang))
        return []

    return gen


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════


def _filter_input(
    input_path: Path,
    tmp_path: Path,
    langs: list[str],
    limit_intents: int | None,
) -> int:
    """Filter the input JSONL to requested langs + optional intent cap. Returns rows written."""
    rows: list[dict] = []
    seen_intents: list[str] = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("lang") not in langs:
                continue
            intent = r.get("id")
            if intent not in seen_intents:
                seen_intents.append(intent)
            if limit_intents is not None and intent not in seen_intents[:limit_intents]:
                continue
            rows.append(r)
    with tmp_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--backend", choices=["ollama", "openai", "anthropic", "dry"], default="ollama")
    ap.add_argument(
        "--model", default=None, help="Model name (backend-specific default if omitted)"
    )
    ap.add_argument("--ollama-host", default="http://localhost:11434")
    ap.add_argument(
        "--input",
        type=Path,
        default=SUPPORT_DATA_DIR / "dataset.jsonl",
        help="Source JSONL (default: dataset.jsonl — originals only).",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=SUPPORT_DATA_DIR / "dataset_augmented_v3.jsonl",
    )
    ap.add_argument("--target", type=int, default=150, help="Rows per (intent, lang) to reach.")
    ap.add_argument(
        "--n-per-intent",
        type=int,
        default=100,
        help="How many paraphrases to request from the LLM per source question (pre-dedup).",
    )
    ap.add_argument("--lang", default="all", help="Comma list or 'all'.")
    ap.add_argument("--limit-intents", type=int, default=None, help="Smoke-test: cap N intents.")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--no-noise", action="store_true", help="Skip NoiseAugmenter fallback.")
    args = ap.parse_args()

    # ─── Resolve backend ───
    if args.backend == "ollama":
        model = args.model or "qwen2.5:7b-instruct"
        gen_fn = make_ollama_backend(model, host=args.ollama_host)
        print(f"[backend] ollama (model={model}, host={args.ollama_host})")
    elif args.backend == "openai":
        model = args.model or "gpt-4o-mini"
        gen_fn = make_openai_backend(model)
        print(f"[backend] openai (model={model})")
    elif args.backend == "anthropic":
        model = args.model or "claude-3-5-haiku-latest"
        gen_fn = make_anthropic_backend(model)
        print(f"[backend] anthropic (model={model})")
    else:
        gen_fn = make_dry_backend()
        print("[backend] dry (no network calls — prompts will be printed)")

    # ─── Filter input if needed ───
    langs = list(SUPPORT_CFG.languages) if args.lang == "all" else args.lang.split(",")
    effective_input = args.input
    tmp_input: Path | None = None
    if args.limit_intents is not None or set(langs) != set(SUPPORT_CFG.languages):
        tmp_input = args.output.with_suffix(".input-filtered.jsonl")
        n_rows = _filter_input(args.input, tmp_input, langs, args.limit_intents)
        print(
            f"[filter] wrote {n_rows} rows to {tmp_input} (langs={langs}, limit={args.limit_intents})"
        )
        effective_input = tmp_input

    # ─── Compose augmenter pipeline (paraphrase first → noise fallback) ───
    augmenters = [ParaphraseAugmenter(generate_fn=gen_fn)]
    if not args.no_noise:
        augmenters.append(NoiseAugmenter())
    print(f"[pipeline] {[a.name for a in augmenters]}  target={args.target}/intent/lang")

    # Smoke health check — single prompt before the big run.
    print("\n[health-check] firing 1 probe …")
    probe = gen_fn("What is a value bet?", 3, "en")
    print(f"  got {len(probe)} paraphrases: {probe}")
    if args.backend != "dry" and not probe:
        print("\n[WARN] backend returned 0 paraphrases — aborting to save time.")
        print("       Check backend availability (ollama daemon running? API key set?).")
        return 2

    # ─── Run orchestrator ───
    t0 = time.time()
    stats = augment_dataset(
        input_path=effective_input,
        output_path=args.output,
        target_per_intent=args.target,
        augmenters=augmenters,
        rng_seed=args.seed,
    )
    dt = time.time() - t0

    # ─── Summary ───
    print("\n" + "=" * 72)
    print(f"[done] {stats.n_output_rows} rows → {args.output}  ({dt:.1f}s)")
    print(f"       per-lang: {dict(stats.per_language)}")
    print(f"       per-source: {dict(stats.per_source)}")
    print(f"       variants/intent/lang: {stats.variants_per_intent_lang}")

    # Cleanup
    if tmp_input is not None and tmp_input.exists():
        # Keep it for debuggability, but flag.
        print(f"[note] filter tmp kept at {tmp_input}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
