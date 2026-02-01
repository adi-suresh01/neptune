import json
import os
from dataclasses import dataclass
from typing import Dict, Optional
from app.core.settings import settings


@dataclass
class TopicCacheItem:
    note_id: str
    checksum: str
    topic: str


class TopicCache:
    def __init__(self) -> None:
        self.path = self._resolve_path()
        self._data: Dict[str, TopicCacheItem] = {}
        self._loaded = False

    def _resolve_path(self) -> str:
        base, ext = os.path.splitext(settings.kg_cache_path)
        if ext:
            return f"{base}.topics.{settings.llm_prompt_version}{ext}"
        return f"{settings.kg_cache_path}.topics.{settings.llm_prompt_version}.json"

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r") as handle:
                raw = json.load(handle)
            for note_id, item in raw.items():
                self._data[note_id] = TopicCacheItem(
                    note_id=note_id,
                    checksum=item["checksum"],
                    topic=item["topic"],
                )
        except Exception:
            self._data = {}

    def get(self, note_id: str, checksum: str) -> Optional[str]:
        self._load()
        item = self._data.get(note_id)
        if item and item.checksum == checksum:
            return item.topic
        return None

    def set(self, note_id: str, checksum: str, topic: str) -> None:
        self._load()
        self._data[note_id] = TopicCacheItem(note_id=note_id, checksum=checksum, topic=topic)

    def flush(self) -> None:
        self._load()
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        payload = {
            note_id: {"checksum": item.checksum, "topic": item.topic}
            for note_id, item in self._data.items()
        }
        with open(self.path, "w") as handle:
            json.dump(payload, handle)


topic_cache = TopicCache()
