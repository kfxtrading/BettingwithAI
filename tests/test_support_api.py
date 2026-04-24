"""Smoke tests for the POST /support/ask endpoint.

The real two-head model weighs ~1 GB per language and is slow to load on CI,
so the tests monkey-patch :func:`football_betting.api.support_service.classify`
to exercise the routing layer without touching torch.
"""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from football_betting.api import support_service  # noqa: E402
from football_betting.api.app import create_app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def test_support_ask_returns_predictions(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = [
        support_service.SupportPrediction(
            intent_id="value-bet",
            chapter="basics",
            score=0.82,
            chapter_score=0.91,
        ),
        support_service.SupportPrediction(
            intent_id="kelly",
            chapter="strategy",
            score=0.05,
            chapter_score=0.04,
        ),
    ]
    monkeypatch.setattr(
        "football_betting.api.routes.support_service.classify",
        lambda question, lang, top_k: fake,
    )
    res = client.post(
        "/support/ask",
        json={"question": "was ist ein value bet?", "lang": "de", "top_k": 2},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["lang"] == "de"
    assert body["fallback"] is False
    assert len(body["predictions"]) == 2
    assert body["predictions"][0]["intent_id"] == "value-bet"


def test_support_ask_ood_falls_back(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "football_betting.api.routes.support_service.classify",
        lambda question, lang, top_k: [],
    )
    res = client.post(
        "/support/ask",
        json={"question": "hello world", "lang": "en"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["fallback"] is True
    assert body["predictions"] == []


def test_support_ask_model_unavailable_still_returns_200(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(question: str, lang: str, top_k: int) -> list[support_service.SupportPrediction]:
        raise support_service.SupportModelUnavailable("missing model dir")

    monkeypatch.setattr(
        "football_betting.api.routes.support_service.classify",
        _raise,
    )
    res = client.post(
        "/support/ask",
        json={"question": "anything", "lang": "en"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["fallback"] is True
    assert body["predictions"] == []


def test_support_ask_rejects_empty_question(client: TestClient) -> None:
    res = client.post("/support/ask", json={"question": "", "lang": "en"})
    assert res.status_code == 422


def test_classify_returns_empty_for_blank_question() -> None:
    assert support_service.classify("   ", "en") == []


def test_normalize_lang_defaults_to_english() -> None:
    # Unsupported locale is coerced to 'en' (never raises).
    assert support_service._normalize_lang("pt") == "en"
    assert support_service._normalize_lang("DE") == "de"
    assert support_service._normalize_lang("en-GB") == "en"
