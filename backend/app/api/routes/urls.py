import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import (
    PersistenceError,
    ShortCodeGenerationExhaustedError,
    ShortenedUrlExpiredError,
    ShortenedUrlNotFoundError,
)
from app.schemas.url import (
    AdvancedAnalyticsResponse,
    CreateUrlRequest,
    UrlAnalyticsResponse,
    UrlResponse,
)
from app.services import url_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["urls"])

_SHORT_CODE_PATTERN = r"^[0-9A-Za-z]{4,16}$"


@router.post("/api/v1/urls", response_model=UrlResponse, status_code=201)
def create_url(payload: CreateUrlRequest, db: Session = Depends(get_db)):
    try:
        return url_service.create_url(db, payload.original_url, payload.expires_at)
    except ShortCodeGenerationExhaustedError as exc:
        logger.error("Short code generation exhausted: %s", exc)
        raise HTTPException(
            status_code=503, detail="Could not allocate a unique short code. Try again."
        ) from exc
    except PersistenceError as exc:
        logger.error("Failed to persist shortened URL: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create the shortened URL.") from exc


@router.get("/api/v1/urls/{short_code}/analytics", response_model=UrlAnalyticsResponse)
def get_url_analytics(short_code: str, db: Session = Depends(get_db)):
    try:
        return url_service.get_analytics(db, short_code)
    except ShortenedUrlNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load analytics for %s: %s", short_code, exc)
        raise HTTPException(status_code=500, detail="Failed to load analytics.") from exc


@router.get(
    "/api/v1/urls/{short_code}/analytics/advanced", response_model=AdvancedAnalyticsResponse
)
def get_url_advanced_analytics(short_code: str, db: Session = Depends(get_db)):
    """Interpretation C (Phase 10 ambiguous-requirement scenario) — see
    docs/adr/ADR-005-advanced-analytics-privacy.md."""
    try:
        return url_service.get_advanced_analytics(db, short_code)
    except ShortenedUrlNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load advanced analytics for %s: %s", short_code, exc)
        raise HTTPException(status_code=500, detail="Failed to load advanced analytics.") from exc


# Registered last in app.main so it never shadows a more specific route
# (e.g. /health, /docs). A 307 (not 301/308) is used deliberately: a
# permanent redirect status invites browsers to cache it and stop hitting
# this server on future visits, which would silently undercount clicks —
# see docs/adr/ADR-004-analytics-design.md.
#
# Phase 9 (brownfield): the click-count write is deferred to a
# BackgroundTask, which FastAPI runs after the response has already been
# sent (and, per FastAPI's own documented guarantee, before the `db`
# session from Depends(get_db) is closed — see
# docs/scenarios/brownfield.md) — so it no longer sits on the critical
# path being measured. The response itself (status code, Location header,
# body) is unchanged from before this change.
@router.get("/{short_code}")
def redirect_short_code(
    request: Request,
    background_tasks: BackgroundTasks,
    short_code: str = Path(pattern=_SHORT_CODE_PATTERN),
    db: Session = Depends(get_db),
):
    try:
        url = url_service.resolve_active_url(db, short_code)
    except ShortenedUrlNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ShortenedUrlExpiredError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to resolve short code %s: %s", short_code, exc)
        raise HTTPException(status_code=500, detail="Failed to resolve the short code.") from exc

    # Captured here (request is gone once the background task runs) and
    # passed through — the write itself, including hashing the IP, still
    # happens in the deferred background task. See ADR-005: the raw IP
    # never gets any further than this function call's arguments.
    background_tasks.add_task(
        url_service.record_click_for,
        db,
        url,
        referrer=request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
        client_ip=request.client.host if request.client else None,
    )
    return RedirectResponse(url=url.original_url, status_code=307)
