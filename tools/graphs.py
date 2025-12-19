"""Graph visualization tools."""

from typing import List

import matplotlib.pyplot as plt
import networkx as nx

from config import default_config
from plot_utils import handle_plot_errors, save_and_show_plot


@handle_plot_errors("relationship graph")
async def create_relationship_graph(
    nodes: List[str], 
    edges: List[List[str]], 
    title: str = "Relationship Graph",
    node_size: int = 1000,
    font_size: int = 12
) -> str:
    """Create a directed relationship graph."""
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    for edge in edges:
        if len(edge) >= 2:
            G.add_edge(edge[0], edge[1])
    
    plt.figure(figsize=default_config.figsize_large)
    pos = nx.spring_layout(G, k=2, iterations=50)
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=node_size, alpha=0.8)
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20, arrowstyle='->')
    nx.draw_networkx_labels(G, pos, font_size=font_size, font_weight='bold')
    
    plt.title(title, fontsize=default_config.title_fontsize, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    return save_and_show_plot("relationship_graph")
