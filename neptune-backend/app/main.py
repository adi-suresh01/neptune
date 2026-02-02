from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.logging import configure_logging, request_id_ctx
from app.core.settings import settings
from app.db.database import init_db
from app.services.embeddings import start_background_backfill
import logging
import socket
import sys
from contextlib import asynccontextmanager
import uuid

# Modern FastAPI lifespan event handler (replaces deprecated on_event)
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting Neptune Backend...")
    init_db()
    start_background_backfill()
    logger.info("Neptune Backend ready!")
    
    yield
    
    # Shutdown (if needed)
    logger.info("Neptune Backend shutting down...")

# Create FastAPI app with lifespan handler
app = FastAPI(
    title="Neptune Backend API",
    description="Fast Note Saving!",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.resolved_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_ctx.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_ctx.reset(token)

# Root endpoint
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
    return {
        "status": "healthy", 
        "service": "neptune-backend",
        "message": "API is operational"
    }

# Include API routes
app.include_router(api_router, prefix="/api")

def find_free_port(start_port=8000, max_port=8100):
    """Find a free port starting from start_port"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = settings.host
    preferred_port = settings.port
    
    # Check if we're in a bundled app (desktop mode)
    if settings.app_mode == "desktop" or getattr(sys, 'frozen', False):
        logger.info("Desktop mode: Finding available port...")
        # In desktop mode, find any available port
        port = find_free_port(preferred_port, preferred_port + 100)
        if not port:
            logger.error("No available ports found!")
            sys.exit(1)
        
        if port != preferred_port:
            logger.warning("Port %s in use, using port %s instead", preferred_port, port)
    else:
        # In development mode, use the configured port
        port = preferred_port
        logger.info("Development mode: Using configured port")
    
    logger.info("Starting server at http://%s:%s", host, port)
    uvicorn.run(app, host=host, port=port)
