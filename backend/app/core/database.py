from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# PostgreSQL is the proposed production database (see ARCHITECTURE.md). SQLite
# is used as the zero-dependency default so the application keeps the
# "runs with no external services" property established in Phase 2 — set
# DATABASE_URL to a Postgres URL to use Postgres instead.


def _normalize_database_url(raw_url: str) -> str:
    """Managed Postgres providers (e.g. Render) hand back a bare
    postgres:// or postgresql:// connection string. Plain "postgresql://"
    resolves to the psycopg2 driver by default, which isn't installed here
    (only psycopg3, per requirements.txt) — rewrite to the explicit
    postgresql+psycopg:// dialect+driver SQLAlchemy needs, without
    requiring every deployment target to hand-edit the URL it's given."""
    for prefix in ("postgres://", "postgresql://"):
        if raw_url.startswith(prefix):
            return "postgresql+psycopg://" + raw_url[len(prefix) :]
    return raw_url


DATABASE_URL = _normalize_database_url(settings.database_url or "sqlite:///./workbench.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
