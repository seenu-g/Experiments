import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# Module-level state, populated by main() before the graph/search helpers are used.
graph = None
vector_store = None

QUERIES = [
    ("Isaac Newton", "What did Isaac Newton discover?"),
    ("Black Hole", "What is the relationship between gravity and black holes?"),
    ("Photosynthesis", "How does photosynthesis depend on light?"),
    ("Machine Learning", "What are neural networks used for in machine learning?"),
    ("Einstein", "What was Einstein known for in the field of physics?"),
    ("ChatGPT", "How does ChatGPT work under the hood?"),
]


def load_documents(csv_path="graphrag_sample.csv"):
    """Load the CSV of concepts into LangChain Documents."""
    df = pd.read_csv(csv_path)
    print("Loaded", len(df), "rows.")

    return [
        Document(page_content=row['content'], metadata={"name": row['title'], "type": "Concept"})
        for _, row in df.iterrows()
    ]


def build_faiss_store(docs):
    """Embed the documents and load them into an in-memory FAISS index."""
    embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
    store = FAISS.from_documents(documents=docs, embedding=embeddings)
    print("Successfully added documents to FAISS vector store.")
    return store


def build_knowledge_graph():
    """Build a small sample knowledge graph of entity relationships."""
    kg = nx.DiGraph()
    kg.add_edge("Isaac Newton", "Gravity", relation="discovered")
    kg.add_edge("Einstein", "Relativity", relation="developed")
    kg.add_edge("Machine Learning", "Neural Network", relation="uses")
    kg.add_edge("ChatGPT", "Neural Network", relation="based_on")
    kg.add_edge("Photosynthesis", "Light", relation="depends_on")
    kg.add_edge("DNA", "Genetics", relation="represents")
    kg.add_edge("Black Hole", "Gravity", relation="affected_by")
    return kg


def visualize_graph(kg):
    """(Optional) Draw the knowledge graph."""
    plt.figure(figsize=(10, 6))
    nx.draw(kg, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, edge_color='gray')
    plt.title("Knowledge Graph")
    plt.show()


def get_related_entities(entity):
    return list(graph.neighbors(entity)) if entity in graph else []


def graph_rag_search(entity, k=5):
    """Expand the entity using the knowledge graph, then search the vector store."""
    related_entities = get_related_entities(entity)
    expanded_query = " ".join([entity] + related_entities)
    print("Expanded Query:", expanded_query)

    return vector_store.similarity_search(expanded_query, k=k)


def build_qa_chain():
    """Build a retrieval-augmented QA chain over the FAISS vector store."""
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    llm = ChatOllama(model="llama3.1:latest", temperature=0)

    prompt = ChatPromptTemplate.from_template(
        """Answer the question using *only* the following context:

{context}

Question: {input}"""
    )

    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, combine_docs_chain)


def answer_query(qa_chain, entity, query):
    """Run one entity/query pair: graph-expanded retrieval, then LLM answer generation."""
    print(f"🔍 Query: {query}")

    # Step 1: Expand using graph
    graph_rag_search(entity)

    # Step 2: Answer generation using the LangChain QA chain
    response = qa_chain.invoke({"input": query})
    answer = response["answer"]

    print(f"✅ Answer: {answer}")
    print("-" * 80)
    return answer


def main():
    global graph, vector_store

    docs = load_documents()
    vector_store = build_faiss_store(docs)

    graph = build_knowledge_graph()
    visualize_graph(graph)
    print(get_related_entities("Isaac Newton"))  # ➝ ['Gravity']

    qa_chain = build_qa_chain()

    for entity, query in QUERIES:
        answer_query(qa_chain, entity, query)


if __name__ == "__main__":
    main()
