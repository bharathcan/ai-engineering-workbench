import ipaddress
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator

MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = {"http", "https"}
# This service only stores and redirects — it never fetches a submitted URL
# server-side — so classic SSRF (the server itself being tricked into
# calling an internal endpoint) does not directly apply. This blocklist
# instead prevents the *redirect* target from pointing at obviously
# internal/private infrastructure, so the shortener can't be used to
# obscure links into a network an attacker shouldn't be pointing others at.
# See docs/validation/PHASE-8-SECURITY-REVIEW.md.
_BLOCKED_HOSTNAMES = {"localhost"}


class CreateUrlRequest(BaseModel):
    original_url: str
    expires_at: datetime | None = None

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("original_url must not be empty.")
        if len(value) > MAX_URL_LENGTH:
            raise ValueError(f"original_url must not exceed {MAX_URL_LENGTH} characters.")

        parsed = urlparse(value)
        if parsed.scheme not in ALLOWED_SCHEMES:
            raise ValueError(
                f"original_url must use one of {sorted(ALLOWED_SCHEMES)}, got {parsed.scheme!r}."
            )
        if not parsed.hostname:
            raise ValueError("original_url must include a host.")

        hostname = parsed.hostname.lower()
        if hostname in _BLOCKED_HOSTNAMES:
            raise ValueError("original_url host is not allowed.")

        try:
            ip = ipaddress.ip_address(hostname)
        except ValueError:
            ip = None
        is_internal = ip is not None and (
            ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
        )
        if is_internal:
            raise ValueError("original_url must not target a private or internal address.")

        return value


class UrlResponse(BaseModel):
    id: str
    short_code: str
    original_url: str
    status: str
    created_at: datetime
    expires_at: datetime | None


class UrlAnalyticsResponse(BaseModel):
    short_code: str
    click_count: int
    created_at: datetime
    last_accessed_at: datetime | None


class BreakdownEntry(BaseModel):
    key: str
    count: int


class AdvancedAnalyticsResponse(BaseModel):
    """Interpretation C (Phase 10) — see
    docs/adr/ADR-005-advanced-analytics-privacy.md. geographic_breakdown is
    always empty with geographic_status explaining why: no GeoIP data
    source exists in this environment, and this is not fabricated."""

    short_code: str
    total_events: int
    device_breakdown: list[BreakdownEntry]
    browser_breakdown: list[BreakdownEntry]
    referrer_breakdown: list[BreakdownEntry]
    repeat_visitor_count: int
    repeat_visitor_rate: float
    geographic_breakdown: list[BreakdownEntry]
    geographic_status: str
