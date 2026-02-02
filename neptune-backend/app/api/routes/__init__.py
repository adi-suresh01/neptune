from fastapi import APIRouter

# Import routers from each module
from .filesystem import router as filesystem_router
from .knowledge_graph import router as knowledge_graph_router
from .search import router as search_router
from .system import router as system_router

# Create main router
router = APIRouter()

# Include all routers
router.include_router(filesystem_router, prefix="/filesystem", tags=["filesystem"])
router.include_router(knowledge_graph_router, prefix="/knowledge-graph", tags=["knowledge-graph"])
router.include_router(search_router, prefix="/search", tags=["search"])
router.include_router(system_router, prefix="/system", tags=["system"])
