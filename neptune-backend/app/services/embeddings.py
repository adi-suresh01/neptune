from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Dict, List

import requests
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models import FileSystem, NoteEmbedding
from app.services.vector_index_faiss import load_index, save_index

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmbeddingResult:
    vector: List[float]
    dim: int


class EmbeddingService:
    def __init__(self) -> None:
        self.session = requests.Session()

    def embed(self, text: str) -> EmbeddingResult:
        payload = {
            "model": settings.embedding_model,
            "prompt": text[: settings.embedding_max_chars],
        }
        response = self.session.post(
            f"{settings.ollama_url}/api/embeddings",
            json=payload,
            timeout=(settings.ollama_connect_timeout_seconds, settings.ollama_timeout_seconds),
        )
        response.raise_for_status()
        data = response.json()
        vector = data.get("embedding", [])
        return EmbeddingResult(vector=vector, dim=len(vector))


embedding_service = EmbeddingService()


def _get_note_embedding(db: Session, file_id: int) -> NoteEmbedding | None:
    return db.query(NoteEmbedding).filter(NoteEmbedding.file_id == file_id).first()


def upsert_embedding(db: Session, item: FileSystem, content: str) -> None:
    content = content or ""
    if not content.strip():
        delete_embedding(db, item.id)
        return
    if item.content_checksum:
        existing = _get_note_embedding(db, item.id)
        if existing and existing.content_checksum == item.content_checksum:
            return

    result = embedding_service.embed(content)
    vector_json = json.dumps(result.vector)
    existing = _get_note_embedding(db, item.id)
    if existing:
        existing.vector = vector_json
        existing.dim = result.dim
        existing.content_checksum = item.content_checksum
    else:
        db.add(
            NoteEmbedding(
                file_id=item.id,
                vector=vector_json,
                dim=result.dim,
                content_checksum=item.content_checksum,
            )
        )

    index = load_index(result.dim)
    index.upsert(item.id, result.vector)
    save_index()


def delete_embedding(db: Session, file_id: int) -> None:
    existing = _get_note_embedding(db, file_id)
    if not existing:
        return
    db.delete(existing)
    try:
        index = load_index(existing.dim)
        index.delete(file_id)
        save_index()
    except Exception as e:
        logger.warning("Failed to update vector index for delete: %s", e)


def load_embeddings_map(db: Session, note_ids: List[int]) -> Dict[int, List[float]]:
    if not note_ids:
        return {}
    embeddings = (
        db.query(NoteEmbedding)
        .filter(NoteEmbedding.file_id.in_(note_ids))
        .all()
    )
    result: Dict[int, List[float]] = {}
    for emb in embeddings:
        try:
            result[emb.file_id] = json.loads(emb.vector)
        except Exception:
            continue
    return result
