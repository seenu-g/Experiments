import os

import numpy as np
import ollama
import pandas as pd

EMBEDDINGS_PATH = 'embeddings_minilm_5k.npy'
EMBEDDING_MODEL = 'all-minilm:l6-v2'
MAX_EMBED_CHARS = 500  # all-minilm:l6-v2 has a 256-token context window

# Load the metadata
df = pd.read_csv('arxiv_papers_5k.csv')
print(f"Loaded {len(df)} papers")


def embed(text):
    return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text[:MAX_EMBED_CHARS])["embedding"]


def compute_embeddings(texts, path=EMBEDDINGS_PATH):
    total = len(texts)
    vectors = []

    for i, text in enumerate(texts, start=1):
        vectors.append(embed(text))
        if i % 100 == 0 or i == total:
            print(f"  Embedded {i}/{total} ({i / total:.0%})")

    embeddings = np.array(vectors, dtype=np.float32)
    np.save(path, embeddings)
    return embeddings


def load_embeddings(texts, path=EMBEDDINGS_PATH):
    # Load cached embeddings if present, otherwise compute and cache them
    if os.path.exists(path):
        embeddings = np.load(path)
        print(f"Loaded cached embeddings with shape: {embeddings.shape}")
    else:
        print(f"Computing embeddings for {len(texts)} abstracts via {EMBEDDING_MODEL}...")
        embeddings = compute_embeddings(texts, path=path)
        print(f"Computed embeddings with shape: {embeddings.shape}")

    return embeddings


embeddings = load_embeddings(df['abstract'].tolist())
print(f"Each paper is represented by a {embeddings.shape[1]}-dimensional vector")

# Verify they match
assert len(df) == len(embeddings), "Mismatch between papers and embeddings!"

# Check the distribution across categories
print(f"\nPapers per category:")
print(df['category'].value_counts().sort_index())

# Look at a sample paper
print(f"\nSample paper:")
print(f"Title: {df['title'].iloc[0]}")
print(f"Category: {df['category'].iloc[0]}")
print(f"Abstract: {df['abstract'].iloc[0][:200]}...")
