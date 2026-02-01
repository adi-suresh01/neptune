from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class SimilarityStrategy:
    def score(self, topic_a: str, topic_b: str, topic_note_map: Dict[str, set[str]]) -> float:
        raise NotImplementedError


@dataclass(frozen=True)
class CooccurrenceSimilarity(SimilarityStrategy):
    def score(self, topic_a: str, topic_b: str, topic_note_map: Dict[str, set[str]]) -> float:
        a = topic_note_map.get(topic_a, set())
        b = topic_note_map.get(topic_b, set())
        if not a and not b:
            return 0.0
        intersection = a.intersection(b)
        union = a.union(b)
        return len(intersection) / max(len(union), 1)


def fallback_similarity() -> SimilarityStrategy:
    return CooccurrenceSimilarity()
