"""Engine/session factories for both deployment targets.

Web backend:      build_mysql_url(...) -> create_db_engine(url)
Desktop backend:  build_sqlite_url(db_path) -> create_db_engine(url)

Both paths return a plain `sqlalchemy.Engine` — every repository and
service downstream is written against that generic interface only.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base


def build_sqlite_url(db_path: str | Path) -> str:
    """Build a SQLite connection URL for the Desktop backend.

    `db_path` should live under the application's user-data directory
    (Development Prompt.md Section 9), e.g. `%APPDATA%/FIFA-Prediction/app.db`
    — never inside the read-only installation/extraction directory.
    """

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def build_mysql_url(
    *, host: str, port: int, database: str, username: str, password: str
) -> str:
    """Build a MySQL connection URL for the Web backend (uses PyMySQL)."""

    return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"


def create_db_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine.

    SQLite needs `check_same_thread=False` because FastAPI may access the
    session from a different thread than the one that created the
    connection; every other engine (MySQL) ignores this argument.
    """

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(database_url, connect_args=connect_args, future=True)


def create_all_tables(engine: Engine) -> None:
    """Create every table in `database.models` if it does not exist yet.

    Desktop uses this directly on first launch (no migration history to
    manage on a single-user portable app). Web should use Alembic
    migrations instead (added in Stage 3) once the schema needs to evolve
    without dropping data.
    """

    Base.metadata.create_all(engine)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
