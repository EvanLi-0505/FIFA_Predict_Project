"""FastAPI session wiring on top of database.engine.

The engine is created once at import time from `settings.database_url`.
Swapping SQLite for MySQL is purely a `DATABASE_URL` environment variable
change (see backend/app/config.py) — nothing here is database-specific.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.app.config import settings
from database.engine import create_db_engine, create_session_factory

engine = create_db_engine(settings.database_url)
SessionFactory = create_session_factory(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yields one Session per request, always closed."""

    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
