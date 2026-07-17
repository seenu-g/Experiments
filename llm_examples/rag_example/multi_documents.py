import os

from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Which embeddings backend to use: "ollama" (default, local, no download needed
# beyond `ollama pull all-minilm:l6-v2`) or "huggingface" (downloads the model
# via sentence-transformers). Override with the EMBEDDINGS_PROVIDER env var.
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "ollama").lower()
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm:l6-v2")
HF_EMBED_MODEL = os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def load_documents(folder_path: str):
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder '{folder_path}' does not exist")

    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            print(f"📄 Loading: {filename}")
            try:
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    return documents


def split_text(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(documents)
    print(f"✂️ Created {len(chunks)} chunks")
    return chunks


def get_embeddings():
    """Return an embeddings model for the configured EMBEDDINGS_PROVIDER."""
    if EMBEDDINGS_PROVIDER == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=HF_EMBED_MODEL)
    return OllamaEmbeddings(model=OLLAMA_EMBED_MODEL)


embedding_function = get_embeddings()


def create_vector_store(chunks):
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory="./chroma_db",
        collection_name="rag_docs"
    )
    return vector_store


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def query_rag_system(query_text, vector_store):
    llm = ChatOllama(model="llama3.1:latest")  # Make sure you have Ollama installed and running!

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful assistant.
        Answer ONLY using the context below.
        If the answer is not present, say "I don't know."

        Context:
        {context}

        Question:
        {question}
        """
    )

    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke(query_text)


def main():
    folder_path = "D:/code/Experiments/llm_examples/rag_example/documents"  # CHANGE THIS to your folder path

    if not os.path.exists("./chroma_db"):
        print("📦 No vector DB found. Creating one...")
        docs = load_documents(folder_path)
        chunks = split_text(docs)
        vector_store = create_vector_store(chunks)
        print("Vector database created")
    else:
        print("📦 Loading existing vector DB...")
        vector_store = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embedding_function,
            collection_name="rag_docs"
        )

    while True:
        query = input("\n❓ Ask a question (or type 'exit'): ")
        if query.lower() == "exit":
            break

        print("🤔 Thinking...")
        answer = query_rag_system(query, vector_store)
        print("\n🧠 Answer:\n", answer)


if __name__ == "__main__":
    main()