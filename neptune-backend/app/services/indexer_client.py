from __future__ import annotations

import logging
import requests

from app.core.settings import settings

logger = logging.getLogger(__name__)


def _post(path: str, payload: dict) -> None:
    if not settings.indexer_enabled:
        return
    url = f"{settings.indexer_url}{path}"
    try:
        requests.post(url, json=payload, timeout=2)
    except Exception as e:
        logger.warning("Indexer request failed: %s", e)


def notify_note_upsert(note_id: int) -> None:
    _post("/indexer/note-upsert", {"note_id": note_id})


def notify_note_delete(note_id: int) -> None:
    _post("/indexer/note-delete", {"note_id": note_id})


def notify_graph_refresh() -> None:
    _post("/indexer/graph-refresh", {})
