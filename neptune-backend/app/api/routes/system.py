from fastapi import APIRouter
from sqlalchemy import text
from app.db.database import engine
from app.services.llm_service import llm_service

router = APIRouter()


@router.get("/ready")
async def readiness_check():
    db_ok = False
    db_error = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    llm_status = llm_service.healthcheck()

    return {
        "ready": db_ok and llm_status.get("ok", False),
        "database": {"ok": db_ok, "error": db_error},
        "llm": llm_status,
    }
