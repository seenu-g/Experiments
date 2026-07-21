from dotenv import load_dotenv
load_dotenv()

from sklearn.metrics.pairwise import cosine_similarity
from llm_sample import model, results_df

def similarity_score(a, b):
    emb1 = model.encode([a])
    emb2 = model.encode([b])
    return cosine_similarity(emb1, emb2)[0][0]

results_df["similarity"] = results_df.apply(
    lambda row: similarity_score(row["ground_truth"], row["prediction"]),
    axis=1
)

results_df["context_score"] = results_df.apply(
    lambda row: similarity_score(row["retrieved_context"], row["ground_truth"]),
    axis=1
)

def groundedness(answer, context):
    context_words = set(context.lower().split())
    answer_words = answer.lower().split()
    return int(any(word.strip(".,!?") in context_words for word in answer_words))

results_df["groundedness"] = results_df.apply(
    lambda row: groundedness(row["prediction"], row["retrieved_context"]),
    axis=1
)

print("Average Similarity:", results_df["similarity"].mean())
print("Average Context Score:", results_df["context_score"].mean())
print("Groundedness Rate:", results_df["groundedness"].mean())