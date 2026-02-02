from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.embeddings import backfill_embeddings, related_notes

router = APIRouter()


@router.post("/backfill")
async def backfill(limit: int = Query(default=200, ge=1, le=2000), db: Session = Depends(get_db)):
    result = backfill_embeddings(db, limit=limit)
    db.commit()
    return result


@router.get("/related/{file_id}")
async def related(file_id: int, top_k: int = Query(default=8, ge=1, le=50), db: Session = Depends(get_db)):
    results = related_notes(db, file_id=file_id, top_k=top_k)
    return {"file_id": file_id, "count": len(results), "results": results}
