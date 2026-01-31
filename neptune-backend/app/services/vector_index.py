from dataclasses import dataclass
from typing import List, Tuple

from app.core.settings import settings


@dataclass(frozen=True)
class VectorIndex:
    def upsert(self, namespace: str, item_id: str, vector: List[float]) -> None:
        raise NotImplementedError

    def query(self, namespace: str, vector: List[float], top_k: int) -> List[Tuple[str, float]]:
        raise NotImplementedError


@dataclass(frozen=True)
class NoopVectorIndex(VectorIndex):
    def upsert(self, namespace: str, item_id: str, vector: List[float]) -> None:
        return None

    def query(self, namespace: str, vector: List[float], top_k: int) -> List[Tuple[str, float]]:
        return []


def get_vector_index() -> VectorIndex:
    if settings.vector_backend == "none":
        return NoopVectorIndex()
    return NoopVectorIndex()
