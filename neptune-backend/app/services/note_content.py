import hashlib
from dataclasses import dataclass
from typing import Optional

from app.core.settings import settings
from app.db.models import FileSystem
from app.services.storage import storage_client


@dataclass(frozen=True)
class ContentResult:
    content: Optional[str]
    storage_backend: Optional[str]
    storage_key: Optional[str]
    storage_checksum: Optional[str]
    storage_size: Optional[int]


def _object_key_for_note(note_id: int) -> str:
    return f"{settings.s3_prefix}notes/{note_id}.md"


def _checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def store_note_content(item: FileSystem, content: str) -> ContentResult:
    data = content.encode("utf-8")
    if len(data) > settings.max_note_bytes:
        raise ValueError("Note content exceeds size limit")
    checksum = _checksum(data)
    size = len(data)

    if settings.storage_mode == "db":
        item.content = content
        item.storage_backend = "db"
        item.storage_key = None
        item.storage_checksum = checksum
        item.storage_size = size
        return ContentResult(content, "db", None, checksum, size)

    if not storage_client.enabled:
        item.content = content
        item.storage_backend = "db"
        item.storage_key = None
        item.storage_checksum = checksum
        item.storage_size = size
        return ContentResult(content, "db", None, checksum, size)

    object_key = _object_key_for_note(item.id)
    storage_client.put_object(object_key, data, "text/markdown")

    if settings.storage_mode == "dual":
        item.content = content
        item.storage_backend = "s3+db"
    else:
        item.content = None
        item.storage_backend = "s3"

    item.storage_key = object_key
    item.storage_checksum = checksum
    item.storage_size = size

    return ContentResult(item.content, item.storage_backend, object_key, checksum, size)


def load_note_content(item: FileSystem) -> ContentResult:
    if settings.storage_mode == "db" or not storage_client.enabled:
        data = item.content.encode("utf-8") if item.content else b""
        checksum = _checksum(data) if data else item.storage_checksum
        size = len(data) if data else item.storage_size
        return ContentResult(item.content, "db", None, checksum, size)

    object_key = item.storage_key or _object_key_for_note(item.id)
    data = storage_client.get_object(object_key)
    content = data.decode("utf-8")

    return ContentResult(
        content=content if settings.storage_mode != "dual" else content,
        storage_backend=item.storage_backend or "s3",
        storage_key=object_key,
        storage_checksum=_checksum(data),
        storage_size=len(data),
    )
