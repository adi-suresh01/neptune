from typing import List, Dict, Any, Tuple
import networkx as nx
import itertools
import logging
from app.services.similarity import default_similarity, SimilarityStrategy
from app.core.settings import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


def find_topic_relationships(
    topic_note_map: Dict[str, set[str]],
    strategy: SimilarityStrategy | None = None,
) -> List[Tuple[str, str, float]]:
    """
    Find relationships between topics using note co-occurrence.
    """
    if len(topic_note_map) < 2:
        return []

    topic_pairs = list(itertools.combinations(topic_note_map.keys(), 2))

    logger.info("Finding relationships for %s topic pairs", len(topic_pairs))

    similarity = strategy or default_similarity()
    edges = []
    batch_size = max(1, settings.llm_relationship_batch_size)
    pairs = [{"a": a, "b": b} for a, b in topic_pairs]

    for i in range(0, len(pairs), batch_size):
        batch = pairs[i : i + batch_size]
        scored = llm_service.score_relationships_batch(batch)
        scored_map = {(item["a"], item["b"]): item["score"] for item in scored}
        for pair in batch:
            key = (pair["a"], pair["b"])
            if key in scored_map:
                edges.append((pair["a"], pair["b"], scored_map[key]))
            else:
                strength = similarity.score(pair["a"], pair["b"], topic_note_map)
                edges.append((pair["a"], pair["b"], strength))

    logger.info("Found %s relationships between topics", len(edges))
    return edges

def create_topic_graph(topics_data: List[Dict[str, Any]]) -> nx.Graph:
    """
    Create a NetworkX graph from topic extraction results.
    """
    G = nx.Graph()
    
    topic_note_map: Dict[str, set[str]] = {}
    for item in topics_data:
        topic_note_map[item["topic"]] = set(item["note_ids"])
    
    # Add topic nodes with size based on number of notes
    for item in topics_data:
        topic_name = item["topic"]
        note_ids = item["note_ids"]
        G.add_node(
            topic_name, 
            type="topic",
            size=len(note_ids) * 20,
            note_count=len(note_ids),
            note_ids=note_ids
        )
    
    # Find and add relationships between topics
    topic_relationships = find_topic_relationships(topic_note_map)
    filtered = [
        (t1, t2, s) for t1, t2, s in topic_relationships if s >= settings.kg_min_strength
    ]
    filtered.sort(key=lambda item: item[2], reverse=True)
    if settings.kg_max_edges > 0:
        filtered = filtered[: settings.kg_max_edges]
    for topic1, topic2, strength in filtered:
        G.add_edge(topic1, topic2, weight=strength)
    
    return G

def graph_to_frontend_format(G: nx.Graph) -> Dict:
    """
    Convert NetworkX graph to a frontend-friendly JSON structure with note details
    """
    from app.db.database import SessionLocal
    from app.db.models import FileSystem
    
    db = SessionLocal()
    try:
        notes = db.query(FileSystem).filter(FileSystem.type == "file").all()
        note_names = {note.id: note.name for note in notes}
    except Exception as e:
        logger.warning("Error fetching note names: %s", e)
        note_names = {}
    finally:
        db.close()
    
    nodes = []
    for node, data in G.nodes(data=True):
        note_details = []
        for note_id_str in data.get("note_ids", []):
            try:
                note_id = int(note_id_str)
                note_name = note_names.get(note_id, f"Note {note_id}")
                note_details.append({
                    "id": note_id,
                    "name": note_name
                })
            except (ValueError, TypeError):
                note_details.append({
                    "id": note_id_str,
                    "name": f"Note {note_id_str}"
                })
        
        nodes.append({
            "id": node,
            "label": node,
            "topic": node,
            "size": data.get("size", 30),
            "noteCount": data.get("note_count", 0),
            "noteIds": data.get("note_ids", []),
            "noteDetails": note_details
        })
    
    links = []
    for u, v, data in G.edges(data=True):
        links.append({
            "source": u,
            "target": v,
            "strength": data.get("weight", 0.5)
        })
    
    return {
        "nodes": nodes,
        "links": links
    }
