from fastapi import APIRouter, HTTPException
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_knowledge_graph():
    """Get cached knowledge graph data."""
    try:
        from app.services.knowledge_graph import get_latest_graph_data, get_generation_status
        
        # Return cached data immediately without blocking.
        graph_data = get_latest_graph_data()
        status = get_generation_status()
        
        # Return whatever we have (cached or empty)
        if graph_data.get("nodes"):
            return {
                **graph_data,
                "status": status,
                "cached": True
            }
        else:
            # Return empty with status
            return {
                "nodes": [], 
                "links": [], 
                "message": "No cached knowledge graph. Click 'Generate' to create one.",
                "status": status,
                "cached": False
            }
        
    except Exception as e:
        logger.error("Error getting knowledge graph: %s", e)
        return {
            "nodes": [], 
            "links": [], 
            "error": str(e),
            "cached": False
        }

@router.post("/refresh")
async def refresh_knowledge_graph():
    """Start knowledge graph generation in the background."""
    try:
        from app.services.knowledge_graph import start_background_generation, invalidate_cache, get_generation_status
        
        status = get_generation_status()
        
        # Check if already generating
        if status["is_generating"]:
            return {
                "message": "Knowledge graph generation already in progress",
                "status": status,
                "generating": True
            }
        
        logger.info("Starting background knowledge graph generation")
        invalidate_cache()
        
        # Start background generation without blocking.
        started = start_background_generation()
        if not started:
            return {
                "message": "Knowledge graph generation already in progress",
                "status": get_generation_status(),
                "generating": True
            }
        
        return {
            "message": "Knowledge graph generation started in background",
            "status": {"is_generating": True, "progress": "starting"},
            "generating": True,
            "note": "Check /api/knowledge-graph/status for progress"
        }
        
    except Exception as e:
        logger.error("Error starting knowledge graph generation: %s", e)
        return {
            "error": str(e),
            "message": "Failed to start knowledge graph generation"
        }

@router.get("/status")
async def get_generation_status():
    """Get knowledge graph generation status."""
    try:
        from app.services.knowledge_graph import get_generation_status, get_latest_graph_data
        
        status = get_generation_status()
        graph_data = get_latest_graph_data()
        
        return {
            "generation_status": status,
            "has_cached_graph": bool(graph_data.get("nodes")),
            "node_count": len(graph_data.get("nodes", [])),
            "link_count": len(graph_data.get("links", [])),
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.post("/invalidate")
async def invalidate_knowledge_graph_cache():
    """Clear all knowledge graph caches."""
    try:
        from app.services.knowledge_graph import invalidate_cache
        
        invalidate_cache()
        return {"message": "All caches invalidated"}
        
    except Exception as e:
        logger.error("Error invalidating cache: %s", e)
        return {"error": str(e)}
