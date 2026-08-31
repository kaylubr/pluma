from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from core.db.session import create_db_engine

_engine = None
_session_factory: sessionmaker | None = None


def _get_session_factory() -> sessionmaker:
    global _engine, _session_factory
    if _session_factory is None:
        _engine = create_db_engine("pluma.db")
        _session_factory = sessionmaker(bind=_engine)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
