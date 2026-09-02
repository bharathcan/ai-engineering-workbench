from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# PostgreSQL is the proposed production database (see ARCHITECTURE.md). SQLite
# is used as the zero-dependency default so the application keeps the
# "runs with no external services" property established in Phase 2 — set
# DATABASE_URL to a postgresql+psycopg:// URL to use Postgres instead; no
# code change is required since SQLAlchemy abstracts the dialect.
DATABASE_URL = settings.database_url or "sqlite:///./workbench.db"

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
