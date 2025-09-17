"""
Semantic Cache using Sentence Transformers and FAISS
Provides a cache that retrieves items based on semantic similarity of keys.
"""

from typing import Dict, Any, Optional, List

# Import necessary libraries, with error handling for missing dependencies
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "SentenceTransformer is not installed. Please run 'pip install sentence-transformers'."
    )

try:
    import faiss
except ImportError:
    raise ImportError("FAISS is not installed. Please run 'pip install faiss-cpu'.")


class SemanticCache:
    """
    A cache that stores text-based queries and their responses, allowing retrieval
    based on the semantic similarity of the query.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.95,
    ):
        """
        Initializes the semantic cache.

        Args:
            model_name (str): The name of the SentenceTransformer model to use.
            similarity_threshold (float): The minimum similarity score to consider a cache hit.
        """
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold

        # Get the embedding dimension from the model
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        # FAISS index for efficient similarity search
        self.index = faiss.IndexFlatL2(self.embedding_dim)

        # Storage for the actual queries and responses
        self.query_storage: List[str] = []
        self.response_storage: Dict[str, Any] = {}

    def add(self, query: str, response: Any):
        """
        Adds a query and its response to the cache.

        Args:
            query (str): The user query (e.g., a prompt).
            response (Any): The response to be cached.
        """
        if query in self.response_storage:
            # Query already exists, no need to add again
            return

        # Generate embedding for the query
        query_embedding = self.model.encode([query])

        # Add the embedding to the FAISS index
        self.index.add(query_embedding)

        # Store the query and response
        self.query_storage.append(query)
        self.response_storage[query] = response

    def search(self, query: str) -> Optional[Any]:
        """
        Searches for a semantically similar query in the cache.

        Args:
            query (str): The user query to search for.

        Returns:
            Optional[Any]: The cached response if a similar query is found, otherwise None.
        """
        if self.index.ntotal == 0:
            return None  # Cache is empty

        # Generate embedding for the search query
        query_embedding = self.model.encode([query])

        # Search the FAISS index for the most similar query
        # We search for the top 1 most similar item (k=1)
        distances, indices = self.index.search(query_embedding, 1)

        if len(indices) > 0:
            most_similar_index = indices[0][0]
            distance = distances[0][0]

            # Convert L2 distance to a similarity score (0 to 1)
            # This is a simple heuristic; a more principled mapping might be needed
            # For normalized embeddings, cosine similarity is (2 - L2_distance^2) / 2
            similarity = (2 - distance**2) / 2

            if similarity >= self.similarity_threshold:
                # Found a sufficiently similar query
                most_similar_query = self.query_storage[most_similar_index]
                return self.response_storage[most_similar_query]

        return None
