from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models import FileSystem


@dataclass(frozen=True)
class SearchResult:
    id: int
    name: str
    content_preview: str
    score: float | None
    updated_at: str | None


def _is_sqlite(db: Session) -> bool:
    return db.bind and db.bind.dialect.name == "sqlite"


def ensure_fts(db: Session) -> None:
    if not _is_sqlite(db):
        return
    db.execute(
        text(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS filesystem_fts
            USING fts5(name, content, file_id UNINDEXED);
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS filesystem_ai
            AFTER INSERT ON filesystem
            WHEN NEW.type = 'file' AND NEW.deleted_at IS NULL
            BEGIN
              INSERT INTO filesystem_fts(rowid, name, content, file_id)
              VALUES (NEW.id, NEW.name, COALESCE(NEW.content, ''), NEW.id);
            END;
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS filesystem_ad
            AFTER DELETE ON filesystem
            BEGIN
              DELETE FROM filesystem_fts WHERE rowid = OLD.id;
            END;
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS filesystem_au
            AFTER UPDATE ON filesystem
            BEGIN
              DELETE FROM filesystem_fts WHERE rowid = OLD.id;
              INSERT INTO filesystem_fts(rowid, name, content, file_id)
              VALUES (NEW.id, NEW.name, COALESCE(NEW.content, ''), NEW.id);
            END;
            """
        )
    )


def fts_available(db: Session) -> bool:
    if not _is_sqlite(db):
        return False
    try:
        db.execute(text("SELECT 1 FROM filesystem_fts LIMIT 1;"))
        return True
    except Exception:
        return False


def index_note(db: Session, item: FileSystem, content: str | None) -> None:
    if not _is_sqlite(db):
        return
    if not fts_available(db):
        return
    db.execute(
        text(
            """
            INSERT INTO filesystem_fts(rowid, name, content, file_id)
            VALUES (:id, :name, :content, :id)
            ON CONFLICT(rowid) DO UPDATE SET
              name = excluded.name,
              content = excluded.content;
            """
        ),
        {
            "id": item.id,
            "name": item.name or "",
            "content": content or "",
        },
    )


def _preview(text_value: str | None, limit: int = 200) -> str:
    if not text_value:
        return ""
    if len(text_value) <= limit:
        return text_value
    return text_value[:limit].rsplit(" ", 1)[0] + "…"


def search_notes(
    db: Session,
    query: str,
    owner_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[SearchResult]:
    trimmed = (query or "").strip()
    if len(trimmed) < settings.search_min_query_len:
        return []
    limit = min(limit or settings.search_max_results, settings.search_max_results)

    if _is_sqlite(db) and settings.search_mode in {"auto", "fts"} and fts_available(db):
        rows = db.execute(
            text(
                """
                SELECT file_id, bm25(filesystem_fts) AS score
                FROM filesystem_fts
                WHERE filesystem_fts MATCH :q
                ORDER BY score
                LIMIT :limit;
                """
            ),
            {"q": trimmed, "limit": limit},
        ).fetchall()
        file_ids = [row[0] for row in rows]
        score_map = {row[0]: row[1] for row in rows}
        if not file_ids:
            return []
        query_obj = (
            db.query(FileSystem)
            .filter(FileSystem.id.in_(file_ids))
            .filter(FileSystem.deleted_at.is_(None))
        )
        if owner_id:
            query_obj = query_obj.filter(FileSystem.owner_id == owner_id)
        results = []
        for item in query_obj.all():
            results.append(
                SearchResult(
                    id=item.id,
                    name=item.name,
                    content_preview=_preview(item.content),
                    score=score_map.get(item.id),
                    updated_at=item.updated_at.isoformat() if item.updated_at else None,
                )
            )
        return results

    # Fallback search (ILIKE)
    ilike = f"%{trimmed}%"
    query_obj = (
        db.query(FileSystem)
        .filter(FileSystem.type == "file")
        .filter(FileSystem.deleted_at.is_(None))
        .filter((FileSystem.name.ilike(ilike)) | (FileSystem.content.ilike(ilike)))
        .order_by(FileSystem.updated_at.desc())
        .limit(limit)
    )
    if owner_id:
        query_obj = query_obj.filter(FileSystem.owner_id == owner_id)
    return [
        SearchResult(
            id=item.id,
            name=item.name,
            content_preview=_preview(item.content),
            score=None,
            updated_at=item.updated_at.isoformat() if item.updated_at else None,
        )
        for item in query_obj.all()
    ]
