"""Smoke tests for the FastAPI layer.

Skipped automatically if FastAPI / httpx aren't installed (the [api] / [dev]
extras provide them).
"""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from football_betting.api.app import create_app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def test_health_endpoint(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "models_available" in body


def test_leagues_endpoint(client: TestClient) -> None:
    res = client.get("/leagues")
    assert res.status_code == 200
    leagues = res.json()
    assert isinstance(leagues, list)
    assert len(leagues) >= 1
    keys = {league["key"] for league in leagues}
    assert {"PL", "BL", "SA", "LL", "CH"}.issubset(keys)


def test_predictions_today_returns_payload(client: TestClient) -> None:
    res = client.get("/predictions/today")
    assert res.status_code == 200
    body = res.json()
    assert "generated_at" in body
    assert "predictions" in body
    assert "value_bets" in body


def test_unknown_league_is_404(client: TestClient) -> None:
    res = client.get("/leagues/ZZ/ratings")
    assert res.status_code == 404


def test_performance_summary_is_resilient_to_empty_log(client: TestClient) -> None:
    res = client.get("/performance/summary")
    assert res.status_code == 200
    body = res.json()
    assert body["n_bets"] >= 0
    assert "per_league" in body


def test_performance_bankroll_returns_list(client: TestClient) -> None:
    res = client.get("/performance/bankroll")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
