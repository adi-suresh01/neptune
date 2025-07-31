import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import os
import itertools
from dotenv import load_dotenv
from .llm_service import extract_topics_from_notes, get_llm_response
from typing import List, Dict, Any, Tuple

# Load environment variables
load_dotenv()

def find_topic_relationships(topics: List[str]) -> List[Tuple[str, str, float]]:
    """
    Find relationships between topics using Ollama LLM.
    
    Args:
        topics: List of topic strings
        
    Returns:
        List of tuples (topic1, topic2, strength) representing edges
    """
    # No need to find relationships if there are too few topics
    if len(topics) < 2:
        return []
    
    # Generate all possible pairs of topics
    topic_pairs = list(itertools.combinations(topics, 2))
    
    # For each pair, ask Ollama to rate the relationship
    edges = []
    
    for topic1, topic2 in topic_pairs:
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
            response = get_llm_response(prompt)
            # Extract number from response
            strength = float(response.strip())
            # Ensure it's in valid range
            strength = max(0.1, min(1.0, strength))
            edges.append((topic1, topic2, strength))
        except:
            # Default relationship if parsing fails
            edges.append((topic1, topic2, 0.3))
    
    print(f"Found {len(edges)} relationships between topics")
    return edges

def create_topic_graph(topics_data: List[Dict[str, Any]]) -> nx.Graph:
    """
    Create a NetworkX graph from topic extraction results.
    
    Args:
        topics_data: List of topic dictionaries, each with 'topic' and 'note_ids' fields
        
    Returns:
        NetworkX graph with topic nodes and relationship edges
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
            size=len(note_ids) * 20,  # Size proportional to number of notes
            note_count=len(note_ids),
            note_ids=note_ids
        )
    
    # Find and add relationships between topics
    topic_relationships = find_topic_relationships(topic_names)
    for topic1, topic2, strength in topic_relationships:
        G.add_edge(topic1, topic2, weight=strength)
    
    return G

def visualize_graph_plotly(G: nx.Graph, filename: str = "topic_graph.html"):
    """
    Create an interactive Plotly visualization of the topic graph
    
    Args:
        G: NetworkX graph of topics
        filename: Output HTML file name
    """
    # Create a spring layout for node positions
    pos = nx.spring_layout(G, k=0.4, iterations=50, seed=42)
    
    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_sizes = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        note_count = G.nodes[node].get('note_count', 0)
        node_text.append(f"{node}<br>Notes: {note_count}")
        node_sizes.append(G.nodes[node].get('size', 30))
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=list(G.nodes()),
        textposition="bottom center",
        marker=dict(
            size=node_sizes,
            color='rgba(25, 118, 210, 0.8)',
            line=dict(width=2, color='rgba(50, 50, 50, 0.8)')
        ),
        hoverinfo='text',
        hovertext=node_text,
        name="Topics"
    )
    
    # Create edge trace
    edge_x = []
    edge_y = []
    edge_text = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        weight = G.edges[edge].get('weight', 0.5)
        edge_text.append(f"Relationship strength: {weight:.2f}")
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1, color='rgba(100, 100, 200, 0.7)'),
        hoverinfo='text',
        hovertext=edge_text,
        name="Relationships"
    )
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title={
                'text': 'Knowledge Graph: Topic Relationships',
                'font': {'size': 16}
            },
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor='rgba(255, 255, 255, 1)',
            plot_bgcolor='rgba(255, 255, 255, 1)'
        )
    )
    
    # Create output directory
    import os
    os.makedirs("outputs", exist_ok=True)

    # Save to outputs directory instead
    fig.write_html(f"outputs/{filename}")
    print(f"Interactive graph saved to {filename}")
    
    return fig

def visualize_graph_matplotlib(G: nx.Graph, filename: str = "topic_graph.png"):
    """
    Create a static Matplotlib visualization of the topic graph
    
    Args:
        G: NetworkX graph of topics
        filename: Output PNG file name
    """
    plt.figure(figsize=(12, 10))
    
    # Generate layout
    pos = nx.spring_layout(G, k=0.4, iterations=50, seed=42)
    
    # Get node sizes based on note count
    node_sizes = [G.nodes[node].get('size', 300) for node in G.nodes()]
    
    # Get edge widths based on relationship strength
    edge_widths = [G.edges[edge].get('weight', 0.5) * 2 for edge in G.edges()]
    
    # Draw network
    nx.draw(G, pos,
           node_size=node_sizes,
           node_color='skyblue',
           width=edge_widths,
           edge_color='navy',
           with_labels=True,
           font_size=10,
           font_weight='bold')
    
    plt.title("Knowledge Graph: Topic Relationships", fontsize=16)
    plt.tight_layout()
    
    # Save static image
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Static graph image saved to {filename}")
    
    plt.close()

def visualize_topic_relationships(topics_data, filename_base="topic_relationships"):
    """Create a knowledge graph with just topics and their relationships"""
    G = create_topic_graph(topics_data)
    
    # Print graph statistics
    print(f"\nTopic Graph Statistics:")
    print(f"Number of topics: {len(G.nodes())}")
    print(f"Number of relationships: {len(G.edges())}")
    
    # Print topic details
    print("\nTopics and associated note counts:")
    for node, data in G.nodes(data=True):
        note_count = data.get('note_count', 0)
        print(f"  - {node}: {note_count} notes")
    
    # Print relationship details
    if G.edges():
        print("\nTopic relationships:")
        for u, v, data in G.edges(data=True):
            strength = data.get('weight', 0.5)
            print(f"  - {u} <--> {v} (strength: {strength:.2f})")
    else:
        print("\nNo relationships detected between topics.")
    
    # Generate visualizations
    print("\nGenerating topic relationship visualizations...")
    visualize_graph_plotly(G, filename=f"{filename_base}.html")
    visualize_graph_matplotlib(G, filename=f"{filename_base}.png")
    
    return G

def graph_to_frontend_format(G: nx.Graph) -> Dict:
    """
    Convert NetworkX graph to a frontend-friendly JSON structure
    
    Args:
        G: NetworkX graph of topics and relationships
        
    Returns:
        Dictionary with nodes and links arrays for frontend visualization
    """
    nodes = []
    for node, data in G.nodes(data=True):
        nodes.append({
            "id": node,
            "label": node,
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
    
# Run this to generate the visualizations
# if __name__ == "__main__":
#     from test_llm import test_notes, topics
    
#     # If topics weren't extracted yet, do it now
#     if not topics:
#         topics = extract_topics_from_notes(test_notes)
#         print(f"Extracted topics: {topics}")
    
#     # Create and visualize the topic graph
#     print("\nCreating knowledge graph with just topics and their relationships...")
#     G_topics = visualize_topic_relationships(topics)