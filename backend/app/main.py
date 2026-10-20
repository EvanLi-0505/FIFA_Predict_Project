"""FastAPI application entry point.

Run with:
    .venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --port 8000

/docs and /redoc are provided automatically by FastAPI (Development
Prompt.md Section 38).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import datasets, history, models, predictions, team_stats, teams
from backend.app.config import settings
from backend.app.db.session import SessionFactory, engine
from backend.app.services import feature_service, team_stats_service
from database.bootstrap import bootstrap_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: bootstrapping database...")
    with SessionFactory() as session:
        bootstrap_database(
            engine,
            session,
            builtin_dataset_csv=settings.builtin_dataset_csv,
            initial_model_dir=settings.initial_model_dir,
        )
        logger.info("Database ready.")

        # Building the historical-feature pipeline over the full dataset is
        # the single most expensive operation this app performs (several
        # seconds on the ~50k-row built-in dataset). It's cached after the
        # first call (see feature_service/team_stats_service module
        # docstrings), but paying that cost lazily on whatever request
        # happens to arrive first makes the Desktop app look "ready" (the
        # window is shown, the health check passed) and then freeze for
        # several seconds on the user's first click — surprising and, on a
        # slow machine, easy to mistake for a hang/crash. Warming both
        # caches here instead means the cost is paid ONCE, up front, before
        # the Desktop app's window is ever shown (see desktop_app/main.py's
        # `wait_for_server`, which blocks on this very lifespan finishing).
        logger.info("Warming feature/team-stats caches...")
        try:
            feature_service.get_inference_context(session)
        except Exception:  # noqa: BLE001 - startup warm-up must never be fatal
            logger.exception("Feature cache warm-up failed (will retry on first request).")
        try:
            team_stats_service.list_teams(session)
        except Exception:  # noqa: BLE001
            logger.exception("Team-stats cache warm-up failed (will retry on first request).")
        logger.info("Caches warm.")

    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="FIFA World Cup Match Prediction API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions.router)
app.include_router(history.router)
app.include_router(teams.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(team_stats.router)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
