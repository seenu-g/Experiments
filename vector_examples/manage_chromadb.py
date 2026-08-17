import chromadb
client = chromadb.Client()

neo_collection = client.create_collection(name="neo")
neo_collection.add(
    embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
    metadatas=[{"quote": "I know kung fu."}, {"quote": "There is no spoon."}],
    ids=["quote_1", "quote_2"]
)
results = neo_collection.query(
    query_embeddings=[[0.1, 0.2, 0.3]],
    n_results=1
)

print(results)


morpheus_collection = client.create_collection(
    name="morpheus", metadata={"hnsw:space": "cosine"}
)
morpheus_collection.add(
    documents=[
        "This is your last chance. After this, there is no turning back.",
        "You take the blue pill, the story ends, you wake up in your bed and believe whatever you want to believe.",
        "You take the red pill, you stay in Wonderland, and I show you how deep the rabbit hole goes.",
    ],
    ids=["quote_1", "quote_2", "quote_3"],
)
# query based on query text
results = morpheus_collection.query(
    query_texts=["Make a choice"],
    n_results=2,
)
print(results)

results = morpheus_collection.query(
    query_texts=["make a choice"], n_results=1, include=["distances", "embeddings"]
)
print(results)

# query and   choose which data is returned
items = morpheus_collection.get(ids=["quote_1", "quote_3"])
print(items)

item_count = morpheus_collection.count()
print(f"Count of items in collection: {item_count}")

matrix_collection = client.create_collection(name="matrix", metadata={"hnsw:space": "cosine"})
matrix_collection.add(
    documents=[
        "The Matrix is everywhere, it is all around us.",
        "You can see it when you look out your window or when you turn on your television.",
        "Unfortunately, no one can be told what the Matrix is",
        "You hear that Mr. Anderson?... That is the sound of inevitability...",
        "You are a plague, Mr. Anderson. You and your kind are a cancer of this planet.",
    ],
    metadatas=[
        {"category": "quote", "speaker": "Morpheus"},
        {"category": "quote", "speaker": "Morpheus"},
        {"category": "quote", "speaker": "Morpheus"},
        {"category": "quote", "speaker": "Agent Smith"},
        {"category": "quote", "speaker": "Agent Smith"},
    ],
    ids=["quote_1", "quote_2", "quote_3", "quote_4", "quote_5"],
)
results = matrix_collection.query(
    query_texts=["What is the Matrix?"],
    where={"speaker": "Morpheus"},
    n_results=2,
)
print(results)

matrix_collection.update(
    ids=["quote_2"],
    metadatas=[{"category": "quote", "speaker": "Morpheus"}],
    documents=["The Matrix is a system, Neo. That system is our enemy."],
)
items = matrix_collection.get(ids=["quote_2"])

print(items)

matrix_collection.upsert(
    ids=["quote_2", "quote_4"],
    metadatas=[
        {"category": "quote", "speaker": "Morpheus"},
        {"category": "quote", "speaker": "Srinivasan"},
    ],
    documents=[
        "You take the blue pill, the story ends, you wake up in your bed and believe whatever you want to believe.",
        "I'm going to enjoy watching you die, Mr. Anderson.",
    ],
)
items = matrix_collection.get(ids=["quote_2", "quote_4"])


matrix_collection.delete(where={"speaker": "Srinivasan"})
item_count = matrix_collection.count()
print(f"Count of items in collection: {item_count}")

matrix_collection.delete(ids=["quote_3"])
items = matrix_collection.get()
print(items)