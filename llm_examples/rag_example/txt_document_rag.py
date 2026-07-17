from dotenv import load_dotenv
load_dotenv()

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def create_chunks(policy_text, chunk_size=150, chunk_overlap=20):
    """Split the source text into overlapping chunks."""
    # This splitter is smart. It tries to split on paragraphs ("\n\n"),
    # then newlines ("\n"), then spaces (" "), to keep semantically
    # related text together as much as possible.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,       # Max size of a chunk
        chunk_overlap=chunk_overlap, # Overlap to maintain context between chunks
        length_function=len
    )
    chunks = text_splitter.split_text(policy_text)

    print(f"We have {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---\n{chunk}\n")

    return chunks


def embed_chunks(chunks, model):
    """Embed all our chunks using the given SentenceTransformer model."""
    # This will take a moment as it "reads" and "understands" each chunk.
    chunk_embeddings = model.encode(chunks)
    print(f"Shape of our embeddings: {chunk_embeddings.shape}")
    return chunk_embeddings


def create_faiss_index(chunk_embeddings):
    """Create a FAISS index and add our chunk embeddings to it."""
    # Get the dimension of our vectors (e.g., 384)
    d = chunk_embeddings.shape[1]

    # IndexFlatL2 is the simplest, most basic index. It calculates
    # the exact distance (L2 distance) between our query and all vectors.
    index = faiss.IndexFlatL2(d)

    # We must convert to float32 for FAISS
    index.add(np.array(chunk_embeddings).astype('float32'))
    print(f"FAISS index created with {index.ntotal} vectors.")

    return index


def load_policy_text(path="my_policy.txt"):
    """Load the source document we'll chunk, embed, and search over."""
    with open(path) as f:
        return f.read()


def load_models():
    """Load the embedding model and the seq2seq generation model."""
    # 'all-MiniLM-L6-v2' is a fantastic, fast, and small model.
    # It runs 100% on your local machine.
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # We'll use a small, instruction-tuned seq2seq model from Google. Loaded
    # directly (rather than via pipeline()) since flan-t5 is encoder-decoder
    # and newer transformers versions no longer expose a
    # "text2text-generation" pipeline task alias for it.
    generator_tokenizer = AutoTokenizer.from_pretrained('google/flan-t5-small')
    generator_model = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small')

    return model, generator_tokenizer, generator_model


policy_text = load_policy_text()
chunks = create_chunks(policy_text)

model, generator_tokenizer, generator_model = load_models()
chunk_embeddings = embed_chunks(chunks, model)

index = create_faiss_index(chunk_embeddings)


# --- This is our RAG pipeline function ---
def answer_question(query):
    # 1. RETRIEVE
    # Embed the user's query
    query_embedding = model.encode([query]).astype('float32')

    # Search the FAISS index for the top k (e.g., k=2) most similar chunks
    k = 2
    distances, indices = index.search(query_embedding, k)

    # Get the actual text chunks from our original 'chunks' list
    retrieved_chunks = [chunks[i] for i in indices[0] if i != -1]
    context = "\n\n".join(retrieved_chunks)

    # 2. AUGMENT
    # This is the "magic prompt." We combine the retrieved context
    # with the user's query.
    prompt_template = f"""
    Answer the following question using *only* the provided context.
    If the answer is not in the context, say "I don't have that information."

    Context:
    {context}

    Question:
    {query}

    Answer:
    """

    # 3. GENERATE
    # Feed the augmented prompt to our generative model
    input_ids = generator_tokenizer(prompt_template, return_tensors="pt").input_ids
    output_ids = generator_model.generate(input_ids, max_length=100)
    answer = generator_tokenizer.decode(output_ids[0], skip_special_tokens=True)
    print(f"--- CONTEXT ---\n{context}\n")
    return answer


# --- Try it out ---
if __name__ == "__main__":
    question = "How many PTO days do full-time employees get?"
    print(f"Question: {question}")
    print(f"Answer: {answer_question(question)}")

    query_2 = "What is the company's dental plan?"
    print(f"Query: {query_2}")
    print(f"Answer: {answer_question(query_2)}\n")