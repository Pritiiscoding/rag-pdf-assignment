"""Thin wrapper around the Qdrant client for this project's specific needs."""
import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.pdf_loader import Chunk


class VectorStore:
    def __init__(self, url: str, api_key: str, collection_name: str, vector_size: int):
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = collection_name
        self.vector_size = vector_size

    def recreate_collection(self) -> None:
        """Drop and recreate the collection (used at ingestion time)."""
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=qmodels.VectorParams(
                size=self.vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )

    def collection_exists(self) -> bool:
        return self.client.collection_exists(self.collection_name)

    def upsert_chunks(self, chunks: List[Chunk], vectors: List[List[float]], batch_size: int = 128) -> None:
        points = []
        for chunk, vector in zip(chunks, vectors):
            # Deterministic-ish unique id; content isn't needed for lookup by id later.
            point_id = str(uuid.uuid4())
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "doc_name": chunk.doc_name,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                    },
                )
            )

        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=self.collection_name, points=batch)

    def search(self, query_vector: List[float], top_k: int):
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )
        return results.points
