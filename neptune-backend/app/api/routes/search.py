from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.search import search_notes

router = APIRouter()


@router.get("/")
async def search(
    q: str = Query(..., min_length=1),
    owner_id: str | None = None,
    limit: int | None = None,
    db: Session = Depends(get_db),
):
    results = search_notes(db=db, query=q, owner_id=owner_id, limit=limit)
    return {
        "query": q,
        "count": len(results),
        "results": [
            {
                "id": item.id,
                "name": item.name,
                "content_preview": item.content_preview,
                "score": item.score,
                "updated_at": item.updated_at,
            }
            for item in results
        ],
    }
