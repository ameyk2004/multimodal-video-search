from huggingface_hub import InferenceClient

class HuggingFaceEmbedder:
    """
    Handles communication with HuggingFace Inference API to generate embeddings.
    Uses the huggingface_hub InferenceClient which automatically routes to the
    correct endpoint (router.huggingface.co).
    """
    def __init__(self, api_key: str, model_id: str = "BAAI/bge-m3", vector_dimension: int = 1024):
        self.client = InferenceClient(token=api_key)
        self.model_id = model_id
        self.vector_dimension = vector_dimension

    def generate_embedding(self, text: str) -> list[float]:
        """
        Calls the HuggingFace Inference API to produce an embedding.
        Works for multilingual inputs (e.g., English and Marathi) if the model supports it.
        """
        embedding = self.client.feature_extraction(
            text=text,
            model=self.model_id,
        )

        # The client returns a numpy array or nested list; convert to flat list
        result = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)

        # Flatten if nested
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]

        if len(result) != self.vector_dimension:
            raise ValueError(
                f"Expected {self.vector_dimension}-d vector, got {len(result)}-d"
            )

        return result
