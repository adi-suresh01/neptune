from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import FileSystem
from app.schemas.file_system import FileSystemItem, FileSystemCreate, FileSystemUpdate, FileSystemListResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from app.services.note_content import store_note_content, load_note_content
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ContentUpdate(BaseModel):
    content: str

@router.get("/", response_model=list[FileSystemItem])
async def get_file_system(parent_id: int = None, db: Session = Depends(get_db)):
    """Get all files for a note-only structure."""
    # Only fetch files; folders are currently not supported.
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
            content=default_note.content,
            storage_backend=default_note.storage_backend,
            storage_key=default_note.storage_key,
            storage_checksum=default_note.storage_checksum,
            storage_size=default_note.storage_size,
        )]
    
    return [
        FileSystemItem(
            id=item.id,
            name=item.name,
            type=item.type,
            parent_id=item.parent_id,
            content=item.content,
            storage_backend=item.storage_backend,
            storage_key=item.storage_key,
            storage_checksum=item.storage_checksum,
            storage_size=item.storage_size,
        ) for item in items
    ]

@router.post("/", response_model=FileSystemItem)
async def create_file_system_item(item: FileSystemCreate, db: Session = Depends(get_db)):
    """Create a new file."""
    # Enforce file-only creation.
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
        content=db_item.content,
        storage_backend=db_item.storage_backend,
        storage_key=db_item.storage_key,
        storage_checksum=db_item.storage_checksum,
        storage_size=db_item.storage_size,
    )

@router.put("/{item_id}/content", response_model=FileSystemItem)
async def update_file_content(
    item_id: int, 
    data: dict, 
    db: Session = Depends(get_db)
):
    """Update file content."""
    content = data.get("content")
    if content is None:
        raise HTTPException(status_code=400, detail="Content field is required")
        
    db_item = db.query(FileSystem).filter(FileSystem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="File not found")
    if db_item.type != "file":
        raise HTTPException(status_code=400, detail="Cannot set content for non-files")
    
    # Persist content via storage service.
    try:
        store_note_content(db_item, content)
    except Exception as e:
        logger.warning("Failed to store note %s content: %s", item_id, e)
        raise HTTPException(status_code=503, detail="Storage unavailable")

    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)
    
    return FileSystemItem(
        id=db_item.id,
        name=db_item.name,
        type=db_item.type,
        parent_id=db_item.parent_id,
        content=db_item.content,
        storage_backend=db_item.storage_backend,
        storage_key=db_item.storage_key,
        storage_checksum=db_item.storage_checksum,
        storage_size=db_item.storage_size,
    )

@router.get("/{item_id}", response_model=FileSystemItem)
async def get_file_by_id(item_id: int, db: Session = Depends(get_db)):
    """Get a specific file by ID"""
    item = db.query(FileSystem).filter(FileSystem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        result = load_note_content(item)
    except Exception as e:
        logger.warning("Failed to read note %s content: %s", item_id, e)
        raise HTTPException(status_code=503, detail="Storage unavailable")
    return FileSystemItem(
        id=item.id,
        name=item.name,
        type=item.type,
        parent_id=item.parent_id,
        content=result.content,
        storage_backend=result.storage_backend,
        storage_key=result.storage_key,
        storage_checksum=result.storage_checksum,
        storage_size=result.storage_size,
    )

@router.delete("/{item_id}", response_model=Dict[str, Any])
async def delete_file_system_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Delete a file."""
    # Find the item in the database
    db_item = db.query(FileSystem).filter(FileSystem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Only allow file deletion since folders are not supported.
    if db_item.type != "file":
        raise HTTPException(status_code=400, detail="Only files can be deleted")
    
    # Delete the item instantly
    db.delete(db_item)
    db.commit()
    
    return {"success": True, "message": f"File '{db_item.name}' deleted successfully"}
