from fastapi import APIRouter
from sqlalchemy import text
from app.db.database import engine, SessionLocal
from app.db.models import FileSystem
from app.services.knowledge_graph import get_generation_status, get_latest_graph_data
from app.services.llm_service import llm_service
from app.core.settings import settings
from app.services.storage import storage_client

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


@router.get("/status")
async def system_status():
    storage_status = storage_client.healthcheck()
    return {
        "environment": settings.environment,
        "app_mode": settings.app_mode,
        "storage_mode": settings.storage_mode,
        "host": settings.host,
        "port": settings.port,
        "cors": {
            "allow_all": settings.cors_allow_all,
            "origins": settings.resolved_cors_origins(),
        },
        "llm": {
            "endpoint": settings.ollama_url,
            "model": settings.ollama_model,
        },
        "storage": {
            "enabled": storage_status.enabled,
            "ok": storage_status.ok,
            "endpoint": settings.s3_endpoint,
            "bucket": settings.s3_bucket,
            "prefix": settings.s3_prefix,
            "error": storage_status.error,
        },
    }


@router.get("/metrics")
async def metrics():
    db = SessionLocal()
    try:
        file_count = db.query(FileSystem).filter(FileSystem.type == "file").count()
    finally:
        db.close()

    graph_data = get_latest_graph_data()
    status = get_generation_status()

    return {
        "files": {"count": file_count},
        "knowledge_graph": {
            "cached": bool(graph_data.get("nodes")),
            "node_count": len(graph_data.get("nodes", [])),
            "link_count": len(graph_data.get("links", [])),
            "generation_status": status,
        },
    }
