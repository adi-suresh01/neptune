from fastapi import APIRouter

# Import routers from each module
from .filesystem import router as filesystem_router
from .folders import router as folders_router
from .knowledge_graph import router as knowledge_graph_router

# Create main router
router = APIRouter()

# Include all routers
router.include_router(filesystem_router, prefix="/filesystem", tags=["filesystem"])
router.include_router(folders_router, prefix="/folders", tags=["folders"])
router.include_router(knowledge_graph_router, prefix="/knowledge-graph", tags=["knowledge-graph"])