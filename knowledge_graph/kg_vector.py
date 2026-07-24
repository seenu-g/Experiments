"""
Knowledge-graph RAG (retrieval-augmented generation) over the kg.py ontology
demo (companies/cities/countries). Each stage of the pipeline is a named
function so the end-to-end flow is easy to follow:

  1. build_graph()      -> reuse kg.py's KnowledgeGraph: nodes, edges,
                            ontology rules, and the reasoner's inferred facts
  2. verbalize()         -> turn a graph triple (source, relation, target)
                            into a plain-English sentence
  3. build_index()       -> embed every sentence once, via Ollama's own
                            embedding model (no HF/sentence-transformers
                            dependency needed)
  4. retrieve()          -> cosine-similarity search: top-k relevant facts
                            for a natural-language question
  5. generate_answer()   -> the "G" in RAG: hand the retrieved facts + the
                            question to a local LLM (Ollama) and ground its
                            answer in only those facts

Requires: pip install ollama numpy
          Ollama running locally with qwen3.5:latest and all-minilm:l6-v2
          pulled (`ollama pull all-minilm:l6-v2`).

Run: python kg_vector.py
"""
import numpy as np
import ollama

from kg import Edge, KnowledgeGraph, location_inheritance_rule, transitivity_rule
from load_kg_data import load_from_csv

EMBEDDING_MODEL = "all-minilm:l6-v2"
LLM_MODEL = "qwen3.5:latest"
TOP_K = 5


def embed(text: str) -> np.ndarray:
    """Embed one string via Ollama, normalized so dot product == cosine similarity."""
    vec = np.array(ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)["embedding"])
    return vec / np.linalg.norm(vec)


def build_graph() -> KnowledgeGraph:
    """Same setup as kg.py's __main__, but we also run the reasoner so
    implicit/inferred facts (e.g. transitive subsidiaries) are retrievable
    too, not just the explicit ones loaded from CSV."""
    kg = KnowledgeGraph()
    kg.add_ontology_rule("headquartered_in", "Company", "City")
    kg.add_ontology_rule("located_in",       "City",    "Country")
    kg.add_ontology_rule("subsidiary_of",    "Company", "Company")
    kg.add_ontology_rule("operates_in",      "Company", "Country")
    kg.add_inference_rule(transitivity_rule)
    kg.add_inference_rule(location_inheritance_rule)

    load_from_csv(kg)
    kg.run_reasoner()
    return kg


def verbalize(edge: Edge) -> str:
    """Turn a graph triple into a plain-English sentence, since an embedding
    model compares natural language, not raw IDs like 'co:youtube'."""
    def label(node_id: str) -> str:
        return node_id.split(":", 1)[-1].replace("_", " ")

    relation_phrase = edge.relation.replace("_", " ")
    return f"{label(edge.source)} {relation_phrase} {label(edge.target)}."


def build_index(kg: KnowledgeGraph):
    """Embed every fact in the graph once. Returns the sentences and their
    embedding matrix (normalized, so similarity is just a dot product)."""
    sentences = [verbalize(e) for e in kg.edges]
    embeddings = np.array([embed(s) for s in sentences])
    return sentences, embeddings


def retrieve(query: str, sentences: list, embeddings, top_k: int = TOP_K):
    """Embed the question and return the top_k most similar facts."""
    query_vec = embed(query)
    scores = embeddings @ query_vec
    top_idx = np.argsort(-scores)[:top_k]
    return [(sentences[i], float(scores[i])) for i in top_idx]


def generate_answer(query: str, retrieved_facts: list) -> str:
    """Ground the LLM's answer in only the retrieved facts, so it can't
    make things up beyond what the graph actually contains."""
    context = "\n".join(f"- {fact}" for fact in retrieved_facts)
    prompt = (
        "Answer the question using ONLY the facts below. "
        "If the facts don't contain the answer, say so.\n\n"
        f"Facts:\n{context}\n\nQuestion: {query}\nAnswer:"
    )
    response = ollama.chat(model=LLM_MODEL, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]


def ask(query: str, sentences: list, embeddings):
    hits = retrieve(query, sentences, embeddings)
    print(f"\nQ: {query}")
    print("Retrieved facts:")
    for fact, score in hits:
        print(f"  [{score:.2f}] {fact}")
    answer = generate_answer(query, [fact for fact, _ in hits])
    print(f"A: {answer}")


if __name__ == "__main__":
    print("1. Building knowledge graph (facts + reasoner-inferred facts)...")
    kg = build_graph()
    print(f"   {len(kg.nodes)} nodes, {len(kg.edges)} edges (including inferred)")

    print("2/3. Verbalizing triples and embedding them...")
    sentences, embeddings = build_index(kg)
    for s in sentences:
        print(f"   - {s}")

    print("\n4/5. Retrieval + generation over example questions:")
    example_questions = [
        "Is YouTube a subsidiary of Alphabet?",
        "What country does Google operate in?",
        "Where is Google headquartered?",
    ]
    for q in example_questions:
        ask(q, sentences, embeddings)
