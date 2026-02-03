from fastapi import FastAPI

from app.api.routes.indexer import router as indexer_router
from app.core.logging import configure_logging
from app.db.database import init_db

configure_logging()

app = FastAPI(
    title="Neptune Indexer",
    description="Background indexing and graph generation service",
    version="1.0.0",
)

init_db()

app.include_router(indexer_router, prefix="/indexer")
