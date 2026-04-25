from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from football_betting.data import football_data
from football_betting.evaluation import live_results

CSV = """Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A
E0,25/04/2026,15:00,Arsenal,Chelsea,,,,1.90,3.50,4.20
E0,25/04/2026,17:30,Liverpool,Everton,2,1,H,1.55,4.00,6.00
E0,26/04/2026,14:00,Tottenham,Brighton,,,,2.20,3.40,3.10
"""


def test_load_fixtures_for_date_from_football_data_csv(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "E0_2526.csv").write_text(CSV, encoding="utf-8")
    monkeypatch.setattr(football_data, "RAW_DIR", tmp_path)

    fixtures = football_data.load_fixtures_for_date(
        date(2026, 4, 25),
        leagues=["PL"],
        refresh=False,
    )

    assert len(fixtures) == 2
    assert fixtures[0]["source"] == "football_data"
    assert fixtures[0]["home_team"] == "Arsenal"
    assert fixtures[0]["odds"] == {
        "home": 1.9,
        "draw": 3.5,
        "away": 4.2,
        "bookmaker": "Bet365",
    }
    assert fixtures[1]["home_team"] == "Liverpool"


def test_poll_and_store_scores_football_data(
    tmp_path: Path,
    monkeypatch,
) -> None:
    season = football_data.season_for_date(date.today())
    from football_betting.data.downloader import season_code

    csv_name = f"E0_{season_code(season)}.csv"
    today = date.today().strftime("%d/%m/%Y")
    (tmp_path / csv_name).write_text(
        "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        f"E0,{today},15:00,Arsenal,Chelsea,3,1,H,1.90,3.50,4.20\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(football_data, "RAW_DIR", tmp_path)
    monkeypatch.setattr(live_results, "LIVE_SCORES_FILE", tmp_path / "live_scores.jsonl")

    added = live_results.poll_and_store_scores_football_data(["E0"], refresh=False)

    assert added == 1
    rows = [
        json.loads(line)
        for line in (tmp_path / "live_scores.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0]["source"] == "football_data"
    assert rows[0]["status"] == "completed"
    assert rows[0]["ftr"] == "H"
