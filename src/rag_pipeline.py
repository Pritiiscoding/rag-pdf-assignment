"""Wires together PDF parsing, embeddings, Qdrant, and the LLM into one pipeline."""
import concurrent.futures
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
        self.embedder = EmbeddingModel(
            model_name=settings.embedding_model,
            use_api=settings.use_api_embeddings,
            api_key=settings.openai_api_key if settings.use_api_embeddings else None
        )
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
        """Parse all PDFs in settings.pdf_dir, embed them, and load into Qdrant.

        Returns the number of chunks indexed.
        """
        try:
            # Use ThreadPoolExecutor for timeout handling
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._ingest_internal)
                return future.result(timeout=300)  # 5 minute timeout
        except concurrent.futures.TimeoutError:
            raise TimeoutError("Document ingestion timed out after 5 minutes")
    
    def _ingest_internal(self) -> int:
        """Internal ingestion method without timeout wrapper."""
        chunks = load_pdfs(
            pdf_dir=self.settings.pdf_dir,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        print(f"[INFO] Total chunks to embed: {len(chunks)}")

        texts = [c.text for c in chunks]
        vectors = self.embedder.embed(texts)

        self.store.recreate_collection()
        self.store.upsert_chunks(chunks, vectors)

        print(f"[INFO] Indexed {len(chunks)} chunks into Qdrant collection '{self.settings.qdrant_collection}'")
        return len(chunks)

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
