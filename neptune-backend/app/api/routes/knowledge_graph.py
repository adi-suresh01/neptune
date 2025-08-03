from fastapi import APIRouter, HTTPException
from typing import Dict

router = APIRouter()

@router.get("/")
async def get_knowledge_graph():
    """Get knowledge graph data - always try cached first"""
    try:
        from app.services.knowledge_graph import get_latest_graph_data
        
        # Always return cached data if available (instant response)
        graph_data = get_latest_graph_data()
        
        # Return whatever we have (cached or empty)
        if graph_data.get("nodes"):
            return graph_data
        else:
            # Return empty with metadata
            return {
                "nodes": [], 
                "links": [], 
                "message": "No cached knowledge graph. Generate one from your notes.",
                "cached": False
            }
        
    except Exception as e:
        print(f"Error getting knowledge graph: {e}")
        return {
            "nodes": [], 
            "links": [], 
            "error": str(e),
            "cached": False
        }

@router.post("/refresh")
async def refresh_knowledge_graph():
    """FIXED: Use sync version to avoid event loop conflicts"""
    try:
        from app.services.knowledge_graph import generate_knowledge_graph_from_db, invalidate_cache
        
        print("🔄 Force generating fresh knowledge graph...")
        invalidate_cache()
        
        # Use sync version (NO async complications)
        graph_data = generate_knowledge_graph_from_db()
        
        # Add metadata
        if not graph_data.get("error"):
            graph_data["cached"] = False
            graph_data["fresh"] = True
            graph_data["generated_at"] = "just_now"
        
        return graph_data
        
    except Exception as e:
        print(f"Error refreshing knowledge graph: {e}")
        return {
            "nodes": [], 
            "links": [], 
            "error": str(e),
            "message": "Failed to generate knowledge graph"
        }

@router.post("/invalidate")
async def invalidate_knowledge_graph_cache():
    """Clear all knowledge graph caches"""
    try:
        from app.services.knowledge_graph import invalidate_cache
        
        invalidate_cache()
        return {"message": "All caches invalidated"}
        
    except Exception as e:
        print(f"Error invalidating cache: {e}")
        return {"error": str(e)}

@router.get("/status")
async def get_cache_status():
    """Get cache status information"""
    try:
        from app.services.knowledge_graph import get_latest_graph_data, get_cached_graph_data
        
        memory_cache = get_latest_graph_data()
        file_cache = get_cached_graph_data()
        
        return {
            "has_memory_cache": bool(memory_cache.get("nodes")),
            "has_file_cache": bool(file_cache.get("nodes")),
            "memory_cache_size": len(memory_cache.get("nodes", [])),
            "file_cache_size": len(file_cache.get("nodes", [])),
        }
        
    except Exception as e:
        return {"error": str(e)}