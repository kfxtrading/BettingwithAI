from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from football_betting.config import LEAGUES, WEATHER_CFG
from football_betting.data.loader import load_league
from football_betting.features.builder import FeatureBuilder
from football_betting.features.weather import WeatherTracker
from football_betting.predict.catboost_model import CatBoostPredictor
from football_betting.scraping.sofascore import SofascoreClient

print("weather_enabled:", WEATHER_CFG.enabled)

for league in LEAGUES.keys():
    try:
        matches = load_league(league, seasons=["2021-22", "2022-23", "2023-24", "2024-25"])
    except FileNotFoundError as exc:
        print(f"{league}: skip ({exc})")
        continue
    wt = WeatherTracker() if WEATHER_CFG.enabled else None
    fb = FeatureBuilder(weather_tracker=wt)
    for season in ("2023-24", "2024-25"):
        sf = SofascoreClient.load_matches(league, season)
        if sf:
            fb.stage_sofascore_batch(sf)
    predictor = CatBoostPredictor(feature_builder=fb)
    try:
        X, y, seasons = predictor.build_training_data(matches, warmup_games=100)
    except Exception as exc:
        print(f"{league}: ERR: {exc}")
        continue
    print(f"{league}: n_matches={len(matches)}, n_rows={len(X)}, n_feature_cols={X.shape[1]}")
