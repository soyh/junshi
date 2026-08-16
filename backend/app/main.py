import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config.settings import get_settings
from app.core.bootstrap import ensure_local_user
from app.core.database import initialize_database
from app.core.logging import setup_logging
from app.core.migrations import run_migrations

setup_logging()

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    run_migrations()
    ensure_local_user()

    logger.info("Application startup complete")

    yield

    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.1.0",
    }


app.include_router(api_router)
