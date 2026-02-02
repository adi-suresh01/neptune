from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Tuple

import faiss
import numpy as np

from app.core.settings import settings


@dataclass
class FaissIndex:
    index: faiss.IndexIDMap2
    dim: int

    def upsert(self, item_id: int, vector: List[float]) -> None:
        vec = _normalize(np.array([vector], dtype="float32"))
        ids = np.array([item_id], dtype="int64")
        self.index.remove_ids(ids)
        self.index.add_with_ids(vec, ids)

    def delete(self, item_id: int) -> None:
        ids = np.array([item_id], dtype="int64")
        self.index.remove_ids(ids)

    def query(self, vector: List[float], top_k: int) -> List[Tuple[int, float]]:
        if self.index.ntotal == 0:
            return []
        vec = _normalize(np.array([vector], dtype="float32"))
        scores, ids = self.index.search(vec, top_k)
        results = []
        for idx, score in zip(ids[0], scores[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(score)))
        return results


_index: FaissIndex | None = None
_index_dim: int | None = None


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _index_path() -> str:
    return settings.vector_index_path


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def _create_index(dim: int) -> FaissIndex:
    base = faiss.IndexFlatIP(dim)
    return FaissIndex(index=faiss.IndexIDMap2(base), dim=dim)


def load_index(dim: int) -> FaissIndex:
    global _index, _index_dim
    if _index is not None and _index_dim == dim:
        return _index
    path = _index_path()
    if os.path.exists(path):
        index = faiss.read_index(path)
        if index.d != dim:
            index = _create_index(dim).index
        if not isinstance(index, faiss.IndexIDMap2):
            index = faiss.IndexIDMap2(index)
        _index = FaissIndex(index=index, dim=dim)
    else:
        _index = _create_index(dim)
    _index_dim = dim
    return _index


def save_index() -> None:
    if _index is None:
        return
    path = _index_path()
    _ensure_dir(path)
    faiss.write_index(_index.index, path)


def rebuild_index(embeddings: List[Tuple[int, List[float]]], dim: int) -> None:
    global _index, _index_dim
    index = _create_index(dim)
    if embeddings:
        ids = np.array([item_id for item_id, _ in embeddings], dtype="int64")
        vecs = np.array([vec for _, vec in embeddings], dtype="float32")
        vecs = _normalize(vecs)
        index.index.add_with_ids(vecs, ids)
    _index = index
    _index_dim = dim
    save_index()
