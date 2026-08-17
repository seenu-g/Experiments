"""
Standalone test client for the embedding server started via:
    python hybrid_ollama.py --serve

This client only talks HTTP to the server -- it can be started, stopped,
and restarted independently while the server keeps the model loaded.
"""
import argparse
import json
import urllib.request

import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression

SAMPLE_TEXTS = [
    "The stock market rallied today on strong earnings reports.",
    "Investors are optimistic about the tech sector's growth.",
    "The central bank raised interest rates to curb inflation.",
    "The striker scored a hat-trick in last night's football match.",
    "The team celebrated their championship win with a parade.",
    "The coach praised the players' defensive performance.",
]

# 0 = finance, 1 = sports -- used for the LogisticRegression demo
SAMPLE_LABELS = [0, 0, 0, 1, 1, 1]
LABEL_NAMES = {0: "finance", 1: "sports"}


def fetch_embeddings(base_url, texts):
    payload = json.dumps({"texts": texts}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        body = json.loads(response.read())
    return np.array(body["embeddings"])


def check_health(base_url):
    with urllib.request.urlopen(f"{base_url}/health", timeout=5) as response:
        return json.loads(response.read())


def ask(base_url, question):
    payload = json.dumps({"question": question}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        body = json.loads(response.read())
    return body["answer"]


def repl(base_url):
    print("\nClient REPL ready. Ask a question; 'exit' or 'quit' to stop.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        print(f"A: {ask(base_url, question)}\n")


def main():
    parser = argparse.ArgumentParser(description="Test client for the hybrid_ollama embedding server.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    base_url = f"http://{args.host}:{args.port}"

    print(f"Checking server at {base_url} ...")
    print(check_health(base_url))

    print(f"\nFetching embeddings for {len(SAMPLE_TEXTS)} sample texts ...")
    embeddings = fetch_embeddings(base_url, SAMPLE_TEXTS)
    print(f"Got embeddings of shape {embeddings.shape}")

    print("\n--- KMeans clustering (unsupervised, k=2) ---")
    kmeans = KMeans(n_clusters=2, random_state=0, n_init="auto").fit(embeddings)
    for text, cluster in zip(SAMPLE_TEXTS, kmeans.labels_):
        print(f"cluster {cluster}: {text}")

    print("\n--- Logistic Regression (supervised, finance vs sports) ---")
    clf = LogisticRegression().fit(embeddings, SAMPLE_LABELS)
    test_text = "The team's new signing impressed fans in his debut match."
    test_embedding = fetch_embeddings(base_url, [test_text])
    prediction = clf.predict(test_embedding)[0]
    print(f"'{test_text}' -> predicted class: {LABEL_NAMES[prediction]}")

    repl(base_url)


if __name__ == "__main__":
    main()
