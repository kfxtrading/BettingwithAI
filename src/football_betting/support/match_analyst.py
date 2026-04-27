"""Nomen match-article generator — Günter Netzer style football analyst.

Two serving backends (auto-selected via env vars):

1. **vLLM** (production / fine-tuned model):
   Set ``NOMEN_VLLM_URL`` to the base URL of a RunPod vLLM inference pod
   (e.g. ``https://<pod-id>-8080.proxy.runpod.net/v1``).
   Uses the OpenAI-compatible ``/v1/chat/completions`` endpoint.
   Optional: ``NOMEN_VLLM_API_KEY`` (default: "nomen")

2. **Ollama** (local / development fallback):
   ``OLLAMA_HOST``  — Ollama server URL   (default: http://localhost:11434)
   ``OLLAMA_MODEL`` — model tag to use    (default: nomen-v1, falls back to qwen2.5:7b-instruct)

Returns a 4–6 sentence match preview in the Netzer analytical style, or ``None``
on any network failure so the chatbot never breaks in production.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger("football_betting.support.nomen")

_DEFAULT_OLLAMA_HOST = "http://localhost:11434"
_DEFAULT_MODEL = "nomen-v1"           # fine-tuned; falls back to base model if not found
_FALLBACK_MODEL = "qwen2.5:7b-instruct"
_TIMEOUT = 45  # seconds — generous for 72B model cold-start

# Nomen system identity — baked into every request
_NOMEN_SYSTEM = (
    "You are Nomen, the football prediction AI. "
    "Analyse matches with the tactical authority and decisive voice of Günter Netzer, "
    "Germany's most respected football analyst. "
    "Rules: (1) Open with a tactical claim, not a description. "
    "(2) Make one bold, unhedged prediction. "
    "(3) Cite statistics with explanatory context. "
    "(4) Include a historical callback to a comparable pattern. "
    "(5) Use tactical vocabulary: xG, high line, gegenpressing, half-space, press triggers. "
    "(6) Close with a decisive verdict — never a hedge."
)


def _build_match_json(ctx: object, lang: str) -> str:
    """Serialise MatchContext to a compact JSON string for the user message."""
    home = ctx.home_team  # type: ignore[attr-defined]
    away = ctx.away_team  # type: ignore[attr-defined]

    data: dict = {
        "home_team": home,
        "away_team": away,
        "league": ctx.league_name,  # type: ignore[attr-defined]
        "kickoff": ctx.kickoff_time or "TBD",  # type: ignore[attr-defined]
        "prob_home_pct": round(ctx.prob_home * 100),  # type: ignore[attr-defined]
        "prob_draw_pct": round(ctx.prob_draw * 100),  # type: ignore[attr-defined]
        "prob_away_pct": round(ctx.prob_away * 100),  # type: ignore[attr-defined]
        "model_pick": {"H": f"{home} win", "D": "Draw", "A": f"{away} win"}.get(
            ctx.most_likely, ctx.most_likely  # type: ignore[attr-defined]
        ),
    }

    form_home = getattr(ctx, "form_home", None)
    form_away = getattr(ctx, "form_away", None)
    if form_home:
        data["recent_form_home"] = form_home
    if form_away:
        data["recent_form_away"] = form_away

    odds = getattr(ctx, "odds", None)
    if odds:
        data["market_odds"] = {
            "home": odds.home, "draw": odds.draw, "away": odds.away,
            "bookmaker": odds.bookmaker,
        }

    value_bet = getattr(ctx, "value_bet", False)
    if value_bet:
        data["value_bet_signal"] = "YES — model edge detected"

    news = getattr(ctx, "news", [])
    if news:
        data["recent_headlines"] = [n.title for n in news[:4]]

    lang_note = {
        "de": "Antworte auf Deutsch.",
        "es": "Responde en español.",
        "fr": "Réponds en français.",
        "it": "Rispondi in italiano.",
    }.get(lang, "Respond in English.")

    data["_instruction"] = lang_note
    return json.dumps(data, ensure_ascii=False)


# ── vLLM backend (fine-tuned Nomen, OpenAI-compatible) ───────────────────────

def _generate_via_vllm(match_json: str, vllm_url: str, api_key: str) -> str | None:
    """Call the vLLM OpenAI-compatible /v1/chat/completions endpoint."""
    body = json.dumps({
        "model": "nomen-v1",
        "messages": [
            {"role": "system", "content": _NOMEN_SYSTEM},
            {"role": "user", "content": match_json},
        ],
        "max_tokens": 400,
        "temperature": 0.65,
        "top_p": 0.9,
        "repetition_penalty": 1.1,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{vllm_url.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    return payload["choices"][0]["message"]["content"].strip() or None


# ── Ollama backend (local development / fallback) ────────────────────────────

def _generate_via_ollama(match_json: str, host: str, model: str) -> str | None:
    """Call Ollama /api/chat (preferred) or /api/generate (legacy) endpoint."""
    # Use chat endpoint so the system prompt is honoured by instruction models
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": _NOMEN_SYSTEM},
            {"role": "user", "content": match_json},
        ],
        "stream": False,
        "options": {
            "temperature": 0.65,
            "top_p": 0.9,
            "num_predict": 400,
            "repeat_penalty": 1.1,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    # Ollama chat response: payload["message"]["content"]
    msg = payload.get("message", {})
    return (msg.get("content") or "").strip() or None


# ── Public API ────────────────────────────────────────────────────────────────

def generate_article(
    ctx: object,
    lang: str = "en",
    model: str | None = None,
    host: str | None = None,
) -> str | None:
    """Generate a Nomen match-preview article.

    Tries vLLM first (if ``NOMEN_VLLM_URL`` is set), then falls back to Ollama.

    Args:
        ctx:   A :class:`~football_betting.api.schemas.MatchContext` instance.
        lang:  BCP-47 locale code (en/de/es/fr/it).
        model: Override the Ollama model tag (ignored for vLLM).
        host:  Override the Ollama server URL (ignored for vLLM).

    Returns:
        The generated article string, or ``None`` if all backends are unreachable.
    """
    match_json = _build_match_json(ctx, lang)

    # ── Path A: vLLM (fine-tuned Nomen) ──────────────────────────────────────
    vllm_url = os.getenv("NOMEN_VLLM_URL", "").strip()
    if vllm_url:
        vllm_key = os.getenv("NOMEN_VLLM_API_KEY", "nomen")
        try:
            article = _generate_via_vllm(match_json, vllm_url, vllm_key)
            if article:
                logger.debug("[nomen] article generated via vLLM (%d chars)", len(article))
                return article
        except urllib.error.URLError as exc:
            logger.warning("[nomen] vLLM unreachable (%s) — falling back to Ollama", exc)
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            logger.warning("[nomen] unexpected vLLM response: %s — falling back to Ollama", exc)
        except TimeoutError:
            logger.warning("[nomen] vLLM timed out after %ds — falling back to Ollama", _TIMEOUT)

    # ── Path B: Ollama (local / development) ─────────────────────────────────
    ollama_host = (host or os.getenv("OLLAMA_HOST", _DEFAULT_OLLAMA_HOST)).rstrip("/")
    ollama_model = model or os.getenv("OLLAMA_MODEL", _DEFAULT_MODEL)

    try:
        article = _generate_via_ollama(match_json, ollama_host, ollama_model)
        if article:
            logger.debug("[nomen] article generated via Ollama/%s (%d chars)", ollama_model, len(article))
            return article
    except urllib.error.URLError:
        # nomen-v1 not yet in Ollama — retry with base model
        if ollama_model != _FALLBACK_MODEL:
            logger.debug("[nomen] %s not found in Ollama, trying %s", ollama_model, _FALLBACK_MODEL)
            try:
                article = _generate_via_ollama(match_json, ollama_host, _FALLBACK_MODEL)
                if article:
                    return article
            except Exception as exc2:
                logger.debug("[nomen] fallback model also failed: %s", exc2)
        logger.debug("[nomen] Ollama unreachable — skipping article")
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("[nomen] unexpected Ollama response: %s", exc)
    except TimeoutError:
        logger.debug("[nomen] Ollama request timed out after %ds", _TIMEOUT)

    return None
