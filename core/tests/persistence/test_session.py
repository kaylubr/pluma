from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool

from core.db.session import DEFAULT_DB_PATH, create_db_engine, ensure_schema
from core.models import Base


class TestDefaultDbPath:
    def test_is_absolute(self):
        assert Path(DEFAULT_DB_PATH).is_absolute()

    def test_resides_in_core_package(self):
        core_dir = Path(__file__).resolve().parents[2]
        assert Path(DEFAULT_DB_PATH) == core_dir / "pluma.db"


class TestCreateDbEngine:
    def test_no_path_uses_in_memory_database(self):
        engine = create_db_engine()
        assert engine.url.database is None
        assert engine.pool.__class__ is StaticPool
        engine.dispose()

    def test_path_uses_given_file(self, tmp_path):
        db = tmp_path / "store.db"
        engine = create_db_engine(str(db))
        assert engine.url.database == str(db)
        engine.dispose()


class TestEnsureSchema:
    def test_raises_with_actionable_message_on_empty_database(self):
        engine = create_db_engine()
        with pytest.raises(RuntimeError, match="upgrade head"):
            ensure_schema(engine)
        engine.dispose()

    def test_passes_when_schema_exists(self):
        engine = create_db_engine()
        Base.metadata.create_all(engine)
        ensure_schema(engine)
        engine.dispose()
