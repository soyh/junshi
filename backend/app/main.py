import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config.settings import Settings, get_settings
from app.core.bootstrap import ensure_local_user
from app.core.database import initialize_database
from app.core.logging import setup_logging
from app.core.migrations import run_migrations
from app.core.runtime_health import check_runtime_readiness

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


def _fastapi_surface_options(current_settings: Settings) -> dict[str, object]:
    is_production = current_settings.app_env.lower() == "production"

    return {
        "debug": bool(current_settings.app_debug and not is_production),
        "docs_url": None if is_production else "/docs",
        "redoc_url": None if is_production else "/redoc",
        "openapi_url": None if is_production else "/openapi.json",
    }


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    **_fastapi_surface_options(settings),
)


@app.middleware("http")
async def apply_http_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    path = request.url.path
    if (
        path.startswith("/api/v1/auth")
        or path.startswith("/api/v1/settings")
        or path in {"/health/live", "/health/ready"}
    ):
        response.headers["Cache-Control"] = "no-store"

    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.1.0",
    }


@app.get("/health/live")
def health_live():
    return {
        "status": "ok",
        "check": "liveness",
    }


@app.get("/health/ready")
def health_ready():
    current_settings = get_settings()
    report = check_runtime_readiness(current_settings.database_path)
    payload = {
        "status": "ready" if report.ready else "not_ready",
        "database": report.database,
        "migrations": report.migrations,
    }
    return JSONResponse(
        status_code=200 if report.ready else 503,
        content=payload,
    )


app.include_router(api_router)
