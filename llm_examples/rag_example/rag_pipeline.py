"""
rag_pipeline.py

A minimal Retrieval-Augmented Generation (RAG) pipeline with these stages:
1. Load documents from PDF files
2. Chunk documents into smaller passages
3. Index chunks in a local Chroma vector store
4. Retrieve relevant chunks for a user query
5. Pass retrieved context to an LLM
6. Return an answer to the user

The model weights are cached locally in `hf_cache/`. The vector index in `chroma_db/` is rebuilt from
scratch on every run so document changes are always picked up.
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

DATA_DIR = Path(__file__).resolve().parent / "documents"
PERSIST_DIR = Path(__file__).resolve().parent / "chroma_db"
MODEL_CACHE_DIR = Path(__file__).resolve().parent / "hf_cache"
COLLECTION_NAME = "rag_store"


def load_documents(folder_path: Path):
    """Load PDF documents from a folder into LangChain document objects."""
    docs = []
    for file in folder_path.iterdir():
        if file.suffix.lower() == ".pdf":
            loader = PyPDFLoader(file)
            docs.extend(loader.load())
    print("PDF Pages Loaded:", len(docs))
    return docs


def chunk_documents(docs, chunk_size: int = 500, chunk_overlap: int = 80):
    """Split raw documents into smaller chunks for embedding and retrieval."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_documents(docs)
    print("Chunks Created:", len(chunks))
    return chunks


def build_vector_store(chunks):
    """Encode chunks and store them in a persistent Chroma vector database."""
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [
        {key: str(value) for key, value in chunk.metadata.items()}
        for chunk in chunks
    ]

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_model,
        persist_directory=str(PERSIST_DIR),
    )
    db.add_texts(texts=texts, metadatas=metadatas)
    return db


def load_or_build_vector_store():
    """Wipe any persisted index and rebuild it fresh from the current PDFs."""
    if PERSIST_DIR.exists():
        shutil.rmtree(PERSIST_DIR)

    docs = load_documents(DATA_DIR)
    if not docs:
        raise FileNotFoundError(f"No PDF files found in {DATA_DIR}")

    chunks = chunk_documents(docs)
    return build_vector_store(chunks)


def load_model(model_name: str = "google/flan-t5-base"):
    """Load tokenizer and seq2seq model weights from local cache or Hugging Face."""
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=str(MODEL_CACHE_DIR))
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=str(MODEL_CACHE_DIR))
    return tokenizer, model


def get_user_query():
    """Prompt the user for a query, or exit if blank."""
    try:
        return input("Enter a question (or blank to exit): ").strip()
    except EOFError:
        return ""


def retrieve_documents(query: str, retriever):
    """Retrieve relevant document chunks from the vector store for the query."""
    return retriever.invoke(query)


def build_prompt(query: str, context: str) -> str:
    """Assemble the LLM prompt from retrieved context and the user's question."""
    return (
        "Answer the question using only the context below. "
        "If the context does not contain the answer, say you don't know.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    )


def generate_answer(query: str, results, llm):
    """Build a prompt from retrieved context and generate an answer using the LLM."""
    if not results:
        return "No relevant documents found for this query."

    context = "\n\n".join(
        f"[source: {doc.metadata.get('source', 'unknown')}] {doc.page_content}"
        for doc in results
    )
    prompt = build_prompt(query, context)
    return llm(prompt)


def create_pipeline(model_name: str = "google/flan-t5-base"):
    """Build the full LLM pipeline for inference."""
    tokenizer, model = load_model(model_name)

    def llm(prompt: str):
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            do_sample=False,
        )
        return tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

    return llm


def main():
    """Run the RAG application loop: load data, retrieve, and answer user queries."""
    db = load_or_build_vector_store()
    retriever = db.as_retriever(search_kwargs={"k": 3})
    llm = create_pipeline("google/flan-t5-base")

    print("Ready to answer queries.")
    while True:
        query = get_user_query()
        if not query:
            print("Goodbye.")
            break

        results = retrieve_documents(query, retriever)
        answer = generate_answer(query, results, llm)

        print("\nAnswer:")
        print(answer)
        print("-" * 40)


if __name__ == "__main__":
    main()
