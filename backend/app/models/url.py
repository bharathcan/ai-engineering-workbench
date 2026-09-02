from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ShortenedUrl(Base):
    __tablename__ = "shortened_urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    # Unique + indexed: every redirect does an equality lookup on this
    # column, and uniqueness is what the collision-retry logic in
    # app.repositories.url_repository relies on (a DB-level IntegrityError
    # is the actual collision signal, not a pre-check — see ADR-002).
    short_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Explicit lifecycle state, independent of expires_at: ACTIVE | DISABLED.
    # A URL can be manually disabled before its expiry (or with no expiry
    # set at all) — expiry and disablement are two different reasons a
    # redirect can stop working, so they're two different fields.
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")

    # Minimum analytics per REQUIREMENTS.md URL-FR-005: click count + a
    # timestamp. Kept on the row itself rather than a separate per-click
    # events table — no infrastructure or real traffic volume in this
    # environment justifies that complexity yet (AMB-001 is still
    # unresolved); see ADR-004.
    click_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    click_events: Mapped[list["ClickEvent"]] = relationship(
        back_populates="url", order_by="ClickEvent.occurred_at"
    )

    @property
    def public_id(self) -> str:
        return f"URL-{self.id:03d}"

    def is_expired(self, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        current = now or _utcnow()
        expires = self.expires_at
        # SQLite does not reliably round-trip timezone-aware datetimes — a
        # value read back from the DB can come back naive even though it
        # was written as aware. expires_at may also arrive from a client in
        # any offset (not necessarily UTC), so this converts to UTC first
        # and only then drops the (by-then-redundant) tzinfo, rather than
        # stripping an arbitrary offset's label and silently misreading it
        # as UTC.
        if current.tzinfo is not None:
            current = current.astimezone(timezone.utc).replace(tzinfo=None)
        if expires.tzinfo is not None:
            expires = expires.astimezone(timezone.utc).replace(tzinfo=None)
        return current >= expires


class ClickEvent(Base):
    """Per-click record for Advanced User Analytics — see
    docs/adr/ADR-005-advanced-analytics-privacy.md. This table was
    explicitly NOT built in Phase 8 (ADR-004) for lack of justification;
    the engineer's choice of Interpretation C for the Phase 10 ambiguous
    scenario is that justification, made explicitly, not assumed by AI.

    Deliberately does NOT store: raw IP address (hashed instead — see
    ADR-005), or geographic location (no GeoIP data source exists in this
    environment; NOT fabricated — see the same ADR).
    """

    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url_id: Mapped[int] = mapped_column(ForeignKey("shortened_urls.id"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    referrer: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    device_type: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    browser: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")

    # SHA-256 of the client IP + a process-local salt — never the raw IP.
    # Enough to derive "is this the same visitor as before" without
    # persisting an address that directly identifies someone. See ADR-005.
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_repeat_visitor: Mapped[bool] = mapped_column(nullable=False, default=False)

    url: Mapped["ShortenedUrl"] = relationship(back_populates="click_events")

    @property
    def public_id(self) -> str:
        return f"CLICK-{self.id:05d}"
