from typing import Dict, List, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import os
import threading
import logging

from app.services.llm_service import extract_topics_from_notes
from app.services.visualize_topics import create_topic_graph, graph_to_frontend_format
from app.db.models import FileSystem
from app.db.database import SessionLocal
from app.core.settings import settings

logger = logging.getLogger(__name__)
# Cache for the latest graph data
latest_graph_data = None
generation_status = {
    "is_generating": False,
    "progress": "idle",
    "started_at": None,
    "finished_at": None,
    "last_error": None,
}
generation_lock = threading.Lock()

# Caching configuration
cache_file = settings.kg_cache_path
cache_duration = timedelta(minutes=settings.kg_cache_ttl_minutes)

def get_cached_graph_data() -> Dict:
    """Get cached graph data from file if valid, otherwise return empty"""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < cache_duration:
                print("Using cached knowledge graph from file")
                return cached_data['graph']
        
        logger.info("Cache expired or missing")
        return {"nodes": [], "links": []}
        
    except Exception as e:
        logger.warning("Cache error: %s", e)
        return {"nodes": [], "links": []}

def cache_graph_data(graph_data: Dict):
    """Cache the graph data with timestamp"""
    global latest_graph_data
    
    try:
        os.makedirs(os.path.dirname(cache_file) or ".", exist_ok=True)
        
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "graph": graph_data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        latest_graph_data = graph_data
        logger.info("Knowledge graph cached")
        
    except Exception as e:
        logger.warning("Cache save error: %s", e)

def get_latest_graph_data() -> Dict:
    """Get the latest graph data from memory or file cache"""
    global latest_graph_data
    
    if latest_graph_data is not None:
        print("Using in-memory cached knowledge graph")
        return latest_graph_data
    
    file_cached = get_cached_graph_data()
    if file_cached.get("nodes"):
        latest_graph_data = file_cached
        return file_cached
    
    return {"nodes": [], "links": []}

def get_generation_status() -> Dict:
    """Get current generation status"""
    global generation_status
    return generation_status.copy()

def generate_knowledge_graph_background():
    """Generate knowledge graph without blocking the server."""
    global generation_status
    
    generation_status["is_generating"] = True
    generation_status["progress"] = "starting"
    generation_status["started_at"] = datetime.now().isoformat()
    generation_status["finished_at"] = None
    generation_status["last_error"] = None
    
    logger.info("Generating knowledge graph in background")
    
    # Create new database session
    db = SessionLocal()
    
    try:
        generation_status["progress"] = "fetching_notes"
        
        # Get ALL notes from database
        notes = db.query(FileSystem).filter(
            FileSystem.type == "file",
            FileSystem.content.isnot(None),
            FileSystem.content != ""
        ).all()
        
        if not notes:
            logger.info("No notes found in database")
            empty_graph = {"nodes": [], "links": []}
            cache_graph_data(empty_graph)
            return
        
        # Format notes for LLM processing
        formatted_notes = []
        for note in notes:
            if note.content and len(note.content.strip()) > 10:
                formatted_notes.append({
                    "id": str(note.id), 
                    "content": note.content
                })
        
        if not formatted_notes:
            logger.info("No meaningful content found in notes")
            empty_graph = {"nodes": [], "links": []}
            cache_graph_data(empty_graph)
            return
        
        generation_status["progress"] = f"processing_{len(formatted_notes)}_notes"
        logger.info("Processing %s notes with Ollama", len(formatted_notes))
        
        # Process with Ollama (topic extraction).
        topics_data = extract_topics_from_notes(formatted_notes)
        
        if topics_data:
            generation_status["progress"] = "building_graph"
            
            # Create knowledge graph - SLOW OLLAMA CALLS HAPPEN HERE
            graph = create_topic_graph(topics_data)
            graph_data = graph_to_frontend_format(graph)
            
            # Cache the result
            cache_graph_data(graph_data)
            generation_status["progress"] = "completed"
            generation_status["finished_at"] = datetime.now().isoformat()
            logger.info("Knowledge graph generated with %s nodes", len(graph_data.get("nodes", [])))
        else:
            logger.info("No topics extracted from notes")
            empty_graph = {"nodes": [], "links": []}
            cache_graph_data(empty_graph)
    
    except Exception as e:
        logger.error("Error generating knowledge graph: %s", e)
        generation_status["progress"] = f"error: {str(e)}"
        generation_status["last_error"] = str(e)
        empty_graph = {"nodes": [], "links": []}
        cache_graph_data(empty_graph)
    
    finally:
        db.close()
        generation_status["is_generating"] = False
        if generation_status["finished_at"] is None:
            generation_status["finished_at"] = datetime.now().isoformat()
        logger.info("Graph generation completed")

def start_background_generation():
    """Start knowledge graph generation in background thread"""
    if not generation_lock.acquire(blocking=False):
        logger.info("Generation already running")
        return False
    def _run():
        try:
            generate_knowledge_graph_background()
        finally:
            generation_lock.release()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    logger.info("Knowledge graph generation started")
    return True

def invalidate_cache():
    """Clear all cached data"""
    global latest_graph_data
    latest_graph_data = None
    
    try:
        if os.path.exists(cache_file):
            os.remove(cache_file)
        logger.info("Cache invalidated")
    except Exception as e:
        logger.warning("Error invalidating cache: %s", e)
