from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ShortenedUrlExpiredError, ShortenedUrlNotFoundError
from app.models.url import ShortenedUrl
from app.repositories import click_event_repository, url_repository
from app.schemas.url import (
    AdvancedAnalyticsResponse,
    BreakdownEntry,
    UrlAnalyticsResponse,
    UrlResponse,
)
from app.services.click_analytics import hash_ip
from app.services.short_code import generate_short_code
from app.services.user_agent import classify_browser, classify_device

# No GeoIP data source (local database or network lookup service) exists in
# this environment — geographic breakdown is honestly reported as
# unavailable rather than fabricated. See ADR-005.
GEOGRAPHIC_STATUS_NOT_AVAILABLE = (
    "Not implemented: no GeoIP data source is available in this environment. "
    "IP is hashed for repeat-visitor detection only, never resolved to a location."
)


def create_url(db: Session, original_url: str, expires_at: datetime | None) -> UrlResponse:
    url = url_repository.create_shortened_url(
        db, original_url, generate_short_code, expires_at=expires_at
    )
    return _to_response(url)


def resolve_active_url(db: Session, short_code: str) -> ShortenedUrl:
    """Read-only resolution for a redirect — no write happens here. See
    docs/scenarios/brownfield.md (Phase 9): the click-count write is
    deferred to record_click_for(), run as a FastAPI background task after
    the redirect response is already on its way, so it no longer blocks
    the request that's actually being timed."""
    return _get_active_or_raise(db, short_code)


def record_click_for(
    db: Session,
    url: ShortenedUrl,
    *,
    referrer: str | None = None,
    user_agent: str | None = None,
    client_ip: str | None = None,
) -> None:
    """Records both the basic click count (Phase 8/9) and, per
    Interpretation C (Phase 10), a ClickEvent for advanced breakdowns. Both
    writes stay deferred to a background task — see brownfield.md for why
    this must not block the redirect response."""
    url_repository.record_click(db, url)

    ip_hash = hash_ip(client_ip)
    is_repeat = click_event_repository.has_prior_click(db, url, ip_hash)
    click_event_repository.save_click_event(
        db,
        url,
        referrer=referrer,
        user_agent=user_agent,
        device_type=classify_device(user_agent),
        browser=classify_browser(user_agent),
        ip_hash=ip_hash,
        is_repeat_visitor=is_repeat,
    )


def get_analytics(db: Session, short_code: str) -> UrlAnalyticsResponse:
    url = _get_or_raise(db, short_code)
    return UrlAnalyticsResponse(
        short_code=url.short_code,
        click_count=url.click_count,
        created_at=url.created_at,
        last_accessed_at=url.last_accessed_at,
    )


def get_advanced_analytics(db: Session, short_code: str) -> AdvancedAnalyticsResponse:
    url = _get_or_raise(db, short_code)
    events = click_event_repository.get_click_events_for_url(db, url)

    device_counts = Counter(e.device_type for e in events)
    browser_counts = Counter(e.browser for e in events)
    referrer_counts = Counter(e.referrer or "(none)" for e in events)
    repeat_count = sum(1 for e in events if e.is_repeat_visitor)

    return AdvancedAnalyticsResponse(
        short_code=url.short_code,
        total_events=len(events),
        device_breakdown=_to_breakdown(device_counts),
        browser_breakdown=_to_breakdown(browser_counts),
        referrer_breakdown=_to_breakdown(referrer_counts),
        repeat_visitor_count=repeat_count,
        repeat_visitor_rate=(repeat_count / len(events)) if events else 0.0,
        geographic_breakdown=[],
        geographic_status=GEOGRAPHIC_STATUS_NOT_AVAILABLE,
    )


def _to_breakdown(counts: Counter) -> list[BreakdownEntry]:
    return [
        BreakdownEntry(key=key, count=count)
        for key, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]


def _get_or_raise(db: Session, short_code: str) -> ShortenedUrl:
    url = url_repository.get_by_short_code(db, short_code)
    if url is None:
        raise ShortenedUrlNotFoundError(short_code)
    return url


def _get_active_or_raise(db: Session, short_code: str) -> ShortenedUrl:
    url = _get_or_raise(db, short_code)
    if url.is_expired() or url.status != "ACTIVE":
        raise ShortenedUrlExpiredError(short_code)
    return url


def _to_response(url: ShortenedUrl) -> UrlResponse:
    return UrlResponse(
        id=url.public_id,
        short_code=url.short_code,
        original_url=url.original_url,
        status=url.status,
        created_at=url.created_at,
        expires_at=url.expires_at,
    )
