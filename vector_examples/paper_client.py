import chromadb

from load_data import embed

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "arxiv_papers"

client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    collection = client.get_collection(name=COLLECTION_NAME)
except chromadb.errors.NotFoundError:
    raise SystemExit(
        f"Collection '{COLLECTION_NAME}' not found in {CHROMA_PATH}. "
        "Run load_toDB.py first to populate it."
    )


def query_papers(query_text, n_results=5):
    query_embedding = embed(query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    papers = []
    for doc, metadata, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        papers.append({
            "title": metadata["title"],
            "category": metadata["category"],
            "year": metadata["year"],
            "distance": distance,
            "abstract": doc
        })

    return papers


def search_papers(query_text, n_results=5):
    papers = query_papers(query_text, n_results=n_results)

    print(f"Query: \"{query_text}\"\n")
    for paper in papers:
        print(f"Title: {paper['title']} ({paper['year']})")
        print(f"Category: {paper['category']} | Distance: {paper['distance']:.4f}")
        print(f"Abstract: {paper['abstract'][:200]}...\n")

    return papers


if __name__ == "__main__":
    query = "neural network training"
    papers = query_papers(query, n_results=5)

    print(f"Query: \"{query}\"\n")
    for paper in papers:
        print(f"Title: {paper['title']} ({paper['year']})")
        print(f"Category: {paper['category']} | Distance: {paper['distance']:.4f}")
        print(f"Abstract: {paper['abstract'][:200]}...\n")

    results = search_papers("reinforcement learning and robotics")
    results_cv = search_papers("image segmentation techniques")
    results_broad = search_papers("deep learning applications")
