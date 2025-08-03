from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.db.database import engine
from app.db.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Neptune Backend API",
    description="Fast note-taking with separate knowledge graph processing",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes with /api prefix
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Neptune Backend API - Fast Note Saving!",
        "note_saving": "Instant (no AI processing)",
        "knowledge_graph": "Generated on-demand from database",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is operational"}