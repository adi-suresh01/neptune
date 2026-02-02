from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, FileSystem
from app.core import settings as settings_module
from app.services.search import ensure_fts, index_note, search_notes


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_search_fts_basic():
    db = _make_session()
    original = settings_module.settings.search_mode
    try:
        object.__setattr__(settings_module.settings, "search_mode", "fts")
        ensure_fts(db)
        item = FileSystem(name="Alpha note", type="file", content="hello world")
        db.add(item)
        db.commit()
        db.refresh(item)
        index_note(db, item, item.content)
        db.commit()

        results = search_notes(db, "hello")
        assert len(results) == 1
        assert results[0].id == item.id
    finally:
        object.__setattr__(settings_module.settings, "search_mode", original)
        db.close()


def test_search_excludes_deleted():
    db = _make_session()
    original = settings_module.settings.search_mode
    try:
        object.__setattr__(settings_module.settings, "search_mode", "fts")
        ensure_fts(db)
        item = FileSystem(name="Beta note", type="file", content="secret")
        db.add(item)
        db.commit()
        db.refresh(item)
        item.deleted_at = item.updated_at
        db.commit()
        index_note(db, item, item.content)
        db.commit()

        results = search_notes(db, "secret")
        assert len(results) == 0
    finally:
        object.__setattr__(settings_module.settings, "search_mode", original)
        db.close()
