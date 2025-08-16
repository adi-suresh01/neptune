from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.db.database import engine
from app.db.models import Base
import uvicorn

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Neptune Backend API",
    description="Fast note-taking with separate knowledge graph processing",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "tauri://localhost"],
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

# ADD THIS BLOCK - Only runs when script is executed directly (bundled)
# Won't interfere with uvicorn app.main:app development
if __name__ == "__main__":
    print("Starting Neptune Backend (bundled mode)...")
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        log_level="info"
    )