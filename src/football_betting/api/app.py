"""FastAPI application entry point."""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from football_betting.api.routes import API_VERSION, router


def _cors_origins() -> list[str]:
    raw = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


def _configure_logging() -> None:
    """Ensure `football_betting.api` log lines appear in the uvicorn console."""
    api_logger = logging.getLogger("football_betting.api")
    if api_logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-5s | %(message)s",
                                           datefmt="%H:%M:%S"))
    api_logger.addHandler(handler)
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = False


def create_app() -> FastAPI:
    _configure_logging()
    app = FastAPI(
        title="Betting with AI",
        version=API_VERSION,
        description="Football match predictions, value bets and model performance.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _log_startup() -> None:
        import asyncio
        from football_betting.api.snapshots import load_today
        from football_betting.config import DATA_DIR, LEAGUES, MODELS_DIR

        async def _seed_raw_csvs() -> None:
            """Idempotently fill /data/raw/ if empty — Railway volume fresh-boots empty."""
            raw_dir = DATA_DIR / "raw"
            if raw_dir.exists() and any(raw_dir.glob("*.csv")):
                return
            logger_ = logging.getLogger("football_betting.api")
            logger_.info("[startup] /data/raw empty — downloading football-data CSVs in background")
            try:
                from football_betting.data.downloader import download_all
                await asyncio.to_thread(download_all)
                logger_.info("[startup] CSV seed complete")
            except Exception as exc:
                logger_.warning("[startup] CSV seed failed: %s", exc)

        asyncio.create_task(_seed_raw_csvs())

        api_logger = logging.getLogger("football_betting.api")
        api_logger.info("=" * 70)
        api_logger.info("Betting with AI v%s — serving predictions", API_VERSION)
        api_logger.info("=" * 70)

        model_status = []
        for key in LEAGUES:
            cb = (MODELS_DIR / f"catboost_{key}.cbm").exists()
            mlp = (MODELS_DIR / f"mlp_{key}.pt").exists()
            if cb or mlp:
                parts = []
                if cb: parts.append("CatBoost")
                if mlp: parts.append("MLP")
                model_status.append(f"{key}=[{'+'.join(parts)}]")
            else:
                model_status.append(f"{key}=[Poisson]")
        api_logger.info("[startup] Models per league: %s", " ".join(model_status))

        snap = load_today()
        if snap is None:
            api_logger.info("[startup] Snapshot: none — will compute on-demand on first request.")
        else:
            api_logger.info(
                "[startup] Snapshot: %d predictions, %d value bets (generated %s)",
                len(snap.predictions), len(snap.value_bets),
                snap.generated_at.isoformat(timespec="seconds"),
            )
            for ds in snap.data_sources:
                api_logger.info(
                    "[startup]   ↳ %s (%s): %s over %d matches | seasons %s",
                    ds.league_name, ds.league, ds.model, ds.n_matches,
                    ",".join(ds.seasons),
                )
        api_logger.info("[startup] Waiting for http://localhost:3000 to fetch /predictions/today …")

        from football_betting.api import scheduler
        await scheduler.start()

    app.include_router(router)
    return app


app = create_app()
