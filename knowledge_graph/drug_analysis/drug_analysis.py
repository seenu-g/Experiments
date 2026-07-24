import matplotlib.pyplot as plt

from build_drug_graph import load_data, build_graph, display_graph
from centrality_analysis import (
    calculate_centrality_measures,
    display_degree_centrality,
    display_betweenness_centrality,
    display_closeness_centrality,
    find_shortest_path,
    display_shortest_path,
)
# node2vec / gensim are not installed yet (needs a C compiler to build from
# source on this machine) - uncomment once they're available.
# from graph_embeddings import (
#     compute_node_embeddings,
#     reduce_embeddings_2d,
#     display_embeddings,
# )
# from clustering_analysis import (
#     calculate_cluster_kmeans,
#     calculate_cluster_dbscan,
#     display_graph_cluster,
#     display_dbscan_cluster,
# )

df = load_data()
G = build_graph(df)
pos = display_graph(G)

num_nodes = G.number_of_nodes()
num_edges = G.number_of_edges()
print(f'Number of nodes: {num_nodes}')
print(f'Number of edges: {num_edges}')
print(f'Ratio edges to nodes: {round(num_edges / num_nodes, 2)}')

# Calculate centrality measures
centrality = calculate_centrality_measures(G)
degree_centrality = centrality['degree']
betweenness_centrality = centrality['betweenness']
closeness_centrality = centrality['closeness']

for node, val in degree_centrality.items():
    print(f'{node}: Degree Centrality = {val:.2f}')

for node, val in betweenness_centrality.items():
    print(f'Betweenness Centrality of {node}: {val:.2f}')

for node, val in closeness_centrality.items():
    print(f'Closeness Centrality of {node}: {val:.2f}')

# Visualize centrality measures
fig, axes = plt.subplots(1, 3, figsize=(15, 10))
display_degree_centrality(G, pos, degree_centrality, axes[0])
display_betweenness_centrality(G, pos, betweenness_centrality, axes[1])
display_closeness_centrality(G, pos, closeness_centrality, axes[2])

plt.tight_layout()
plt.show()

source_node = 'gene2'
target_node = 'cancer'

# Find and visualize the shortest path
shortest_path = find_shortest_path(G, source_node, target_node)
display_shortest_path(G, pos, shortest_path)
print('Shortest Path:', shortest_path)

# --- Everything below needs node2vec / gensim (not installed) ---
# Uncomment once `pip install node2vec gensim` succeeds.

# # Node embeddings via node2vec + t-SNE
# embeddings = compute_node_embeddings(G)
# embeddings_2d = reduce_embeddings_2d(embeddings)
# display_embeddings(G, embeddings_2d)
#
# # K-Means clustering on the embeddings
# kmeans_model = calculate_cluster_kmeans(embeddings, num_clusters=3)
# kmeans_labels = kmeans_model.fit_predict(embeddings)
# display_embeddings(G, embeddings_2d, cluster_labels=kmeans_labels, title='K-Means Clustering in Embedding Space with Node Labels')
# display_graph_cluster(G, pos, embeddings, kmeans_model)
#
# # DBSCAN clustering on the embeddings
# dbscan_model = calculate_cluster_dbscan(embeddings, eps=1.0, min_samples=2)
# dbscan_labels = dbscan_model.fit_predict(embeddings)
# display_dbscan_cluster(G, pos, embeddings, dbscan_model)