# ChromaDB's default (and only  built-in) vector index type is
#   HNSW (Hierarchical Navigable Small World) — an
#   approximate-nearest-neighbor graph index. Instead of scanning
#   every vector like our plain VectorDatabase.search() does,
#   HNSW builds a multi-layer graph where each vector links to a
#   handful of nearby neighbors, so a query only has to hop through a
#   small subset of the graph instead of comparing against all N
#   vectors. That's the main  difference from the brute-force cosine approach
#   HNSW is approximate (occasionally misses the true top-k) but scales
#   roughly logarithmically instead of linearly.

import time

import chromadb
import matplotlib.pyplot as plt

from load_data import df, embeddings, embed
from vector_database import VectorDatabase

SIZES = [100, 500, 1000, 2500, 5000]
QUERY = "neural network training"

COLOR_COSINE = "#4C72B0"
COLOR_CHROMA = "#DD8452"


def build_cosine_db(n):
    db = VectorDatabase()
    for i in range(n):
        db.add_vector(vec_id=f"paper_{i}", vector=embeddings[i])
    return db


def build_chroma_collection(n, client):
    collection = client.create_collection(
        name=f"bench_{n}",
        metadata={"hnsw:space": "cosine"}
    )
    ids = [f"paper_{i}" for i in range(n)]
    collection.add(
        ids=ids,
        embeddings=embeddings[:n].tolist(),
        documents=df["abstract"].tolist()[:n]
    )
    return collection


def benchmark(sizes=SIZES, query=QUERY):
    query_vector = embed(query)
    chroma_client = chromadb.Client()  # ephemeral, isolated from the persistent chroma_db

    cosine_times = []
    chroma_times = []

    for n in sizes:
        cosine_db = build_cosine_db(n)
        start = time.perf_counter()
        cosine_db.search(query_vector, top_k=5)
        cosine_times.append((time.perf_counter() - start) * 1000)

        collection = build_chroma_collection(n, chroma_client)
        start = time.perf_counter()
        collection.query(query_embeddings=[query_vector], n_results=5)
        chroma_times.append((time.perf_counter() - start) * 1000)

        print(f"n={n}: cosine={cosine_times[-1]:.2f}ms, chromadb={chroma_times[-1]:.2f}ms")

    return cosine_times, chroma_times


def plot_results(sizes, cosine_times, chroma_times, path="benchmark_results.png"):
    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.plot(sizes, cosine_times, color=COLOR_COSINE, linewidth=2,
            marker="o", markersize=8, label="Plain cosine")
    ax.plot(sizes, chroma_times, color=COLOR_CHROMA, linewidth=2,
            marker="o", markersize=8, label="ChromaDB (HNSW)")

    # Direct labels at the last point (contrast WARN on the orange line means
    # color alone isn't reliable, so label both series explicitly)
    ax.annotate("Plain cosine", (sizes[-1], cosine_times[-1]),
                textcoords="offset points", xytext=(8, 0),
                color=COLOR_COSINE, va="center", fontsize=10)
    ax.annotate("ChromaDB (HNSW)", (sizes[-1], chroma_times[-1]),
                textcoords="offset points", xytext=(8, 0),
                color=COLOR_CHROMA, va="center", fontsize=10)

    ax.set_xlabel("Number of papers")
    ax.set_ylabel("Query time (ms)")
    ax.set_title(f'Query time vs. dataset size: "{QUERY}"')
    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend()

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"Saved chart to {path}")
    plt.show()


queries = [
    "machine learning model evaluation metrics",
    "how do convolutional neural networks work",
    "SQL query optimization techniques",
    "testing and debugging software systems"
]

if __name__ == "__main__":
    cosine_times, chroma_times = benchmark()
    plot_results(SIZES, cosine_times, chroma_times)
