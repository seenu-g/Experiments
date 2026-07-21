from dotenv import load_dotenv
load_dotenv()

import pandas as pd

data = [
    {
        "question": "What does a data scientist do?",
        "context": "A data scientist analyzes data to extract insights using statistics and machine learning.",
        "answer": "A data scientist analyzes data to extract insights."
    },
    {
        "question": "What is machine learning?",
        "context": "Machine learning is a subset of AI that enables systems to learn from data.",
        "answer": "Machine learning allows systems to learn from data."
    }
]

df = pd.DataFrame(data)

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_index(contexts):
    doc_embeddings = model.encode(contexts)
    index = faiss.IndexFlatL2(doc_embeddings.shape[1])
    index.add(np.array(doc_embeddings))
    return index

documents = df["context"].tolist()
index = build_index(documents)

def retrieve(query, k=1):
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k)
    return [documents[i] for i in indices[0]]

from transformers import pipeline, GenerationConfig

generator = pipeline("text-generation", model="distilgpt2")
generator.tokenizer.pad_token = generator.tokenizer.eos_token

generation_config = GenerationConfig(
    max_new_tokens=50,
    num_return_sequences=1,
    pad_token_id=generator.tokenizer.eos_token_id,
)

def generate_answer(query, context):
    prompt = f"Context: {context}\nQuestion: {query}\nAnswer:"
    output = generator(
        prompt,
        generation_config=generation_config,
        clean_up_tokenization_spaces=False,
    )
    generated_text = output[0]["generated_text"]
    return generated_text[len(prompt):].strip()

def get_context(question):
    retrieved_context = retrieve(question)[0]
    answer = generate_answer(question, retrieved_context)
    return retrieved_context, answer

def build_results(df):
    results = []

    for _, row in df.iterrows():
        context, prediction = get_context(row["question"])

        results.append({
            "question": row["question"],
            "ground_truth": row["answer"],
            "prediction": prediction,
            "retrieved_context": context
        })

    return pd.DataFrame(results)

results_df = build_results(df)

print(results_df)