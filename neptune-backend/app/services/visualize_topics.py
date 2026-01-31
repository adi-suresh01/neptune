from typing import List, Dict, Any, Tuple
import networkx as nx
import itertools
import logging
from app.services.similarity import default_similarity, SimilarityStrategy

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
    for topic1, topic2 in topic_pairs:
        strength = similarity.score(topic1, topic2, topic_note_map)
        edges.append((topic1, topic2, strength))

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
    for topic1, topic2, strength in topic_relationships:
        if strength > 0.2:  # Only add meaningful relationships
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
