"""Runtime service for the public support-chatbot endpoint.

Wraps :class:`football_betting.support.two_head_transformer.TwoHeadTransformerIntentClassifier`
with a single-slot LRU cache so only one language model lives in RAM at a
time (the trained XLM-R-base encoder is ~1.1 GB per language, which is too
much to keep loaded simultaneously on Railway).

Temperature calibration (``temperature.json`` next to each encoder) is applied
post-hoc here because ``TwoHeadTransformerIntentClassifier.load`` does not
restore it at present; applying it sharpens top-k probabilities without
changing argmax.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from football_betting.config import SUPPORT_CFG, SUPPORT_MODELS_DIR

logger = logging.getLogger("football_betting.api")

# Languages for which a ``support_twohead_{lang}`` directory was shipped.
_SUPPORTED_LANGS: tuple[str, ...] = ("de", "en", "es", "fr", "it")

# Low-confidence / out-of-distribution thresholds. When the top-1 intent is
# ``__ood__`` **or** its calibrated probability falls below this gate, the
# endpoint reports an empty ``predictions`` list so the frontend can fall back
# to its Fuse.js FAQ search.
_OOD_INTENT_ID = "__ood__"
_MIN_CONFIDENCE = 0.20


@dataclass(frozen=True, slots=True)
class SupportPrediction:
    intent_id: str
    chapter: str
    score: float
    chapter_score: float


class SupportModelUnavailable(RuntimeError):
    """Raised when the two-head model cannot be loaded (missing dir, bad deps)."""


class _SingleSlotCache:
    """Thread-safe cache that keeps at most one classifier in RAM."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current_lang: str | None = None
        self._current_clf: object | None = None
        self._current_temperature: float = 1.0

    def get(self, lang: str) -> tuple[object, float]:
        with self._lock:
            if self._current_lang == lang and self._current_clf is not None:
                return self._current_clf, self._current_temperature
            # Evict the previous classifier *before* loading the next one so
            # peak RSS stays below ~1.5 GB instead of ~2.5 GB.
            self._current_clf = None
            self._current_lang = None
            self._current_temperature = 1.0
            clf, temperature = _load_classifier(lang)
            self._current_clf = clf
            self._current_lang = lang
            self._current_temperature = temperature
            return clf, temperature


_cache = _SingleSlotCache()


def _model_dir(lang: str) -> Path:
    return SUPPORT_MODELS_DIR / SUPPORT_CFG.two_head_model_dirname_template.format(lang=lang)


def _load_classifier(lang: str) -> tuple[object, float]:
    directory = _model_dir(lang)
    if not directory.exists():
        raise SupportModelUnavailable(f"Support model directory missing: {directory}")

    try:
        from football_betting.support.two_head_transformer import (
            TwoHeadTransformerIntentClassifier,
        )
    except ImportError as exc:  # missing torch/transformers extras
        raise SupportModelUnavailable(
            "Support runtime requires torch + transformers (install [api] extras)."
        ) from exc

    logger.info("[support] loading two-head model for lang=%s", lang)
    clf = TwoHeadTransformerIntentClassifier.load(directory)

    temperature = 1.0
    temp_path = directory / "temperature.json"
    if temp_path.exists():
        try:
            payload = json.loads(temp_path.read_text(encoding="utf-8"))
            t_val = float(payload.get("temperature", 1.0))
            if t_val > 0:
                temperature = t_val
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("[support] invalid temperature.json for %s: %s", lang, exc)

    logger.info("[support] loaded lang=%s (T=%.3f)", lang, temperature)
    return clf, temperature


def _normalize_lang(lang: str) -> str:
    norm = (lang or "en").strip().lower()[:2]
    return norm if norm in _SUPPORTED_LANGS else "en"


def _apply_temperature(score: float, temperature: float) -> float:
    """Sharpen/soften a softmax probability by rescaling its logit by 1/T.

    Because :meth:`predict_topk` only returns the per-intent probability (not
    the full logits vector), this is a first-order approximation good enough
    for display — it does not change ranking.
    """
    if temperature <= 0 or abs(temperature - 1.0) < 1e-6:
        return score
    score = min(max(score, 1e-9), 1 - 1e-9)
    import math

    logit = math.log(score / (1.0 - score))
    scaled = logit / temperature
    return 1.0 / (1.0 + math.exp(-scaled))


def classify(question: str, lang: str, top_k: int = 3) -> list[SupportPrediction]:
    """Classify a user question.

    Returns an empty list when the top-1 prediction is out-of-distribution or
    below the confidence gate — the caller should fall back to FAQ search in
    that case.
    """
    question = (question or "").strip()
    if not question:
        return []

    resolved = _normalize_lang(lang)
    clf, temperature = _cache.get(resolved)

    # ``TwoHeadTransformerIntentClassifier`` exposes ``predict_topk``.
    predictions = clf.predict_topk(question, k=max(1, min(int(top_k), 10)))  # type: ignore[attr-defined]
    if not predictions:
        return []

    top = predictions[0]
    if top.intent_id == _OOD_INTENT_ID:
        return []
    if _apply_temperature(top.score, temperature) < _MIN_CONFIDENCE:
        return []

    out: list[SupportPrediction] = []
    for p in predictions:
        if p.intent_id == _OOD_INTENT_ID:
            continue
        out.append(
            SupportPrediction(
                intent_id=p.intent_id,
                chapter=p.chapter,
                score=_apply_temperature(p.score, temperature),
                chapter_score=p.chapter_score,
            )
        )
    return out


