from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "pluma.db")

REQUIRED_TABLES = ("documents", "sentences", "questions")


def _enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_db_engine(db_path: str | None = None) -> Engine:
    if db_path is None:
        engine = create_engine(
            "sqlite://",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def ensure_schema(engine: Engine) -> None:
    """Fail clearly at startup if the schema has not been migrated yet."""
    existing = set(inspect(engine).get_table_names())
    missing = [table for table in REQUIRED_TABLES if table not in existing]
    if missing:
        raise RuntimeError(
            f"The database at {engine.url} is missing required tables "
            f"({', '.join(missing)}). Run `uv run alembic -c core/alembic.ini upgrade head` "
            "to apply the schema before starting the application."
        )
