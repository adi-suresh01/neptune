from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import settings as settings_module
from app.db.models import Base, FileSystem, NoteRevision
from app.services.revisions import create_revision


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_revision_pruning():
    db = _make_session()
    original = settings_module.settings.max_note_revisions
    try:
        object.__setattr__(settings_module.settings, "max_note_revisions", 2)
        item = FileSystem(name="Note", type="file", content="v1")
        db.add(item)
        db.commit()
        db.refresh(item)

        create_revision(db, item, "v1", "a")
        db.commit()
        create_revision(db, item, "v2", "b")
        db.commit()
        create_revision(db, item, "v3", "c")
        db.commit()

        count = db.query(NoteRevision).filter(NoteRevision.file_id == item.id).count()
        assert count == 2
    finally:
        object.__setattr__(settings_module.settings, "max_note_revisions", original)
        db.close()
