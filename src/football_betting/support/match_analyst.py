"""Nomen match-article generator — wraps a local Ollama LLM.

Calls the Ollama ``/api/generate`` endpoint (default: ``http://localhost:11434``)
with a structured prompt that includes model probabilities, recent form, odds,
and news headlines.  Returns a 3–5 sentence informative match preview written
in the user's language, or ``None`` on any network / timeout failure so the
chatbot never breaks in production.

Environment variables:
    OLLAMA_HOST   — base URL of the Ollama server (default: http://localhost:11434)
    OLLAMA_MODEL  — model tag to use          (default: qwen2.5:7b-instruct)
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger("football_betting.support.nomen")

_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_MODEL = "qwen2.5:7b-instruct"
_TIMEOUT = 30  # seconds


def _build_prompt(ctx: object, lang: str) -> str:  # ctx: MatchContext
    """Assemble the structured prompt sent to Ollama."""
    home = ctx.home_team  # type: ignore[attr-defined]
    away = ctx.away_team  # type: ignore[attr-defined]
    league = ctx.league_name  # type: ignore[attr-defined]
    ko = ctx.kickoff_time or "TBD"  # type: ignore[attr-defined]

    ph = round(ctx.prob_home * 100)  # type: ignore[attr-defined]
    pd = round(ctx.prob_draw * 100)  # type: ignore[attr-defined]
    pa = round(ctx.prob_away * 100)  # type: ignore[attr-defined]

    form_home = ctx.form_home or "N/A"  # type: ignore[attr-defined]
    form_away = ctx.form_away or "N/A"  # type: ignore[attr-defined]
    value_flag = "YES — this match has a value-bet signal" if ctx.value_bet else "No"  # type: ignore[attr-defined]

    odds_line = ""
    if ctx.odds:  # type: ignore[attr-defined]
        o = ctx.odds  # type: ignore[attr-defined]
        odds_line = f"\nMarket odds: Home {o.home} | Draw {o.draw} | Away {o.away} ({o.bookmaker})"

    news_lines = ""
    news = getattr(ctx, "news", [])
    if news:
        headlines = "\n".join(f"  - {n.title} ({n.source})" for n in news[:4])
        news_lines = f"\nRecent headlines:\n{headlines}"

    lang_instruction = {
        "de": "Write the article in German.",
        "es": "Write the article in Spanish.",
        "fr": "Write the article in French.",
        "it": "Write the article in Italian.",
    }.get(lang, "Write the article in English.")

    return f"""You are Nomen, an expert AI football analyst. Your role is to help users understand upcoming football matches using predictive model data.

Match data:
  Match: {home} vs {away}
  League: {league}
  Kickoff: {ko}
  Model probabilities: Home {ph}% | Draw {pd}% | Away {pa}%
  Recent form ({home}): {form_home}
  Recent form ({away}): {form_away}
  Value-bet signal: {value_flag}{odds_line}{news_lines}

Task: Write a concise, informative match preview of exactly 3–5 sentences. Reference the probabilities, both teams' recent form, and at least one news headline if available. Conclude with the model's prediction and whether there is a value-bet opportunity. Do not use bullet points — write flowing prose only. {lang_instruction}

Match preview:"""


def generate_article(
    ctx: object,
    lang: str = "en",
    model: str | None = None,
    host: str | None = None,
) -> str | None:
    """Generate a Nomen match-preview article via Ollama.

    Args:
        ctx:   A :class:`~football_betting.api.schemas.MatchContext` instance.
        lang:  BCP-47 locale code (en/de/es/fr/it).
        model: Override the Ollama model tag.
        host:  Override the Ollama server URL.

    Returns:
        The generated article string, or ``None`` if Ollama is unreachable or
        returns an error.
    """
    resolved_host = (host or os.getenv("OLLAMA_HOST", _DEFAULT_HOST)).rstrip("/")
    resolved_model = model or os.getenv("OLLAMA_MODEL", _DEFAULT_MODEL)

    prompt = _build_prompt(ctx, lang)

    body = json.dumps({
        "model": resolved_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 300,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{resolved_host}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        article = payload.get("response", "").strip()
        if not article:
            logger.warning("[nomen] Ollama returned empty response for %s", resolved_model)
            return None
        return article
    except urllib.error.URLError as exc:
        logger.debug("[nomen] Ollama unreachable (%s) — skipping article", exc)
        return None
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("[nomen] unexpected Ollama response format: %s", exc)
        return None
    except TimeoutError:
        logger.debug("[nomen] Ollama request timed out after %ds", _TIMEOUT)
        return None
