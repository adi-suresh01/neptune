from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.settings import settings
from app.db.database import init_db
import socket
import sys
from contextlib import asynccontextmanager

# Modern FastAPI lifespan event handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    print("🚀 Starting Neptune Backend...")
    init_db()
    print("✅ Neptune Backend ready!")
    
    yield
    
    # Shutdown (if needed)
    print("👋 Neptune Backend shutting down...")

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

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Neptune Backend API - Fast Note Saving!",
        "note_saving": "Instant (no AI processing)",
        "knowledge_graph": "Generated on-demand from database",
        "status": "healthy"
    }

# 👈 FIX: Make sure health endpoint returns the expected format
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
    if getattr(sys, 'frozen', False):
        print("📱 Desktop app mode: Finding available port...")
        # In desktop mode, find any available port
        port = find_free_port(preferred_port, preferred_port + 100)
        if not port:
            print("❌ No available ports found!")
            sys.exit(1)
        
        if port != preferred_port:
            print(f"⚠️  Port {preferred_port} in use, using port {port} instead")
    else:
        # In development mode, use the configured port
        port = preferred_port
        print("🔧 Development mode: Using configured port")
    
    print(f"🌐 Starting server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
