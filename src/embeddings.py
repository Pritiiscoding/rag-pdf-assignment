"""Wraps a local sentence-transformers model or API-based embeddings for generating embeddings.

Supports both local models (via sentence-transformers) and API-based embeddings (via OpenAI)
to handle storage constraints on cloud platforms.
"""
from typing import List, Optional
import os

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError):
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[WARN] sentence-transformers not available (torch dependency issue)")

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
        
        if use_api and OPENAI_AVAILABLE and api_key and api_key != "sk-proj-your-key-here":
            self._client = OpenAI(api_key=api_key)
            self.dimension = 1536  # OpenAI text-embedding-3-small dimension
            print("[INFO] Using OpenAI API embeddings")
        elif not use_api and SENTENCE_TRANSFORMERS_AVAILABLE:
            print(f"[INFO] Loading local embedding model: {model_name}")
            try:
                self._model = SentenceTransformer(model_name)
                self.dimension = self._model.get_sentence_embedding_dimension()
            except Exception as e:
                print(f"[ERROR] Failed to load sentence-transformers: {e}")
                raise RuntimeError(f"Failed to load local model: {e}")
        else:
            # Fallback for testing without proper API keys
            print("[WARN] No valid embedding backend available - using dummy embeddings for testing")
            print("[WARN] Please set USE_API_EMBEDDINGS=true with a valid OPENAI_API_KEY")
            print("[WARN] Or fix torch/sentence-transformers installation for local embeddings")
            self._use_dummy = True
            self.dimension = 384

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        if hasattr(self, '_use_dummy') and self._use_dummy:
            return self._embed_with_dummy(texts)
        elif self.use_api and self._client:
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

    def _embed_with_dummy(self, texts: List[str]) -> List[List[float]]:
        """Generate dummy embeddings for testing purposes."""
        import hashlib
        import numpy as np
        
        embeddings = []
        for text in texts:
            # Create a consistent hash-based embedding
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to float array
            embedding = []
            for i in range(self.dimension):
                byte_val = hash_bytes[i % len(hash_bytes)]
                normalized = (byte_val / 255.0) * 2 - 1  # Normalize to [-1, 1]
                embedding.append(float(normalized))
            
            embeddings.append(embedding)
        
        return embeddings

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]
