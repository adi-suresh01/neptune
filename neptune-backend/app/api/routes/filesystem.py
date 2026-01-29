from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import FileSystem
from app.schemas.file_system import FileSystemItem, FileSystemCreate, FileSystemUpdate, FileSystemListResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from app.core.settings import settings
from app.services.storage import storage_client
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
        content=db_item.content
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
    
    # Persist content immediately.
    db_item.content = content
    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)

    # Optional object storage mirroring
    if storage_client.enabled and settings.storage_mode in ("dual", "s3"):
        object_key = f"{settings.s3_prefix}notes/{item_id}.md"
        try:
            storage_client.put_object(object_key, content.encode("utf-8"), "text/markdown")
        except Exception as e:
            logger.warning("Failed to store note %s in object storage: %s", item_id, e)
            if settings.storage_mode == "s3":
                raise HTTPException(status_code=503, detail="Object storage unavailable")
    
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
    content = item.content
    if storage_client.enabled and settings.storage_mode == "s3":
        object_key = f"{settings.s3_prefix}notes/{item_id}.md"
        try:
            content = storage_client.get_object(object_key).decode("utf-8")
        except Exception as e:
            logger.warning("Failed to read note %s from object storage: %s", item_id, e)
    return FileSystemItem(
        id=item.id,
        name=item.name,
        type=item.type,
        parent_id=item.parent_id,
        content=content
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
