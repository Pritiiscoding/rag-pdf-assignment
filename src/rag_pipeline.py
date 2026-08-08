"""Wires together PDF parsing, embeddings, Qdrant, and the LLM into one pipeline."""
from dataclasses import dataclass
from typing import List

from src.config import Settings
from src.embeddings import EmbeddingModel
from src.llm import NOT_FOUND_PHRASE, OpenRouterLLM
from src.pdf_loader import load_pdfs
from src.vector_store import VectorStore


@dataclass
class Citation:
    doc_name: str
    page_number: int
    snippet: str
    score: float


@dataclass
class RAGAnswer:
    answer: str
    citations: List[Citation]
    found: bool


class RAGPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedder = EmbeddingModel(settings.embedding_model)
        self.store = VectorStore(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection_name=settings.qdrant_collection,
            vector_size=self.embedder.dimension,
        )
        self.llm = OpenRouterLLM(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
        )

    def ingest(self) -> int:
    """Parse PDFs and index embeddings in small batches."""

    chunks = load_pdfs(
        pdf_dir=self.settings.pdf_dir,
        chunk_size=self.settings.chunk_size,
        chunk_overlap=self.settings.chunk_overlap,
    )

    total_chunks = len(chunks)

    if total_chunks == 0:
        print("[INFO] No PDF chunks found.")
        return 0

    print(f"[INFO] Total chunks to embed: {total_chunks}")

    # Create/reset Qdrant collection first
    self.store.recreate_collection()

    batch_size = 8
    indexed = 0

    for start in range(0, total_chunks, batch_size):
        batch_chunks = chunks[start:start + batch_size]

        texts = [chunk.text for chunk in batch_chunks]

        print(
            f"[INFO] Processing chunks "
            f"{start + 1}-{min(start + batch_size, total_chunks)} "
            f"of {total_chunks}"
        )

        # Generate only a small number of embeddings at once
        vectors = self.embedder.embed(
            texts,
            batch_size=batch_size
        )

        # Immediately upload this batch
        self.store.upsert_chunks(
            batch_chunks,
            vectors
        )

        indexed += len(batch_chunks)

        # Release temporary objects
        del texts
        del vectors
        del batch_chunks

    # Release the complete chunk list
    del chunks

    print(
        f"[INFO] Indexed {indexed} chunks into "
        f"Qdrant collection '{self.settings.qdrant_collection}'"
    )

    return indexed

    
    def query(self, question: str) -> RAGAnswer:
        if not self.store.collection_exists():
            raise RuntimeError(
                "Qdrant collection does not exist yet. Run ingestion first (python main.py ingest)."
            )

        query_vector = self.embedder.embed_one(question)
        hits = self.store.search(query_vector, top_k=self.settings.top_k)

        answer_text = self.llm.generate_answer(question, hits)
        found = NOT_FOUND_PHRASE not in answer_text

        citations = []
        if found:
            for hit in hits:
                payload = hit.payload
                citations.append(
                    Citation(
                        doc_name=payload["doc_name"],
                        page_number=payload["page_number"],
                        snippet=payload["text"],
                        score=round(hit.score, 4),
                    )
                )

        return RAGAnswer(answer=answer_text, citations=citations, found=found)
