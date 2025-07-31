from typing import Dict, List, Any
import asyncio
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, APIRouter, Depends
from datetime import datetime

from app.services.llm_service import extract_topics_from_notes
from app.services.visualize_topics import create_topic_graph, graph_to_frontend_format
from app.db.models import FileSystem
from app.db.database import get_db

# Cache for the latest graph data
latest_graph_data = None

async def generate_knowledge_graph(db: Session) -> Dict:
    """
    Generate knowledge graph from all notes in the database
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with nodes and links for the frontend visualization
    """
    global latest_graph_data
    
    # Fetch all file content from database
    notes = db.query(FileSystem).filter(FileSystem.type == "file").all()
    
    # Format notes for processing
    formatted_notes = [
        {
            "id": str(note.id),
            "content": note.content or ""
        }
        for note in notes
        if note.content  # Only include notes with content
    ]
    
    # Only process if we have notes with content
    if formatted_notes:
        # Extract topics
        topics_data = extract_topics_from_notes(formatted_notes)
        
        # Generate graph
        if topics_data:
            graph = create_topic_graph(topics_data)
            graph_data = graph_to_frontend_format(graph)
            
            # Update cache
            latest_graph_data = graph_data
            
            return graph_data
    
    # Return empty graph if no data
    return {"nodes": [], "links": []}

def get_cached_graph_data() -> Dict:
    """Get the latest cached knowledge graph data"""
    if latest_graph_data is None:
        return {"nodes": [], "links": []}
    return latest_graph_data

async def update_knowledge_graph_async(db: Session):
    """Update the knowledge graph in the background"""
    await generate_knowledge_graph(db)

def schedule_knowledge_graph_update(background_tasks: BackgroundTasks, db: Session):
    """Schedule a background task to update the knowledge graph"""
    background_tasks.add_task(update_knowledge_graph_async, db)

router = APIRouter()

@router.get("/", response_model=Dict)
async def get_knowledge_graph(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Get the knowledge graph data for visualization.
    This endpoint will return cached data if available,
    and trigger a refresh in the background.
    """
    # Get current cached data
    graph_data = get_cached_graph_data()
    
    # Schedule update for next time
    background_tasks.add_task(generate_knowledge_graph, db)
    
    return graph_data

@router.post("/refresh", response_model=Dict)
async def refresh_knowledge_graph(db: Session = Depends(get_db)):
    """
    Force refresh the knowledge graph and wait for the results
    """
    return await generate_knowledge_graph(db)