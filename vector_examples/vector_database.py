import numpy as np

class VectorDatabase:
    def __init__(self):
        # Store all vectors in an array
        self.vectors = []
    
    # Add vector to database
    def add_vector(self, vec_id, vector, metadata=None):
        record = {
            "id": vec_id,
            "vector": np.array(vector, dtype=np.float32),
            "metadata": metadata
        }

        self.vectors.append(record)

    # Retreive all vectors from database
    def get_all_vectors(self):
        return self.vectors

    # Calculate consine similarity between vectors
    def _cosine_similarity(self, vec_a, vec_b): 
        # Calculate dot product
        dot_product = np.dot(vec_a, vec_b) 
        
        # Calculate the magnitude of vector A 
        norm_a = np.linalg.norm(vec_a)

        # Calculate the magnitude of vector B 
        norm_b = np.linalg.norm(vec_b)

        cos_sim = dot_product / (norm_a * norm_b + 1e-8)  # small epsilon to avoid division by zero
        
        return cos_sim
    
     # Search for similar vectors and return the top_k results
    def search(self, query_vector, top_k = 3):
        query_vector = np.array(query_vector, dtype = np.float32)
        
        # Stores the top_k results
        results = []

        for record in self.vectors:
            sim = self._cosine_similarity(query_vector, record["vector"])
            
            results.append({
                "id": record["id"],
                "similarity": sim,
                "metadata": record["metadata"]
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results[:top_k]