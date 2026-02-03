from fastapi import APIRouter
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.db.models import FileSystem
from app.services.embeddings import upsert_embedding, delete_embedding, backfill_embeddings
from app.services.knowledge_graph import start_background_generation, invalidate_cache
from app.services.note_content import load_note_content

router = APIRouter()


class NotePayload(BaseModel):
    note_id: int


@router.post("/note-upsert")
async def note_upsert(payload: NotePayload):
    db = SessionLocal()
    try:
        note = (
            db.query(FileSystem)
            .filter(FileSystem.id == payload.note_id)
            .filter(FileSystem.deleted_at.is_(None))
            .first()
        )
        if note:
            loaded = load_note_content(note)
            content = loaded.content or ""
            if content.strip():
                upsert_embedding(db, note, content)
                db.commit()
        invalidate_cache()
        start_background_generation()
        return {"ok": True}
    finally:
        db.close()


@router.post("/note-delete")
async def note_delete(payload: NotePayload):
    db = SessionLocal()
    try:
        delete_embedding(db, payload.note_id)
        db.commit()
        invalidate_cache()
        start_background_generation()
        return {"ok": True}
    finally:
        db.close()


@router.post("/graph-refresh")
async def graph_refresh():
    invalidate_cache()
    started = start_background_generation()
    return {"started": started}


@router.post("/backfill")
async def backfill(limit: int = 500):
    db = SessionLocal()
    try:
        result = backfill_embeddings(db, limit=limit)
        db.commit()
        return result
    finally:
        db.close()
