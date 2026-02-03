from __future__ import annotations

import logging
import time
import requests

from app.core.settings import settings

logger = logging.getLogger(__name__)


def _post(path: str, payload: dict) -> None:
    if not settings.indexer_enabled:
        return
    url = f"{settings.indexer_url}{path}"
    attempts = 3
    delay = 0.2
    for attempt in range(attempts):
        try:
            requests.post(url, json=payload, timeout=2)
            return
        except Exception as e:
            if attempt == attempts - 1:
                logger.warning("Indexer request failed: %s", e)
                return
            time.sleep(delay)
            delay *= 2


def notify_note_upsert(note_id: int) -> None:
    _post("/indexer/note-upsert", {"note_id": note_id})


def notify_note_delete(note_id: int) -> None:
    _post("/indexer/note-delete", {"note_id": note_id})


def notify_graph_refresh() -> None:
    _post("/indexer/graph-refresh", {})
