"""Wraps a local sentence-transformers model for generating embeddings.

Embeddings are generated locally (no API cost/key needed) so the only paid
component we depend on is the LLM call, which uses a free OpenRouter model.
"""
from typing import List


class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model_name = model_name

        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dimension = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return vectors.tolist()

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]
