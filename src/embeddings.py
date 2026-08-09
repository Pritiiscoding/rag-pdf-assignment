"""Wraps a local sentence-transformers model or API-based embeddings for generating embeddings.

Supports both local models (via sentence-transformers) and API-based embeddings (via OpenAI)
to handle storage constraints on cloud platforms.
"""
from typing import List, Optional
import os

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EmbeddingModel:
    def __init__(self, model_name: str, use_api: bool = False, api_key: Optional[str] = None):
        self.model_name = model_name
        self.use_api = use_api
        self._model = None
        self._client = None
        self.dimension = 384  # Default dimension for most models
        
        if use_api and OPENAI_AVAILABLE and api_key:
            self._client = OpenAI(api_key=api_key)
            self.dimension = 1536  # OpenAI text-embedding-3-small dimension
        elif SENTENCE_TRANSFORMERS_AVAILABLE:
            print(f"[INFO] Loading local embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
            self.dimension = self._model.get_sentence_embedding_dimension()
        else:
            raise RuntimeError("No embedding backend available. Install sentence-transformers or openai.")

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        if self.use_api and self._client:
            return self._embed_with_api(texts)
        elif self._model:
            return self._embed_with_local(texts)
        else:
            raise RuntimeError("Embedding model not initialized")

    def _embed_with_local(self, texts: List[str]) -> List[List[float]]:
        """Embed using local sentence-transformers model."""
        vectors = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return vectors.tolist()

    def _embed_with_api(self, texts: List[str]) -> List[List[float]]:
        """Embed using OpenAI API."""
        # Process in batches to avoid rate limits
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self._client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"[ERROR] API embedding failed: {e}")
                raise
        
        return all_embeddings

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]
