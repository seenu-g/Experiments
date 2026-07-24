import networkx as nx
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN


# kmeans produce its final clustering based on the number of clusters
# defined by the user (represented by the variable K) and the dataset.
# For example, if you set K equal to 3, then your dataset will be grouped in 3 clusters;
# if you set K equal to 4, you will group the data in 4 clusters, and so on.
def calculate_cluster_kmeans(embeddings, num_clusters=3, random_state=42):
    kmeans = KMeans(n_clusters=num_clusters, random_state=random_state)
    return kmeans

# clear view of how the algorithm clusters nodes based on their embeddings:
def display_kmeans_cluster(G, embeddings, embeddings_2d, kmeans, num_clusters=3, random_state=42):
    # Reuse the already-fit K-Means model instead of fitting a new one
    cluster_labels = kmeans.fit_predict(embeddings)

    # Visualize K-Means clustering in the embedding space with node labels
    plt.figure(figsize=(12, 10))
    plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=cluster_labels, cmap=plt.cm.Set1, alpha=0.7)

    # Add node labels
    for i, node in enumerate(G.nodes()):
        plt.text(embeddings_2d[i, 0], embeddings_2d[i, 1], node, fontsize=8)

    plt.title('K-Means Clustering in Embedding Space with Node Labels')

    plt.colorbar(label="Cluster Label")
    plt.show()

# color the points in the scatter plot of the 2D embedding space.
# Each color represents a different cluster.
def display_graph_cluster(G, pos, embeddings, kmeans, num_clusters=3, random_state=42):
    # Reuse the already-fit K-Means model instead of fitting a new one
    cluster_labels = kmeans.fit_predict(embeddings)

    # Visualize clusters
    plt.figure(figsize=(12, 10))
    nx.draw(G, pos, with_labels=True, font_size=10, node_size=700, node_color=cluster_labels, cmap=plt.cm.Set1, edge_color='gray', alpha=0.6)
    plt.title('Graph Clustering using K-Means')

    plt.show()

# Density-Based Clustering algorithms like DBSCAN don't require a preset number of clusters.
# It also identifies outliers as noises. it can find arbitrarily sized
# and arbitrarily shaped clusters quite well
def  calculate_cluster_dbscan(embeddings, eps=1.0, min_samples=2):
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    return dbscan

 # eps parameter defines the maximum distance between two samples for
 # one to be considered as in the neighborhood of the other, and
 # the min_samples parameter determines the minimum number of samples
 # in a neighborhood for a point to be considered as a core point.
 # DBSCAN will assign nodes to clusters and identify noise points that don't belong to any cluster.

def display_dbscan_cluster(G, pos, embeddings, dbscan):
    cluster_labels = dbscan.fit_predict(embeddings)

    # Visualize clusters
    plt.figure(figsize=(12, 10))
    nx.draw(G, pos, with_labels=True, font_size=10, node_size=700, node_color=cluster_labels, cmap=plt.cm.Set1, edge_color='gray', alpha=0.6)
    plt.title('Graph Clustering using DBSCAN')
    plt.show()
