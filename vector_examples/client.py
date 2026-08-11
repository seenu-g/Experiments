import numpy as np

from vector_database import VectorDatabase

db = VectorDatabase()
np.random.seed(10)

db.add_vector("vec1", np.random.rand(5), metadata = {"text": "First item"})
db.add_vector("vec2", np.random.rand(5), metadata = {"text": "Second item"})
db.add_vector("vec3", np.random.rand(5), metadata = {"text": "Third item"})
db.add_vector("vec4", np.random.rand(5), metadata = {"text": "Fourth item"})
db.add_vector("vec5", np.random.rand(5), metadata = {"text": "Fifth item"})
db.add_vector("vec6", np.random.rand(5), metadata = {"text": "Sixth item"})
db.add_vector("vec7", np.random.rand(5), metadata = {"text": "Seventh item"})
db.add_vector("vec8", np.random.rand(5), metadata = {"text": "Eight item"})
db.add_vector("vec9", np.random.rand(5), metadata = {"text": "Ninth item"})
db.add_vector("vec10", np.random.rand(5), metadata = {"text": "Tenth item"})

# print(db.get_all_vectors())

query_vector = np.random.rand(5)
print("Query vector: ", query_vector)

results = db.search(query_vector, top_k = 3)
print(f"Query vector: {query_vector}\n")
for res in results:
    print(f"ID: {res['id']} | Similarity: {res['similarity']:.2f} | Metadata: {res['metadata']}")

import ollama

def embed(text):
    return ollama.embeddings(model="all-minilm:l6-v2", prompt=text)["embedding"]

sentences = [
    "Kunal's cat is playing with wool.",
    "Ashish was born on 1st September 1700.",
    "Dogs are loyal animals.",
    "I love eating pizza but only on Fridays.",
    "Manika was born in Bhopal."
]

sentence_db = VectorDatabase()

for idx, sentence in enumerate(sentences):
    # Create sentence embedding
    embedding = embed(sentence)

    sentence_db.add_vector(vec_id=f"sent_{idx}",
                           vector=embedding, metadata={"sentence": sentence})

query = "When is Ashish's birthday?"
query_vec = embed(query)

results = sentence_db.search(query_vec, top_k = 1)

print(f"Query: \"{query}\"\n")

for res in results:
    print(f"Similar Sentence: {res['metadata']['sentence']}")
    print(f"Cosine Similarity Score: {res['similarity']:.2f}\n")