from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models import FileSystem, NoteRevision


def create_revision(db: Session, item: FileSystem, content: str, checksum: str | None) -> None:
    revision = NoteRevision(
        file_id=item.id,
        content=content,
        content_checksum=checksum,
    )
    db.add(revision)
    prune_revisions(db, item.id)


def prune_revisions(db: Session, file_id: int) -> None:
    if settings.max_note_revisions <= 0:
        return
    revisions = (
        db.query(NoteRevision)
        .filter(NoteRevision.file_id == file_id)
        .order_by(NoteRevision.created_at.desc())
        .all()
    )
    if len(revisions) <= settings.max_note_revisions:
        return
    for rev in revisions[settings.max_note_revisions :]:
        db.delete(rev)
