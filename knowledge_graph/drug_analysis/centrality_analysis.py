import networkx as nx
import matplotlib.pyplot as plt


def calculate_centrality_measures(G):
    return {
        'degree': nx.degree_centrality(G),
        'betweenness': nx.betweenness_centrality(G),
        'closeness': nx.closeness_centrality(G),
    }


def display_degree_centrality(G, pos, degree_centrality, ax=None):
    if ax is None:
        ax = plt.gca()
    nx.draw(G, pos, ax=ax, with_labels=True, font_size=10, node_size=[v * 3000 for v in degree_centrality.values()], node_color=list(degree_centrality.values()), cmap=plt.cm.Blues, edge_color='gray', alpha=0.6)
    ax.set_title('Degree Centrality')


def display_betweenness_centrality(G, pos, betweenness_centrality, ax=None):
    if ax is None:
        ax = plt.gca()
    nx.draw(G, pos, ax=ax, with_labels=True, font_size=10, node_size=[v * 3000 for v in betweenness_centrality.values()], node_color=list(betweenness_centrality.values()), cmap=plt.cm.Oranges, edge_color='gray', alpha=0.6)
    ax.set_title('Betweenness Centrality')


def display_closeness_centrality(G, pos, closeness_centrality, ax=None):
    if ax is None:
        ax = plt.gca()
    nx.draw(G, pos, ax=ax, with_labels=True, font_size=10, node_size=[v * 3000 for v in closeness_centrality.values()], node_color=list(closeness_centrality.values()), cmap=plt.cm.Greens, edge_color='gray', alpha=0.6)
    ax.set_title('Closeness Centrality')


# Shortest path analysis focuses on finding the shortest path between two nodes in the graph.
# Helps to understand the connectivity between different entities
# and the minimum number of relationships required to connect them.
def find_shortest_path(G, source, target):
    return nx.shortest_path(G, source=source, target=target)


def display_shortest_path(G, pos, path):
    plt.figure(figsize=(10, 8))
    path_edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
    nx.draw(G, pos, with_labels=True, font_size=10, node_size=700, node_color='lightblue', edge_color='gray', alpha=0.6)
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='red', width=2)
    plt.title(f'Shortest Path from {path[0]} to {path[-1]}')
    plt.show()
