from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import FileSystem
from app.schemas.file_system import FileSystemItem, FileSystemCreate, FileSystemUpdate, FileSystemListResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

router = APIRouter()

class ContentUpdate(BaseModel):
    content: str

@router.get("/", response_model=list[FileSystemItem])
async def get_file_system(parent_id: int = None, db: Session = Depends(get_db)):
    """Get all files (NO FOLDERS) - simplified for note-only structure"""
    # SIMPLIFIED: Only get files, ignore parent_id since we don't use folders
    query = db.query(FileSystem).filter(FileSystem.type == "file")
    
    items = query.all()
    
    # Create default note if nothing exists
    if not items:
        default_note = FileSystem(
            name="My First Note",
            type="file",
            parent_id=None,
            content="Welcome to Neptune! Start writing your notes here..."
        )
        db.add(default_note)
        db.commit()
        db.refresh(default_note)
        return [FileSystemItem(
            id=default_note.id,
            name=default_note.name,
            type=default_note.type,
            parent_id=default_note.parent_id,
            content=default_note.content
        )]
    
    return [
        FileSystemItem(
            id=item.id,
            name=item.name,
            type=item.type,
            parent_id=item.parent_id,
            content=item.content
        ) for item in items
    ]

@router.post("/", response_model=FileSystemItem)
async def create_file_system_item(item: FileSystemCreate, db: Session = Depends(get_db)):
    """Create a new file ONLY - NO FOLDER SUPPORT"""
    # ENFORCE: Only allow file creation
    if item.type != "file":
        raise HTTPException(status_code=400, detail="Only file creation is supported. Folders are not allowed.")
    
    db_item = FileSystem(
        name=item.name,
        type="file",  # Force file type
        parent_id=None,  # All files are root level
        content=""  # Start with empty content
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return FileSystemItem(
        id=db_item.id,
        name=db_item.name,
        type=db_item.type,
        parent_id=db_item.parent_id,
        content=db_item.content
    )

@router.put("/{item_id}/content", response_model=FileSystemItem)
async def update_file_content(
    item_id: int, 
    data: dict, 
    db: Session = Depends(get_db)
):
    """Update file content - INSTANT SAVE, NO OLLAMA"""
    content = data.get("content")
    if content is None:
        raise HTTPException(status_code=400, detail="Content field is required")
        
    db_item = db.query(FileSystem).filter(FileSystem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="File not found")
    if db_item.type != "file":
        raise HTTPException(status_code=400, detail="Cannot set content for non-files")
    
    # INSTANT SAVE
    db_item.content = content
    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)
    
    return FileSystemItem(
        id=db_item.id,
        name=db_item.name,
        type=db_item.type,
        parent_id=db_item.parent_id,
        content=db_item.content
    )

@router.get("/{item_id}", response_model=FileSystemItem)
async def get_file_by_id(item_id: int, db: Session = Depends(get_db)):
    """Get a specific file by ID"""
    item = db.query(FileSystem).filter(FileSystem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return FileSystemItem(
        id=item.id,
        name=item.name,
        type=item.type,
        parent_id=item.parent_id,
        content=item.content
    )

@router.delete("/{item_id}", response_model=Dict[str, Any])
async def delete_file_system_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Delete a file - INSTANT, NO OLLAMA"""
    # Find the item in the database
    db_item = db.query(FileSystem).filter(FileSystem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # SIMPLIFIED: Only allow file deletion since we don't have folders
    if db_item.type != "file":
        raise HTTPException(status_code=400, detail="Only files can be deleted")
    
    # Delete the item instantly
    db.delete(db_item)
    db.commit()
    
    return {"success": True, "message": f"File '{db_item.name}' deleted successfully"}