import chromadb

from load_data import df, embeddings

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "arxiv_papers"

# Persistent client so the collection survives across script runs
chromadb_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Create (or reuse) the collection
collection = chromadb_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"description": "5000 arXiv papers from computer science"}
)

print(f"Using collection: {collection.name}")
print(f"Collection count: {collection.count()}")

if collection.count() >= len(df):
    print("Collection already populated, skipping insert.")
else:
    ids = [f"paper_{i}" for i in range(len(df))]
    metadatas = [
        {
            "title": row['title'],
            "category": row['category'],
            "year": int(str(row['published'])[:4]),  # Store year as integer for filtering
            "authors": row['authors'][:100] if len(row['authors']) <= 100 else row['authors'][:97] + "..."
        }
        for _, row in df.iterrows()
    ]
    documents = df['abstract'].tolist()

    print(f"Inserting {len(embeddings)} embeddings...")

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        documents=documents
    )

    print(f"\nCollection now contains {collection.count()} papers")