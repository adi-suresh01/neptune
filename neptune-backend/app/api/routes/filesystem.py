from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import FileSystem
from app.schemas.file_system import (
    FileSystemItem,
    FileSystemMeta,
    FileSystemCreate,
    FileContentResponse,
    DeleteResponse,
)
from pydantic import BaseModel
from datetime import datetime
from app.services.note_content import store_note_content, load_note_content
from app.services.revisions import create_revision
from app.services.search import index_note
from app.services.knowledge_graph import invalidate_cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ContentUpdate(BaseModel):
    content: str
    content_checksum: str | None = None

@router.get("/", response_model=list[FileSystemMeta])
async def get_file_system(
    parent_id: int = None,
    owner_id: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Get file metadata with pagination."""
    # Only fetch files; folders are currently not supported.
    query = (
        db.query(FileSystem)
        .filter(FileSystem.type == "file")
        .filter(FileSystem.deleted_at.is_(None))
    )
    if owner_id:
        query = query.filter(FileSystem.owner_id == owner_id)
    query = query.order_by(FileSystem.updated_at.desc()).offset(offset).limit(limit)
    
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
        index_note(db, default_note, default_note.content)
        try:
            invalidate_cache()
        except Exception:
            pass
        return [FileSystemMeta(
            id=default_note.id,
            owner_id=default_note.owner_id,
            name=default_note.name,
            type=default_note.type,
            parent_id=default_note.parent_id,
            storage_backend=default_note.storage_backend,
            storage_key=default_note.storage_key,
            storage_checksum=default_note.storage_checksum,
            storage_size=default_note.storage_size,
            content_checksum=default_note.content_checksum,
        )]
    
    response_items = []
    for item in items:
        response_items.append(
            FileSystemMeta(
                id=item.id,
                owner_id=item.owner_id,
                name=item.name,
                type=item.type,
                parent_id=item.parent_id,
                storage_backend=item.storage_backend,
                storage_key=item.storage_key,
                storage_checksum=item.storage_checksum,
                storage_size=item.storage_size,
                content_checksum=item.content_checksum,
            )
        )
    return response_items

@router.post("/", response_model=FileSystemItem, status_code=201)
async def create_file_system_item(item: FileSystemCreate, db: Session = Depends(get_db)):
    """Create a new file."""
    # Enforce file-only creation.
    if item.type != "file":
        raise HTTPException(status_code=400, detail="Only file creation is supported. Folders are not allowed.")
    
    db_item = FileSystem(
        name=item.name,
        type="file",  # Force file type
        parent_id=None,  # All files are root level
        content="",  # Start with empty content
        owner_id=item.owner_id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    index_note(db, db_item, db_item.content)
    try:
        invalidate_cache()
    except Exception:
        pass
    
    return FileSystemItem(
        id=db_item.id,
        owner_id=db_item.owner_id,
        name=db_item.name,
        type=db_item.type,
        parent_id=db_item.parent_id,
        content=db_item.content,
        storage_backend=db_item.storage_backend,
        storage_key=db_item.storage_key,
        storage_checksum=db_item.storage_checksum,
        storage_size=db_item.storage_size,
        content_checksum=db_item.content_checksum,
    )

@router.put("/{item_id}/content", response_model=FileSystemItem)
async def update_file_content(
    item_id: int, 
    data: ContentUpdate,
    db: Session = Depends(get_db)
):
    """Update file content."""
    content = data.content
        
    db_item = (
        db.query(FileSystem)
        .filter(FileSystem.id == item_id)
        .filter(FileSystem.deleted_at.is_(None))
        .first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="File not found")
    if db_item.type != "file":
        raise HTTPException(status_code=400, detail="Cannot set content for non-files")
    if data.content_checksum and db_item.content_checksum and data.content_checksum != db_item.content_checksum:
        raise HTTPException(status_code=409, detail="Content checksum mismatch")
    
    # Snapshot current content before update.
    try:
        current = load_note_content(db_item)
        if current.content is not None and current.content != content:
            create_revision(db, db_item, current.content, current.storage_checksum)
    except Exception:
        # Best-effort revisions; don't block updates.
        pass

    # Persist content via storage service.
    try:
        store_note_content(db_item, content)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.warning("Failed to store note %s content: %s", item_id, e)
        raise HTTPException(status_code=503, detail="Storage unavailable")

    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)
    index_note(db, db_item, content)
    try:
        invalidate_cache()
    except Exception:
        pass
    
    return FileSystemItem(
        id=db_item.id,
        owner_id=db_item.owner_id,
        name=db_item.name,
        type=db_item.type,
        parent_id=db_item.parent_id,
        content=db_item.content,
        storage_backend=db_item.storage_backend,
        storage_key=db_item.storage_key,
        storage_checksum=db_item.storage_checksum,
        storage_size=db_item.storage_size,
        content_checksum=db_item.content_checksum,
    )

@router.get("/{item_id}", response_model=FileSystemItem)
async def get_file_by_id(item_id: int, db: Session = Depends(get_db)):
    """Get a specific file by ID"""
    item = (
        db.query(FileSystem)
        .filter(FileSystem.id == item_id)
        .filter(FileSystem.deleted_at.is_(None))
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        result = load_note_content(item)
    except Exception as e:
        logger.warning("Failed to read note %s content: %s", item_id, e)
        raise HTTPException(status_code=503, detail="Storage unavailable")
    return FileSystemItem(
        id=item.id,
        owner_id=item.owner_id,
        name=item.name,
        type=item.type,
        parent_id=item.parent_id,
        content=result.content,
        storage_backend=result.storage_backend,
        storage_key=result.storage_key,
        storage_checksum=result.storage_checksum,
        storage_size=result.storage_size,
        content_checksum=item.content_checksum,
    )


@router.get("/{item_id}/content", response_model=FileContentResponse)
async def get_file_content(item_id: int, db: Session = Depends(get_db)):
    """Get file content only."""
    item = (
        db.query(FileSystem)
        .filter(FileSystem.id == item_id)
        .filter(FileSystem.deleted_at.is_(None))
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        result = load_note_content(item)
    except Exception as e:
        logger.warning("Failed to read note %s content: %s", item_id, e)
        raise HTTPException(status_code=503, detail="Storage unavailable")
    return FileContentResponse(
        id=item.id,
        content=result.content,
        storage_backend=result.storage_backend,
        storage_key=result.storage_key,
        storage_checksum=result.storage_checksum,
        storage_size=result.storage_size,
        content_checksum=item.content_checksum,
    )

@router.delete("/{item_id}", response_model=DeleteResponse)
async def delete_file_system_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Soft-delete a file."""
    db_item = (
        db.query(FileSystem)
        .filter(FileSystem.id == item_id)
        .filter(FileSystem.deleted_at.is_(None))
        .first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    if db_item.type != "file":
        raise HTTPException(status_code=400, detail="Only files can be deleted")

    db_item.deleted_at = datetime.utcnow()
    db.commit()
    try:
        invalidate_cache()
    except Exception:
        pass
    
    return {"success": True, "message": f"File '{db_item.name}' deleted successfully"}


@router.post("/{item_id}/restore", response_model=DeleteResponse)
async def restore_file_system_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted file."""
    db_item = db.query(FileSystem).filter(FileSystem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.deleted_at is None:
        return {"success": True, "message": f"File '{db_item.name}' is already active"}
    db_item.deleted_at = None
    db.commit()
    try:
        invalidate_cache()
    except Exception:
        pass
    return {"success": True, "message": f"File '{db_item.name}' restored successfully"}
