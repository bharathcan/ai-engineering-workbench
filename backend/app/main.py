import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401  # registers ORM models on Base.metadata before create_all
from app.api.routes.ai_runs import router as ai_runs_router
from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.health import router as health_router
from app.api.routes.requirements import router as requirements_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.urls import router as urls_router
from app.api.routes.validations import router as validations_router
from app.core.config import settings
from app.core.database import Base, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # No migration framework yet (see backend/README.md) — with two tables
    # and a schema still likely to change, create_all() is the smallest
    # maintainable choice for this phase.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Engineering Workbench API",
    description="Backend API for the AI Engineering Workbench.",
    version="0.1.0",
    lifespan=lifespan,
)

# Defaults to the local Vite dev server; set CORS_ORIGINS (comma-separated)
# for any deployed frontend origin — see app.core.config.Settings.cors_origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(requirements_router)
app.include_router(tasks_router)
app.include_router(ai_runs_router)
app.include_router(artifacts_router)
app.include_router(validations_router)
# Registered last: its GET /{short_code} catch-all route must never shadow
# a more specific route registered above it.
app.include_router(urls_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Last-resort safety net: never let an unexpected exception's message or
    # traceback reach the client. Route-level handlers should catch specific
    # errors before this is hit; this exists in case one doesn't.
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})
