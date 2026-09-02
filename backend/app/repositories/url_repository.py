from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError, ShortCodeGenerationExhaustedError
from app.models.url import ShortenedUrl

MAX_COLLISION_RETRIES = 5


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_shortened_url(
    db: Session,
    original_url: str,
    short_code_factory: Callable[[], str],
    expires_at: datetime | None = None,
) -> ShortenedUrl:
    """Collision handling: the short code is not checked for uniqueness
    before inserting — under concurrent creation, a pre-check-then-insert
    has a race window another request could win between the check and the
    write. Instead this relies on the DB's own unique constraint as the
    single source of truth: attempt the insert, and on IntegrityError
    (constraint violation), roll back and generate a fresh code, up to
    MAX_COLLISION_RETRIES times. See docs/adr/ADR-002-short-code-strategy.md.
    """
    for _attempt in range(MAX_COLLISION_RETRIES):
        code = short_code_factory()
        try:
            url = ShortenedUrl(
                original_url=original_url,
                short_code=code,
                expires_at=expires_at,
                status="ACTIVE",
            )
            db.add(url)
            db.commit()
            db.refresh(url)
            return url
        except IntegrityError:
            db.rollback()
            continue
        except SQLAlchemyError as exc:
            db.rollback()
            raise PersistenceError("Failed to create shortened URL.") from exc

    raise ShortCodeGenerationExhaustedError(MAX_COLLISION_RETRIES)


def get_by_short_code(db: Session, short_code: str) -> ShortenedUrl | None:
    try:
        return db.query(ShortenedUrl).filter(ShortenedUrl.short_code == short_code).first()
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load shortened URL.") from exc


def record_click(db: Session, url: ShortenedUrl) -> None:
    """Increments click_count via an atomic SQL-level UPDATE
    (`click_count = click_count + 1`, evaluated by the database against the
    row's current value at execution time) rather than Python-side
    read-modify-write (`url.click_count += 1` then UPDATE). The latter lost
    updates under Phase 9's background-task deferral: two overlapping
    background tasks for the same short_code could both read the same
    starting count before either wrote back, so one increment was
    silently dropped — caught by a real before/after click-count check
    (500 redirects, 498 recorded), not anticipated in advance. See
    docs/scenarios/brownfield.md."""
    try:
        db.execute(
            update(ShortenedUrl)
            .where(ShortenedUrl.id == url.id)
            .values(click_count=ShortenedUrl.click_count + 1, last_accessed_at=_utcnow())
        )
        db.commit()
        # No db.refresh(url) here — nothing reads `url` again after this
        # background task completes, and refreshing it turned out to be
        # more than unnecessary: it actively failed
        # (InvalidRequestError: "Instance is not persistent within this
        # Session") when run as a background task, caught by actually
        # running the tests. See docs/scenarios/brownfield.md.
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to record click.") from exc
