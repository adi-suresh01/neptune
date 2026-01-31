from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class FileSystemItem(BaseModel):
    id: int
    owner_id: Optional[str] = None
    name: str
    type: str  # Type can be 'file' or 'folder'
    parent_id: Optional[int] = None  # ID of the parent folder, if applicable
    content: Optional[str] = None  # Only for files, not folders
    storage_backend: Optional[str] = None
    storage_key: Optional[str] = None
    storage_checksum: Optional[str] = None
    storage_size: Optional[int] = None
    class Config:
        from_attributes = True

class FileSystemMeta(BaseModel):
    id: int
    owner_id: Optional[str] = None
    name: str
    type: str
    parent_id: Optional[int] = None
    storage_backend: Optional[str] = None
    storage_key: Optional[str] = None
    storage_checksum: Optional[str] = None
    storage_size: Optional[int] = None
    class Config:
        from_attributes = True

class FileSystemCreate(BaseModel):
    name: str
    type: str  # Type can be 'file' or 'folder'
    parent_id: Optional[int] = None  # ID of the parent folder, if applicable
    owner_id: Optional[str] = None

class FileSystemUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None  # Type can be 'file' or 'folder'
    parent_id: Optional[int] = None  # ID of the parent folder, if applicable

class FileSystemResponse(BaseModel):
    item: FileSystemItem

class FileSystemListResponse(BaseModel):
    items: List[FileSystemItem]

class FileContentResponse(BaseModel):
    id: int
    content: Optional[str] = None
    storage_backend: Optional[str] = None
    storage_key: Optional[str] = None
    storage_checksum: Optional[str] = None
    storage_size: Optional[int] = None

# Add the missing folder-specific schemas
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class FolderResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None

class DeleteResponse(BaseModel):
    success: bool
    message: str
