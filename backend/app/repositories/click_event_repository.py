from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.models.url import ClickEvent, ShortenedUrl


def has_prior_click(db: Session, url: ShortenedUrl, ip_hash: str | None) -> bool:
    if ip_hash is None:
        return False
    try:
        return (
            db.query(ClickEvent)
            .filter(ClickEvent.url_id == url.id, ClickEvent.ip_hash == ip_hash)
            .first()
            is not None
        )
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to check prior click history.") from exc


def save_click_event(
    db: Session,
    url: ShortenedUrl,
    *,
    referrer: str | None,
    user_agent: str | None,
    device_type: str,
    browser: str,
    ip_hash: str | None,
    is_repeat_visitor: bool,
) -> ClickEvent:
    try:
        event = ClickEvent(
            url_id=url.id,
            referrer=referrer,
            user_agent=user_agent,
            device_type=device_type,
            browser=browser,
            ip_hash=ip_hash,
            is_repeat_visitor=is_repeat_visitor,
        )
        db.add(event)
        db.commit()
        return event
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to save click event.") from exc


def get_click_events_for_url(db: Session, url: ShortenedUrl) -> list[ClickEvent]:
    try:
        return (
            db.query(ClickEvent)
            .filter(ClickEvent.url_id == url.id)
            .order_by(ClickEvent.id)
            .all()
        )
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load click events.") from exc
