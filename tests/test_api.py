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


def test_enrich_predictions_with_live_and_graded() -> None:
    """Unit-test the enrichment pass: live + graded rows merge into PredictionOut."""
    from datetime import datetime

    from football_betting.api import services
    from football_betting.api.schemas import (
        OddsOut,
        PredictionOut,
        TodayPayload,
    )

    payload = TodayPayload(
        generated_at=datetime.utcnow(),
        predictions=[
            PredictionOut(
                date="2026-04-18",
                league="PL",
                league_name="Premier League",
                home_team="Tottenham",
                away_team="Brighton",
                prob_home=0.3,
                prob_draw=0.3,
                prob_away=0.4,
                odds=OddsOut(home=3.0, draw=3.3, away=2.2),
                model_name="Ensemble",
                most_likely="A",
            ),
            PredictionOut(
                date="2026-04-18",
                league="PL",
                league_name="Premier League",
                home_team="Chelsea",
                away_team="Man United",
                prob_home=0.5,
                prob_draw=0.25,
                prob_away=0.25,
                odds=OddsOut(home=1.8, draw=3.5, away=4.0),
                model_name="Ensemble",
                most_likely="H",
            ),
            PredictionOut(
                date="2026-04-18",
                league="PL",
                league_name="Premier League",
                home_team="Arsenal",
                away_team="Liverpool",
                prob_home=0.4,
                prob_draw=0.3,
                prob_away=0.3,
                odds=None,
                model_name="Ensemble",
                most_likely="H",
            ),
        ],
    )

    fake_live = {
        "PL": {
            # Chelsea vs Man United is live, 0-0
            (
                datetime(2026, 4, 18).date(),
                "chelsea",
                "man united",
            ): ("live", "D", 0, 0),
            # Arsenal vs Liverpool completed Arsenal won 2-1
            (
                datetime(2026, 4, 18).date(),
                "arsenal",
                "liverpool",
            ): ("completed", "H", 2, 1),
        }
    }

    # Tottenham-Brighton settled via graded log as a LOST pick (pick=A, ft=H).
    class FakeGraded:
        def __init__(
            self, league, date, home, away, status, ft_result, ft_score
        ) -> None:
            self.league = league
            self.date = date
            self.home_team = home
            self.away_team = away
            self.status = status
            self.ft_result = ft_result
            self.ft_score = ft_score
            self.kind = "prediction"

    graded = [
        FakeGraded("PL", "2026-04-18", "Tottenham", "Brighton", "lost", "H", "2-0"),
    ]

    def fake_load_graded():
        return graded

    def fake_load_live(code):
        return fake_live.get("PL", {}) if code == "E0" else {}

    import football_betting.evaluation.grader as grader_mod
    import football_betting.evaluation.live_results as lr_mod

    orig_load_graded = grader_mod.load_graded
    orig_load_live = lr_mod.load_live_matches_for_code
    try:
        grader_mod.load_graded = fake_load_graded  # type: ignore[assignment]
        lr_mod.load_live_matches_for_code = fake_load_live  # type: ignore[assignment]
        enriched = services._enrich_predictions_with_live_and_graded(payload)
    finally:
        grader_mod.load_graded = orig_load_graded  # type: ignore[assignment]
        lr_mod.load_live_matches_for_code = orig_load_live  # type: ignore[assignment]

    by_home = {p.home_team: p for p in enriched.predictions}

    tot = by_home["Tottenham"]
    assert tot.is_live is False
    assert tot.pick_correct is False
    assert tot.ft_score == "2-0"

    chel = by_home["Chelsea"]
    assert chel.is_live is True
    assert chel.pick_correct is None
    assert chel.ft_score == "0-0"

    ars = by_home["Arsenal"]
    assert ars.is_live is False
    assert ars.pick_correct is True  # picked H, completed H
    assert ars.ft_score == "2-1"


def test_seo_slugs_returns_league_slugs(client: TestClient) -> None:
    res = client.get("/seo/slugs")
    assert res.status_code == 200
    assert "public" in res.headers.get("cache-control", "").lower()
    body = res.json()
    assert "leagues" in body and "teams" in body
    keys = {entry["key"] for entry in body["leagues"]}
    assert {"PL", "BL", "SA", "LL", "CH"}.issubset(keys)
    for entry in body["leagues"]:
        assert entry["slug"]
        assert " " not in entry["slug"]
        assert entry["slug"] == entry["slug"].lower()


def test_get_match_wrapper_persists_lazy_sofascore_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import datetime

    from football_betting.api import services
    from football_betting.api.schemas import PredictionOut, TodayPayload
    import football_betting.seo.match_slugs as match_slugs_mod

    slug = "lecce-vs-fiorentina-2026-04-20"
    snapshot = TodayPayload(
        generated_at=datetime.utcnow(),
        predictions=[
            PredictionOut(
                date="2026-04-20",
                league="SA",
                league_name="Serie A",
                home_team="Lecce",
                away_team="Fiorentina",
                prob_home=0.24,
                prob_draw=0.26,
                prob_away=0.50,
                model_name="Ensemble",
                most_likely="A",
            )
        ],
    )
    persisted: dict[str, TodayPayload] = {}

    class FakeSofascoreClient:
        def find_event_id(self, *_args, **_kwargs) -> int:
            return 13980099

    def fake_write_today(payload: TodayPayload) -> str:
        persisted["payload"] = payload.model_copy(deep=True)
        return "today.json"

    monkeypatch.setattr(services, "load_today", lambda: snapshot)
    monkeypatch.setattr(services, "write_today", fake_write_today)
    monkeypatch.setattr(
        services,
        "_new_sofascore_lookup_client",
        lambda _context: FakeSofascoreClient(),
    )
    monkeypatch.setattr(match_slugs_mod, "attach_archive", lambda wrapper: wrapper)

    wrapper = services.get_match_wrapper(slug)

    assert wrapper is not None
    assert wrapper.sofascore_event_id == 13980099
    assert persisted["payload"].predictions[0].sofascore_event_id == 13980099