def supported_languages() -> tuple[str, ...]:
    return _SUPPORTED_LANGS


# ── Match-context detection ───────────────────────────────────────────────────

import re
import unicodedata


def _normalise_name(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).lower().strip()


def _team_tokens(team: str) -> list[str]:
    """Split a team name into searchable sub-tokens.

    Returns the full normalised name plus each individual word longer than
    2 chars so e.g. "Arsenal" matches "Arsenal FC" and vice-versa.
    """
    full = _normalise_name(team)
    words = [w for w in full.split() if len(w) > 2]
    tokens = [full] + words
    return tokens


def find_match_context(
    question: str,
    predictions: list,
    value_bets: list,
) -> object | None:
    """Return a :class:`MatchContext` when the question mentions a team.

    Scans ``predictions`` (list of PredictionOut) for any team whose name
    (or a meaningful sub-token) appears in the question text. Returns the
    first match found, enriched with recent news headlines and form strings.
    Returns ``None`` when no team mention is detected or the prediction list
    is empty.
    """
    if not predictions:
        return None

    from football_betting.api.schemas import MatchContext, MatchNewsItem, OddsOut
    from football_betting.scraping.news import fetch_match_news

    q_norm = _normalise_name(question)

    # Build a set of value-bet (home, away) pairs for quick lookup
    value_pairs: set[tuple[str, str]] = {
        (_normalise_name(vb.home_team), _normalise_name(vb.away_team))
        for vb in value_bets
    }

    matched_pred = None
    for pred in predictions:
        home_tokens = _team_tokens(pred.home_team)
        away_tokens = _team_tokens(pred.away_team)
        all_tokens = home_tokens + away_tokens
        if any(tok in q_norm for tok in all_tokens):
            matched_pred = pred
            break

    if matched_pred is None:
        return None

    # Fetch recent form strings via league data (best-effort)
    form_home: str | None = None
    form_away: str | None = None
    try:
        from football_betting.data.loader import load_league

        matches = load_league(matched_pred.league)
        matches.sort(key=lambda m: m.date)
        _N = 5
        h_str = ""
        a_str = ""
        for m in reversed(matches):
            if len(h_str) < _N and (m.home_team == matched_pred.home_team or m.away_team == matched_pred.home_team):
                scored = m.home_goals if m.home_team == matched_pred.home_team else m.away_goals
                conceded = m.away_goals if m.home_team == matched_pred.home_team else m.home_goals
                h_str += "W" if scored > conceded else ("D" if scored == conceded else "L")
            if len(a_str) < _N and (m.home_team == matched_pred.away_team or m.away_team == matched_pred.away_team):
                scored = m.home_goals if m.home_team == matched_pred.away_team else m.away_goals
                conceded = m.away_goals if m.home_team == matched_pred.away_team else m.home_goals
                a_str += "W" if scored > conceded else ("D" if scored == conceded else "L")
            if len(h_str) >= _N and len(a_str) >= _N:
                break
        form_home = h_str[::-1] or None  # reverse to chronological (oldest→newest)
        form_away = a_str[::-1] or None
    except Exception as exc:
        logger.debug("[support] form lookup failed: %s", exc)

    # Fetch news (non-blocking; empty list on failure)
    news_items = fetch_match_news(matched_pred.home_team, matched_pred.away_team, max_per_team=2)

    is_value = (
        _normalise_name(matched_pred.home_team),
        _normalise_name(matched_pred.away_team),
    ) in value_pairs

    odds_out: OddsOut | None = None
    if matched_pred.odds is not None:
        odds_out = OddsOut(
            home=matched_pred.odds.home,
            draw=matched_pred.odds.draw,
            away=matched_pred.odds.away,
            bookmaker=matched_pred.odds.bookmaker,
        )

    return MatchContext(
        home_team=matched_pred.home_team,
        away_team=matched_pred.away_team,
        league=matched_pred.league,
        league_name=matched_pred.league_name,
        kickoff_time=matched_pred.kickoff_time,
        prob_home=round(matched_pred.prob_home, 3),
        prob_draw=round(matched_pred.prob_draw, 3),
        prob_away=round(matched_pred.prob_away, 3),
        most_likely=matched_pred.most_likely,
        odds=odds_out,
        form_home=form_home,
        form_away=form_away,
        value_bet=is_value,
        news=[
            MatchNewsItem(title=n.title, url=n.url, source=n.source)
            for n in news_items
        ],
    )


def generate_match_article(ctx: object, lang: str) -> str | None:
    """Generate a Nomen match-preview article for *ctx* in the given language.

    Delegates to :mod:`football_betting.support.match_analyst`.  Returns
    ``None`` when Ollama is not available so the chatbot keeps working.
    """
    try:
        from football_betting.support.match_analyst import generate_article
        return generate_article(ctx, lang=lang)
    except Exception as exc:
        logger.debug("[nomen] article generation failed: %s", exc)
        return None
