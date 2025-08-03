from typing import Dict, List, Any
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, APIRouter, Depends
from datetime import datetime, timedelta
import json
import os

from app.services.llm_service import extract_topics_from_notes
from app.services.visualize_topics import create_topic_graph, graph_to_frontend_format
from app.db.models import FileSystem
from app.db.database import get_db, SessionLocal

# Cache for the latest graph data
latest_graph_data = None

# Caching configuration
cache_file = "outputs/kg_cache.json"
cache_duration = timedelta(minutes=10)

def get_cached_graph_data() -> Dict:
    """Get cached graph data from file if valid, otherwise return empty"""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < cache_duration:
                print("✅ Using cached knowledge graph from file")
                return cached_data['graph']
        
        print("🔄 Cache expired or missing")
        return {"nodes": [], "links": []}
        
    except Exception as e:
        print(f"❌ Cache error: {e}")
        return {"nodes": [], "links": []}

def cache_graph_data(graph_data: Dict):
    """Cache the graph data with timestamp"""
    global latest_graph_data
    
    try:
        os.makedirs("outputs", exist_ok=True)
        
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "graph": graph_data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        latest_graph_data = graph_data
        print("✅ Knowledge graph cached (file + memory)")
        
    except Exception as e:
        print(f"❌ Cache save error: {e}")

def get_latest_graph_data() -> Dict:
    """Get the latest graph data from memory or file cache"""
    global latest_graph_data
    
    if latest_graph_data is not None:
        print("✅ Using in-memory cached knowledge graph")
        return latest_graph_data
    
    file_cached = get_cached_graph_data()
    if file_cached.get("nodes"):
        latest_graph_data = file_cached
        return file_cached
    
    return {"nodes": [], "links": []}

def generate_knowledge_graph_from_db() -> Dict:
    """FIXED: Simple sync version without event loop conflicts"""
    print("🔄 Generating knowledge graph from database...")
    
    # Create new database session
    db = SessionLocal()
    
    try:
        # Get ALL notes from database
        notes = db.query(FileSystem).filter(
            FileSystem.type == "file",
            FileSystem.content.isnot(None),
            FileSystem.content != ""
        ).all()
        
        if not notes:
            print("❌ No notes found in database")
            empty_graph = {"nodes": [], "links": []}
            cache_graph_data(empty_graph)
            return empty_graph
        
        # Format notes for LLM processing
        formatted_notes = []
        for note in notes:
            if note.content and len(note.content.strip()) > 10:
                formatted_notes.append({
                    "id": str(note.id), 
                    "content": note.content
                })
        
        if not formatted_notes:
            print("❌ No meaningful content found in notes")
            empty_graph = {"nodes": [], "links": []}
            cache_graph_data(empty_graph)
            return empty_graph
        
        print(f"🔄 Processing {len(formatted_notes)} notes with Ollama...")
        
        # Process with Ollama (topic extraction)
        topics_data = extract_topics_from_notes(formatted_notes)
        
        if topics_data:
            # Create knowledge graph (NOW SYNC - no event loop conflicts)
            graph = create_topic_graph(topics_data)
            graph_data = graph_to_frontend_format(graph)
            
            # Cache the result
            cache_graph_data(graph_data)
            print(f"✅ Knowledge graph generated with {len(graph_data.get('nodes', []))} nodes")
            return graph_data
        else:
            print("❌ No topics extracted from notes")
            empty_graph = {"nodes": [], "links": []}
            cache_graph_data(empty_graph)
            return empty_graph
    
    except Exception as e:
        print(f"❌ Error generating knowledge graph: {e}")
        empty_graph = {"nodes": [], "links": []}
        cache_graph_data(empty_graph)
        return empty_graph
    
    finally:
        db.close()

def invalidate_cache():
    """Clear all cached data"""
    global latest_graph_data
    latest_graph_data = None
    
    try:
        if os.path.exists(cache_file):
            os.remove(cache_file)
        print("✅ Cache invalidated")
    except Exception as e:
        print(f"❌ Error invalidating cache: {e}")

# API Router
router = APIRouter()

@router.get("/", response_model=Dict)
async def get_knowledge_graph():
    """Get knowledge graph data (cached for speed) - NON-BLOCKING"""
    # Return cached data immediately (this is always fast)
    graph_data = get_latest_graph_data()
    
    if not graph_data.get("nodes"):
        return {
            "nodes": [], 
            "links": [], 
            "message": "No knowledge graph available. Click 'Refresh' to generate from your notes."
        }
    
    return graph_data

@router.post("/refresh", response_model=Dict)
async def refresh_knowledge_graph():
    """FIXED: Simple sync call without async complications"""
    try:
        print("🔄 Manual knowledge graph refresh requested...")
        invalidate_cache()
        
        # Use simple sync version (no event loop conflicts)
        graph_data = generate_knowledge_graph_from_db()
        
        # Add metadata
        graph_data["cached"] = False
        graph_data["fresh"] = True
        graph_data["generated_at"] = "just_now"
        
        return graph_data
        
    except Exception as e:
        print(f"❌ Error refreshing knowledge graph: {e}")
        # Return error response instead of raising exception
        return {
            "nodes": [], 
            "links": [], 
            "error": str(e),
            "message": "Failed to generate knowledge graph"
        }

@router.post("/invalidate")
async def invalidate_knowledge_graph_cache():
    """Clear the knowledge graph cache"""
    invalidate_cache()
    return {"message": "Cache invalidated"}