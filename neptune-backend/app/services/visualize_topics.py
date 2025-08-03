import os
import requests
from typing import List, Dict, Any, Tuple
import networkx as nx
import itertools
from dotenv import load_dotenv

load_dotenv()

def find_topic_relationships(topics: List[str]) -> List[Tuple[str, str, float]]:
    """
    Find relationships between topics using Ollama LLM.
    
    Args:
        topics: List of topic strings
        
    Returns:
        List of tuples (topic1, topic2, strength) representing edges
    """
    if len(topics) < 2:
        return []
    
    # Generate all possible pairs of topics
    topic_pairs = list(itertools.combinations(topics, 2))
    
    print(f"🔄 Finding relationships for {len(topic_pairs)} topic pairs...")
    
    edges = []
    for topic1, topic2 in topic_pairs:
        strength = get_relationship_strength(topic1, topic2)
        edges.append((topic1, topic2, strength))
    
    print(f"✅ Found {len(edges)} relationships between topics")
    return edges

def get_relationship_strength(topic1: str, topic2: str) -> float:
    """Get relationship strength between two topics using Ollama"""
    from app.services.llm_service import llm_service
    
    prompt = f"""
    Rate the relationship strength between these two topics on a scale from 0.1 to 1.0:
    Topic 1: {topic1}
    Topic 2: {topic2}
    
    Consider ANY type of relationship: subjects taught together, historical connections, 
    conceptual overlap, shared methods, complementary ideas, or topics that might appear 
    in the same text or course.
    
    Be generous with connections - find ANY logical connection, no matter how slight.
    - 0.1 means very weakly related but still connected
    - 1.0 means strongly related
    
    Respond with ONLY a number between 0.1 and 1.0, nothing else.
    """
    
    try:
        response = llm_service._call_ollama(prompt, max_tokens=10)
        strength = float(response.strip())
        strength = max(0.1, min(1.0, strength))
        print(f"📊 {topic1} ↔ {topic2}: {strength}")
        return strength
    except Exception as e:
        print(f"❌ Error getting relationship for {topic1}-{topic2}: {e}")
        return 0.3  # Default relationship

def create_topic_graph(topics_data: List[Dict[str, Any]]) -> nx.Graph:
    """
    Create a NetworkX graph from topic extraction results.
    FIXED: Removed async complications, pure sync version.
    """
    G = nx.Graph()
    
    # Extract all topic names
    topic_names = [item["topic"] for item in topics_data]
    
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
    
    # Find and add relationships between topics (SYNC)
    topic_relationships = find_topic_relationships(topic_names)
    for topic1, topic2, strength in topic_relationships:
        if strength > 0.2:  # Only add meaningful relationships
            G.add_edge(topic1, topic2, weight=strength)
    
    return G

def graph_to_frontend_format(G: nx.Graph) -> Dict:
    """
    Convert NetworkX graph to a frontend-friendly JSON structure
    """
    nodes = []
    for node, data in G.nodes(data=True):
        nodes.append({
            "id": node,
            "label": node,
            "topic": node,  # Add topic field
            "size": data.get("size", 30),
            "noteCount": data.get("note_count", 0),
            "noteIds": data.get("note_ids", [])
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

# REMOVED ALL ASYNC FUNCTIONS THAT WERE CAUSING CONFLICTS
# We'll stick with sync for now to avoid event loop issues