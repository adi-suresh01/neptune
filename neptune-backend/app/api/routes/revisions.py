from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.database import get_db
from app.db.models import NoteRevision

router = APIRouter()


@router.get("/{file_id}")
async def list_revisions(
    file_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    limit = min(limit, settings.max_note_revisions or limit)
    revisions = (
        db.query(NoteRevision)
        .filter(NoteRevision.file_id == file_id)
        .order_by(NoteRevision.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "file_id": file_id,
        "count": len(revisions),
        "revisions": [
            {
                "id": rev.id,
                "content": rev.content,
                "content_checksum": rev.content_checksum,
                "created_at": rev.created_at.isoformat() if rev.created_at else None,
            }
            for rev in revisions
        ],
    }
