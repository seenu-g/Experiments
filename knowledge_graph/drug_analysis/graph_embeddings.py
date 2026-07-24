import matplotlib.pyplot as plt
import numpy as np
from node2vec import Node2Vec
from sklearn.manifold import TSNE

# Graph embeddings are mathematical representations of nodes or edges 
# in a graph in a continuous vector space. 
# These embeddings capture the structural and relational information of the graph, 
# allowing us to perform various analyses, suc as
# node similarity calculation and visualization in lower-dimensional space.

def compute_node_embeddings(G, dimensions=64, walk_length=30, num_walks=200, workers=4, window=10, min_count=1, batch_words=4):
    # node2vec algorithm, which learns embeddings by performing random walks on the graph and
    # optimizing to preserve the local neighborhood structure of nodes.
    node2vec = Node2Vec(G, dimensions=dimensions, walk_length=walk_length, num_walks=num_walks, workers=workers)
    model = node2vec.fit(window=window, min_count=min_count, batch_words=batch_words)
    return np.array([model.wv[node] for node in G.nodes()])


def reduce_embeddings_2d(embeddings, perplexity=10, max_iter=400):
    tsne = TSNE(n_components=2, perplexity=perplexity, max_iter=max_iter)
    return tsne.fit_transform(embeddings)


def display_embeddings(G, embeddings_2d, cluster_labels=None, title='Node Embeddings Visualization'):
    plt.figure(figsize=(12, 10))
    if cluster_labels is None:
        plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c='blue', alpha=0.7)
    else:
        plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=cluster_labels, cmap=plt.cm.Set1, alpha=0.7)
        plt.colorbar(label='Cluster Label')
    for i, node in enumerate(G.nodes()):
        plt.text(embeddings_2d[i, 0], embeddings_2d[i, 1], node, fontsize=8)
    plt.title(title)
    plt.show()
