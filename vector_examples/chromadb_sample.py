import chromadb
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="personal_collection")

documents=[
        "This is a document about machine learning",
        "This is another document about data science",
        "A third document about artificial intelligence",
        "This is a document about economics",
        "This is another document about accounting",
        "A third document about finance",
        "This is a document about control systems",
        "This is another document about building automation systems",
        "A third document about vehicle control systems"
    ]
metadatas=[
        {"source": "test1"},
        {"source": "test2"},
        {"source": "test3"},
        {"source": "test4"},
        {"source": "test5"},
        {"source": "test6"},
        {"source": "test7"},
        {"source": "test8"},
        {"source": "test9"}
    ]
ids=[
        "id1",
        "id2",
        "id3",
        "id4",
        "id5",
        "id6",
        "id7",
        "id8",
        "id9"
    ]

collection.add(ids=ids, documents=documents, metadatas=metadatas)

results = collection.query(
    query_texts=[
        "This is a query about systems"
    ],
    n_results=2
)

print(results)

results = collection.query(
    query_texts=[
        "This is a query about machine learning and data science"
    ],
    n_results=2
)

print(results, "\n")