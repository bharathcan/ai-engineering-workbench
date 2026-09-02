import pytest

from app.core.database import SessionLocal
from app.core.exceptions import ShortCodeGenerationExhaustedError
from app.repositories import url_repository


def test_collision_is_retried_and_a_unique_code_is_eventually_used(client):
    db = SessionLocal()
    try:
        codes = iter(["AAAAAAA", "AAAAAAA", "BBBBBBB"])

        first = url_repository.create_shortened_url(
            db, "https://example.com/one", lambda: next(codes)
        )
        assert first.short_code == "AAAAAAA"

        # Next factory call collides with the existing "AAAAAAA" row, then
        # succeeds with "BBBBBBB" on retry.
        second = url_repository.create_shortened_url(
            db, "https://example.com/two", lambda: next(codes)
        )
        assert second.short_code == "BBBBBBB"
    finally:
        db.close()


def test_exhausted_retries_raises_when_every_attempt_collides(client):
    db = SessionLocal()
    try:
        url_repository.create_shortened_url(db, "https://example.com/x", lambda: "CCCCCCC")

        with pytest.raises(ShortCodeGenerationExhaustedError):
            url_repository.create_shortened_url(db, "https://example.com/y", lambda: "CCCCCCC")
    finally:
        db.close()


def test_get_by_short_code_returns_none_for_unknown(client):
    db = SessionLocal()
    try:
        assert url_repository.get_by_short_code(db, "NOPE9999") is None
    finally:
        db.close()


def test_record_click_increments_count_and_sets_timestamp(client):
    db = SessionLocal()
    try:
        url = url_repository.create_shortened_url(
            db, "https://example.com/click-test", lambda: "CLICK001"
        )
        assert url.click_count == 0
        assert url.last_accessed_at is None

        url_repository.record_click(db, url)
        assert url.click_count == 1
        assert url.last_accessed_at is not None

        url_repository.record_click(db, url)
        assert url.click_count == 2
    finally:
        db.close()
