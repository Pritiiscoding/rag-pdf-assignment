"""Local sentence-transformer embeddings with memory-efficient batching."""

from typing import List
import os

import torch
from sentence_transformers import SentenceTransformer


# Keep CPU usage/memory under control on small Render instances
torch.set_num_threads(1)
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model_name = model_name

        print(f"[INFO] Loading embedding model: {model_name}")

        self._model = SentenceTransformer(
            model_name,
            device="cpu"
        )

        self._model.eval()

        self.dimension = self._model.get_sentence_embedding_dimension()

        print(f"[INFO] Embedding dimension: {self.dimension}")

    def embed(
        self,
        texts: List[str],
        batch_size: int = 8
    ) -> List[List[float]]:
        """Generate embeddings in small batches to reduce memory usage."""

        if not texts:
            return []

        all_vectors = []

        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]

            print(
                f"[INFO] Embedding chunks "
                f"{start + 1}-{min(start + batch_size, len(texts))} "
                f"of {len(texts)}"
            )

            with torch.no_grad():
                vectors = self._model.encode(
                    batch,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                    convert_to_numpy=True
                )

            all_vectors.extend(vectors.tolist())

            # Explicitly release temporary tensors
            del vectors

        return all_vectors

    def embed_one(self, text: str) -> List[float]:
        """Generate an embedding for one question."""

        with torch.no_grad():
            vector = self._model.encode(
                [text],
                batch_size=1,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True
            )

        return vector[0].tolist()
